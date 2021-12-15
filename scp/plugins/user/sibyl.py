from time import sleep
from pyrogram.types import (
    Message,
)
from pyrogram.types.user_and_chats.user import User

from scp import user
from SibylSystem.types import GeneralInfo

from scp.utils.parser import( 
    html_bold,
    html_mention,
    html_mention_by_user, 
    html_mono, 
    html_normal,
    split_some,
)

@user.on_message(
    (user.owner | user.enforcer) &
    user.command(
        ['sinfo', 'sinfo!'],
    ),
)
async def sinfo_handler(_, message: Message):
    cmd = message.command
    is_silent = user.is_silent(message)
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
    
    my_user : User = None
    try:
        my_user = await user.get_users(the_user)
    except Exception: pass
    try:
        if my_user:
            the_user = my_user.id
        the_info = user.sibyl.user_info(the_user)
        general_info: GeneralInfo = None
        try:
            general_info = user.sibyl.get_general_info(the_user)
        except Exception: pass
        if not the_info:
            await my_msg.edit_text('failed to receive info from Sibyl System.')
            return
        txt = html_bold("Sibyl System scan results:", "\n")
        if my_user:
            the_mention = await html_mention(
                value=my_user,
                client=user,
            )
            txt += html_bold(" • User: ") + the_mention + "\n"
        
        txt += html_bold(" • ID: ") + html_mono(the_info.user_id, "\n")
        txt += html_bold(" • Is banned: ") + html_mono(the_info.banned, "\n")
        if the_info.banned:
            if the_info.banned_by != 0:
                the_banner: User
                try:
                    the_banner = await user.get_users(the_info.banned_by)
                except Exception: pass
                txt += html_bold(" • Banned by: ") + (
                    html_mono(the_info.banned_by, "\n") 
                    if not the_banner 
                    else html_mention_by_user(the_banner, "\n")
                )
            if the_info.ban_flags and len(the_info.ban_flags) > 0:
                f = ', '.join(the_info.ban_flags)
                txt += html_bold(" • Ban flags: ") + html_mono(f, "\n")
            txt += html_bold(" • Crime Coefficient: ") + html_mono(the_info.crime_coefficient, "\n")
            txt += html_bold(" • Last update: ") + html_mono(the_info.date, "\n")
            txt += html_bold(" • Ban reason: ")+ html_mono(the_info.reason, "\n")
        else:
            txt += html_bold(" • Crime Coefficient: ") + html_mono(the_info.crime_coefficient, "\n")
            txt += html_bold(" • Last update: ") + html_mono(the_info.date, "\n")
            if general_info:
                div = user.sibyl.get_div(general_info)
                txt += html_normal(
                    "\nThe user is a valid " ,
                    user.sibyl.get_general_str(general_info),
                    " registered at PSB " + (f"division {div}." if div else "."),
                )
        
        await my_msg.edit_text(txt, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        #print(e)
        #logging.exception("some errors found")
        await my_msg.edit_text("Got error: " + html_mono(e), parse_mode="HTML")
        return


@user.on_message(
    (user.owner) &
    user.command(
        ['fScan', 'fScan!']
    ),
)
async def scan_handler(_, message: Message):
    if not message.reply_to_message: return # TODO
    #cmd = message.command
    #is_silent = user.is_silent(message)
    replied = message.reply_to_message
    target_user = replied.from_user.id
    the_reason = split_some(message.text, 2, ' ', '\n')

    ptxt = "Sending cymatic scan request to Sibyl System."
    my_msg = await message.reply_text(ptxt)

    try:
        user.sibyl.ban(
            user_id=target_user,
            reason=the_reason,
            source=message.link,
            message=replied.text,
        )
    except Exception as e:
        await my_msg.edit_text("Got error: " + html_mono(e), parse_mode="HTML")

