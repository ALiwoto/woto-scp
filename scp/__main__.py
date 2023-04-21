"""

"""
import asyncio
from pyrogram import idle
from scp import user, bot
from scp.core.functions.plugins import (
    loadUserPlugins,
    load_bot_plugins,
    loadPrivatePlugins,
)
from scp.utils.selfInfo import updateInfo
from scp.utils.interpreter import shell
#from scp.database.Operational import InitializeDatabase


HELP_COMMANDS = {}


async def start_bot():
    await bot.start()
    await user.start()
    await updateInfo()
    #await InitializeDatabase()
    asyncio.create_task(shell())
    await asyncio.gather(
        load_bot_plugins(),
        loadUserPlugins(),
        loadPrivatePlugins(),
        idle()
    )
    
if __name__ == '__main__':
    from . import loop
    loop.run_until_complete(start_bot())
