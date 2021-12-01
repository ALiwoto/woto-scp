from scp import user

__PLUGIN__ = 'autoread'

@user.on_message(
    ~(user.owner | user.sudo | user.my_contacts | user.filters.private),
    group=100,
)
async def auto_read_handler(_, message: user.types.Message):
    if not user.auto_read_enabled:
        return
    try:
        await user.read_history(message.chat.id)
    except Exception:
        return
    return

@user.on_message(
    user.owner & user.command('gautoread'),
)
async def sinfo_handler(_, message: user.types.Message):
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
