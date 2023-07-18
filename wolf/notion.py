"""
This module contains the Notion class, which is a subclass of the API class. It is used to interact with the Notion API.
The Notion API is documented here: https://developers.notion.com/reference/intro
"""

# 286ecfe40ac34190960ca136e54901a8

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
            "pages": {"verb": "GET", "method": self.get_pages, "params": str},
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

    def get_pages(self, params):
        """
        Retrieve pages from Notion API.

        :param params: The parameters used to retrieve the pages.
        :return: The response containing the pages' data.

        """
        url = self._url + "/v1/pages/" + params
        header = self.oauth_header()
        header["accept"] = "application/json"
        response = requests.get(url, headers=header)
        request_response = api.RequestResponse(status_code=response.status_code, data=response.json())
        return request_response


if __name__ == "__main__":
    notion = Notion()
    print(notion.get.databases("str").status_code)
    print(notion.get.pages("str").status_code)
