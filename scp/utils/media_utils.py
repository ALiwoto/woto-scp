import asyncio
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

math.abs = abs
math.min = min
math.max = max

class BaseContainer:
    length: int = 0
    """Base class for all containers"""
    pass

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

class NcInfoContainer(BaseContainer):
    initial_url: str = None
    parsed_url: UrlParseResult = None
    target_url: str = ""
    origin_target_url: str = ""
    url_qs = None
    app_data: str = ""
    platform: str = ""
    app_version: str = ""
    app_refresher_obj: object = None
    app_refresher: Callable = None
    src_url: str = ""
    click_amount = 14
    max_fail_amount = 16

    logger = logging.getLogger("NcInfoContainer")

    pe_token: str = None
    access_token: str = None
    refresh_token: str = None
    last_q: str = None
    last_q_answer: str = None
    log_q_answers: bool = True
    log_balance: bool = True
    last_click_data: dict = None

    http_client: httpx.AsyncClient = None
    x_requested_with: str = "org.telegram.messenger.web"

    is_task_started: bool = False
    is_cancel_requested: bool = False
    is_task_completed: bool = False
    task_finished_reason: str = None

    def __init__(self, 
        url: str, 
        refresher_obj: object = None,
        refresher: Callable = None,
        src_url: str = ""
    ) -> None:
        self.parse_url_stuff(url)
        self.app_refresher_obj = refresher_obj
        self.app_refresher = refresher
        self.src_url = src_url
        self.http_client = httpx.AsyncClient()
    
    async def refresh_container(self):
        refresher_result = await self.app_refresher(self.src_url)
        the_url = getattr(refresher_result, "url", None)
        if not the_url:
            self.parse_url_stuff(self.src_url)
        
        # do not allow the start task to start its own loop,
        # because refresh_container might be called from within a loop
        # itself. Starting a loop after this is up to the caller.
        await self._start_task(no_loop=True)


    def parse_url_stuff(self, url: str):
        self.initial_url = url
        self.parsed_url = urlparse(url)
        self.url_qs = parse_qs(self.parsed_url.fragment)
        self.target_url = f"{self.parsed_url.scheme}://{self.parsed_url.hostname}"
        self.origin_target_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        self.app_data = self.url_qs['tgWebAppData'][0]
        self.platform = self.url_qs['tgWebAppPlatform'][0]
        self.app_version = self.url_qs['tgWebAppVersion'][0]

    async def aclose(self):
        await self.http_client.aclose()
    
    def __str__(self) -> str:
        if self.is_cancel_requested:
            return "Being canceled NcContainer"
        elif self.is_task_completed:
            return f"Completed NcContainer {self.task_finished_reason}"
        elif self.last_click_data:
            return f"Running NcContainer {self.last_click_data[0]['availableCoins']}"
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

    async def start_task(self):
        try:
            return await self._start_task()
        except Exception as e:
            return self.mark_as_incomplete(f'failed to start task: {e}')
        
    async def _start_task(self, no_loop: bool = False):
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
                available_bl = click_data[0]['availableCoins']
                limit_bl = click_data[0]['limitCoins']
                self.last_click_data = click_data
                if self.log_balance:
                    logging.info(f"balance: {click_data[0]['balanceCoins']} | {available_bl}")
                
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
                failed_count += 1
                if self.app_refresher:
                    await self.refresh_container()
                
                await asyncio.sleep(10)

    async def do_click(
        self, 
        amount: int = 300, 
        q_response: int = None,
        retry_times: int = 3
    ):
        for _ in range(retry_times):
            last_ex = None
            try:
                return await self._do_click(
                    amount=amount,
                    q_response=q_response
                )
            except Exception as ex:
                last_ex = ex
        raise last_ex
        
    async def _do_click(self, amount: int = 300, q_response: int = None):
        if q_response:
            self.last_q_answer = q_response
        
        req_data = {"amount": amount, "webAppData": self.app_data}
        if self.last_q_answer:
            req_data["hash"] = self.last_q_answer
        
        data = json.dumps(req_data)
        response = await self.invoke_request(
            "clicker/core/click",
            data=data,
            token=self.access_token,
            override_host="clicker-api.joincommunity.xyz",
            override_url="https://clicker-api.joincommunity.xyz"
        )
        j_data = json.loads(response)
        if not j_data['ok']:
            raise ValueError(f"failed to do click: {j_data}")
        
        self.last_q = base64.b64decode(j_data["data"][0]["hash"][0]).decode("utf-8")
        try:
            self.last_q_answer = self.calculate_q_answer(self.last_q)
            if self.log_q_answers:
                self.logger.info(f"q: {self.last_q}, answer: {self.last_q_answer}")
        except Exception as e:
            print(f"failed to calculate q answer: {e}")
            # return self.mark_as_incomplete(f'failed to calculate q answer: {e}')
            print(f"q is : {self.last_q}")
        
        return j_data["data"]
    
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
        return response.decode("utf-8")
    
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
        j_resp = json.loads(response)
        if j_resp['ok'] == False:
            return self.mark_as_incomplete(f'failed to authorize client: {j_resp}')
        
        self.access_token = j_resp['data']['accessToken']
        self.refresh_token = j_resp['data']['refreshToken']
        return j_resp['data']

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
        response.raise_for_status()
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
            'Content-Type': 'application/json',
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
        
        response = await self.http_client.post(
            f"{override_url if override_url else self.target_url}/{path}", data=data_value, headers=headers)
        response.raise_for_status()
        return response.content

    async def invoke_get_request(
        self, 
        path: str,
        override_url: str = None,
        if_non_match: str = None,
        dest_value: str = None,
    ):
        headers = {
            'Host': f"{self.parsed_url.hostname}",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; google Pixel 2 Build/LMY47I; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36',
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
        }

        if if_non_match:
            headers['If-None-Match'] = if_non_match

        response = await self.http_client.get(
            f"{override_url if override_url else self.target_url}/{path}", 
            headers=headers
        )
        response.raise_for_status()
        return response.content

    async def cancel_task(self):
        self.is_cancel_requested = True
        while not self.is_task_completed:
            await asyncio.sleep(0.5)
    
    def mark_as_incomplete(self, reason: str):
        self.is_task_completed = True
        self.is_cancel_requested = False
        self.task_finished_reason = reason
        # TODO: use some loggings here in future
