"""

"""
import asyncio
from pyrogram import idle
from scp import user, bot
from scp.core.functions.plugins import (
    load_user_plugins,
    load_bot_plugins,
    load_private_plugins,
)
from scp.core.functions.extra_features import load_extra_features
from scp.utils.selfInfo import updateInfo
from scp.utils.interpreter import shell
#from scp.database.Operational import InitializeDatabase


HELP_COMMANDS = {}


async def start_bot():
    load_extra_features()
    
    await bot.start()
    await user.start()
    await updateInfo()
    #await InitializeDatabase()
    if not user.scp_config.no_input:
        asyncio.create_task(shell())
    await asyncio.gather(
        load_bot_plugins(),
        load_user_plugins(),
        load_private_plugins(),
        idle()
    )
    
if __name__ == '__main__':
    from . import loop
    loop.run_until_complete(start_bot())
