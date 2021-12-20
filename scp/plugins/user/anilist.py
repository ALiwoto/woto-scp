import html
from scp import user
from pyrogram import filters
from pyrogram.types import (
    Message,
)
from pyrogram.types.messages_and_media import Photo
from pyrogram.raw.types.messages.bot_results import (
    BotResults,
)
from pyrogram.errors.exceptions.forbidden_403 import Forbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatSendInlineForbidden

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
        text = {'message': results.results[page].send_message.message, 'entities': results.results[page].send_message.entities}
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
