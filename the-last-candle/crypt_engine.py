"""Stage 3: server-owned, asymmetric six-by-six maze at Hollow Manor.

Never emit the complete puzzle, route or trap layout in a player STATE.
"""
import random

SIZE = 6
START = (5, 0)
EXIT = (0, 5)
TRAP_COUNT = 8
DIRECTIONS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}


def generate(seed):
    rng = random.Random('crypt:' + str(seed))
    # Ten randomized, cardinal steps guarantee a connected path from the
    # south-west entrance to the north-east sealed door.
    steps = [DIRECTIONS['up']] * 5 + [DIRECTIONS['right']] * 5
    rng.shuffle(steps)
    route = [START]
    y, x = START
    for dy, dx in steps:
        y, x = y + dy, x + dx
        route.append((y, x))
    assert route[-1] == EXIT and len(set(route)) == len(route)
    candidates = [(row, col) for row in range(SIZE) for col in range(SIZE) if (row, col) not in route]
    traps = rng.sample(candidates, TRAP_COUNT)
    # One separately held piece of Quill's knowledge, neither start nor exit.
    safe = route[rng.choice([2, 3, 4, 5, 6, 7, 8])]
    return {'start': START, 'exit': EXIT, 'path': route, 'traps': set(traps), 'safe': safe,
            'variantId': ''.join(hex(ord(c) % 16)[2:] for c in str(seed))[:10]}


def new_progress():
    return {'position': START, 'steps': 0, 'trapHits': 0, 'sureStepArmed': False,
            'sureStepUsed': False, 'recentTrap': None, 'lastMoveAt': 0,
            'solvedAt': None, 'shortcutApplied': False}


def neighbors(pos):
    y, x = pos
    return [(r, c) for r in range(SIZE) for c in range(SIZE) if abs(r-y)+abs(c-x) <= 1]


def can_walk(room, seat):
    if room['mode'] == 'solo':
        return room['solo']['targetLens'] is None and room['solo']['activeLens'] == 'walker'
    return 'walker' in seat['roles']


def view(room, seat):
    """Sanitized per-seat view. Wren never receives remote traps."""
    puzzle, progress = room['cryptPuzzle'], room['crypt']
    position = progress['position']
    visible = neighbors(position)
    actor = can_walk(room, seat)
    lens = room['solo']['activeLens'] if room['mode'] == 'solo' else None
    switching = room['mode'] == 'solo' and room['solo']['targetLens'] is not None
    guide = room['mode'] == 'multiplayer' and not actor
    seats = len(room['players'])
    roles = [lens] if room['mode'] == 'solo' else seat['roles']
    known = set()
    if not switching and not actor:
        if guide and seats == 2:
            known = puzzle['traps'].copy()
        else:
            if 'lantern' in roles:
                known.update(p for p in puzzle['traps'] if p[1] < SIZE//2)
            if 'medium' in roles:
                known.update(p for p in puzzle['traps'] if p[1] >= SIZE//2)
    safe = puzzle['safe'] if not switching and not actor and 'archivist' in roles else None
    # Fog hides distant outlines. Guides still receive a private coordinate
    # ledger (the trap list) to communicate verbally with Wren.
    return {
        'size': SIZE, 'position': list(position), 'start': list(START),
        'visible': [list(p) for p in visible],
        'knownTraps': [list(p) for p in sorted(known)],
        'safeTile': list(safe) if safe else None,
        'canMove': actor and not switching,
        'canGuide': not actor and not switching,
        'exitVisible': EXIT in visible or (room['mode']=='solo' and not actor and not switching),
        'steps': progress['steps'], 'trapHits': progress['trapHits'],
        'sureStepArmed': progress['sureStepArmed'], 'sureStepUsed': progress['sureStepUsed'],
        'recentTrap': progress['recentTrap'], 'variantId': puzzle['variantId'],
        'shortcutApplied': progress['shortcutApplied'],
    }


def advance(room, seat, direction, now_ms, penalty):
    if direction not in DIRECTIONS:
        raise ValueError('Move using the four cardinal directions')
    if not can_walk(room, seat):
        raise ValueError('Only Wren can move. Solo: switch to Wren’s Lens first')
    progress, puzzle = room['crypt'], room['cryptPuzzle']
    if now_ms - progress['lastMoveAt'] < 140:
        raise ValueError('The stone needs a heartbeat before the next step')
    dy, dx = DIRECTIONS[direction]
    y, x = progress['position']
    ny, nx = y + dy, x + dx
    if not (0 <= ny < SIZE and 0 <= nx < SIZE):
        raise ValueError('A crypt wall blocks that way')
    progress['lastMoveAt'] = now_ms
    progress['steps'] += 1
    target = (ny, nx)
    progress['recentTrap'] = None
    if target in puzzle['traps']:
        if progress['sureStepArmed']:
            progress['sureStepArmed'] = False
            progress['sureStepUsed'] = True
            progress['position'] = target
            return 'protected'
        progress['trapHits'] += 1
        progress['recentTrap'] = {'tile': list(target), 'at': now_ms}
        progress['position'] = START
        penalty(room, 30_000)
        return 'trap'
    progress['position'] = target
    if target == EXIT:
        progress['solvedAt'] = now_ms
        return 'solved'
    return 'moved'


def apply_shortcut(room):
    """A successful Reginald roll skips about half the guaranteed route."""
    progress = room['crypt']
    if not room['story']['flags']['shortCut'] or progress['shortcutApplied'] or progress['steps'] or progress['position'] != START:
        return False
    progress['position'] = room['cryptPuzzle']['path'][len(room['cryptPuzzle']['path'])//2]
    progress['shortcutApplied'] = True
    return True
