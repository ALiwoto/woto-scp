from scp import user
from scp.utils.similarWords import get_similar_words_async
from scp.utils.mdparser import escapeAny
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import (
    Message,
)


__PLUGIN__ = 'UrbanDictionary'
__DOC__ = str(
    user.md.KanTeXDocument(
        user.md.Section(
            'UrbanDictionary Definitions',
            user.md.SubSection(
                'Urban',
                user.md.Code('(*prefix)ud {query}'),
            ),
        ),
    ),
)


def replace_text(text: str):
    return text.replace(
        '"', '',
    ).replace(
        '\\r', '',
    ).replace(
        '\\n', '',
    ).replace(
        '\\', '',
    )

def is_undefined(response) -> bool:
    return ((not response) or (not response['list']) or (len(response['list']) == 0)
        or (len(response['list'][0]) == 0) or 
        (len(response['list'][0]['word']) == 0) or 
        (len(response['list'][0]['definition']) == 0))


@user.on_message(
    (user.sudo | user.owner) & 
    user.command('ud'))
async def ud_handler(_, message: Message):
    text = ""
    if len(message.text.split()) <= 1:
        if not message.reply_to_message:
            return
        else:
            text = message.reply_to_message.text
    else:
        text = message.text.split(None, 1)[1]
    response = await user.Request(
        f'http://api.urbandictionary.com/v0/define?term={text}',
        type='get',
    )
    if is_undefined(response):
        similarities = await get_similar_words_async(text)
        if (not similarities) or (len(similarities) == 0):
            text = escapeAny(f'No definition found for "{text}"...')
        else:
            text = escapeAny(f'No definition found for "{text}"...\n'+
                '✧ but here are some similarities:')
            num = 0
            for similar in similarities:
                num += 1
                text += escapeAny(f'\n{num}- ') + '__' + escapeAny(similar) + '__ '
        return await message.reply_text(text, parse_mode=ParseMode.HTML)
    else:    
        text = user.md.KanTeXDocument(
            user.md.Section(
                'UrbanDictionary',
                user.md.SubSection(
                    'Text:',
                    user.md.Italic(replace_text(response['list'][0]['word'])),
                ),
                user.md.SubSection(
                    'Meaning:',
                    user.md.Italic(
                        replace_text(
                            response['list'][0]['definition'],
                        ),
                    ),
                ),
                user.md.SubSection(
                    'Example:',
                    user.md.Italic(replace_text(response['list'][0]['example'])),
                ),
            ),
        )
    await message.reply_text(text, quote=True)
