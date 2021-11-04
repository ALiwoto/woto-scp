from scp import user
import html

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
    try:
        the_info = user.sibyl.get_info(get_user)
        if the_info.banned:
            await message.reply_text(html.escape("This user is banned."), parse_mode="HTML", disable_web_page_preview=True)
            return
        else:
            await message.reply_text(html.escape(f"{the_info}"), parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await message.reply_text("<code>" + html.escape(str(e)) + "</code>", parse_mode="HTML")
        return
    
