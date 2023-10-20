from scp import user, bot
from pyrogram.types import (
    Message,
    CallbackQuery,
)
import yt_dlp
import os


__PLUGIN__ = 'youtube'


__cached_yt_media_infos = {}

@user.on_message(
    (user.sudo | user.owner) &
    user.command(
        ['yt', 'youtube'],
    ),
)
async def yt_handler(_, message: Message):
    user_input = user.get_non_cmd(message)
    if not user_input:
        txt = user.html_bold("Usage:") + "\n"
        txt += user.html_mono("   .yt <url>")
        return await message.reply_text(txt, quote=True)
    
    with yt_dlp.YoutubeDL() as ydl:
        try:
            result = ydl.extract_info(user_input, download=False)
        except Exception as err:
            return await message.reply_text(f"error at extract_info from url: {err}", quote=True)

    media_id = result["id"]
    title = result["title"]
    thumbnail = result["thumbnail"]
    duration_string = result["duration_string"]
    view_count = result["view_count"]
    result["cut_from"] = "00:00.000"
    result["cut_to"] = "00:00.000"
    result["chat_id"] = message.chat.id
    result["message_id"] = message.id
    
    __cached_yt_media_infos[media_id] = result

    txt = user.html_bold("💠 Youtube media info\n")
    txt += user.html_bold("  Title:") + user.html_link(title, result["url"]) + "\n"
    txt += user.html_bold("  Duration:") + f" {duration_string}\n"
    txt += user.html_bold("  Views:") + f" {view_count}\n"
    txt += user.html_normal("\nSelect a quality to download:")
    keyboard = [
        {"Mp3" : f"yt_{media_id}_mp3"},
        {"240p" : f"yt_{media_id}_240"},
        {"360p" : f"yt_{media_id}_360"},
        {"480p" : f"yt_{media_id}_480"},
        {"720p" : f"yt_{media_id}_720"},
        {"1080p" : f"yt_{media_id}_1080"},
    ]

    try:
        if thumbnail:
            return await message.reply_photo(
                photo=thumbnail,
                caption=txt,
                reply_markup=keyboard,
            )
    except: pass

    await message.reply_text(
        text=txt,
        reply_markup=keyboard,
    )

@bot.on_callback_query(
    (user.sudo | user.owner) 
    & bot.filters.regex('^yt_'),
)
async def _(_, query: CallbackQuery):
    query_data = query.data.split("_")
    if len(query_data) != 3:
        return await query.answer(
            "bad callback data",
            show_alert=True,
        )
        
    
    media_info = __cached_yt_media_infos.get(query_data[1], None)
    if not media_info:
        return await query.answer(
            "media info not found",
            show_alert=True,
        )
    
    ydl_opts: dict = {}
    if query_data[2] == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            "quiet": True,
        }
    else:
        ydl_opts = {
            "format": f"bestvideo[height<={query_data[2]}]+bestaudio/best[height<={query_data[2]}]",
            "quiet": True,
        }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        file_name = ydl.prepare_filename(media_info)
        try:
            ydl.process_info(media_info)
        except Exception as err:
            return await query.message.reply_text(f"error at process_info: {err}", quote=True)
    
    if query_data[2] == "mp3":
        # convert the file to mp3 with ffmpeg if it's not mp3
        if not file_name.endswith(".mp3"):
            correct_file_name = file_name.replace(file_name.split(".")[-1], "mp3")
            user.remove_file(file_name)
            await user.shell_base(f"{user.ffmpeg_path} -i {file_name} {correct_file_name} -hide_banner -loglevel error")
            file_name = correct_file_name
        
        return await user.send_audio(
            chat_id=media_info["chat_id"],
            audio=file_name,
            caption=media_info["title"],
            reply_to_message_id=media_info["message_id"],
            duration=media_info["duration"],
            thumb=media_info["thumbnail"],
        )

    # the media is a video
    await user.send_video(
        chat_id=media_info["chat_id"],
        video=file_name,
        caption=media_info["title"],
        reply_to_message_id=media_info["message_id"],
        duration=media_info["duration"],
        thumb=media_info["thumbnail"],
    )
    os.remove(file_name)
    del __cached_yt_media_infos[query_data[1]]