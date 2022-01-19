import typing
import json
from typing import(
    NoReturn, 
    Union,
)
from pyrogram import(
    filters, 
    types, 
    raw, 
    errors, 
)
from wotoplatform import WotoClient
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
                    session_name=':memory:',
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
            session_name=name,
            api_id=the_config.api_id,
            api_hash=the_config.api_hash,
            workers=8,
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
        until_date: int = 0,
    ) -> Union["types.Message", bool]:
        return await super().ban_chat_member(chat_id, user_id, until_date=until_date)
    
    async def kick_chat_member(
        self, 
        chat_id: Union[int, str], 
        user_id: Union[int, str], 
        until_date: int = 0,
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
    for x in _config.get('scp-5170', 'SudoList').split():
        _sudo.append(int(x))
    
    try:
        for x in _config.get('scp-5170', 'OwnerList').split():
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
    
    for x in _config.get('scp-5170', 'public_dumps').split():
        dump_usernames.append(x)
    

    the_bots: typing.List[WotoClientBase] = _get_scp_bots()
    are_bots_started: bool = False

    sudo = (filters.me | filters.user(_sudo))
    owner = (filters.me | filters.user(_owners))
    enforcer = (filters.me | filters.user(_enforcers))
    inspector = (filters.me | filters.user(_inspectors))
    cmd_prefixes = _config.get('scp-5170', 'prefixes').split() or ['!', '.']
    wp: WotoClient = __get_wp_client__()
    
    log_channel = _config.getint('scp-5170', 'LogChannel')
    private_resources = _config.getint('scp-5170', 'private_resources')
    # sibyl configuration stuff:
    sibyl_token = _config.get('sibyl-system', 'token')
    public_listener = _config.getint('sibyl-system', 'public_listener')
    public_logger = _config.get('sibyl-system', 'public_logger')
    private_listener = _config.get('sibyl-system', 'private_listener')
    private_logger = _config.get('sibyl-system', 'private_logger')
    public_sibyl_filter = filters.chat(
        public_listener,
    )
    private_sibyl_filter = filters.chat(
        private_listener,
    )
    sibyl: SibylClient = SibylClient(sibyl_token)
    auto_read_enabled = True
