# https://greentreesnakes.readthedocs.io/
# https://gitlab.com/blankX/sukuinote/-/blob/master/sukuinote/plugins/pyexec.py
import asyncio
import os
import html
import tempfile
from io import BytesIO
from . import progress_callback
from scp import user

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
async def shell(_, message: user.types.Message):
    if isinstance(message, user.types.Message):
        command = message.text.split(None, 1)[1]
        await shell_base(message, command)


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
async def neo_handler(_, message: user.types.Message):
    if not isinstance(message, user.types.Message):
        return
    
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
async def git_handler(_, message: user.types.Message):
    if not isinstance(message, user.types.Message):
        return
    
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
async def screen_handler(_, message: user.types.Message):
    if isinstance(message, user.types.Message):
        await shell_base(
            message, 
            "screen -ls" if message.text[1:].lower() == "screen" else message.text[1:],
        )

async def shell_base(message: user.types.Message, command: str):
    if not isinstance(message, user.types.Message):
        return
    
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
                caption=user.md.KanTeXDocument(sec),
                quote=True,
            ),
        )
    else:
        await reply.edit_text(doc)


@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & ~user.filters.edited
    & user.filters.me
    & user.filters.command(
        'git',
        prefixes=user.cmd_prefixes,
    ),
    )
async def cat(_, message: user.types.Message):
    if not isinstance(message, user.types.Message):
        return
    
    media = (message.text or message.caption).markdown.split(' ', 1)[1:]
    if media:
        media = os.path.expanduser(media[0])
    else:
        media = message.document
        if not media and not getattr(message.reply_to_message, 'empty', True):
            media = message.reply_to_message.document
        if not media:
            await message.reply_text('Document or local file path required')
            return
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
                chunk = f'<code>{html.escape(chunk)}</code>'
                if done:
                    await message.reply_text(chunk, quote=False)
                else:
                    await getattr(reply, 'edit_text', message.reply_text)(chunk)
                    done = True
    finally:
        if rfile:
            rfile.close()


