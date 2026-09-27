"""Offline regression checks. Uses a temporary database, never altar.db."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
TEMP = tempfile.TemporaryDirectory()
os.environ['EL_REGRESO_DB'] = str(Path(TEMP.name) / 'test.db')
os.environ['EL_REGRESO_SLOW'] = '0'
from web import server
from solution import voice
voice.chain = lambda: []
from fastapi.testclient import TestClient


class StoryTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        for name in ('abuela', 'donchuy', 'mateo', 'tio'):
            server.CHECKPOINTER.delete_thread(name)
        for row in server._conn.execute('SELECT id FROM story_branches').fetchall():
            server.CHECKPOINTER.delete_thread(row[0])
        with server._conn:
            server._conn.execute('DELETE FROM story_branches')

    def send(self, ws, message):
        ws.send_json(message)
        events = []
        while True:
            event = ws.receive_json()
            events.append(event)
            if event['type'] in ('done', 'interrupt', 'error', 'forgotten'):
                return events

    def test_prepared_altar_album_and_isolated_persistent_branch(self):
        with self.client.websocket_connect('/ws') as ws:
            result = self.send(ws, {'action':'run','soul':'abuela','year':2021,'gifts':['cempasúchil','su']})
            self.assertEqual(result[-1]['type'], 'done', result)
            values = result[-1]['values']
            self.assertEqual(values['ofrenda'], ['cempasúchil','su'])
            self.assertTrue(values['visits'][0]['words'])
            self.assertTrue(values['visits'][0]['calaverita'])
            state = self.client.get('/api/state/abuela').json()
            source = next(x for x in state['history'] if x['can_fork'])
            result = self.send(ws, {'action':'fork','soul':'abuela','checkpoint':source['id'],'gifts':['şəkil','şam']})
            self.assertEqual(result[-1]['type'], 'done', result)
            after = self.client.get('/api/state/abuela').json()
            self.assertEqual(after['values'], state['values'])
            branch = after['branches'][0]
            self.assertEqual(branch['baseline'], state['values'])
            self.assertIn('şəkil', branch['values']['ofrenda'])
            self.assertEqual(len(branch['values']['visits']), 1)
            self.assertGreater(branch['values']['remembrance'], values['remembrance'])
            self.assertEqual(self.client.get('/api/state/mateo', params={'branch_id':branch['id']}).status_code,404)
            # A newly opened client can retrieve both persisted alternatives.
            self.assertEqual(TestClient(server.app).get('/api/state/abuela').json()['branches'][0]['id'], branch['id'])

    def test_empty_draft_interrupt_resume_and_next_year_reset(self):
        with self.client.websocket_connect('/ws') as ws:
            result=self.send(ws, {'action':'run','soul':'mateo','year':2021,'gifts':[]})
            self.assertEqual(result[-1]['type'],'interrupt',result)
            self.assertTrue(self.client.get('/api/state/mateo').json()['interrupt'])
            self.assertEqual(self.client.get('/api/state/mateo').json()['values']['ofrenda'],[])
            result=self.send(ws, {'action':'resume','soul':'mateo','gift':'cempasúchil'})
            self.assertEqual(result[-1]['type'],'done',result)
            result=self.send(ws, {'action':'run','soul':'mateo','year':2022})
            self.assertEqual(result[-1]['type'],'done',result)
            self.assertIn('süd',result[-1]['values']['ofrenda'])
            self.assertEqual(len(result[-1]['values']['visits']),2)

    def test_validation_keeps_socket_usable(self):
        with self.client.websocket_connect('/ws') as ws:
            for msg in ({'action':'run','soul':'../x','year':2021},
                        {'action':'run','soul':'abuela','year':9999},
                        {'action':'run','soul':'abuela','year':2021,'gifts':'bad'},
                        {'action':'fork','soul':'abuela','checkpoint':'missing','gifts':[]}):
                self.assertEqual(self.send(ws,msg)[-1]['type'],'error')
            self.assertEqual(self.send(ws,{'action':'run','soul':'abuela','year':2021,'gifts':['cempasúchil']})[-1]['type'],'done')

def tearDownModule():
    server._conn.close()
    TEMP.cleanup()

if __name__ == '__main__':
    unittest.main()
