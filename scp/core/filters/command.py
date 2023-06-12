import logging
import re
from traceback import format_exc
from typing import List, Union
import pyrogram
from pyrogram.filters import (
    create,
    command as p_command
)
from pyrogram.types import Message
from pyrogram import Client
from scp.utils.selfInfo import info
from ...woto_config import the_config

prefixes = the_config.prefixes


def command_OLD(
    commands: str or List[str],
    prefixes: str or List[str] = the_config.prefixes,
    case_sensitive: bool = False,
):
    """
    This is a drop in replacement for the
    default filters.command that is included
    in Pyrogram. The Pyrogram one does not support
    /command@botname type commands,
    so this custom filter enables that throughout
    all groups and private chats.
    This filter works exactly the same as the original
    command filter even with support for multiple command
    prefixes and case sensitivity.
    Command arguments are given to user as message.command
    """

    async def func(flt, _: Client, message: Message):
        try:
            text: str = message.text or message.caption
            message.command = None
            if not text:
                return False
            if message.from_user != None and message.text.lower().find("@me") != -1:
                text = text.replace("@me", f"@{message.from_user.username}")

            regex = r'(?i)^({prefix})({regex})(@{bot_name})?(\s.*)?$'.format(
                prefix='|'.join(re.escape(x) for x in flt.prefixes),
                regex='|'.join(flt.commands),
                bot_name=info['_user_username'].lower(),
            )
            if matches := re.search(regex, text, flags=re.IGNORECASE):
                message.command = [matches.group(2)]
                if matches.group(4):  # The command has arguments
                    message.command.extend(
                        [arg for arg in matches.group(4).strip().split()],
                    )
                return True
            return p_command()
        except Exception:
            logging.error(format_exc())

    try:
        commands = commands if isinstance(commands, list) else [commands]
        commands = {c if case_sensitive else c.lower() for c in commands}
        prefixes = prefixes or []
        prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
        prefixes = set(prefixes) if prefixes else {''}
        return create(
            func,
            'CustomUserCommandFilter',
            commands=commands,
            prefixes=prefixes,
            case_sensitive=case_sensitive,
        )
    except Exception:
        logging.error(format_exc())


def command(
    commands: Union[str, List[str]], 
    prefixes: Union[str, List[str]] = the_config.prefixes, 
    case_sensitive: bool = False,
):
    """Filter commands, i.e.: text messages starting with "/" or any other custom prefix.

    Parameters:
        commands (``str`` | ``list``):
            The command or list of commands as string the filter should look for.
            Examples: "start", ["start", "help", "settings"]. When a message text containing
            a command arrives, the command itself and its arguments will be stored in the *command*
            field of the :obj:`~pyrogram.types.Message`.

        prefixes (``str`` | ``list``, *optional*):
            A prefix or a list of prefixes as string the filter should look for.
            Defaults to "/" (slash). Examples: ".", "!", ["/", "!", "."], list(".:!").
            Pass None or "" (empty string) to allow commands with no prefix at all.

        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, command="Start" would trigger /Start but not /start.
    """
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

    async def func(flt, client: pyrogram.Client, message: Message):
        try:
            username = client.me.username or ""
            text = message.text or message.caption
            message.command = None

            if not text:
                return False

            if message.from_user != None and text.lower().find("@me") != -1:
                text = text.replace("@me", f"@{message.from_user.username}")

            for prefix in flt.prefixes:
                if not text.startswith(prefix):
                    continue

                without_prefix = text[len(prefix):]

                for cmd in flt.commands:
                    if not re.match(rf"^(?:{cmd}(?:@?{username})?)(?:\s|$)", without_prefix,
                                    flags=re.IGNORECASE if not flt.case_sensitive else 0):
                        continue

                    without_command = re.sub(rf"{cmd}(?:@?{username})?\s?", "", without_prefix, count=1,
                                            flags=re.IGNORECASE if not flt.case_sensitive else 0)

                    # match.groups are 1-indexed, group(1) is the quote, group(2) is the text
                    # between the quotes, group(3) is unquoted, whitespace-split text

                    # Remove the escape character from the arguments
                    message.command = [cmd] + [
                        re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                        for m in command_re.finditer(without_command)
                    ]

                    return True

            return False
        except Exception:
            logging.error(format_exc())

    commands = commands if isinstance(commands, list) else [commands]
    commands = {c if case_sensitive else c.lower() for c in commands}

    prefixes = [] if prefixes is None else prefixes
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    prefixes = set(prefixes) if prefixes else {""}

    return create(
        func,
        "CommandFilter",
        commands=commands,
        prefixes=prefixes,
        case_sensitive=case_sensitive
    )
