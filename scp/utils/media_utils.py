import asyncio
import time
from typing import Callable
from urllib.parse import (
    parse_qs, 
    urlparse, 
    ParseResult as UrlParseResult
)
import random
import base64
import httpx
import json
import math
import logging
import subprocess
from scp.woto_config import the_config

math.abs = abs
math.min = min
math.max = max

def run_command(command: str) -> str:
    """Utility function to run commands."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    return output.decode("utf-8")

class BaseContainer:
    length: int = 0
    """Base class for all containers"""
    pass



class BaseTaskContainer(BaseContainer):
    src_url: str = ""
    initial_url: str = None
    parsed_url: UrlParseResult = None
    url_fragments = None
    url_query_params = None
    target_url: str = ""
    origin_target_url: str = ""
    app_data: str = ""
    platform: str = ""
    app_version: str = ""
    app_refresher_obj: object = None
    app_refresher: Callable = None
    http_client: httpx.AsyncClient = None
    x_requested_with: str = "org.telegram.messenger.web"
    x_app: str = "\u0074\u0061\u0070\u0073\u0077\u0061\u0070\u005f\u0073\u0065\u0072\u0076\u0065\u0072"
    x_cv: str = "607"
    user_agent: str = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36'
    sec_ch_ua: str = '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
    sec_ch_ua_mobile: str = "?1"
    sec_ch_ua_platform: str = '"Android"'
    is_authorized: bool = False

    is_task_started: bool = False
    is_cancel_requested: bool = False
    is_task_completed: bool = False
    task_finished_reason: str = None
    running_task: asyncio.Task = None

    read_timeout_reply_delay = 3

    """
    Base task container is a container that can be acted as a "task".
    It can basically manage some related tasks together inside of a container.
    """

    async def cancel_task(self): pass

    async def restart(self): pass

    async def restart(self): pass

    async def aclose(self): pass

    async def refresh_container(self): pass

    def parse_data(self, the_response: bytes): pass

    def __str__(self) -> str: return "NotImplemented BaseTaskContainer"

    async def start_task(self): pass

    def mark_as_incomplete(self, reason: str):
        self.is_task_completed = True
        self.is_cancel_requested = False
        self.task_finished_reason = reason
        # TODO: use some loggings here in future

    def parse_url_stuff(self, url: str):
        self.initial_url = url
        self.parsed_url = urlparse(url)
        self.url_fragments = parse_qs(self.parsed_url.fragment)
        self.url_query_params = parse_qs(self.parsed_url.query)
        self.target_url = f"{self.parsed_url.scheme}://{self.parsed_url.hostname}"
        self.origin_target_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        self.app_data = self.url_fragments['tgWebAppData'][0]
        self.platform = self.url_fragments['tgWebAppPlatform'][0]
        self.app_version = self.url_fragments['tgWebAppVersion'][0]

class PixivIllustInfo:
    is_multiple: bool = False
    meta_pages: list = None

    has_error: bool = False
    error_message: str = None
    user_error_message: str = None
    error_reason: str = None

    def __init__(self, illust_json) -> None:
        if illust_json.error:
            self.has_error = True
            self.error_message = illust_json.error.message
            self.user_error_message = illust_json.error.user_message
            self.error_reason = illust_json.error.reason
            return
        self.is_multiple = illust_json.illust.meta_pages != None \
            and len(illust_json.illust.meta_pages) > 0
        if self.is_multiple:
            self.meta_pages = illust_json.illust.meta_pages

    def get_original_image_url(self) -> str:
        pass

class NcResponseException(Exception):
    message: str = None
    data: str = None
    def __init__(self, message: str, data: str = None) -> None:
        super().__init__(message)
        self.message = message
        self.data = data
        
class NcInfoContainer(BaseTaskContainer):
    click_amount = 300
    max_fail_amount = 8172

    logger = logging.getLogger("NcInfoContainer")
    
    last_pool_data: dict = None
    on_new_pool_data: Callable = None

    pe_token: str = None
    access_token: str = None
    refresh_token: str = None
    last_q: str = None
    last_q_answer: str = None
    log_q_answers: bool = True
    log_balance: bool = True
    last_click_data: dict = None

    def __init__(self, 
        url: str, 
        refresher_obj: object = None,
        refresher: Callable = None,
        src_url: str = "",
        verbose: bool = True
    ) -> None:
        self.parse_url_stuff(url)
        self.app_refresher_obj = refresher_obj
        self.app_refresher = refresher
        self.src_url = src_url
        self.http_client = httpx.AsyncClient()

        if verbose:
            self.logger.setLevel(logging.INFO)
        
    
    async def restart(self):
        return await self.refresh_container(self)
    
    async def refresh_container(self, plain_only: bool = False):
        refresher_result = await self.app_refresher(self.src_url)
        the_url = getattr(refresher_result, "url", None)
        if not the_url:
            self.parse_url_stuff(self.src_url)
        else:
            self.parse_url_stuff(the_url)
        
        if plain_only:
            self.refresh_token = None
            self.access_token = None
            await self.authorize_client(token=None)
        else:
            # do not allow the start task to start its own loop,
            # because refresh_container might be called from within a loop
            # itself. Starting a loop after this is up to the caller.
            await self._start_click_task(no_loop=True)


    async def aclose(self):
        await self.http_client.aclose()
    
    def __str__(self) -> str:
        if self.is_cancel_requested:
            return "Being canceled NcContainer"
        elif self.is_task_completed:
            return f"Completed NcContainer {self.task_finished_reason}"
        elif self.last_click_data:
            return f"Running NcContainer {self.last_click_data['availableCoins']}"
        else:
            return "Running NcContainer"
    
    def find_pe_token(self, content: str) -> str:
        all_lines = content.split("\n")
        correct_line: str = None
        for line in all_lines:
            if line.find("petok") != -1:
                correct_line = line
                break
        
        if not correct_line:
            return None
        
        self.pe_token = correct_line.split("=")[1].strip().split('"')[1]
    
    def parse_data(self, the_response: bytes, flatten: bool = False):
        if not the_response:
            return None
        
        try:
            if the_response.decode("utf-8") == "ok":
                return True
        except: pass
        
        j_resp = json.loads(the_response)
        if not j_resp['ok']:
            if j_resp["data"]["message"]:
                raise NcResponseException(f"{j_resp['data']['message']}", the_response)
            raise NcResponseException(f"failed to activate turbo", the_response)
        
        if isinstance(j_resp['data'], list) \
            and flatten \
            and len(j_resp['data']) == 1:
            return j_resp['data'][0]
        else:
            return j_resp['data']
    
    async def activate_turbo(self):
        return await self.active_turbo()
    
    async def active_turbo(self):
        await self.invoke_options_request(
            path="clicker/core/active-turbo",
            future_method="POST",
            needed_header="auth,authorization",
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )

        response = await self.invoke_request(
            path="clicker/core/active-turbo",
            data="",
            token=self.access_token,
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )

        return self.parse_data(response)

    async def start_click_task(self):
        try:
            return await self._start_task()
        except Exception as e:
            return self.mark_as_incomplete(f'failed to start task: {e}')
        
    async def _start_click_task(self, no_loop: bool = False):
        index_content = await self.invoke_get_request(self.parsed_url.path)
        if not index_content:
            return self.mark_as_incomplete('failed to get index content')
        
        try:
            self.find_pe_token(index_content.decode("utf-8"))
        except Exception as e:
            self.logger.warning(f"failed to load pe token: {e}")
            # return self.mark_as_incomplete(f'failed to find pe token: {e}')

        await self.notify_api_event()
        # authorize the client
        await self.authorize_client(token=self.refresh_token)

        if no_loop:
            return
        
        failed_count = -1
        while not self.is_cancel_requested and not self.is_task_completed:
            if failed_count > self.max_fail_amount:
                return self.mark_as_incomplete("Too many failed attempts to click. Stopping.")
            
            try:
                # do the job here
                click_data = await self.do_click(amount=self.click_amount)
                available_bl = click_data['availableCoins']
                limit_bl = click_data['limitCoins']
                self.last_click_data = click_data
                if self.log_balance:
                    logging.info(f"balance: {click_data['balanceCoins']} | {available_bl}")
                
                if available_bl < self.click_amount:
                    await asyncio.sleep(60)
                elif available_bl < 1000:
                    if limit_bl > 2000:
                        await asyncio.sleep(60)
                    await asyncio.sleep(20)
                
                failed_count = 0
                await asyncio.sleep(30)
            except httpx.ReadTimeout:
                # read timeouts aren't important much, retry after few seconds...
                await asyncio.sleep(3)
                continue
            except Exception as ex:
                logging.warning(f"failed to do click: {ex}")
                if getattr(ex, "message", "").find("Try later") != -1:
                    await asyncio.sleep(60)
                    continue

                failed_count += 1
                if failed_count % 5 == 0:
                    await self.refresh_container()
                
                await asyncio.sleep(20)

    async def start_pool_check_task(self):
        try:
            return await self._start_pool_check_task()
        except Exception as e:
            return self.mark_as_incomplete(f'failed to start pool check task: {e}')
    
    async def _start_pool_check_task(self, no_loop: bool = False):
        # await self.notify_api_event()
        # authorize the client
        await self.authorize_client(token=self.refresh_token)

        if no_loop:
            return
        
        while not self.is_cancel_requested and not self.is_task_completed:
            try:
                pool_data = await self.get_my_pool()
                if not pool_data:
                    await asyncio.sleep(60)
                    self.logger.warning("pool data is None")
                    continue

                self.last_pool_data = pool_data
                if self.on_new_pool_data:
                    logging.info("invoking on_new_pool_data callback...")
                    await self.on_new_pool_data(pool_data)
                await asyncio.sleep(60)
            except Exception as ex:
                if f"{ex}".lower().find("unauthorized") != -1:
                    logging.info("unauthorized, refreshing...")
                    await self.refresh_container(plain_only=True)
                    await asyncio.sleep(5)
                    continue
                logging.warning(f"failed to check pool: {ex}")
                await asyncio.sleep(60)
    
    async def get_my_pool(self) -> dict:
        if not self.is_authorized:
            await self.authorize_client(token=self.refresh_token)
        
        response = await self.invoke_get_request(
            path="pool/my",
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )
        j_resp = self.parse_data(response)
        
        # note: parse_data method already checks for errors
        # and only returns the "data" field.
        if not j_resp:
            raise NcResponseException("failed to get my pool", response)
        
        return j_resp

    async def do_click(
        self, 
        amount: int = 300, 
        q_response: int = None,
        retry_times: int = 3,
        is_turbo: bool = False,
    ):
        for _ in range(retry_times):
            last_ex = None
            try:
                return await self._do_click(
                    amount=amount,
                    q_response=q_response,
                    is_turbo=is_turbo,
                )
            except Exception as ex:
                last_ex = ex
        raise last_ex
        
    async def _do_click(
        self, 
        amount: int = 300, 
        q_response: int = None,
        is_turbo: bool = False,
    ):
        if q_response:
            self.last_q_answer = q_response
        
        req_data = {"amount": amount, "webAppData": self.app_data}
        if self.last_q_answer:
            req_data["hash"] = self.last_q_answer
        if is_turbo:
            req_data["turbo"] = True
        
        data = json.dumps(req_data)
        response = await self.invoke_request(
            "clicker/core/click",
            data=data,
            token=self.access_token,
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )
        j_data = self.parse_data(response)
        
        self.last_q = base64.b64decode(j_data["hash"][0]).decode("utf-8")
        try:
            self.last_q_answer = self.calculate_q_answer(self.last_q)
            if self.log_q_answers:
                self.logger.info(f"q: {self.last_q}, answer: {self.last_q_answer}")
        except Exception as e:
            print(f"failed to calculate q answer: {e}")
            # return self.mark_as_incomplete(f'failed to calculate q answer: {e}')
            print(f"q is : {self.last_q}")
        
        return j_data
    
    def calculate_q_answer(self, q: str) -> int:
        lowered_q = q.lower()
        if lowered_q.find("math") != -1:
            return eval(lowered_q)
        elif q.find("window.location.host") != -1 or \
            q.find("initDataUnsafe") != -1 or \
            q.find("new Date")!= -1:
            return int(q.split("?")[1].split(":")[0].strip())
        elif q.find("document.querySelectorAll") != -1:
            # a random number
            return random.randint(126, 349)

    async def notify_api_event(self):
        resp = await self.invoke_get_request("assets/vendor-28842ac8.js", dest_value="script")
        resp = await self.invoke_get_request("assets/index-eaf7a2bd.js", dest_value="script")
        resp = await self.invoke_get_request("assets/index-876b7b94.css", dest_value="style")
        # resp = await self.invoke_get_request(
        #     "beacon.min.js",
        #     override_url="https://static.cloudflareinsights.com",
        #     dest_value="script"
        # )
        # resp = await self.invoke_get_request(
        #     "beacon.min.js/v84a3a4012de94ce1a686ba8c167c359c1696973893317", 
        #     override_url="https://static.cloudflareinsights.com",
        #     dest_value="script"
        # )

        data = json.dumps({
            "n": "pageview", 
            "u": self.initial_url, 
            "d": f"{self.parsed_url.hostname}",
            "r": None
        })
        response = await self.invoke_request(
            "api/event", 
            data=data, 
            override_host="plausible.joincommunity.xyz",
            override_url="https://plausible.joincommunity.xyz",
        )
        return self.parse_data(response)
    
    async def authorize_client(self, token: str = None):
        # need to request access to the method first
        await self.invoke_options_request(
            path="auth/webapp-session",
            future_method="POST",
            needed_header="auth,authorization,content-type",
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )

        data = json.dumps({"webAppData": self.app_data})
        response = await self.invoke_request(
            "auth/webapp-session", 
            data=data,
            token=token,
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )
        j_resp = self.parse_data(response)
        
        self.access_token = j_resp['accessToken']
        self.refresh_token = j_resp['refreshToken']
        self.is_authorized = True
        return j_resp

    async def invoke_options_request(
        self, 
        path: str, 
        future_method: str,
        needed_header: str = None,
        override_host: str = None,
        override_url: str = None,
    ):
        path = path.rstrip('/')
        headers = {
            'Host': f"{override_host if override_host else self.parsed_url.hostname}",
            'Accept': '*/*',
            'Access-Control-Request-Method': future_method,
            'Access-Control-Request-Headers': needed_header,
            'Origin': f'{self.origin_target_url}',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; google Pixel 2 Build/LMY47I; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36',
            'Sec-Fetch-Mode': 'cors',
            "X-Requested-With": self.x_requested_with,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f'{self.origin_target_url}/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.9',
        }
        response = await self.http_client.options(
            f"{override_url if override_url else self.target_url}/{path}", headers=headers)
        # response.raise_for_status()
        return response.content

    async def invoke_request(
        self, 
        path: str, 
        data: str, 
        token: str = None,
        override_host: str = None,
        override_url: str = None,
    ):
        path = path.rstrip('/')
        data_value = data.encode('utf-8')
        headers = {
            'Host': override_host if override_host else f"{self.parsed_url.hostname}",
            'Content-Length': str(len(data_value)),
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; google Pixel 2 Build/LMY47I; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36',
            'Auth': '1',
            'Origin': f'{self.origin_target_url}',
            "X-Requested-With": self.x_requested_with,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f'{self.origin_target_url}/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.9',
        }

        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if data:
            headers['Content-Type'] = 'application/json'
        
        response = await self.http_client.post(
            f"{override_url if override_url else self.target_url}/{path}", data=data_value, headers=headers)
        # response.raise_for_status()
        return response.content

    async def invoke_get_request(
        self, 
        path: str,
        override_host: str = None,
        override_url: str = None,
        if_non_match: str = None,
        dest_value: str = None,
        accept_value: str = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    ):
        headers = {
            'Host': f"{override_host if override_host else self.parsed_url.hostname}",
            'Accept': accept_value,
            'User-Agent': self.user_agent,
            'Auth': '1',
            'Content-Type': 'application/json',
            'Origin': f'{self.origin_target_url}',
            "X-Requested-With": self.x_requested_with,
            'Sec-Ch-Ua': self.sec_ch_ua,
            'Sec-Ch-Ua-Mobile': self.sec_ch_ua_mobile,
            'Sec-Ch-Ua-Platform': self.sec_ch_ua_platform,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': dest_value if dest_value else 'document',
            'Referer': f'{self.origin_target_url}/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.9',
            'Connection': 'close',
        }

        if if_non_match:
            headers['If-None-Match'] = if_non_match
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'

        response = await self.http_client.get(
            f"{override_url if override_url else self.target_url}/{path}", 
            headers=headers
        )
        if response.status_code != 200:
            raise NcResponseException(f"failed to get response from {path}", response.content)
        
        return response.content

    async def cancel_task(self):
        self.is_cancel_requested = True
        if self.running_task:
            self.running_task.cancel()
            self.is_task_completed = True
        else:
            # old way of doing things
            while not self.is_task_completed:
                await asyncio.sleep(0.5)
    

class TpsInfoContainer(BaseTaskContainer):
    click_amount: int = 40
    click_rand_diff: int = 20
    max_fail_amount: int = 8172
    after_login_delay: int = 4

    logger = logging.getLogger("TpsInfoContainer")

    player_info: dict = None
    account_info: dict = None
    config_info: dict = None
    user_settings: dict = None
    bot_key = "\u0061\u0070\u0070\u005f\u0062\u006f\u0074\u005f\u0030"

    access_token: str = None

    log_balance: bool = True
    last_click_data: dict = None


    def __init__(self, 
        url: str, 
        refresher_obj: object = None,
        refresher: Callable = None,
        src_url: str = "",
        verbose: bool = True
    ) -> None:
        self.parse_url_stuff(url)
        self.app_refresher_obj = refresher_obj
        self.app_refresher = refresher
        self.src_url = src_url
        self.http_client = httpx.AsyncClient()

        if verbose:
            self.logger.setLevel(logging.INFO)
        
        if self.url_query_params and self.url_query_params["bot"]:
            self.bot_key = self.url_query_params["bot"][0x0]

    async def start_task(self):
        try:
            return await self._start_task()
        except Exception as e:
            return self.mark_as_incomplete(f'failed to start task: {e}')

    async def _start_task(self, no_loop: bool = False):
        index_content = await self.invoke_get_request(self.parsed_url.path)
        if not index_content:
            return self.mark_as_incomplete('failed to get index content')
        
        login_resp = await self.login_client()
        if not login_resp:
            raise NcResponseException("login response is none!")
        
        self.player_info = login_resp["player"]
        self.account_info = login_resp["account"]
        self.config_info = login_resp["conf"]

        if no_loop:
            return

        # after a fresh login, wait for few seconds before clicking,
        # so our activity doesn't look suspicious perhaps
        await asyncio.sleep(self.after_login_delay)
        failed_count = -1
        while not self.is_cancel_requested and not self.is_task_completed:
            if failed_count > self.max_fail_amount:
                return self.mark_as_incomplete("Too many failed attempts to click. Stopping.")
            
            try:
                chosen_click_amount = random.randint(
                    self.click_amount - self.click_rand_diff, self.click_amount + self.click_rand_diff)
                available_bl = self.player_info["energy"]
                if available_bl < (chosen_click_amount * self.player_info["tap_level"]):
                    await asyncio.sleep(20)
                
                # do the job here
                click_data = await self.do_click(amount=chosen_click_amount)
                player_info = click_data.get("player", None)
                if player_info:
                    self.player_info = player_info
                    available_bl = self.player_info["energy"]
                else:
                    raise Exception("returned player_info from do_click is None!")

                self.last_click_data = click_data
                if self.log_balance:
                    self.logger.info(f"(clicked {chosen_click_amount} times) balance: {self.player_info['shares']} | {available_bl}")
                
                if available_bl < self.click_amount * self.player_info["tap_level"]:
                    await asyncio.sleep(60)
                elif available_bl < 1000:
                    await asyncio.sleep(20)
                
                failed_count = 0
                await asyncio.sleep(30)
            except httpx.ReadTimeout:
                # read timeouts aren't important much, retry after few seconds...
                self.logger.info(f"got ReadTimeout, retrying after {self.read_timeout_reply_delay} seconds...")
                await asyncio.sleep(self.read_timeout_reply_delay)
                continue
            except Exception as ex:
                logging.warning(f"failed to do click: {ex}")
                if getattr(ex, "message", "").find("Try later") != -1:
                    await asyncio.sleep(60)
                    continue

                failed_count += 1
                if failed_count % 5 == 0:
                    await self.refresh_container()
                
                await asyncio.sleep(20)

    async def refresh_container(self):
        refresher_result = await self.app_refresher(self.src_url)
        the_url = getattr(refresher_result, "url", None)
        if not the_url:
            self.parse_url_stuff(self.src_url)
        else:
            self.parse_url_stuff(the_url)
        
        # do not allow the start task to start its own loop,
        # because refresh_container might be called from within a loop
        # itself. Starting a loop after this is up to the caller.
        await self._start_task(no_loop=True)

    async def do_click(
        self, 
        amount: int = 220, 
        retry_times: int = 3,
        is_turbo: bool = False,
    ):
        for _ in range(retry_times):
            last_ex = None
            try:
                return await self._do_click(
                    amount=amount,
                    is_turbo=is_turbo,
                )
            except Exception as ex:
                if f"{ex}".lower().find("unauthorized") != -1:
                    await self.refresh_container()
                    await asyncio.sleep(5)
                    continue
                last_ex = ex
        raise last_ex
        
    async def _do_click(
        self, 
        amount: int = 300, 
        is_turbo: bool = False,
    ):
        await self.invoke_options_request(
            path="api/player/submit_taps",
            future_method="POST",
            needed_header="authorization,content-id,content-type,x-app,x-cv",
            override_host="api.tapswap.ai",
            override_url="https://api.tapswap.ai",
        )

        current_time = time.time_ns() // 1_000_000
        req_data = {"taps": amount, "time": current_time}
        if is_turbo:
            req_data["turbo"] = True
        
        data = json.dumps(req_data)
        response = await self.invoke_request(
            "api/player/submit_taps",
            data=data,
            token=self.access_token,
            override_host="api.tapswap.ai",
            override_url="https://api.tapswap.ai",
            content_id=self.get_content_id(self.player_info["id"], current_time)
        )
        j_data = self.parse_data(response)
        
        # if there is any q_param, the q_answer should be
        # calculated here.

        return j_data
    
    def get_content_id(self, player_id: int, current_time: int) -> str:
        return str(int(float(player_id) * float(current_time) % float(player_id)))
    
    def parse_data(self, the_response: bytes):
        if not the_response:
            return None
        
        try:
            if the_response.decode("utf-8") == "ok":
                return True
        except: pass
        
        j_resp: dict = json.loads(the_response)
        status_code = j_resp.get("statusCode", None)
        if status_code and status_code != 200:
            resp_message = j_resp.get("message", None)
            if resp_message:
                raise NcResponseException(resp_message, the_response)
            raise NcResponseException(f"failed to parse response data", the_response)
        
        return j_resp
    

    async def login_client(self, token: str = None):
        data = json.dumps({
            "init_data": self.app_data,
            "bot_key": self.bot_key,
            "referrer": "",
        })
        response = await self.invoke_request(
            "api/account/login", 
            data=data,
            token=token,
            override_host="api.tapswap.ai",
            override_url="https://api.tapswap.ai"
        )
        j_resp = self.parse_data(response)
        
        self.access_token = j_resp['access_token']
        return j_resp

    async def invoke_options_request(
        self, 
        path: str, 
        future_method: str,
        needed_header: str = None,
        override_host: str = None,
        override_url: str = None,
    ):
        path = path.rstrip('/')
        headers = {
            'Host': f"{override_host if override_host else self.parsed_url.hostname}",
            'Accept': '*/*',
            'Access-Control-Request-Method': future_method,
            'Access-Control-Request-Headers': needed_header,
            'Origin': f'{self.origin_target_url}',
            'User-Agent': self.user_agent,
            'Sec-Fetch-Mode': 'cors',
            "X-Requested-With": self.x_requested_with,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f'{self.origin_target_url}/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.9',
            'X-App': self.x_app,
            'X-CV': self.x_cv,
            'X-Cv': '1',
            'Sec-Ch-Ua': self.sec_ch_ua,
            'Sec-Ch-Ua-Mobile': self.sec_ch_ua_mobile,
            'Sec-Ch-Ua-Platform': self.sec_ch_ua_platform,
        }
        response = await self.http_client.options(
            f"{override_url if override_url else self.target_url}/{path}", headers=headers)
        # response.raise_for_status()
        return response.content

    async def aclose(self):
        await self.http_client.aclose()
    
    def __str__(self) -> str:
        if self.is_cancel_requested:
            return "Being canceled TpsInfoContainer"
        elif self.is_task_completed:
            return f"Completed TpsInfoContainer {self.task_finished_reason}"
        elif self.last_click_data:
            return f"Running TpsInfoContainer {self.last_click_data['shares']}"
        else:
            return "Running TpsInfoContainer"
    
    async def invoke_request(
        self, 
        path: str, 
        data: str, 
        token: str = None,
        override_host: str = None,
        override_url: str = None,
        content_id: str = None,
    ):
        path = path.rstrip('/')
        data_value = data.encode('utf-8')
        headers = {
            'Host': override_host if override_host else f"{self.parsed_url.hostname}",
            'Content-Length': str(len(data_value)),
            'Accept': 'application/json',
            'User-Agent': self.user_agent,
            'Auth': '1',
            'Origin': f'{self.origin_target_url}',
            "X-Requested-With": self.x_requested_with,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f'{self.origin_target_url}/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.9',
            'X-App': self.x_app,
            'X-CV': self.x_cv,
            'Sec-Ch-Ua': self.sec_ch_ua,
            'Sec-Ch-Ua-Mobile': self.sec_ch_ua_mobile,
            'Sec-Ch-Ua-Platform': self.sec_ch_ua_platform,
        }

        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if content_id:
            headers['Content-Id'] = content_id
        
        if data:
            headers['Content-Type'] = 'application/json'
        
        response = await self.http_client.post(
            f"{override_url if override_url else self.target_url}/{path}", data=data_value, headers=headers)
        # response.raise_for_status()
        return response.content

    async def invoke_get_request(
        self, 
        path: str,
        override_url: str = None,
        if_non_match: str = None,
        dest_value: str = None,
        content_id: str = None,
    ):
        headers = {
            'Host': f"{self.parsed_url.hostname}",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': self.user_agent,
            'Auth': '1',
            'Content-Type': 'application/json',
            'Origin': f'{self.origin_target_url}',
            "X-Requested-With": self.x_requested_with,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': dest_value if dest_value else 'document',
            'Referer': f'{self.origin_target_url}/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.9',
            'Connection': 'close',
            'X-App': self.x_app,
            'X-CV': self.x_cv,
            'Sec-Ch-Ua': self.sec_ch_ua,
            'Sec-Ch-Ua-Mobile': self.sec_ch_ua_mobile,
            'Sec-Ch-Ua-Platform': self.sec_ch_ua_platform,
        }

        if if_non_match:
            headers['If-None-Match'] = if_non_match
        
        if content_id:
            headers['Content-Id'] = content_id

        response = await self.http_client.get(
            f"{override_url if override_url else self.target_url}/{path}", 
            headers=headers
        )
        response.raise_for_status()
        return response.content
    
    async def cancel_task(self):
        self.is_cancel_requested = True
        if self.running_task:
            self.running_task.cancel()
            self.is_task_completed = True
        else:
            # old way of doing things
            while not self.is_task_completed:
                await asyncio.sleep(0.5)
