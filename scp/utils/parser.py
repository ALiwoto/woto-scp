from io import BytesIO
from typing import Union
from pyrogram import types
import html
import re
from pyrogram.client import Client

from pyrogram.types import (
    User,
    Chat,
)



class PurgeFlags:
    """
        all
        me
        text
        sticker
        gif
        service
        media
        bot
        via_bot
        new_chat_members:: join
        left_chat_member:: left
        new_chat_title:: new_title
        new_chat_photo:: new_photo
        delete_chat_photo:: del_photo
        group_chat_created:: group_created
        supergroup_chat_created:: supergroup_created
        channel_chat_created:: channel_created
        migrate_to_chat_id:: migrated_to
        migrate_from_chat_id:: migrated_from
        pinned_message:: pinned
    """
    flag_all: bool = False
    flag_me: bool = False
    flag_text: bool = False
    flag_sticker: bool = False
    flag_gif: bool = False
    flag_service: bool = False
    flag_media: bool = False
    flag_bot: bool = False
    flag_via_bot: bool = False
    flag_join: bool = False
    flag_left: bool = False
    flag_new_title: bool = False
    flag_new_photo: bool = False
    flag_del_photo: bool = False
    flag_group_created: bool = False
    flag_supergroup_created: bool = False
    flag_channel_created: bool = False
    flag_migrated_to: bool = False
    flag_migrated_from: bool = False
    flag_pinned: bool = False

    def __init__(self, flags: str):
        if not isinstance(flags, str) or len(flags) < 2:
            self.flag_text = True
            return
        
        flags = flags.lower().strip()
        self.flag_all = 'all' in flags
        self.flag_me = 'me' in flags
        self.flag_text = 'text' in flags
        self.flag_sticker = 'sticker' in flags
        self.flag_gif = 'gif' in flags or 'animation' in flags
        self.flag_service = 'service' in flags
        self.flag_media = 'media' in flags
        self.flag_bot = 'bot' in flags
        self.flag_via_bot = 'via_bot' in flags
        self.flag_join = 'join' in flags
        self.flag_left = 'left' in flags
        self.flag_new_title = 'new_title' in flags
        self.flag_new_photo = 'new_photo' in flags
        self.flag_del_photo = 'del_photo' in flags
        self.flag_group_created = 'group_created' in flags
        self.flag_supergroup_created = 'supergroup_created' in flags
        self.flag_channel_created = 'channel_created' in flags
        self.flag_migrated_to = 'migrated_to' in flags
        self.flag_migrated_from = 'migrated_from' in flags
        self.flag_pinned = 'pinned' in flags




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

def split_some(value: str, max_count: int = -1, *delimiters) -> list:
    regP = '|'.join(map(re.escape, delimiters))
    return remove_empty_strs(re.split(regP, value, max_count))

def contains_str(value: str, *substrs) -> bool:
    if substrs is None:
        return False
    try:    
        for current in substrs:
            if isinstance(current, str):
                if value.count(current) > 0:
                    return True
            else:
                if value.count(str(current)) > 0:
                    return True
        
        return False
    except Exception: return False

def remove_empty_strs(values: list) -> list:
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
    return f"<code>{html.escape(str(value))}</code>" +  get_html_normal(*argv)

def html_in_parantesis(value) -> str:
    if not value:
        return ": "
    return f" ({ html.escape(value)}): "

def html_bold(value, *argv) -> str:
    return f"<b>{html.escape(str(value))}</b>" + get_html_normal(*argv)


def html_link(value, link: str, *argv) -> str:
    if not isinstance(link, str) or len(link) == 0:
        return html_mono(value, *argv)
    return f"<a href={html.escape(link)}>{html.escape(str(value))}</a>" +  get_html_normal(*argv)

async def html_normal_chat_link(value, chat: Chat, *argv) -> str:
    if not isinstance(chat, Chat):
        return html_mono(value, *argv)
    link: str = ''
    if not isinstance(chat.username, str) or len(chat.username) == 0:
        count = 1
        if chat._client:
            messages = await chat._client.get_history(
                chat_id=chat.id,
                limit=1,
            )
            if messages:
                count = messages[0].message_id
        link = f'https://t.me/c/{str(chat.id)[4:]}/{count}'
    else:
        link = f'https://t.me/{chat.username}'

    return html_link(value, link, *argv)

async def html_mention(value: Union[User, int], name: str = None, client: Client = None, *argv):
    if isinstance(value, int):
        if not name and client:
            try:
                the_user: User
                the_user = await client.get_users(user_ids=value)
                name = the_user.first_name
            except Exception:
                return html_mono(value, *argv)
        elif not name:
            name = str(value)
        return f"<a href=tg://user?id={value}>{html.escape(name)}</a>"
    elif isinstance(value, User):
        return f"<a href=tg://user?id={value.id}>{html.escape(value.first_name)}</a>"

def html_mention_by_user(value: User, *argv):
    if not isinstance(value, User):
        return html_mono(value, *argv)
    return (
        f"<a href=tg://user?id={value.id}>{html.escape(value.first_name)}</a>" 
        + get_html_normal(*argv)
    )

def get_html_normal(*argv) -> str:
    if argv is None or len(argv) == 0: return ""
    my_str = ""
    for value in argv:
        if isinstance(value, str):
            my_str += value
    
    return my_str

def html_normal(value, *argv) -> str:
    my_str = html.escape(str(value))
    for value in argv:
        if isinstance(value, str):
            my_str += value
    return my_str

async def in_common_length(user: types.User) -> int:
    if not user:
        return 0
    return len(await user.get_common_chats())

async def html_in_common(user: types.User, get_common: bool = False) -> str:
    if user.is_self or get_common:
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
