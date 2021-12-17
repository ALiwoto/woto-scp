import asyncio
from pyrogram.types import (
    Message,
    ChatMember,
)
from pyrogram.methods.chats.get_chat_members import Filters
from pyrogram.types.user_and_chats.chat_permissions import ChatPermissions
from scp import user
from scp.utils.misc import can_member_match, remove_special_chars
from scp.utils.parser import (
    html_bold,
    html_in_common,
    html_mono, 
    mention_user_html,
    split_all, 
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
async def admins_handler(_, message: Message):
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
        
    top_msg = await message.reply_text(html_mono("fetching group admins..."))
    txt = ''
    m = None
    try:
        m = await user.get_chat_members(the_chat, filter=Filters.ADMINISTRATORS)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    creator: ChatMember = None
    admins: list[ChatMember] = []
    bots: list[ChatMember] = []
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
        txt += html_bold("The creator:", "\n")
        u = creator.user
        txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id)
        txt += "\n\n"

    if len(admins) > 0:
        txt += html_bold("Admins", "\n")
        for admin in admins:
            u = admin.user
            txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id)
            txt += "\n"
        txt += "\n"
    
    if len(bots) > 0:
        txt += html_bold("Bots:", "\n")
        for bot in bots:
            u = bot.user
            txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id)
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
    ),
)
async def members_handler(_, message: Message):
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

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['bots'],
        prefixes=user.cmd_prefixes,
    ),
)
async def bots_handler(_, message: Message):
    all_strs = message.text.split(' ')
    if len(all_strs) < 2:
        if not message.reply_to_message:
            the_chat = message.chat.id
        else:
            replied = message.reply_to_message
            if replied.text.isdigit() and replied.text.startswith('-100'):
                the_chat = int(replied.text)
            else:
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
        
    top_msg = await message.reply_text(html_mono('fetching group bots...'))
    txt: str = ''
    m = None
    try:
        m = await user.get_chat_members(the_chat)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    
    admin_bots: list[ChatMember] = []
    member_bots: list[ChatMember] = []
    async for current in user.iter_chat_members(the_chat):
        if not isinstance(current, ChatMember) or not current.user.is_bot:
            continue

        if current.status == 'administrator':
            admin_bots.append(current)
            continue

        if current.status != 'left' and current.status != 'kicked':
            member_bots.append(current)
            continue



    if  len(admin_bots) == 0 and len(member_bots) == 0:
        await top_msg.edit_text(text="Seems like this group doesn't have any bots...")
        return

    starter = html_mono(" • ") 
    if len(admin_bots) > 0:
        txt += html_bold("Admin bots:", "\n")
        for member in admin_bots:
            u = member.user
            txt += starter + mention_user_html(u, 16) + ": " + html_mono(u.id, "\n")
        txt += "\n"
    
    if len(member_bots) > 0:
        txt += html_bold("Normal bots:", "\n")
        for member in member_bots:
            u = member.user
            txt += starter + mention_user_html(u, 16) + ": " + html_mono(u.id, "\n")
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
        ['fmembers'],
        prefixes=user.cmd_prefixes,
    ),
)
async def fmembers_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n', '\t')
    is_here = False
    query = ""
    if len(all_strs) < 2:
        the_chat = message.chat.id
        is_here = True
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
    
    if len(all_strs) >= 3:
        query = ''.join(all_strs[2:])
    elif is_here and len(all_strs) == 2:
        query = all_strs[1]
    else: return
    
    top_msg = await message.reply_text(html_mono('fetching group members...'))
    txt: str = ''
    m = None
    try:
        m = await user.get_chat_members(the_chat)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    
    members: list[ChatMember] = []
    bots: list[ChatMember] = []
    for i in m:
        if i.status == 'member' and i.status != 'left' and i.status != 'kicked':
            if not await can_member_match(i, user, query):
                continue
            if i.user.is_bot:
                bots.append(i)
                continue
            members.append(i)

    if  len(members) == 0 and len(bots) == 0:
        await top_msg.edit_text(text="No results found...")
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


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['fadmins', 'fadmins!'],
        prefixes=user.cmd_prefixes,
    ),
)
async def fadmins_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n', '\t')
    is_here = False
    query = ""
    if len(all_strs) < 2:
        the_chat = message.chat.id
        is_here = True
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
    
    if len(all_strs) >= 3:
        query = ' '.join(all_strs[2:])
    elif is_here and len(all_strs) == 2:
        query = all_strs[1]
    else: return
        
    top_msg = await message.reply_text(html_mono('fetching group admins...'))
    txt: str = ''
    common = all_strs[0][-1] == '!'
    m = None
    try:
        m = await user.get_chat_members(the_chat, filter=Filters.ADMINISTRATORS)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    
    creator: ChatMember = None
    admins: list[ChatMember] = []
    bots: list[ChatMember] = []
    for i in m:
        if i.status == 'creator':
            if not await can_member_match(i, user, query):
                continue
            creator = i
            continue
        elif i.status == 'administrator':
            if not await can_member_match(i, user, query):
                continue
            if i.user.is_bot:
                bots.append(i)
                continue
            admins.append(i)

    if not creator and len(admins) == 0 and len(bots) == 0:
        try:
            await top_msg.edit_text(
                text=f"No results found for query '{html_mono(query)}'...",
            )
        except Exception: return
        return

    starter = "<code>" + " • " + "</code>"
    if creator:
        txt += html_bold("The creator:", "\n")
        u = creator.user
        txt += starter + mention_user_html(u, 16) + await html_in_common(u, common) + html_mono(u.id)
        txt += "\n\n"
    
    if len(admins) > 0:
        txt += html_bold("Admins:", "\n")
        for member in admins:
            u = member.user
            txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id, "\n")
        txt += "\n"
    
    if len(bots) > 0:
        txt += html_bold("Bots:", "\n")
        for bot in bots:
            u = bot.user
            txt += starter + mention_user_html(u, 16) + await html_in_common(u) + html_mono(u.id, "\n")
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
        ['remspec'],
        prefixes=user.cmd_prefixes,
    ),
)
async def remspec_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n', '\t')
    if len(all_strs) < 2: return
    query = ' '.join(all_strs[1:])
    result = ''
    try:
        result = remove_special_chars(query)
    except Exception as e:
        result = f'{e}'
    await message.reply_text(
        f"Result for query '{html_mono(query)}':\n{html_bold(result)}",
        parse_mode="html",
    )


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['ban'],
    ),
)
async def ban_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    
    output = ''
    try:
        done = await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
        output = html_mono('done.' if done else f'impossible to ban {target_user}.')
    except Exception as e:
        output = html_mono(str(e)[:4095])

    try:
        await message.reply_text(
            text=output,
            disable_notification=True, 
            disable_web_page_preview=True,
        )
    except: return


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['mute'],
        prefixes=user.cmd_prefixes,
    ),
)
async def mute_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    
    output = ''
    try:
        done = await user.restrict_chat_member(
            chat_id=target_chat, 
            user_id=target_user,
            permissions=ChatPermissions(
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_send_animations=False,
                can_send_games=False,
                can_send_media_messages=False,
                can_send_messages=False,
                can_send_polls=False,
                can_send_stickers=False,
                can_use_inline_bots=False,
            )
        )
        output = html_mono('done.' if done else f'impossible to mute {target_user}.')
    except Exception as e:
        output = html_mono(str(e)[:4095])

    try:
        await message.reply_text(
            text=output,
            disable_notification=True, 
            disable_web_page_preview=True,
        )
    except: return


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['unmute'],
        prefixes=user.cmd_prefixes,
    ),
)
async def mute_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    
    output = ''
    try:
        done = await user.restrict_chat_member(
            chat_id=target_chat, 
            user_id=target_user,
            permissions=ChatPermissions(
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_animations=True,
                can_send_games=True,
                can_send_media_messages=True,
                can_send_messages=True,
                can_send_polls=True,
                can_send_stickers=True,
                can_use_inline_bots=True,
            )
        )
        output = html_mono('done.' if done else f'impossible to mute {target_user}.')
    except Exception as e:
        output = html_mono(str(e)[:4095])

    try:
        await message.reply_text(
            text=output,
            disable_notification=True, 
            disable_web_page_preview=True,
        )
    except: return


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['aban'],
        prefixes=user.cmd_prefixes,
    ),
)
async def aban_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    
    try:
        await user.delete_user_history(chat_id=target_chat, user_id=target_user)
    except Exception: pass

    try:
        await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
        await message.delete()
    except Exception: pass


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['kick'],
        prefixes=user.cmd_prefixes,
    ),
)
async def kick_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    else: return

    output = ''
    try:
        done = await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
        await user.unban_chat_member(chat_id=target_chat, user_id=target_user)
        output = html_mono('done.' if done else f'impossible to kick {target_user}.')
    except Exception as e:
        output = html_mono(str(e)[:4095])

    try:
        await message.reply_text(
            text=output,
            disable_notification=True, 
            disable_web_page_preview=True,
        )
    except: return

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['unban'],
        prefixes=user.cmd_prefixes,
    ),
)
async def unban_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    else: return
    
    output = ''
    try:
        done = await user.unban_chat_member(chat_id=target_chat, user_id=target_user)
        output = html_mono('done.' if done else f'impossible to unban {target_user}.')
    except Exception as e:
        output = html_mono(str(e)[:4095])

    try:
        await message.reply_text(
            text=output,
            disable_notification=True, 
            disable_web_page_preview=True,
        )
    except: return


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['sban'],
        prefixes=user.cmd_prefixes,
    ),
)
async def sban_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) >= 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    else: return
    
    try:
        await message.delete()
    except Exception: pass

    try:
        await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
    except Exception: pass

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['skick'],
        prefixes=user.cmd_prefixes,
    ),
)
async def kick_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    else: return

    try:
        await message.delete()
    except Exception: pass
    
    try:
        await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
        await user.unban_chat_member(chat_id=target_chat, user_id=target_user)
    except Exception: pass

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['sunban'],
        prefixes=user.cmd_prefixes,
    ),
)
async def unban_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n')
    target_user = 0
    target_chat = 0

    if len(all_strs) == 1:
        if message.reply_to_message is None:
            return
        
        replied = message.reply_to_message
        target_user = (
            replied.sender_chat.id 
            if replied.sender_chat != None 
            else replied.from_user.id
        )
        target_chat = message.chat.id
    elif len(all_strs) == 2:
        target_user = all_strs[1]
        target_chat = message.chat.id
    elif len(all_strs) == 3:
        target_chat = all_strs[1]
        target_user = all_strs[2]
    else: return

    try:
        await message.delete()
    except Exception: pass

    try:
        await user.unban_chat_member(chat_id=target_chat, user_id=target_user)
    except Exception: pass



