import typing
import os
import json
import uuid
from datetime import datetime
from typing import (
    NoReturn,
    Union,
    Callable,
    List,
    Optional
)
from pyrogram import (
    filters,
    types,
    raw,
    errors,
    utils as pUtils,
)
from pyrogram.raw.types.messages.bot_results import BotResults
from pyrogram import enums
from pyrogram.raw.functions.messages import ReadMentions
from wotoplatform import WotoClient
from wotoplatform.types.errors import (
    ClientAlreadyInitializedException,
)
from scp.core.filters.command import command
from scp.utils import wfilters
from scp.utils.auto_inline import (
    auto_inline_dict,
    AutoInlineContainer,
    AutoInlineType
)
from scp.utils.sibylUtils import SibylClient
from scp.database.database_client import DatabaseClient
from scp.utils.misc import restart_scp as restart_woto_scp
from kantex import md as Markdown
from .woto_base import WotoClientBase
from .woto_client import WotoPyroClient
from ...woto_config import the_config
import asyncio
import logging

__scp__helper__bots__: typing.List[WotoClientBase] = None

__wp_client__: WotoClient = None


def __get_wp_client__() -> WotoClient:
    if not the_config.wp_host or not the_config.wp_username:
        return None
    
    global __wp_client__
    if __wp_client__:
        return __wp_client__

    __wp_client__ = WotoClient(
        username=the_config.wp_username,
        password=the_config.wp_password,
        endpoint=the_config.wp_host,
        port=the_config.wp_port,
    )
    return __wp_client__


def _get_scp_bots() -> typing.List[WotoClientBase]:
    global __scp__helper__bots__
    if __scp__helper__bots__ is not None:
        return __scp__helper__bots__
    # open the file "bots.json"
    try:
        my_str = open('bots.json').read()
        # load into json
        my_json = json.loads(my_str)
        if not isinstance(my_json, list):
            return None

        my_bots: typing.List[WotoClientBase] = []
        current_client: WotoClientBase = None

        for current in my_json:
            if not isinstance(current, str):
                continue
            try:
                current_client = WotoClientBase(
                    name=current.split(':')[0],
                    in_memory=True,
                    bot_token=current,
                    api_id=the_config.api_id,
                    api_hash=the_config.api_hash,
                )
                my_bots.append(current_client)
            except Exception as ex:
                logging.warning(f'failed to load bots: {ex}')

        __scp__helper__bots__ = my_bots
        return my_bots

    except:
        return None


class ScpClient(WotoPyroClient):
    def __init__(
        self,
        name: str,
        is_scp_bot: bool = True,
        the_scp_bot: 'ScpClient' = None
    ):
        self.name = name
        proxy = None
        if the_config.use_proxy:
            proxy = {
                "scheme": the_config.proxy_scheme,  # "socks4", "socks5" and "http" are supported
                "hostname": the_config.proxy_hostname,
                "port": the_config.proxy_port,
                "username": the_config.proxy_username,
                "password": the_config.proxy_password
            }
        
        super().__init__(
            name=name,
            api_id=the_config.api_id,
            api_hash=the_config.api_hash,
            workers=16,
            device_model=the_config.device_model,
            app_version=the_config.app_version,
            no_updates=False,
            proxy=proxy,
        )
        self.is_scp_bot = is_scp_bot
        if is_scp_bot:
            self.the_bot = self
        else:
            the_scp_bot.the_user = self
            self.the_user = self
            self.the_bot = the_scp_bot

    async def start(self):
        await super().start()
        # me = await super().get_me()
        if not self.me.id in self.scp_config._sudo_users:
            self.scp_config._sudo_users.append(self.me.id)
            self.sudo |= self.filters.user(self.me.id)
        
        if not self.me.id in self.scp_config._owner_users:
            self.scp_config._owner_users.append(self.me.id)
            self.owner |= self.filters.user(self.me.id)

        if not self.is_scp_bot and self.wp:
            try:
                await self.wp.start()
            except ClientAlreadyInitializedException:
                pass
            except Exception as e:
                logging.warning(e)

        self.original_phone_number = self.me.phone_number
        self.db = DatabaseClient(self.storage.conn)
        logging.warning(
            f'logged in as {self.me.first_name}.',
        )

    async def start_all_bots(self):
        try:
            for bot in self.the_bots:
                await bot.start()
        except Exception as e:
            logging.warning(
                f'failed to start bot: {e}',
            )
        self.are_bots_started = True
        self.the_bot.are_bots_started = True

    async def stop(self, block: bool = True):
        logging.warning(
            f'logged out from {self.me.first_name}.',
        )
        await super().stop(block)

    def command(self, *args, **kwargs):
        return command(*args, **kwargs)

    async def get_message_to_download(self, message: types.Message, continue_till_found: bool = False) -> types.Message:
        link_to_message = self.get_non_cmd(message)
        splitted = link_to_message.split()
        if len(splitted) > 0:
            link_to_message = splitted[0]
        
        if link_to_message:
            try:
                linked_message = await self.get_message_by_link(link_to_message, continue_till_found)
                if linked_message and not linked_message.empty:
                    # just return it, no need to check anything
                    return await self.get_message_to_download(
                        message=message,
                        continue_till_found=continue_till_found
                    )
                
            except: pass
        
        if not message.command:
            message.command = [] #TODO: FIXME
        
        available_media = ("audio", "document", "photo", "sticker", "animation", "video", "voice", "video_note")
        for i in available_media:
            if getattr(message, i, None):
                return message
        else:
            reply = message.reply_to_message
            if not getattr(reply, 'empty', True):
                for i in available_media:
                    if getattr(reply, i, None):
                        return reply
        
        return None

    async def ban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: Union[int, str],
        until_date: datetime = pUtils.zero_datetime(),
    ) -> Union["types.Message", bool]:
        return await super().ban_chat_member(chat_id, user_id, until_date=until_date)

    async def kick_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: Union[int, str],
        ignore_error: bool = True,
        tries: int = 5,
        until_date: datetime = pUtils.zero_datetime(),
    ) -> Union["types.Message", bool]:
        ret_message: types.Message = None
        try:
            ret_message = await super().ban_chat_member(chat_id, user_id, until_date=until_date)
        except Exception:
            pass

        done = False
        if not tries:
            tries = 5
        current_tries = 0
        while not done and current_tries <= tries:
            current_tries += 1
            try:
                await self.unban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id
                )
                done = await self.unban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id
                )
            except Exception:
                if not ignore_error:
                    raise

        return ret_message

    async def restart_scp(self, update_req: bool = False, hard: bool = False) -> bool:
        await self.stop_scp()
        return restart_woto_scp(update_req, hard)

    async def exit_scp(self) -> 'NoReturn':
        await self.stop_scp()
        return exit()

    async def stop_scp(self, only_me: bool = False):
        try:
            if only_me:
                await self.stop(block=False)
                return
            print(' ')
            await self.the_bot.stop_scp(True)
            await self.the_user.stop_scp(True)

        except ConnectionError:
            pass

    async def delete_all_messages(
        self,
        chat_id: Union[int, str],
        message_ids: Union[int, typing.Iterable[int]],
        revoke: bool = True,
    ) -> bool:
        if len(message_ids) < 100:
            return await self.delete_messages(
                chat_id=chat_id,
                message_ids=message_ids,
                revoke=revoke
            )
        all_messages = [message_ids[i:i + 100]
                        for i in range(0, len(message_ids), 100)]
        for current in all_messages:
            try:
                await self.delete_messages(
                    chat_id=chat_id,
                    message_ids=current,
                )
                await asyncio.sleep(3)
            except Exception:
                pass

    async def eval_base(self, client, message, code: str, silent: bool = False):
        """
        Runs a python code and returns the output.
        """

        # not implemented here, but it's supposed to be implemented in
        # the plugins. If no plugin is implementing it, this method
        # will do nothing.
        # This definition here is only for documentation purposes.
        pass
    

    async def shell_base(
        self, 
        message, 
        command: str, 
        silent_on_success: bool = False,
        throw_on_error: bool = False,
    ):
        """
        Runs a shell command.
        """

        # not implemented here, but it's supposed to be implemented in
        # the plugins. If no plugin is implementing it, this method
        # will do nothing.
        # This definition here is only for documentation purposes.
        pass
    
    
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        disable_web_page_preview: bool = None,
        disable_notification: bool = None,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_to_chat_id: int = None,
        reply_to_story_id: int = None,
        quote_text: str = None,
        quote_entities: List["types.MessageEntity"] = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None
    ) -> "types.Message":
        if self.me.is_bot or not isinstance(reply_markup, (types.InlineKeyboardMarkup, dict, list)):
            return await super().send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                entities=entities,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                message_thread_id=message_thread_id,
                schedule_date=schedule_date,
                protect_content=protect_content,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                quote_text=quote_text,
                quote_entities=quote_entities,
                reply_markup=reply_markup,
            )
        
        # if this is a user and is trying to send a message with keyboard buttons, automate
        # sending it with using inline through bot.
        if isinstance(reply_markup, (dict, list)):
            reply_markup = self._parse_inline_reply_markup(reply_markup)
        container = AutoInlineContainer(
            unique_id="auIn" + str(uuid.uuid4()),
            message_type=AutoInlineType.TEXT,
            text=text,
            keyboard=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            entities=entities,
        )
        auto_inline_dict[container.unique_id] = container
        inline_response: BotResults = await self.get_inline_bot_results(
            self.the_bot.me.username,
            container.unique_id,
        )

        all_updates = []
        for current_result in inline_response.results:
            the_update = await self.send_inline_bot_result(
                chat_id=chat_id,
                query_id=inline_response.query_id,
                result_id=current_result.id,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id
            )
            all_updates.append(the_update)

        all_messages = await self.get_parsed_updates(all_updates, types.Message)
        if not all_messages:
            return None
        elif len(all_messages) == 1:
            return all_messages[0]
        else:
            return all_messages
    
    async def send_photo(
        self,
        chat_id: typing.Union[int, str],
        photo: typing.Union[str, typing.BinaryIO],
        caption: str = "",
        parse_mode: typing.Optional["enums.ParseMode"] = None,
        caption_entities: typing.List["types.MessageEntity"] = None,
        ttl_seconds: int = None,
        has_spoiler: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        reply_to_story_id: int = None,
        message_thread_id: int = None,
        quote_text: str = None,
        quote_entities: List["types.MessageEntity"] = None,
        reply_markup: typing.Union["types.InlineKeyboardMarkup", "types.ReplyKeyboardMarkup",
                                   "types.ReplyKeyboardRemove", "types.ForceReply"] = None,
        progress: Callable = None,
        progress_args: tuple = ()
    ) -> typing.Optional["types.Message"]:
        if self.me.is_bot or not isinstance(reply_markup, (types.InlineKeyboardMarkup, dict, list)) or not the_config.shared_channel:
            return await super().send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                has_spoiler=has_spoiler,
                ttl_seconds=ttl_seconds,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                protect_content=protect_content,
                message_thread_id=message_thread_id,
                reply_to_story_id=reply_to_story_id,
                quote_text=quote_text,
                quote_entities=quote_entities,
                reply_markup=reply_markup,
                progress=progress,
                progress_args=progress_args
            )

        # if this is a user and is trying to send a message with keyboard buttons, automate
        # sending it with using inline through bot.

        sent_message = await super().send_photo(
            chat_id=the_config.shared_channel,
            photo=photo,
        )
        if isinstance(reply_markup, (dict, list)):
            reply_markup = self._parse_inline_reply_markup(reply_markup)
        container = AutoInlineContainer(
            unique_id="auIn" + str(uuid.uuid4()),
            message_type=AutoInlineType.PHOTO,
            text=caption,
            media_chat_id=sent_message.chat.id,
            media_message_id=sent_message.id,
            keyboard=reply_markup,
        )
        auto_inline_dict[container.unique_id] = container
        inline_response: BotResults = await self.get_inline_bot_results(
            self.the_bot.me.username,
            container.unique_id,
        )

        all_updates = []
        for current_result in inline_response.results:
            the_update = await self.send_inline_bot_result(
                chat_id=chat_id,
                query_id=inline_response.query_id,
                result_id=current_result.id,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id
            )
            all_updates.append(the_update)

        all_messages = await self.get_parsed_updates(all_updates, types.Message)
        if not all_messages:
            return None
        elif len(all_messages) == 1:
            setattr(all_messages[0], "user_photo", sent_message.photo)
            return all_messages[0]
        else:
            for current in all_messages:
                setattr(current, "user_photo", sent_message.photo)
            return all_messages

    async def send_inline_bot_result(
        self,
        chat_id: Union[int, str],
        query_id: int,
        result_id: str,
        disable_notification: bool = None,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        quote_text: str = None,
        parse_mode: Optional["enums.ParseMode"] = None,
        quote_entities: List["types.MessageEntity"] = None
    ):
        try:
            return await super().send_inline_bot_result(
                chat_id=chat_id,
                query_id=query_id,
                result_id=result_id,
                disable_notification=disable_notification,
                quote_text=quote_text,
                quote_entities=quote_entities,
                parse_mode=parse_mode,
                message_thread_id=message_thread_id,
                reply_to_message_id=reply_to_message_id
            )
        except errors.SlowmodeWait as e:
            await asyncio.sleep(e.x)
            return await super().send_inline_bot_result(
                chat_id=chat_id,
                query_id=query_id,
                result_id=result_id,
                disable_notification=disable_notification,
                quote_text=quote_text,
                quote_entities=quote_entities,
                parse_mode=parse_mode,
                message_thread_id=message_thread_id,
                reply_to_message_id=reply_to_message_id
            )

    async def read_all_mentions(self, chat_id: typing.Union[str, int]) -> None:
        try:
            await self.send(
                ReadMentions(
                    peer=await self.resolve_peer(chat_id),
                ),
            )
        except Exception:
            pass

    async def get_bot_perspective(
        self, 
        message: types.Message, 
        delay: float = 2,
        max_tries: int = 10,
        allow_text: bool = True,
    ):
        """
            Returns a message from the bot's perspective.
        """
        if not message.media and not allow_text:
            return None
        
        if self.me.is_bot:
            return message
        
        asyncio.create_task(self.forward_messages_with_delay(
            chat_id=self.the_bot.me.username or self.the_bot.me.id,
            from_chat_id=message.chat.id,
            message_ids=message.id,
            disable_notification=False,
            delay=delay,
        ))
        message_from_bot: types.Message = None
        for _ in range(max_tries):
            message_from_bot = await self.the_bot.scp_listen(chat_id=self.me.id)
            if message_from_bot.media == message.media:
                break
        
        return message_from_bot
        
    async def get_media_file_id(
        self, 
        message: types.Message, 
        delay: float = 2,
    ) -> str:
        """
            Returns the perma media id (file_id) of a media message.
            The id belongs to the scp_bot, it's not usable by the user; because
            media ids for users in telegram will get revoked too soon, hence there is
            no point in getting the id that belongs to the user.
            If the message is not a media message, it returns None.
        """
        message_from_bot = await self.get_bot_perspective(message, delay, allow_text=False)
        return getattr(getattr(message_from_bot, message_from_bot.media.name.lower(), None), 
                       "file_id", None)
    
    original_phone_number: str = ''
    is_scp_bot: bool = False
    wordle_global_config = None
    the_bot: 'ScpClient'
    the_user: 'ScpClient'
    wfilters = wfilters
    raw = raw
    types = types
    md = Markdown
    exceptions = errors
    
    scp_config = the_config
    
    cached_messages: typing.List[types.Message] = None
    the_bots: typing.List[WotoClientBase] = _get_scp_bots()
    are_bots_started: bool = False

    sudo = (filters.me | filters.user(the_config._sudo_users))
    owner = (filters.me | filters.user(the_config._owner_users))
    special_users = (filters.me | filters.user(the_config._special_users))
    special_channels = filters.chat(the_config._special_channels)
    azure_sudo_users = filters.user(the_config._azure_sudo_users)
    enforcer = (filters.me | filters.user(the_config._enforcers))
    inspector = (filters.me | filters.user(the_config._inspectors))
    cmd_prefixes = the_config.prefixes or ['!', '.']
    wp: WotoClient = __get_wp_client__()
    db: DatabaseClient = None
    log_channel = the_config.log_channel
    private_resources = the_config.private_resources

    # sibyl configuration stuff:
    public_sibyl_filter = filters.chat(
        the_config.public_listener,
    )
    private_sibyl_filter = filters.chat(
        the_config.private_listener,
    )
    sibyl: SibylClient = SibylClient(the_config.sibyl_token)

    auto_read_enabled = True
    avalon_system_enabled = True
