import asyncio
from enum import Enum
from typing import (
    Dict,
    Union,
    Callable,
    BinaryIO
)
from pyrogram.types import InlineKeyboardMarkup

auto_inline_dict: Dict["str", "AutoInlineContainer"] = {}


class AutoInlineType(Enum):
    TEXT    = 0
    """ normal text message """
    
    PHOTO   = 1
    
    VIDEO   = 2
    GIF     = 3
    VOICE   = 4
    


class AutoInlineContainer:
    unique_id: str = None
    inline_message_type: AutoInlineType = AutoInlineType.TEXT
    text: str = None
    title: str = None
    media_chat_id: Union[str, int] = None
    media_message_id: int = None
    media_path: str = None
    media_url: str = None
    keyboard: InlineKeyboardMarkup = None
    progress: Callable = None
    progress_args: tuple = ()
    ttl_seconds: int = None
    
    cache_time: int = 300
    is_gallery: bool = False
    is_personal: bool = False
    next_offset: str = ""
    switch_pm_text: str = ""
    switch_pm_parameter: str = ""
    __internal_lock: asyncio.Lock = None
        
    def __init__(
        self,
        unique_id: str,
        message_type: AutoInlineType,
        text: str = None,
        title: str = None,
        media_chat_id: Union[str, int] = None,
        media_message_id: int = None,
        media_path: str = None,
        media_url: str = None,
        keyboard: InlineKeyboardMarkup = None,
        progress: Callable = None,
        progress_arg: tuple = (),
        cache_time: int = 0,
        is_gallery: bool = False,
        is_personal: bool = False,
        next_offset: str = "",
        switch_pm_text: str = "",
        switch_pm_parameter: str = ""
    ) -> None:
        self.unique_id = unique_id
        self.inline_message_type = message_type
        self.text = text
        self.title = title
        self.media_chat_id = media_chat_id
        self.media_message_id = media_message_id
        self.media_path = media_path
        self.media_url = media_url
        self.keyboard = keyboard
        self.progress = progress
        self.progress_args = progress_arg
        self.__internal_lock = asyncio.Lock()
        self.cache_time = cache_time
        self.is_gallery = is_gallery
        self.is_personal = is_personal
        self.next_offset = next_offset
        self.switch_pm_text = switch_pm_text
        self.switch_pm_parameter = switch_pm_parameter
    
    async def wait_for_response(self, timeout: int = 6) -> bool:
        try:
            asyncio.wait_for(self.__wait_for_response(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
        
    async def __wait_for_response(self):
        await self.__internal_lock.acquire()
        await self.__internal_lock.acquire()
        self.__internal_lock.release()
    
    def mark_as_done(self):
        self.__internal_lock.release()