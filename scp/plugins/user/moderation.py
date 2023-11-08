import asyncio
import typing
from io import BytesIO
from pyrogram.types import (
    Message,
    Chat,
    User,
    ChatMember,
)
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.enums.chat_member_status import ChatMemberStatus
from pyrogram.enums.chat_members_filter import ChatMembersFilter
from SibylSystem.types import MultiBanInfo
from pyrogram.types.user_and_chats.chat_permissions import ChatPermissions
from scp import user
from scp.utils.misc import can_member_match, remove_special_chars
from scp.utils.parser import (
    BasicFlagContainer,
    html_bold,
    html_in_common,
    html_link,
    html_mono,
    html_normal_chat_link, 
    mention_user_html,
    split_all,
    split_some, 
    to_output_file,
)


STARTER = html_mono("• \u200D") 


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['investigate'],
        prefixes=user.cmd_prefixes,
    ),
)
async def investigate_handler(_, message: Message):
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
    done = 0
    async for _ in user.iter_chat_members(the_chat):
        done += 1

    await message.reply_text(
        f"investigated {done} members in {the_chat}",
        quote=True,
        parse_mode=ParseMode.HTML,
    )


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['stalkers'],
        prefixes=user.cmd_prefixes,
    ),
)
async def stalkers_handler(_, message: Message):
    commands = user.split_message(message)
    if len(commands) < 3:
        return
    
    # command should be sent like this:
    # .stalkers kick 2
    
    action: str = commands[1].lower()
    all_members: typing.List[ChatMember] = []
    minimum: int = 2
    sleep_time = 4
    my_text = html_mono(f'searching for stalkers with less than {minimum} message(s)...')
    top_message = await message.reply_text(my_text, quote=True)
    try:
        minimum = int(commands[2])
    except Exception: pass
    async for member in user.iter_chat_members(message.chat.id):
        if not isinstance(member, ChatMember):
            continue

        await asyncio.sleep(sleep_time)

        if member.status == ChatMemberStatus.ADMINISTRATOR or member.status == ChatMemberStatus.OWNER:
            sleep_time = 13
            continue
        
        
        if member.privileges.is_anonymous or member.user.is_contact:
            sleep_time = 12
            continue

        if member.user.is_bot or member.user.is_self:
            sleep_time = 18
            continue
        
        message_count = await user.try_get_messages_count(
            chat_id=message.chat.id,
            user_id=member.user.id,
        )

        if message_count >= minimum:
            sleep_time = 15
            continue

        common = await user.try_get_common_chats_count(user_id=member.user.id)
        
        if common < 4:
            all_members.append(member)
    
    my_text = ''
    if action == 'kick':
        my_count = 0
        for current in all_members:
            try:
                await user.kick_chat_member(
                    chat_id=message.chat.id,
                    user_id=current.user.id,
                )
                my_count += 1
            except Exception: pass
        
        my_text = html_mono(f'found {len(all_members)} stalkers in ')
        my_text += await html_normal_chat_link(message.chat.title, message.chat, ' .\n')
        my_text += html_mono(f'kicked {my_count} of them.')
    else:
        my_text = html_mono(f'found {len(all_members)} stalkers in ')
        my_text += await html_normal_chat_link(message.chat.title, message.chat, ' .')
    
    await top_message.edit_text(text=my_text, disable_web_page_preview=True)
    

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['admins', 'admins!'],
        prefixes=user.cmd_prefixes,
    ),
)
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
    common = user.is_silent(message)
    the_members = None
    try:
        the_members = await user.fetch_chat_members(the_chat, filter=ChatMembersFilter.ADMINISTRATORS)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    creator: ChatMember = None
    admins: list[ChatMember] = []
    bots: list[ChatMember] = []
    for current_member in the_members:
        if not isinstance(current_member, ChatMember):
            continue

        if current_member.status == ChatMemberStatus.OWNER:
            creator = current_member
        elif current_member.status == ChatMemberStatus.ADMINISTRATOR:
            if current_member.user.is_bot:
                bots.append(current_member)
                continue
            admins.append(current_member)

    if not creator and len(admins) == 0:
        await top_msg.edit_text(text="Seems like all admins are anon...")
        return

    if creator:
        txt += html_bold("The creator:", "\n")
        u = creator.user
        txt += STARTER + mention_user_html(u, 16) + await html_in_common(u, common) + html_mono(u.id)
        txt += "\n\n"

    if len(admins) > 0:
        txt += html_bold("Admins", f" ({len(admins)}):\n")
        for admin in admins:
            u = admin.user
            txt += STARTER + mention_user_html(u, 16) + await html_in_common(u, common) + html_mono(u.id)
            txt += "\n"
        txt += "\n"
    
    if len(bots) > 0:
        txt += html_bold("Bots:", f" ({len(bots)}):\n")
        for bot in bots:
            u = bot.user
            txt += STARTER + mention_user_html(u, 16) + await html_in_common(u, common) + html_mono(u.id)
            txt += "\n"
        txt += "\n"
    
    if len(txt) > 4096:
        await asyncio.gather(top_msg.delete(), message.reply_document(to_output_file(txt)))
        return

    await top_msg.edit_text(text=txt, parse_mode=ParseMode.HTML)


#@user.on_message(
#    user.wfilters.channel_in_group
#)
async def by_channels_handler(_, message: Message):
    from_message: Message = None
    original_message: Message = None
    try:
        from_message = await user.send_message(
            chat_id=user.log_channel, text=f'from {message.chat.id}',
        )
        original_message = await message.forward(chat_id=user.log_channel)
    except Exception: pass
    if not original_message and from_message:
        await from_message.delete()


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
    user.filters.reply &
	user.owner & 
	user.command(
        ['purge'],
        prefixes=user.cmd_prefixes,
    ),
)
async def purge_handler(_, message: Message):
    first = message.reply_to_message.id
    current = message.id
    # messages between first and current
    messages = [m for m in range(first, current + 1)]

    await user.delete_all_messages(
        chat_id=message.chat.id,
        message_ids=messages,
    )


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
    user.filters.reply &
	user.sudo & 
	user.command(
        ['tPurge'],
        prefixes=user.cmd_prefixes,
    ),
)
async def tPurge_handler(_, message: Message):
    first = message.reply_to_message.id
    current = message.id
    limit = current - first

    my_strs: list[str] = split_some(message.text, 1, ' ', '\n')
    flags = BasicFlagContainer(my_strs[1] if len(my_strs) > 1 else '')
    
    the_messages: typing.List[int] = []

    async for current in user.iter_history(
        chat_id=message.chat.id, 
        limit=limit, 
        offset_id=current,
    ):
        if not isinstance(current, Message):
            continue
        
        if flags.can_match(current):
            the_messages.append(current.id)

    if not message.id in the_messages:
        the_messages.append(message.id)
    
    try:
        await user.delete_all_messages(
            chat_id=message.chat.id,
            message_ids=the_messages,
        )
    except Exception: pass


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo & 
	user.command(
        ['deadaccs'],
        prefixes=user.cmd_prefixes,
    ),
)
async def deadaccs_handler(_, message: Message):
    should_kick = message.text.find('kick') > 0
    found_count = 0
    kicked_count = 0
    async for current in user.iter_chat_members(chat_id=message.chat.id):
        if not isinstance(current, ChatMember) or current.status == ChatMemberStatus.LEFT:
            continue
        if current.user.is_deleted:
            found_count += 1
            if should_kick:
                try:
                    await user.kick_chat_member(
                        chat_id=message.chat.id,
                        user_id=current.user.id,
                    )
                    kicked_count += 1
                except Exception: pass
    await message.reply_text(
        text=html_mono(f'found {found_count} deleted accounts, kicked {kicked_count}.'),
        parse_mode=ParseMode.HTML,
        quote=True,
    )
    

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
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
        m = await user.fetch_chat_members(the_chat)
    except Exception as ex:
        await top_msg.edit_text(text=html_mono(ex))
        return
    
    members: typing.List[ChatMember] = []
    bots: typing.List[ChatMember] = []
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
            if not isinstance(u, User):
                continue
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

    await top_msg.edit_text(text=txt, parse_mode=ParseMode.HTML)

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo &
	user.command(
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
    
    the_group: Chat = None
    try:
        the_group = await user.get_chat(the_chat)
    except Exception as e:
        await top_msg.edit_text(text=html_mono(e))
        return

    the_query = ''
    if the_group.members_count >= 5000:
        # for groups that has less than 5k members, we better don't use this
        # 'bot' query thingy, since there might be a bot that doesn't have
        # bot at the end of its username, and in small groups we will sacrifice this
        # and iterate over to find all bots.
        # bot groups with more than 5k members are just too big and we might hit
        # lots of floodwait error, so we better use the query.
        the_query = 'bot'
    admin_bots: list[ChatMember] = []
    member_bots: list[ChatMember] = []
    async for current in user.iter_chat_members(chat_id=the_chat, query=the_query):
        if not isinstance(current, ChatMember) or not current.user.is_bot:
            continue

        if current.status == ChatMemberStatus.ADMINISTRATOR:
            admin_bots.append(current)
            continue

        if current.status != ChatMemberStatus.LEFT and current.status != ChatMemberStatus.BANNED:
            member_bots.append(current)
            continue

    if  len(admin_bots) == 0 and len(member_bots) == 0:
        await top_msg.edit_text(text="Seems like this group doesn't have any bots...")
        return

    txt += '▫ Bots list in ' + await html_normal_chat_link(the_group.title, the_group, "\n\n")
    if len(admin_bots) > 0:
        txt += html_bold(f"Admin bots: ({len(admin_bots)})", "\n")
        for member in admin_bots:
            u = member.user
            txt += STARTER + mention_user_html(u, 16) + ": " + html_mono(u.id, "\n")
        txt += "\n"
    
    if len(member_bots) > 0:
        txt += html_bold(f"Normal bots: ({len(member_bots)})", "\n")
        for member in member_bots:
            u = member.user
            txt += STARTER + mention_user_html(u, 16) + ": " + html_mono(u.id, "\n")
        txt += "\n"
    
    
    if len(txt) > 4096:
        await asyncio.gather(top_msg.delete(), message.reply_document(to_output_file(txt)))
        return

    await top_msg.edit_text(
        text=txt, 
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
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
        m = await user.fetch_chat_members(the_chat)
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

    await top_msg.edit_text(text=txt, parse_mode=ParseMode.HTML)


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['fAdmins', 'fAdmins!'],
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
    common = not user.is_silent(message)
    m = None
    try:
        m = await user.fetch_chat_members(the_chat, filter=ChatMembersFilter.ADMINISTRATORS)
    except Exception as ex:
        return await top_msg.edit_text(text=html_mono(ex))
    
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

    await top_msg.edit_text(text=txt, parse_mode=ParseMode.HTML)


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['remSpec'],
        prefixes=user.cmd_prefixes,
    ),
)
async def remSpec_handler(_, message: Message):
    all_strs = split_all(message.text, ' ', '\n', '\t')
    if len(all_strs) < 2: return
    query = user.get_non_cmd(message.text)
    result = ''
    try:
        result = remove_special_chars(query)
    except Exception as e:
        result = f'{e}'
    await message.reply_text(
        f"Result for query '{html_mono(query)}':\n{html_bold(result)}",
        parse_mode=ParseMode.HTML,
    )


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['ban'],
        prefixes=user.cmd_prefixes,
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
        done = await user.ban_chat_member(chat_id=target_chat, user_id=target_user)
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
	user.owner & 
	user.command(
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
	user.owner & 
	user.command(
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
	user.owner & 
	user.command(
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
        await user.ban_chat_member(chat_id=target_chat, user_id=target_user)
        await message.delete()
    except Exception: pass


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
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
	user.owner & 
	user.command(
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
	user.owner & 
	user.command(
        ['sban'],
        prefixes=user.cmd_prefixes,
    ),
)
async def sBan_handler(_, message: Message):
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
        message = await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
        if isinstance(message, Message):
            await message.delete()
    except Exception: pass

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['skick'],
        prefixes=user.cmd_prefixes,
    ),
)
async def skick_handler(_, message: Message):
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
        message = await user.kick_chat_member(chat_id=target_chat, user_id=target_user)
        if isinstance(message, Message):
            await message.delete()
        await user.unban_chat_member(chat_id=target_chat, user_id=target_user)
    except Exception: pass

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
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





@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo & 
	user.command(
        ['getLinks'],
        prefixes=user.cmd_prefixes,
    ),
)
async def getlinks_handler(_, message: Message):
    # .getlinks GROUP_ID MSG_ID1-MSG_ID2 <flags>
    if message.text.find(' ') == -1:
        txt = user.html_bold('Usage:', '\n')
        txt += user.html_mono('\t.getlinks GROUP_ID MSG_ID1-MSG_ID2 <flags>\n')
        txt += user.html_normal('(where MSG_ID2 > MSG_ID1)')
        return await message.reply_text(txt)
    
    reply = await message.reply_text(user.html_mono('fetching messages links...'))
    my_strs: list[str] = split_some(message.text, 3, ' ', '\n')
    group_id = my_strs[1]
    msg_ids = my_strs[2].split('-')
    
    first = int(msg_ids[0])
    current = int(msg_ids[1])
    limit = current - first

    flags = BasicFlagContainer(my_strs[3] if len(my_strs) > 3 else '')
    
    #the_messages: typing.List[int] = []
    final_txt: str = ''

    async for current in user.iter_history(
        chat_id=group_id, 
        limit=limit, 
        offset_id=current,
    ):
        if not isinstance(current, Message):
            continue
        
        if flags.can_match(current):
            final_txt += user.html_normal(current.link + '\n')
    
    if len(final_txt) > 4096:
        f = BytesIO(final_txt)
        f.name = 'output.txt'
        await asyncio.gather(
            reply.delete(),
            message.reply_document(
                f,
                caption=user.html_mono(f'matched links from {first} to {current} in {group_id}'),
                quote=True,
            ),
        )
    else:
        await reply.edit_text(final_txt)


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['replyTo'],
        prefixes=user.cmd_prefixes,
    ),
)
async def replyTo_handler(_, message: Message):
    args = user.split_some(message.text, 2, ' ', '\n')
    if not args or len(args) < 3:
        await message.reply_text(
            user.html_bold('usage:', '\n') +
            user.html_mono('.replyTo message_link text')
        )
        return
    
    # format should be like this:
    # .replyTo message_link text
    
    message_link = args[1]
    try:
        target_message = await user.get_message_by_link(message_link)
        await target_message.reply_text(args[2])
    except Exception as e:
        return await user.reply_exception(message, e)
    

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo & 
	user.command(
        ['tCacheMessages'],
        prefixes=user.cmd_prefixes,
    ),
)
async def tCacheMessages_handler(_, message: Message):
    # .tGetMessages GROUP_ID MSG_ID1-MSG_ID2 <flags>
    if message.text.find(' ') == -1:
        txt = user.html_bold('Usage:', '\n')
        txt += user.html_mono('\t.tCacheMessages GROUP_ID MSG_ID1-MSG_ID2 <flags>\n')
        txt += user.html_normal('(where MSG_ID2 > MSG_ID1)')
        return await message.reply_text(txt)
    
    reply = await message.reply_text(user.html_mono('fetching messages...'))
    my_strs: list[str] = split_some(message.text, 3, ' ', '\n')
    group_id = my_strs[1]
    msg_ids = my_strs[2].split('-')
    
    first = int(msg_ids[0])
    current = int(msg_ids[1])
    limit = current - first

    flags = BasicFlagContainer(my_strs[3] if len(my_strs) > 3 else '')
    
    the_messages: typing.List[Message] = []

    async for current in user.iter_history(
        chat_id=group_id, 
        limit=limit, 
        offset_id=current,
    ):
        if not isinstance(current, Message):
            continue
        
        if flags.can_match(current):
            the_messages.append(current)
        
    user.cached_messages = the_messages
    await reply.edit_text(user.html_mono(f'successfully cached {len(the_messages)} messages.'))

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo & 
	user.command(
        ['cachedScan'],
        prefixes=user.cmd_prefixes,
    ),
)
async def cachedScan_handler(_, message: Message):
    # .tGetMessages GROUP_ID MSG_ID1-MSG_ID2 <flags>
    if message.text.find(' ') == -1:
        txt = user.html_bold('Usage:', '\n')
        txt += user.html_mono('\t.cachedScan REASON\n')
        return await message.reply_text(txt)
    
    the_reason = user.get_non_cmd(message)
    all_infos: typing.List[MultiBanInfo] = []
    all_targets: typing.List[int] = []
    
    for current in user.cached_messages:
        if not isinstance(current, Message):
            continue
        
        if not current.from_user or current.from_user.id in all_targets:
            continue
        
        all_targets.append(current.from_user.id)
        all_infos.append(MultiBanInfo(
            user_id=current.from_user.id,
            reason=the_reason,
            message=current.link,
            source=message.link,
            source_group=str(current.chat.id)
        ))
    
    my_msg = await message.reply_text('Sending cymatic scan request to sibyl system.')
    try:
        user.sibyl.multi_ban(all_infos)
    except Exception as e:
        await my_msg.edit_text("Got error: " + html_mono(e), parse_mode=ParseMode.HTML)
        return
    
    await my_msg.edit_text(
        html_mono('Cymatic scan request has been sent to Sibyl.'), 
        parse_mode=ParseMode.HTML,
    )




