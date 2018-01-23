import json
import unittest
from nose.tools import assert_equal
from bf.app import app
from bf.helpers import obj_name_is_valid


class BloomFunctionTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_invalid_url(self):
        rv = self.app.get('/random')

        assert_equal(json.loads(rv.data), {'error': 'invalid url'})

    def test_invalid_content_type(self):
        rv = self.app.post('/search', data=json.dumps(dict(
            objects=['test/jest/obj.jpg']
        )), headers={"Content-Type": "text/plain"})

        assert_equal(json.loads(rv.data), {'error': 'expected json'})

    def test_missing_keys(self):
        rv = self.app.post('/search', data=json.dumps(dict(
            abc=['test/jest/obj.jpg']
        )), headers={"Content-Type": "application/json"})
        assert_equal(json.loads(rv.data), {
            'error': """invalid json: expected  {"object": "some/test/obj.jpg"}"""})

    def test_search_incomplete_object(self):
        rv = self.app.post('/search', data=json.dumps(dict(
            object=['/incomplete/obj']
        )), headers={"Content-Type": "application/json"})

        obj_name_is_valid('/incomplete/obj')
        assert_equal(json.loads(rv.data), {"state": "FAILURE", "result": "No object found", 'task_id': None})

