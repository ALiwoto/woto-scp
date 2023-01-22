from scp import user, __version__, bot, RUNTIME, __long_version__
import time
from scp.utils.parser import humanize_time

@user.on_message(
    user.sudo & user.command('scp'),
)
async def _(_, message: user.types.Message):
    start = time.time()
    m = await user.send_message('me', '.')
    end = time.time()
    await m.delete()
    with user.storage.lock, user.storage.conn:
        groups_query_result = user.storage.conn.execute(
            'SELECT COUNT(id) FROM peers WHERE type in ("group", "supergroup", "channel")',
        ).fetchall()
        users_query_result = user.storage.conn.execute(
            'SELECT COUNT(id) FROM peers WHERE type in ("user", "bot")',
        ).fetchall()

    text = user.html_bold("woto-scp\n")
    text += user.html_bold("\t\tversion: ")
    text += user.html_link(__version__,
                           f"https://github.com/ALiwoto/woto-scp/commit/{__long_version__}")
    text += user.html_bold("\t\t\t\tdc_id: ") + user.html_mono(await user.storage.dc_id())
    text += user.html_bold("\t\t\t\tping_dc: ") + \
        user.html_mono(f'{round((end - start) * 1000, 3)}ms')
    text += user.html_bold("\t\t\t\tpeer_users: ") + \
        user.html_mono(f'{len(users_query_result[0][0])} users')
    text += user.html_bold("\t\t\t\tpeer_groups: ") + \
        user.html_mono(f'{len(groups_query_result)} groups')
    text += user.html_bold("\t\t\t\tscp_uptime: ") + \
        user.html_mono(humanize_time(time.time() - RUNTIME))
    buttons = {
        {"Source": "https://github.com/aliwoto/woto-scp", "close": "close_message"},
    }
    return await message.reply_text(text=text, reply_markup=buttons)


@bot.on_callback_query(
    bot.sudo
    & bot.filters.regex('^close_message'),
)
async def _(_, query: user.types.CallbackQuery):
    await query.message.delete()
