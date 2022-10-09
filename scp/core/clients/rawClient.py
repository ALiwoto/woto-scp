import typing
import json
from datetime import datetime
from typing import(
    NoReturn, 
    Union,
    Optional,
    List,
)
from pyrogram import(
    filters, 
    types, 
    raw, 
    errors, 
    utils as pUtils,
)
from pyrogram import enums
from pyrogram.raw.functions.messages import ReadMentions
from wotoplatform import WotoClient
from wotoplatform.types.errors import (
    ClientAlreadyInitializedException,
)
from scp.core.filters.Command import command
from scp.utils import wfilters
from scp.utils.sibylUtils import SibylClient
from scp.utils.misc import restart_scp as restart_woto_scp
from configparser import ConfigParser
from kantex import md as Markdown
from aiohttp import ClientSession, client_exceptions
from .wotobase import WotoClientBase
from ...wotoConfig import the_config
import asyncio
import logging

__scp__helper__bots__: typing.List[WotoClientBase] = None

__wp_client__: WotoClient = None

def __get_wp_client__() -> WotoClient:
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
                    in_memory=True,
                    bot_token=current,
                    api_id=the_config.api_id,
                    api_hash=the_config.api_hash,
                )
                my_bots.append(current_client)
            except Exception: continue
        
        __scp__helper__bots__ = my_bots
        return my_bots

    except: return None

class ScpClient(WotoClientBase):
    def __init__(
        self,
        name: str,
        is_scp_bot: bool = True,
        the_scp_bot: 'ScpClient' = None
    ):
        self.name = name
        super().__init__(
            name=name,
            api_id=the_config.api_id,
            api_hash=the_config.api_hash,
            workers=16,
            device_model='kaizoku',
            app_version='woto-scp',
            no_updates=False,
        )
        self.aioclient:ClientSession = ClientSession()
        self.is_scp_bot = is_scp_bot
        if is_scp_bot:
            self.the_bot = self
        else:
            the_scp_bot.the_user = self
            self.the_user = self
            self.the_bot = the_scp_bot

    async def start(self):
        await super().start()
        me = await super().get_me()
        if not me.id in self._sudo:
            self._sudo.append(me.id)
        if not me.id in self._owners:
            self._owners.append(me.id)
        
        try:
            await self.wp.start()
        except ClientAlreadyInitializedException: pass
        except Exception as e: logging.warning(e)
        
        self.original_phone_number = me.phone_number
        logging.warning(
            f'logged in as {me.first_name}.',
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
            f'logged out from {(await super().get_me()).first_name}.',
        )
        await super().stop(block)

    def command(self, *args, **kwargs):
        return command(*args, **kwargs)
    
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
        until_date: datetime = pUtils.zero_datetime(),
    ) -> Union["types.Message", bool]:
        return await super().ban_chat_member(chat_id, user_id, until_date=until_date)

    # from Kantek
    async def resolve_url(self, url: str) -> str:
        if not url.startswith('http'):
            url: str = f'http://{url}'
        async with self.aioclient.get(
            f'http://expandurl.com/api/v1/?url={url}',
        ) as response:
            e = await response.text()
        return e if e != 'false' and e[:-1] != url else None
    
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
    
    async def get_message_by_link(self, link: str) -> types.Message:
        link = link.replace('telegram.me', 't.me')
        link = link.replace('telegram.dog', 't.me')
        link = link.replace('https://', '')
        link = link.replace('http://', '')
        if link.find('t.me') == -1:
            return None
        
        chat_id = None
        message_id: int = 0
        # the format can be either like t.me/c/1627169341/1099 or
        # t.me/AnimeKaizoku/6669424
        if link.find('/c/') != -1:
            my_strs = link.split('/c/')
            if len(my_strs) < 2:
                return None
            my_strs = my_strs[1].split('/')
            if len(my_strs) < 2:
                return None
            chat_id = int('-100' + my_strs[0])
            message_id = int(my_strs[1])
        else:
            my_strs = link.split('/')
            if len(my_strs) < 3:
                return None
            chat_id = my_strs[1]
            message_id = int(my_strs[2])
        
        if not chat_id:
            return None
        
        return await self.get_messages(chat_id, message_id)

    async def Request(self, url: str, type: str, *args, **kwargs):
        if type == 'get':
            resp = await self.aioclient.get(url, *args, **kwargs)
        elif type == 'post':
            resp = await self.aioclient.post(url, *args, **kwargs)
        elif type == 'put':
            resp = await self.aioclient.put(url, *args, **kwargs)
        try:
            return await resp.json()
        except client_exceptions.ContentTypeError:
            return (await resp.read()).decode('utf-8')
        
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
        all_messages  = [message_ids[i:i + 100] for i in range(0, len(message_ids), 100)]
        for current in all_messages:
            try:
                await self.delete_messages(
                    chat_id=chat_id,
                    message_ids=current,
                )
                await asyncio.sleep(3)
            except Exception: pass
    
    # async def eval_base(client: user, message: Message, code: str, silent: bool = False):
    eval_base = None
    # async def shell_base(message: Message, command: str):
    shell_base = None
    
    async def get_my_dialogs(self) -> typing.List[types.Dialog]:
        if not self.__my_all_dialogs__ or len(self.__my_all_dialogs__) < 2:
            return await self.refresh_dialogs()
        return self.__my_all_dialogs__
    
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        disable_web_page_preview: bool = None,
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
    ) -> "types.Message":
        try:
            return await super().send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                entities=entities,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                protect_content=protect_content,
                reply_markup=reply_markup
            )
        except errors.SlowmodeWait as e:
            await asyncio.sleep(e.x)
            return await super().send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                entities=entities,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                protect_content=protect_content,
                reply_markup=reply_markup
            )

    async def send_inline_bot_result(
        self,
        chat_id: Union[int, str],
        query_id: int,
        result_id: str,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        hide_via: bool = None
    ):
        try:
            return await super().send_inline_bot_result(
                chat_id=chat_id,
                query_id=query_id,
                result_id=result_id,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                hide_via=hide_via
            )
        except errors.SlowmodeWait as e:
            await asyncio.sleep(e.x)
            return await super().send_inline_bot_result(
                chat_id=chat_id,
                query_id=query_id,
                result_id=result_id,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                hide_via=hide_via
            )

    
    async def get_dialog_by_id(self, chat_id: typing.Union[str, int]) -> types.Dialog:
        my_all = await self.get_my_dialogs()
        if not my_all:
            return None
        
        for current in my_all:
            if not current.chat:
                continue
            if current.chat.username == chat_id or current.chat.id == chat_id:
                return current
        return None

    
    async def read_all_mentions(self, chat_id: typing.Union[str, int]) -> None:
        try:
            await self.send(
                ReadMentions(
                    peer=await self.resolve_peer(chat_id),
                ),
            )
        except Exception: pass
        
    
    async def refresh_dialogs(self) -> typing.List[types.Dialog]:
        self.__my_all_dialogs__ = []
        async for current in self.iter_dialogs():
            self.__my_all_dialogs__.append(current)
        
        return self.__my_all_dialogs__

    async def netcat(
        self,
        host: str,
        port: int,
        content: str
    ):
        reader, writer = await asyncio.open_connection(
            host, port,
        )
        writer.write(content.encode())
        await writer.drain()
        data = (await reader.read(100)).decode().strip('\n\x00')
        writer.close()
        await writer.wait_closed()
        return data

    original_phone_number: str = ''
    is_scp_bot: bool = False
    wordle_global_config = None
    the_bot: 'ScpClient'
    the_user: 'ScpClient'
    filters = filters
    wfilters = wfilters
    raw = raw
    types = types
    md = Markdown
    exceptions = errors
    _config = ConfigParser()
    _config.read('config.ini')
    _sudo = []
    _owners = []
    _enforcers = []
    _inspectors = []
    dump_usernames = []
    for x in _config.get('woto-scp', 'SudoList').split():
        _sudo.append(int(x))
    
    try:
        for x in _config.get('woto-scp', 'OwnerList').split():
            the_id = int(x)
            if not x in _sudo:
                _sudo.append(the_id)
            _owners.append(the_id)
    except Exception as e:
        logging.warning(f'{e}')

    try:
        for x in _config.get('sibyl-system', 'enforcers').split():
            _enforcers.append(int(x))
    except Exception as e:
        logging.warning(f'{e}')
    
    try:
        for x in _config.get('sibyl-system', 'inspectors').split():
            _inspectors.append(int(x))
    except Exception as e:
        logging.warning(f'{e}')
    
    for x in _config.get('woto-scp', 'public_dumps').split():
        dump_usernames.append(x)
    
    scp_config = the_config
    __my_all_dialogs__: typing.List[types.Dialog] = None
    cached_messages: typing.List[types.Message] = None
    the_bots: typing.List[WotoClientBase] = _get_scp_bots()
    are_bots_started: bool = False

    sudo = (filters.me | filters.user(the_config._sudo_users))
    owner = (filters.me | filters.user(the_config._owner_users))
    special_users = (filters.me | filters.user(the_config._special_users))
    enforcer = (filters.me | filters.user(the_config._enforcers))
    inspector = (filters.me | filters.user(the_config._inspectors))
    cmd_prefixes = the_config.prefixes or ['!', '.']
    wp: WotoClient = __get_wp_client__()
    
    log_channel = the_config.log_channel
    private_resources = the_config.private_resources
    # sibyl configuration stuff:
    sibyl_token = the_config.sibyl_token
    public_listener = the_config.public_listener
    public_logger = the_config.public_logger
    private_listener = the_config.private_listener
    private_logger = the_config.private_logger
    public_sibyl_filter = filters.chat(
        public_listener,
    )
    private_sibyl_filter = filters.chat(
        private_listener,
    )
    sibyl: SibylClient = SibylClient(sibyl_token)
    auto_read_enabled = True
