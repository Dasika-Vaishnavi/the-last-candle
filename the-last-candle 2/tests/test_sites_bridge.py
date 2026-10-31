"""Cross-origin Sites frontend and Render WebSocket bridge acceptance tests."""
import os
import unittest
from unittest.mock import patch
from aiohttp import ClientSession, WSServerHandshakeError
from aiohttp.test_utils import TestServer
import server

SITE = 'https://last-candle-example.openai.chatgpt.site'


class SitesBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env = patch.dict(os.environ, {'ALLOWED_WS_ORIGINS': SITE})
        self.env.start()
        self.runner = TestServer(server.create_app())
        await self.runner.start_server()
        self.session = ClientSession()
        self.url = str(self.runner.make_url('/ws')).replace('http://', 'ws://')

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.close()
        self.env.stop()
        server.ROOMS.clear()
        server.LOCKS.clear()
        server.SOCKETS.clear()
        server.ADMISSION_ATTEMPTS.clear()

    async def test_samesite_and_authorized_site_origins_only(self):
        async with self.session.ws_connect(self.url, headers={'Origin': SITE}) as ws:
            await ws.send_json({'type': 'HELLO'})
            self.assertEqual((await ws.receive_json(timeout=3))['type'], 'READY')
        async with self.session.ws_connect(self.url, headers={'Origin': str(self.runner.make_url('/')).rstrip('/')}) as ws:
            await ws.send_json({'type': 'HELLO'})
            self.assertEqual((await ws.receive_json(timeout=3))['type'], 'READY')
        with self.assertRaises(WSServerHandshakeError) as denial:
            await self.session.ws_connect(self.url, headers={'Origin': 'https://malicious.example'})
        self.assertEqual(denial.exception.status, 403)

    async def test_health_cors_is_exact_and_room_state_shared(self):
        async with self.session.get(str(self.runner.make_url('/health')), headers={'Origin': SITE}) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers.get('Access-Control-Allow-Origin'), SITE)
        async with self.session.get(str(self.runner.make_url('/health')), headers={'Origin': 'https://other.example'}) as r:
            self.assertIsNone(r.headers.get('Access-Control-Allow-Origin'))
        async with self.session.ws_connect(self.url, headers={'Origin': SITE}) as first, self.session.ws_connect(self.url, headers={'Origin': SITE}) as second:
            await first.send_json({'type': 'CREATE_ROOM', 'name': 'Vesper', 'capacity': 2})
            welcome = await first.receive_json(timeout=3)
            self.assertEqual(welcome['type'], 'WELCOME')
            code = welcome['roomCode']
            await first.receive_json(timeout=3)  # state update
            await second.send_json({'type': 'JOIN_ROOM', 'name': 'Quill', 'code': code})
            second_welcome = await second.receive_json(timeout=3)
            self.assertEqual(second_welcome['type'], 'WELCOME')
            state = await second.receive_json(timeout=3)
            self.assertEqual(state['type'], 'STATE')
            self.assertEqual(len(state['state']['players']), 2)
            for _ in range(4):
                first_state = await first.receive_json(timeout=3)
                if first_state['type']=='STATE' and len(first_state['state']['players'])==2:
                    break
            else:
                self.fail('First player did not see second player')
            self.assertEqual(first_state['state']['room']['code'], code)

    async def test_solo_resume_from_site_origin(self):
        async with self.session.ws_connect(self.url, headers={'Origin': SITE}) as first:
            await first.send_json({'type':'CREATE_SOLO'})
            welcome = await first.receive_json(timeout=3)
            self.assertEqual(welcome['roomMode'], 'solo')
            state = await first.receive_json(timeout=3)
            self.assertEqual(state['state']['timer']['durationMs'], 1_500_000)
            await first.close()
        async with self.session.ws_connect(self.url, headers={'Origin': SITE}) as resumed:
            await resumed.send_json({'type':'RESUME_SEAT','roomId':welcome['roomId'],'token':welcome['token']})
            again = await resumed.receive_json(timeout=3)
            self.assertEqual(again['seatId'], welcome['seatId'])
            state=await resumed.receive_json(timeout=3)
            self.assertEqual(len(state['state']['players']), 1)

if __name__=='__main__':
    unittest.main()
