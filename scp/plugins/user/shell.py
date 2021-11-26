# https://greentreesnakes.readthedocs.io/
# https://gitlab.com/blankX/sukuinote/-/blob/master/sukuinote/plugins/pyexec.py
import asyncio
from io import BytesIO
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
async def shell(_, message: user.types.Message):
    await shell_base(message, "neofetch --stdout")




async def shell_base(message: user.types.Message, command: str):
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




