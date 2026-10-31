"""THE LAST CANDLE — complete four-stage authoritative multiplayer/solo server.
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
import story_engine as story
import crypt_engine as crypt
import finale_engine as finale

ROOT = Path(__file__).parent
PORT = int(os.environ.get('PORT', '8080'))
SERVE_FRONTEND = os.environ.get('SERVE_FRONTEND', '1') != '0'
DURATION_MS = 20 * 60 * 1000
SOLO_DURATION_MS = 25 * 60 * 1000
LENS_SWITCH_MS = 2_000
SYMBOLS = ['☾', '✶', '⚱', '❦']
ORDER = ['✶', '☾', '❦', '⚱']
LIBRARY_SYMBOLS = ['☾', '✶', '⚱', '❦', '◇', '✧', '♜', '☿']
LIBRARY_WORDS = ['RAVEN', 'CRYPT', 'GHOST', 'SHADE', 'WITCH', 'NIGHT', 'COVEN', 'GRAVE', 'DEATH', 'FLAME']
LIBRARY_HOLD_MS = 3000
RHYTHM_BEAT_WINDOW_MS = 950
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


def permitted_web_origin(request):
    """Only the same hostname and explicitly configured Sites origins may connect.

    WebSocket CORS is not enforced by browsers, so reject unapproved Origin
    values before the server upgrades the HTTP connection.
    """
    origin = request.headers.get('Origin')
    if not origin:
        return True  # Nonbrowser health/automation clients may omit Origin.
    configured = os.environ.get('ALLOWED_WS_ORIGINS', '')
    origins = {entry.strip().rstrip('/') for entry in configured.split(',') if entry.strip()}
    # Render TLS terminates at the proxy. The public browser Origin will be https.
    origins.update({f'http://{request.host}', f'https://{request.host}'})
    return origin in origins


def now():
    return int(time.time() * 1000)


# Render Free intentionally uses ephemeral in-process room state.
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



def make_library_puzzle(seed):
    """Deterministic variant generated from the same round seed as the Foyer."""
    rng = random.Random('library:' + seed)
    word = rng.choice(LIBRARY_WORDS)
    glyphs = rng.sample(LIBRARY_SYMBOLS, 5)
    glyph_to_letter = dict(zip(glyphs, word))
    decoy_symbols = [s for s in LIBRARY_SYMBOLS if s not in glyphs]
    decoy_letters = rng.sample([c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if c not in word], 3)
    glyph_to_letter.update(zip(decoy_symbols, decoy_letters))
    wheel = list(glyph_to_letter.items())
    rng.shuffle(wheel)
    glowing = list(word)
    rng.shuffle(glowing)
    books = [{'letter': c, 'glowing': True} for c in glowing] + [
        {'letter': c, 'glowing': False} for c in decoy_letters]
    rng.shuffle(books)
    # The solo player must memorize these three timing intervals under Vesper's Lens.
    cadence = [rng.choice([1350, 1650, 1950]) for _ in range(3)]
    offsets = []
    elapsed = 1000
    for delta in cadence:
        elapsed += delta
        offsets.append(elapsed)
    return {'variantId': hashlib.sha256(seed.encode()).hexdigest()[:10], 'word': word,
            'symbols': glyphs, 'wheel': [{'symbol': sym, 'letter': letter} for sym, letter in wheel],
            'books': books, 'cadence': cadence, 'beatOffsets': offsets}


def reset_crypt(room):
    room['cryptPuzzle'] = crypt.generate(room['puzzle']['seed'])
    room['crypt'] = crypt.new_progress()


def reset_finale(room):
    room['finalePuzzle'] = finale.make(room['puzzle']['seed'])
    room['finale'] = finale.new_progress()


def reset_library(room):
    room['libraryPuzzle'] = make_library_puzzle(room['puzzle']['seed'])
    room['library'] = {'part': 'cipher', 'holds': {}, 'allHeldAt': None,
                       'cipherAttempts': 0, 'solvedAt': None,
                       'rhythm': {'active': False, 'startedAt': None, 'beatIndex': 0,
                                  'held': False, 'releasedAt': None, 'beatGlowUntil': None}}


def stage_hints(room):
    if room['stage'] == 'finale':
        return [
            'Three streams must reach three bowls. Each living player controls their own part of the yantra; alone, change Lenses to work on each stream.',
            'Tap a tile to turn it clockwise. A continuous route begins at the centre-facing lower tile and runs to the upper bowl. Every section must be connected.',
            'When the three bowls are lit, privately offer an unused equipped ability, sixty seconds of candle, or nothing. You need one meaningful offering per living player to return the yantra.'
        ]
    if room['stage'] == 'crypt':
        return [
            'Wren sees only the step beneath their feet and its four neighbors. Ask the guides for danger before you move.',
            'Ember sees traps in the left three columns; Vesper sees traps in the right three. Quill knows one safe tile. With two players, the guide carries the full trap ledger.',
            'Begin in the south-west and reach the sealed door in the north-east. Walk only north, south, east or west. A trap sends you home and costs thirty seconds; Sure Step protects one trapped tile.'
        ]
    if room['stage'] == 'library':
        return [
            'The wall speaks in symbols, Quill keeps the wheel, and Ember sees which books are awake. Compare all three before Crowe binds the word.',
            'Read Vesper’s five glyphs from left to right. Quill translates each with the torn cipher wheel. Ember’s five glowing book letters confirm the answer, even if the wheel is torn.',
            'Crowe must submit the five-letter word formed by Quill’s translations in Vesper’s order. Then each player holds a lever together for three uninterrupted seconds; alone, remember Vesper’s cadence and retrigger Crowe’s lever on all three beats.'
        ]
    return [
        'The four spirit symbols connect the portraits to the family diary. Compare the markings you each see.',
        'The scratched symbols have a precise order. Ask the Lantern-bearer to read them aloud, then match each to a diary hour.',
        'The Locksmith must set the dials in this order: ✶ → ☾ → ❦ → ⚱. Use the corresponding hours from the Archivist’s diary.'
    ]


def solve_library(room):
    story.closure(room, 'library')
    room['library']['part'] = 'solved'
    room['library']['solvedAt'] = now()
    room['phase'] = 'library_solved'
    room['solvedAt'] = now()


def reset_levers(room):
    room['library']['holds'] = {}
    room['library']['allHeldAt'] = None


def reset_rhythm(room):
    room['library']['rhythm'] = {'active': False, 'startedAt': None, 'beatIndex': 0,
                                 'held': False, 'releasedAt': None, 'beatGlowUntil': None}


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
            'veilClueUntil': None, 'stage': 'foyer',
            'timer': {'startedAt': None, 'deadlineAt': None, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None},
            'hintLevel': 0, 'wrongAttempts': 0, 'solvedAt': None, 'chat': [], 'seenActions': [],
            'lastAttemptAt': 0, 'lastChatAt': {}, 'result': None, 'story': story.new_story()}
    reset_library(room)
    reset_crypt(room)
    reset_finale(room)
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
    if timer['frozenRemainingMs'] is not None and timer.get('freezeUntil') is not None and now() < timer['freezeUntil']:
        return timer['frozenRemainingMs']
    if timer['deadlineAt'] is None:
        return duration(room)
    return max(0, timer['deadlineAt'] - now())


def expire(room):
    if room['phase'] in ('playing', 'foyer_solved', 'library_solved', 'crypt_solved', 'finale_reveal') and remaining(room) <= 0:
        room['phase'] = 'lost'
        if 'story' in room: room['story']['flags']['candleTimeAtEnd'] = 0
        room['result'] = {'outcome': 'lost', 'endedAt': now(), 'secondsRemaining': 0, 'stage': room.get('stage', 'foyer'),
                          'whisper': 'Eleanor: Even an unfinished story was worth sharing.'}
        room['timer']['frozenRemainingMs'] = 0
        room['timer']['freezeUntil'] = None
        room['version'] += 1
        persist(room)
        return True
    return False


def role_clues(room, seat):
    if room['stage'] == 'finale':
        return {}
    if room['phase'] not in ('playing', 'foyer_solved', 'library_solved', 'crypt_solved', 'stage2_preview', 'stage3_preview', 'stage4_preview', 'lost'):
        return {}
    output = {}
    permitted = seat['roles']
    if room['mode'] == 'solo':
        permitted = [] if solo_switch_pending(room) else [room['solo']['activeLens']]
    for role in permitted:
        if room['stage'] == 'crypt':
            # Every player receives only their own character-specific crypt
            # clues; no full trap layout, path or seed escapes through STATE.
            if role == 'archivist' and not crypt.can_walk(room, seat):
                output[role] = {'safeTile': list(room['cryptPuzzle']['safe']), 'message': 'An inscription gives one safe tile, counted from the upper-left.'}
            elif role == 'medium':
                output[role] = {'message': 'Your spectral sight reveals the right half of the trap ledger.'}
            elif role == 'lantern':
                output[role] = {'message': 'Your lantern reveals the left half of the trap ledger.'}
            elif role == 'walker':
                output[role] = {'message': 'You can feel the four tiles next to you. Ask your friends before stepping.'}
            else:
                output[role] = {'message': 'Watch Wren’s footsteps, and guide them away from the hands below.'}
            continue
        if room['stage'] == 'library':
            puzzle = room['libraryPuzzle']
            if role == 'medium':
                output[role] = {'symbols': puzzle['symbols'], 'cadence': puzzle['cadence'] if room['mode'] == 'solo' else None}
            elif role == 'archivist':
                output[role] = {'wheel': puzzle['wheel']}
            elif role == 'lantern':
                output[role] = {'books': puzzle['books']}
            elif role == 'locksmith':
                output[role] = {'binder': True}
            else:
                output[role] = {'message': 'The library holds a lever for each living soul. Be ready to hold yours.'}
            continue
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
    hints = stage_hints(room)
    solo = room['solo']
    return {'room': {'code': room['code'] if room['mode'] == 'multiplayer' else None, 'capacity': room['capacity'], 'id': room['roomId'], 'hostId': room['hostId'], 'mode': room['mode']},
            'solo': ({'equippedAbilities': solo['equippedAbilities'][:], 'activeLens': None if solo_switch_pending(room) else solo['activeLens'], 'targetLens': solo['targetLens'], 'lensReadyAt': solo['lensReadyAt'], 'switchDurationMs': LENS_SWITCH_MS} if solo is not None else None),
            'version': room['version'], 'round': room['round'], 'phase': room['phase'], 'stage': room.get('stage', 'foyer'),
            'library': ({'part': room['library']['part'], 'variantId': room['libraryPuzzle']['variantId'],
                         'heldSeats': list(room['library']['holds']), 'holdStartedAt': room['library']['allHeldAt'],
                         'requiredHoldMs': LIBRARY_HOLD_MS,
                         'cipherAttempts': room['library']['cipherAttempts'],
                         'rhythm': {k: v for k,v in room['library']['rhythm'].items() if k in ('active','startedAt','beatIndex','held','beatGlowUntil')}}
                         if room['stage'] == 'library' else None),
            'crypt': crypt.view(room, seat) if room['stage'] == 'crypt' else None,
            'finale': finale.view(room, seat) if room['stage'] == 'finale' else None,
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
            if room['phase'] in ('lost', 'foyer_solved', 'stage2_preview', 'library_solved', 'stage3_preview', 'crypt_solved', 'stage4_preview', 'won') else None,
            'librarySolution': ({'word': room['libraryPuzzle']['word']} if room['phase'] in ('lost','library_solved','stage3_preview','crypt_solved','stage4_preview','won') else None),
            'cryptSolution': ({'route': [list(x) for x in room['cryptPuzzle']['path']], 'traps': [list(x) for x in sorted(room['cryptPuzzle']['traps'])]}
                              if room['phase']=='lost' else None),
            'finaleSolution': (finale.solutions(room) if room['phase']=='lost' else None),
            'story': story.public_story(room, seat)}


async def send(ws, data):
    if ws and not ws.closed:
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
    if not permitted_web_origin(request):
        raise web.HTTPForbidden(text='WebSocket origin is not authorized')
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
                    if old and old is not ws:
                        await send(old, {'type': 'REPLACED'})
                        await old.close()
                    SOCKETS[code][seat_id] = ws
                    seat['connected'] = True
                    migrate_host(room)
                    if room['phase'] == 'playing' and room['stage'] != 'finale' and story.stage_ghost(room)['speakerId'] is None:
                        story.stage_ghost(room)['speakerId'] = seat['id']
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
                        room['stage'] = 'foyer'
                        room['timer'] = {'startedAt': started, 'deadlineAt': started + SOLO_DURATION_MS, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None}
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        story.enter_stage(room, 'foyer')
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
                        room['stage'] = 'foyer'
                        room['timer'] = {'startedAt': now(), 'deadlineAt': now() + DURATION_MS, 'totalPenaltyMs': 0, 'frozenRemainingMs': None, 'freezeUntil': None}
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        story.enter_stage(room, 'foyer')
                        for p in room['players']:
                            p['ack'] = False
                        changed = True
                        effect = {'name': 'GAME_STARTED'}
                    elif typ == 'ACK_REVEAL':
                        need_phase(room, 'playing')
                        seat['ack'] = True
                        changed = True
                    elif typ == 'GHOST_REPLY':
                        need_phase(room, 'playing')
                        if room['stage'] == 'finale': raise ValueError('The Goddess listens without ghost dialogue')
                        outcome = story.reply(room, seat, str(packet.get('optionId', '')))
                        effect = {'name': 'GHOST_REPLY', 'reply': outcome, 'roll': outcome.get('roll')}
                        changed = True
                    elif typ == 'HELP_SPEAKER':
                        need_phase(room, 'playing')
                        if room['stage'] == 'finale': raise ValueError('The ghost dialogue has ended')
                        story.help_speaker(room, seat)
                        effect = {'name': 'ADVANTAGE_GRANTED', 'by': seat['name']}
                        changed = True
                    elif typ == 'STEADY_BREATH':
                        need_phase(room, 'playing')
                        if room['stage'] == 'finale': raise ValueError('The offering cannot be altered by dice')
                        if room['mode'] != 'solo':
                            raise ValueError('Only a solo character can steady their breath')
                        story.effective_role(room, seat)
                        story.steady_breath(room)
                        effect = {'name': 'ADVANTAGE_GRANTED', 'by': seat['name']}
                        changed = True
                    elif typ == 'VOTE_CROSSROADS':
                        need_phase(room, 'playing')
                        if room['stage'] == 'finale': raise ValueError('The party now chooses offerings')
                        choice = str(packet.get('choice', ''))
                        outcome = story.vote(room, seat, choice)
                        if outcome and room['stage'] == 'crypt':
                            crypt.apply_shortcut(room)
                        effect = ({'name': 'CROSSROADS_RESOLVED', 'outcome': outcome,
                                   'roll': outcome.get('roll'), 'tieRoll': outcome.get('tieRoll')}
                                  if outcome else {'name': 'CROSSROADS_VOTE', 'by': seat['name']})
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
                        if room['stage'] == 'finale': raise ValueError('Unused abilities can be offered, not cast, in Kaashi')
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
                            if room['stage'] != 'crypt':
                                raise ValueError('Sure Step awakens only in the Crypt (Stage 3)')
                            if not crypt.can_walk(room, seat):
                                raise ValueError('Wren must be holding the map to use Sure Step')
                            room['crypt']['sureStepArmed'] = True
                        if room['stage'] != 'foyer' and role in ('medium','locksmith'):
                            raise ValueError('This power is available only in the Foyer')
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
                        if room['stage'] != 'foyer':
                            raise ValueError('The Foyer has already been completed')
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
                            story.closure(room, 'foyer')
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
                    elif typ == 'SUBMIT_LIBRARY_WORD':
                        need_phase(room, 'playing')
                        if room['stage'] != 'library' or room['library']['part'] != 'cipher':
                            raise ValueError('The cipher is not awaiting an answer')
                        if 'locksmith' not in seat['roles']:
                            raise ValueError('Only Crowe can bind the decoded word')
                        if room['mode'] == 'solo' and (solo_switch_pending(room) or room['solo']['activeLens'] != 'locksmith'):
                            raise ValueError('Switch to Crowe’s Lens first')
                        word = packet.get('word')
                        if not isinstance(word, str) or not re.fullmatch(r'[A-Za-z]{5}', word):
                            raise ValueError('Enter exactly five letters')
                        if now() - room['lastAttemptAt'] < 1800:
                            raise ValueError('The manuscript needs a moment to settle')
                        room['lastAttemptAt'] = now()
                        room['library']['cipherAttempts'] += 1
                        if word.upper() == room['libraryPuzzle']['word']:
                            room['library']['part'] = 'levers'
                            effect = {'name': 'LIBRARY_CIPHER_SOLVED'}
                        else:
                            room['wrongAttempts'] += 1
                            apply_penalty(room, 30000)
                            effect = {'name': 'WRONG_LIBRARY_WORD'}
                        changed = True
                    elif typ in ('LEVER_DOWN', 'LEVER_UP'):
                        need_phase(room, 'playing')
                        if room['mode'] != 'multiplayer' or room['stage'] != 'library' or room['library']['part'] != 'levers':
                            raise ValueError('The circle levers are not ready')
                        holds = room['library']['holds']
                        if typ == 'LEVER_DOWN':
                            if seat_id in holds:
                                raise ValueError('You are already holding your lever')
                            holds[seat_id] = now()
                            if len(holds) == len(room['players']) and all(p['connected'] for p in room['players']):
                                room['library']['allHeldAt'] = now()
                                asyncio.create_task(complete_levers_after_delay(room['code'], room['library']['allHeldAt']))
                            effect = {'name': 'LEVER_HELD', 'seatId': seat_id}
                        else:
                            # A release resets every lever, even if another player's hold was nearly complete.
                            reset_levers(room)
                            effect = {'name': 'LEVERS_RESET'}
                        changed = True
                    elif typ == 'START_SOLO_RHYTHM':
                        need_phase(room, 'playing')
                        if room['mode'] != 'solo' or room['stage'] != 'library' or room['library']['part'] != 'levers':
                            raise ValueError('The solo rhythm is unavailable')
                        if solo_switch_pending(room) or room['solo']['activeLens'] != 'locksmith':
                            raise ValueError('Use Crowe’s Lens to operate the rhythm lever')
                        r = room['library']['rhythm']
                        if r['active']:
                            raise ValueError('The ritual is already underway')
                        reset_rhythm(room)
                        r = room['library']['rhythm']
                        r['active'] = True
                        r['startedAt'] = now()
                        effect = {'name': 'RHYTHM_STARTED'}
                        changed = True
                        for index, offset in enumerate(room['libraryPuzzle']['beatOffsets']):
                            asyncio.create_task(send_solo_beat_after_delay(room['code'], r['startedAt'], index, offset))
                    elif typ in ('SOLO_LEVER_DOWN', 'SOLO_LEVER_UP'):
                        need_phase(room, 'playing')
                        if room['mode'] != 'solo' or room['stage'] != 'library' or room['library']['part'] != 'levers':
                            raise ValueError('The solo lever is unavailable')
                        if solo_switch_pending(room) or room['solo']['activeLens'] != 'locksmith':
                            raise ValueError('Use Crowe’s Lens to operate the lever')
                        r = room['library']['rhythm']
                        if not r['active']:
                            raise ValueError('Start the three-beat ritual first')
                        i = r['beatIndex']
                        beat_at = r['startedAt'] + room['libraryPuzzle']['beatOffsets'][i]
                        if typ == 'SOLO_LEVER_UP':
                            if not r['held'] or r['releasedAt'] is not None:
                                raise ValueError('Hold the lever before releasing on a beat')
                            if abs(now() - beat_at) > RHYTHM_BEAT_WINDOW_MS:
                                reset_rhythm(room)
                                effect = {'name': 'RHYTHM_MISSED'}
                            else:
                                r['held'] = False
                                r['releasedAt'] = now()
                                effect = {'name': 'RHYTHM_RELEASE', 'beatIndex': i}
                        else:
                            if r['held']:
                                raise ValueError('Release the lever before pressing again')
                            if r['releasedAt'] is None:
                                if i > 0 or now() >= beat_at:
                                    raise ValueError('The rhythm has already begun; start again')
                                r['held'] = True
                            elif now() - r['releasedAt'] <= RHYTHM_BEAT_WINDOW_MS:
                                r['held'] = True
                                r['releasedAt'] = None
                                r['beatIndex'] += 1
                                if r['beatIndex'] == 3:
                                    solve_library(room)
                                    effect = {'name': 'LIBRARY_SOLVED'}
                                else:
                                    effect = {'name': 'RHYTHM_BEAT_COMPLETE', 'beatIndex': r['beatIndex']}
                            else:
                                reset_rhythm(room)
                                effect = {'name': 'RHYTHM_MISSED'}
                        changed = True
                    elif typ == 'ROTATE_STREAM_TILE':
                        need_phase(room, 'playing')
                        if room['stage'] != 'finale':
                            raise ValueError('The yantra belongs only in Kaashi')
                        outcome = finale.rotate(room, seat, packet.get('section'), packet.get('tile'))
                        if outcome == 'restored':
                            story.narrate(room, 'You turn the final tile. Three bowls brighten together. Wick would clap, if fire had hands.')
                        effect = {'name': 'STREAMS_RESTORED' if outcome == 'restored' else 'STREAM_TILE_TURNED'}
                        changed = True
                    elif typ == 'SEAL_OFFERING':
                        need_phase(room, 'playing')
                        if room['stage'] != 'finale':
                            raise ValueError('Only Kaashi accepts the offering')
                        outcome = finale.submit_offering(room, seat, str(packet.get('kind', '')), packet.get('role'))
                        if outcome is not None:
                            room['phase'] = 'finale_reveal'
                            room['finale']['revealUntil'] = now() + 4200
                            story.narrate(room, 'The offerings open together. The Goddess judges the giving, not the grandeur.')
                            asyncio.create_task(finish_finale_after_delay(room['code'], room['finale']['revealUntil']))
                            effect = {'name': 'OFFERINGS_REVEALED', 'accepted': outcome}
                        else:
                            effect = {'name': 'OFFERING_SEALED', 'seatId': seat_id}
                        changed = True
                    elif typ == 'CRYPT_MOVE':
                        need_phase(room, 'playing')
                        if room['stage'] != 'crypt':
                            raise ValueError('The crypt is not open yet')
                        outcome = crypt.advance(room, seat, str(packet.get('direction', '')).lower(), now(), apply_penalty)
                        if outcome == 'solved':
                            story.closure(room, 'crypt')
                            room['phase'] = 'crypt_solved'
                            room['solvedAt'] = room['crypt']['solvedAt']
                            effect = {'name': 'CRYPT_SOLVED'}
                        elif outcome == 'trap':
                            story.narrate(room, 'You take one step. A skeletal hand shakes yours. Thirty seconds vanish, and the crypt sends you back to the entrance.')
                            effect = {'name': 'CRYPT_TRAP', 'position': room['crypt']['recentTrap']['tile']}
                        elif outcome == 'protected':
                            story.narrate(room, 'You hear the hands below. Wren simply steps over them. How unsettlingly professional.')
                            effect = {'name': 'CRYPT_SURE_STEP'}
                        else:
                            effect = {'name': 'CRYPT_STEP'}
                        changed = True
                    elif typ == 'CONTINUE_CRYPT':
                        need_phase(room, 'crypt_solved')
                        if now() - room['crypt']['solvedAt'] < 2900:
                            raise ValueError('The sealed door is still answering the candle')
                        room['phase'] = 'playing'
                        room['stage'] = 'finale'
                        room['finale']['enteredAt'] = now()
                        room['hintLevel'] = 0
                        room['solvedAt'] = None
                        story.narrate(room, 'The manor falls away. You stand beneath Kaashi before a sacred light. Do not mistake reverence for terror.')
                        effect = {'name': 'FINALE_ENTERED'}
                        changed = True
                    elif typ == 'CONTINUE_LIBRARY':
                        need_phase(room, 'library_solved')
                        if now() - room['library']['solvedAt'] < 3500:
                            raise ValueError('The bookshelf is still opening')
                        room['phase'] = 'playing'
                        room['stage'] = 'crypt'
                        room['solvedAt'] = None
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        story.enter_stage(room, 'crypt')
                        changed = True
                        effect = {'name': 'CRYPT_ENTERED'}
                    elif typ == 'CONTINUE':
                        need_phase(room, 'foyer_solved')
                        if now() - room['solvedAt'] < 2300:
                            raise ValueError('The passage is still opening')
                        room['phase'] = 'playing'
                        room['stage'] = 'library'
                        story.enter_stage(room, 'library')
                        room['hintLevel'] = 0
                        room['wrongAttempts'] = 0
                        room['lastAttemptAt'] = 0
                        # The candle burns continuously through the door reveal; only
                        # Ember's explicitly approved 20-second ability can freeze it.
                        room['solvedAt'] = None
                        changed = True
                        effect = {'name': 'LIBRARY_ENTERED'}
                    elif typ == 'TRY_AGAIN':
                        if room['phase'] not in ('lost', 'won', 'playing', 'stage3_preview', 'stage4_preview'):
                            raise ValueError('Finish this round first')
                        if room['phase'] == 'playing' and room['stage'] != 'crypt':
                            raise ValueError('Finish this round first')
                        if room['hostId'] != seat_id:
                            raise ValueError('Only the host can restart the room')
                        room['round'] += 1
                        room['phase'] = 'lobby'
                        room['puzzle'] = make_puzzle()
                        room['stage'] = 'foyer'
                        reset_library(room)
                        reset_crypt(room)
                        reset_finale(room)
                        room['story'] = story.new_story()
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
                        if room['phase'] == 'playing' and room['stage'] != 'finale' and room['story']['ghosts'][room['stage']]['coldUntil'] is not None:
                            cold_at = room['story']['ghosts'][room['stage']]['coldUntil']
                            asyncio.create_task(return_cold_ghost_after_delay(room['code'], room['stage'], cold_at))
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
                    if room['phase'] == 'playing' and room['stage'] != 'finale':
                        ghost = story.stage_ghost(room)
                        if ghost['speakerId'] == seat_id and not ghost['closed']:
                            story.advance_speaker(room)
                    if room['stage'] == 'library' and room['phase'] == 'playing' and room['library']['part'] == 'levers':
                        reset_levers(room)
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


async def complete_levers_after_delay(room_code, held_at):
    await asyncio.sleep(LIBRARY_HOLD_MS / 1000)
    if room_code not in LOCKS:
        return
    async with LOCKS[room_code]:
        room = ROOMS.get(room_code)
        if not room or room['phase'] != 'playing' or room['stage'] != 'library' or room['library']['part'] != 'levers':
            return
        if room['library']['allHeldAt'] != held_at or now() - held_at < LIBRARY_HOLD_MS - 30:
            return
        if len(room['library']['holds']) != len(room['players']) or any(not p['connected'] for p in room['players']):
            reset_levers(room)
            room['version'] += 1
            await broadcast(room, {'name': 'LEVERS_RESET'})
            return
        solve_library(room)
        room['version'] += 1
        persist(room)
        await broadcast(room, {'name': 'LIBRARY_SOLVED'})


async def send_solo_beat_after_delay(room_code, started_at, index, offset):
    await asyncio.sleep(offset / 1000)
    if room_code not in LOCKS:
        return
    async with LOCKS[room_code]:
        room = ROOMS.get(room_code)
        if not room or room['phase'] != 'playing' or room['stage'] != 'library':
            return
        r = room['library']['rhythm']
        if not r['active'] or r['startedAt'] != started_at:
            return
        if r['beatIndex'] != index:
            reset_rhythm(room)
            room['version'] += 1
            await broadcast(room, {'name': 'RHYTHM_MISSED'})
            return
        r['beatGlowUntil'] = now() + RHYTHM_BEAT_WINDOW_MS
        room['version'] += 1
        await broadcast(room, {'name': 'RHYTHM_BEAT', 'beatIndex': index})


async def return_cold_ghost_after_delay(code, stage, expected_until):
    await asyncio.sleep(max(0, (expected_until - now()) / 1000))
    if code not in ROOMS:
        return
    async with LOCKS[code]:
        room = ROOMS.get(code)
        if not room or room['stage'] != stage:
            return
        ghost = room['story']['ghosts'][stage]
        if ghost['coldUntil'] != expected_until:
            return
        if story.recover_cold(room):
            room['version'] += 1
            persist(room)
            await broadcast(room, {'name': 'GHOST_RETURNED'})


async def finish_finale_after_delay(code, deadline):
    await asyncio.sleep(max(0, (deadline - now()) / 1000))
    if code not in ROOMS:
        return
    async with LOCKS[code]:
        room = ROOMS.get(code)
        if not room or room['phase'] != 'finale_reveal' or room['finale']['revealUntil'] != deadline:
            return
        accepted = finale.finish_offer(room, apply_penalty)
        if expire(room):
            await broadcast(room, {'name': 'TIME_EXPIRED'})
            return
        if accepted:
            score = max(0, remaining(room) // 1000)
            flags = room['story']['flags']
            flags['candleTimeAtEnd'] = score
            room['phase'] = 'won'
            room['solvedAt'] = now()
            room['finale']['completedAt'] = now()
            room['result'] = {'outcome': 'won', 'secondsRemaining': score, 'endedAt': now(),
                              'rank': solo_rank(score) if room['mode']=='solo' else rank(score),
                              'leaderboard': room['mode'],
                              'players': [{'name': p['name'], 'characters': [CHARACTERS[r]['name'] for r in p['roles']]} for p in room['players']],
                              'abilitiesUsed': [CHARACTERS[r]['ability'] for r in ROLES if room['abilitiesUsed'][r]],
                              'funStat': {'label': 'Crypt traps shaken off', 'value': room['crypt']['trapHits']},
                              'storyFlags': {'items': flags['items'][:], 'crits': flags['crits'], 'fumbles': flags['fumbles'],
                                             'votesTaken': flags['votesTaken'], 'WRONG_TURN': flags['WRONG_TURN']},
                              'eleanor': 'The dawn is warm. You may carry us forward now.'}
            story.narrate(room, 'The yantra returns to its shrine. At dawn Eleanor smiles, finally lighter than the morning.')
        else:
            room['phase'] = 'playing'
            story.narrate(room, 'The shrine waits. Nothing given is no offering at all. Two minutes leave the candle; the bowls remain lit.')
        room['version'] += 1
        persist(room)
        await broadcast(room, {'name': 'FINALE_WON' if accepted else 'OFFERINGS_RETRY'})


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
                if room['phase'] in ('playing', 'foyer_solved', 'library_solved', 'crypt_solved', 'finale_reveal') and room['timer'].get('freezeUntil') and now() >= room['timer']['freezeUntil']:
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
    response = web.json_response({'status': 'ok', 'rooms': len(ROOMS), 'release': 'stage-4-complete', 'chapters': 4})
    if permitted_web_origin(request) and request.headers.get('Origin'):
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        response.headers['Vary'] = 'Origin'
    return response


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
    if SERVE_FRONTEND:
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
