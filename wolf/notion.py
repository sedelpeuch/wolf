"""
This module contains the Notion class, which is a subclass of the API class. It is used to interact with the Notion API.
The Notion API is documented here: https://developers.notion.com/reference/intro
"""

import json
import os

import requests

from wolf_core import api


class Notion(api.API):
    """
    The reference is your key to a comprehensive understanding of the Notion API.

    Integrations use the API to access Notion's pages, databases, and users.
    Integrations can connect services to Notion and build interactive experiences for users within Notion.
    Using the navigation on the left, you'll find details for objects and endpoints used in the API.

    https://developers.notion.com/reference/intro
    """

    def __init__(self):
        absolute_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(absolute_path, "token.json")) as f:
            token = json.load(f)["notion"]
            os.environ["NOTION_TOKEN"] = token

        ressources = {
            "pages": {
                "page_get": {"verb": "GET", "method": self.get_page, "params": str},
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
                "block_get": {"verb": "GET", "method": self.get_block, "params": str}},
            "create_database": {"verb": "POST", "method": self.create_database, "params": [str, dict],
                                "optional_params": str},
            "database": {
                "database_get": {"verb": "GET", "method": self.get_database, "params": str},
                "database_patch": {"verb": "PATCH", "method": self.patch_database, "params": str,
                                   "optional_params": [list, list, dict]},
                "database_query": {"verb": "POST", "method": self.query_database, "params": str,
                                   "optional_params": [dict, list, str, int]}
            },
            "user": {"verb": "GET", "method": self.get_user, "params": "", "optional_params": str},
            "search": {"verb": "POST", "method": self.search, "params": dict},
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
        :return: The response contains the block's data.
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

    def get_page(self, params):
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

    ##################################
    # Database: Notion API requests #
    ##################################

    def create_database(self, parent, properties, title=None):
        """
        Creates a database as a subpage in the specified parent page, with the specified properties' schema.
        Currently, the parent of a new database must be a Notion page.

        :param parent: The ID of the parent page.
        :param properties: The properties of the database.
        :param title: (optional) The title of the database.
        :return: The response contains the database's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/databases"
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {
            "parent": {"page_id": parent},
            "properties": properties,
            "title": title
        }
        response = requests.post(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def query_database(self, id, filter=None, sorts=None, start_cursor=None, page_size=None):
        """
        Gets a list of Pages contained in the database, filtered and ordered according to the filter conditions and
        sort criteria provided in the request.
        The response may contain fewer than page_size of results.
        If the response includes a next_cursor value, refer to the pagination reference for details about how to use a
        cursor to iterate through the list.

        Filters are similar to the filters provided in the Notion UI,
        where the set of filters and filter groups chained by "And"
        in the UI is equivalent to having each filter in the array of the compound "and" filter.
        The same set of filters chained by "Or" in the UI would be represented as filters in the array of the "or"
        compound filter.
        Filters operate on database properties and can be combined.
        If no filter is provided, all the pages in the database will be returned with pagination.

        :param id: The ID of the database.
        :param filter: (optional) The filter of the database.
        :param sorts: (optional) The sorts of the database.
        :param start_cursor: (optional) The start cursor of the database.
        :param page_size: (optional) The page size of the database.
        :return: The response contains the database's data.
        :rtype: api.RequestResponse
        """
        url = self._url + "/v1/databases/" + id + "/query"
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {
            "filter": filter,
            "sorts": sorts,
            "start_cursor": start_cursor,
            "page_size": page_size
        }
        response = requests.post(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def get_database(self, id):
        """
        Retrieves a database object — information that describes the structure and columns of a database —
        for a provided database ID. The response adheres to any limits to an integration’s capabilities.

        To fetch database rows rather than columns, use the "Query a database endpoint."

        :param id: The ID of the database.
        :return: A RequestResponse object containing the status code and data of the API request.
        """

        url = self._url + "/v1/databases/" + id
        header = self.oauth_header()
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    def patch_database(self, id, title=None, description=None, properties=None):
        """
        Updates the database object — the title, description, or properties — of a specified database.

        Returns the updated database object.

        Database properties represent the columns (or schema) of a database.
        To update the properties of a database, use the properties body param with this endpoint.
        Learn more about database properties in the database properties and Update database properties docs.

        To update a relation database property, share the related database with the integration.
        Learn more about relations on the database properties page.

        For an overview of how to use the REST API with databases, refer to the Working with databases guide.

        :param id: The ID of the database.
        :param title: (optional) The title of the database.
        :param description: (optional) The description of the database.
        :param properties: (optional) The properties of the database.
        :return: A RequestResponse object containing the status code and data of the API request.
        """

        url = self._url + "/v1/databases/" + id
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {
            "title": title,
            "description": description,
            "properties": properties
        }
        response = requests.patch(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    ##############################
    # Users: Notion API requests #
    ##############################

    def get_user(self, id=None):
        """
        Retrieves a user object using the ID specified in the request URL if id is specified,
        or retrieves all users that the integration has access to if id is not specified.

        :param id: The ID of the user.
        :return: A RequestResponse object containing the status code and data of the API request.
        """

        if id is None:
            url = self._url + "/v1/user"
        else:
            url = self._url + "/v1/users/" + id
        header = self.oauth_header()
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response

    ###############################
    # Search: Notion API requests #
    ###############################

    def search(self, query, sort=None, filter=None, start_cursor=None, page_size=None):
        """
        Searches all pages and child pages that are shared with the integration.
        The response may contain fewer than page_size of results.
        If the response includes a next_cursor value, refer to the pagination reference for details about how to use a
        cursor to iterate through the list.

        :param query: The query of the search.
        :param sort: (optional) The sort of the search.
        :param filter: (optional) The filter of the search.
        :param start_cursor: (optional) The start cursor of the search.
        :param page_size: (optional) The page size of the search.
        :return: A RequestResponse object containing the status code and data of the API request.
        """

        url = self._url + "/v1/search"
        header = self.oauth_header()
        header["Content-Type"] = "application/json"
        data = {
            "query": query,
            "sort": sort,
            "filter": filter,
            "start_cursor": start_cursor,
            "page_size": page_size
        }
        response = requests.post(url, headers=header, data=json.dumps(data))
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response


if __name__ == "__main__":
    notion = Notion()
    req = notion.get.block_children("011f57a503864878b9e777d80932706d")
    print(req.status_code)
    print(req.data)
