"""Stage 4: server-authoritative, turnable three-stream yantra and sealed trust offerings.

The Kaashi setting is isolated to the finale. Tile targets and private offerings
never enter public per-seat STATE before the relevant reveal.
"""
import random

ROLE_STREAM = {'medium': 0, 'archivist': 1, 'lantern': 2}
DIRECTIONS = ('N', 'E', 'S', 'W')
OPPOSITE = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}
DELTAS = {'N': (-1, 0), 'E': (0, 1), 'S': (1, 0), 'W': (0, -1)}
VARIANTS = (
    ((2, 1), (2, 0), (1, 0), (0, 0), (0, 1)),
    ((2, 1), (2, 2), (1, 2), (0, 2), (0, 1)),
    ((2, 1), (1, 1), (1, 0), (0, 0), (0, 1)),
    ((2, 1), (1, 1), (1, 2), (0, 2), (0, 1)),
)


def direction(a, b):
    diff = (b[0] - a[0], b[1] - a[1])
    return next(k for k, v in DELTAS.items() if v == diff)


def rotate_ports(ports, count):
    return tuple(DIRECTIONS[(DIRECTIONS.index(p) + count) % 4] for p in ports)


def make(seed):
    rng = random.Random('kaashi:' + str(seed))
    sections = []
    for section_index in range(3):
        route = rng.choice(VARIANTS)
        path = []
        for index, location in enumerate(route):
            entering = 'S' if index == 0 else OPPOSITE[direction(route[index-1], location)]
            leaving = 'N' if index == len(route)-1 else direction(location, route[index+1])
            ports = (entering, leaving)
            # The identity and piece geometry is randomized per section.
            offset = rng.randrange(4)
            initial = rotate_ports(ports, offset)
            path.append({'at': location, 'base': initial, 'rotation': 0, 'target': (-offset) % 4})
        section = {'path': path, 'route': route, 'connected': False}
        if section_connected(section):
            section['path'][0]['rotation'] = 1  # Always start needing restoration.
        sections.append(section)
    # Ensure the entrance is never fully solved accidentally.
    if all(section_connected(s) for s in sections):
        sections[0]['path'][2]['rotation'] = 1
        sections[0]['connected'] = False
    return {'sections': sections, 'seedId': str(seed)[:8]}


def section_connected(section):
    path = section['path']
    for i, tile in enumerate(path):
        previous = 'S' if i == 0 else OPPOSITE[direction(section['route'][i-1], section['route'][i])]
        following = 'N' if i == len(path)-1 else direction(section['route'][i], section['route'][i+1])
        if set(rotate_ports(tile['base'], tile['rotation'])) != {previous, following}:
            return False
    return True


def new_progress():
    return {'part': 'streams', 'rotations': 0, 'offerings': {}, 'offerRound': 1,
            'reveal': None, 'revealUntil': None, 'completedAt': None}


def owned_sections(room, seat):
    if room['mode'] == 'solo':
        solo = room['solo']
        if solo['targetLens'] is not None:
            return []
        i = ROLE_STREAM.get(solo['activeLens'])
        return [i] if i is not None else []
    index = next((i for i, p in enumerate(room['players']) if p['id'] == seat['id']), None)
    if index is None:
        return []
    if len(room['players']) <= 3:
        return [i for i in range(3) if i % len(room['players']) == index]
    # Four- and five-person circles share one of the three sacred streams:
    # every player participates, with concurrent, server-broadcast rotations.
    return [index % 3]


def view(room, seat):
    puzzle, progress = room['finalePuzzle'], room['finale']
    sections = []
    allowed = owned_sections(room, seat)
    for i, section in enumerate(puzzle['sections']):
        item = {'id': i, 'connected': section['connected'], 'owned': i in allowed}
        if i in allowed and progress['part'] == 'streams':
            item['tiles'] = [{'row': p['at'][0], 'col': p['at'][1],
                              'ports': list(rotate_ports(p['base'], p['rotation'])),
                              'index': j} for j, p in enumerate(section['path'])]
        sections.append(item)
    offers = progress['offerings']
    can_offer = []
    if progress['part'] == 'offering':
        can_offer = [r for r in seat['roles'] if not room['abilitiesUsed'][r]
                     and (room['mode'] != 'solo' or r in room['solo']['equippedAbilities'])]
    return {'part': progress['part'], 'sections': sections, 'rotations': progress['rotations'],
            'offeredSeats': list(offers.keys()), 'myOffer': offers.get(seat['id']),
            'canOfferAbilities': can_offer, 'offerRound': progress['offerRound'],
            'threshold': 1 if room['mode'] == 'solo' else len(room['players']),
            'reveal': progress['reveal'], 'revealUntil': progress['revealUntil'],
            'enteredAt': progress.get('enteredAt')}


def rotate(room, seat, section_id, tile_index):
    progress = room['finale']
    if progress['part'] != 'streams':
        raise ValueError('The streams have already been restored')
    if type(section_id) is not int or section_id not in owned_sections(room, seat):
        raise ValueError('This stream belongs to another Lens or player')
    if type(tile_index) is not int or not 0 <= tile_index < 5:
        raise ValueError('Choose a valid yantra tile')
    section = room['finalePuzzle']['sections'][section_id]
    section['path'][tile_index]['rotation'] = (section['path'][tile_index]['rotation'] + 1) % 4
    section['connected'] = section_connected(section)
    progress['rotations'] += 1
    if all(s['connected'] for s in room['finalePuzzle']['sections']):
        progress['part'] = 'offering'
        return 'restored'
    return 'rotated'


def submit_offering(room, seat, kind, role=None):
    progress = room['finale']
    if progress['part'] != 'offering':
        raise ValueError('Offerings are not open')
    if seat['id'] in progress['offerings']:
        raise ValueError('Your offering is already sealed')
    if kind not in ('ability', 'candle', 'nothing'):
        raise ValueError('Choose an unused ability, sixty seconds, or nothing')
    if kind == 'ability':
        permitted = [r for r in seat['roles'] if not room['abilitiesUsed'][r]
                     and (room['mode'] != 'solo' or r in room['solo']['equippedAbilities'])]
        if role not in permitted:
            raise ValueError('Only an unused ability you own can be offered')
    progress['offerings'][seat['id']] = {'kind': kind, 'role': role if kind == 'ability' else None}
    if len(progress['offerings']) != len(room['players']):
        return None
    threshold = 1 if room['mode'] == 'solo' else len(room['players'])
    total = sum(offer['kind'] != 'nothing' for offer in progress['offerings'].values())
    accepted = total >= threshold
    reveal = [{'seatId': p['id'], 'name': p['name'], **progress['offerings'][p['id']]}
              for p in room['players']]
    progress['reveal'] = {'offers': reveal, 'total': total, 'threshold': threshold, 'accepted': accepted}
    progress['part'] = 'reveal'
    return accepted


def finish_offer(room, penalty):
    progress = room['finale']
    if progress['part'] != 'reveal' or not progress['reveal']:
        raise ValueError('Nothing has been revealed')
    accepted = progress['reveal']['accepted']
    if accepted:
        for offer in progress['offerings'].values():
            if offer['kind'] == 'ability':
                room['abilitiesUsed'][offer['role']] = True
            elif offer['kind'] == 'candle':
                penalty(room, 60_000)
        progress['part'] = 'complete'
    else:
        penalty(room, 120_000)
        progress['offerRound'] += 1
        progress['offerings'] = {}
        progress['part'] = 'offering'
    return accepted


def solutions(room):
    return [{'section': i, 'route': [list(t) for t in sec['route']],
             'rotations': [p['target'] for p in sec['path']]}
            for i, sec in enumerate(room['finalePuzzle']['sections'])]
