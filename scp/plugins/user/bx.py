

from scp import user
from pyrogram.types import Message


__PLUGIN__ = 'bx'


__HELP__ = """
BX plugin is designed for easily accessing and managing your BX
positions through Telegram. It allows you to view your positions,
open new positions, close existing positions, and view your account
information and stats.
"""

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        'hot_assets',
    ),
)
async def hot_assets_handler(_, message: Message):
    if not user.bx_client:
        await message.reply('BX client not initialized.')
        return

    txt = user.html_bold('Hot Assets:')

    hot_search_results = await user.bx_client.get_hot_search()
    for current_item in hot_search_results.data.result:
        txt += user.html_bold("\n - ") + user.html_normal(f"{current_item}")
