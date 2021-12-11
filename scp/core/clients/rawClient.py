from pyrogram import Client, filters, types, raw, errors, session
from scp.core.filters.Command import command
from scp.utils import wfilters
from scp.utils.sibylUtils import SibylClient
from scp.utils.misc import restart_scp as restart_woto_scp
from configparser import ConfigParser
from kantex import md as Markdown
from aiohttp import ClientSession, client_exceptions
import asyncio
import logging

session.Session.notice_displayed = True

class ScpClient(Client):
    def __init__(
        self,
        name: str,
        is_scp_bot: bool = True,
        the_scp_bot: 'ScpClient' = None
    ):
        self.name = name
        super().__init__(
            name,
            workers=8,
        )
        self.aioclient:ClientSession = ClientSession()
        self.is_scp_bot = is_scp_bot
        if is_scp_bot:
            self.the_bot = self
        else:
            the_scp_bot.the_user = self
            self.the_bot = the_scp_bot

    async def start(self):
        await super().start()
        logging.warning(
            f'logged in as {(await super().get_me()).first_name}.',
        )

    async def stop(self, block: bool = True):
        logging.warning(
            f'logged out from {(await super().get_me()).first_name}.',
        )
        await super().stop(block)

    def command(self, *args, **kwargs):
        return command(*args, **kwargs)

    async def send(
        self,
        data: raw.core.TLObject,
        retries: int = session.Session.MAX_RETRIES,
        timeout: float = session.Session.WAIT_TIMEOUT,
        sleep_threshold: float = None
    ):
        try:
            return await super().send(
                data=data,
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
            await asyncio.sleep(e.x)
            return await super().send(
                data=data,
                retries=retries,
                timeout=timeout,
                sleep_threshold=sleep_threshold,
            )

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
    
    async def exit_scp(self):
        await self.stop_scp()
        exit()
    
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
    for x in _config.get('scp-5170', 'SudoList').split():
        _sudo.append(int(x))
    try:
        for x in _config.get('scp-5170', 'OwnerList').split():
            _owners.append(int(x))
    except Exception as e:
        logging.warning(f'{e}')


    

    sudo = (filters.me | filters.user(_sudo))
    owner = (filters.me | filters.user(_owners))
    cmd_prefixes = _config.get('scp-5170', 'prefixes').split() or ['!', '.']
    
    log_channel = _config.getint('scp-5170', 'LogChannel')
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
