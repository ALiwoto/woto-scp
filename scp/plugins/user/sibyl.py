import logging
from time import sleep
from pyrogram.types import (
    Message,
)
from pyrogram.types.user_and_chats.user import User

from scp import user
import html
from SibylSystem.types import GeneralInfo

from scp.utils.parser import( 
    html_bold,
    html_mention,
    html_mention_by_user, 
    html_mono, 
    html_normal,
)

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
        txt = html_bold("Sibyl System scan results:", "\n")
        the_men = html_mention(
            value=the_info.user_id,
            client=user,
        )
        if isinstance(the_men, str) and len(the_men) > 0:
            txt += html_bold("‍ • User: ") + the_men + "\n"
        
        txt += html_bold("‍ • ID: ") + html_mono(the_info.user_id, "\n")
        txt += html_bold("‍ • Is banned: ") + html_mono(the_info.banned, "\n")
        if the_info.banned:
            if the_info.banned_by != 0:
                the_banner: User
                try:
                    the_banner = user.get_users(the_info.banned_by)
                except Exception: pass
                txt += html_bold("‍ • Banned by: ") + (
                    html_mono(the_info.banned_by, "\n") 
                    if not the_banner 
                    else html_mention_by_user(the_banner, "\n")
                )
            if the_info.ban_flags and len(the_info.ban_flags) > 0:
                f = ', '.join(the_info.ban_flags)
                txt += html_bold("‍ • Ban flags: ") + html_mono(f, "\n")
            txt += html_bold("‍ • Crime Coefficient: ") + html_mono(the_info.crime_coefficient, "\n")
            txt += html_bold("‍ • Last update: ") + html_mono(the_info.date, "\n")
            txt += html_bold("‍ • Ban reason: ")+ + html_mono(the_info.reason, "\n")
        else:
            txt += html_bold("‍ • Crime Coefficient: ") + html_mono(the_info.crime_coefficient, "\n")
            txt += html_bold("‍ • Last update: ") + html_mono(the_info.date, "\n")
            if general_info:
                div = user.sibyl.get_div(general_info)
                txt += html_normal(
                    "\nThe user is a valid " ,
                    user.sibyl.get_general_str(general_info),
                    " registered at PSB " + (f"division {div}." if div else "."),
                )
        
        await my_msg.edit_text(txt, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print(e)
        logging.exception('Error occurred')
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


