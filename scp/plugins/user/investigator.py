from scp import user
from scp.utils import parser
from pyrogram.types import (
    Message,
)


@user.on_message(user.sudo & user.command('uInvest'))
async def create_handler(_, message: Message):
    # .uInvest @aa bot
    commands = user.split_message(message, 2)



    pass

