from time import sleep
from pyrogram.types import (
    Message,
)
from scp import user
import html
from scp.sibyl.types.general_info import GeneralInfo

from scp.utils.parser import html_bold, html_mono, html_normal

@user.on_message(
    (user.sudo | user.owner) &
    user.command(
        ['sinfo', 'sinfo!'],
    ),
)
async def sinfo_handler(_, message: Message):
    cmd = message.command
    is_silent = cmd[0].endswith('!')
    the_user = 0
    if not message.reply_to_message and len(cmd) == 1:
        the_user = message.from_user.id
    elif len(cmd) == 1:
        if message.reply_to_message.forward_from:
            the_user = message.reply_to_message.forward_from.id
        else:
            the_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        the_user = cmd[1]
        try:
            the_user = int(cmd[1])
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
        the_info = user.sibyl.user_info(the_user)
        general_info: GeneralInfo
        try:
            general_info = user.sibyl.get_general_info(the_user)
        except Exception: pass
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
            txt += html_bold("‍ • Last update: ") + html_mono(str(the_info.date), "\n")
            if general_info:
                div = general_info.get_div()
                txt += html_normal(
                    "\nThe user is a valid " ,
                    general_info.to_general_perm(),
                    " registered at PSB " + (f"division {div}." if div else "."),
                )
        
        await my_msg.edit_text(txt, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print(e)
        await my_msg.edit_text("Got error: " +html_mono(str(e)), parse_mode="HTML")
        return



@user.on_message(
    (user.sudo | user.owner) &
    user.command('sban'),
)
async def sban_handler(_, message: user.types.Message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        the_user = message.from_user.id
    elif len(cmd) == 1:
        if message.reply_to_message.forward_from:
            the_user = message.reply_to_message.forward_from.id
        else:
            the_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        the_user = cmd[1]
        try:
            the_user = int(cmd[1])
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
        the_info = user.sibyl.user_info(the_user)
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


