import unittest
from unittest.mock import Mock

from wolf_core.api import API, RequestResponse


class TestAPI(unittest.TestCase):

    def setUp(self):
        API.instances = []
        self.mock_logger = Mock()
        ressource = {
            'test_resource': {
                'verb': 'GET',
                'method': Mock(),
                'params': str
            }
        }
        self.api = API(url='http://test_url', token='test_token', ressources=ressource)
        self.api.ressources = ressource

    def test_process_sub_resource(self):
        self.api.set_method()

        self.assertTrue(hasattr(self.api.get, 'test_resource'))


class TestRequestResponse(unittest.TestCase):

    def setUp(self):
        self.req_resp = RequestResponse(200, {'test': 'data'})

    def test_init(self):
        with self.assertRaises(TypeError):
            RequestResponse('200', {'test': 'data'})
            RequestResponse(200, ['a', 'b', 'c'])

    def test_eq(self):
        self.assertEqual(self.req_resp, RequestResponse(200, {'test': 'data'}))
        self.assertNotEqual(self.req_resp, RequestResponse(404, {'test': 'data'}))


if __name__ == '__main__':
    unittest.main()
