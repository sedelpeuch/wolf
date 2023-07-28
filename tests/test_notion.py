import unittest
from unittest.mock import patch

from wolf.notion import Notion


class TestNotionBlock(unittest.TestCase):

    @patch('requests.patch')
    def test_append_block_children(self, mock_patch):
        mock_patch.return_value.json.return_value = {"test": "value"}
        mock_patch.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.append_block_children("block_id", [{"object": "block", "type": "paragraph"}])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.get')
    def test_get_block(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_block("block_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.get')
    def test_get_block_children(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_block_children("block_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.patch')
    def test_update_block(self, mock_patch):
        mock_patch.return_value.json.return_value = {"test": "value"}
        mock_patch.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.update_block("block_id", {"title": "Updated title"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.delete')
    def test_delete_block(self, mock_delete):
        mock_delete.return_value.json.return_value = {"test": "value"}
        mock_delete.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.delete_block("block_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})


class TestNotionDatabase(unittest.TestCase):

    @patch('requests.get')
    def test_get_database(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_database("database_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.patch')
    def test_patch_database(self, mock_patch):
        mock_patch.return_value.json.return_value = {"test": "value"}
        mock_patch.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.patch_database("database_id", title="Updated title")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.post')
    def test_query_database(self, mock_post):
        mock_post.return_value.json.return_value = {"test": "value"}
        mock_post.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.query_database("database_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})


class TestNotionPage(unittest.TestCase):

    @patch('requests.get')
    def test_get_page(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_page("params")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.post')
    def test_post_page(self, mock_post):
        mock_post.return_value.json.return_value = {"test": "value"}
        mock_post.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.post_page("parent_id", {"title": "Page Title"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.get')
    def test_get_page_property(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_page_property("page_id", "property_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.patch')
    def test_patch_page_property(self, mock_patch):
        mock_patch.return_value.json.return_value = {"test": "value"}
        mock_patch.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.patch_page_property("page_id", {"title": "Updated Title"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})


class TestNotionUsersAndSearch(unittest.TestCase):

    @patch('requests.get')
    def test_get_user(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_user("user_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.get')
    def test_get_all_users(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_user()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.post')
    def test_search(self, mock_post):
        mock_post.return_value.json.return_value = {"test": "value"}
        mock_post.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.search({"query": "query"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})


class TestNotionDatabaseActions(unittest.TestCase):

    @patch('requests.get')
    def test_get_databases(self, mock_get):
        mock_get.return_value.json.return_value = {"test": "value"}
        mock_get.return_value.status_code = 200
        notion = Notion(test=True)
        resp = notion.get_databases("database_id")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})

    @patch('requests.post')
    def test_create_database(self, mock_post):
        mock_post.return_value.json.return_value = {"test": "value"}
        mock_post.return_value.status_code = 200
        notion = Notion(test=True)
        properties = {"Name": {"title": []}, "Description": {"rich_text": []}}
        resp = notion.create_database("parent_id", properties, title="Test Database")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"test": "value"})


if __name__ == "__main__":
    unittest.main()
