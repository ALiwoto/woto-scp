import asyncio
from scp import user
from pyrogram.types import (
    Message,
    Chat,
)


@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['pirate'],
        prefixes=user.cmd_prefixes,
    ),
)
async def pirate_handler(_, message: Message):
    if not user.the_bots or len(user.the_bots) < 1:
        await message.reply_text('bot lists is empty.')
        return
    
    if not user.are_bots_started:
        top_message = await message.reply_text(user.html_mono('starting bots...'))
        await user.start_all_bots()
        await top_message.edit_text(user.html_mono('bots started.'))
        

    args = user.split_message(message)
    if not args or len(args) < 2:
        return
    
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
                to_id = messages[0].message_id
    except Exception as e:
        return await message.reply_text(user.html_mono(e))

    link_pre = f'https://t.me/c/{str(the_chat.id)[4:]}/'
    channel_text = f'Pirating messages from {from_id} to {to_id} in {the_chat.title}\n'
    channel_text += 'target username: @' + the_chat.username + '\n'
    channel_text += f'format: @{the_chat.username} [' + user.html_mono(the_chat.id) + ']: '
    channel_text += user.html_link(from_id, link_pre + f'{from_id}') + '-'
    channel_text += user.html_link(to_id, link_pre + f'{to_id}')
    channel_post: Message = await user.send_message(
        chat_id=user.private_resources,
        text=channel_text,
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
        except:
            failed += 1
            continue

    text = user.html_bold(f'Tried to pirate {done+failed} messages from ')
    text += user.html_normal(f'{the_chat.title} [') + user.html_mono(f'{target_chat}', '].\n')
    text += user.html_mono(done, ' messages were pirated successfully.\n')
    text += user.html_mono(failed, ' messages were not pirated.')
    await message.reply_text(text, disable_web_page_preview=True, parse_mode='html')

@user.on_message(
	~user.filters.forwarded &
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['cBackup'],
        prefixes=user.cmd_prefixes,
    ),
)
async def cBackup_handler(_, message: Message):
    if not user.the_bots or len(user.the_bots) < 1:
        await message.reply_text('bot lists is empty.')
        return
    
    if not user.are_bots_started:
        top_message = await message.reply_text(user.html_mono('starting bots...'))
        await user.start_all_bots()
        await top_message.edit_text(user.html_mono('bots started.'))
    
    #target username: rickychannel_movies
    all_usernames = [
        'tt_mm_ii_gg_mm_ll', 'tt_mm_meow_ff_moheyou', 'tt_mm_ss_ff_lolol'
    ]
    target_chat = 'rickychannel_movies'
    public_username: str = all_usernames[0]
    tg_link_first = f'https://t.me/{public_username}/'
    the_chat: Chat = None
    backup_channel_id = -1001675937900
    from_id: int = 1
    to_id: int = 0
    try:
        the_chat = await user.get_chat(target_chat)
    except Exception as e:
        return await message.reply_text(user.html_mono(e))
    try:
        messages = await user.get_history(
            chat_id=target_chat,
            limit=1,
        )
        if messages:
            to_id = messages[0].message_id
    except Exception as e:
        return await message.reply_text(user.html_mono(e))
    
    if to_id < 10:
        to_id = 77144
    
    current_user_message: Message = None
    current_bot_index: int = 0
    done: int = 0
    failed: int = 0
    
    for index in range(from_id, to_id + 1):
        await asyncio.sleep(5)
        current_bot_index = index % len(user.the_bots)
        public_username = all_usernames[index % len(all_usernames)]
        tg_link_first = f'https://t.me/{public_username}/'
        try:
            current_user_message = await user.the_bots[current_bot_index].forward_messages(
                chat_id=public_username,
                from_chat_id=target_chat,
                message_ids=index,
            )

            current_user_message = await user.send_message(
                chat_id=current_user_message.from_user.id,
                text=tg_link_first+str(current_user_message.message_id),
                disable_web_page_preview=False,
            )

            if current_user_message.service:
                print('service')
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
                    current_user_message = await user.the_bots[current_bot_index].get_messages(
                        chat_id=current_user_message.chat.id,
                        message_ids=current_user_message.message_id,
                    )
                    if current_user_message.web_page or counter > 6:
                        break
                if not current_user_message.web_page:
                    print('no preview: ', current_user_message.text)
                    continue

            if current_user_message.web_page.document:
                await user.the_bots[current_bot_index].send_document(
                    chat_id=backup_channel_id,
                    document=current_user_message.web_page.document.file_id,
                )
            elif current_user_message.web_page.audio:
                await user.the_bots[current_bot_index].send_audio(
                    chat_id=backup_channel_id,
                    audio=current_user_message.web_page.audio.file_id,
                )
            elif current_user_message.web_page.video:
                await user.the_bots[current_bot_index].send_video(
                    chat_id=backup_channel_id,
                    video=current_user_message.web_page.video.file_id,
                )
            elif current_user_message.web_page.photo:
                await user.the_bots[current_bot_index].send_photo(
                    chat_id=backup_channel_id,
                    photo=current_user_message.web_page.photo.file_id,
                )
            elif current_user_message.web_page.animation:
                await user.the_bots[current_bot_index].send_animation(
                    chat_id=backup_channel_id,
                    animation=current_user_message.web_page.animation.file_id,
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
        except Exception as e:
            failed += 1
    
    text = user.html_bold(f'Tried to backup {done+failed} messages from ')
    text += user.html_normal(f'{the_chat.title} [') + user.html_mono(f'{target_chat}', '].\n')
    text += user.html_mono(done, ' messages were backed up successfully.\n')
    text += user.html_mono(failed, ' messages were not backed up.')
    await message.reply_text(text, disable_web_page_preview=True, parse_mode='html')


@user.on_message(
    ~(
        user.owner | 
        user.sudo | 
        user.filters.private
    ) & 
    user.filters.animation &
    user.wfilters.intemperate,
    group=123,
)
async def send_stare_gif(_, message: Message):
    if message.animation.file_unique_id != 'AgADbgADz3-YRg':
        return
    await user.send_animation(
        message.chat.id, 
        message.animation.file_id, 
        reply_to_message_id=message.message_id,
    )

