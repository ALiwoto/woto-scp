from typing import Union
import typing
from attrify import Attrify as Atr
from pyrogram import(
    Client, 
    types, 
    raw, 
)
from scp.utils.parser import(
    html_bold,
    html_link, 
    html_mention, 
    html_mono,
    html_normal_chat_link, 
    split_some,
)
from scp.utils.unpack import unpackInlineMessage

class WotoClientBase(Client):
    def is_silent(self, message: types.Message) -> bool:
        return (
            isinstance(message, types.Message)
            and message.command != None
            and len(message.command) > 0
            and message.command[0x0].endswith('!')
        )
    
    def get_non_cmd(self, message: types.Message) -> str:
        my_strs = split_some(message.text, 1, ' ', '\n')
        if len(my_strs) < 1:
            return ''
        return my_strs[1]
    
    def split_some(self, value: str, max_count: int = -1, *delimiters) -> list:
        return split_some(value, max_count, *delimiters)
    
    def split_message(self, message: types.Message, max_count: int = -1) -> typing.List[str]:
        return split_some(message.text, max_count, ' ', '\n')

    def html_mono(self, value, *argv) -> str:
        return html_mono(value, *argv)
    
    def html_bold(self, value, *argv) -> str:
        return html_bold(value, *argv)
    
    def html_link(self, value, link: str, *argv) -> str:
        return html_link(value, link, *argv)
    
    async def html_normal_chat_link(self, value, chat: types.Chat, *argv) -> str:
        return await html_normal_chat_link(value, chat, *argv)

    async def html_mention(self, value: Union[types.User, int], name: str = None, *argv) -> str:
        return await html_mention(value, name, self, *argv)
    

    async def get_online_counts(self, chat_id: Union[int, str]) -> int:
        response = await self.send(
            raw.functions.messages.GetOnlines(
                peer=await self.resolve_peer(chat_id),
            )
        )
        return getattr(response, 'onlines', 0)
    
    async def get_online_count(self, chat_id: Union[int, str]) -> int:
        return await self.get_online_counts(chat_id)
    async def get_onlines_count(self, chat_id: Union[int, str]) -> int:
        return await self.get_online_counts(chat_id)
    
    async def try_get_online_counts(self, chat_id: Union[int, str]) -> int:
        try:
            response = await self.send(
                raw.functions.messages.GetOnlines(
                    peer=await self.resolve_peer(chat_id),
                )
            )
            return getattr(response, 'onlines', 0)
        except Exception: return 0
    
    async def try_get_common_chats_count(self, user_id: Union[int, str]) -> int:
        try:
            return len(await self.get_common_chats(user_id))
        except Exception: return 0
    
    def unpack_inline_message_id(inline_message_id: str) -> Atr:
        return unpackInlineMessage(inline_message_id)

