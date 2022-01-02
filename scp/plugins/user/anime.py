import os
import asyncio
import datetime
import tempfile
from scp import user
from pyrogram.types import (
    Message,
    Sticker,
)
from scp.utils import progress_callback
from pyrogram.types.messages_and_media import Photo
from pyrogram.raw.types.messages.bot_results import (
    BotResults,
)
from pyrogram.errors.exceptions.forbidden_403 import Forbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatSendInlineForbidden

from decimal import Decimal
from pyrogram.types import Sticker

@user.on_message(
    ~user.filters.scheduled & 
    ~user.filters.forwarded & 
    ~user.filters.sticker & 
    ~user.filters.via_bot & 
    ~user.filters.edited & 
    user.sudo & 
    user.filters.command(
        ['anilist', 'al', 'alc', 'alchar', 'alcharacter', 'anilistc', 'anilistchar', 'anilistcharacter'], 
        prefixes=user.cmd_prefixes,
    )
)
async def anilist(_, message: Message):
    bot = await user.the_bot.get_me()
    query = message.command
    page = 1
    character = 'c' in query.pop(0)
    if len(query) > 1 and query[0].isnumeric():
        page = int(query.pop(0))
    page -= 1
    if page < 0:
        page = 0
    elif page > 9:
        page = 9
    query = ' '.join(query)
    if not query:
        return
    results: BotResults = await user.get_inline_bot_results(
        bot.username or bot.id, 
        f'al{"c" if character else ""} ' + query,
    )
    if not results.results:
        await message.reply_text('No results')
        return
    try:
        await message.reply_inline_bot_result(results.query_id, results.results[page].id)
    except IndexError:
        await message.reply_text(f'There are only {len(results.results)} results')
    except (Forbidden, ChatSendInlineForbidden):
        text = {
            'message': results.results[page].send_message.message, 
            'entities': results.results[page].send_message.entities,
        }
        photo = url = None
        if getattr(results.results[page], 'photo', None) is not None:
            photo = Photo._parse(user, results.results[page].photo)
        else:
            url = results.results[page].content.url
        try:
            if photo is not None:
                await message.reply_cached_media(photo.file_id, caption=text, parse_mode='through')
            else:
                await message.reply_photo(url, caption=text, parse_mode='through')
        except Forbidden:
            await message.reply_text(text, disable_web_page_preview=True, parse_mode='through')


@user.on_message(
    ~user.filters.scheduled & 
	~user.filters.forwarded & 
	~user.filters.sticker & 
	~user.filters.via_bot & 
	~user.filters.edited & 
	user.owner & 
	user.filters.command(
        ['trace', 'tracemoe', 'whatanime', 'wa', 'wait'],
        prefixes=user.cmd_prefixes,
    ),
)
async def whatanime(_, message: Message):
    media = (
        message.photo or
        message.animation or 
        message.video or 
        message.sticker or 
        message.document
    )
    if not media:
        reply = message.reply_to_message
        if not getattr(reply, 'empty', True):
            media = reply.photo or reply.animation or reply.video or reply.sticker or reply.document
    if not media:
        await message.reply_text('Photo or GIF or Video or Sticker required')
        return
    if isinstance(media, Sticker) and media.is_animated:
        await message.reply_text('No animated stickers')
        return
    with tempfile.TemporaryDirectory() as tempdir:
        reply = await message.reply_text('Downloading...')
        path = await user.download_media(
            media, 
            file_name=os.path.join(tempdir, '0'), 
            progress=progress_callback, 
            progress_args=(reply, 'Downloading...', False),
        )
        new_path = os.path.join(tempdir, '1.png')
        proc = await asyncio.create_subprocess_exec(
            'ffmpeg', 
            '-hide_banner', 
            '-loglevel', 'error', 
            '-i', path, 
            '-frames:v', '1', 
            new_path,
        )
        await proc.communicate()
        await reply.edit_text('Uploading...')
        with open(new_path, 'rb') as file:
            async with user.aioclient.post('https://api.trace.moe/search?cutBorders&anilistInfo', data={'image': file}) as resp:
                json = await resp.json(content_type=None)
    if json.get('error'):
        await reply.edit_text(json['error'], parse_mode=None)
    else:
        try:
            match = json['result'][0]
        except IndexError:
            await reply.edit_text('No match')
        else:
            nsfw = match['anilist']['isAdult']
            title_native = match['anilist']['title']['native']
            title_english = match['anilist']['title']['english']
            title_romaji = match['anilist']['title']['romaji']
            synonyms = ', '.join(match['anilist']['synonyms'])
            anilist_id = match['anilist']['id']
            episode = match['episode']
            similarity = match['similarity']
            from_time = str(datetime.timedelta(seconds=match['from'])).split('.', 1)[0].rjust(8, '0')
            to_time = str(datetime.timedelta(seconds=match['to'])).split('.', 1)[0].rjust(8, '0')
            text = f'<a href="https://anilist.co/anime/{anilist_id}">{title_romaji}</a>'
            if title_english:
                text += f' ({title_english})'
            if title_native:
                text += f' ({title_native})'
            if synonyms:
                text += f'\n<b>Synonyms:</b> {synonyms}'
            text += f'\n<b>Similarity:</b> {(Decimal(similarity) * 100).quantize(Decimal(".01"))}%\n'
            if episode:
                text += f'<b>Episode:</b> {episode}\n'
            if nsfw:
                text += '<b>Hentai/NSFW:</b> Yes'
            async def _send_preview():
                with tempfile.NamedTemporaryFile() as file:
                    async with user.aioclient.get(match['video']) as resp:
                        while True:
                            chunk = await resp.content.read(4096)
                            if not chunk:
                                break
                            file.write(chunk)
                    file.seek(0)
                    try:
                        await reply.reply_video(file.name, caption=f'{from_time} - {to_time}')
                    except BaseException:
                        await reply.reply_text('Cannot send preview :/')
            await asyncio.gather(reply.edit_text(text, disable_web_page_preview=True), _send_preview())

