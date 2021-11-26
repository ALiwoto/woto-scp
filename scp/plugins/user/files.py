import asyncio
import os
import html
import sys
import time
import shutil
from datetime import timedelta
from scp import user

@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['ls', 'hls', 'hiddenls'],
        prefixes=user._config.get('scp-5170', 'prefixes').split(),
    ))
async def ls(_, message: user.types.Message):
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
        text = f'<code>{html.escape(os.path.basename(dir))}</code>'
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
        prefixes=user._config.get('scp-5170', 'prefixes').split(),
    ))
async def pwd(_, message: user.types.Message):
    dir = os.path.abspath(os.path.expanduser(' '.join(message.command[1:]) or '.'))
    await message.reply_text(dir or 'Empty', disable_web_page_preview=True)



@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command('gitpull',
        prefixes=user._config.get('scp-5170', 'prefixes').split(),
    ))
async def gitpull(_, message: user.types.Message):
    command = "git pull"
    r = await message.reply("Trying to pull changes")
    process = await asyncio.create_subprocess_shell(command, 
                stdin=asyncio.subprocess.PIPE if sys.stdin else None,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                
    res = await process.communicate()
    output = res[0].decode()
    await r.edit("<code>" + html.escape(str(output)[:4000]) + "</code>", parse_mode='html')

    try:
        r = await user.send_message(chat_id=message.chat.id, text="Restarting")
        await user.stop(block=False)

        os.execv("run.sh", sys.argv)

    except Exception as e:
        await r.edit("<code>" + html.escape(str(e)[:4000]) + "</code>", parse_mode='html')



@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['ul', 'upload'],
        prefixes=user._config.get('scp-5170', 'prefixes').split(),
    ))
async def upload(_, message: user.types.Message):
    file = os.path.expanduser(' '.join(message.command[1:]))
    if not file:
        return
    text = f'Uploading {html.escape(file)}...'
    reply = await message.reply_text(text)
    file_name = os.path.basename(file)
    if os.path.isdir(file):
        shutil.make_archive(f"{file_name}-archive", 'zip', file)
        file = os.path.expanduser(f"{file_name}-archive.zip")
    
    try:
        await user.send_document(message.chat.id, file, 
            progress=progress_callback, progress_args=(reply, text, True), force_document=True, reply_to_message_id=None if message.chat.type in ('private', 'bot') else message.message_id)
    except user.exceptions.MediaInvalid:
        await message.reply_text('Upload cancelled!')
    else:
        await reply.delete()


@user.on_message(~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['dl', 'download'],
        prefixes=user._config.get('scp-5170', 'prefixes').split(),
    ))
async def download(_, message: user.types.Message):
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



progress_callback_data = dict()
async def progress_callback(current, total, reply, text, upload):
    message_identifier = (reply.chat.id, reply.message_id)
    last_edit_time, prevtext, start_time = progress_callback_data.get(message_identifier, (0, None, time.time()))
    if current == total:
        try:
            progress_callback_data.pop(message_identifier)
        except KeyError:
            pass
    elif (time.time() - last_edit_time) > 1:
        handle = 'Upload' if upload else 'Download'
        if last_edit_time:
            speed = format_bytes((total - current) / (time.time() - start_time))
        else:
            speed = '0 B'
        text = f'''{text}
<code>{return_progress_string(current, total)}</code>

<b>Total Size:</b> {format_bytes(total)}
<b>{handle}ed Size:</b> {format_bytes(current)}
<b>{handle} Speed:</b> {speed}/s
<b>ETA:</b> {calculate_eta(current, total, start_time)}'''
        if prevtext != text:
            await reply.edit_text(text)
            prevtext = text
            last_edit_time = time.time()
            progress_callback_data[message_identifier] = last_edit_time, prevtext, start_time


# https://stackoverflow.com/a/34325723
def return_progress_string(current, total):
    filled_length = int(30 * current // total)
    return '[' + '=' * filled_length + ' ' * (30 - filled_length) + ']'


# https://stackoverflow.com/a/852718
# https://stackoverflow.com/a/775095
def calculate_eta(current, total, start_time):
    if not current:
        return '00:00:00'
    end_time = time.time()
    elapsed_time = end_time - start_time
    seconds = (elapsed_time * (total / current)) - elapsed_time
    thing = ''.join(str(timedelta(seconds=seconds)).split('.')[:-1]).split(', ')
    thing[-1] = thing[-1].rjust(8, '0')
    return ', '.join(thing)



# https://stackoverflow.com/a/49361727
def format_bytes(size):
    size = int(size)
    # 2**10 = 1024
    power = 1024
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]+'B'}"






