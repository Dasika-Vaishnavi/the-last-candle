"""Character-selection and role-ability end-to-end tests against the local WebSocket server."""
import asyncio
import unittest
import sys
from pathlib import Path
from aiohttp import ClientSession

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_multiplayer import BASE, Player


class AutoAssignmentUnitTests(unittest.TestCase):
    def test_selection_expiry_allocates_unique_unclaimed_roles(self):
        import server
        room=server.new_room('Test',5)
        a,_=server.add_player(room,'Ada')
        b,_=server.add_player(room,'Bram')
        c,_=server.add_player(room,'Clara')
        a['primaryRole']='medium'; a['lockedAt']=server.now()
        self.assertTrue(server.start_selection_if_needed(room))
        self.assertEqual(room['selectionDeadlineAt']-room['selectionStartedAt'],45000)
        room['selectionDeadlineAt']=server.now()-1
        assigned=server.auto_lock_stragglers(room)
        self.assertEqual(len(assigned),2)
        self.assertEqual(len({p['primaryRole'] for p in room['players']}),3)
        server.update_merged_roles(room)
        self.assertEqual({r for p in room['players'] for r in p['roles']},set(server.ROLES))
        self.assertNotEqual(next(p['id'] for p in room['players'] if 'lantern' in p['roles']),next(p['id'] for p in room['players'] if 'archivist' in p['roles']))

    def test_late_lobby_join_is_auto_locked_after_expiry(self):
        import server
        room=server.new_room('Test',5)
        server.add_player(room,'Ada');server.add_player(room,'Bram')
        server.start_selection_if_needed(room)
        room['selectionDeadlineAt']=server.now()-1
        self.assertEqual(len(server.auto_lock_stragglers(room)),2)
        server.add_player(room,'Clara')
        late=server.auto_lock_stragglers(room)
        self.assertEqual(len(late),1)
        self.assertEqual(len({p['primaryRole'] for p in room['players']}),3)

    def test_flame_resumes_at_original_remaining_time_after_20_seconds(self):
        import server
        room=server.new_room('Test',2)
        t=server.now()
        room['phase']='playing'
        room['timer']={'startedAt':t,'deadlineAt':t+1220000,
                      'frozenRemainingMs':1200000,'freezeUntil':t+20000,'totalPenaltyMs':0}
        old=server.now
        try:
            server.now=lambda:t+12000
            self.assertEqual(server.remaining(room),1200000)
            server.now=lambda:t+21000
            self.assertEqual(server.remaining(room),1199000)
        finally:
            server.now=old


class CharacterSelectTests(unittest.IsolatedAsyncioTestCase):
    async def connect_two(self, session):
        a = Player(await session.ws_connect(BASE + '/ws'))
        b = Player(await session.ws_connect(BASE + '/ws'))
        await a.send('CREATE_ROOM', name='Ash', capacity=5)
        await a.receive(lambda d: d['type'] == 'WELCOME')
        await a.until_phase('lobby')
        self.assertIsNone(a.state['selection']['deadlineAt'])
        await b.send('JOIN_ROOM', name='Moth', code=a.code)
        await b.receive(lambda d: d['type'] == 'WELCOME')
        await b.until_phase('lobby')
        await a.receive(lambda d: d['type'] == 'STATE' and len(d['state']['players']) == 2)
        self.assertGreater(a.state['selection']['deadlineAt'], a.state['serverNow'])
        self.assertLessEqual(a.state['selection']['deadlineAt'] - a.state['serverNow'], 45000)
        return a, b

    async def test_unique_lock_and_merged_roles(self):
        async with ClientSession() as session:
            a, b = await self.connect_two(session)
            await a.send('LOCK_CHARACTER', role='medium')
            await a.receive(lambda d: d['type'] == 'STATE' and d['state']['me']['primaryRole'] == 'medium')
            await b.send('LOCK_CHARACTER', role='medium')
            await b.receive(lambda d: d['type'] == 'ERROR' and 'already been locked' in d['message'])
            self.assertIsNone(b.state['me']['primaryRole'])
            # Check auto-selection in a pure server test below; the deployed server
            # runs in a separate process, so changing imported globals here does not work.
            await b.send('LOCK_CHARACTER', role='archivist')
            await b.receive(lambda d:d['type']=='STATE' and d['state']['me']['primaryRole']=='archivist')
            self.assertTrue(b.state['me']['lockedAt'])
            await a.receive(lambda d:d['type']=='STATE' and all(x['primaryRole'] for x in d['state']['players']))
            self.assertEqual(set(b.state['me']['roles']+a.state['me']['roles']), set(['medium','lantern','walker','archivist','locksmith']))
            await a.ws.close()
            await b.ws.close()

    async def test_abilities_candle_freeze_free_hint_and_shield(self):
        async with ClientSession() as session:
            a,b = await self.connect_two(session)
            await a.send('LOCK_CHARACTER',role='medium')
            await a.receive(lambda d:d['type']=='STATE' and d['state']['me']['primaryRole']=='medium')
            await b.send('LOCK_CHARACTER',role='archivist')
            await b.receive(lambda d:d['type']=='STATE' and d['state']['me']['primaryRole']=='archivist')
            await a.send('SET_READY',ready=True)
            await b.send('SET_READY',ready=True)
            await a.receive(lambda d:d['type']=='STATE' and all(p['ready'] for p in d['state']['players']))
            await a.send('START_GAME')
            await a.until_phase('playing')
            await b.until_phase('playing')
            self.assertEqual(a.state['me']['roles'],['medium','lantern','walker'])
            self.assertEqual(b.state['me']['roles'],['archivist','locksmith'])
            base_deadline=a.state['timer']['deadlineAt']
            await a.send('USE_ABILITY',role='medium')
            await a.receive(lambda d:d['type']=='STATE' and d['state']['abilities']['used']['medium'])
            self.assertIsNotNone(a.state['veilClue'])
            self.assertGreater(a.state['veilClue']['expiresAt'],a.state['serverNow'])
            await a.send('USE_ABILITY',role='medium')
            await a.receive(lambda d:d['type']=='ERROR' and 'already been used' in d['message'])
            await b.send('USE_ABILITY',role='archivist')
            await b.receive(lambda d:d['type']=='STATE' and d['state']['hintLevel']==1)
            self.assertEqual(b.state['timer']['deadlineAt'],base_deadline)
            await a.send('USE_ABILITY',role='lantern')
            await a.receive(lambda d:d['type']=='STATE' and d['state']['abilities']['used']['lantern'])
            self.assertEqual(a.state['timer']['deadlineAt'],base_deadline+20000)
            freeze_before=a.state['timer']['remainingMs']
            await asyncio.sleep(.22)
            # Freeze is authoritative: elapsed real time should not burn the candle.
            self.assertAlmostEqual(freeze_before,a.state['timer']['remainingMs'],delta=200)
            await b.send('USE_ABILITY',role='locksmith')
            await b.receive(lambda d:d['type']=='STATE' and d['state']['abilities']['secondTurnArmed'])
            await b.send('SUBMIT_CLOCK_CODE',hours=[1,1,1,1])
            await b.receive(lambda d:d['type']=='STATE' and d['state']['wrongAttempts']==1)
            self.assertEqual(b.state['timer']['totalPenaltyMs'],0)
            self.assertFalse(b.state['abilities']['secondTurnArmed'])
            await asyncio.sleep(1.85)
            await b.send('SUBMIT_CLOCK_CODE',hours=[1,1,1,1])
            await b.receive(lambda d:d['type']=='STATE' and d['state']['wrongAttempts']==2)
            self.assertEqual(b.state['timer']['totalPenaltyMs'],30000)
            self.assertAlmostEqual(b.state['timer']['remainingMs'],freeze_before-30000,delta=100)
            await a.send('USE_ABILITY',role='walker')
            await a.receive(lambda d:d['type']=='ERROR' and 'only in the Crypt' in d['message'])
            await a.ws.close();await b.ws.close()

    async def test_replay_resets_character_selections_and_powers(self):
        async with ClientSession() as session:
            a,b=await self.connect_two(session)
            for player,role in ((a,'medium'),(b,'locksmith')):
                await player.send('LOCK_CHARACTER',role=role)
                await player.receive(lambda d:d['type']=='STATE' and d['state']['me']['primaryRole']==role)
                await player.send('SET_READY',ready=True)
            await a.receive(lambda d:d['type']=='STATE' and all(p['ready'] for p in d['state']['players']))
            await a.send('START_GAME'); await a.until_phase('playing')
            await b.until_phase('playing')
            await a.send('USE_ABILITY',role='medium')
            await a.receive(lambda d:d['type']=='STATE' and d['state']['abilities']['used']['medium'])
            # Solve the Foyer using the independently delivered private clues.
            await b.receive(lambda d:d['type']=='STATE' and d['state']['phase']=='playing')
            diary=(a.state if 'archivist' in a.state['clues'] else b.state)['clues']['archivist']['entries']
            order=(a.state if 'lantern' in a.state['clues'] else b.state)['clues']['lantern']['order']
            correct=[next(e['hour'] for e in diary if e['symbol']==sym) for sym in order]
            await b.send('SUBMIT_CLOCK_CODE',hours=correct)
            await b.until_phase('foyer_solved')
            await asyncio.sleep(2.35)
            await a.send('CONTINUE')
            await a.until_phase('stage2_preview')
            await a.send('TRY_AGAIN')
            await a.receive(lambda d:d['type']=='STATE' and d['state']['phase']=='lobby' and d['state']['round']==2)
            self.assertTrue(all(p['primaryRole'] is None for p in a.state['players']))
            self.assertFalse(any(a.state['abilities']['used'].values()))
            self.assertGreater(a.state['selection']['deadlineAt'],a.state['serverNow'])
            await a.ws.close();await b.ws.close()


if __name__=='__main__': unittest.main()
