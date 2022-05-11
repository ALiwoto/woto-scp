# https://greentreesnakes.readthedocs.io/
# https://gitlab.com/blankX/sukuinote/-/blob/master/sukuinote/plugins/pyexec.py
import asyncio
import os
import tempfile
from io import BytesIO
from pyrogram.types import (
    Message,
)
from scp.utils import progress_callback
from scp import user
from scp.utils.parser import html_mono, split_some

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
    & ~user.filters.edited
    & user.filters.me
    & user.filters.command(
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
    & ~user.filters.edited
    & user.owner
    & user.filters.command(
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
    & ~user.filters.edited
    & user.filters.me
    & user.filters.command(
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
    & ~user.filters.edited
    & user.filters.me
    & user.filters.command(
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
    & ~user.filters.edited
    & user.filters.me
    & user.filters.command(
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
    & ~user.filters.edited
    & user.filters.me
    & user.filters.command(
        'curl',
        prefixes=user.cmd_prefixes,
    ),
)
async def curl_handler(_, message: Message):
    await shell_base(message, message.text[1:])

async def shell_base(message: Message, command: str):
    reply = await message.reply_text('Executing...', quote=True)
    process = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    stdout, _ = await process.communicate()
    returncode = process.returncode
    doc = user.md.KanTeXDocument()
    sec = user.md.Section(f'ExitCode: {returncode}')
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
                caption=f'ExitCode: {returncode}',
                quote=True,
            ),
        )
    else:
        await reply.edit_text(doc)

user.shell_base = shell_base

@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & ~user.filters.edited
    & user.owner
    & user.filters.command(
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
    & ~user.filters.edited
    & user.owner
    & user.filters.command(
        'toGif',
        prefixes=user.cmd_prefixes,
    ),
)
async def toGif_handler(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return
    sticker = message.reply_to_message.sticker
    if not sticker.is_video:
        await message.reply_text('the sticker needs to be a video-sticker')
        return
    
    rfile = tempfile.NamedTemporaryFile()
    reply = await message.reply_text('Downloading...')
    await user.download_media(
        media, 
        file_name=rfile.name,
        progress=progress_callback, 
        progress_args=(reply, 'Downloading...', False),
    )
    media = rfile.name
    output_to_gif = 'output-toGif.mp4'
    await shell_base(message, f'rm "{output_to_gif}" -f && ffmpeg -an -sn -i "{output_to_gif}" -c:v libx264 -crf 10 "{output_to_gif}" -hide_banner -loglevel error')
    
    file = os.path.expanduser(' '.join(output_to_gif))
    if not file:
        return
    text = f'Uploading {html_mono(file)}...'
    reply = await message.reply_text(text)
    
    try:
        await user.send_document(
            chat_id=message.chat.id, 
            document=file, 
            progress=progress_callback, 
            progress_args=(reply, text, True),
            reply_to_message_id=(
                None if message.chat.type in ('private', 'bot') 
                else message.message_id
            ),
        )
        os.remove(file)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    except Exception as e:
        try:
            await reply.edit_text(html_mono(str(e)[:4000]), parse_mode='html')
            return
        except Exception: pass
    else:
        await reply.delete()
    

