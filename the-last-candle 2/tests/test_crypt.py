"""Crypt acceptance tests: asymmetric fog, real WS movements, traps, solo and closure."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server
import crypt_engine as crypt
import story_engine as story
from test_solo import SoloSocket


class MazeGeneration(unittest.TestCase):
    def tearDown(self):
        server.ROOMS.clear(); server.LOCKS.clear(); server.SOCKETS.clear()

    def test_seeded_6x6_eight_traps_always_has_valid_path(self):
        grids = [crypt.generate('seed-' + str(i)) for i in range(150)]
        self.assertGreater(len({tuple(sorted(g['traps'])) for g in grids}), 120)
        for g in grids:
            self.assertEqual(g['start'], (5, 0))
            self.assertEqual(g['exit'], (0, 5))
            self.assertEqual(len(g['traps']), 8)
            self.assertEqual(len(g['path']), 11)
            self.assertTrue(all(0 <= r < 6 and 0 <= c < 6 for r,c in g['traps']))
            self.assertFalse(set(g['path']) & g['traps'])
            self.assertIn(g['safe'], g['path'])
            self.assertEqual(len(set(g['path'])), 11)
            self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(g['path'],g['path'][1:])))
            self.assertEqual(crypt.generate('seed-1')['traps'], crypt.generate('seed-1')['traps'])

    def test_three_plus_half_reveals_and_wren_is_blind(self):
        room=server.new_room('Wren', 3)
        w,_=server.add_player(room,'Wren'); e,_=server.add_player(room,'Ember');v,_=server.add_player(room,'Vesper')
        w['roles']=['walker'];e['roles']=['lantern','archivist'];v['roles']=['medium','locksmith']
        w['primaryRole']='walker';e['primaryRole']='lantern';v['primaryRole']='medium'
        room['phase']='playing';room['stage']='crypt'
        maps=[crypt.view(room,p) for p in (w,e,v)]
        self.assertTrue(maps[0]['canMove']);self.assertFalse(maps[0]['canGuide'])
        self.assertEqual(maps[0]['knownTraps'],[])
        self.assertEqual(maps[0]['visible'],[[4,0],[5,0],[5,1]])
        traps=room['cryptPuzzle']['traps']
        self.assertEqual(set(map(tuple,maps[1]['knownTraps'])),{p for p in traps if p[1]<3})
        self.assertEqual(set(map(tuple,maps[2]['knownTraps'])),{p for p in traps if p[1]>=3})
        self.assertEqual(maps[1]['safeTile'],list(room['cryptPuzzle']['safe']))
        self.assertIsNone(maps[2]['safeTile'])
        self.assertNotIn('traps',server.public_state(room,w)['crypt'])
        self.assertNotIn('path',server.public_state(room,e)['crypt'])


class CryptSockets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runner=TestServer(server.create_app()); await self.runner.start_server()
        self.session=ClientSession()
        self.url=str(self.runner.make_url('/ws')).replace('http://','ws://')
        self.clients=[]

    async def asyncTearDown(self):
        for p in self.clients:
            if not p.socket.closed: await p.socket.close()
        await self.session.close();await self.runner.close()
        server.ROOMS.clear();server.LOCKS.clear();server.SOCKETS.clear();server.ADMISSION_ATTEMPTS.clear()

    async def player(self):
        p=SoloSocket(await self.session.ws_connect(self.url))
        self.clients.append(p)
        return p

    async def duo(self):
        a,b=await self.player(),await self.player()
        await a.action('CREATE_ROOM',name='Ada',capacity=2)
        await a.next(lambda d:d['type']=='WELCOME');await a.next_state(lambda s:s['phase']=='lobby')
        code=a.welcome['roomCode']
        await b.action('JOIN_ROOM',name='Bram',code=code)
        await b.next(lambda d:d['type']=='WELCOME');await b.next_state(lambda s:len(s['players'])==2)
        await a.action('LOCK_CHARACTER',role='medium');await a.next_state(lambda s:s['me']['primaryRole']=='medium')
        await b.action('LOCK_CHARACTER',role='archivist');await b.next_state(lambda s:s['me']['primaryRole']=='archivist')
        await a.action('SET_READY',ready=True);await b.action('SET_READY',ready=True)
        await a.next_state(lambda s:all(p['ready'] for p in s['players']))
        await a.action('START_GAME');await a.next_state(lambda s:s['phase']=='playing');await b.next_state(lambda s:s['phase']=='playing')
        room=server.ROOMS[code]
        # Stage entry is tested separately by CONTINUE_LIBRARY in existing tests.
        room['stage']='crypt';room['phase']='playing';room['hintLevel']=0;story.enter_stage(room,'crypt')
        room['version']+=1;await server.broadcast(room)
        await a.next_state(lambda s:s['stage']=='crypt');await b.next_state(lambda s:s['stage']=='crypt')
        return a,b,room

    async def solo(self):
        p=await self.player();await p.action('CREATE_SOLO')
        await p.next(lambda d:d['type']=='WELCOME');await p.next_state(lambda s:s['phase']=='lobby')
        await p.action('EQUIP_SOLO_ABILITY',role='walker');await p.next_state(lambda s:len(s['solo']['equippedAbilities'])==1)
        await p.action('EQUIP_SOLO_ABILITY',role='archivist');await p.next_state(lambda s:len(s['solo']['equippedAbilities'])==2)
        await p.action('START_SOLO');await p.next_state(lambda s:s['phase']=='playing')
        room=server.ROOMS[p.welcome['roomCode']];room['stage']='crypt';room['hintLevel']=0;story.enter_stage(room,'crypt')
        room['version']+=1;await server.broadcast(room)
        await p.next_state(lambda s:s['stage']=='crypt')
        return p,room

    async def walk_path(self, p,room):
        route=room['cryptPuzzle']['path']
        labels={(-1,0):'up',(1,0):'down',(0,-1):'left',(0,1):'right'}
        for a,b in zip(route,route[1:]):
            await asyncio.sleep(.15)
            await p.action('CRYPT_MOVE',direction=labels[(b[0]-a[0],b[1]-a[1])])
            await p.next_state(lambda s,p=b: s['crypt'] is not None and s['crypt']['position']==list(p) or s['phase']=='crypt_solved' and p==route[-1])

    async def test_multiplayer_wren_moves_both_clients_sync_and_closure(self):
        a,b,room=await self.duo()
        self.assertIn('walker',a.state['me']['roles'])
        self.assertEqual(a.state['crypt']['knownTraps'],[])
        self.assertEqual(len(b.state['crypt']['knownTraps']),8)
        self.assertFalse(b.state['crypt']['canMove'])
        await b.action('CRYPT_MOVE',direction='up')
        await b.next(lambda d:d['type']=='ERROR' and 'Only Wren' in d['message'])
        await a.action('REQUEST_HINT');await a.next_state(lambda s:s['hintLevel']==1)
        await b.next_state(lambda s:s['hintLevel']==1)
        self.assertEqual(a.state['timer']['totalPenaltyMs'],60000)
        await self.walk_path(a,room)
        await b.next_state(lambda s:s['phase']=='crypt_solved')
        self.assertTrue(b.state['story']['ghost']['closed'])
        self.assertEqual(a.state['crypt']['position'],[0,5])
        self.assertEqual(b.state['crypt']['position'],[0,5])
        self.assertEqual(room['crypt']['trapHits'],0)
        await asyncio.sleep(3.0)
        await b.action('CONTINUE_CRYPT')
        await a.next_state(lambda s:s['phase']=='playing' and s['stage']=='finale')
        await b.next_state(lambda s:s['phase']=='playing' and s['stage']=='finale')
        self.assertIsNone(room['story']['flags']['candleTimeAtEnd'], 'Final rank is awarded after the Kaashi offering')

    async def test_trap_reset_penalty_and_sure_step_exactly_once(self):
        a,b,room=await self.duo()
        traps=room['cryptPuzzle']['traps']
        tile=next(iter(traps));y,x=tile
        neighbor=next((p for p in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)) if 0<=p[0]<6 and 0<=p[1]<6 and p not in traps),None)
        self.assertIsNotNone(neighbor)
        direction=next(k for k,d in crypt.DIRECTIONS.items() if (neighbor[0]+d[0],neighbor[1]+d[1])==tile)
        room['crypt']['position']=neighbor
        before=room['timer']['deadlineAt']
        await a.action('CRYPT_MOVE',direction=direction)
        await a.next_state(lambda s:s['crypt']['trapHits']==1)
        await b.next_state(lambda s:s['crypt']['trapHits']==1)
        self.assertEqual(a.state['crypt']['position'],[5,0])
        self.assertEqual(a.state['timer']['deadlineAt'],before-30000)
        room['crypt']['position']=neighbor;room['crypt']['lastMoveAt']=0
        await a.action('USE_ABILITY',role='walker')
        await a.next_state(lambda s:s['crypt']['sureStepArmed'])
        await a.action('CRYPT_MOVE',direction=direction)
        await a.next_state(lambda s:s['crypt']['sureStepUsed'])
        self.assertEqual(a.state['crypt']['position'],list(tile))
        self.assertEqual(a.state['timer']['deadlineAt'],before-30000)
        await a.action('USE_ABILITY',role='walker')
        await a.next(lambda d:d['type']=='ERROR' and 'already been used' in d['message'])

    async def test_solo_lens_movement_gating_refresh_and_completion(self):
        p,room=await self.solo()
        self.assertFalse(p.state['crypt']['canMove'])
        await p.action('CRYPT_MOVE',direction='up')
        await p.next(lambda d:d['type']=='ERROR' and 'Wren' in d['message'])
        self.assertEqual(set(map(tuple,p.state['crypt']['knownTraps'])),{p for p in room['cryptPuzzle']['traps'] if p[1]>=3})
        await p.action('SWITCH_LENS',role='lantern')
        await p.next_state(lambda s:s['solo']['targetLens']=='lantern')
        self.assertEqual(p.state['crypt']['knownTraps'],[])
        await p.next_state(lambda s:s['solo']['activeLens']=='lantern')
        self.assertEqual(set(map(tuple,p.state['crypt']['knownTraps'])),{q for q in room['cryptPuzzle']['traps'] if q[1]<3})
        await p.action('SWITCH_LENS',role='walker')
        await p.next_state(lambda s:s['solo']['activeLens']=='walker')
        self.assertTrue(p.state['crypt']['canMove'])
        self.assertEqual(p.state['crypt']['knownTraps'],[])
        start_code=p.welcome['roomCode'];token=p.welcome['token'];private=p.welcome['roomId']
        # Move, then recover the single seat without losing the crypt position.
        first=room['cryptPuzzle']['path'][1]
        direction='up' if first==(4,0) else 'right'
        await p.action('CRYPT_MOVE',direction=direction)
        await p.next_state(lambda s:s['crypt']['position']==list(first))
        await p.socket.close()
        p2=await self.player();await p2.action('RESUME_SEAT',roomId=private,token=token)
        await p2.next(lambda d:d['type']=='WELCOME');await p2.next_state(lambda s:s['stage']=='crypt')
        self.assertEqual(p2.state['crypt']['position'],list(first))
        self.assertEqual(len(server.ROOMS[start_code]['players']),1)
        # Replay remainder from authoritative path, no advantage from refreshing.
        room['crypt']['position']=crypt.START;room['crypt']['lastMoveAt']=0
        await self.walk_path(p2,room)
        self.assertEqual(p2.state['phase'],'crypt_solved')
        self.assertTrue(p2.state['story']['ghost']['closed'])

    async def test_three_hints_cost_exactly_three_minutes(self):
        a,b,room=await self.duo()
        before=room['timer']['deadlineAt']
        for level in range(1,4):
            await a.action('REQUEST_HINT');await a.next_state(lambda s,n=level:s['hintLevel']==n)
        await b.next_state(lambda s:s['hintLevel']==3)
        self.assertEqual(room['timer']['deadlineAt'],before-180000)
        await a.action('REQUEST_HINT');await a.next(lambda d:d['type']=='ERROR' and 'All three' in d['message'])

    async def test_reginald_crossroads_can_skip_half_safe_route(self):
        a,b,room=await self.duo()
        # Crypt is intentionally one brief exchange; this vote is optional.
        g=story.stage_ghost(room)
        for _ in range(len(story.GHOSTS['crypt']['replies'])):
            active=server.get_seat(room,g['speakerId'])
            option=next(o for o in story.options(room,active) if o['stat'] is None and o['tone']!='rude')
            story.reply(room,active,option['id'])
        room['version']+=1;await server.broadcast(room)
        await a.next_state(lambda s:s['story']['ghost']['finished'])
        with patch.object(story,'roll_d20',return_value=19):
            await a.action('VOTE_CROSSROADS',choice='trust')
            await a.next_state(lambda s:s['story']['ghost']['votes'].get(a.welcome['seatId'])=='trust')
            await b.action('VOTE_CROSSROADS',choice='trust')
            await b.next_state(lambda s:s['story']['ghost']['crossroads'] is not None)
        self.assertTrue(room['story']['flags']['shortCut'])
        self.assertIn('COMPASS',room['story']['flags']['items'])
        self.assertTrue(room['crypt']['shortcutApplied'])
        self.assertEqual(room['crypt']['position'],room['cryptPuzzle']['path'][5])

if __name__=='__main__': unittest.main()
