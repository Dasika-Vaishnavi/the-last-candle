"""Integrated server-authoritative solo Stage 1 and same-seat refresh recovery.
Self-hosted aiohttp tests; no external port or deployment needed.
"""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from aiohttp import ClientSession, WSMsgType
from aiohttp.test_utils import TestServer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server


class SoloSocket:
    def __init__(self, socket):
        self.socket = socket
        self.state = None
        self.welcome = None
        self.seq = 0

    async def action(self, type, **fields):
        self.seq += 1
        await self.socket.send_json({'type': type, 'actionId': f'solo-test-{id(self)}-{self.seq}', **fields})

    async def next(self, pred=None, timeout=6):
        async def scan():
            while True:
                msg = await self.socket.receive()
                if msg.type != WSMsgType.TEXT:
                    raise AssertionError(f'Websocket unexpectedly closed: {msg.type}')
                data = json.loads(msg.data)
                if data['type'] == 'STATE':
                    self.state = data['state']
                elif data['type'] == 'WELCOME':
                    self.welcome = data
                if pred is None or pred(data):
                    return data
        return await asyncio.wait_for(scan(), timeout=timeout)

    async def next_state(self, predicate):
        return await self.next(lambda msg: msg['type']=='STATE' and predicate(msg['state']))


class SoloFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runner = TestServer(server.create_app())
        await self.runner.start_server()
        self.session = ClientSession()
        self.url = str(self.runner.make_url('/ws'))
        self.url = self.url.replace('http://', 'ws://').replace('https://', 'wss://')

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.close()
        # Keep global in-memory state from leaking between test methods.
        server.ROOMS.clear(); server.LOCKS.clear(); server.SOCKETS.clear(); server.ADMISSION_ATTEMPTS.clear()

    async def create(self):
        p = SoloSocket(await self.session.ws_connect(self.url))
        await p.action('CREATE_SOLO')
        welcome=await p.next(lambda d:d['type']=='WELCOME')
        self.assertEqual(welcome['roomMode'], 'solo')
        self.assertRegex(welcome['roomId'], '^[a-f0-9]{32}$')
        await p.next_state(lambda s:s['phase']=='lobby')
        async with self.session.get(self.runner.make_url('/solo/'+welcome['roomId'])) as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(p.state['room']['mode'], 'solo')
        self.assertIsNone(p.state['room']['code'])  # Internal join code stays private.
        self.assertEqual(len(p.state['players']), 1)
        self.assertEqual(set(p.state['me']['roles']), set(server.ROLES))
        return p

    async def equip_and_start(self, p):
        await p.action('EQUIP_SOLO_ABILITY', role='medium')
        await p.next_state(lambda s:s['solo']['equippedAbilities']==['medium'])
        await p.action('EQUIP_SOLO_ABILITY', role='locksmith')
        await p.next_state(lambda s:len(s['solo']['equippedAbilities'])==2)
        await p.action('EQUIP_SOLO_ABILITY', role='lantern')
        await p.next(lambda d:d['type']=='ERROR' and 'exactly two abilities' in d['message'])
        await p.action('START_SOLO')
        await p.next_state(lambda s:s['phase']=='playing')
        self.assertEqual(p.state['timer']['durationMs'], 25*60*1000)
        self.assertGreater(p.state['timer']['deadlineAt']-p.state['timer']['startedAt'], 1499000)
        await p.action('ACK_REVEAL')
        await p.next_state(lambda s:s['me']['ack'])

    async def switch(self,p,target):
        await p.action('SWITCH_LENS',role=target)
        await p.next_state(lambda s:s['solo']['targetLens']==target)
        self.assertIsNone(p.state['solo']['activeLens'])
        self.assertEqual(p.state['clues'], {}, 'No clue should leak during the smoke wipe')
        start=p.state['serverNow']
        await p.next_state(lambda s:s['solo']['activeLens']==target and s['solo']['targetLens'] is None)
        self.assertGreaterEqual(p.state['serverNow'] - start, 1850)
        self.assertEqual(list(p.state['clues']),[target])

    async def test_complete_solo_foyer_and_separate_trial_rank(self):
        p=await self.create()
        # Cannot start without both powers.
        await p.action('START_SOLO')
        await p.next(lambda d:d['type']=='ERROR' and 'exactly two' in d['message'])
        await self.equip_and_start(p)
        self.assertEqual(set(p.state['clues']),{'medium'})
        # Cannot cast an unchosen power despite carrying every role.
        await p.action('USE_ABILITY', role='archivist')
        await p.next(lambda d:d['type']=='ERROR' and ('View this character' in d['message'] or 'not equipped' in d['message']))
        # Crowe cannot unlock until his Lens is active, even though the seat carries Locksmith.
        await p.action('SUBMIT_CLOCK_CODE', hours=[1,2,3,4])
        await p.next(lambda d:d['type']=='ERROR' and 'Crowe' in d['message'])
        await self.switch(p, 'archivist')
        entries=p.state['clues']['archivist']['entries']
        await p.action('USE_ABILITY',role='archivist')
        await p.next(lambda d:d['type']=='ERROR' and 'not equipped' in d['message'])
        await self.switch(p, 'lantern')
        order=p.state['clues']['lantern']['order']
        correct=[next(e['hour'] for e in entries if e['symbol']==sym) for sym in order]
        await self.switch(p, 'locksmith')
        self.assertEqual(p.state['solo']['equippedAbilities'], ['medium','locksmith'])
        before=p.state['timer']['deadlineAt']
        incorrect=[1,1,1,1]
        self.assertNotEqual(incorrect,correct)
        await p.action('SUBMIT_CLOCK_CODE',hours=incorrect)
        await p.next_state(lambda s:s['wrongAttempts']==1)
        self.assertEqual(p.state['timer']['deadlineAt'], before-30000)
        await asyncio.sleep(1.85)  # existing per-room wrong-attempt cooldown
        await p.action('SUBMIT_CLOCK_CODE',hours=correct)
        await p.next_state(lambda s:s['phase']=='foyer_solved')
        self.assertNotIn('clues',p.state['solutions'] or {})
        await asyncio.sleep(2.35)
        await p.action('CONTINUE')
        await p.next_state(lambda s:s['phase']=='stage2_preview')
        result=p.state['result']
        self.assertEqual(result['outcome'],'trial_complete')
        self.assertEqual(result['leaderboard'],'solo')
        self.assertIn(result['rank'],['Lone Lightkeeper','The Unbroken Witness','Last of the Living'])
        self.assertLess(result['secondsRemaining'],1500)
        self.assertGreater(result['secondsRemaining'],0)
        prev_seed=server.ROOMS[p.welcome['roomCode']]['puzzle']['seed']
        await p.action('TRY_AGAIN')
        await p.next_state(lambda s:s['phase']=='lobby' and s['round']==2)
        self.assertEqual(p.state['solo']['equippedAbilities'],[])
        self.assertEqual(p.state['me']['roles'],server.ROLES)
        self.assertNotEqual(prev_seed,server.ROOMS[p.welcome['roomCode']]['puzzle']['seed'])
        await p.socket.close()

    async def test_refresh_during_switch_recovers_exact_solo_seat(self):
        p=await self.create()
        await self.equip_and_start(p)
        original_id = p.welcome['seatId']
        original_room = p.welcome['roomId']
        token=p.welcome['token']
        code=p.welcome['roomCode']
        await p.action('SWITCH_LENS',role='archivist')
        await p.next_state(lambda s:s['solo']['targetLens']=='archivist')
        await p.socket.close()
        # Simulate a fresh WebSocket after a page refresh. The server's Lens change continues.
        reconnect = SoloSocket(await self.session.ws_connect(self.url))
        await reconnect.action('RESUME_SEAT',roomId=original_room,token=token)
        await reconnect.next(lambda d:d['type']=='WELCOME')
        await reconnect.next_state(lambda s:s['phase']=='playing')
        self.assertEqual(reconnect.welcome['seatId'],original_id)
        self.assertEqual(reconnect.welcome['roomId'],original_room)
        self.assertEqual(len(reconnect.state['players']),1)
        self.assertTrue(reconnect.state['players'][0]['connected'])
        self.assertEqual(reconnect.state['timer']['durationMs'],1500000)
        self.assertEqual(reconnect.state['solo']['equippedAbilities'],['medium','locksmith'])
        if reconnect.state['solo']['targetLens']:
            self.assertEqual(reconnect.state['clues'],{})
            await reconnect.next_state(lambda s:s['solo']['activeLens']=='archivist')
        self.assertEqual(list(reconnect.state['clues']),['archivist'])
        # A second browser cannot join a solo room, even if its internal code leaks.
        stranger=SoloSocket(await self.session.ws_connect(self.url))
        await stranger.action('JOIN_ROOM',name='Intruder',code=code)
        await stranger.next(lambda d:d['type']=='ERROR' and 'solo chamber' in d['message'])
        self.assertEqual(len(server.ROOMS[code]['players']),1)
        await reconnect.socket.close();await stranger.socket.close()


if __name__=='__main__':
    unittest.main()
