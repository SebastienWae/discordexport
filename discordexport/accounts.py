import logging
import platform
import sqlite3
from pathlib import Path
from typing import ClassVar, Literal, NamedTuple, Self, assert_never

import plyvel  # type: ignore[import]

from .utils import UnsupportedSystemError

log = logging.getLogger("rich")


class Account(NamedTuple):
    email: str
    token: str
    source: str


class AccountFinder:
    _OS: Literal["linux"]
    _accounts: ClassVar[set[Account]] = set()

    def __init__(self: Self) -> None:
        match platform.system():
            case "Linux":
                self._OS = "linux"
            case _:
                raise UnsupportedSystemError

    def find_accounts(self: Self) -> list[Account]:
        self._find_accounts_firefox()
        self._find_accounts_chromium()
        # self._find_accounts_discord_app() - FIXME: not working yet, returns 401
        return list(self._accounts)

    def _find_accounts_firefox(self: Self) -> None:
        log.info("Searching for accounts in Firefox")
        profiles_dir: Path
        match self._OS:
            case "linux":
                profiles_dir = Path("~/.mozilla/firefox").expanduser()
            case _:
                assert_never(self.OS)

        dbs = profiles_dir.glob("*/storage/default/https+++discord.com/ls/data.sqlite")
        for db in dbs:
            con = sqlite3.connect(db)
            cur = con.cursor()
            query = cur.execute(
                "SELECT key, value FROM data WHERE key='email_cache' OR key='token'",
            )
            res = query.fetchall()
            email = ""
            token = ""
            if len(res) == 2:  # noqa: PLR2004
                for key, value in res:
                    if key == "email_cache":
                        email = value.decode("utf-8")[1:-1]
                    elif key == "token":
                        token = value.decode("utf-8")[1:-1]
                if len(email) > 0 and len(token) > 0:
                    self._accounts.add(Account(email, token, "Firefox"))

    def _find_accounts_chromium(self: Self) -> None:
        log.info("Searching for accounts in Chromium")
        profiles_dir: Path
        match self._OS:
            case "linux":
                profiles_dir = Path("~/.config/chromium").expanduser()
            case _:
                assert_never(self.OS)

        dbs = profiles_dir.glob("*/Local Storage/leveldb")
        for db in dbs:
            self._chromium_extract_account(str(db), "Chromium")

    # def _find_accounts_discord_app(self: Self) -> None:
    #     log.info("Searching for accounts in Discord app")
    #     leveldb_path: Path
    #     match self._OS:
    #         case "linux":
    #             leveldb_path = Path(
    #                 "~/.config/discord/Local Storage/leveldb",
    #             ).expanduser()
    #         case _:
    #             assert_never(self.OS)

    #     self._chromium_extract_account(str(leveldb_path), "Discord app")

    def _chromium_extract_account(self: Self, db_path: str, source: str) -> None:
        try:
            db = plyvel.DB(str(db_path))
            email = db.get(b"_https://discordapp.com\x00\x01email_cache")
            token = db.get(b"_https://discordapp.com\x00\x01token")
            if email is not None and token is not None:
                self._accounts.add(
                    Account(
                        email.decode("utf-8")[2:-1],
                        token.decode("utf-8")[2:-1],
                        source,
                    ),
                )
        except OSError:
            log.warning(f"{source}, is running. Please close it and try again.")
        except plyvel.Error:
            log.warning(f"Error while reading {source} database.")
