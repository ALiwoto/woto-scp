import asyncio
from scp import user
from pyrogram.types import (
    Message,
    Chat,
    ChatPrivileges,
)
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.errors import(
    MessageIdInvalid,
    MessageTooLong,
    EncryptedMessageInvalid,
    MediaCaptionTooLong,
)
from shortuuid import ShortUUID
from scp.utils.str_utils import (
    get_random_cup,
    get_random_username_repr,
    get_random_emoji,
    get_random_username_str,
    get_random_format_str,
    get_random_stuff_str,
    get_random_note_str,
    get_random_sad_emoji,
    get_random_right_arrow
)

_operations_stats = {}

@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo & 
	user.command(
        ['ord'],
        prefixes=user.cmd_prefixes,
    ),
)
async def ord_handler(_, message: Message):
    all_str = user.get_non_cmd(message)
    if not all_str:
        return
    
    txt = ''
    current_ord = 0
    for current in all_str:
        current_ord = ord(current)
        txt += user.html_bold(f"'{current}': ") + user.html_mono(current_ord, ' (')
        txt += user.html_mono(hex(current_ord), ')\n')
        
    
    await message.reply_text(txt)


@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.sudo & 
	user.command(
        ['chr'],
        prefixes=user.cmd_prefixes,
    ),
)
async def chr_handler(_, message: Message):
    all_str = user.get_non_cmd(message)
    if not all_str:
        return
    my_int = 0
    try:
        my_int = int(all_str)
    except Exception as e:
        return await message.reply_text(user.html_mono(f'{e}'))

    txt = user.html_bold(f"'{my_int}: '") + user.html_mono(chr(my_int), "\n")
    
    await message.reply_text(txt)


@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot & 
	user.owner & 
	user.command(
        ['pirate'],
        prefixes=user.cmd_prefixes,
    ),
)
async def pirate_handler(_, message: Message):
    if not user.the_bots or len(user.the_bots) < 1:
        await message.reply_text('bots list is empty.')
        return
    
    if not user.are_bots_started:
        top_message = await message.reply_text(user.html_mono('starting bots...'))
        try:
            await user.start_all_bots()
        except Exception as ex:
            return await top_message.edit_text(
                user.html_bold("Failed to start all bots:") + user.html_mono(ex))
        await top_message.edit_text(user.html_mono('bots started.'))
        

    args = user.split_message(message)
    if not args or len(args) < 2:
        txt = user.html_bold("Pirate: \n\t\t")
        txt += user.html_italic("Pirates messages from another chat to the defined private_resources chat.\n\n\t\t")
        txt += user.html_bold("Usage:\n")
        txt += user.html_mono(".pirate target_chat from_id-to_id")
        return await message.reply_text(text=txt, parse_mode=ParseMode.HTML)
    
    target_chat = args[1]
    the_chat: Chat = None
    from_id: int = 1
    to_id: int = 0
    try:
        the_chat = await user.get_chat(target_chat)
    except Exception as e:
        return await message.reply_text(user.html_mono(e))
    try:
        if len(args) > 2:
            all_numbers = args[2].split('-')
            if len(all_numbers) == 2:
                from_id = int(all_numbers[0])
                to_id = int(all_numbers[1])
        else:
            messages = await user.get_history(
                chat_id=target_chat,
                limit=1,
            )
            if messages:
                to_id = messages[0].id
    except Exception as e:
        return await message.reply_text(user.html_mono(e))

    unique_id = str(ShortUUID().random(length=8))
    operation_info = {"canceled": False}
    _operations_stats[unique_id] = operation_info

    keyboard = [
        {"refresh": "pirateRefresh_"},
        {"cancel": f"pirateCancel_{unique_id}"},
    ]
    link_pre = f'https://t.me/c/{str(the_chat.id)[4:]}/'
    channel_text = f'{get_random_cup()} getting {get_random_stuff_str()}'
    channel_text += f' from ({from_id}) to ({to_id}) in 🏷{the_chat.title} for request {unique_id}\n'
    channel_text += f'{get_random_emoji()} {get_random_username_str()} is {get_random_right_arrow()} '
    channel_text += get_random_username_repr(the_chat.username) + f'{get_random_sad_emoji()} \n'
    channel_text += f'{get_random_note_str()} {get_random_format_str()} {get_random_right_arrow()}'
    channel_text += f' {get_random_username_repr(the_chat.username)} [' + user.html_mono(the_chat.id) + ']: '
    channel_text += user.html_link(from_id, link_pre + f'{from_id}') + get_random_right_arrow()
    channel_text += user.html_link(to_id, link_pre + f'{to_id}') + f" {get_random_emoji()}"
    channel_post: Message = await user.send_message(
        chat_id=user.private_resources,
        text=channel_text,
        reply_markup=keyboard,
    )

    await channel_post.pin()
    
    current_bot_index: int = 0
    done: int = 0
    failed: int = 0
    for index in range(from_id, to_id + 1):
        current_bot_index = index % len(user.the_bots)
        try:
            await user.the_bots[current_bot_index].copy_message(
                chat_id=user.private_resources,
                from_chat_id=target_chat,
                message_id=index,
            )
            done += 1
            await asyncio.sleep(0.5)
        except Exception:
            failed += 1
            continue

    text = user.html_bold(f'Tried to pirate {done+failed} messages from ')
    text += user.html_normal(f'{the_chat.title} [') + user.html_mono(f'{target_chat}', '].\n')
    text += user.html_mono(done, ' messages were pirated successfully.\n')
    text += user.html_mono(failed, ' messages were not pirated.')
    await message.reply_text(text, disable_web_page_preview=True, parse_mode=ParseMode.HTML)


@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot & 
	user.owner & 
	user.command(
        ['addPBots'],
        prefixes=user.cmd_prefixes,
    ),
)
async def addPBots_handler(_, message: Message):
    if not user.the_bots or len(user.the_bots) < 1:
        return await message.reply_text('bot lists is empty.')
    
    if not user.are_bots_started:
        top_message = await message.reply_text(user.html_mono('starting bots...'))
        await user.start_all_bots()
        await top_message.edit_text(user.html_mono('bots started.'))
    
    added = 0
    failed = 0
    for current_bot in user.the_bots:
        try:
            await user.promote_chat_member(
                chat_id=message.chat.id, 
                user_id=current_bot.me.username,
                privileges=ChatPrivileges(can_post_messages=True),
            )
            added += 1
        except Exception as e:
            print(e)
            failed += 1
            continue
    
    text = user.html_bold('Added: ') + user.html_mono(added, '\n')
    text += user.html_bold('Failed: ') + user.html_mono(failed, '\n')
    await message.reply_text(text, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot & 
	user.owner & 
	user.command(
        ['cBackup'],
        prefixes=user.cmd_prefixes,
    ),
)
async def cBackup_handler(_, message: Message):
    if not user.the_bots or len(user.the_bots) < 1:
        return await message.reply_text('bot lists is empty.')
    
    if not user.scp_config.dump_usernames or len(user.scp_config.dump_usernames) < 1:
        return await message.reply_text('list of public usernames is empty.')
    
    if not user.are_bots_started:
        top_message = await message.reply_text(user.html_mono('starting bots...'))
        await user.start_all_bots()
        await top_message.edit_text(user.html_mono('bots started.'))
    
    args = user.split_message(message)
    if not args or len(args) < 4:
        await message.reply_text(
            user.html_bold('usage:', '\n') +
            user.html_mono('.cBackup target_chat backup_channel_id from_id-to_id')
        )
        return
    
    # format should be like this:
    # .cBackup target_chat backup_channel_id from_id-to_id
    
    target_chat = args[1]
    public_username: str = user.scp_config.dump_usernames[0]
    tg_link_first = f'https://t.me/{public_username}/'
    the_chat: Chat = None
    backup_channel_id = args[2]
    from_id: int = 1
    to_id: int = 0
    try:
        the_chat = await user.get_chat(target_chat)
    except Exception as e:
        return await message.reply_text(user.html_mono(e))
    
    try:
        my_splits = args[3].split('-')
        from_id = int(my_splits[0])
        to_id = int(my_splits[1])
    except Exception as e:
        return await message.reply_text(user.html_mono(e))

    my_username = the_chat.username
    if not my_username:
        my_username = str(the_chat.id)
    
    link_pre = f'https://t.me/c/{str(the_chat.id)[4:]}/'
    channel_text = f'🍷 getting some stuff from ({from_id}) to ({to_id}) in 🏷{the_chat.title}\n'
    channel_text += '💎 target username is @' + the_chat.username + '🔮 \n'
    channel_text += f'📝 formoewt => @{the_chat.username} [' + user.html_mono(the_chat.id) + ']: '
    channel_text += user.html_link(from_id, link_pre + f'{from_id}') + '=>'
    channel_text += user.html_link(to_id, link_pre + f'{to_id}')

    channel_post: Message = await user.send_message(
        chat_id=user.private_resources,
        text=channel_text,
    )

    await channel_post.pin()
    
    current_user_message: Message = None
    current_bot_index: int = 0
    done: int = 0
    failed: int = 0
    for index in range(from_id, to_id + 1):
        await asyncio.sleep(5)
        current_bot_index = index % len(user.the_bots)
        public_username = user.scp_config.dump_usernames[index % len(user.scp_config.dump_usernames)]
        tg_link_first = f'https://t.me/{public_username}/'
        try:
            current_user_message = await user.the_bots[current_bot_index].forward_messages(
                chat_id=public_username,
                from_chat_id=target_chat,
                message_ids=index,
            )

            current_user_message = await user.the_bots[current_bot_index].send_message(
                chat_id=user.private_resources,
                text=tg_link_first+str(current_user_message.id),
                disable_web_page_preview=False,
            )

            if current_user_message.service:
                #print('service')
                continue
                #log.warning(f"Service messages cannot be copied. "
                #            f"chat_id: {self.chat.id}, message_id: {self.message_id}")
            elif current_user_message.game:
                print('game')
                continue
                #log.warning(f"Users cannot send messages with Game media type. "
                #            f"chat_id: {self.chat.id}, message_id: {self.message_id}")
            elif current_user_message.empty:
                print('empty')
                continue
                #log.warning(f"Empty messages cannot be copied. ")
            else:
                counter: int = 0
                while True:
                    await asyncio.sleep(2+counter)
                    counter += 1
                    current_user_message = await user.get_messages(
                        chat_id=current_user_message.chat.id,
                        message_ids=current_user_message.id,
                    )
                    if current_user_message.web_page or counter > 6:
                        break
                if not current_user_message.web_page:
                    print('no preview: ', current_user_message.text)
                    continue
            
            if not current_user_message.web_page.description:
                current_user_message.web_page.description = ''

            if current_user_message.web_page.document:
                await user.send_document(
                    chat_id=backup_channel_id,
                    document=current_user_message.web_page.document.file_id,
                    caption=current_user_message.web_page.description,
                )
            elif current_user_message.web_page.audio:
                await user.send_audio(
                    chat_id=backup_channel_id,
                    audio=current_user_message.web_page.audio.file_id,
                    caption=current_user_message.web_page.description,
                )
            elif current_user_message.web_page.video:
                await user.send_video(
                    chat_id=backup_channel_id,
                    video=current_user_message.web_page.video.file_id,
                    caption=current_user_message.web_page.description,
                )
            elif current_user_message.web_page.photo:
                await user.send_photo(
                    chat_id=backup_channel_id,
                    photo=current_user_message.web_page.photo.file_id,
                    caption=current_user_message.web_page.description,
                )
            elif current_user_message.web_page.animation:
                await user.send_animation(
                    chat_id=backup_channel_id,
                    animation=current_user_message.web_page.animation.file_id,
                    caption=current_user_message.web_page.description,
                )
            elif current_user_message.web_page.description:
                await user.the_bots[current_bot_index].send_message(
                    chat_id=backup_channel_id,
                    text=current_user_message.web_page.description,
                )
            else:
                print('something else')
                print(current_user_message.web_page)
                continue
            done += 1
        except (
            MessageTooLong,
            MessageIdInvalid,
            MediaCaptionTooLong,
            EncryptedMessageInvalid,
        ): 
            continue
        except Exception as e:
            print(e)
            failed += 1
    
    text = user.html_bold(f'Tried to backup {done+failed} messages from ')
    text += user.html_normal(f'{the_chat.title} [') + user.html_mono(f'{target_chat}', '].\n')
    text += user.html_mono(done, ' messages were backed up successfully.\n')
    text += user.html_mono(failed, ' messages were not backed up.')
    await message.reply_text(text, disable_web_page_preview=True, parse_mode=ParseMode.HTML)


# @user.on_message(
    # ~(
        # user.owner | 
        # user.sudo | 
        # user.filters.private
    # ) & 
    # user.filters.animation &
    # user.wfilters.intemperate,
    # group=123,
# )
async def send_stare_gif(_, message: Message):
    if message.animation.file_unique_id != 'AgADbgADz3-YRg':
        return
    await user.send_animation(
        message.chat.id, 
        message.animation.file_id, 
        reply_to_message_id=message.id,
    )


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['iUser'],
        prefixes=user.cmd_prefixes,
    ),
)
async def investigate_user_handler(_, message: Message):
    args = user.split_some(message.text, 2, ' ', '\n')
    if not args or len(args) < 3:
        await message.reply_text(
            user.html_bold('usage:', '\n') +
            user.html_mono('.iUser group-id user-id')
        )
        return
    
    # format should be like this:
    # .iUser group-id user-id
    
    chat_id = args[1]
    user_id = args[2]
    try:
        target_user = await user.get_users(user_id)
        the_group = await user.get_chat(chat_id)
        count = await user.search_messages_count(
            chat_id=chat_id,
            from_user=user_id,
        )
        if not count:
            return await message.reply_text('this user has no messages in that chat.')
        
        target_message: Message = None
        async for current in user.search_messages(
            chat_id=chat_id,
            from_user=user_id,
        ):
            target_message = current
            break
        txt = user.mention_user_html(target_user, 8) + user.html_normal("'s statistic in ")
        txt += await user.html_normal_chat_link(the_group.title, the_group, "\n\n")
        txt += user.html_bold('・Messages count: ') + user.html_mono(count, '\n')
        txt += user.html_bold('・Last message: ')
        txt += user.html_link(f'>> {target_message.id}', target_message.link)
        return await message.reply_text(txt, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
    except Exception as e:
        return await user.reply_exception(message, e)
    

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['archiveByUser'],
        prefixes=user.cmd_prefixes,
    ),
)
async def archive_by_user_handler(_, message: Message):
    args = user.split_some(message.text, 3, ' ', '\n')
    if not args or len(args) < 4:
        await message.reply_text(
            user.html_bold('usage:', '\n') +
            user.html_mono('.iUser from-chat target-user to-chat')
        )
        return

    from_chat = args[1]
    target_user = args[2]
    to_chat = args[3]
    all_messages = []

    async for current_message in user.search_messages(
        chat_id=from_chat,
        from_user=target_user
    ):
        all_messages.append(current_message.id)
        if len(all_messages) % 15 == 0:
            await asyncio.sleep(2)
        elif len(all_messages) % 300 == 0:
            await asyncio.sleep(20)
        elif len(all_messages) % 200 == 0:
            await asyncio.sleep(10)
        elif len(all_messages) % 50 == 0:
            await asyncio.sleep(5)
    
    all_messages.reverse()        
    try:
        await user.forward_all_messages(
            chat_id=to_chat,
            from_chat_id=from_chat,
            message_ids=all_messages,
        )
    except Exception as ex:
        await user.reply_exception(
            message=message,
            e=ex,
        )
