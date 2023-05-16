
import logging
import os
import html
import logging
from pyrogram.types import (
    Message,
)
from pyrogram.enums.parse_mode import ParseMode
from scp.utils import progress_callback
from scp import user

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

g_auth: GoogleAuth = None
g_drive: GoogleDrive = None

try:
    g_auth: GoogleAuth = GoogleAuth(settings_file='gdrive_settings.yaml')
    g_drive: GoogleDrive = GoogleDrive(g_auth)
    user.g_auth = g_auth
    user.g_drive = g_drive
except: logging.warn('failed to load gdrive.')

@user.on_message(
    ~user.filters.scheduled &
    ~user.filters.forwarded &
    ~user.filters.sticker &
    ~user.filters.via_bot &
    user.owner &
    user.command(
        ['gul', 'gUpload'],
        prefixes=user.cmd_prefixes,
    ),
)
async def gUpload_handler(_, message: Message):
    original_message = message

    download_message = await user.get_message_to_download(message)
    if not download_message:
        return await message.reply_text('Media required')
    elif download_message.empty:
        top_message = await message.reply_text(
            'Required message is empty, searching for the correct one...'
        )
        download_message = await user.get_message_to_download(original_message, True)
        if not download_message or message.empty:
            return await top_message.edit_text('message iteration ended.')
        
        await top_message.edit_text('Next message found! \n' + user.html_mono(download_message.link))

    file_path = os.path.abspath(os.path.expanduser(' '.join(message.command[1:]) or './'))
    if os.path.isdir(file_path):
        file_path = os.path.join(file_path, '')

    text = 'Downloading...'
    reply = await message.reply_text(text)
    try:
        file_path = await download_message.download(file_path, progress=progress_callback, progress_args=(reply, text, False))
    except user.exceptions.MediaInvalid:
        return await message.reply_text('Download cancelled!')
    
    g_drive = getattr(user, 'g_drive', None)
    if not isinstance(g_drive, GoogleDrive):
        try:
            g_auth: GoogleAuth = GoogleAuth(settings_file='gdrive_settings.yaml')
            g_drive: GoogleDrive = GoogleDrive(g_auth)
            user.g_auth = g_auth
            user.g_drive = g_drive
        except Exception as e: 
            return await user.reply_exception(original_message, e=e)
    
    file_metadata = {
        'title': os.path.basename(file_path)
    }
    if user.scp_config.gdrive_upload_folder_id:
        file_metadata['parents'] = [{'id': user.scp_config.gdrive_upload_folder_id}]
    
    try:
        g_file = g_drive.CreateFile(file_metadata)
        # Read file and set it as the content of this instance.
        g_file.SetContentFile(file_path)
        g_file.Upload()  # Upload the file.
    except Exception as e:
        return await user.reply_exception(original_message, e=e)
    
    await reply.edit_text(f'File is ready to download.\n' + user.html_mono(html.escape(g_file['webContentLink'])))
