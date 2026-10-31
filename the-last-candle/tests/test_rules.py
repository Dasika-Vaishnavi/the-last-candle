"""Pure game-rule checks independent of network/web browsers."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server

class RulesTest(unittest.TestCase):
    def test_default_role_bundles(self):
        expected={
            2:[['medium','lantern','walker'],['archivist','locksmith']],
            3:[['medium','lantern'],['archivist','locksmith'],['walker']],
            4:[['medium','lantern'],['archivist'],['locksmith'],['walker']],
            5:[['medium'],['archivist'],['lantern'],['locksmith'],['walker']]
        }
        for n,bundles in expected.items():
            with self.subTest(players=n):
                room={'players':[{'id':str(i),'primaryRole':None,'roles':[]} for i in range(n)]}
                server.allocate_roles(room)
                self.assertEqual([p['roles'] for p in room['players']],bundles)

    def test_all_primary_role_combinations_have_asymmetric_clues(self):
        from itertools import permutations
        for n in range(2,6):
            for picks in permutations(server.ROLES,n):
                room={'players':[{'id':str(i),'primaryRole':role,'roles':[]} for i,role in enumerate(picks)]}
                server.allocate_roles(room)
                self.assertEqual(set(r for p in room['players'] for r in p['roles']),set(server.ROLES))
                self.assertTrue(all(p['primaryRole'] in p['roles'] for p in room['players']))
                ar=next(p['id'] for p in room['players'] if 'archivist' in p['roles'])
                la=next(p['id'] for p in room['players'] if 'lantern' in p['roles'])
                self.assertNotEqual(ar,la)

    def test_clock_solution_matches_randomized_diary(self):
        seeds=set()
        for _ in range(50):
            puzzle=server.make_puzzle()
            seeds.add(puzzle['seed'])
            expected=[next(e['hour'] for e in puzzle['entries'] if e['symbol']==sym) for sym in server.ORDER]
            self.assertEqual(puzzle['solution'],expected)
            self.assertEqual(len(set(puzzle['solution'])),4)
            self.assertTrue(all(1<=h<=12 for h in puzzle['solution']))
        self.assertEqual(len(seeds),50)

    def test_server_timer_penalty_and_expiration(self):
        start=server.now()
        room={'phase':'playing','timer':{'deadlineAt':start+1200000,'startedAt':start,'totalPenaltyMs':0,'frozenRemainingMs':None},'result':None,'version':0,'code':'TEST'}
        server.apply_penalty(room,30000)
        self.assertEqual(room['timer']['deadlineAt'],start+1170000)
        self.assertEqual(room['timer']['totalPenaltyMs'],30000)
        self.assertFalse(server.expire(room))
        room['timer']['deadlineAt']=start-1
        # patch persistence (pure unit test no DB mutation)
        orig=server.persist
        server.persist=lambda x:None
        try: self.assertTrue(server.expire(room))
        finally:server.persist=orig
        self.assertEqual(room['phase'],'lost')
        self.assertEqual(room['timer']['frozenRemainingMs'],0)

if __name__=='__main__':unittest.main()
