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
        the_info = user.sibyl.user_info(get_user)
        if the_info.banned:
            txt = "<b>" + "This user is banned in Sibyl System." + "</b>\n"
            txt += "<b>" + "ID: " + "</b><code>" + str(the_info.user_id) + "</code>\n"
            await message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=True)
            return
        else:
            txt = "<b>" + "Sibyl System scan results:" + "</b>\n"
            txt += "<b>" + "‍ •ID: " + "</b><code>" + str(the_info.user_id) + "</code>\n"
            txt += "<b>" + "‍ •Is banned: " + "</b><code>" + str(the_info.banned) + "</code>\n"
            txt += "<b>" + "‍ •Crime Coefficient: " + "</b><code>" + str(the_info.crime_coefficient) + "</code>\n"
            txt += "<b>" + "‍ •Last update: " + "</b><code>" + str(the_info.date) + "</code>\n"
            await message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await message.reply_text("Got error: <code>" + html.escape(str(e)) + "</code>", parse_mode="HTML")
        return
    
