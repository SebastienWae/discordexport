from typing import NoReturn, Self


class UnsupportedSystemError(Exception):
    def __init__(self: Self) -> None:
        super().__init__("Your system is currently not supported.")


def assert_never(value: NoReturn) -> NoReturn:
    msg = f"This code should never be reached, got: {value}"
    raise AssertionError(msg)
