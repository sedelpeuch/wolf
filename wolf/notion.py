"""
This module contains the Notion class, which is a subclass of the API class. It is used to interact with the Notion API.
The Notion API is documented here: https://developers.notion.com/reference/intro
"""

import json
import os

import requests

from wolf_core import api


class Notion(api.API):
    def __init__(self):
        absolute_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(absolute_path, "token.json")) as f:
            token = json.load(f)["notion"]

        ressources = {
            "databases": {"verb": "GET", "method": self.get_databases, "params": str},
            "pages": {
                "page_get": {"verb": "GET", "method": self.get_pages, "params": str},
                "page_post": {"verb": "POST", "method": self.post_page, "params": [str, dict],
                              "optional_params": [list, dict, dict, dict]}},
            "page_property": {
                "property_get": {"verb": "GET", "method": self.get_page_property, "params": [str, str]},
                "property_patch": {"verb": "PATCH", "method": self.patch_page_property,
                                   "params": str, "optional_params": [dict, bool]}},
            "block_children": {
                "block_append": {"verb": "PATCH", "method": self.append_block_children, "params": [str, list],
                                 "optional_params": str},
                "block_children": {"verb": "GET", "method": self.get_block_children, "params": str}},
            "block": {
                "block_patch": {"verb": "PATCH", "method": self.update_block, "params": [str, dict]},
                "block_delete": {"verb": "DELETE", "method": self.delete_block, "params": str},
                "block_get": {"verb": "GET", "method": self.get_block, "params": str}}
        }

        super().__init__(url="https://api.notion.com", test_url="", token=token, ressources=ressources)

    def oauth_header(self):
        """
        Generate the OAuth header for API requests.

        :return: The OAuth header.
        :rtype: dict
        """
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": "2022-06-28",
            "accept": "application/json"
        }

    ##############################
    # Block: Notion API requests #
    ##############################

    def append_block_children(self, block_id, children, after=None):
        """
        Append children to a block.

        :param block_id: The ID of the block.
        :param children: The children to append.
        Must be a list of block objects.
        :param after: (optional) The child block to add the new children after.
            Default is None, which appends the children at the end of the block.
        :return: The response contains the block's data.
        :rtype: api.RequestResponse
        :raises TypeError: If the "children" parameter is not a list of block objects.
        """
        url = self._url + "/v1/blocks/" + block_id + "/children"
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {"children": children} if after is None else {"children": children, "after": after}
        response = requests.patch(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def get_block(self, block_id):
        """
        Retrieve a block from Notion API.

        :param block_id: The ID of the block.
        :return: The response contains the block's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/blocks/" + block_id
        header = self.oauth_header()
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def get_block_children(self, block_id):
        """
        Retrieve a block's children from Notion API.

        :param block_id: The ID of the block.
        :return: The response contains the block's children.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/blocks/" + block_id + "/children"
        header = self.oauth_header()
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def update_block(self, block_id, data, archived=False):
        """
        Update a block from Notion API.

        :param archived: Boolean value indicating whether the block should be archived or not.
        :param block_id: The ID of the block to update.
        :param data: The data to update the block with.
        :return: The response containing the block's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/blocks/" + block_id
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data["archived"] = archived
        response = requests.patch(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def delete_block(self, block_id):
        """
        Delete a block from Notion API.

        :param block_id: The ID of the block.
        :return: The response contains the block's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/blocks/" + block_id
        header = self.oauth_header()
        response = requests.delete(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    ##############################
    # Page: Notion API requests #
    ##############################

    def post_page(self, parent_id, properties, children=None, icon=None, cover=None):
        """
        Create a page in Notion.

        :param parent_id: The ID of the parent page.
        :param properties: The properties of the page.
        :param children: (optional) The children of the page.
        :param icon: (optional) The icon of the page.
        :param cover: (optional) The cover of the page.
        :return: The response contains the page's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/pages"
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {
            "parent": {"page_id": parent_id},
            "properties": properties,
            "children": children,
            "icon": icon,
            "cover": cover
        }
        response = requests.post(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def get_pages(self, params):
        """
        Retrieve pages from Notion API.

        :param params: The parameters used to retrieve the pages.
        :return: The response contains the pages' data.

        """
        url = self._url + "/v1/pages/" + params
        header = self.oauth_header()
        header["accept"] = "application/json"
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def get_page_property(self, page_id, property_id):
        """
        Retrieve a page's property from Notion API.

        :param page_id: The ID of the page.
        :param property_id: The id of the property.
        :return: The response contains the page's property.
        """
        url = self._url + "/v1/pages/" + page_id + "/properties/" + property_id
        header = self.oauth_header()
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def patch_page_property(self, page_id, property=None, archived=False):
        """
        Update a page's property from Notion API.

        :param archived: Boolean value indicating whether the page should be archived or not.
        :param page_id: The ID of the page.
        :param property: The property to update.
        :return: The response contains the page's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/pages/" + page_id
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {"archived": archived} if property is None else {"archived": archived, "properties": property}
        response = requests.patch(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def get_databases(self, params):
        """
        Retrieves information about a Notion database.

        :param params: The ID of the database.
        :return: A RequestResponse object containing the status code and data of the API request.
        """

        url = self._url + "/v1/databases/" + params
        header = self.oauth_header()
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response


if __name__ == "__main__":
    notion = Notion()
