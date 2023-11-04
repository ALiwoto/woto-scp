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
from pyrogram.enums.parse_mode import ParseMode
from scp.utils import progress_callback
from scp import user
from scp.utils.parser import (
    contains_str,
    html_bold,
    html_mono,
)

@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	(user.owner | user.sudo ) &
	user.command(
        ['ls', 'hls', 'hiddenls'],
        prefixes=user.cmd_prefixes,
    ),
)
async def ls_handler(_, message: Message):
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
	user.owner & 
	user.command(
        ['pwd', 'dir'],
        prefixes=user.cmd_prefixes,
    ))
async def pwd_handler(_, message: Message):
    dir = os.path.abspath(os.path.expanduser(' '.join(message.command[1:]) or '.'))
    await message.reply_text(dir or 'Empty', disable_web_page_preview=True)



@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
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
    stdout = res[0].decode()
    output = (stdout + '\n\n' if stdout else '') + res[1].decode()
    await r.edit_text(html_mono(str(output)[:4000]), parse_mode=ParseMode.HTML)
    if output.count('Already up to date') > 0 and not is_forced:
        return
    elif not stdout:
        txt = html_bold('looks like something went wrong...\n')
        txt += "Make sure your git configurations are all correct and try again."
        return await user.send_message(chat_id=message.chat.id, text=txt)
    
    try:
        r = await user.send_message(chat_id=message.chat.id, text="Restarting...")
        await user.restart_scp()
    except Exception as e:
        await r.edit_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
        raise e


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	(user.owner | user.sudo) & 
	user.command(
        ['ul', 'upload', 'uld'],
        prefixes=user.cmd_prefixes,
    ),
)
async def upload_handler(_, message: Message):
    file = os.path.expanduser(' '.join(message.command[1:]))
    if not file:
        return
    
    should_delete = message.command[0].lower().endswith('d')
    text = f'Uploading {html_mono(file)}...'
    reply = await message.reply_text(text)
    if os.path.isdir(file):
        file_name = os.path.basename(file)
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
                else message.id
            ),
        )
        if should_delete:
            os.remove(file)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    except Exception as e:
        try:
            await reply.edit_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
            return
        except Exception: pass
        await message.reply_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
    else:
        await reply.delete()


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	(user.owner | user.sudo) & 
	user.command(
        ['ulv', 'upload_video', 'ulvd'],
        prefixes=user.cmd_prefixes,
    ),
)
async def upload_handler(_, message: Message):
    file = os.path.expanduser(' '.join(message.command[1:]))
    if not file:
        return
    
    should_delete = message.command[0].lower().endswith('d')
    text = f'Uploading {html_mono(file)}...'
    reply = await message.reply_text(text)
    if os.path.isdir(file):
        file_name = os.path.basename(file)
        shutil.make_archive(f"{file_name}-archive", 'zip', file)
        file = os.path.expanduser(f"{file_name}-archive.zip")
    
    try:
        await user.send_video(
            chat_id=message.chat.id, 
            video=file, 
            progress=progress_callback, 
            progress_args=(reply, text, True),
            reply_to_message_id=(
                None if message.chat.type in ('private', 'bot') 
                else message.id
            ),
        )
        if should_delete:
            os.remove(file)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Video upload cancelled!')
    except Exception as e:
        try:
            await reply.edit_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
            return
        except Exception: pass
        await message.reply_text(html_mono(str(e)[:4000]), parse_mode=ParseMode.HTML)
    else:
        await reply.delete()


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot &
	user.owner & 
	user.command(
        ['dl', 'download'],
        prefixes=user.cmd_prefixes,
    ),
)
async def download_handler(_, message: Message):
    download_message: Message = await user.get_message_to_download(message)
    if download_message is None:
        return await message.reply_text('Media required')
    
    non_cmd = user.get_non_cmd(message=message)
    target_args = non_cmd.split()
    if len(target_args) != 0:
        target_path = ''
        if len(target_args) > 1:
            if target_args[0].startswith('https://'):
                target_path = target_args[1]
            else:
                target_path = non_cmd
        else:
            target_path = target_args[0]

        file_path = os.path.abspath(os.path.expanduser(target_path))
    else:
        file_path = os.path.abspath(os.path.expanduser('./'))

    if os.path.isdir(file_path):
        file_path = os.path.join(file_path, '')
    
    text = 'Downloading...'
    reply = await message.reply_text(text)
    try:
        file_path = await download_message.download(file_path, progress=progress_callback, progress_args=(reply, text, False))
    except user.exceptions.MediaInvalid:
        await message.reply_text('Download cancelled!')
    else:
        await reply.edit_text(f'Downloaded to {html_mono(file_path)}')
