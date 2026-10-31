"""THE LAST CANDLE — authoritative multiplayer Milestone 1 server.
Run: python server.py  (requires aiohttp)
"""
import asyncio
import hashlib
import json
import os
import random
import re
import secrets
import string
import time
from pathlib import Path
from aiohttp import web, WSMsgType

ROOT = Path(__file__).parent
PORT = int(os.environ.get('PORT', '8080'))
DURATION_MS = 20 * 60 * 1000
SOLO_DURATION_MS = 25 * 60 * 1000
LENS_SWITCH_MS = 2_000
SYMBOLS = ['☾', '✶', '⚱', '❦']
ORDER = ['✶', '☾', '❦', '⚱']
ROLES = ['medium', 'archivist', 'lantern', 'locksmith', 'walker']
CHARACTERS = {
    'medium': {'name': 'VESPER', 'class': 'SEER', 'ability': 'Veil Sight'},
    'archivist': {'name': 'QUILL', 'class': 'KEEPER', 'ability': 'Remembered Page'},
    'lantern': {'name': 'EMBER', 'class': 'LIGHT', 'ability': 'Steady Flame'},
    'locksmith': {'name': 'CROWE', 'class': 'BINDER', 'ability': 'Second Turn'},
    'walker': {'name': 'WREN', 'class': 'VOYAGER', 'ability': 'Sure Step'},
}
SELECTION_MS = 45_000
FREEZE_MS = 20_000
VEIL_MS = 10_000
NAMES = [('Thomas Hollow', 'fever'), ('Beatrice Hollow', 'a fall from the western balcony'), ('Edmund Hollow', 'the winter flood'), ('Adelaide Hollow', 'a mysterious illness')]
ROOMS = {}
LOCKS = {}
SOCKETS = {}  # room code -> {seat id: websocket}
ADMISSION_ATTEMPTS = {}  # IP -> recent timestamps, to slow four-letter-code guessing


def now():
    return int(time.time() * 1000)


# Milestone 1 intentionally uses ephemeral in-process room state.
# Free Render instances have no durable disk: a restart clears all rooms.
def persist(room):
    """State changes already mutate the authoritative in-memory ROOMS dictionary."""
    return None


def load():
    """Start with an empty room registry after a cold start."""
    return None


def make_puzzle():
    seed = secrets.token_hex(12)
    r = random.Random(int(seed, 16))
    hours = r.sample(range(1, 13), 4)
    # Family members are paired with stable icon identities, while hours are different each round.
    entries = [{'name': name, 'cause': cause, 'symbol': symbol, 'hour': hour}
               for (name, cause), symbol, hour in zip(NAMES, SYMBOLS, hours)]
    r.shuffle(entries)
    return {'seed': seed, 'entries': entries, 'solution': [next(e['hour'] for e in entries if e['symbol'] == s) for s in ORDER],
            'variantId': seed[:8]}


def new_room(name, capacity, mode='multiplayer'):
    if mode not in ('multiplayer', 'solo') or (mode == 'solo' and capacity != 1):
        raise ValueError('Invalid room mode or capacity')
    for _ in range(100):
        code = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(4))
        if code not in ROOMS:
            break
    else:
        raise RuntimeError('Room codes exhausted')
    room = {'code': code, 'roomId': secrets.token_hex(16), 'capacity': capacity,
            'createdAt': now(), 'version': 0, 'round': 1, 'phase': 'lobby', 'mode': mode,
            'solo': {'equippedAbilities': [], 'activeLens': 'medium', 'targetLens': None, 'lensReadyAt': None} if mode == 'solo' else None,
            'hostId': None, 'players': [], 'puzzle': make_puzzle(),
            'selectionStartedAt': None, 'selectionDeadlineAt': None,
            'abilitiesUsed': {role: False for role in ROLES}, 'secondTurnArmed': False,
            'veilClueUntil': None,
            'timer': {'startedAt': None, 'deadlineAt': None, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None},
            'hintLevel': 0, 'wrongAttempts': 0, 'solvedAt': None, 'chat': [], 'seenActions': [],
            'lastAttemptAt': 0, 'lastChatAt': {}, 'result': None}
    ROOMS[code] = room
    LOCKS[code] = asyncio.Lock()
    SOCKETS[code] = {}
    return room


def add_player(room, name):
    token = secrets.token_urlsafe(36)
    seat = {'id': secrets.token_hex(12), 'name': name, 'joinedAt': now(),
            'tokenHash': hashlib.sha256(token.encode()).hexdigest(),
            'connected': True, 'primaryRole': None, 'roles': [], 'ready': False, 'ack': False, 'lockedAt': None}
    room['players'].append(seat)
    if room['hostId'] is None:
        room['hostId'] = seat['id']
    if room['mode'] == 'solo':
        seat['roles'] = ROLES[:]  # Responsibilities, NOT automatically equipped abilities.
    return seat, token


def get_seat(room, seat_id):
    return next((p for p in room['players'] if p['id'] == seat_id), None)


def migrate_host(room):
    current = get_seat(room, room['hostId'])
    if current and current['connected']:
        return
    connected = [p for p in room['players'] if p['connected']]
    if connected:
        room['hostId'] = min(connected, key=lambda p: p['joinedAt'])['id']


def start_selection_if_needed(room):
    """The first two occupied lobby seats begin the shared 45-second selection."""
    if room['mode'] == 'multiplayer' and room['phase'] == 'lobby' and len([p for p in room['players'] if p['connected']]) >= 2 and room['selectionDeadlineAt'] is None:
        room['selectionStartedAt'] = now()
        room['selectionDeadlineAt'] = now() + SELECTION_MS
        return True
    return False


def auto_lock_stragglers(room):
    """Assign unclaimed primary characters once the selection window has elapsed."""
    if room['mode'] != 'multiplayer' or room['phase'] != 'lobby' or room['selectionDeadlineAt'] is None or now() < room['selectionDeadlineAt']:
        return []
    chosen = {p['primaryRole'] for p in room['players'] if p['primaryRole']}
    locked = []
    for seat in room['players']:
        if seat['primaryRole']:
            continue
        available = [role for role in ROLES if role not in chosen]
        if not available:
            raise ValueError('No character remains available')
        role = secrets.choice(available)
        seat['primaryRole'] = role
        seat['lockedAt'] = now()
        chosen.add(role)
        locked.append((seat, role))
    return locked


def update_merged_roles(room):
    """Display complete assignments only when every current player has locked."""
    if room['mode'] == 'solo':
        for seat in room['players']:
            seat['roles'] = ROLES[:] 
        return
    if len(room['players']) >= 2 and all(p['primaryRole'] for p in room['players']):
        allocate_roles(room)
    else:
        for p in room['players']:
            p['roles'] = [p['primaryRole']] if p['primaryRole'] else []


def reset_selection(room):
    room['selectionStartedAt'] = None
    room['selectionDeadlineAt'] = None
    room['abilitiesUsed'] = {role: False for role in ROLES}
    room['secondTurnArmed'] = False
    room['veilClueUntil'] = None
    if room['mode'] == 'solo':
        room['solo'] = {'equippedAbilities': [], 'activeLens': 'medium', 'targetLens': None, 'lensReadyAt': None}
    for p in room['players']:
        p['primaryRole'] = None
        p['lockedAt'] = None
        p['ready'] = False
        p['roles'] = []
        p['ack'] = False


def allocate_roles(room):
    """Respect primary selections, assign all roles, and separate Archivist/Lantern."""
    seats = list(room['players'])
    if room.get('mode', 'multiplayer') == 'solo':
        if len(seats) != 1:
            raise ValueError('A solo chamber must contain one seat')
        seats[0]['roles'] = ROLES[:] 
        return
    n = len(seats)
    if n < 2:
        raise ValueError('Need at least two players')
    if all(not s['primaryRole'] for s in seats):
        defaults = {
            2: [['medium','lantern','walker'],['archivist','locksmith']],
            3: [['medium','lantern'],['archivist','locksmith'],['walker']],
            4: [['medium','lantern'],['archivist'],['locksmith'],['walker']],
            5: [['medium'],['archivist'],['lantern'],['locksmith'],['walker']]
        }[n]
        for seat, assigned in zip(seats, defaults):
            seat['roles'] = assigned[:]
        return
    for s in seats:
        s['roles'] = [s['primaryRole']] if s['primaryRole'] else []
    selected = {r for s in seats for r in s['roles']}
    # Seat capacity distribution: 3/2, 2/2/1, 2/1/1/1, 1/1/1/1/1.
    target = {2: [3, 2], 3: [2, 2, 1], 4: [2, 1, 1, 1], 5: [1, 1, 1, 1, 1]}[n]
    # Prefer assigned primary seats as anchors, preserving role selection.
    # Since all roles fit across 5 slots and role selection is unique, each player can receive >=1 role.
    for i, s in enumerate(seats):
        if not s['roles']:
            unassigned = [r for r in ROLES if r not in selected]
            role = unassigned[0]
            s['roles'].append(role)
            selected.add(role)
    for role in [r for r in ROLES if r not in selected]:
        candidates = [s for s in seats if not ((role == 'lantern' and 'archivist' in s['roles']) or (role == 'archivist' and 'lantern' in s['roles']))]
        if not candidates:
            raise ValueError('Unable to distribute puzzle clues safely')
        def priority(s):
            i = seats.index(s)
            return (len(s['roles']) >= target[i], len(s['roles']), i)
        chosen = min(candidates, key=priority)
        chosen['roles'].append(role)
        selected.add(role)
    # If a selected primary assigned to different distribution would squeeze one seat, this is okay:
    # clue separation matters more than the nominal bundle sizes.
    archivist = next(s for s in seats if 'archivist' in s['roles'])
    lantern = next(s for s in seats if 'lantern' in s['roles'])
    assert archivist['id'] != lantern['id']


def duration(room):
    return SOLO_DURATION_MS if room['mode'] == 'solo' else DURATION_MS


def solo_switch_pending(room):
    return room['mode'] == 'solo' and room['solo']['targetLens'] is not None


def solo_switch_complete(room):
    """Resolve only at the authoritative deadline; never release clues early."""
    solo = room['solo']
    if room['mode'] != 'solo' or not solo['targetLens'] or now() < solo['lensReadyAt']:
        return False
    solo['activeLens'] = solo['targetLens']
    solo['targetLens'] = None
    solo['lensReadyAt'] = None
    return True


def solo_rank(seconds):
    if seconds >= 900:
        return 'Lone Lightkeeper'
    if seconds >= 450:
        return 'The Unbroken Witness'
    return 'Last of the Living'


def remaining(room):
    timer = room['timer']
    if timer['frozenRemainingMs'] is not None and (room['phase'] != 'playing' or (timer.get('freezeUntil') is not None and now() < timer['freezeUntil'])):
        return timer['frozenRemainingMs']
    if timer['deadlineAt'] is None:
        return duration(room)
    return max(0, timer['deadlineAt'] - now())


def expire(room):
    if room['phase'] == 'playing' and remaining(room) <= 0:
        room['phase'] = 'lost'
        room['result'] = {'outcome': 'lost', 'endedAt': now(), 'secondsRemaining': 0}
        room['timer']['frozenRemainingMs'] = 0
        room['timer']['freezeUntil'] = None
        room['version'] += 1
        persist(room)
        return True
    return False


def role_clues(room, seat):
    if room['phase'] not in ('playing', 'foyer_solved', 'stage2_preview', 'lost'):
        return {}
    output = {}
    permitted = seat['roles']
    if room['mode'] == 'solo':
        permitted = [] if solo_switch_pending(room) else [room['solo']['activeLens']]
    for role in permitted:
        if role == 'medium':
            output[role] = {'portraits': SYMBOLS}
        elif role == 'archivist':
            output[role] = {'entries': room['puzzle']['entries']}
        elif role == 'lantern':
            output[role] = {'order': ORDER}
        elif role == 'locksmith':
            output[role] = {'dials': 4}
        else:
            output[role] = {'message': 'Your footsteps will matter in the Crypt. In this room, listen and help coordinate.'}
    return output


def rank(seconds):
    return 'Ghost Whisperer' if seconds >= 600 else 'Survivor' if seconds >= 300 else 'Barely Breathing'


def public_state(room, seat):
    hints = [
        'The four spirit symbols connect the portraits to the family diary. Compare the markings you each see.',
        'The scratched symbols have a precise order. Ask the Lantern-bearer to read them aloud, then match each to a diary hour.',
        'The Locksmith must set the dials in this order: ✶ → ☾ → ❦ → ⚱. Use the corresponding hours from the Archivist’s diary.'
    ]
    solo = room['solo']
    return {'room': {'code': room['code'] if room['mode'] == 'multiplayer' else None, 'capacity': room['capacity'], 'id': room['roomId'], 'hostId': room['hostId'], 'mode': room['mode']},
            'solo': ({'equippedAbilities': solo['equippedAbilities'][:], 'activeLens': None if solo_switch_pending(room) else solo['activeLens'], 'targetLens': solo['targetLens'], 'lensReadyAt': solo['lensReadyAt'], 'switchDurationMs': LENS_SWITCH_MS} if solo is not None else None),
            'version': room['version'], 'round': room['round'], 'phase': room['phase'],
            'me': {'id': seat['id'], 'name': seat['name'], 'roles': seat['roles'], 'primaryRole': seat['primaryRole'], 'ack': seat['ack'], 'lockedAt': seat.get('lockedAt')},
            'players': [{'id': p['id'], 'name': p['name'], 'connected': p['connected'], 'primaryRole': p['primaryRole'],
                         'roles': p['roles'], 'ready': p['ready'], 'ack': p['ack'], 'lockedAt': p.get('lockedAt')} for p in room['players']],
            'selection': {'durationMs': SELECTION_MS, 'startedAt': room['selectionStartedAt'], 'deadlineAt': room['selectionDeadlineAt']},
            'abilities': {'used': room['abilitiesUsed'], 'secondTurnArmed': room['secondTurnArmed']},
            'veilClue': ({'symbol': '✶', 'hour': next(e['hour'] for e in room['puzzle']['entries'] if e['symbol'] == '✶'), 'expiresAt': room['veilClueUntil']}
                         if room['phase'] == 'playing' and room['veilClueUntil'] and now() < room['veilClueUntil'] and
                         (room['mode'] == 'multiplayer' or (not solo_switch_pending(room) and solo['activeLens'] == 'medium')) else None),
            'timer': {**room['timer'], 'remainingMs': remaining(room), 'durationMs': duration(room)}, 'hintLevel': room['hintLevel'],
            'hints': hints[:room['hintLevel']], 'wrongAttempts': room['wrongAttempts'],
            'clues': role_clues(room, seat), 'chat': room['chat'][-40:], 'serverNow': now(),
            'solvedAt': room['solvedAt'], 'result': room['result'],
            'solutions': {'order': ORDER, 'entries': room['puzzle']['entries'], 'code': room['puzzle']['solution']}
            if room['phase'] in ('lost', 'foyer_solved', 'stage2_preview') else None}


async def send(ws, data):
    # A WebSocketResponse is falsy on older aiohttp, so compare with None.
    if ws is not None and not ws.closed:
        try:
            await ws.send_json(data)
        except (ConnectionResetError, RuntimeError):
            pass


async def broadcast(room, effect=None):
    for seat_id, ws in list(SOCKETS[room['code']].items()):
        seat = get_seat(room, seat_id)
        if seat:
            await send(ws, {'type': 'STATE', 'state': public_state(room, seat)})
    if effect:
        for ws in list(SOCKETS[room['code']].values()):
            await send(ws, {'type': 'EFFECT', 'effect': effect, 'serverNow': now()})


def character_effect(seat, role, automatic=False):
    return {'name': 'CHARACTER_LOCKED', 'character': CHARACTERS[role]['name'],
            'role': role, 'by': seat['name'], 'automatic': automatic}


async def broadcast_effect(room, effect):
    for ws in list(SOCKETS[room['code']].values()):
        await send(ws, {'type': 'EFFECT', 'effect': effect, 'serverNow': now()})


async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=60, max_msg_size=16384)
    await ws.prepare(request)
    code = None
    seat_id = None
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            packet = {}
            try:
                packet = json.loads(msg.data)
                typ = packet.get('type')
                if not isinstance(typ, str):
                    raise ValueError('Missing action type')
                # An unauthenticated readiness handshake lets the landing page
                # wait for a cold Render instance without creating a seat.
                if typ == 'HELLO' and not seat_id:
                    await send(ws, {'type': 'READY', 'serverNow': now()})
                    continue
                if typ == 'PING' and not seat_id:
                    await send(ws, {'type': 'PONG', 'serverNow': now(),
                                    'clientSentAt': packet.get('clientSentAt')})
                    continue
                if typ in ('CREATE_ROOM', 'CREATE_SOLO', 'JOIN_ROOM', 'RESUME_SEAT'):
                    if seat_id:
                        raise ValueError('Already connected to a seat')
                    ip = request.remote or 'unknown'
                    timestamp = now()
                    recent = [t for t in ADMISSION_ATTEMPTS.get(ip, []) if timestamp-t < 60000]
                    if len(recent) >= 25:
                        raise ValueError('Too many room attempts. Try again in a minute.')
                    recent.append(timestamp)
                    ADMISSION_ATTEMPTS[ip] = recent
                    if typ == 'CREATE_SOLO':
                        room = new_room('The Wanderer', 1, mode='solo')
                        seat, token = add_player(room, 'The Wanderer')
                    elif typ == 'CREATE_ROOM':
                        name = clean_name(packet.get('name'))
                        capacity = packet.get('capacity', 5)
                        if type(capacity) is not int or capacity not in (2, 3, 4, 5):
                            raise ValueError('Room capacity must be 2–5')
                        room = new_room(name, capacity)
                        seat, token = add_player(room, name)
                    else:
                        target = str(packet.get('code', '')).upper().strip()
                        room_id = str(packet.get('roomId', '')).strip()
                        if typ == 'RESUME_SEAT' and re.fullmatch(r'[a-f0-9]{32}', room_id):
                            room = next((r for r in ROOMS.values() if r['roomId'] == room_id and r['mode'] == 'solo'), None)
                        else:
                            if not re.fullmatch(r'[A-Z]{4}', target):
                                raise ValueError('Enter a valid four-letter room code')
                            room = ROOMS.get(target)
                        if not room:
                            if typ == 'RESUME_SEAT':
                                await send(ws, {'type': 'ROOM_RESET',
                                                'message': 'The spirits have reset this room. Create a new one'})
                                continue
                            raise ValueError('Room not found or expired')
                        if typ == 'RESUME_SEAT':
                            token = str(packet.get('token', ''))
                            digest = hashlib.sha256(token.encode()).hexdigest()
                            seat = next((p for p in room['players'] if secrets.compare_digest(p['tokenHash'], digest)), None)
                            if not seat:
                                raise ValueError('This seat could not be recovered on this browser')
                        else:
                            name = clean_name(packet.get('name'))
                            if room['mode'] == 'solo':
                                raise ValueError('A solo chamber cannot be joined by other players')
                            if room['phase'] != 'lobby':
                                raise ValueError('Game in progress — new players cannot join, but existing players can reconnect')
                            if len(room['players']) >= room['capacity']:
                                raise ValueError('This room is full')
                            seat, token = add_player(room, name)
                    code, seat_id = room['code'], seat['id']
                    old = SOCKETS[code].get(seat_id)
                    if old is not None and old is not ws:
                        await send(old, {'type': 'REPLACED'})
                        await old.close()
                    SOCKETS[code][seat_id] = ws
                    seat['connected'] = True
                    migrate_host(room)
                    start_selection_if_needed(room)
                    auto_assigned = auto_lock_stragglers(room)
                    if room['phase'] == 'lobby':
                        update_merged_roles(room)
                    room['version'] += 1
                    persist(room)
                    await send(ws, {'type': 'WELCOME', 'roomCode': code, 'roomId': room['roomId'], 'roomMode': room['mode'], 'seatId': seat_id, 'token': token})
                    await broadcast(room)
                    for chosen_seat, chosen_role in auto_assigned:
                        await broadcast_effect(room, character_effect(chosen_seat, chosen_role, automatic=True))
                    continue

                if not seat_id or not code:
                    raise ValueError('Join a room first')
                room = ROOMS.get(code)
                if not room:
                    raise ValueError('Room expired')
                lock = LOCKS[code]
                async with lock:
                    seat = get_seat(room, seat_id)
                    if not seat or SOCKETS[code].get(seat_id) is not ws:
                        raise ValueError('Seat no longer active')
                    if expire(room):
                        await broadcast(room, {'name': 'TIME_EXPIRED'})
                    if solo_switch_complete(room):
                        room['version'] += 1
                        await broadcast(room)
                    action_id = str(packet.get('actionId', ''))
                    if typ not in ('GET_STATE', 'PING'):
                        if not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', action_id):
                            raise ValueError('Missing unique action ID')
                        if action_id in room['seenActions']:
                            await send(ws, {'type': 'ACK', 'actionId': action_id, 'duplicate': True})
                            continue
                    effect = None
                    changed = False
                    if typ == 'GET_STATE':
                        await send(ws, {'type': 'STATE', 'state': public_state(room, seat)})
                        continue
                    elif typ == 'PING':
                        await send(ws, {'type': 'PONG', 'serverNow': now(), 'clientSentAt': packet.get('clientSentAt')})
                        continue
                    elif typ in ('LOCK_CHARACTER', 'SELECT_ROLE'):
                        if room['mode'] == 'solo':
                            raise ValueError('Choose two solo abilities instead')
                        need_phase(room, 'lobby')
                        role = str(packet.get('role', ''))
                        if role not in ROLES:
                            raise ValueError('Invalid character')
                        if seat['primaryRole']:
                            raise ValueError('You have already locked in your character')
                        if room['selectionDeadlineAt'] is not None and now() >= room['selectionDeadlineAt']:
                            raise ValueError('Selection has ended. The manor will choose for you.')
                        if any(p['id'] != seat_id and p['primaryRole'] == role for p in room['players']):
                            raise ValueError('That character has already been locked')
                        seat['primaryRole'] = role
                        seat['lockedAt'] = now()
                        seat['ready'] = False
                        update_merged_roles(room)
                        effect = character_effect(seat, role)
                        changed = True
                    elif typ == 'SET_READY':
                        if room['mode'] == 'solo':
                            raise ValueError('Solo players begin using Begin Alone')
                        need_phase(room, 'lobby')
                        if not seat['primaryRole']:
                            raise ValueError('Lock in a character first')
                        seat['ready'] = bool(packet.get('ready'))
                        changed = True
                    elif typ == 'EQUIP_SOLO_ABILITY':
                        need_phase(room, 'lobby')
                        if room['mode'] != 'solo':
                            raise ValueError('Only the solo chamber can equip powers this way')
                        role = str(packet.get('role', ''))
                        if role not in ROLES:
                            raise ValueError('Unknown ability')
                        equipped = room['solo']['equippedAbilities']
                        if role in equipped:
                            equipped.remove(role)
                        elif len(equipped) < 2:
                            equipped.append(role)
                        else:
                            raise ValueError('You may equip exactly two abilities; remove one first')
                        changed = True
                    elif typ == 'START_SOLO':
                        need_phase(room, 'lobby')
                        if room['mode'] != 'solo':
                            raise ValueError('This action is for solo chambers only')
                        if room['hostId'] != seat_id or len(room['players']) != 1:
                            raise ValueError('Invalid solo seat')
                        if len(room['solo']['equippedAbilities']) != 2:
                            raise ValueError('Choose exactly two abilities to enter alone')
                        allocate_roles(room)
                        started = now()
                        room['phase'] = 'playing'
                        room['timer'] = {'startedAt': started, 'deadlineAt': started + SOLO_DURATION_MS, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None}
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        seat['ack'] = False
                        changed = True
                        effect = {'name': 'GAME_STARTED'}
                    elif typ == 'START_GAME':
                        if room['mode'] == 'solo':
                            raise ValueError('Use Begin Alone')
                        need_phase(room, 'lobby')
                        if room['hostId'] != seat_id:
                            raise ValueError('Only the host can start')
                        if len([p for p in room['players'] if p['connected']]) < 2:
                            raise ValueError('At least two connected players are required')
                        if any(not p['connected'] for p in room['players']):
                            raise ValueError('All seats must be connected before starting')
                        if any(not p['primaryRole'] for p in room['players']):
                            raise ValueError('Every player must lock in or wait for automatic assignment')
                        if any(not p['ready'] for p in room['players']):
                            raise ValueError('Everyone must be ready before starting')
                        allocate_roles(room)
                        room['phase'] = 'playing'
                        room['timer'] = {'startedAt': now(), 'deadlineAt': now() + DURATION_MS, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None}
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        for p in room['players']:
                            p['ack'] = False
                        changed = True
                        effect = {'name': 'GAME_STARTED'}
                    elif typ == 'ACK_REVEAL':
                        need_phase(room, 'playing')
                        seat['ack'] = True
                        changed = True
                    elif typ == 'SEND_CHAT':
                        raw = str(packet.get('text', '')).strip()
                        if not raw or len(raw) > 180:
                            raise ValueError('Messages must be 1–180 characters')
                        if now() - room['lastChatAt'].get(seat_id, 0) < 700:
                            raise ValueError('Please slow down your messages')
                        room['lastChatAt'][seat_id] = now()
                        room['chat'].append({'id': secrets.token_hex(6), 'seatId': seat_id, 'name': seat['name'], 'text': raw, 'sentAt': now()})
                        room['chat'] = room['chat'][-40:]
                        changed = True
                    elif typ == 'SWITCH_LENS':
                        need_phase(room, 'playing')
                        if room['mode'] != 'solo':
                            raise ValueError('Only the solo player may use the Lens')
                        target = str(packet.get('role', ''))
                        if target not in ROLES:
                            raise ValueError('Unknown character lens')
                        if solo_switch_pending(room):
                            raise ValueError('The smoke must clear before changing Lens again')
                        if target == room['solo']['activeLens']:
                            raise ValueError('Already looking through that Lens')
                        room['solo']['targetLens'] = target
                        room['solo']['lensReadyAt'] = now() + LENS_SWITCH_MS
                        changed = True
                        effect = {'name': 'LENS_SWITCH_STARTED', 'role': target}
                        asyncio.create_task(complete_lens_after_delay(room['code'], target, room['solo']['lensReadyAt']))
                    elif typ == 'USE_ABILITY':
                        need_phase(room, 'playing')
                        role = str(packet.get('role', ''))
                        if role not in ROLES or role not in seat['roles']:
                            raise ValueError('This power does not belong to your seat')
                        if room['mode'] == 'solo':
                            if solo_switch_pending(room) or room['solo']['activeLens'] != role:
                                raise ValueError('View this character through the Lens first')
                            if role not in room['solo']['equippedAbilities']:
                                raise ValueError('This ability was not equipped for the solo trial')
                        if room['abilitiesUsed'][role]:
                            raise ValueError('This ability has already been used this game')
                        if role == 'walker':
                            raise ValueError('Sure Step awakens only in the Crypt (Stage 3)')
                        if role == 'archivist':
                            if room['hintLevel'] >= 3:
                                raise ValueError('All hints have already been revealed')
                            room['hintLevel'] += 1  # Free, but consumes the next escalating hint.
                        elif role == 'medium':
                            room['veilClueUntil'] = now() + VEIL_MS
                        elif role == 'lantern':
                            current_remaining = remaining(room)
                            room['timer']['frozenRemainingMs'] = current_remaining
                            room['timer']['freezeUntil'] = now() + FREEZE_MS
                            room['timer']['deadlineAt'] += FREEZE_MS
                        elif role == 'locksmith':
                            room['secondTurnArmed'] = True
                        room['abilitiesUsed'][role] = True
                        effect = {'name': 'ABILITY_CAST', 'role': role, 'character': CHARACTERS[role]['name'],
                                  'ability': CHARACTERS[role]['ability'], 'by': seat['name']}
                        changed = True
                    elif typ == 'REQUEST_HINT':
                        need_phase(room, 'playing')
                        if room['hintLevel'] >= 3:
                            raise ValueError('All three hints have been revealed')
                        room['hintLevel'] += 1
                        apply_penalty(room, 60000)
                        changed = True
                        effect = {'name': 'HINT', 'level': room['hintLevel']}
                    elif typ == 'SUBMIT_CLOCK_CODE':
                        need_phase(room, 'playing')
                        if 'locksmith' not in seat['roles']:
                            raise ValueError('Only the Locksmith can turn the key')
                        if room['mode'] == 'solo' and (solo_switch_pending(room) or room['solo']['activeLens'] != 'locksmith'):
                            raise ValueError('Switch to Crowe’s Lens before turning the key')
                        submitted = packet.get('hours')
                        if not isinstance(submitted, list) or len(submitted) != 4 or any(type(x) is not int or x < 1 or x > 12 for x in submitted):
                            raise ValueError('Set all four dials to hours from 1 to 12')
                        if now() - room['lastAttemptAt'] < 1800:
                            raise ValueError('Let the clock settle before another attempt')
                        room['lastAttemptAt'] = now()
                        if submitted == room['puzzle']['solution']:
                            room['phase'] = 'foyer_solved'
                            room['solvedAt'] = now()
                            room['timer']['frozenRemainingMs'] = remaining(room)
                            room['timer']['freezeUntil'] = None
                            effect = {'name': 'FOYER_SOLVED'}
                        else:
                            room['wrongAttempts'] += 1
                            if room['secondTurnArmed']:
                                room['secondTurnArmed'] = False
                                effect = {'name': 'WRONG_SHIELDED'}
                            else:
                                apply_penalty(room, 30000)
                                effect = {'name': 'WRONG_ANSWER'}
                        changed = True
                    elif typ == 'CONTINUE':
                        need_phase(room, 'foyer_solved')
                        if now() - room['solvedAt'] < 2300:
                            raise ValueError('The passage is still opening')
                        room['phase'] = 'stage2_preview'
                        if room['mode'] == 'solo':
                            score = max(0, remaining(room) // 1000)
                            room['result'] = {'outcome': 'trial_complete', 'endedAt': now(),
                                              'secondsRemaining': score, 'rank': solo_rank(score), 'leaderboard': 'solo'}
                        changed = True
                    elif typ == 'TRY_AGAIN':
                        if room['phase'] not in ('lost', 'stage2_preview'):
                            raise ValueError('Finish this round first')
                        if room['hostId'] != seat_id:
                            raise ValueError('Only the host can restart the room')
                        room['round'] += 1
                        room['phase'] = 'lobby'
                        room['puzzle'] = make_puzzle()
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        room['solvedAt'] = None
                        room['result'] = None
                        room['lastAttemptAt'] = 0
                        room['chat'] = []
                        room['timer'] = {'startedAt': None, 'deadlineAt': None, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None}
                        reset_selection(room)
                        if room['mode'] == 'solo':
                            room['players'][0]['roles'] = ROLES[:] 
                        start_selection_if_needed(room)
                        changed = True
                    elif typ == 'LEAVE_ROOM':
                        if room['mode'] == 'solo':
                            raise ValueError('Close the tab to leave the solo chamber')
                        if room['phase'] == 'lobby':
                            room['players'] = [p for p in room['players'] if p['id'] != seat_id]
                            update_merged_roles(room)
                        else:
                            seat['connected'] = False
                        if room['hostId'] == seat_id:
                            room['hostId'] = None
                        migrate_host(room)
                        changed = True
                    else:
                        raise ValueError('Unknown action: ' + typ)
                    if changed:
                        room['seenActions'].append(action_id)
                        room['seenActions'] = room['seenActions'][-250:]
                        room['version'] += 1
                        if room['phase'] == 'playing' and expire(room):
                            effect = {'name': 'TIME_EXPIRED'}
                        persist(room)
                        await broadcast(room, effect)
                        await send(ws, {'type': 'ACK', 'actionId': action_id})
                        if typ == 'LEAVE_ROOM':
                            await ws.close()
            except (ValueError, KeyError, TypeError) as exc:
                await send(ws, {'type': 'ERROR', 'message': str(exc), 'actionId': packet.get('actionId') if isinstance(packet, dict) else None})
            except Exception:
                await send(ws, {'type': 'ERROR', 'message': 'An unexpected server error occurred'})
    finally:
        if code and seat_id and code in ROOMS:
            room = ROOMS[code]
            async with LOCKS[code]:
                if SOCKETS[code].get(seat_id) is ws:
                    SOCKETS[code].pop(seat_id, None)
                    seat = get_seat(room, seat_id)
                    if seat:
                        seat['connected'] = False
                    migrate_host(room)
                    room['version'] += 1
                    persist(room)
                    await broadcast(room)
    return ws


def need_phase(room, phase):
    if room['phase'] != phase:
        raise ValueError('This action is unavailable at this stage')


def apply_penalty(room, amount):
    room['timer']['deadlineAt'] -= amount
    if room['phase'] == 'playing' and room['timer'].get('freezeUntil') and now() < room['timer']['freezeUntil']:
        room['timer']['frozenRemainingMs'] = max(0, room['timer']['frozenRemainingMs'] - amount)
    room['timer']['totalPenaltyMs'] += amount


def clean_name(value):
    name = ' '.join(str(value or '').strip().split())
    if len(name) < 1 or len(name) > 22 or '<' in name or '>' in name:
        raise ValueError('Name must be 1–22 characters')
    return name


async def complete_lens_after_delay(room_code, target, ready_at):
    """Let the real candle burn for two seconds before the new private clue is released."""
    await asyncio.sleep(max(0, (ready_at - now()) / 1000))
    if room_code not in LOCKS:
        return
    async with LOCKS[room_code]:
        room = ROOMS.get(room_code)
        if not room or room['mode'] != 'solo' or room['phase'] != 'playing':
            return
        if room['solo']['targetLens'] != target or room['solo']['lensReadyAt'] != ready_at:
            return
        if solo_switch_complete(room):
            room['version'] += 1
            persist(room)
            await broadcast(room, {'name': 'LENS_SWITCH_COMPLETE', 'role': target})


async def heartbeat(app):
    while True:
        await asyncio.sleep(2)
        for code, room in list(ROOMS.items()):
            async with LOCKS[code]:
                if expire(room):
                    await broadcast(room, {'name': 'TIME_EXPIRED'})
                if room['mode'] == 'solo' and room['phase'] == 'playing' and solo_switch_complete(room):
                    room['version'] += 1
                    persist(room)
                    await broadcast(room)
                if room['phase'] == 'lobby':
                    auto_assigned = auto_lock_stragglers(room)
                    if auto_assigned:
                        update_merged_roles(room)
                        room['version'] += 1
                        persist(room)
                        await broadcast(room)
                        for seat, role in auto_assigned:
                            await broadcast_effect(room, character_effect(seat, role, automatic=True))
                if room['phase'] == 'playing' and room['timer'].get('freezeUntil') and now() >= room['timer']['freezeUntil']:
                    room['timer']['freezeUntil'] = None
                    room['timer']['frozenRemainingMs'] = None
                    room['version'] += 1
                    await broadcast(room, {'name': 'FLAME_RESUMED'})
                if room['veilClueUntil'] and now() >= room['veilClueUntil']:
                    room['veilClueUntil'] = None
                    room['version'] += 1
                    await broadcast(room)
                for ws in list(SOCKETS[code].values()):
                    await send(ws, {'type': 'SYNC', 'serverNow': now(), 'deadlineAt': room['timer']['deadlineAt'],
                                    'frozenRemainingMs': room['timer']['frozenRemainingMs'],
                                    'freezeUntil': room['timer'].get('freezeUntil'),
                                    'selectionDeadlineAt': room['selectionDeadlineAt']})


async def index(request):
    return web.FileResponse(ROOT / 'static' / 'index.html')


async def health(request):
    return web.json_response({'status': 'ok', 'rooms': len(ROOMS)})


async def on_start(app):
    load()
    app['heartbeat_task'] = asyncio.create_task(heartbeat(app))


async def on_stop(app):
    app['heartbeat_task'].cancel()
    try:
        await app['heartbeat_task']
    except asyncio.CancelledError:
        pass


def create_app():
    instance = web.Application(client_max_size=16384)
    instance.router.add_get('/ws', ws_handler)
    instance.router.add_get('/health', health)
    instance.router.add_static('/static', ROOT / 'static')
    instance.router.add_get('/', index)
    instance.router.add_get('/room/{code}', index)
    instance.router.add_get('/solo/{roomId}', index)
    instance.on_startup.append(on_start)
    instance.on_cleanup.append(on_stop)
    return instance


app = create_app()

if __name__ == '__main__':
    web.run_app(app, port=PORT, host='0.0.0.0')
