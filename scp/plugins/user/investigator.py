from scp import user
from pyrogram.types import (
    Message,
    Chat,
)

@user.on_message(
    ~user.filters.scheduled & 
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
    args = user.get_non_cmd(message)
    if not args or len(args) < 1:
        return
    
    target_chat = args[0]
    the_chat: Chat = None
    from_id: int = 1
    to_id: int = 0
    try:
        the_chat = await user.get_chat(target_chat)
    except Exception as e:
        return await message.reply_text(user.html_mono(e))
    try:
        if len(args) > 1:
            all_numbers = args[1].split('-')
            if len(all_numbers) == 2:
                from_id = int(all_numbers[0])
                to_id = int(all_numbers[1])
    except:
        messages = await user.get_history(
                chat_id=target_chat,
                limit=1,
        )
        if messages:
            to_id = messages[0].message_id
    
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

    text = user.html_bold(f'Tried to pirate {done+failed} messages from {the_chat.title}.\n')
    text += user.html_bold(f'{done} messages were copied successfully.\n')
    text += user.html_bold(f'{failed} messages were not copied.\n')
    await message.reply_text(text, disable_web_page_preview=True, parse_mode='html')
