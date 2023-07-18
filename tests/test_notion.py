#! /usr/bin/env python3
"""
This module test notion class
"""
from unittest import TestCase, mock
from unittest.mock import MagicMock

from wolf_core import api
from wolf import notion


class NotionTest(TestCase):
    """
    Testing Notion class
    """

    def setUp(self):
        """
        Initializes the NotionTest class.

        :return: None
        """
        self.notion = notion.Notion()
        self.notion._token = "mock_token"

    @mock.patch('requests.get')
    def test_get_databases(self, mock_get):
        """
        Test get_databases method
        """
        # Arrange the mock return value
        mock_resp_instance = MagicMock()
        expected_resp = api.RequestResponse(status_code=200, data={})
        mock_resp_instance.json.return_value = expected_resp.data
        mock_resp_instance.status_code = expected_resp.status_code

        # Connect the mock
        mock_get.return_value = mock_resp_instance

        # Call the method
        response = self.notion.get_databases('test_params')

        # Test that the method behaves as expected
        self.assertEqual(expected_resp, response)
        mock_get.assert_called_once_with(self.notion._url + "/v1/databases/" + 'test_params',
                                         headers=self.notion.oauth_header())

    @mock.patch('requests.get')
    def test_get_pages(self, mock_get):
        """
        Test get_pages method
        """
        # Arrange the mock return value
        mock_resp_instance = MagicMock()
        expected_resp = api.RequestResponse(status_code=200, data={})
        mock_resp_instance.json.return_value = expected_resp.data
        mock_resp_instance.status_code = expected_resp.status_code

        # Connect the mock
        mock_get.return_value = mock_resp_instance

        # Call the method
        response = self.notion.get_pages('test_params')

        # Test that the method behaves as expected
        self.assertEqual(expected_resp, response)
        mock_get.assert_called_once_with(self.notion._url + "/v1/pages/" + 'test_params',
                                         headers=self.notion.oauth_header())

    def test_oauth_header(self):
        """
        Test oauth_header method
        """
        # Call the method
        header = self.notion.oauth_header()

        # Test that the method behaves as expected
        expected_header = {
            "Authorization": f"Bearer mock_token",
            "Notion-Version": "2022-06-28",
            "accept": "application/json"
        }
        self.assertEqual(expected_header, header)

    @mock.patch('requests.get', side_effect=Exception('mocked error'))
    def test_get_databases_exception(self, mock_get):
        """
        Test get_databases method when an exception is raised by requests.get
        """
        # Call the method and test that it raises an exception
        with self.assertRaises(Exception) as context:
            self.notion.get_databases('test_params')

        self.assertTrue('mocked error' in str(context.exception))

    @mock.patch('requests.get', side_effect=Exception('mocked error'))
    def test_get_pages_exception(self, mock_get):
        """
        Test get_pages method when an exception is raised by requests.get
        """
        # Call the method and test that it raises an exception
        with self.assertRaises(Exception) as context:
            self.notion.get_pages('test_params')

        self.assertTrue('mocked error' in str(context.exception))
