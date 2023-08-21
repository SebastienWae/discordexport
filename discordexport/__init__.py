import logging
from datetime import datetime
from enum import Enum
from json import JSONEncoder
from pathlib import Path
from typing import Annotated, Literal, Optional, Self

import rich
import typer
from rich.logging import RichHandler
from simple_term_menu import TerminalMenu  # type: ignore[import]

from discordexport.discord import Discord

from .accounts import AccountFinder


class App:
    _log: logging.Logger
    _discord: Discord
    _token: Optional[str] = None
    _server_id: Optional[str] = None
    _channel_id: Optional[str] = None
    _output: Optional[Path] = None
    _channel_type: Optional[Literal["Server", "Discussion Channel"]] = None

    class LogLevel(str, Enum):
        debug = "debug"
        info = "info"
        warn = "warn"
        error = "error"
        quiet = "quiet"

    def run(
        self: Self,
        token: Annotated[str, typer.Option(help="Authentication token")] = "",
        server_id: Annotated[
            str,
            typer.Option(help="Server ID, leave empty for direct messages"),
        ] = "",
        channel_id: Annotated[str, typer.Option(help="Channel ID")] = "",
        output: Annotated[
            Optional[Path],
            typer.Option(help="Path to the output file"),
        ] = None,
        log: Annotated[
            LogLevel,
            typer.Option(help="Log level"),
        ] = LogLevel.info,
    ) -> None:
        self.setup_logging(log)
        self._output = output
        if len(token) == 0:
            self.get_token()
            if self._token is None:
                logging.error("No token provided")
                return
        else:
            self._token = token
        self._discord = Discord(self._token)
        if len(server_id) == 0 and len(channel_id) == 0:
            self.get_channel_type()
            if self._channel_type is None:
                logging.error("No channel type provided")
                return
            if self._channel_type == "Server":
                self.get_server_id()
                if self._server_id is None:
                    logging.error("No server ID provided")
                    return
        if len(channel_id) == 0:
            if self._channel_type == "Discussion Channel":
                self.get_dm_channel_id()
            else:
                self.get_server_channel_id()
            if self._channel_id is None:
                logging.error("No channel ID provided")
                return

        self.extract_messages()

    def setup_logging(self: Self, debug_level: LogLevel) -> None:
        level = logging.DEBUG
        if debug_level == self.LogLevel.info:
            level = logging.INFO
        elif debug_level == self.LogLevel.warn:
            level = logging.WARN
        elif debug_level == self.LogLevel.error:
            level = logging.ERROR
        elif debug_level == self.LogLevel.quiet:
            level = logging.CRITICAL

        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, omit_repeated_times=False)],
        )
        self._log = logging.getLogger("rich")

    def multi_choice_menu(self: Self, msg: str, options: list[str]) -> Optional[int]:
        rich.print(msg)
        terminal_menu = TerminalMenu(options, multi_select=False)
        res = terminal_menu.show()
        if res is None:
            return None
        print(options[int(res)])
        return int(res)

    def get_token(self: Self) -> None:
        finder = AccountFinder()
        accounts = finder.find_accounts()
        account_index = self.multi_choice_menu(
            "Please select an account:",
            [f"{account.email} ({account.source})" for account in accounts],
        )
        if account_index is None:
            self._token = None
        else:
            self._token = accounts[account_index].token

    def get_channel_type(self: Self) -> None:
        options = ["Server", "Discussion Channel"]
        chan_type = self.multi_choice_menu(
            "Do you want to export messages from a server or a discussion channel?",
            options,
        )
        if chan_type is None:
            self._channel_type = None
        elif chan_type == 0:
            self._channel_type = "Server"
        else:
            self._channel_type = "Discussion Channel"

    def get_server_id(self: Self) -> None:
        servers = self._discord.guilds()
        server_index = self.multi_choice_menu(
            "Select a server:",
            [f"{c.name}" for c in servers],
        )
        if server_index is None:
            self._server_id = None
        else:
            self._server_id = servers[server_index].uid

    def get_server_channel_id(self: Self) -> None:
        if self._server_id is not None:
            channels = self._discord.guild_channels(self._server_id)
            channel_index = self.multi_choice_menu(
                "Select a channel:",
                [f"{c.name}" for c in channels],
            )
            if channel_index is None:
                self._channel_id = None
            else:
                self._channel_id = channels[channel_index].uid

    def get_dm_channel_id(self: Self) -> None:
        discussions = self._discord.channels()
        discussion_index = self.multi_choice_menu(
            "Select a discussion channel:",
            [f"{c.name}" for c in discussions],
        )
        if discussion_index is None:
            self._channel_id = None
        else:
            self._channel_id = discussions[discussion_index].uid

    def extract_messages(self: Self) -> None:
        if self._channel_id is not None:
            messages = self._discord.messages(self._channel_id)
            if self._output is None:
                output = Path(
                    f"{self._channel_id}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.json",
                )
            self._log.info(f"Writing messages to {output}")
            with output.open("w") as f:
                f.write(JSONEncoder().encode(messages))


def main() -> None:
    typer.run(App().run)
