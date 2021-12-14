from time import sleep
from pyrogram.types import (
    Message,
)
from scp import user
import html

@user.on_message(
    (user.sudo | user.owner) &
    user.command(
        ['sinfo', 'sinfo!'],
    ),
)
async def sinfo_handler(_, message: Message):
    cmd = message.command
    is_silent = cmd[0].endswith('!')
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
    ptxt = "Sending cymatic scan request to Sibyl System."
    my_msg = await message.reply_text(ptxt)
    if not is_silent:
        sleep(1.2)
        ptxt += "."
        my_msg = await my_msg.edit_text(ptxt)
        sleep(1.2)
        ptxt += "."
        my_msg = await my_msg.edit_text(ptxt)
    
    try:
        the_info = user.sibyl.user_info(get_user)
        if not the_info:
            await my_msg.edit_text('failed to receive info from Sibyl System.')
            return
        txt = "<b>" + "Sibyl System scan results:" + "</b>\n"
        txt += "<b>" + "‍ • ID: " + "</b><code>" + str(the_info.user_id) + "</code>\n"
        txt += "<b>" + "‍ • Is banned: " + "</b><code>" + str(the_info.banned) + "</code>\n"
        if the_info.banned:
            if the_info.banned_by != 0:
                txt += "<b>" + "‍ • Banned by: " + "</b><code>" + str(the_info.banned_by) + "</code>\n"
            if the_info.ban_flags and len(the_info.ban_flags) > 0:
                f = ', '.join(the_info.ban_flags)
                txt += "<b>" + "‍ • Ban flags: " + "</b><code>" + html.escape(f) + "</code>\n"
            txt += "<b>" + "‍ • Crime Coefficient: " + "</b><code>" + str(the_info.crime_coefficient) + "</code>\n"
            txt += "<b>" + "‍ • Last update: " + "</b><code>" + str(the_info.date) + "</code>\n"
            txt += "<b>" + "‍ • Ban reason: " + "</b><code>" + html.escape(the_info.reason) + "</code>\n"
        else:
            txt += "<b>" + "‍ • Crime Coefficient: " + "</b><code>" + str(the_info.crime_coefficient) + "</code>\n"
            txt += "<b>" + "‍ • Last update: " + "</b><code>" + str(the_info.date) + "</code>\n"
        
        
        await my_msg.edit_text(txt, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await my_msg.edit_text("Got error: <code>" + html.escape(str(e)) + "</code>", parse_mode="HTML")
        return

@user.on_message(
    (user.sudo | user.owner) &
    user.command('sban'),
)
async def sban_handler(_, message: user.types.Message):
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
    ptxt = "Sending cymatic scan request to Sibyl System."
    my_msg = await message.reply_text(ptxt)
    sleep(1.2)
    ptxt += "."
    my_msg = await my_msg.edit_text(ptxt)
    sleep(1.2)
    ptxt += "."
    my_msg = await my_msg.edit_text(ptxt)
    try:
        the_info = user.sibyl.user_info(get_user)
        if not the_info:
            await my_msg.edit_text('failed to receive info from Sibyl System.')
            return
        txt = "<b>" + "Sibyl System scan results:" + "</b>\n"
        txt += "<b>" + "‍ • ID: " + "</b><code>" + str(the_info.user_id) + "</code>\n"
        txt += "<b>" + "‍ • Is banned: " + "</b><code>" + str(the_info.banned) + "</code>\n"
        if the_info.banned:
            if the_info.banned_by != 0:
                txt += "<b>" + "‍ • Banned by: " + "</b><code>" + str(the_info.banned_by) + "</code>\n"
            if the_info.ban_flags and len(the_info.ban_flags) > 0:
                f = ', '.join(the_info.ban_flags)
                txt += "<b>" + "‍ • Ban flags: " + "</b><code>" + html.escape(f) + "</code>\n"
            txt += "<b>" + "‍ • Crime Coefficient: " + "</b><code>" + str(the_info.crime_coefficient) + "</code>\n"
            txt += "<b>" + "‍ • Last update: " + "</b><code>" + str(the_info.date) + "</code>\n"
            txt += "<b>" + "‍ • Ban reason: " + "</b><code>" + html.escape(the_info.reason) + "</code>\n"
        else:
            txt += "<b>" + "‍ • Crime Coefficient: " + "</b><code>" + str(the_info.crime_coefficient) + "</code>\n"
            txt += "<b>" + "‍ • Last update: " + "</b><code>" + str(the_info.date) + "</code>\n"
        
        
        await my_msg.edit_text(txt, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await my_msg.edit_text("Got error: <code>" + html.escape(str(e)) + "</code>", parse_mode="HTML")
        return


