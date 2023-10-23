from scp import user, bot
from pyrogram.types import (
    Message,
    CallbackQuery,
)
from scp.utils import format_bytes
import yt_dlp
import os


__PLUGIN__ = 'youtube'


_SEP_CHAR = "+-()-+"

# ffmpeg's args for hiding banner and errors
_FG_ARGS = "-hide_banner -loglevel error -y"
# the output file name template.
_OUT_TML = "%(title).200B.%(ext)s"
__cached_yt_media_infos = {}

@user.on_message(
    (user.sudo | user.owner | user.special_users) &
    user.command(
        ['yt', 'youtube', 'tiktok'],
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
    title = result.get("title", "Unknown Title")
    thumbnail = result.get("thumbnail", None)
    duration_string = result.get("duration_string", "00:00:00")
    view_count = result.get("view_count", 0)
    result["cut_from"] = "00:00.000"
    result["cut_to"] = "00:00.000"
    result["chat_id"] = message.chat.id
    result["message_id"] = message.id
    result["user_message"] = message
    
    __cached_yt_media_infos[media_id] = result

    txt = user.html_bold(f"💠 {result.get('extractor_key', 'Unknown')} media info\n")
    txt += user.html_bold("  Title: ") + user.html_link(title, result["webpage_url"]) + "\n"
    txt += user.html_bold("  Duration: ") + f" {duration_string}\n"
    txt += user.html_bold("  Views: ") + f" {view_count}\n"
    txt += user.html_normal("\nSelect a quality to download:")

    k_id = f"{_SEP_CHAR}{media_id}{_SEP_CHAR}"
    keyboard = [
        {"mp4 720p" : f"ytDl{k_id}720#$mp4", "Best" : f"ytDl{k_id}2500#$mp4", "Mp3" : f"ytDl{k_id}320#$mp3"},
    ]

    line_limit = 2
    if len(result["formats"]) >= 40:
        line_limit = 3
    
    current_sub_dict = {}
    for current_format in result["formats"]:
        if not isinstance(current_format, dict):
            continue

        video_ext: str = current_format.get("video_ext", None)
        if not video_ext or video_ext.lower() == 'none':
            continue
        
        the_size = current_format.get('filesize', None)
        if not the_size and len(result["formats"]) >= 25:
            continue

        
        btn_txt = f"{video_ext},{current_format['width']}"
        if the_size: btn_txt += f",{format_bytes(the_size)}"
        current_sub_dict[btn_txt] =  f"ytDl{k_id}{current_format['format_id']}#$key"

        if len(current_sub_dict) == line_limit:
            keyboard.append(current_sub_dict)
            current_sub_dict = {}

    try:
        if thumbnail:
            sent_message = await message.reply_photo(
                photo=thumbnail,
                caption=txt,
                reply_markup=keyboard,
            )
            result["sent_message"] = sent_message
            return
    except Exception as ex:
        print(f"failed to send photo: {ex}")

    # fallback to text
    await message.reply_text(
        text=txt,
        reply_markup=keyboard,
    )

@bot.on_callback_query(
    (user.sudo | user.owner | user.special_users) 
    & bot.filters.regex(f'^ytDl'),
)
async def _(_, query: CallbackQuery):
    query_data = query.data.split(_SEP_CHAR)
    if len(query_data) != 3:
        return await query.answer(
            "bad callback data",
            show_alert=True,
        )

    media_id = query_data[1]
    media_quality, media_format = query_data[2].split("#$")
    is_from_key = media_format == "key"

    media_info: dict = __cached_yt_media_infos.get(media_id, None)
    if not media_info:
        return await query.answer(
            "media info not found... please rerun the command",
            show_alert=True,
        )

    await query.answer(
        "Now downloading... please wait...",
        show_alert=True,
    )
    await query.edit_message_reply_markup(reply_markup=None)
    
    if media_format == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            "quiet": True,
            'noprogress': True,
            "outtmpl": _OUT_TML,
        }
    elif is_from_key:
        ydl_opts = {
            "format": media_quality,
            "quiet": True,
            'noprogress': True,
            "outtmpl": _OUT_TML,
        }
    else:
        ydl_opts = {
            "format": f"bestvideo[height<={media_quality}]+bestaudio/best[height<={media_quality}]",
            "quiet": True,
            'noprogress': True,
            "outtmpl": _OUT_TML,
        }
    
    the_info: dict = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # the info but this time has our desired format and stuff -_-
        the_info = ydl.extract_info(media_info["webpage_url"], download=False)
        file_name = ydl.prepare_filename(the_info)
        try:
            ydl.process_info(the_info)
        except Exception as err:
            txt = user.html_bold("Error at process_info: \n")
            txt += user.html_mono(f"{err}")
            return await user.send_message(
                text=txt,
                chat_id=media_info["chat_id"],
                reply_to_message_id=media_info["message_id"],
            )
    
    thumbnail = None
    if isinstance(media_info.get("sent_message", None), Message):
        thumbnail = getattr(media_info["sent_message"], "user_photo", None)
        if thumbnail:
            try:
                # we assume here that size of thumbnail is relatively small (<200kb)
                thumbnail = await user.download_media(thumbnail.file_id, in_memory=True)
            except: thumbnail = None

    if not os.path.exists(file_name) and os.path.exists(the_info['filepath']):
        # just switch over...
        file_name = the_info['filepath']
    
    # just get rid of the annoying ids in file name
    correct_file_name = file_name.replace(media_id, "").replace("[]", "").replace("()", "")
    correct_file_name = correct_file_name.replace("__", "").strip()
    os.rename(file_name, correct_file_name)
    file_name = correct_file_name

    if is_from_key:
        media_format = the_info.get("video_ext", None) or the_info.get("ext", "mp3")
    
    if not file_name.endswith(f".{media_format}"):
        try:
            correct_file_name = file_name.replace(file_name.split(".")[-1].strip(), media_format)
            # only mp3 requires re-encoding
            cp_arg = "-c copy" if media_format != "mp3" else ""
            if not os.path.exists(correct_file_name):
                await user.shell_base(
                    message=media_info["user_message"],
                    command=f"{user.ffmpeg_path} -i \"{file_name}\" {cp_arg} \"{correct_file_name}\" {_FG_ARGS}",
                    silent_on_success=True,
                    throw_on_error=True,
                )
            user.remove_file(file_name)
            file_name = correct_file_name
        except: pass # fallback to just sending original file
    
    if media_format == "mp3":
        await user.send_audio(
            chat_id=media_info["chat_id"],
            audio=file_name,
            caption=media_info["title"],
            reply_to_message_id=media_info["message_id"],
            duration=media_info["duration"],
            thumb=thumbnail,
        )
    else:
        await user.send_video(
            chat_id=media_info["chat_id"],
            video=file_name,
            caption=media_info["title"],
            reply_to_message_id=media_info["message_id"],
            duration=int(media_info["duration"]),
            thumb=thumbnail,
        )
    
    user.remove_file(file_name)
    del __cached_yt_media_infos[query_data[1]]