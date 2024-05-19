"""

"""
import asyncio
import sys
from . import woto_config
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
    if '--help' in sys.argv:
        print('''
        --help: Show this message
        --no-input: Disable the input shell
        --gen-config: Generate a new encrypted config file
        ''')
        sys.exit(0)
    
    if '--no-input' in sys.argv:
        user.scp_config.no_input = True

    if '--gen-config' in sys.argv:
        user_key = input("Enter your config gen key: ")
        fav_letter = input("Enter your favorite letter: ")
        woto_config.the_config.gen_encrypted_config("config.ini.enc", user_key, fav_letter)
        sys.exit(0)

    from . import loop
    loop.run_until_complete(start_bot())
