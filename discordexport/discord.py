import logging
from datetime import datetime
from time import sleep
from typing import Any, NamedTuple, Optional, Self

from requests import PreparedRequest, Response, get
from requests.auth import AuthBase
from requests.exceptions import RequestException


class DiscordAuth(AuthBase):
    def __init__(self: Self, token: str) -> None:
        self.token = token

    def __call__(self: Self, r: PreparedRequest) -> PreparedRequest:
        r.headers["Authorization"] = self.token
        return r


class DiscordUser(NamedTuple):
    uid: str
    name: str


class DiscordChannel:
    uid: str
    name: str

    def __init__(self: Self, data: Any) -> None:  # noqa: ANN401
        self.uid = data["id"]
        if "name" in data and data["name"] is not None:
            self.name = data["name"]
        else:
            names = [recipient["username"] for recipient in data["recipients"]]
            self.name = ", ".join(names)


class DiscordGuild(NamedTuple):
    uid: str
    name: str


class Discord:
    _API_URL = "https://discord.com/api/v10/"
    _token: str
    _log = logging.getLogger("rich")

    def __init__(self: Self, token: str) -> None:
        self._token = token

    def _api_get(
        self: Self,
        endpoint: str,
        params: Optional[dict[str, str]] = None,
        tries: int = 0,
    ) -> Optional[Response]:
        self._log.debug(f"Requesting {endpoint}, {params}")
        if params is None:
            params = {}
        try:
            r = get(
                f"{self._API_URL}{endpoint}",
                params=params,
                auth=DiscordAuth(self._token),
                timeout=5,
            )
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                time = r.json()["retry_after"] + 1
                self._log.warning(f"Rate limit exceeded, waiting {time} seconds")
                sleep(time)
            if tries < 3:
                self._log.debug(f"Retrying request to {endpoint} ({tries + 1}/3))")
                return self._api_get(endpoint, params, tries + 1)
        except RequestException:
            self._log.exception("Request failed")
            if tries < 3:
                self._log.debug(f"Retrying request to {endpoint} ({tries + 1}/3))")
                return self._api_get(endpoint, params, tries + 1)
        return None

    def me(self: Self) -> Optional[DiscordUser]:
        r = self._api_get("users/@me")
        return None if r is None else DiscordUser(r.json()["id"], r.json()["username"])

    def channels(self: Self) -> list[DiscordChannel]:
        channels: list[DiscordChannel] = []
        r = self._api_get("users/@me/channels")
        if r is not None:
            for c in r.json():
                if c["type"] == 1:
                    channels.append(DiscordChannel(c))  # noqa: PERF401
        return channels

    def guilds(self: Self) -> list[DiscordGuild]:
        guilds: list[DiscordGuild] = []
        params = {"limit": "100", "after": "0"}
        while True:
            r = self._api_get("users/@me/guilds", params)
            if r is not None:
                data = r.json()
                if len(data) > 0:
                    guilds.extend([DiscordGuild(el["id"], el["name"]) for el in data])
                    params["after"] = data[-1]["id"]
                    continue
            break
        return guilds

    def guild_channels(self: Self, guild_id: str) -> list[DiscordChannel]:
        channels: list[DiscordChannel] = []
        r = self._api_get(f"guilds/{guild_id}/channels")
        if r is not None:
            for c in r.json():
                if c["type"] == 0:
                    channels.append(DiscordChannel(c))  # noqa: PERF401
        return channels

    def messages(
        self: Self,
        channel_id: str,
    ) -> list[Any]:
        messages: list[Any] = []
        params = {"limit": "100", "after": "0"}
        while True:
            r = self._api_get(f"channels/{channel_id}/messages", params)
            if r is not None:
                data = r.json()
                if len(data) > 0:
                    messages.extend(data)
                    params["after"] = data[0]["id"]
                    continue
            break
        return messages
