import os
import re
from scp.utils.selfInfo import info
from scp import bot
from scp.utils.auto_inline import AutoInlineType, auto_inline_dict
from pyrogram import utils as pUtils
from pyrogram.file_id import FileType
from pyrogram.types import InlineQuery


@bot.on_inline_query(
    bot.filters.user(bot.the_user.me.id)
    & bot.filters.regex('^auIn'),
)
async def answer_auto_inline_query(__, query: InlineQuery):
    query_text = query.query
    container = auto_inline_dict.get(query_text, None)
    if not container: return
    else: auto_inline_dict.pop(query_text, None)
    answers = []
    
    if not container.title:
        container.title = "Kaizoku"
    
    # answer the userbot's inline query here...
    if container.inline_message_type == AutoInlineType.TEXT:
        answers.append(
            bot.types.InlineQueryResultArticle(
                title=container.title,
                input_message_content=bot.types.InputTextMessageContent(
                    container.text,
                    disable_web_page_preview=container.disable_web_page_preview,
                    entities=container.entities,
                ),
                reply_markup=container.keyboard,
            ),
        )
        return await query.answer(
            results=answers,
            cache_time=container.cache_time,
            is_gallery=container.is_gallery,
            is_personal=container.is_personal,
            next_offset=container.next_offset,
            switch_pm_text=container.switch_pm_text,
            switch_pm_parameter=container.switch_pm_parameter
        )
    elif container.inline_message_type == AutoInlineType.PHOTO:
        shared_message = await bot.get_messages(
            chat_id=container.media_chat_id,
            message_ids=container.media_message_id
        )
        
        answers.append(
            bot.types.InlineQueryResultCachedPhoto(
                photo_file_id=shared_message.photo.file_id,
                title=container.title,
                caption=container.text,
                reply_markup=container.keyboard,
            ),
        )
        return await query.answer(
            results=answers,
            cache_time=container.cache_time,
            is_gallery=container.is_gallery,
            is_personal=container.is_personal,
            next_offset=container.next_offset,
            switch_pm_text=container.switch_pm_text,
            switch_pm_parameter=container.switch_pm_parameter
        )
    
        
