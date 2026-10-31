"""Stage 4 acceptance: complete four-room game via authoritative WebSockets."""
import asyncio
import sys
import unittest
from pathlib import Path
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server
import finale_engine as finale
import crypt_engine as crypt
from test_solo import SoloSocket


class YantraRules(unittest.TestCase):
    def tearDown(self):
        server.ROOMS.clear();server.LOCKS.clear();server.SOCKETS.clear()

    def test_randomized_connectivity_and_no_target_leak(self):
        variants=set()
        for i in range(80):
            puzzle=finale.make('seed-'+str(i))
            self.assertEqual(len(puzzle['sections']),3)
            variants.add(tuple(tuple(s['route']) for s in puzzle['sections']))
            for section in puzzle['sections']:
                self.assertEqual(len(section['path']),5)
                self.assertFalse(finale.section_connected(section))
                for t in section['path']:
                    t['rotation']=t['target']
                self.assertTrue(finale.section_connected(section))
        self.assertGreater(len(variants),25)
        room=server.new_room('Nora',3)
        people=[server.add_player(room,name)[0] for name in ('Nora','Iris','Pax')]
        room['phase']='playing';room['stage']='finale'
        for seat in people:
            result=server.public_state(room,seat)['finale']
            self.assertEqual(len([x for x in result['sections'] if x['owned']]),1)
            self.assertNotIn('target',str(result))
            self.assertNotIn('seed',str(result))
            self.assertTrue(all(('tiles' in s)==s['owned'] for s in result['sections']))

    def test_two_and_five_player_assignment_and_solo_lens(self):
        for count in (2,4,5):
            room=server.new_room('person',count)
            players=[server.add_player(room,'person')[0] for _ in range(count)]
            room['phase']='playing';room['stage']='finale'
            owns=[finale.owned_sections(room,p) for p in players]
            self.assertEqual(sorted(set(sum(owns,[]))),[0,1,2])
            self.assertEqual(owns[0],[0,2] if count==2 else [0])
            self.assertTrue(all(owns), 'Every player must be assigned a stream')
        room=server.new_room('solo',1,mode='solo')
        seat,_=server.add_player(room,'solo')
        room['stage']='finale';room['phase']='playing'
        for role,part in finale.ROLE_STREAM.items():
            room['solo']['activeLens']=role
            self.assertEqual(finale.owned_sections(room,seat),[part])
        room['solo']['targetLens']='archivist'
        self.assertEqual(finale.owned_sections(room,seat),[])
        with self.assertRaises(ValueError):
            finale.rotate(room,seat,0,0)

    def test_five_player_secret_offers_and_expired_ember_freeze(self):
        room=server.new_room('A',5)
        players=[server.add_player(room,f'P{i}')[0] for i in range(5)]
        for i,p in enumerate(players):p['roles']=[server.ROLES[i]]
        room['stage']='finale';room['phase']='playing';room['finale']['part']='offering'
        room['timer']['deadlineAt']=server.now()+140_000
        room['timer']['freezeUntil']=server.now()-1
        room['timer']['frozenRemainingMs']=550_000
        self.assertLess(server.remaining(room),145000, 'Expired freeze cannot pause a finale')
        for p in players[:4]:
            self.assertIsNone(finale.submit_offering(room,p,'candle'))
        state=finale.view(room,players[-1])
        self.assertEqual(len(state['offeredSeats']),4)
        self.assertIsNone(state['reveal'])
        self.assertIsNone(state['myOffer'])
        self.assertTrue(finale.submit_offering(room,players[4],'candle'))
        self.assertEqual(room['finale']['reveal']['threshold'],5)
        self.assertEqual(room['finale']['reveal']['total'],5)


class FinalGame(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runner=TestServer(server.create_app());await self.runner.start_server()
        self.session=ClientSession()
        self.url=str(self.runner.make_url('/ws')).replace('http://','ws://')
        self.clients=[]

    async def asyncTearDown(self):
        for p in self.clients:
            if not p.socket.closed:await p.socket.close()
        await self.session.close();await self.runner.close()
        server.ROOMS.clear();server.LOCKS.clear();server.SOCKETS.clear();server.ADMISSION_ATTEMPTS.clear()

    async def player(self):
        p=SoloSocket(await self.session.ws_connect(self.url));self.clients.append(p);return p

    async def duo(self):
        a,b=await self.player(),await self.player()
        await a.action('CREATE_ROOM',name='Ada',capacity=2)
        await a.next(lambda d:d['type']=='WELCOME');await a.next_state(lambda s:s['phase']=='lobby')
        await b.action('JOIN_ROOM',name='Bram',code=a.welcome['roomCode'])
        await b.next(lambda d:d['type']=='WELCOME');await b.next_state(lambda s:len(s['players'])==2)
        await a.action('LOCK_CHARACTER',role='medium');await a.next_state(lambda s:s['me']['primaryRole']=='medium')
        await b.action('LOCK_CHARACTER',role='archivist');await b.next_state(lambda s:s['me']['primaryRole']=='archivist')
        await a.action('SET_READY',ready=True);await b.action('SET_READY',ready=True)
        await a.next_state(lambda s:all(p['ready'] for p in s['players']))
        await a.action('START_GAME');await a.next_state(lambda s:s['phase']=='playing');await b.next_state(lambda s:s['phase']=='playing')
        return a,b,server.ROOMS[a.welcome['roomCode']]

    async def enter_finale(self,a,room):
        # Each preceding chapter is completed through its actual public action,
        # not by forcing phase to 'finale'. Private test inspection substitutes
        # for human conversation when deriving a known solution.
        if room['stage']=='foyer':
            locker=next(p for p in room['players'] if 'locksmith' in p['roles'])
            player=next(x for x in self.clients if x.welcome['seatId']==locker['id'])
            await player.action('SUBMIT_CLOCK_CODE',hours=room['puzzle']['solution'])
            await a.next_state(lambda s:s['phase']=='foyer_solved')
            await asyncio.sleep(2.35)
            await a.action('CONTINUE')
            await a.next_state(lambda s:s['stage']=='library')
        if room['stage']=='library':
            locker=next(p for p in room['players'] if 'locksmith' in p['roles'])
            player=next(x for x in self.clients if x.welcome['seatId']==locker['id'])
            await player.action('SUBMIT_LIBRARY_WORD',word=room['libraryPuzzle']['word'])
            await a.next_state(lambda s:s['library']['part']=='levers')
            for client in self.clients: await client.action('LEVER_DOWN')
            await a.next_state(lambda s:s['phase']=='library_solved')
            await asyncio.sleep(3.6)
            await a.action('CONTINUE_LIBRARY')
            await a.next_state(lambda s:s['stage']=='crypt')
        walker=next(p for p in room['players'] if 'walker' in p['roles'])
        client=next(x for x in self.clients if x.welcome['seatId']==walker['id'])
        route=room['cryptPuzzle']['path']
        directions={(-1,0):'up',(1,0):'down',(0,-1):'left',(0,1):'right'}
        for before,after in zip(route,route[1:]):
            await asyncio.sleep(.16)
            await client.action('CRYPT_MOVE',direction=directions[(after[0]-before[0],after[1]-before[1])])
            await a.next_state(lambda s,p=after:s['crypt'] is not None and s['crypt']['position']==list(p) or s['phase']=='crypt_solved' and p==route[-1])
        if a.state['phase']!='crypt_solved': await a.next_state(lambda s:s['phase']=='crypt_solved')
        await asyncio.sleep(3.05)
        await a.action('CONTINUE_CRYPT')
        await a.next_state(lambda s:s['phase']=='playing' and s['stage']=='finale')
        self.assertIsNone(a.state['finaleSolution'])

    async def solve_streams_multiplayer(self,a,b,room):
        owners={s:next(x for x in (a,b) if s in finale.owned_sections(room,server.get_seat(room,x.welcome['seatId']))) for s in range(3)}
        await a.action('ROTATE_STREAM_TILE',section=2,tile=1)  # may be owned by Ada; ensures server rejects forged moves when not.
        # Reset one deliberate rotation at end of that stream's solution.
        for sid,section in enumerate(room['finalePuzzle']['sections']):
            for i,t in enumerate(section['path']):
                turns=(t['target']-t['rotation'])%4
                for _ in range(turns):
                    await owners[sid].action('ROTATE_STREAM_TILE',section=sid,tile=i)
                    await a.next_state(lambda s:s['finale'] and s['finale']['rotations']>=1)
        # account for client possibly not receiving all changed states yet
        await a.next_state(lambda s:s['finale']['part']=='offering')
        await b.next_state(lambda s:s['finale']['part']=='offering')

    async def test_multiplayer_full_four_room_win_and_replay(self):
        a,b,room=await self.duo()
        await self.enter_finale(a,room)
        await b.next_state(lambda s:s['stage']=='finale')
        self.assertEqual([x['owned'] for x in a.state['finale']['sections']],[True,False,True])
        self.assertEqual([x['owned'] for x in b.state['finale']['sections']],[False,True,False])
        await b.action('ROTATE_STREAM_TILE',section=0,tile=0)
        await b.next(lambda d:d['type']=='ERROR' and 'another' in d['message'])
        self.assertIsNone(b.state['finaleSolution'])
        # Solve each tile via a genuine player action, never a client-reported solution.
        for sid,section in enumerate(room['finalePuzzle']['sections']):
            actor=a if sid in (0,2) else b
            for i,t in enumerate(section['path']):
                turns=(t['target']-t['rotation'])%4
                for _ in range(turns):
                    previous=room['finale']['rotations']
                    await actor.action('ROTATE_STREAM_TILE',section=sid,tile=i)
                    await a.next_state(lambda s,n=previous:s['finale'] and s['finale']['rotations']>n)
        if a.state['finale']['part']!='offering': await a.next_state(lambda s:s['finale']['part']=='offering')
        await b.next_state(lambda s:s['finale']['part']=='offering')
        before=room['timer']['deadlineAt']
        await a.action('SEAL_OFFERING',kind='nothing')
        await a.next_state(lambda s:len(s['finale']['offeredSeats'])==1)
        await b.next_state(lambda s:len(s['finale']['offeredSeats'])==1)
        self.assertIsNone(b.state['finale']['reveal'])
        self.assertIsNone(b.state['finale']['myOffer'])
        await b.action('SEAL_OFFERING',kind='nothing')
        await a.next_state(lambda s:s['phase']=='finale_reveal')
        await b.next_state(lambda s:s['phase']=='finale_reveal')
        self.assertFalse(a.state['finale']['reveal']['accepted'])
        await a.next_state(lambda s:s['phase']=='playing' and s['finale']['offerRound']==2)
        await b.next_state(lambda s:s['phase']=='playing' and s['finale']['offerRound']==2)
        self.assertEqual(room['timer']['deadlineAt'],before-120000)
        await a.action('SEAL_OFFERING',kind='ability',role='medium')
        await a.next_state(lambda s:len(s['finale']['offeredSeats'])==1)
        self.assertFalse(room['abilitiesUsed']['medium'], 'Offering is not consumed before reveal')
        await b.action('SEAL_OFFERING',kind='candle')
        await a.next_state(lambda s:s['phase']=='finale_reveal')
        await b.next_state(lambda s:s['phase']=='finale_reveal')
        self.assertEqual(a.state['finale']['reveal'],b.state['finale']['reveal'])
        await a.next_state(lambda s:s['phase']=='won')
        await b.next_state(lambda s:s['phase']=='won')
        self.assertEqual(a.state['result'],b.state['result'])
        self.assertEqual(room['timer']['deadlineAt'],before-180000)
        self.assertTrue(room['abilitiesUsed']['medium'])
        self.assertEqual(a.state['result']['leaderboard'],'multiplayer')
        self.assertEqual(len(a.state['result']['players']),2)
        self.assertEqual(room['story']['flags']['candleTimeAtEnd'],a.state['result']['secondsRemaining'])
        seed=room['puzzle']['seed']
        await a.action('TRY_AGAIN')
        await a.next_state(lambda s:s['phase']=='lobby' and s['round']==2)
        await b.next_state(lambda s:s['phase']=='lobby')
        self.assertNotEqual(seed,room['puzzle']['seed'])
        self.assertEqual(room['finale']['part'],'streams')
        self.assertEqual(room['story']['flags']['candleTimeAtEnd'],None)

    async def test_solo_full_four_room_win_lens_gate_and_refresh(self):
        p=await self.player()
        await p.action('CREATE_SOLO');await p.next(lambda d:d['type']=='WELCOME')
        await p.next_state(lambda s:s['phase']=='lobby')
        id_,token=p.welcome['roomId'],p.welcome['token']
        room=server.ROOMS[p.welcome['roomCode']]
        for ability in ('medium','archivist'):
            await p.action('EQUIP_SOLO_ABILITY',role=ability)
            await p.next_state(lambda s,n=('medium','archivist').index(ability)+1:len(s['solo']['equippedAbilities'])==n)
        await p.action('START_SOLO');await p.next_state(lambda s:s['phase']=='playing')
        async def switch(role):
            if p.state['solo']['activeLens']==role:return
            await p.action('SWITCH_LENS',role=role)
            await p.next_state(lambda s:s['solo']['activeLens']==role)
        await switch('locksmith')
        await p.action('SUBMIT_CLOCK_CODE',hours=room['puzzle']['solution'])
        await p.next_state(lambda s:s['phase']=='foyer_solved')
        await asyncio.sleep(2.35)
        await p.action('CONTINUE');await p.next_state(lambda s:s['stage']=='library')
        await p.action('SUBMIT_LIBRARY_WORD',word=room['libraryPuzzle']['word'])
        await p.next_state(lambda s:s['library']['part']=='levers')
        await p.action('START_SOLO_RHYTHM')
        await p.next_state(lambda s:s['library']['rhythm']['active'])
        t0=room['library']['rhythm']['startedAt']
        await p.action('SOLO_LEVER_DOWN');await p.next_state(lambda s:s['library']['rhythm']['held'])
        for i,off in enumerate(room['libraryPuzzle']['beatOffsets']):
            await asyncio.sleep(max(0,(t0+off-server.now())/1000)+.10)
            await p.action('SOLO_LEVER_UP')
            await p.next_state(lambda s,i=i:s['library']['rhythm']['beatIndex']==i and not s['library']['rhythm']['held'])
            await p.action('SOLO_LEVER_DOWN')
            if i<2:await p.next_state(lambda s,i=i:s['library']['rhythm']['beatIndex']==i+1)
        await p.next_state(lambda s:s['phase']=='library_solved')
        await asyncio.sleep(3.6)
        await p.action('CONTINUE_LIBRARY');await p.next_state(lambda s:s['stage']=='crypt')
        await switch('walker')
        labels={(-1,0):'up',(1,0):'down',(0,-1):'left',(0,1):'right'}
        for before,after in zip(room['cryptPuzzle']['path'],room['cryptPuzzle']['path'][1:]):
            await asyncio.sleep(.16)
            await p.action('CRYPT_MOVE',direction=labels[(after[0]-before[0],after[1]-before[1])])
            await p.next_state(lambda s,after=after:s['crypt'] and s['crypt']['position']==list(after) or s['phase']=='crypt_solved' and after==crypt.EXIT)
        await asyncio.sleep(3.05)
        await p.action('CONTINUE_CRYPT');await p.next_state(lambda s:s['stage']=='finale')
        self.assertEqual(p.state['finale']['sections'][0]['owned'],False)
        await p.action('ROTATE_STREAM_TILE',section=0,tile=1)
        await p.next(lambda d:d['type']=='ERROR' and 'Lens' in d['message'])
        for role,section in finale.ROLE_STREAM.items():
            await switch(role)
            self.assertEqual([x['owned'] for x in p.state['finale']['sections']],[i==section for i in range(3)])
            for i,t in enumerate(room['finalePuzzle']['sections'][section]['path']):
                for _ in range((t['target']-t['rotation'])%4):
                    previous=room['finale']['rotations']
                    await p.action('ROTATE_STREAM_TILE',section=section,tile=i)
                    await p.next_state(lambda s,previous=previous:s['finale']['rotations']>previous)
        if p.state['finale']['part']!='offering': await p.next_state(lambda s:s['finale']['part']=='offering')
        # Reconnect mid-offering without losing flags, board, or sealed identity.
        progress=room['finale']['rotations'];remaining=room['timer']['deadlineAt']
        await p.socket.close()
        p=await self.player();await p.action('RESUME_SEAT',roomId=id_,token=token)
        await p.next(lambda d:d['type']=='WELCOME');await p.next_state(lambda s:s['stage']=='finale')
        self.assertEqual(p.state['finale']['rotations'],progress)
        self.assertEqual(p.state['timer']['deadlineAt'],remaining)
        await p.action('SEAL_OFFERING',kind='candle')
        await p.next_state(lambda s:s['phase']=='finale_reveal')
        self.assertEqual(p.state['finale']['reveal']['threshold'],1)
        await p.next_state(lambda s:s['phase']=='won')
        self.assertEqual(p.state['result']['leaderboard'],'solo')
        self.assertEqual(p.state['result']['rank'],server.solo_rank(p.state['result']['secondsRemaining']))
        self.assertEqual(room['timer']['deadlineAt'],remaining-60000)
        await p.action('TRY_AGAIN')
        await p.next_state(lambda s:s['phase']=='lobby' and s['round']==2)
        self.assertEqual(p.state['solo']['equippedAbilities'],[])

    async def test_timeout_reveals_all_stage_solutions(self):
        a,b,room=await self.duo()
        room['stage']='finale';room['phase']='playing';room['timer']['deadlineAt']=server.now()-1
        await a.action('PING')
        await a.next_state(lambda s:s['phase']=='lost')
        await b.next_state(lambda s:s['phase']=='lost')
        self.assertEqual(len(a.state['cryptSolution']['route']),11)
        self.assertEqual(len(b.state['finaleSolution']),3)
        self.assertEqual(a.state['result']['stage'],'finale')
