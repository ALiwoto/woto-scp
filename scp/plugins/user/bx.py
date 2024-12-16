from scp import user
from pyrogram.types import Message
import asyncio


__PLUGIN__ = "bx"


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
        "hot_assets",
    ),
)
async def hot_assets_handler(_, message: Message):
    if not user.bx_client:
        await message.reply_text("BX client not initialized.")
        return

    txt = user.html_bold("Hot Assets:")

    hot_search_results = await user.bx_client.get_hot_search()
    for current_item in hot_search_results.data.result:
        txt += user.html_bold("\n - ") + user.html_normal(f"{current_item}")

    await message.reply_text(text=txt, disable_web_page_preview=True)

@user.on_message(
    ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.owner
    & user.command(
        "positions",
    ),
)
async def positions_handler(_, message: Message):
    if not user.bx_client:
        await message.reply_text("BX client not initialized.")
        return
    elif not user.bx_client.authorization_token: # use method later on
        await message.reply_text("BX client not authorized.")
        return

    result = await user.bx_client.get_contract_list(page_id=0, page_size=1)
    per_page_size = 10

    assert result is not None
    assert result.code == 0
    assert result.data is not None

    for current_stat in result.data.margin_stats:
        txt = user.html_bold(
            f" - {current_stat.margin_coin_name}: {current_stat.total} positions open"
        )
        total_fetched = 0
        while total_fetched < current_stat.total:
            current_page = total_fetched // per_page_size
            result = await user.bx_client.get_contract_list(
                page_id=current_page,
                page_size=per_page_size,
                margin_coin_name=current_stat.margin_coin_name,
            )
            for current_contract in result.data.orders:
                txt += user.html_normal(f" - {current_contract}")

            await asyncio.sleep(0.5)  # prevent rate limiting
            total_fetched += per_page_size
        
        await message.reply_text(text=txt, disable_web_page_preview=True)
