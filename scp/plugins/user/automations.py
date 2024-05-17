import asyncio
from scp import user
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
)
from pyrogram.raw.functions.messages import RequestWebView
from scp.utils.media_utils import (
    BaseTaskContainer,
    NcInfoContainer,
    TpsInfoContainer
)
import pyrogram

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
    user.owner & user.command('clickWeb'),
)
async def clickWeb_handler(_, message: Message):
    is_verbose = message.text.find("--verbose") != -1
    message.text = message.text.replace("--verbose", "").strip()

    the_link = user.get_non_cmd(message)
    if not the_link and not (message.reply_to_message and 
                             not user.message_has_keyboard(message.reply_to_message)):
        return await message.reply_text('No link found, you can also reply to the target message.')
    
    try:
        if message.reply_to_message and user.message_has_keyboard(message.reply_to_message):
            # yes, this will work. it might be weird for you, but not for me
            click_result = await user.click_web_button_by_message_link(message.reply_to_message)
        else:
            # the provided link in front of the message has to look like "https://t.me/somethingBot/1234"
            # where the 1234 number is actually the message id of the message that contains the
            # WebPage inline button.
            click_result = await user.click_web_button_by_message_link(the_link, term_search="welcome")
        
        clicked_message = getattr(click_result, "message", None)
        if isinstance(clicked_message, Message):
            if clicked_message.from_user.is_bot:
                #FIXME: move this part to message.link in wpyrogram lib.
                the_link = f"https://t.me/{clicked_message.from_user.username}/{clicked_message.id}"
            else:
                the_link = clicked_message.link
    except Exception as e:
        return await message.reply_text('Error: \n\t' + user.html_mono(str(e)))

    target_url = click_result.url
    if target_url.find('clicker') != -1:
        nc_container = getattr(user, 'nc_container', None)
        if isinstance(nc_container, BaseTaskContainer):
            # cancel the previous task
            await nc_container.cancel_task()
        
        nc_container = NcInfoContainer(
            url=target_url,
            refresher_obj=user,
            refresher=user.click_web_button_by_message_link,
            src_url=the_link,
        )
        setattr(user, 'nc_container', nc_container)
        # start the task in another coroutine
        asyncio.create_task(nc_container.start_task())
    elif target_url.find("a\u0070p\u002e\u0074a\u0070\u0073\u0077\u0061\u0070.\u0063l\u0075b") != -1:
        tps_container = getattr(user, 'tps_container', None)
        if isinstance(tps_container, BaseTaskContainer):
            # cancel the previous task
            await tps_container.cancel_task()
        
        tps_container = TpsInfoContainer(
            url=target_url,
            refresher_obj=user,
            refresher=user.click_web_button_by_message_link,
            src_url=the_link,
            verbose=is_verbose,
        )
        setattr(user, 'tps_container', tps_container)
        # start the task in another coroutine
        asyncio.create_task(tps_container.start_task())

        await asyncio.sleep(5)
        txt = ""
        if tps_container.player_info:
            txt = user.html_bold("Task is started successfully!\n")
            txt += user.html_normal(f"Balance: {tps_container.player_info['shares']} | ")
            txt += user.html_normal(f"{tps_container.player_info['energy']}")
        else:
            txt = user.html_normal("player_info object is not set... maybe 5s is not enough?")
        return await message.reply_text(txt)
    else:
        # TODO: implement other kinds of urls
        return await message.reply_text('No implementation found for this kind of url: ' + target_url)

@user.on_message(
    user.owner & user.command('stopWeb'),
)
async def stopWeb_handler(_, message: Message):
    nc_container = getattr(user, 'nc_container', None)
    if isinstance(nc_container, BaseTaskContainer):
        await nc_container.cancel_task()
        return await message.reply_text('Task has been cancelled.')
    return await message.reply_text('No task found.')

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
    group=101,
)
@user.on_message(
    user.filters.bot,
    group=101,
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
        try:
            return await message.click(0)
        except Exception: return
    
