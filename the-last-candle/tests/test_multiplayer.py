"""End-to-end WebSocket acceptance tests. Run against PORT=8765 python server.py."""
import asyncio
import json
import unittest
from aiohttp import ClientSession, WSMsgType

BASE = 'http://127.0.0.1:8765'


class Player:
    def __init__(self, ws):
        self.ws = ws
        self.state = None
        self.token = None
        self.id = None
        self.code = None
        self.events = []
        self.index = 0

    async def send(self, typ, **fields):
        self.index += 1
        await self.ws.send_json({'type': typ, 'actionId': f'test-action-{id(self)}-{self.index}', **fields})

    async def receive(self, pred, limit=40):
        for _ in range(limit):
            msg = await asyncio.wait_for(self.ws.receive(), 3)
            if msg.type != WSMsgType.TEXT:
                raise AssertionError(f'WebSocket closed: {msg}')
            data = json.loads(msg.data)
            self.events.append(data)
            if data['type'] == 'WELCOME':
                self.token, self.id, self.code = data['token'], data['seatId'], data['roomCode']
            if data['type'] == 'STATE':
                self.state = data['state']
            if pred(data):
                return data
        raise AssertionError(f'No desired event; last={self.events[-5:]}')

    async def until_phase(self, phase):
        return await self.receive(lambda d: d['type']=='STATE' and d['state']['phase']==phase)

    async def updated(self, key, expected):
        return await self.receive(lambda d: d['type']=='STATE' and d['state'].get(key)==expected)


class GameFlow(unittest.IsolatedAsyncioTestCase):
    async def test_health_and_readiness_probe(self):
        async with ClientSession() as session:
            async with session.get(BASE+'/health') as response:
                self.assertEqual(response.status, 200)
                self.assertEqual((await response.json())['status'], 'ok')
            async with session.ws_connect(BASE+'/ws') as ws:
                await ws.send_json({'type':'HELLO'})
                data=await ws.receive_json(timeout=4)
                self.assertEqual(data['type'],'READY')
                self.assertIsInstance(data['serverNow'],int)
                await ws.send_json({'type':'PING','clientSentAt':123456})
                data=await ws.receive_json(timeout=4)
                self.assertEqual(data['type'],'PONG')
                self.assertEqual(data['clientSentAt'],123456)
                # The landing page reuses the proven-live socket to create a room.
                await ws.send_json({'type':'CREATE_ROOM','name':'Probe','capacity':2})
                data=await ws.receive_json(timeout=4)
                self.assertEqual(data['type'],'WELCOME')
                self.assertRegex(data['roomCode'], r'^[A-Z]{4}$')

    async def test_two_independent_clients_join_same_room(self):
        async with ClientSession() as first_session, ClientSession() as second_session:
            first=Player(await first_session.ws_connect(BASE+'/ws'))
            second=Player(await second_session.ws_connect(BASE+'/ws'))
            await first.send('CREATE_ROOM',name='Ember',capacity=2)
            await first.receive(lambda x:x['type']=='WELCOME')
            await first.until_phase('lobby')
            await second.send('JOIN_ROOM',code=first.code,name='Ash')
            await second.receive(lambda x:x['type']=='WELCOME')
            await second.receive(lambda x:x['type']=='STATE' and len(x['state']['players'])==2)
            await first.receive(lambda x:x['type']=='STATE' and len(x['state']['players'])==2)
            self.assertEqual([p['name'] for p in first.state['players']], ['Ember','Ash'])
            self.assertEqual({p['id'] for p in first.state['players']},
                             {p['id'] for p in second.state['players']})
            self.assertTrue(all(p['connected'] for p in first.state['players']))
            await second.ws.close()
            await first.receive(lambda x:x['type']=='STATE' and
                                any(p['name']=='Ash' and not p['connected']
                                    for p in x['state']['players']))
            await first.ws.close()

    async def test_three_player_room(self):
        async with ClientSession() as session:
            async def new(): return Player(await session.ws_connect(BASE+'/ws'))
            a, b, c = await new(), await new(), await new()
            await a.send('CREATE_ROOM',name='Ada',capacity=5)
            await a.receive(lambda d:d['type']=='WELCOME')
            await a.until_phase('lobby')
            for pl,name in [(b,'Bram'),(c,'Clara')]:
                await pl.send('JOIN_ROOM',code=a.code,name=name)
                await pl.receive(lambda d:d['type']=='WELCOME')
                await pl.until_phase('lobby')
            await a.receive(lambda d:d['type']=='STATE' and len(d['state']['players'])==3)
            await a.send('SELECT_ROLE',role='medium')
            await b.send('SELECT_ROLE',role='archivist')
            await c.send('SELECT_ROLE',role='locksmith')
            # readiness can be set concurrently, independent of role-ack result.
            await asyncio.sleep(.15)
            for p in (a,b,c):
                await p.send('SET_READY',ready=True)
            # host start after all three received ready transitions.
            await a.receive(lambda d:d['type']=='STATE' and sum(p['ready'] for p in d['state']['players'])==3)
            await a.send('START_GAME')
            await a.until_phase('playing')
            await b.until_phase('playing')
            await c.until_phase('playing')
            self.assertEqual(set(a.state['me']['roles']+b.state['me']['roles']+c.state['me']['roles']), {'medium','archivist','lantern','locksmith','walker'})
            self.assertNotEqual(next(p['id'] for p in a.state['players'] if 'archivist' in p['roles']),next(p['id'] for p in a.state['players'] if 'lantern' in p['roles']))
            self.assertIsNone(a.state['solutions'])
            self.assertNotIn('entries', c.state['clues'].get('locksmith', {}))
            self.assertNotIn('entries', a.state['clues'].get('medium', {}))
            start=a.state['timer']['deadlineAt']
            # Only locksmith can submit; rejected action cannot cost time.
            await a.send('SUBMIT_CLOCK_CODE',hours=[1,1,1,1])
            await a.receive(lambda d:d['type']=='ERROR' and 'Only the Locksmith' in d['message'])
            await c.send('SUBMIT_CLOCK_CODE',hours=[1,1,1,1])
            await c.receive(lambda d:d['type']=='STATE' and d['state']['wrongAttempts']==1)
            self.assertEqual(c.state['timer']['totalPenaltyMs'],30000)
            self.assertEqual(c.state['timer']['deadlineAt'],start-30000)
            await b.send('REQUEST_HINT')
            await b.receive(lambda d:d['type']=='STATE' and d['state']['hintLevel']==1)
            self.assertEqual(b.state['timer']['totalPenaltyMs'],90000)
            self.assertEqual(len(b.state['hints']),1)
            # New users cannot join active rooms.
            d=await new()
            await d.send('JOIN_ROOM',name='Late',code=a.code)
            await d.receive(lambda x:x['type']=='ERROR' and 'Game in progress' in x['message'])
            await d.ws.close()
            # Connected/host presence migration and same-seat reconnect.
            a_id=a.id
            await a.ws.close()
            await b.receive(lambda x:x['type']=='STATE' and x['state']['room']['hostId']==b.id)
            replacement=await new()
            await replacement.send('RESUME_SEAT',code=a.code,token=a.token)
            await replacement.receive(lambda x:x['type']=='WELCOME')
            await replacement.until_phase('playing')
            self.assertEqual(replacement.id,a_id)
            self.assertEqual(len(replacement.state['players']),3)
            self.assertEqual(replacement.state['room']['hostId'],b.id)
            self.assertEqual(replacement.state['timer']['totalPenaltyMs'],90000)
            # Derive the solution using role-specific clues, just like real players.
            # The server keeps the answer key private and entirely in memory.
            diary=b.state['clues']['archivist']['entries']
            symbols=a.state['clues']['lantern']['order']
            correct=[next(entry['hour'] for entry in diary if entry['symbol']==symbol)
                     for symbol in symbols]
            await asyncio.sleep(1.85)
            await c.send('SUBMIT_CLOCK_CODE',hours=correct)
            await c.until_phase('foyer_solved')
            await b.until_phase('foyer_solved')
            self.assertEqual(c.state['solutions']['code'],correct)
            self.assertGreater(c.state['timer']['frozenRemainingMs'],0)
            await asyncio.sleep(2.5)
            await c.send('CONTINUE')
            await c.until_phase('stage2_preview')
            await b.send('TRY_AGAIN')
            await b.until_phase('lobby')
            self.assertEqual(b.state['round'],2)
            self.assertEqual(len(b.state['players']),3)
            for p in (replacement,b,c):
                await p.ws.close()


if __name__ == '__main__':
    unittest.main()
