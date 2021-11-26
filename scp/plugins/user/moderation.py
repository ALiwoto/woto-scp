import asyncio
import os
import html
import sys
import time
import shutil
from datetime import timedelta
from scp import user




@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['admins'],
        prefixes=user.cmd_prefixes,
    ))
async def admins_handler(_, message: user.types.Message):
    all_strs = message.text.split(' ')
    if len(all_strs) < 2:
        the_chat = message.chat.id
    else:
        the_chat = message.text.split(' ')[1]
        
    top_msg = await message.reply_text(f"<code>{html.escape('fetching group admins...')}</code>")
    txt = ''
    m = await user.get_chat_members(the_chat)
    creator = None
    admins = []
    for i in m:
        if i.status == 'creator':
            creator = i
        elif i.status == 'administrator':
            admins.append(i)

    if not creator and len(admins) == 0:
        await top_msg.edit_text(text="Seems like all admins are anon...")
        return

    starter = "<code>" + " • " + "</code>"
    if creator:
        txt += "<bold>" + html.escape("The creator:\n") + "</bold>"
        txt += starter + f"<a href=tg://user?id={creator.user.id}>{html.escape(creator.user.first_name)}</a>"
        txt += "\n\n"

    if len(admins) > 0:
        txt += "<bold>" + html.escape("Admins:\n") + "</bold>"
        for admin in admins:
            txt += starter + f"<a href=tg://user?id={admin.user.id}>{html.escape(admin.user.first_name)}</a>"
            txt += "\n"
    
    await top_msg.edit_text(text=txt, parse_mode="html")
