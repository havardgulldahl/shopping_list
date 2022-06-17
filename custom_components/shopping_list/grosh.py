#!/usr/bin/env python
# coding: utf8
from __future__ import annotations

from json import JSONDecodeError
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, Union
from base64 import b64encode

from aiohttp import ClientResponse, ClientSession, InvalidURL, BasicAuth

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]

"""
This inofficial API implementation is based on communication with the 
awesome Grosh team. 

For information about Grosh please see groshapp.com

Everybody feel free to use it, but without any liability or warranty.

"""

GROSH_URL = "https://groshapp.com/edge"


class AuthentificationFailed(Exception):
    pass


class GroshApi:
    def __init__(
        self,
        username: str,
        password: str,
        session: ClientSession = None,
    ) -> None:
        self.username = username
        self.password = password
        self._translations = None
        self.GroshUUID = ""
        self.GroshListID = ""
        self.lists = []
        auth = BasicAuth(username, password)
        self.headers = {"Authorization": auth.encode()}
        #self.auth = BasicAuth(username, password)
        self.addheaders = {}
        self.session = session if session else ClientSession(headers=self.headers)
        self.logged = False
        self.selected_list = "Default"

    async def __aenter__(self) -> GroshApi:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """ Check the response returned by the Grosh API"""
        if response.status in [200, 204]:
            return
        elif response.status == 404:
            raise Exception(response.url, response.reason)

        try:
            result = await response.json(content_type=None)
        except JSONDecodeError:
            result = await response.text()
        if not result:
            result = None
        print(f"### Got {response.status=} {result=}")
        if response.status == 401:
            # we wait until here, so we get the full error message from Grosh
            raise AuthentificationFailed(response.url, result or response.reason)

        message = None
        if result.get("errorCode"):
            message = result.get("error")

        raise Exception(message if message else result)

    async def __get(
        self,
        url: str,
        endpoint: str,
        headers: Optional[JSON] = None,
        payload: Optional[JSON] = None,
        data: Optional[JSON] = None,
        params: Optional[JSON] = None,
    ) -> Any:
        """ Make a GET request to the Grosh API """
        async with self.session.get(
            f"{url}{endpoint}",
            #auth=self.auth,
            headers=headers,
            data=data,
            json=payload,
            params=params,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __put(
        self,
        endpoint: str,
        headers: Optional[JSON] = None,
        payload: Optional[JSON] = None,
        data: Optional[JSON] = None,
        params: Optional[JSON] = None,
    ) -> None:
        """ Make a PUT request to the Grosh API """
        async with self.session.put(
            f"{GROSH_URL}{endpoint}",
            #auth=self.auth,
            headers=headers,
            data=data,
            json=payload,
            params=params,
        ) as response:
            await self.check_response(response)

    async def login(self) -> None:
        try:
            #params = {"email": self.username, "password": self.password}
            login = await self.__get(GROSH_URL, "")
            """self.GroshUUID = login["uuid"]
            self.GroshListID = login["GroshListID"]
            self.headers = {
                "X-Grosh-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
                "X-Grosh-CLIENT": "android",
                "X-Grosh-USER-UUID": self.GroshUUID,
                "X-Grosh-VERSION": "303070050",
                "X-Grosh-COUNTRY": "de",
            }
            self.addheaders = {
                "X-Grosh-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
                "X-Grosh-CLIENT": "android",
                "X-Grosh-USER-UUID": self.GroshUUID,
                "X-Grosh-VERSION": "303070050",
                "X-Grosh-COUNTRY": "de",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }"""
            self.logged = True
        except (InvalidURL, ValueError):
            raise AuthentificationFailed("email password combination not existing")

    async def close(self) -> None:
        """Close the session."""
        await self.session.close()

    async def get_lists(self) -> None:
        lists = await self.__get(
            GROSH_URL, f"/users/me/households", headers=self.headers
        )
        print(f"Got lists: {lists}")
        self.lists = lists

    async def select_list(self, name):
        await self.get_lists()
        selected = next(
            (_list for _list in self.lists if _list.get("name") == name), None
        )
        if not selected:
            raise ValueError(f"List {name} does not exist")
        self.GroshListID = selected.get("id")
        self.selected_list = selected.get("name")
        print(f"### Selected {self.GroshListID=} - {self.selected_list=}")

    # return list of items from current list as well as recent items - translated if requested
    async def get_items(self, locale=None) -> dict:
        items = await self.__get(
            GROSH_URL, f"/households/{self.GroshListID}/current", headers=self.headers
        )
        print(f"### Got items ({self.GroshListID=}: {items}")

        """
        if locale:
            transl = await self.load_translations(locale)
            for item in items["purchase"]:
                item["name"] = transl.get(item["name"]) or item["name"]
            for item in items["recently"]:
                item["name"] = transl.get(item["name"]) or item["name"]
        """
        return items["groceries"]

    # return the details: Name, Image, UUID
    async def get_items_detail(self) -> dict:
        raise NotImplementedError

        items = await self.__get(
            Grosh_URL,
            f"Groshlists/{self.GroshListID}/details",
            headers=self.headers,
        )
        return items

    # add a new item to the current list with a given specification = additional description
    async def purchase_item(self, item):
        await self.__put(
            f"/households/{self.GroshListID}/bought/{item['id']}",
            headers=self.addheaders,
        )

    # add/move something to the recent items
    async def recent_item(self, item):
        raise NotImplementedError
        params = {"recently": item}
        await self.__put(
            f"Groshlists/{self.GroshListID}",
            params=params,
            headers=self.addheaders,
        )

    # remove an item completely (from recent and purchase)
    async def remove_item(self, item):
        raise NotImplementedError
        params = {"remove": item}
        await self.__put(
            f"Groshlists/{self.GroshListID}",
            params=params,
            headers=self.addheaders,
        )

    # search for an item in the list
    async def search_item(self, search):
        all_items = self.load_catalog()
        selected = next(
            (_itm for _itm in all_items if _itm.get("name") == name), None
        )
        return selected

    # // Hidden Icons? Don't know what this is used for
    async def load_products(self):
        raise NotImplementedError
        return await self.__get(Grosh_URL, "Groshproducts", headers=self.headers)

    # // Found Icons? Don't know what this is used for
    async def load_features(self):
        raise NotImplementedError
        return await self.__get(
            Grosh_URL,
            f"Groshusers/{self.GroshUUID}/features",
            headers=self.headers,
        )

    # load all list infos
    async def load_lists(self):
        raise NotImplementedError
        return await self.__get(
            Grosh_URL,
            f"Groshusers/{self.GroshUUID}/lists",
            headers=self.headers,
        )

    # get list of all users in list ID
    async def get_users_from_list(self, listUUID):
        raise NotImplementedError
        return await self.__get(
            Grosh_URL, f"Groshlists/{listUUID}/users", headers=self.headers
        )

    # get settings from user
    async def get_user_settings(self):
        raise NotImplementedError
        return await self.__get(
            Grosh_URL,
            f"Groshusersettings/{self.GroshUUID}",
            headers=self.headers,
        )

    # Load translation file e. g. via 'de-DE'
    async def load_translations(self, locale):
        raise NotImplementedError
        if not self._translations:
            self._translations = await self.__get(
                "https://web.getGrosh.com/", f"locale/articles.{locale}.json"
            )
        return self._translations

    async def translate_to_ch(self, item: str, locale) -> str:
        raise NotImplementedError
        for val, key in self.load_translations(locale).items():
            if key == item:
                return val
        return item

    # Load localized catalag of items
    async def load_catalog(self):
        return await self.__get(
            GROSH_URL,
            f"/groceries",
            headers=self.headers,
        )


if __name__=="__main__":
    import os 
    api = GroshApi(username=os.getenv("GROSHU"), password=os.getenv("GROSHP"))
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(api.get_lists())
    loop.run_until_complete(api.select_list("Einkaufsliste"))
    loop.run_until_complete(api.get_items())
    loop.run_until_complete(api.search_item("Toilettenpapier"))

