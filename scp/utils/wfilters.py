import pyrogram
from pyrogram import (
    types,
    filters,
)


async def my_contacts_filter(_, __, m: types.Message) -> bool:
    return m and m.from_user and m.from_user.is_contact

my_contacts = filters.create(my_contacts_filter)
"""Filter messages sent by contact users."""

async def wordle_bot_filter(_, __, m: types.Message) -> bool:
    if not (m and m.from_user and m.from_user.id == 5017534897):
        return False
    
    if not m.reply_to_message or not m.reply_to_message.from_user or not m.text:
        return False
    
    return m.reply_to_message.from_user.is_self

wordle_bot = filters.create(wordle_bot_filter)
"""Filter messages sent by contact users."""

async def intemperate_filter(_, __, m: types.Message) -> bool:
    return m and m.chat and m.chat.username == 'intemperate'

intemperate = filters.create(intemperate_filter)
"""Filter messages sent in intemperate."""

async def stalk_filter(_, __, m: types.Message) -> bool:
    return m and m.text and m.text.find('stalk') != -1

stalk_text = filters.create(stalk_filter)
"""Filter messages which contains stalk in them."""

async def bluetext_filter(_, __, m: types.Message) -> bool:
    return m and m.text and m.text[0] == '/'

bluetext = filters.create(bluetext_filter)
"""Filter messages which are bot commands (starts with '/')."""

async def noisy_bluetext_filter(_, __, m: types.Message) -> bool:
    if not (m and m.text and m.text.startswith('/')): return False
    if not m.chat or not m.chat.username: return False
    
    if m.text.startswith('/scan'): return False
    
    if m.text.startswith('/s') and not m.text.endswith(chr(0x70)): # such as sban, skick, etc...
        return True
    elif m.text.startswith('/ec'): # such as echo, etc...
        return True
    else: return False
    

noisy_bluetext = filters.create(noisy_bluetext_filter)
"""Filter messages which are considered as noisy bluetext."""

async def channel_in_group_filter(_, __, m: types.Message) -> bool:
    if not m.sender_chat or m.service or not m.chat or not m.chat.title:
        return False
    elif m.game or not m.sender_chat.username:
        return False
    elif m.empty:
        return False
    my_lower = m.sender_chat.username.lower()
    if m.chat.username:
        if m.chat.username.lower().find('night') >= 0:
            return False
    if (
        not m.sender_chat.username or
        my_lower.find('fate') >= 0
    ):
        return False
    my_lower = m.chat.title.lower()
    if (
        my_lower.find('chat') >= 0 or
        my_lower.find('talk') >= 0 or
        my_lower.find('saber') >= 0 or
        my_lower.find('fate') >= 0 or
        my_lower.find('@') >= 0 or
        my_lower.find('discussion') >= 0 or
        my_lower.find('tele') >= 0 or
        my_lower.find('dev') >= 0
    ):
        if not my_lower.find('anime') >= 0:
            return False
    return (
        m and
        m.chat.type in ['group', 'supergroup'] and
        m.sender_chat.type == 'channel'
    )

channel_in_group = filters.create(channel_in_group_filter)
"""Filter messages sent by contact users."""


async def tagged_filter(_, client:'pyrogram.Client', m: types.Message) -> bool:
    if m.empty or not client or not client.me:
        return False
    elif not m.text and not m.caption:
        return False
    
    my_text = (m.text or m.caption).lower()
    if client.me.username and my_text.find(client.me.username) != -1:
        return True
    elif client.me.first_name and my_text.find(client.me.first_name) != -1:
        return True
    elif client.me.last_name and my_text.find(client.me.last_name) != -1:
        return True
    
    return False
    
    

tagged = filters.create(tagged_filter)
"""Filter messages that are tagging you in some ways."""

