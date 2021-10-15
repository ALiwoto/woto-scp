from scp import user
from scp.plugins.user.similarwords import get_similar_words_async
from scp.utils.mdparser import escapeAny


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
        or (len(response['list'][0] == 0)) or 
        (len(response['list'][0]['word'] == 0)) or 
        (len(response['list'][0]['definition'] == 0)))


@user.on_message(
    (user.sudo | user.owner) & 
    user.command('ud'))
async def _(_, message: user.types.Message):
    if len(message.text.split()) == 1:
        return await message.delete()
    text = message.text.split(None, 1)[1]
    response = await user.Request(
        f'http://api.urbandictionary.com/v0/define?term={text}',
        type='get',
    )
    text = ""
    if is_undefined(response):
        similars = await get_similar_words_async(text)
        if (not similars) or (len(similars) == 0):
            text = escapeAny(f'No definition found for "{text}"...')
        else:
            text = escapeAny(f'No definition found for "{text}"...\n'+
                'but here are some similarities:')
            num = 0
            for similar in similars:
                num += 1
                text += escapeAny(f'\n{num}- {similar}')
        return await message.reply(text, parse_mode="MarkdownV2")
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
    await message.reply(text, quote=True)
