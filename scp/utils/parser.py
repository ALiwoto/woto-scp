from io import BytesIO
from pyrogram import types
import html
import re


def HumanizeTime(seconds: int) -> str:
    count = 0
    ping_time = ''
    time_list = []
    time_suffix_list = ['s', 'm', 'h', 'days']
    while count < 4:
        count += 1
        remainder, result = divmod(
            seconds, 60,
        ) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ', '

    time_list.reverse()
    ping_time += ':'.join(time_list)
    return ping_time


def getMediaAttr(
    message: types.Message,
    Attr: list,
):
    for attribute in Attr:
        attr = getattr(message, attribute)
        if attr:
            return attr


def checkToken(token: str) -> bool:
    token = re.findall(
        r'[0-9]{10}:[a-zA-Z0-9_-]{35}',
        token,
    )
    if len(token) == 0:
        return False, False
    else:
        return True, token[0]


def mention_user_html(user: types.User, name_limit: int = -1) -> str:
    if not user:
        return ""
    return f"<a href=tg://user?id={user.id}>{html.escape(get_name(user, name_limit))}</a>"
    

def fix_encoding(value: str) -> str:
    if not isinstance(value, str):
        return ""
    try:
        return value.strip().encode('utf-8')
    except: return ""


def split_all(value: str, *delimiters) -> list:
    regP = '|'.join(map(re.escape, delimiters))
    return remove_empty_strs(re.split(regP, value))

def remove_empty_strs(values: list[str]) -> list:
    myStrs: list[str] = []
    for s in values:
        if not is_invalid_str(s):
            myStrs.append(s)

    return myStrs

def is_invalid_str(value: str) -> bool:
    return not value or len(value.strip()) == 0 or value.isspace()

def to_output_file(value: str, file_name: str = "output.txt") -> BytesIO:
    f = BytesIO(fix_encoding(value))
    f.name = file_name
    return f


def html_mono(value, *argv) -> str:
    return f"<code>{html.escape(str(value))}</code>" + ''.join(argv)

def html_in_parantesis(value) -> str:
    if not value:
        return ": "
    return f" ({value}): "

def html_bold(value, *argv) -> str:
    return f"<b>{html.escape(str(value))}</b>" + ''.join(argv)


async def in_common_length(user: types.User) -> int:
    if not user:
        return 0
    return len(await user.get_common_chats())

async def html_in_common(user: types.User) -> str:
    if user.is_self:
        return html_in_parantesis(None)
    return html_in_parantesis(await in_common_length(user))

def get_name(user: types.User, name_limit: int = -1) -> str:
    if not user:
        return ""
    
    if len(user.first_name) > 0:
        return user.first_name if name_limit == -1 else user.first_name[:name_limit]
    
    if len(user.last_name) > 0:
        return user.last_name if name_limit == -1 else user.last_name[:name_limit]
    
    if len(user.username) > 0:
        return user.username if name_limit == -1 else user.username[:name_limit]
