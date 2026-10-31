"""Stage 2 multiplayer and solo acceptance tests against the actual WebSocket server."""
import asyncio
import sys
import unittest
from pathlib import Path
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server
from test_solo import SoloSocket


class LibraryFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runner = TestServer(server.create_app())
        await self.runner.start_server()
        self.session = ClientSession()
        self.url = str(self.runner.make_url('/ws')).replace('http://','ws://')

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.close()
        server.ROOMS.clear(); server.LOCKS.clear(); server.SOCKETS.clear(); server.ADMISSION_ATTEMPTS.clear()

    async def player(self):
        return SoloSocket(await self.session.ws_connect(self.url))

    async def stage2_from_foyer(self, p):
        await p.next_state(lambda s:s['phase']=='foyer_solved')
        await asyncio.sleep(2.34)
        await p.action('CONTINUE')
        await p.next_state(lambda s:s['phase']=='playing' and s['stage']=='library')
        self.assertEqual(p.state['hintLevel'],0)
        self.assertEqual(p.state['library']['part'],'cipher')

    async def test_multiplayer_cipher_lever_reset_and_three_second_solve(self):
        a,b=await self.player(),await self.player()
        await a.action('CREATE_ROOM',name='Vesper',capacity=2)
        await a.next(lambda d:d['type']=='WELCOME')
        await a.next_state(lambda s:s['phase']=='lobby')
        code=a.welcome['roomCode']
        await b.action('JOIN_ROOM',name='Quill',code=code)
        await b.next(lambda d:d['type']=='WELCOME')
        await b.next_state(lambda s:len(s['players'])==2)
        await a.action('LOCK_CHARACTER',role='medium')
        await a.next_state(lambda s:s['me']['primaryRole']=='medium')
        await b.action('LOCK_CHARACTER',role='archivist')
        await b.next_state(lambda s:s['me']['primaryRole']=='archivist')
        await a.action('SET_READY',ready=True)
        await b.action('SET_READY',ready=True)
        await a.next_state(lambda s:all(p['ready'] for p in s['players']))
        await a.action('START_GAME')
        await a.next_state(lambda s:s['phase']=='playing')
        await b.next_state(lambda s:s['phase']=='playing')
        self.assertIn('lantern',a.state['me']['roles'])
        self.assertIn('locksmith',b.state['me']['roles'])
        diary=b.state['clues']['archivist']['entries']
        order=a.state['clues']['lantern']['order']
        await b.action('SUBMIT_CLOCK_CODE',hours=[next(x['hour'] for x in diary if x['symbol']==y) for y in order])
        await self.stage2_from_foyer(b)
        await a.next_state(lambda s:s['stage']=='library')
        self.assertNotIn('word',a.state['clues']['medium'])
        self.assertNotIn('wheel',a.state['clues']['medium'])
        self.assertNotIn('symbols',b.state['clues']['archivist'])
        symbols=a.state['clues']['medium']['symbols']
        wheel=b.state['clues']['archivist']['wheel']
        letters={x['symbol']:x['letter'] for x in wheel}
        word=''.join(letters[sym] for sym in symbols)
        glowing=sorted(book['letter'] for book in a.state['clues']['lantern']['books'] if book['glowing'])
        self.assertEqual(sorted(word),glowing)
        await a.action('SUBMIT_LIBRARY_WORD',word=word)
        await a.next(lambda d:d['type']=='ERROR' and 'Only Crowe' in d['message'])
        await b.action('SUBMIT_LIBRARY_WORD',word=word)
        await b.next_state(lambda s:s['library']['part']=='levers')
        await a.next_state(lambda s:s['library'] and s['library']['part']=='levers')
        await a.action('LEVER_DOWN')
        await a.next_state(lambda s:len(s['library']['heldSeats'])==1)
        await b.action('LEVER_DOWN')
        await b.next_state(lambda s:s['library']['holdStartedAt'] is not None)
        await a.action('LEVER_UP')
        await a.next_state(lambda s:s['library']['heldSeats']==[])
        await b.next_state(lambda s:s['library']['heldSeats']==[])
        await a.action('LEVER_DOWN')
        await a.next_state(lambda s:len(s['library']['heldSeats'])==1)
        await b.action('LEVER_DOWN')
        await b.next_state(lambda s:s['library']['holdStartedAt'] is not None)
        await a.next_state(lambda s:s['phase']=='library_solved')
        await b.next_state(lambda s:s['phase']=='library_solved')
        self.assertGreaterEqual(server.now()-a.state['library']['holdStartedAt'],2950)
        self.assertEqual(server.ROOMS[code]['library']['part'],'solved')
        await asyncio.sleep(3.6)
        await a.action('CONTINUE_LIBRARY')
        await a.next_state(lambda s:s['phase']=='playing' and s['stage']=='crypt')
        await a.action('TRY_AGAIN')
        await a.next_state(lambda s:s['phase']=='lobby' and s['round']==2)
        self.assertNotEqual(server.ROOMS[code]['libraryPuzzle']['variantId'],a.state['library']['variantId'] if a.state['library'] else 'previous')
        await a.socket.close();await b.socket.close()

    async def switch(self,p,role):
        await p.action('SWITCH_LENS',role=role)
        await p.next_state(lambda s:s['solo']['targetLens']==role)
        self.assertEqual(p.state['clues'],{})
        await p.next_state(lambda s:s['solo']['activeLens']==role)

    async def test_solo_stage2_cipher_rhythm_and_reconnect(self):
        p=await self.player()
        await p.action('CREATE_SOLO')
        await p.next(lambda d:d['type']=='WELCOME')
        await p.next_state(lambda s:s['phase']=='lobby')
        room_code=p.welcome['roomCode']
        room_id=p.welcome['roomId']
        token=p.welcome['token']
        await p.action('EQUIP_SOLO_ABILITY',role='medium')
        await p.next_state(lambda s:len(s['solo']['equippedAbilities'])==1)
        await p.action('EQUIP_SOLO_ABILITY',role='locksmith')
        await p.next_state(lambda s:len(s['solo']['equippedAbilities'])==2)
        await p.action('START_SOLO')
        await p.next_state(lambda s:s['phase']=='playing')
        self.assertEqual(p.state['timer']['durationMs'],1500000)
        await p.action('ACK_REVEAL')
        await p.next_state(lambda s:s['me']['ack'])
        await self.switch(p,'archivist')
        diary=p.state['clues']['archivist']['entries']
        await self.switch(p,'lantern')
        order=p.state['clues']['lantern']['order']
        hours=[next(e['hour'] for e in diary if e['symbol']==g) for g in order]
        await self.switch(p,'locksmith')
        await p.action('SUBMIT_CLOCK_CODE',hours=hours)
        await self.stage2_from_foyer(p)
        await self.switch(p,'medium')
        sequence=p.state['clues']['medium']['symbols']
        cadence=p.state['clues']['medium']['cadence']
        self.assertEqual(len(cadence),3)
        await self.switch(p,'archivist')
        wheel={e['symbol']:e['letter'] for e in p.state['clues']['archivist']['wheel']}
        await self.switch(p,'lantern')
        glowing=sorted(x['letter'] for x in p.state['clues']['lantern']['books'] if x['glowing'])
        word=''.join(wheel[s] for s in sequence)
        self.assertEqual(sorted(word),glowing)
        await self.switch(p,'locksmith')
        await p.action('SUBMIT_LIBRARY_WORD',word=word)
        await p.next_state(lambda s:s['library']['part']=='levers')
        # A page refresh after the cipher does not create another seat or reset the timer.
        timer=p.state['timer']['deadlineAt']
        await p.socket.close()
        p=await self.player()
        await p.action('RESUME_SEAT',roomId=room_id,token=token)
        await p.next(lambda d:d['type']=='WELCOME')
        await p.next_state(lambda s:s['stage']=='library' and s['library']['part']=='levers')
        self.assertEqual(p.welcome['seatId'],server.ROOMS[room_code]['players'][0]['id'])
        self.assertEqual(p.state['timer']['deadlineAt'],timer)
        await p.action('START_SOLO_RHYTHM')
        await p.next_state(lambda s:s['library']['rhythm']['active'])
        t0=p.state['library']['rhythm']['startedAt']
        await p.action('SOLO_LEVER_DOWN')
        await p.next_state(lambda s:s['library']['rhythm']['held'])
        offsets=server.ROOMS[room_code]['libraryPuzzle']['beatOffsets']
        for i,off in enumerate(offsets):
            delay=max(0,(t0+off-server.now())/1000)
            await asyncio.sleep(delay + .10)
            await p.action('SOLO_LEVER_UP')
            await p.next_state(lambda s:s['library']['rhythm']['beatIndex']==i and not s['library']['rhythm']['held'])
            await p.action('SOLO_LEVER_DOWN')
            if i<2:
                await p.next_state(lambda s:s['library']['rhythm']['beatIndex']==i+1 and s['library']['rhythm']['held'])
        await p.next_state(lambda s:s['phase']=='library_solved')
        self.assertIsNotNone(p.state['librarySolution'])
        await asyncio.sleep(3.6)
        await p.action('CONTINUE_LIBRARY')
        await p.next_state(lambda s:s['phase']=='playing' and s['stage']=='crypt')
        self.assertIsNone(p.state['result'], 'Solo trial rank is earned after the Crypt, not before')
        await p.action('TRY_AGAIN')
        await p.next_state(lambda s:s['round']==2 and s['phase']=='lobby')
        await p.socket.close()

if __name__ == '__main__':
    unittest.main()
