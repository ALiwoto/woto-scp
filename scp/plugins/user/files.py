import asyncio
import logging
import os
import html
import sys
import shutil
import traceback
from pyrogram.types import (
    Message,
)
from scp.utils import progress_callback
from scp import user
from scp.utils.parser import (
    contains_str,
    html_mono,
)

@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['ls', 'hls', 'hiddenls'],
        prefixes=user.cmd_prefixes,
    ),
)
async def ls(_, message: Message):
    dir = os.path.abspath(os.path.expanduser(' '.join(message.command[1:]) or '.'))
    text = ''
    folders = []
    files = []
    try:
        for i in sorted(os.listdir(dir)):
            if i.startswith('.') and 'h' not in message.command[0]:
                continue
            (folders if os.path.isdir(os.path.join(dir, i)) else files).append(i)
    except NotADirectoryError:
        text = html_mono(html.escape(os.path.basename(dir)))
    except BaseException as ex:
        text = f'{type(ex).__name__}: {html.escape(str(ex))}'
    else:
        for i in folders:
            text += f'<code>{html.escape(i)}</code>\n'
        for i in files:
            text += f'<code>{html.escape(i)}</code>\n'
    await message.reply_text(text or 'Empty', disable_web_page_preview=True)



@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['pwd', 'dir'],
        prefixes=user.cmd_prefixes,
    ))
async def pwd(_, message: Message):
    dir = os.path.abspath(os.path.expanduser(' '.join(message.command[1:]) or '.'))
    await message.reply_text(dir or 'Empty', disable_web_page_preview=True)



@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['gitpull', 'restart'],
        prefixes=user.cmd_prefixes,
    ),
)
async def gitpull(_, message: Message):
    command = "git pull"
    r = await message.reply_text("Trying to pull changes")
    process = await asyncio.create_subprocess_shell(
                command, 
                stdin=asyncio.subprocess.PIPE if sys.stdin else None,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
    
    is_forced = contains_str(message.text, 'restart', 'force')
    res = await process.communicate()
    output = res[0].decode()
    await r.edit_text(html_mono(str(output)[:4000]), parse_mode='html')
    if output.count('Already up to date') > 0 and not is_forced:
        return
    
    try:
        r = await user.send_message(chat_id=message.chat.id, text="Restarting...")
        await user.restart_scp()
    except Exception as e:
        await r.edit(html_mono(str(e)[:4000]), parse_mode='html')
        raise e


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['ul', 'upload'],
        prefixes=user.cmd_prefixes,
    ),
)
async def upload_handler(_, message: Message):
    file = os.path.expanduser(' '.join(message.command[1:]))
    if not file:
        return
    text = f'Uploading {html_mono(file)}...'
    reply = await message.reply_text(text)
    file_name = os.path.basename(file)
    if os.path.isdir(file):
        shutil.make_archive(f"{file_name}-archive", 'zip', file)
        file = os.path.expanduser(f"{file_name}-archive.zip")
    
    try:
        await user.send_document(
            chat_id=message.chat.id, 
            document=file, 
            progress=progress_callback, 
            progress_args=(reply, text, True), 
            force_document=True, 
            reply_to_message_id=(
                None if message.chat.type in ('private', 'bot') 
                else message.message_id,
            ),
        )
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    except Exception as e:
        try:
            await reply.reply_text(html_mono(traceback.format_exc() +"\n file type is:" + str(type(file))))
            await reply.edit_text(html_mono(str(e)[:4000]), parse_mode='html')
            return
        except Exception: pass
        await message.reply_text(html_mono(str(e)[:4000]), parse_mode='html')
    else:
        await reply.delete()


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['dl', 'download'],
        prefixes=user.cmd_prefixes,
    ),
)
async def download(_, message: Message):
    file = os.path.abspath(os.path.expanduser(' '.join(message.command[1:]) or './'))
    if os.path.isdir(file):
        file = os.path.join(file, '')
    available_media = ("audio", "document", "photo", "sticker", "animation", "video", "voice", "video_note")
    download_message = None
    for i in available_media:
        if getattr(message, i, None):
            download_message = message
            break
    else:
        reply = message.reply_to_message
        if not getattr(reply, 'empty', True):
            for i in available_media:
                if getattr(reply, i, None):
                    download_message = reply
                    break
    if download_message is None:
        await message.reply_text('Media required')
        return
    text = 'Downloading...'
    reply = await message.reply_text(text)
    try:
        file = await download_message.download(file, progress=progress_callback, progress_args=(reply, text, False))
    except user.exceptions.MediaInvalid:
        await message.reply_text('Download cancelled!')
    else:
        await reply.edit_text(f'Downloaded to {html.escape(file)}')






