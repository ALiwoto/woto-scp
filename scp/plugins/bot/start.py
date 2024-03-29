from scp import bot, user, __version__, __long_version__

@bot.on_message(
    bot.sudo
    & bot.command('start', prefixes='/'),
)
async def _(_, message: bot.types.Message):
    try:
        me = await user.get_me()
    except ConnectionError:
        me = None
    userbot_stat = 'Stopped' if not me else 'Running'
    text = user.md.KanTeXDocument(
        user.md.Section(
            'woto-scp',
            user.md.KeyValueItem(
                user.md.Bold('Userbot Status'), user.md.Code(userbot_stat),
            ),
            user.md.KeyValueItem(
                user.md.Bold('Version'),
                user.md.Link(
                    __version__,
                    'https://github.com/pokurt/woto-scp/commit/{}'.format(
                        __long_version__,
                    ),
                ),
            ),
        ),
    )
    await message.reply(
        text,
        reply_markup=bot.types.InlineKeyboardMarkup(
            [[
                bot.types.InlineKeyboardButton(
                    'help', callback_data='help_back',
                ),
            ]],
        ),
        disable_web_page_preview=True,
    )
