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
    if not user.scp_config.auto_read_mode:
        return
    
    if (not user.auto_read_enabled or message.id % 2 != 0 or
        message.chat.id == user.scp_config.avalon_pms):
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
    if not user.scp_config.auto_read_mode:
        return await message.reply_text('Auto read is disabled globally in config.')
    
    if message.text.find('true') > 0:
        if user.auto_read_enabled:
            return await message.reply_text('Auto read is already enabled.')
        
        user.auto_read_enabled = True
        return await message.reply_text('Auto read has been enabled.')

    if message.text.find('false') > 0:
        if not user.auto_read_enabled:
            return await message.reply_text('Auto read is already disabled.')
        user.auto_read_enabled = False
        return await message.reply_text('Auto read has been disabled.')

    if user.auto_read_enabled:
        await message.reply_text('Auto read is enabled.')
    else:
        await message.reply_text('Auto read is disabled.')


@user.on_message(
    user.filters.me & 
    user.filters.group &
    user.wfilters.noisy_bluetext,
    group=100,
)
async def auto_remove_bluetext_handler(_, message: Message):
    if not user.scp_config.auto_read_mode:
        return
    
    if not user.auto_read_enabled or \
        message.chat.title.lower().find('test') != -1:
        return
    elif message.text.find('@') != -1: await asyncio.sleep(1.2)
    
    try:
        await message.delete()
    except Exception: return

@user.on_edited_message(
    user.filters.bot,
    group=100,
)
@user.on_message(
    user.filters.bot,
    group=100,
)
async def auto_sff_handler(_, message: Message):
    """
    sff is short for "send-friend-fac".
    """
    if not message.text: return
    msg_text = message.text.lower()
    if msg_text.find("have finished their work") != -1 or \
        msg_text.find("work options for the worker") != -1:
        await asyncio.sleep(3)
        return await message.click(0)
    
