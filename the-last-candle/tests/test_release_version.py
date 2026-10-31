"""Guard against accidentally uploading the Stage 1-only server again."""
import unittest
from aiohttp.test_utils import TestClient, TestServer
import server


class ReleaseVersionTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_advertises_full_four_stage_release(self):
        async with TestServer(server.create_app()) as srv:
            async with TestClient(srv) as client:
                async with client.get('/health') as response:
                    self.assertEqual(response.status, 200)
                    data = await response.json()
                    self.assertEqual(data['release'], 'stage-4-complete')
                    self.assertEqual(data['chapters'], 4)
                    self.assertEqual(data['status'], 'ok')

    def test_all_four_engines_are_included(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        for filename in ['story_engine.py','crypt_engine.py','finale_engine.py']:
            with self.subTest(filename=filename):
                self.assertTrue((root / filename).is_file())


if __name__ == '__main__':
    unittest.main()
