import asyncio
from scp import user
from pyrogram.types import (
    Message,
)

__PLUGIN__ = 'automations'

@user.on_message(
    ~(
        user.owner | 
        user.sudo | 
        user.wfilters.my_contacts | 
        user.wfilters.stalk_text | 
        user.filters.private |
        user.filters.group
    ),
    group=100,
)
async def auto_read_handler(_, message: Message):
    if (not user.auto_read_enabled or message.id % 2 != 0 or
        message.chat.id == user.scp_config.pm_log_channel):
        return
    try:
        await user.read_chat_history(message.chat.id)
    except Exception:
        return
    return

@user.on_message(
    user.owner & user.command('gautoread'),
)
async def gautoread_handler(_, message: Message):
    if message.text.find('true') > 0:
        if user.auto_read_enabled:
            await message.reply_text('Auto read is already enabled.')
            return
        user.auto_read_enabled = True
        await message.reply_text('Auto read has been enabled.')
        
        return

    if message.text.find('false') > 0:
        if not user.auto_read_enabled:
            await message.reply_text('Auto read is already disabled.')
            return
        user.auto_read_enabled = False
        await message.reply_text('Auto read has been disabled.')
        
        return

    if user.auto_read_enabled:
        await message.reply_text('Auto read is enabled.')
    else:
        await message.reply_text('Auto read is disabled.')
    return


@user.on_message(
    user.filters.me & 
    user.filters.group &
    user.wfilters.noisy_bluetext,
    group=100,
)
async def auto_remove_bluetext_handler(_, message: Message):
    if not user.auto_read_enabled or message.chat.title.lower().find('test') != -1:
        return
    elif message.text.find('@') != -1: await asyncio.sleep(1.2)
    try:
        await message.delete()
    except Exception:
        return
    return

