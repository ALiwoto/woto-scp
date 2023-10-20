from scp import user, bot
from scp.utils.selfInfo import info
from pyrogram.types import (
    Message,
    InlineQuery,
    CallbackQuery,
    ChosenInlineResult
)
from pyrogram.raw.types.messages.bot_results import (
    BotResults,
)
import yt_dlp
import os


__PLUGIN__ = 'youtube'


links = {}

@user.on_message(
    (user.sudo | user.owner) &
    user.command(
        'yt',
        prefixes=user.cmd_prefixes,
    ),
)
async def yt_handler(_, message: Message):
    cmd = message.command
    if len(cmd) != 2:
        await message.reply("invalid args")
        return
    
    try:
        x: BotResults = await user.get_inline_bot_results(
            info['_bot_username'],
            '_yt ' + cmd[1],
        )
    except (
        user.exceptions.PeerIdInvalid,
        user.exceptions.BotResponseTimeout,
    ) as err:
        return await message.reply_text(err, quote=True)
    try:
        m = x.results[0]
    except (
        IndexError,
        ValueError,
    ):
        await message.reply("inline bot results is empty")
        return

    links[m.id] = { # result id
        "url": cmd[1],
        "chat_id": message.chat.id,
        "message_id": message.id,
    }
    await message.reply_inline_bot_result(
        x.query_id,
        m.id,
        quote=True,
    )


@bot.on_inline_query(
    user.filters.user(
        info['_user_id'],
    )
    & user.filters.regex('^_yt'),
)
async def yt_in_qu(_, query: InlineQuery):
    try:
        answers = []
    except (ValueError, IndexError):
        return
    
    keyboard = user.types.InlineKeyboardMarkup([
        [
            user.types.InlineKeyboardButton("...", "wait"),
        ],
    ])
    answers.append(
        user.types.InlineQueryResultArticle(
            title="yt",
            input_message_content=user.types.InputTextMessageContent("fetching data"),
            reply_markup=keyboard,
        )
    )

    await query.answer(
        answers,
        cache_time=0,
    )

@bot.on_chosen_inline_result(
    user.filters.user(
        info['_user_id'],
    )
)
async def yt_ch_in(_, chosen: ChosenInlineResult):
    try:
        this = links[chosen.result_id]
    except KeyError:
        return
    if chosen.query.strip().startswith("_yt"):
        cmd = chosen.query.split(" ")
        if len(cmd) != 2:
            del links[chosen.result_id]
            return
    links[chosen.result_id]["inline_message_id"] = chosen.inline_message_id
    with yt_dlp.YoutubeDL() as ydl:
        try:
            result = ydl.extract_info(this["url"], download=False)
        except:
            await user.send_message(this["chat_id"], "error at extract_info from url", reply_to_message_id=this["message_id"])
            del links[chosen.result_id]
            return
    id = result["id"]
    title = result["title"]
    thumbnail = result["thumbnail"]
    duration = result["duration"]
    duration_string = result["duration_string"]
    view_count = result["view_count"]
    

    text = f"Title: {title}\nDuration: {duration_string}\nViews: {view_count}"
    keyboard = user.types.InlineKeyboardMarkup([
        [user.types.InlineKeyboardButton("240p", callback_data=f"yt_{chosen.result_id}_240")],
        [user.types.InlineKeyboardButton("360p", callback_data=f"yt_{chosen.result_id}_360")],
        [user.types.InlineKeyboardButton("480p", callback_data=f"yt_{chosen.result_id}_480")],
        [user.types.InlineKeyboardButton("720p", callback_data=f"yt_{chosen.result_id}_720")],
        [user.types.InlineKeyboardButton("1080p", callback_data=f"yt_{chosen.result_id}_1080")],
    ])
    await bot.edit_inline_text(
        inline_message_id=chosen.inline_message_id,
        text=text,
        reply_markup=keyboard,
    )

    #await user.send_message(this["chat_id"], "last yt_ch_in", reply_to_message_id=this["message_id"])
    
@bot.on_callback_query(
    bot.sudo
    & bot.filters.regex('^yt_'),
)
async def _(_, query: CallbackQuery):
    cmd = query.data.split("_")
    if len(cmd) != 3:
        await query.answer(
            "bad args in data",
            show_alert=True,
        )
        return
    try:
        this = links[cmd[1]]
    except KeyError:
        await query.answer(
            "link not found",
            show_alert=True,
        )
        return
    ydl_opts = {
        "format": f"bestvideo[height<={cmd[2]}]+bestaudio/best[height<={cmd[2]}]",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(this["url"], download=False)
        file_name = ydl.prepare_filename(info)
        id = info["id"]
        title = info["title"]
        thumbnail = info["thumbnail"]
        duration = info["duration"]
        duration_string = info["duration_string"]
        view_count = info["view_count"]
        try:
            ydl.process_info(info)
        except:
            await query.answer(
                "error in downloading",
                show_alert=True,
            )
    
    #await user.send_message(this["chat_id"], "last yt_ch_in", reply_to_message_id=this["message_id"])
    await user.send_video(
        this["chat_id"],
        file_name,
        reply_to_message_id=this["message_id"],
        duration=duration,
    )
    os.remove(file_name)
    del links[cmd[1]]