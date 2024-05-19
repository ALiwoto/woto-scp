from scp import user, __version__, bot, RUNTIME, __long_version__
import time
from scp.utils.parser import humanize_time
from pyrogram.types import (
    Message,
    CallbackQuery
)

@user.on_message(
    user.sudo & user.command('scp'),
)
async def _(_, message: Message):
    start = time.time()
    m = await user.send_message('me', '.')
    end = time.time()
    await m.delete()

    groups_query_result = user.db.execute(
        'SELECT COUNT(id) FROM peers WHERE type in ("group", "supergroup", "channel")',
    )
    users_query_result = user.db.execute(
        'SELECT COUNT(id) FROM peers WHERE type in ("user", "bot")',
    )

    TAB = "\t\t\t\t"
    text = user.html_bold("woto-scp\n")
    text += user.html_bold("\t\tversion: ")
    text += user.html_link(__version__,
                           f"https://github.com/ALiwoto/woto-scp/commit/{__long_version__}")
    text += user.html_bold(f"\n{TAB}dc_id: ") + user.html_mono(await user.storage.dc_id())
    text += user.html_bold(f"\n{TAB}ping_dc: ") + \
        user.html_mono(f'{round((end - start) * 1000, 3)}ms')
    text += user.html_bold(f"\n{TAB}peer_users: ") + \
        user.html_mono(f'{users_query_result[0][0]} users')
    text += user.html_bold(f"\n{TAB}peer_groups: ") + \
        user.html_mono(f'{groups_query_result[0][0]} groups')
    text += user.html_bold(f"\n{TAB}scp_uptime: ") + \
        user.html_mono(humanize_time(time.time() - RUNTIME))
    buttons = [
        {"Source": "https://github.com/aliwoto/woto-scp", "close": "close_message"},
    ]
    return await message.reply_text(
        text=text, 
        reply_markup=buttons,
        disable_web_page_preview=True,
    )


@bot.on_callback_query(
    bot.sudo
    & bot.filters.regex('^close_message'),
)
async def _(_, query: CallbackQuery):
    await query.message.delete()
