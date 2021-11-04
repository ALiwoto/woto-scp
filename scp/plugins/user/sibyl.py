from scp import user, bot
from scp.utils.selfInfo import info
from scp.utils.strUtils import name_check, permissionParser

@user.on_message(
    (user.sudo | user.owner) &
    user.command('sinfo'),
)
async def _(_, message: user.types.Message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        if message.reply_to_message.forward_from:
            get_user = message.reply_to_message.forward_from.id
        else:
            get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    
