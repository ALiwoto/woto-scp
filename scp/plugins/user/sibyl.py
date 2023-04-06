import asyncio
from pyrogram.types import (
    Message,
)
from pyrogram.types.user_and_chats.user import User
from pyrogram.enums.parse_mode import ParseMode
from scp import user
from SibylSystem.types import GeneralInfo


@user.on_message(
    (user.owner | user.enforcer | user.inspector) &
    user.command(
        ['sinfo', 'sinfo!'],
        prefixes=user.cmd_prefixes,
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
    my_txt = "Sending cymatic scan request to Sibyl System."
    my_msg = await message.reply_text(my_txt)
    if not is_silent:
        await asyncio.sleep(1.2)
        my_txt += "."
        my_msg = await my_msg.edit_text(my_txt)
        await asyncio.sleep(1.2)
        my_txt += "."
        my_msg = await my_msg.edit_text(my_txt)
    
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
        txt = user.html_bold("Sibyl System scan results:", "\n")
        if my_user:
            the_mention = await user.html_mention(
                value=my_user,
                client=user,
            )
            txt += user.html_bold(" • User: ") + the_mention + "\n"
        
        txt += user.html_bold(" • ID: ") + user.html_mono(the_info.user_id, "\n")
        txt += user.html_bold(" • Is banned: ") + user.html_mono(the_info.banned, "\n")
        if the_info.banned:
            if the_info.banned_by != 0:
                the_banner: User
                try:
                    the_banner = await user.get_users(the_info.banned_by)
                except Exception: pass
                txt += user.html_bold(" • Banned by: ") + (
                    user.html_mono(the_info.banned_by, "\n") 
                    if not the_banner 
                    else user.html_mention_by_user(the_banner, "\n")
                )
            if the_info.ban_flags and len(the_info.ban_flags) > 0:
                f = ', '.join(the_info.ban_flags)
                txt += user.html_bold(" • Ban flags: ") + user.html_mono(f, "\n")
            txt += user.html_bold(" • Crime Coefficient: ") + user.html_mono(the_info.crime_coefficient, "\n")
            txt += user.html_bold(" • Last update: ") + user.html_mono(the_info.date, "\n")
            txt += user.html_bold(" • Ban reason: ")+ user.html_mono(the_info.reason, "\n")
            txt += user.html_bold(" • Ban source: ")+ user.html_mono(the_info.ban_source_url, "\n")
        else:
            txt += user.html_bold(" • Crime Coefficient: ") + user.html_mono(the_info.crime_coefficient, "\n")
            txt += user.html_bold(" • Last update: ") + user.html_mono(the_info.date, "\n")
            if general_info:
                div = user.sibyl.get_div(general_info)
                txt += user.html_normal(
                    "\nThe user is a valid " ,
                    user.sibyl.get_general_str(general_info),
                    " registered at PSB " + (f"division {div}." if div else "."),
                )
        
        await my_msg.edit_text(txt, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        return await my_msg.edit_text("Got error: " + user.html_mono(e), parse_mode=ParseMode.HTML)
        


@user.on_message(
    (user.owner | user.inspector) &
    user.command(
        ['fScan', 'fScan!'],
        prefixes=user.cmd_prefixes,
    ),
)
async def fScan_handler(_, message: Message):
    if not message.reply_to_message: return # TODO
    #cmd = message.command
    #is_silent = user.is_silent(message)
    replied = message.reply_to_message
    target_user = replied.from_user.id
    reason_list = user.split_some(message.text, 1, ' ', '\n')
    if len(reason_list) < 2:
        await message.reply_text('reason is required for this action')
    the_reason = reason_list[1]

    p_txt = user.html_mono("Sending cymatic scan request to Sibyl System.")
    my_msg = await message.reply_text(p_txt)

    try:
        user.sibyl.ban(
            user_id=target_user,
            reason=the_reason,
            source=message.link,
            message=replied.text,
        )
    except Exception as e:
        return await my_msg.edit_text("Got error: " + user.html_mono(e), parse_mode=ParseMode.HTML)
        
    
    return await my_msg.edit_text(
        user.html_mono('Cymatic scan request has been sent to Sibyl.'), 
        parse_mode=ParseMode.HTML,
    )


@user.on_message(
    (user.owner | user.inspector) &
    user.command(
        ['revert', 'revert!'],
        prefixes=user.cmd_prefixes,
    ),
)
async def revert_handler(_, message: Message):
    target_user: int = 0
    cmd = message.command
    replied = message.reply_to_message
    if replied and replied.from_user:
        target_user = replied.from_user.id
    
    if target_user == 0:
        if cmd and len(cmd) > 0:
            the_user = await user.get_users(cmd[0])
            if the_user and isinstance(the_user, User):
                target_user = the_user.id
            else:
                target_user = cmd[1]


    my_msg = await message.reply_text("Sending cymatic scan request to Sibyl System.")

    try:
        user.sibyl.revert(target_user)
    except Exception as e:
        await my_msg.edit_text("Got error: " + user.html_mono(e), parse_mode=ParseMode.HTML)
        return
    
    await my_msg.edit_text(
        user.html_mono('Cymatic scan request has been sent to Sibyl.'), 
        parse_mode=ParseMode.HTML,
    )



@user.on_message(
    (user.owner | user.inspector) &
    user.command(
        ['rScan', 'rScan!'],
        prefixes=user.cmd_prefixes,
    ),
)
async def rScan_handler(_, message: Message):
    #cmd = message.command
    #is_silent = user.is_silent(message)
    reason_list = user.split_some(message.text, 2, ' ', '\n')
    if len(reason_list) < 3:
        return await message.reply_text('usage: .rScan LINK reason')
    msg_link = reason_list[1]
    the_reason = reason_list[2]

    p_txt = user.html_mono("Sending cymatic scan request to Sibyl System.")
    my_msg = await message.reply_text(p_txt)
    target_message = await user.get_message_by_link(msg_link)
    if not target_message:
        return await message.reply_text('message not found')
    
    target_user = target_message.from_user.id
    the_final_link: str = message.link
    if the_final_link and the_final_link.find('/c/') != -1:
        t_link = target_message.link
        if t_link and t_link.find('/c/') == -1:
            the_final_link = t_link

    try:
        user.sibyl.ban(
            user_id=target_user,
            reason=the_reason,
            source=the_final_link,
            message=target_message.text,
        )
    except Exception as e:
        await my_msg.edit_text("Got error: " + user.html_mono(e), parse_mode=ParseMode.HTML)
        return
    
    return await my_msg.edit_text(
        user.html_mono('Cymatic scan request has been sent to Sibyl.'), 
        parse_mode=ParseMode.HTML,
    )


