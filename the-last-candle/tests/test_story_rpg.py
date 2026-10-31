"""Ghost conversation + RPG acceptance tests. No external web service needed."""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp import ClientSession, WSMsgType
from aiohttp.test_utils import TestServer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server
import story_engine as story


class Socket:
    def __init__(self, ws):
        self.ws = ws
        self.seq = 0
        self.state = None
        self.welcome = None
    async def action(self, typ, **kwargs):
        self.seq += 1
        await self.ws.send_json({'type':typ, 'actionId':f'story-{id(self)}-{self.seq}', **kwargs})
    async def next(self, pred, timeout=5):
        async def read():
            while True:
                msg = await self.ws.receive()
                if msg.type != WSMsgType.TEXT:
                    raise AssertionError('Socket disconnected')
                packet = json.loads(msg.data)
                if packet['type']=='WELCOME': self.welcome = packet
                if packet['type']=='STATE': self.state = packet['state']
                if pred(packet): return packet
        return await asyncio.wait_for(read(),timeout)
    async def until(self,pred):
        return await self.next(lambda d:d['type']=='STATE' and pred(d['state']))


class StoryFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runner=TestServer(server.create_app())
        await self.runner.start_server()
        self.session=ClientSession()
        self.url=str(self.runner.make_url('/ws')).replace('http://','ws://')
    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.close()
        server.ROOMS.clear();server.LOCKS.clear();server.SOCKETS.clear();server.ADMISSION_ATTEMPTS.clear()
    async def player(self):
        return Socket(await self.session.ws_connect(self.url))
    async def duo(self):
        a,b=await self.player(),await self.player()
        await a.action('CREATE_ROOM',name='Ada',capacity=2)
        await a.next(lambda d:d['type']=='WELCOME'); await a.until(lambda s:s['phase']=='lobby')
        await b.action('JOIN_ROOM',name='Bram',code=a.welcome['roomCode'])
        await b.next(lambda d:d['type']=='WELCOME'); await b.until(lambda s:len(s['players'])==2)
        await a.action('SELECT_ROLE',role='medium')
        await a.until(lambda s:s['me']['primaryRole']=='medium')
        await b.action('SELECT_ROLE',role='archivist')
        await b.until(lambda s:s['me']['primaryRole']=='archivist')
        await a.action('SET_READY',ready=True);await b.action('SET_READY',ready=True)
        await a.until(lambda s:all(p['ready'] for p in s['players']))
        await a.action('START_GAME')
        await a.until(lambda s:s['phase']=='playing');await b.until(lambda s:s['phase']=='playing')
        return a,b

    async def test_two_players_share_same_authoritative_dice_and_different_replies(self):
        a,b=await self.duo()
        self.assertNotEqual(a.state['story']['ghost']['options'][0]['id'], b.state['story']['ghost']['options'][0]['id'])
        self.assertEqual(a.state['story']['ghost']['speakerId'],a.welcome['seatId'])
        # Helper uses their next turn to grant advantage to Ada.
        await b.action('HELP_SPEAKER')
        await a.until(lambda s:s['story']['ghost']['advantage'])
        await a.action('GHOST_REPLY',optionId=a.state['story']['ghost']['options'][0]['id'])
        await a.until(lambda s:s['story']['ghost']['exchange']==1)
        await b.until(lambda s:s['story']['ghost']['exchange']==1)
        self.assertEqual(a.state['story']['ghost']['speakerId'],a.welcome['seatId'])
        # On the next exchange choose the CHARM 12 option; mock the server die.
        opt=next(o for o in a.state['story']['ghost']['options'] if o['stat']=='CHARM')
        with patch.object(story,'roll_d20',side_effect=[4,17]):
            await a.action('GHOST_REPLY',optionId=opt['id'])
            await a.until(lambda s:s['story']['lastRoll'] is not None)
            await b.until(lambda s:s['story']['lastRoll'] is not None)
        r=a.state['story']['lastRoll']
        self.assertEqual(r['dice'],[4,17])
        self.assertEqual(r['modifier'],2)
        self.assertTrue(r['advantage'])
        self.assertEqual(b.state['story']['lastRoll'],r)
        self.assertEqual(b.state['story']['flags']['diceRolls'],1)
        self.assertEqual(b.state['story']['ghost']['warmth'],3)
        await a.ws.close(); await b.ws.close()

    async def test_solo_lens_dice_and_reconnection_preserve_flags(self):
        p=await self.player()
        await p.action('CREATE_SOLO')
        await p.next(lambda d:d['type']=='WELCOME'); await p.until(lambda s:s['phase']=='lobby')
        token=p.welcome['token'];room_id=p.welcome['roomId'];seat=p.welcome['seatId'];code=p.welcome['roomCode']
        await p.action('EQUIP_SOLO_ABILITY',role='medium');await p.until(lambda s:len(s['solo']['equippedAbilities'])==1)
        await p.action('EQUIP_SOLO_ABILITY',role='archivist');await p.until(lambda s:len(s['solo']['equippedAbilities'])==2)
        await p.action('START_SOLO');await p.until(lambda s:s['phase']=='playing')
        before=p.state['timer']['deadlineAt']
        await p.action('STEADY_BREATH');await p.until(lambda s:s['story']['ghost']['advantage'])
        self.assertEqual(p.state['timer']['deadlineAt'],before-30000)
        await p.action('GHOST_REPLY',optionId=p.state['story']['ghost']['options'][0]['id'])
        await p.until(lambda s:s['story']['ghost']['exchange']==1)
        check=next(o for o in p.state['story']['ghost']['options'] if o['stat']=='CHARM')
        with patch.object(story,'roll_d20',side_effect=[2,20]):
            await p.action('GHOST_REPLY',optionId=check['id'])
            await p.until(lambda s:s['story']['flags']['crits']==1)
        self.assertEqual(p.state['story']['lastRoll']['role'],'medium')
        self.assertEqual(p.state['timer']['deadlineAt'],before)
        await p.ws.close()
        p2=await self.player()
        await p2.action('RESUME_SEAT',roomId=room_id,token=token)
        await p2.next(lambda d:d['type']=='WELCOME')
        await p2.until(lambda s:s['story']['flags']['crits']==1)
        self.assertEqual(p2.welcome['seatId'],seat)
        self.assertEqual(p2.state['story']['ghost']['exchange'],2)
        self.assertEqual(len(server.ROOMS[code]['players']),1)
        self.assertEqual(p2.state['timer']['deadlineAt'],before)
        await p2.ws.close()

    async def test_foyer_ghost_closure_does_not_change_clock_solution(self):
        a,b=await self.duo()
        code=a.welcome['roomCode']
        target=server.ROOMS[code]['puzzle']['solution'][:]
        await b.action('SUBMIT_CLOCK_CODE',hours=target)
        await a.until(lambda s:s['phase']=='foyer_solved')
        await b.until(lambda s:s['phase']=='foyer_solved')
        self.assertTrue(a.state['story']['ghost']['closed'])
        self.assertIn('Tick, tick',a.state['story']['ghost']['goodbye'])
        self.assertEqual(server.ROOMS[code]['puzzle']['solution'],target)
        await a.ws.close();await b.ws.close()


class StoryRules(unittest.TestCase):
    def setUp(self):
        self.room=server.new_room('Ada',2)
        self.a,_=server.add_player(self.room,'Ada')
        self.b,_=server.add_player(self.room,'Bram')
        self.a['primaryRole']='medium';self.a['roles']=['medium','lantern','walker']
        self.b['primaryRole']='archivist';self.b['roles']=['archivist','locksmith']
        self.room['phase']='playing'
        start=server.now()
        self.room['timer']={'startedAt':start,'deadlineAt':start+1200000,'totalPenaltyMs':0,'frozenRemainingMs':None,'freezeUntil':None}
        story.enter_stage(self.room,'foyer')
    def tearDown(self):
        server.ROOMS.clear();server.LOCKS.clear();server.SOCKETS.clear()
    def finish_ghost(self):
        for _ in range(4):
            active=server.get_seat(self.room,story.stage_ghost(self.room)['speakerId'])
            opts=story.options(self.room,active)
            # Choose a plain, non-rude response; dice are tested separately.
            plain=next(o for o in opts if o['stat'] is None and o['tone'] != 'rude')
            story.reply(self.room,active,plain['id'])
        self.assertTrue(story.stage_ghost(self.room)['finished'])
    def test_vote_tie_rolloff_and_watch_item(self):
        self.finish_ghost()
        with patch.object(story,'roll_d20',side_effect=[4,19,18]):
            self.assertIsNone(story.vote(self.room,self.a,'watch'))
            result=story.vote(self.room,self.b,'leave')
        self.assertIsNotNone(result['tieRoll'])
        self.assertEqual(set(result['tieRoll']['diceByOption']),{'watch','leave'})
        self.assertEqual(self.room['story']['flags']['votesTaken'],2)
        self.assertTrue(self.room['story']['ghosts']['foyer']['crossroads'])
        self.assertEqual(self.room['story']['flags']['diceRolls'],2)
        self.assertIn('WATCH',self.room['story']['flags']['items'])
    def test_critical_and_fumble_and_nonnegative_warmth(self):
        with patch.object(story,'roll_d20',return_value=1):
            failed=story.skill_check(self.room,self.a,'CHARM',12)
        self.assertTrue(failed['fumble']); self.assertFalse(failed['success'])
        with patch.object(story,'roll_d20',return_value=20):
            success=story.skill_check(self.room,self.b,'WITS',16)
        self.assertTrue(success['critical']);self.assertTrue(success['success'])
        self.assertEqual(self.room['story']['flags']['fumbles'],1)
        self.assertEqual(self.room['story']['flags']['crits'],1)
    def test_cold_penalty_recovery_and_safe_resume(self):
        before=self.room['timer']['deadlineAt']
        cold=story.warmer(self.room,-3)
        self.assertTrue(cold)
        self.assertEqual(self.room['timer']['deadlineAt'],before-30000)
        self.assertTrue(story.stage_ghost(self.room)['coldUntil'])
        with self.assertRaisesRegex(ValueError,'not speaking'):
            story.reply(self.room,self.a,story.options(self.room,self.a)[0]['id'] if story.options(self.room,self.a) else 'bad')
        story.stage_ghost(self.room)['coldUntil']=story.timestamp()-1
        self.assertTrue(story.recover_cold(self.room))
        self.assertEqual(story.stage_ghost(self.room)['warmth'],1)
        self.assertEqual(self.room['timer']['deadlineAt'],before-30000)
    def test_crypt_wrong_turn_is_server_secret_until_ending(self):
        self.room['stage']='crypt'
        story.enter_stage(self.room,'crypt')
        # The Crypt is not yet a playable room; test its prepared decision state.
        for _ in range(1):
            active=server.get_seat(self.room,story.stage_ghost(self.room)['speakerId'])
            story.reply(self.room,active,story.options(self.room,active)[0]['id'])
        self.assertTrue(story.stage_ghost(self.room)['finished'])
        before=self.room['timer']['deadlineAt']
        story.vote(self.room,self.a,'trust')
        with patch.object(story,'roll_d20',return_value=2):
            outcome=story.vote(self.room,self.b,'trust')
        self.assertFalse(outcome['success'])
        self.assertTrue(self.room['story']['flags']['WRONG_TURN'])
        self.assertEqual(self.room['timer']['deadlineAt'],before-30000)
        self.assertNotIn('WRONG_TURN',story.public_story(self.room,self.a)['flags'])
        self.assertTrue(self.room['story']['flags']['WRONG_TURN'])

    def test_library_crossroads_pay_and_flags(self):
        self.room['stage']='library'; story.enter_stage(self.room,'library')
        for _ in range(4):
            active=server.get_seat(self.room,story.stage_ghost(self.room)['speakerId'])
            story.reply(self.room,active,story.options(self.room,active)[0]['id'])
        before=self.room['timer']['deadlineAt']
        story.vote(self.room,self.a,'pay')
        result=story.vote(self.room,self.b,'pay')
        self.assertEqual(result['choice'],'pay')
        self.assertEqual(self.room['timer']['deadlineAt'],before-30000)
        self.assertEqual(story.stage_ghost(self.room)['warmth'],3)

if __name__=='__main__':unittest.main()
