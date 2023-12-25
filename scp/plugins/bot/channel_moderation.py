import re
import time
import json
import asyncio
import datetime
from scp import bot, user
from pyrogram.types import (
    ChatMemberUpdated, 
    ChatEventFilter,
    User
)
from pyrogram.types.user_and_chats.chat_event import ChatEvent

all_recently_joined_users = []
all_recently_joined_users_id = []
join_check_lock = asyncio.Lock()
last_time_check: datetime.datetime = None

@bot.on_chat_member_updated(
    filters=user.special_channels
)
async def chatMember_handler(_, update: ChatMemberUpdated):
    if not update.new_chat_member or \
        update.new_chat_member.invited_by or \
        update.new_chat_member.user.is_bot:
        return
    
    await join_check_lock.acquire()
    try:
        await validate_member(_, update=update)
    except Exception as ex:
        print(f"failed to validate member: {ex}")
    join_check_lock.release()

async def validate_member(_, update: ChatMemberUpdated):
    global last_time_check
    if last_time_check and \
        (datetime.datetime.now() - last_time_check).seconds > 200:
        await asyncio.sleep(5)
    
    last_time_check = datetime.datetime.now()
    the_target: User = None
    if not all_recently_joined_users:
        async for current in user.get_chat_event_log(
            chat_id=update.chat.id, 
            filters=ChatEventFilter(new_members=True),
            limit=250,
        ):
            if not isinstance(current, ChatEvent):
                continue
            
            if update.new_chat_member.user.id == current.user.id:
                the_target = current.user
            all_recently_joined_users.append(current.user)
            all_recently_joined_users_id.append(current.user.id)
    else:
        # just get with limit = 5 because we might have missed few...
        async for current in user.get_chat_event_log(
            chat_id=update.chat.id, 
            filters=ChatEventFilter(new_members=True),
            limit=70
        ):
            if not isinstance(current, ChatEvent):
                continue
            
            if update.new_chat_member.user.id == current.user.id:
                the_target = current.user
            
            if current.user.id in all_recently_joined_users_id:
                continue
            all_recently_joined_users.append(current.user)
    
    # 1. user object validation
    if not the_target:
        try:
            target_id = update.new_chat_member.user.username \
                if update.new_chat_member.user.username \
                else update.new_chat_member.user.id
            the_target = await user.get_users(user_ids=target_id)
        except: 
            the_target = update.new_chat_member.user
    
    # 2. name validation
    whole_name = f"{the_target.first_name or ''} {the_target.last_name or ''}".strip()
    if whole_name.isnumeric():
        await bot.ban_chat_member(chat_id=update.chat.id, user_id=the_target.id)
        return

    # last seen validation
    if not the_target.last_online_date:
        return
    
    # check if the last online date is within 10 minutes
    if (datetime.datetime.now() - the_target.last_online_date).seconds > 600:
        # user has been offline for more than 10 minutes and have joined the channel
        # right now. sounds wrong.
        await bot.ban_chat_member(chat_id=update.chat.id, user_id=the_target.id)
        return
    
    # add more conditions here in the future
