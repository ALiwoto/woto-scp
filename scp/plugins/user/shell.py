# https://greentreesnakes.readthedocs.io/
# https://gitlab.com/blankX/sukuinote/-/blob/master/sukuinote/plugins/pyexec.py
import asyncio
import os
import tempfile
from io import BytesIO
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import (
    Message,
)
from scp.utils import progress_callback
from scp import user
from scp.utils.parser import html_mono, split_some
from shortuuid import ShortUUID

BACKUP_SHELL_SCRIPT = (
    "rm -r -f 'my-backup' &&"
    " mkdir 'my-backup' &&"
    " cp scp-bot.session my-backup/scp-bot.session &&"
    " cp scp-user.session my-backup/scp-user.session &&"
    " cp scp-user.session-journal my-backup/scp-user.session-journal &&"
    " cp config.ini my-backup/config.ini"
)

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'sBackup',
        prefixes=user.cmd_prefixes,
    ),
)
async def sBackup_handler(_, message: Message):
    try:
        await shell_base(message, BACKUP_SHELL_SCRIPT)
    except Exception as e:
        await message.reply_text(user.html_mono(e), quote=True)



@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        ['shell', 'sh'],
        prefixes=user.cmd_prefixes,
    ),
)
async def shell(_, message: Message):
    all_strs = split_some(message.text, 1, ' ', '\n')
    if len(all_strs) < 2:
        return
    
    await shell_base(message, all_strs[1])


@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'neo',
        prefixes=user.cmd_prefixes,
    ),
)
async def neo_handler(_, message: Message):
    await shell_base(message, "neofetch --stdout")



@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'git',
        prefixes=user.cmd_prefixes,
    ),
)
async def git_handler(_, message: Message):
    await shell_base(message, message.text[1:])

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'ffmpeg',
        prefixes=user.cmd_prefixes,
    ),
)
async def git_handler(_, message: Message):
    await shell_base(message, message.text[1:].replace('ffmpeg', user.ffmpeg_path, 1))

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'screen',
        prefixes=user.cmd_prefixes,
    ),
)
async def screen_handler(_, message: Message):
    await shell_base(
        message, 
        "screen -ls" if message.text[1:].lower() == "screen" else message.text[1:],
    )

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.filters.me
    & user.command(
        'curl',
        prefixes=user.cmd_prefixes,
    ),
)
async def curl_handler(_, message: Message):
    await shell_base(message, message.text[1:])

async def shell_base(
    message: Message = None, 
    command: str = None, 
    silent_on_success: bool = False,
    throw_on_error: bool = False,
    absolute_silent: bool = False
):
    reply = await message.reply_text('Executing...', quote=True) if not absolute_silent else None
    process = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    stdout, _ = await process.communicate()
    returnCode = process.returncode
    if throw_on_error and returnCode != 0:
        raise Exception(stdout.decode())
    elif absolute_silent:
        return returnCode, stdout
    
    doc = user.md.KanTeXDocument()
    sec = user.md.Section(f'ExitCode: {returnCode}')
    stdout = stdout.decode().replace('\r', '').strip('\n').rstrip()
    if stdout:
        sec.append(user.md.Code(stdout))
    doc.append(sec)
    if len(str(doc)) > 4096:
        f = BytesIO(stdout.encode('utf-8'))
        f.name = 'output.txt'
        await asyncio.gather(
            reply.delete(),
            message.reply_document(
                f,
                caption=f'ExitCode: {returnCode}',
                quote=True,
            ),
        )
    else:
        if silent_on_success and returnCode == 0:
            await reply.delete()
        else:
            await reply.edit_text(doc)

user.shell_base = shell_base

@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        'cat',
        prefixes=user.cmd_prefixes,
    ),
)
async def cat(_, message: Message):
    media = (message.text or message.caption).markdown.split(' ', 1)[1:]
    if media:
        media = os.path.expanduser(media[0])
    else:
        media = message.document
        if not media and not getattr(message.reply_to_message, 'empty', True):
            media = message.reply_to_message.document
        if not media:
            return await message.reply_text('Document or local file path required')
    done = False
    reply = rfile = None
    try:
        if not isinstance(media, str):
            rfile = tempfile.NamedTemporaryFile()
            reply = await message.reply_text('Downloading...')
            await user.download_media(
                media, 
                file_name=rfile.name,
                progress=progress_callback, 
                progress_args=(reply, 'Downloading...', False),
            )
            media = rfile.name
        with open(media, 'r') as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                if not chunk.strip():
                    continue
                if done:
                    await message.reply_text(html_mono(chunk), quote=False)
                else:
                    await getattr(reply, 'edit_text', message.reply_text)(html_mono(chunk))
                    done = True
    finally:
        if rfile:
            rfile.close()


@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & (user.owner | user.special_users)
    & user.command(
        'toGif',
        prefixes=user.cmd_prefixes,
    ),
)
async def toGif_handler(_, message: Message):
    replied_message = message.reply_to_message
    if replied_message == None or not replied_message.media:
        return await message.reply_text('Please reply to a media message with this command.')
    
    if not replied_message.media.name in ("VIDEO", "STICKER", "ANIMATION"):
        return await message.reply_text(f'Invalid media message detected: {replied_message.media.name}')
    
    sticker = message.reply_to_message.sticker
    if sticker and not sticker.is_video:
        return await message.reply_text('the sticker needs to be a video-sticker')
    
    rfile = tempfile.NamedTemporaryFile()
    await user.download_media(
        message=message.reply_to_message, 
        file_name=rfile.name,
    )
    output_to_gif = 'output-toGif.mp4'
    the_command = f'rm "{output_to_gif}" -f; ffmpeg -an -sn -i "{rfile.name}" -c:v libx264 -crf 10 "{output_to_gif}" -hide_banner -loglevel error'
    await shell_base(message, the_command, silent_on_success=True)
    
    # text = f'Uploading {html_mono(output_to_gif)}...'
    # reply = await message.reply_text(text)
    rfile.close()
    
    try:
        await user.send_document(
            chat_id=message.chat.id, 
            document=output_to_gif, 
            # progress=progress_callback, 
            # progress_args=(reply, text, True),
            reply_to_message_id=(
                None if message.chat.type in ('private', 'bot') 
                else message.id
            ),
        )
        os.remove(output_to_gif)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    except Exception as e:
        try:
            await message.reply_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
            return
        except Exception: pass
    

@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.sudo
    & user.command(
        'makeGif',
        prefixes=user.cmd_prefixes,
    ),
)
async def makeGif_handler(_, message: Message):
    # command format is:
    # .makeGif FILE_NAME 22:45.0 -> 22:49.0
    my_strs = user.split_timestamped_message(message)
    if not my_strs or len(my_strs) < 4:
        txt = user.html_bold('Usage:\n\t')
        txt += user.html_mono('.makeGif FILE_NAME 22:45.0 -> 22:49.0')
        return await message.reply_text(txt)
    
    user_file_name = os.path.abspath(os.path.expanduser(my_strs[1]))
    start_t = my_strs[2]
    end_t = my_strs[3]
    if not os.path.exists(user_file_name):
        # download the file to the destination
        if not message.reply_to_message:
            return await message.reply_text(f'reply to a file to download it to {user_file_name}')
        reply = await message.reply_text('Downloading...')
        await user.download_media(
            message.reply_to_message, 
            file_name=user_file_name,
            progress=progress_callback, 
            progress_args=(reply, 'Downloading...', False),
        )
        await reply.delete()
    
    
    outfile = 'aliwoto-output-cutGif.mp4'
    sh_txt = f'rm "{outfile}" -f'
    scale_value = "scale='min(iw,1280)':'min(ih,720)'"
    times_value = f'-ss {start_t} -to {end_t}'
    sh_txt += f' ; {user.ffmpeg_path} -sn -hide_banner -loglevel error -an {times_value} -i "{user_file_name}"'
    sh_txt += f' -vf "{scale_value}" -pix_fmt yuv420p -c:v libx264 "{outfile}" '
    await shell_base(message, sh_txt)
    
    text = f'Uploading {html_mono(outfile)}...'
    reply = await message.reply_text(text)
    
    try:
        await user.send_animation(
            chat_id=message.chat.id, 
            animation=outfile, 
            progress=progress_callback, 
            progress_args=(reply, text, True),
            reply_to_message_id=(
                None if message.chat.type in ('private', 'bot') 
                else message.id
            ),
        )
        os.remove(outfile)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    except Exception as e:
        try:
            await reply.edit_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
            return
        except Exception: pass
    else:
        await reply.delete()
    

@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.sudo
    & user.command(
        'makeVid',
        prefixes=user.cmd_prefixes,
    ),
)
async def makeVid_handler(_, message: Message):
    # command format is:
    # .makeVid FILE_NAME 22:45.0 -> 22:49.0
    my_strs = user.split_timestamped_message(message)
    if not my_strs or len(my_strs) < 4:
        txt = user.html_bold('Usage:\n\t')
        txt += user.html_mono('.makeVid FILE_NAME 22:45.0 -> 22:49.0')
        return await message.reply_text(txt)
    
    user_file_name = os.path.abspath(os.path.expanduser(my_strs[1]))
    start_t = my_strs[2]
    end_t = my_strs[3]
    if not os.path.exists(user_file_name):
        # download the file to the destination
        if not message.reply_to_message:
            return await message.reply_text(f'reply to a file to download it to {user_file_name}')
        reply = await message.reply_text('Downloading...')
        await user.download_media(
            message.reply_to_message, 
            file_name=user_file_name,
            progress=progress_callback, 
            progress_args=(reply, 'Downloading...', False),
        )
        await reply.delete()
    
    
    outfile = 'aliwoto-output-cutVid.mp4'
    sh_txt = f'rm "{outfile}" -f'
    scale_value = "scale='min(iw,1280)':'min(ih,720)'"
    times_value = f'-ss {start_t} -to {end_t}'
    sh_txt += f' ; {user.ffmpeg_path} -sn -hide_banner -loglevel error {times_value} -i "{user_file_name}"'
    sh_txt += f' -vf "{scale_value}" -pix_fmt yuv420p -c:v libx264 "{outfile}" '
    await shell_base(message, sh_txt)
    
    text = f'Uploading {html_mono(outfile)}...'
    reply = await message.reply_text(text)
    
    try:
        await user.send_video(
            chat_id=message.chat.id, 
            video=outfile, 
            progress=progress_callback, 
            progress_args=(reply, text, True),
            reply_to_message_id=(
                None if message.chat.type in ('private', 'bot') 
                else message.id
            ),
        )
        os.remove(outfile)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    except Exception as e:
        try:
            await reply.edit_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
            return
        except Exception: pass
    else:
        await reply.delete()
    

@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.sudo
    & user.command(
        'postStory',
        prefixes=user.cmd_prefixes,
    ),
)
async def postStory_handler(_, message: Message):
    no_scale = message.text.find('--no-scale') != -1
    if no_scale:
        message.text = message.text.replace('--no-scale', '').strip()
    
    is_everyone = message.text.find('--everyone') != -1
    if is_everyone:
        message.text = message.text.replace('--everyone', '').strip()
    
    # command format is:
    # .makeVid postStory 22:45.0 -> 22:49.0
    my_strs = user.split_timestamped_message(message)
    start_t: str = None
    end_t: str = None
    if not my_strs:
        txt = user.html_bold('Usage:\n\t')
        txt += user.html_mono('.makeVid FILE_NAME [00:01.0 -> 01:00.0] [--no-scale] [--everyone]')
        return await message.reply_text(txt)
    elif len(my_strs) == 2:
        pass
    elif len(my_strs) == 4:
        start_t = my_strs[2]
        end_t = my_strs[3]
    else:
        return await message.reply_text('Invalid command format!')
    
    user_file_name = os.path.abspath(os.path.expanduser(my_strs[1]))
    if not os.path.exists(user_file_name):
        # download the file to the destination
        if not message.reply_to_message:
            return await message.reply_text(f'reply to a file to download it to {user_file_name}')
        reply = await message.reply_text('Downloading...')
        await user.download_media(
            message.reply_to_message, 
            file_name=user_file_name,
            progress=progress_callback, 
            progress_args=(reply, 'Downloading...', False),
        )
        await reply.delete()

    outfile = f'aliwoto-output-cutVid{ShortUUID().random(length=8)}.mp4'
    sh_txt = f'rm "{outfile}" -f'
    times_value = f'-ss {start_t} -to {end_t}' if start_t and end_t else ''
    sh_txt += f' ; {user.ffmpeg_path} -sn -hide_banner -loglevel error {times_value} -i "{user_file_name}"'
    sh_txt += f' -c:v copy -crf 22 "{outfile}" '
    
    await shell_base(message, sh_txt, throw_on_error=True, absolute_silent=True)

    input_file = outfile
    output_file = f'output{ShortUUID().random(length=8)}.mp4'
    vf_value = "-vf 'split[original][copy];[copy]scale=-1:ih*(16/9)*(16/9),crop=w=ih*9/16,\
        gblur=sigma=20[blurred];[blurred][original]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2'"
    sh_txt = f"ffmpeg -i {input_file} {vf_value} -c:v libx265 -crf 22 {output_file} -hide_banner -loglevel error -y"
    await shell_base(message, sh_txt, throw_on_error=True)

    user.remove_file(input_file)
    input_file = output_file
    scale_value = "-vf \"scale='min(iw,720)':'min(ih,1280)'\"" if not no_scale else ''
    output_file = f'output{ShortUUID().random(length=8)}.mp4'
    sh_txt = f"ffmpeg -i ok.mp4 {scale_value} -c:v libx265 -crf 22 {output_file} -hide_banner -loglevel error -y"
    await shell_base(message, sh_txt, throw_on_error=True)

    try:
        await user.send_story(output_file, privacy='all' if is_everyone else 'friends')
    except Exception as e:
        await user.reply_exception(message, e)
    
    user.remove_file(input_file)
    user.remove_file(output_file)

