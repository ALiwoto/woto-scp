from typing import (
    Union,
    Optional,
    List,
    AsyncGenerator,
)
from datetime import datetime
import logging
import asyncio
from pyrogram import(
    utils as pUtils,
    enums,
    Client,
    types, 
    raw, 
    errors, 
    session,
)
from typing import Union
import typing
from attrify import Attrify as Atr
from pyrogram import(
    client as pyroClient,
    Client, 
    types, 
    raw, 
)
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.phone import EditGroupCallTitle
from pyrogram.raw.types.messages.chat_full import ChatFull
from pyrogram.raw.types.channel_full import ChannelFull
from scp.utils.parser import(
    html_mono,
    html_bold,
    html_italic,
    html_link, 
    split_some,
    html_normal,
    html_mention, 
    html_normal_chat_link,
    mention_user_html,
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
        if len(my_strs) < 2:
            return ''
        return my_strs[1]
    
    def split_some(self, value: str, max_count: int = 0, *delimiters) -> list:
        return split_some(value, max_count, *delimiters)
    
    def split_message(self, message: types.Message, max_count: int = 0) -> typing.List[str]:
        return split_some(message.text, max_count, ' ', '\n')
    
    def split_timestamped_message(self, message: types.Message, max_count: int = 0) -> typing.List[str]:
        return split_some(message.text, max_count,  ' -> ', ' ', '\n')

    def html_mono(self, value, *argv) -> str:
        return html_mono(value, *argv)
    
    def html_normal(self, value, *argv) -> str:
        return html_normal(value, *argv)
    
    def html_bold(self, value, *argv) -> str:
        return html_bold(value, *argv)
    
    def html_italic(self, value, *argv) -> str:
        return html_italic(value, *argv)
    
    def html_link(self, value, link: str, *argv) -> str:
        return html_link(value, link, *argv)
    
    async def reply_exception(self, message: types.Message, e: Exception):
        return await message.reply_text(self.html_bold('Error:') + self.html_mono(f'\n\t{e}'))
    
    async def html_normal_chat_link(self, value, chat: types.Chat, *argv) -> str:
        return await html_normal_chat_link(value, chat, *argv)
    
    def mention_user_html(self, user: types.User, name_limit: int = -1) -> str:
        return mention_user_html(user, name_limit)

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
    
    async def try_get_messages_count(self, chat_id:Union[int, str], user_id: Union[int, str]) -> int:
        try:
            message_count = 0
            async for _ in self.search_messages(
                chat_id=chat_id, 
                query="",
                from_user=user_id,
            ):
                message_count += 1
            
            return message_count
        except Exception: return 0
    
    def unpack_inline_message_id(inline_message_id: str) -> Atr:
        return unpackInlineMessage(inline_message_id)

    async def invoke(
        self,
        query: raw.core.TLObject,
        retries: int = session.Session.MAX_RETRIES,
        timeout: float = session.Session.WAIT_TIMEOUT,
        sleep_threshold: float = None
    ) -> raw.core.TLObject:
        while True:
            try:
                return await super().invoke(
                    query=query,
                    retries=retries,
                    timeout=timeout,
                    sleep_threshold=sleep_threshold,
                )
            except (
                errors.SlowmodeWait,
                errors.FloodWait,
                errors.exceptions.flood_420.FloodWait,
                errors.exceptions.flood_420.Flood,
                errors.exceptions.Flood,
                errors.exceptions.ApiIdPublishedFlood,
            ) as e:
                logging.warning(f'Sleeping for - {e.value} | {e}')
                await asyncio.sleep(e.value + 2)
            except OSError:
                # attempt to fix TimeoutError on slower internet connection
                # await self.session.stop()
                # await self.session.start()
                ...
                
    async def send(
        self,
        data: raw.core.TLObject,
        retries: int = session.Session.MAX_RETRIES,
        timeout: float = session.Session.WAIT_TIMEOUT,
        sleep_threshold: float = None
    ) -> raw.core.TLObject:
        return await self.invoke(
            query=data, 
            retries=retries, 
            timeout=timeout, 
            sleep_threshold=sleep_threshold
        )
    
    async def iter_history(
        self, 
        chat_id: Union[int, str], 
        limit: int = 0, 
        offset: int = 0, 
        offset_id: int = 0, 
        offset_date: datetime = pUtils.zero_datetime()
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        return await super().get_chat_history(chat_id, limit, offset, offset_id, offset_date)
    
    
    async def iter_chat_members(
        self, 
        chat_id: Union[int, str], 
        query: str = "", 
        limit: int = 0, 
        filter: "enums.ChatMembersFilter" = enums.ChatMembersFilter.SEARCH
    ) -> Optional[AsyncGenerator["types.ChatMember", None]]:
        return await super().get_chat_members(chat_id, query, limit, filter)
    
    
    async def iter_dialogs(
        self, 
        limit: int = 0
    ) -> Optional[AsyncGenerator["types.Dialog", None]]:
        return await super().get_dialogs(limit)
        
    
    async def get_history(
        self, 
        chat_id: Union[int, str], 
        limit: int = 0, 
        offset: int = 0, 
        offset_id: int = 0, 
        offset_date: datetime = pUtils.zero_datetime()
    ) -> List["types.Message"]:
        all_messages = []
        async for current in self.get_chat_history(chat_id, limit, offset, offset_id, offset_date):
            all_messages.append(current)
        
        return all_messages


    async def handle_updates_woto(self, updates):
        if isinstance(updates, (raw.types.Updates, raw.types.UpdatesCombined)):
            is_min = (await self.fetch_peers(updates.users)) or (await self.fetch_peers(updates.chats))

            users = {u.id: u for u in updates.users}
            chats = {c.id: c for c in updates.chats}

            for update in updates.updates:
                channel_id = getattr(
                    getattr(
                        getattr(
                            update, "message", None
                        ), "peer_id", None
                    ), "channel_id", None
                ) or getattr(update, "channel_id", None)

                pts = getattr(update, "pts", None)
                pts_count = getattr(update, "pts_count", None)

                if isinstance(update, raw.types.UpdateChannelTooLong):
                    pyroClient.log.warning(update)

                if isinstance(update, raw.types.UpdateNewChannelMessage) and is_min:
                    message = update.message

                    if not isinstance(message, raw.types.MessageEmpty):
                        try:
                            diff = await self.send(
                                raw.functions.updates.GetChannelDifference(
                                    channel=await self.resolve_peer(pUtils.get_channel_id(channel_id)),
                                    filter=raw.types.ChannelMessagesFilter(
                                        ranges=[raw.types.MessageRange(
                                            min_id=update.message.id,
                                            max_id=update.message.id
                                        )]
                                    ),
                                    pts=pts - pts_count,
                                    limit=pts
                                )
                            )
                        except errors.ChannelPrivate:
                            pass
                        else:
                            if not isinstance(diff, raw.types.updates.ChannelDifferenceEmpty):
                                if hasattr(diff, 'users'):
                                    users.update({u.id: u for u in diff.users})
                                if hasattr(diff, 'chats'):
                                    chats.update({c.id: c for c in diff.chats})

    async def set_group_call_title(self, chat_id: Union[str, int], title: str):
        try:
            peer = await self.resolve_peer(chat_id)
            chat: ChatFull = await self.send(GetFullChannel(channel=peer))
            if not isinstance(chat.full_chat, ChannelFull):
                return
            await self.send(EditGroupCallTitle(call=chat.full_chat.call, title=title))
        except BaseException:
            pass

    async def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        caption: str = None,
        parse_mode: Optional["enums.ParseMode"] = None,
        caption_entities: List["types.MessageEntity"] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None
    ) -> List["types.Message"]:
        """Copy messages of any kind.

        The method is analogous to the method :meth:`~Client.forward_messages`, but the copied message doesn't have a
        link to the original message.

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            from_chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the source chat where the original message was sent.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_id (``int``):
                Message identifier in the chat specified in *from_chat_id*.

            caption (``string``, *optional*):
                New caption for media, 0-1024 characters after entities parsing.
                If not specified, the original caption is kept.
                Pass "" (empty string) to remove the caption.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the new caption, which can be specified instead of *parse_mode*.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_to_message_id (``int``, *optional*):
                If the message is a reply, ID of the original message.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the copied message is returned.

        Example:
            .. code-block:: python

                # Copy a message
                await app.copy_message(to_chat, from_chat, 123)

        """
        message: types.Message = await self.get_messages(from_chat_id, message_id)
        if message.service:
            return None
            #log.warning(f"Service messages cannot be copied. "
            #            f"chat_id: {self.chat.id}, message_id: {self.message_id}")
        elif message.game and not await message._client.storage.is_bot():
            return None
            #log.warning(f"Users cannot send messages with Game media type. "
            #            f"chat_id: {self.chat.id}, message_id: {self.message_id}")
        elif message.empty:
            return None
            #log.warning(f"Empty messages cannot be copied. ")
        
        if not reply_markup and message.reply_markup:
            reply_markup = message.reply_markup
        
        return await message.copy(
            chat_id=chat_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            schedule_date=schedule_date,
            protect_content=protect_content,
            reply_markup=reply_markup
        )





