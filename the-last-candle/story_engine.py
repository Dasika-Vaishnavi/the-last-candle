"""Authoritative, testable story/ghost/RPG rules for THE LAST CANDLE.
No client-supplied dice, damage, warmth, speaker identity or vote totals are trusted.
"""
from __future__ import annotations
import random
import secrets
import time

ROLES = ('medium', 'archivist', 'lantern', 'locksmith', 'walker')
STATS = {
    'medium': {'CHARM': 2, 'WITS': 0, 'NERVE': 1},
    'archivist': {'CHARM': 1, 'WITS': 2, 'NERVE': 0},
    'lantern': {'CHARM': 0, 'WITS': 1, 'NERVE': 2},
    'locksmith': {'CHARM': 0, 'WITS': 2, 'NERVE': 1},
    'walker': {'CHARM': 1, 'WITS': 0, 'NERVE': 2},
}
GHOSTS = {
    'foyer': {
        'name': 'Horace Tock', 'job': 'clockmaker · deceased 1871',
        'personality': 'Fussy, anxious and incapable of resisting a punctuality pun.',
        'unfinishedBusiness': 'Let the grandfather clock tick again and forgive himself for the passage of time.',
        'sorrow': 'He stopped the clock for each Hollow death because time continuing felt like betrayal.',
        'intro': "Oh! Visitors. You're early. Or I'm late. I've been on time since 1871, so it's hard to tell.",
        'goodbye': "There it goes. Tick, tick... I suppose carrying them forward isn't the same as leaving them behind. Thank you for the time.",
        'replies': [
            ('You look terribly punctual. It suits you.', 'Did the clock keep their memories?', 'Can you hurry up?'),
            ('[CHARM 12] Compliment his lovely spectacles.', 'I think missing someone is its own kind of time.', 'Is this a clock or a guilt collection?'),
            ('I bet your heart still ticks for them.', '[WITS 12] Ask which hour the moon watched.', 'Why are you still here?'),
            ('Then perhaps we can start it again.', 'Would they want you to be lonely forever?', 'Well, that took long enough.'),
        ],
        'responses': [
            ("Punctuality is a difficult hobby when you have no pulse.", "I stopped the clock when they left. I was hoping the world would take the hint.", "Rushing a deceased professional? Well, that takes the biscuit."),
            ("They were father's spectacles. I kept them because I liked seeing what he saw.", "I wrote every hour down, though I could barely look at the hands.", "The clock never charged a fee for listening, unlike you."),
            ("Time does not stop hurting, but it does get better at carrying things.", "The moon saw the first farewell, if my memory serves.", "Please don't make grief another appointment."),
            ("Perhaps I can let the old girl tick again.", "You know, I suspect they would want me to carry on.", "My goodness. Even death has a queue now."),
        ],
        'fragments': [
            "Horace murmurs: 'The moon ☾ watched the first farewell. Look for it in the diary.'",
            "Horace points toward ✶. 'Stars before moons, dear. That's how she scratched the clock.'",
            "Horace admits: 'The clock stopped for each of them, but their hours were different. Ask Quill.'",
        ],
    },
    'library': {
        'name': 'Prudence Page', 'job': 'librarian · overdue since 1889',
        'personality': 'Prickly, witty and fiercely protective of every unread sentence.',
        'unfinishedBusiness': 'Have somebody read the letter she tucked away.',
        'sorrow': 'Her final letter stayed unread between two books.',
        'intro': "Shh. The books have been crying again. Do you know how hard it is to reshelve a sob?",
        'goodbye': "Oh. Someone finally read the page I left behind. It wasn't a fine I wanted. Just a reader. Go on, dear.",
        'replies': [
            ('Your shelves are very... emotionally organized.', 'Who wrote the unread letter?', 'Your fines are a little excessive.'),
            ('[CHARM 12] Tell her her books are beautiful.', 'I think a story can outlive its writer.', 'Could you stop shushing us?'),
            ('Which five letters keep wandering?', '[WITS 12] Ask about the glowing spines.', 'Why not burn the whole place?'),
            ('We will carry your story.', 'You are allowed to be finished.', 'We are literally on a timer.'),
        ],
        'responses': [
            ("The alphabetical section is very nearly sorted by heartache.", "She wrote, 'I will come back tomorrow.' There was no tomorrow.", "I can charge interest in sighs, you know."),
            ("Flattery is a book I haven't checked out in years.", "Sometimes the end of a story is a way of staying.", "My shush is a certified library instrument."),
            ("Five letters. I keep losing one every time the shelves sneeze.", "The illuminated spines are not shy, only selective.", "Book burning? In this economy?"),
            ("Take the story. Leave me the peace and quiet.", "Perhaps being read is enough.", "Twenty minutes? The late fee is astronomical."),
        ],
        'fragments': [
            "Prudence whispers: 'Five symbols. Five letters. Not all the books deserve your eyes.'",
            "A book bows open: 'The glowing spines are the only trustworthy witnesses.'",
            "Prudence taps the lever rail: 'Together. Three slow breaths. Nobody let go.'",
        ],
    },
    'crypt': {
        'name': 'Sir Reginald Rattle', 'job': 'knight · last seen 1882',
        'personality': 'An overconfident, deeply apologetic navigator.',
        'unfinishedBusiness': 'Finally guide a living traveler along a safe path.',
        'sorrow': 'He promised to guide his friend home and chose the wrong tunnel.',
        'intro': "I know a shortcut! I also know several long cuts, but we don't discuss those.",
        'goodbye': "The right road wasn't mine to order. Thank you for letting me walk beside you.",
        'replies': [('Your armor has character.', 'Who did you lose?', 'Do you always misdirect?')],
        'fragments': ["Reginald offers a hesitant map fragment. 'Slow paths are sometimes the kind ones.'"],
    },
    'seance': {
        'name': 'Eleanor Hollow', 'job': 'keeper of the manor · gone 1893',
        'personality': 'Commanding, lonely and terrified of letting go.',
        'unfinishedBusiness': 'Release her family and allow the stolen yantra to return home.',
        'sorrow': 'She thought trapping a moment could preserve a family.',
        'intro': "You came to call the dead. You forgot to ask whether we wanted company.",
        'goodbye': "Then let the last candle show the way out, rather than hold you here.",
        'replies': [('We are listening.', 'What is your true name?', 'This is rather inconvenient.')],
        'fragments': ["Eleanor remembers a name she hasn't spoken in years."],
    },
}
CHOICES = {
    'foyer': [
        {'id': 'watch', 'label': 'Pry the golden pocket watch out', 'stat': 'WITS', 'dc': 13},
        {'id': 'leave', 'label': 'Leave the watch with Horace', 'stat': None, 'dc': None},
    ],
    'library': [
        {'id': 'pay', 'label': 'Pay the overdue fine: 30 seconds', 'stat': None, 'dc': None},
        {'id': 'argue', 'label': 'Argue kindly about the fine', 'stat': 'CHARM', 'dc': 14},
        {'id': 'sneak', 'label': 'Sneak the book out', 'stat': 'NERVE', 'dc': 13},
    ],
    'crypt': [
        {'id': 'trust', 'label': 'Trust Reginald’s shortcut', 'stat': 'NERVE', 'dc': 15},
        {'id': 'map', 'label': 'Map the careful path', 'stat': None, 'dc': None},
    ],
}


def timestamp():
    return int(time.time() * 1000)


def new_story():
    return {
        'ghosts': {stage: {'warmth': 1, 'coldUntil': None, 'coldCount': 0,
                           'exchange': 0, 'speakerId': None, 'history': [],
                           'fragments': [], 'closed': False, 'goodbye': None,
                           'finished': False, 'helpBy': None, 'skippedSeats': [],
                           'pendingAdvantage': False, 'rollsUsed': 0,
                           'votes': {}, 'crossroads': None}
                   for stage in GHOSTS},
        'flags': {'items': [], 'WRONG_TURN': False, 'shortCut': False,
                  'crits': 0, 'fumbles': 0, 'votesTaken': 0, 'diceRolls': 0,
                  'candleTimeAtEnd': None},
        'wick': {'text': 'You light the candle. It has opinions.', 'at': timestamp()},
        'lastRoll': None,
    }


def enter_stage(room, stage):
    ghost = room['story']['ghosts'][stage]
    ghost['speakerId'] = next((p['id'] for p in room['players'] if p['connected']), None)
    messages = {
        'foyer': 'You open the door. It opens back. Rude. A clockmaker floats in to complain about the hour.',
        'library': 'You enter the library. The books have reorganized themselves by how much they dislike you.',
        'crypt': 'You descend into the Crypt. Your footsteps sound expensive.',
        'seance': 'You enter the séance chamber. The candle wishes it had taken the evening off.',
    }
    narrate(room, messages[stage])


def narrate(room, text):
    room['story']['wick'] = {'text': text, 'at': timestamp()}


def stage_ghost(room):
    return room['story']['ghosts'][room['stage']]


def effective_role(room, seat):
    if room['mode'] == 'solo':
        if room['solo']['targetLens'] is not None:
            raise ValueError('The smoke must clear before acting')
        return room['solo']['activeLens']
    return seat['primaryRole'] or (seat['roles'][0] if seat['roles'] else 'medium')


def options(room, seat):
    stage = room['stage']
    ghost = stage_ghost(room)
    if ghost['closed'] or ghost['finished'] or ghost['coldUntil'] is not None:
        return []
    if ghost['exchange'] >= len(GHOSTS[stage]['replies']):
        return []
    role = effective_role(room, seat) if room['mode'] != 'solo' or room['solo']['targetLens'] is None else None
    if not role:
        return []
    # Each seat (and each solo Lens) gets a distinct, original phrasing of the
    # same underlying intentions. The server never accepts client-written text.
    basis = GHOSTS[stage]['replies'][ghost['exchange']]
    role_flavor = {
        'medium': '✦', 'archivist': '✶', 'lantern': '✧',
        'locksmith': '⚿', 'walker': '◇',
    }[role]
    descriptors = {
        'medium': ('Whisper', 'Listen', 'Interrupt'),
        'archivist': ('Remember', 'Research', 'Question'),
        'lantern': ('Encourage', 'Illuminate', 'Dismiss'),
        'locksmith': ('Offer', 'Inspect', 'Joke'),
        'walker': ('Steady', 'Wonder', 'Rush'),
    }[role]
    out = []
    for i, phrase in enumerate(basis):
        stat = None
        dc = None
        if phrase.startswith('['):
            spec, phrase = phrase.split('] ', 1)
            stat, dc = spec[1:].split(' ')
            dc = int(dc)
        out.append({'id': f'{stage}:{ghost["exchange"]}:{role}:{i}', 'label': f'{role_flavor} {descriptors[i]}: {phrase}',
                    'stat': stat, 'dc': dc, 'tone': ('kind', 'curious', 'rude')[i]})
    return out


def advance_speaker(room):
    ghost = stage_ghost(room)
    eligible = [p['id'] for p in room['players'] if p['connected']]
    if not eligible:
        ghost['speakerId'] = None
        return
    old = ghost['speakerId']
    index = eligible.index(old) if old in eligible else -1
    for step in range(1, len(eligible) + 2):
        seat = eligible[(index + step) % len(eligible)]
        if seat in ghost['skippedSeats']:
            ghost['skippedSeats'].remove(seat)
            continue
        ghost['speakerId'] = seat
        return
    ghost['speakerId'] = eligible[0]


def roll_d20():
    return secrets.randbelow(20) + 1


def charge_candle(room, milliseconds):
    """Account for story penalties just like puzzle penalties, including Ember's freeze."""
    timer = room['timer']
    timer['deadlineAt'] -= milliseconds
    if timer.get('freezeUntil') and timestamp() < timer['freezeUntil'] and timer.get('frozenRemainingMs') is not None:
        timer['frozenRemainingMs'] = max(0, timer['frozenRemainingMs'] - milliseconds)
    timer['totalPenaltyMs'] += milliseconds


def skill_check(room, seat, stat, dc, *, advantage=False, context='conversation', count=True):
    stage = room['stage']
    ghost = stage_ghost(room)
    if ghost['rollsUsed'] >= 4:
        raise ValueError('This room has used its four skill checks')
    role = effective_role(room, seat)
    modifier = STATS[role][stat]
    dice = [roll_d20(), roll_d20()] if advantage else [roll_d20()]
    natural = max(dice)
    critical = natural == 20
    fumble = natural == 1
    success = critical or (not fumble and natural + modifier >= dc)
    ghost['rollsUsed'] += 1
    flags = room['story']['flags']
    flags['diceRolls'] += 1
    flags['crits'] += int(critical)
    flags['fumbles'] += int(fumble)
    record = {'role': role, 'character': role.upper(), 'stat': stat, 'dc': dc,
              'dice': dice, 'natural': natural, 'modifier': modifier,
              'total': natural + modifier, 'advantage': advantage,
              'critical': critical, 'fumble': fumble, 'success': success,
              'context': context, 'at': timestamp()}
    room['story']['lastRoll'] = record
    if critical:
        room['timer']['deadlineAt'] += 30_000
        narrate(room, 'Natural twenty. Even the candle applauds. Thirty seconds return to your life.')
    elif fumble:
        narrate(room, 'Natural one. You confidently compliment a cobweb. It does not accept your hand in marriage.')
    else:
        narrate(room, f'You roll {natural} + {modifier} against {dc}. ' + ('The manor reluctantly agrees.' if success else 'The manor raises one eyebrow.'))
    return record


def warmer(room, amount, *, force_cold=False):
    ghost = stage_ghost(room)
    ghost['warmth'] = max(0, min(3, ghost['warmth'] + amount))
    for threshold in (2, 3):
        index = threshold - 1
        clue_list = GHOSTS[room['stage']]['fragments']
        if ghost['warmth'] >= threshold and len(clue_list) >= index and index not in ghost['fragments']:
            ghost['fragments'].append(index)
    if (ghost['warmth'] == 0 or force_cold) and not ghost['closed'] and ghost['coldUntil'] is None:
        ghost['warmth'] = 0
        ghost['coldCount'] += 1
        ghost['coldUntil'] = timestamp() + 30_000
        charge_candle(room, 30_000)
        narrate(room, 'The ghost goes cold. Thirty seconds vanish. Even the candle looks disappointed.')
        return True
    return False


def recover_cold(room):
    ghost = stage_ghost(room)
    if ghost['coldUntil'] is not None and timestamp() >= ghost['coldUntil']:
        ghost['coldUntil'] = None
        ghost['warmth'] = 1
        narrate(room, f'{GHOSTS[room["stage"]]["name"]} returns, distinctly more annoyed.')
        return True
    return False


def reply(room, seat, option_id):
    ghost = stage_ghost(room)
    if ghost['coldUntil'] is not None or ghost['finished'] or ghost['closed']:
        raise ValueError('The ghost is not speaking right now')
    if ghost['speakerId'] != seat['id']:
        raise ValueError('It is not your speaking turn')
    offered = next((o for o in options(room, seat) if o['id'] == option_id), None)
    if offered is None:
        raise ValueError('That reply is not offered to your character')
    roll = None
    warmth_delta = {'kind': 1, 'curious': 0, 'rude': -1}[offered['tone']]
    if offered['stat']:
        if ghost['rollsUsed'] >= 2:  # Preserve checks for the crossroads and possible tie roll-off.
            raise ValueError('The ghost has heard enough dice for now. Choose a plain reply.')
        roll = skill_check(room, seat, offered['stat'], offered['dc'],
                           advantage=bool(ghost['pendingAdvantage']), context='dialogue')
        warmth_delta = 2 if roll['success'] else (-1 if not roll['fumble'] else 0)
        ghost['pendingAdvantage'] = False
        ghost['helpBy'] = None
    cold = warmer(room, warmth_delta)
    mood = 'sad' if cold else 'pleased' if warmth_delta > 0 else 'grumpy' if warmth_delta < 0 else 'nervous'
    responses = GHOSTS[room['stage']].get('responses')
    ghost_line = (responses[ghost['exchange']][('kind', 'curious', 'rude').index(offered['tone'])]
                  if responses and ghost['exchange'] < len(responses) else GHOSTS[room['stage']]['intro'])
    if roll and roll['fumble']:
        ghost_line = 'Oh, dear. That was a remarkable noise. Was it meant to be a sentence?'
    elif roll and roll['critical']:
        ghost_line = 'A perfect twenty! I feel quite alive. Do not tell the undertaker.'
    result = {'seatId': seat['id'], 'speaker': seat['name'], 'role': effective_role(room, seat),
              'ghostText': ghost_line,
              'text': offered['label'], 'warmthDelta': warmth_delta, 'mood': mood,
              'roll': roll, 'at': timestamp()}
    ghost['history'].append(result)
    ghost['exchange'] += 1
    ghost['finished'] = ghost['exchange'] >= min(4, len(GHOSTS[room['stage']]['replies']))
    if not ghost['finished']:
        advance_speaker(room)
    if not roll and not cold:
        narrate(room, "You speak. The ghost listens. Which is honestly more than most living people do.")
    return result


def help_speaker(room, helper):
    ghost = stage_ghost(room)
    if room['mode'] == 'solo' or ghost['speakerId'] == helper['id']:
        raise ValueError('Another player must help the speaker')
    if ghost['helpBy'] or ghost['finished'] or ghost['coldUntil']:
        raise ValueError('Help is not available now')
    if helper['id'] in ghost['skippedSeats']:
        raise ValueError('You have already spent your turn')
    ghost['helpBy'] = helper['id']
    ghost['skippedSeats'].append(helper['id'])
    ghost['pendingAdvantage'] = True
    narrate(room, f'{helper["name"]} lends a hand. Their next speaking turn is spent; the speaker has advantage.')


def steady_breath(room):
    if room['mode'] != 'solo':
        raise ValueError('Steady your breath is a solo action')
    ghost = stage_ghost(room)
    if ghost['pendingAdvantage'] or ghost['finished'] or ghost['coldUntil']:
        raise ValueError('You cannot steady your breath now')
    charge_candle(room, 30_000)
    ghost['pendingAdvantage'] = True
    narrate(room, 'You spend thirty seconds breathing slowly. The candle judges your breathing technique.')


def crossroads_available(room):
    g = stage_ghost(room)
    return room['stage'] in CHOICES and g['finished'] and g['crossroads'] is None and not g['closed']


def vote(room, seat, choice):
    if not crossroads_available(room):
        raise ValueError('The crossroads are not open')
    valid = {x['id'] for x in CHOICES[room['stage']]}
    if choice not in valid:
        raise ValueError('Unknown choice')
    ghost = stage_ghost(room)
    if seat['id'] in ghost['votes']:
        raise ValueError('You already voted')
    ghost['votes'][seat['id']] = choice
    room['story']['flags']['votesTaken'] += 1
    connected = [p for p in room['players'] if p['connected']]
    counts = {key: list(ghost['votes'].values()).count(key) for key in valid}
    majority = next((key for key, count in counts.items() if count > len(connected) / 2), None)
    if majority or all(p['id'] in ghost['votes'] for p in connected):
        winners = [majority] if majority else [k for k, count in counts.items() if count == max(counts.values())]
        tie_roll = None
        if len(winners) > 1:
            if ghost['rollsUsed'] < 4:
                ghost['rollsUsed'] += 1
                room['story']['flags']['diceRolls'] += 1
                candidates = {key: roll_d20() for key in sorted(winners)}
                best = max(candidates.values())
                tied = [k for k,v in candidates.items() if v == best]
                majority = sorted(tied)[0]  # Deterministic final tie breaker.
                tie_roll = {'context': 'vote_tie', 'diceByOption': candidates,
                            'winner': majority, 'at': timestamp()}
                room['story']['lastRoll'] = tie_roll
            else:
                majority = sorted(winners)[0]
        outcome = resolve_crossroads(room, majority, seat)
        outcome['tieRoll'] = tie_roll
        return outcome
    return None


def resolve_crossroads(room, chosen, voter):
    stage = room['stage']
    ghost = stage_ghost(room)
    option = next(x for x in CHOICES[stage] if x['id'] == chosen)
    # The first supporter is the representative for a party skill check.
    representative_id = next((sid for sid, decision in ghost['votes'].items() if decision == chosen), voter['id'])
    representative = next((p for p in room['players'] if p['id'] == representative_id), voter)
    roll = None
    if option['stat']:
        if ghost['rollsUsed'] >= 4:
            raise ValueError('The manor has no more dice to spare')
        roll = skill_check(room, representative, option['stat'], option['dc'], context='crossroads')
    success = roll is None or roll['success']
    harmless = roll is not None and roll['fumble']
    flags = room['story']['flags']
    if stage == 'foyer':
        if chosen == 'watch':
            if success:
                if 'WATCH' not in flags['items']:
                    flags['items'].append('WATCH')
                narrate(room, 'You retrieve the watch. Horace says it never ticked when he needed it most.')
            elif not harmless:
                charge_candle(room, 30_000)
                warmer(room, -1)
                narrate(room, 'The watch snaps shut on your glove. Thirty seconds gone, one ghost unimpressed.')
        else:
            warmer(room, 1)
            if room['hintLevel'] < 3:
                room['hintLevel'] += 1  # Free hint, no candle charge.
            narrate(room, 'You leave the watch. Horace offers a clue, and a very small relieved smile.')
    elif stage == 'library':
        if chosen == 'pay':
            charge_candle(room, 30_000)
            warmer(room, 2)
            narrate(room, 'Thirty seconds for a fine. Prudence stamps PAID on an invisible receipt.')
        elif chosen == 'argue':
            if success: warmer(room, 1)
            narrate(room, 'You debate a ghost librarian. Somehow the footnotes win.')
        elif chosen == 'sneak':
            if success:
                if 'BOOKMARK' not in flags['items']: flags['items'].append('BOOKMARK')
                narrate(room, 'You steal the bookmark. It politely steals your attention back.')
            elif not harmless:
                warmer(room, -3, force_cold=True)
    elif stage == 'crypt':
        if chosen == 'trust':
            if success:
                flags['shortCut'] = True
                if 'COMPASS' not in flags['items']: flags['items'].append('COMPASS')
                narrate(room, 'Reginald knows the shortcut after all. A compass finally finds north.')
            elif not harmless:
                flags['WRONG_TURN'] = True
                charge_candle(room, 30_000)
                narrate(room, 'You take a wrong turn. The trap charges a thirty-second toll.')
        else:
            narrate(room, 'You choose a careful map. Sometimes bravery is reading the signs.')
    ghost['crossroads'] = {'choice': chosen, 'success': success,
                           'roll': roll, 'resolvedAt': timestamp()}
    return {'choice': chosen, 'success': success, 'roll': roll,
            'crossroads': ghost['crossroads']}


def closure(room, stage):
    ghost = room['story']['ghosts'][stage]
    ghost['closed'] = True
    ghost['goodbye'] = GHOSTS[stage]['goodbye']
    ghost['coldUntil'] = None
    narrate(room, 'You gave a ghost something rarer than escape: permission to move on.')


def public_story(room, seat):
    if room['stage'] == 'finale':
        f = room['story']['flags']
        return {'ghost': None, 'stats': {r: STATS[r].copy() for r in ROLES},
                'wick': room['story']['wick'].copy(), 'lastRoll': room['story']['lastRoll'],
                'choices': [], 'flags': {'items': f['items'][:], 'shortCut': f['shortCut'],
                'crits': f['crits'], 'fumbles': f['fumbles'], 'votesTaken': f['votesTaken'],
                'diceRolls': f['diceRolls'], 'candleTimeAtEnd': f['candleTimeAtEnd']}}
    stage = room['stage']
    ghost = stage_ghost(room)
    speaker = next((p for p in room['players'] if p['id'] == ghost['speakerId']), None)
    try:
        offered = options(room, seat)
    except ValueError:
        offered = []
    return {
        'ghost': {
            'id': stage, 'name': GHOSTS[stage]['name'], 'job': GHOSTS[stage]['job'],
            'personality': GHOSTS[stage]['personality'], 'unfinishedBusiness': GHOSTS[stage]['unfinishedBusiness'],
            'warmth': ghost['warmth'], 'coldUntil': ghost['coldUntil'],
            'coldCount': ghost['coldCount'], 'exchange': ghost['exchange'],
            'maxExchanges': min(4, len(GHOSTS[stage]['replies'])),
            'speakerId': ghost['speakerId'], 'speakerName': speaker['name'] if speaker else None,
            'finished': ghost['finished'], 'closed': ghost['closed'],
            'goodbye': ghost['goodbye'], 'history': ghost['history'][-6:],
            'fragments': [GHOSTS[stage]['fragments'][i-1] for i in ghost['fragments'] if 1 <= i <= len(GHOSTS[stage]['fragments'])],
            'options': offered, 'helpBy': ghost['helpBy'],
            'advantage': ghost['pendingAdvantage'], 'rollsUsed': ghost['rollsUsed'],
            'votes': ghost['votes'].copy(), 'crossroads': ghost['crossroads'],
        },
        'stats': {role: STATS[role].copy() for role in ROLES},
        'choices': CHOICES.get(stage, []) if ghost['finished'] and not ghost['closed'] else [],
        'wick': room['story']['wick'].copy(),
        'lastRoll': room['story']['lastRoll'],
        'flags': {'items': room['story']['flags']['items'][:],
                  # WRONG_TURN remains a secret server-side ending flag.
                  'shortCut': room['story']['flags']['shortCut'],
                  'crits': room['story']['flags']['crits'], 'fumbles': room['story']['flags']['fumbles'],
                  'votesTaken': room['story']['flags']['votesTaken'],
                  'diceRolls': room['story']['flags']['diceRolls'],
                  'candleTimeAtEnd': room['story']['flags']['candleTimeAtEnd']},
    }
