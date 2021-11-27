import asyncio
import html
from io import BytesIO
from scp import user
from scp.utils.parser import (
    html_bold,
    html_in_common,
    html_in_parantesis,
    html_mono, 
    mention_user_html, 
    to_output_file,
)

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
        if the_chat.find('/') > 0:
            all_strs = the_chat.split('/')
            index = len(all_strs) - 1
            if all_strs[index].isdigit():
                index -= 1
            if all_strs[index].isdigit():
                all_strs[index] = '-100' + all_strs[index]
            the_chat = all_strs[index]
        
    top_msg = await message.reply_text(f"<code>{html.escape('fetching group admins...')}</code>")
    txt = ''
    m = None
    try:
        m = await user.get_chat_members(the_chat)
    except Exception as ex:
        await top_msg.edit_text(text=f"<code>{ex}</code>")
        return
    creator = None
    admins: list[user.types.ChatMember] = []
    bots: list[user.types.ChatMember] = []
    for i in m:
        if i.status == 'creator':
            creator = i
        elif i.status == 'administrator':
            if i.user.is_bot:
                bots.append(i)
                continue
            admins.append(i)

    if not creator and len(admins) == 0:
        await top_msg.edit_text(text="Seems like all admins are anon...")
        return

    starter = "<code>" + " • " + "</code>"
    if creator:
        txt += "<b>" + html.escape("The creator:") + "</b>\n"
        u = creator.user
        txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id, "\n")
        txt += "\n\n"

    if len(admins) > 0:
        txt += "<b>" + html.escape("Admins:") + "</b>\n"
        for admin in admins:
            u = admin.user
            txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id, "\n")
            txt += "\n"
        txt += "\n"
    
    if len(bots) > 0:
        txt += "<b>" + html.escape("Bots:") + "</b>\n"
        for bot in bots:
            u = bot.user
            txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id, "\n")
            txt += "\n"
        txt += "\n"
    
    if len(txt) > 4096:
        await asyncio.gather(top_msg.delete(), message.reply_document(to_output_file(txt)))
        return

    await top_msg.edit_text(text=txt, parse_mode="html")



@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['members'],
        prefixes=user.cmd_prefixes,
    ))
async def members_handler(_, message: user.types.Message):
    all_strs = message.text.split(' ')
    if len(all_strs) < 2:
        the_chat = message.chat.id
    else:
        the_chat = message.text.split(' ')[1]
        if the_chat.find('/') > 0:
            all_strs = the_chat.split('/')
            index = len(all_strs) - 1
            if all_strs[index].isdigit():
                index -= 1
            if all_strs[index].isdigit():
                all_strs[index] = '-100' + all_strs[index]
            the_chat = all_strs[index]
        
    top_msg = await message.reply_text(html_mono('fetching group members...'))
    txt: str = ''
    m = None
    try:
        m = await user.get_chat_members(the_chat)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    
    members: list[user.types.ChatMember] = []
    bots: list[user.types.ChatMember] = []
    for i in m:
        if i.status == 'member' and i.status != 'left' and i.status != 'kicked':
            if i.user.is_bot:
                bots.append(i)
                continue
            members.append(i)

    if  len(members) == 0 and len(bots) == 0:
        await top_msg.edit_text(text="Seems like this group doesn't have any normal members...")
        return

    starter = "<code>" + " • " + "</code>"
    if len(members) > 0:
        txt += html_bold("Members:", "\n")
        for member in members:
            u = member.user
            txt += starter + mention_user_html(u, 16) + ": " + html_mono(u.id, "\n")
        txt += "\n"
    
    if len(bots) > 0:
        txt += html_bold("Bots:", "\n")
        for bot in bots:
            u = bot.user
            txt += starter + mention_user_html(u, 16) + ": " + html_mono(u.id, "\n")
        txt += "\n"
    
    if len(txt) > 4096:
        await asyncio.gather(top_msg.delete(), message.reply_document(to_output_file(txt)))
        return

    await top_msg.edit_text(text=txt, parse_mode="html")



