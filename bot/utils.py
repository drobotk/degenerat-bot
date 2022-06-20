import typing
from urllib.parse import urlparse

import discord
from discord.ext import commands
from discord import app_commands


def is_url(x: str) -> bool:
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])

    except:
        return False


def dots_after(inp: str, length: int) -> str:
    if len(inp) <= length:
        return inp

    return inp[: length - 3] + "..."


def sub_before(a: str, b: str, c: typing.Optional[str] = None) -> str:
    idx = a.find(b)
    if idx < 0:
        return c or a

    return a[:idx]
