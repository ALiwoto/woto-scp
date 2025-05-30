import re
import os
from typing import (
    Union,
    Optional,
    List,
    AsyncGenerator,
    Iterable,
    BinaryIO
)
from aiohttp import ClientSession, client_exceptions
from datetime import datetime
import logging
import asyncio
from traceback import format_exception
from io import BytesIO
import typing
from attrify import Attrify as Atr
from pyrogram.raw.types.web_view_result_url import WebViewResultUrl
from pyrogram.raw.functions.messages import RequestWebView
from pyrogram import (
    Client,
    types,
    raw,
    utils as pUtils,
    enums,
    errors,
    session,
    filters as pyroFilters
)
from pyrogram.errors.exceptions.bad_request_400 import MessageIdInvalid
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.phone import EditGroupCallTitle
from pyrogram.raw.types.messages.chat_full import ChatFull
from pyrogram.raw.types.channel_full import ChannelFull
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.enums.message_media_type import MessageMediaType
from scp.utils.parser import (
    html_mono,
    html_spoiler,
    html_bold,
    html_italic,
    html_link,
    html_pre,
    split_some,
    html_normal,
    html_mention,
    html_normal_chat_link,
    mention_user_html,
    to_output_file,
)
from scp.utils.unpack import (
    unpack_inline_message,
    WebViewResultContainer,
)

scp_loop = asyncio.get_event_loop()

def get_aio_client() -> ClientSession:
    try:
        return ClientSession(loop=scp_loop)
    except Exception as ex:
        logging.error(f"Failed to get aio-client: {ex}")
        return None

class WotoClientBase(Client):
    HTTP_URL_MATCHING = r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"
    web_platform = "android"
    web_theme = "{\"accent_text_color\":\"#6ab2f2\",\"bg_color\":\"#17212b\",\"button_color\":\"#5288c1\",\"button_text_color\":\"#ffffff\",\"destructive_text_color\":\"#ec3942\",\"header_bg_color\":\"#17212b\",\"hint_color\":\"#708499\",\"link_color\":\"#6ab3f3\",\"secondary_bg_color\":\"#232e3c\",\"section_bg_color\":\"#17212b\",\"section_header_text_color\":\"#6ab3f3\",\"subtitle_text_color\":\"#708499\",\"text_color\":\"#f5f5f5\"}"

    filters = pyroFilters
    __my_all_dialogs__: typing.List[types.Dialog] = None
    aioclient: ClientSession = get_aio_client()

    def is_real_media(self, message: types.Message) -> bool:
        return (message is not None and
                message.media is not None and
                message.media != MessageMediaType.WEB_PAGE)
    
    def fix_eval_text(self, txt: str) -> str:
        if txt[1:].startswith("eval"):
            txt = txt[1:].lstrip("eval")
        
        # remove all non-printable characters from the code.
        return txt.replace("\u00A0", " ").strip()

    def remove_file(self, file_name: str) -> None:
        try:
            os.remove(file_name)
        except Exception:
            return None
    
    async def forward_messages(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_ids: Union[int, Iterable[int]],
        message_thread_id: int = None,
        disable_notification: bool = None,
        schedule_date: datetime = None,
        hide_sender_name: bool = None,
        hide_captions: bool = None,
        protect_content: bool = None,
        allow_paid_broadcast: bool = None
    ) -> Union["types.Message", List["types.Message"]]:
        target_chat = await self.get_chat(from_chat_id)
        if not target_chat.has_protected_content:
            try:
                return await super().forward_messages(
                    chat_id=chat_id,
                    from_chat_id=from_chat_id,
                    message_ids=message_ids,
                    message_thread_id=message_thread_id,
                    disable_notification=disable_notification,
                    schedule_date=schedule_date,
                    hide_sender_name=hide_sender_name,
                    hide_captions=hide_captions,
                    protect_content=protect_content,
                    allow_paid_broadcast=allow_paid_broadcast
                )
            except MessageIdInvalid:
                pass # let it pass actually

        is_iterable = not isinstance(message_ids, int)
        message_ids = list(message_ids) if is_iterable else [message_ids]
        all_messages: List[types.Message] = await self.get_messages(
            chat_id=from_chat_id,
            message_ids=message_ids
        )

        message_results: List[types.Message] = []
        for current_message in all_messages:
            if not current_message or current_message.empty:
                continue

            if not self.is_real_media(current_message):
                if not current_message.text:
                    continue

                # just simply send the text message there
                tmp_message = await self.send_message(
                    chat_id=chat_id,
                    text=current_message.text,
                    disable_notification=disable_notification,
                    schedule_date=schedule_date
                )
                message_results.append(tmp_message)
                continue

            # download and send the media
            downloaded_content = await self.download_media(current_message)
            if not downloaded_content:
                continue

            tmp_message = await self.send_specified_media(
                chat_id=chat_id,
                media_type=current_message.media,
                media=downloaded_content,
                caption=current_message.caption,
                caption_entities=current_message.caption_entities,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                protect_content=protect_content,
            )
            message_results.append(tmp_message)
            os.remove(downloaded_content)

        if len(message_results) == 1:
            # return the only message
            return message_results[0]
        return message_results

    async def forward_message_by_link(
        self,
        chat_id: Union[int, str],
        message_link: str,
        message_thread_id: int = None,
        disable_notification: bool = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        allow_paid_broadcast: bool = None
    ) -> Union["types.Message", List["types.Message"]]:
        the_message = await self.get_message_by_link(message_link)
        if not the_message:
            raise ValueError("Invalid message link provided")

        return await self.forward_messages(
            chat_id=chat_id,
            from_chat_id=the_message.chat.id,
            message_ids=the_message.id,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            schedule_date=schedule_date,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast
        )

    async def get_message_by_link(
        self,
        link: str,
        continue_til_found: bool = False,
        chunk_amount: int = 10,
        term_search: str = None,
    ) -> types.Message:
        link = link.replace('telegram.me', 't.me')
        link = link.replace('telegram.dog', 't.me')
        link = link.replace('https://', '')
        link = link.replace('http://', '')

        chat_id = None
        message_id: int = 0
        # the format can be either like t.me/c/123456/1099 or
        # t.me/username/6669424
        if link.find('/c/') != -1:
            my_strs = link.split('/c/')
            if len(my_strs) < 2:
                return None
            my_strs = my_strs[1].split('/')
            if len(my_strs) < 2:
                return None
            
            if not my_strs[0].startswith("-100"):
                chat_id = int('-100' + my_strs[0])
            message_id = int(my_strs[1])
        else:
            my_strs = link.split('/')
            if len(my_strs) == 1:
                if term_search:
                    async for current in self.search_messages(
                        chat_id=my_strs[0],
                        query=term_search,
                        limit=1,
                    ):
                        return current
                return (await self.get_history(
                    chat_id=chat_id,
                    limit=1,
                ))[0]
            if len(my_strs) < 3:
                return None
            
            chat_id = my_strs[1]
            message_id = int(my_strs[2])

        if not chat_id:
            return None

        if not continue_til_found:
            return await self.get_messages(chat_id, message_id)

        messages = await self.get_history(
            chat_id=chat_id,
            limit=1,
        )
        if messages:
            to_id = messages[0].id

        while message_id <= to_id:
            the_messages: typing.List[types.Message] = \
                await self.get_messages(chat_id, [i for i in range(message_id, message_id + chunk_amount)])
            for msg in the_messages:
                if msg and not msg.empty:
                    return msg

            message_id += chunk_amount

        return None

    async def message_has_keyboard(self, message: types.Message):
        return bool(
            getattr(getattr(message, "reply_markup", None), 
                    "inline_keyboard", None))
    
    async def click_web_button_by_url(
        self,
        target_bot: Union[int, str],
        app_url: str,
        platform: str = 'android',
    ) -> WebViewResultUrl:
        raw_bot = await self.resolve_peer(target_bot)
        my_request = RequestWebView(
            peer=raw.types.InputPeerUser(
                user_id=raw_bot.user_id, 
                access_hash=raw_bot.access_hash
            ),
            bot=raw.types.InputUser(
                user_id=raw_bot.user_id,
                access_hash=raw_bot.access_hash
            ),
            platform=platform,
            url=app_url,
            theme_params=raw.types.DataJSON(data=self.web_theme)
        )

        return await self.invoke(my_request)
    
    async def click_web_button_by_message_link(
        self, 
        msg_url: Union[str, types.Message],
        platform: str = 'android',
        term_search: str = None,
    ) -> WebViewResultUrl:
        if isinstance(msg_url, types.Message):
            target_message = msg_url
        else:
            target_message = await self.get_message_by_link(
                link=msg_url,
                term_search=term_search,
            )
        correct_button: types.InlineKeyboardButton = None
        # go through the buttons and find the web app button
        for button in target_message.reply_markup.inline_keyboard:
            for btn in button:
                if btn.web_app:
                    correct_button = btn
                    break

        if not correct_button:
            raise ValueError('No web app button found.')

        raw_bot = await self.resolve_peer(target_message.from_user.id)
        my_request = RequestWebView(
            peer=raw.types.InputPeerUser(
                user_id=raw_bot.user_id, 
                access_hash=raw_bot.access_hash
            ),
            bot=raw.types.InputUser(
                user_id=raw_bot.user_id,
                access_hash=raw_bot.access_hash
            ),
            platform=platform,
            url=correct_button.web_app.url,
            theme_params=raw.types.DataJSON(data=self.web_theme)
        )

        result: WebViewResultUrl = await self.invoke(my_request)
        return WebViewResultContainer(
            query_id=result.query_id,
            url=result.url,
            message=target_message
        )

    async def send_specified_media(
        self,
        chat_id: Union[int, str],
        media: Union[str, bytes, BytesIO],
        media_type: MessageMediaType,
        caption: str = None,
        parse_mode: Union[str, ParseMode] = None,
        caption_entities: List["types.MessageEntity"] = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        reply_to_chat_id: Union[int, str] = None,
        reply_to_story_id: int = None,
        schedule_date: datetime = None,
        reply_markup: "types.InlineKeyboardMarkup" = None,
        progress: callable = None,
        progress_args: tuple = (),
        protect_content: bool = None,
        business_connection_id: str = None,
        effect_id: int = None,
        unsave: bool = False,
        file_name: str = None,
        thumb: str | BinaryIO = None,
        duration: int = 0,
        has_spoiler: bool = None,
        width: int = 0,
        height: int = 0,
        performer: str = None,
        title: str = None,
        force_document: bool = None,
        ttl_seconds: int = None,
        allow_paid_broadcast: bool = None,
    ) -> "types.Message":
        if media_type == MessageMediaType.ANIMATION:
            return await self.send_animation(
                chat_id=chat_id,
                animation=media,
                caption=caption,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                reply_markup=reply_markup,
                progress=progress,
                progress_args=progress_args,
                unsave=unsave,
                file_name=file_name,
                thumb=thumb,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                duration=duration,
                has_spoiler=has_spoiler,
                width=width,
                height=height,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.AUDIO:
            return await self.send_audio(
                chat_id=chat_id,
                audio=media,
                caption=caption,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                caption_entities=caption_entities,
                duration=duration,
                performer=performer,
                file_name=file_name,
                thumb=thumb,
                parse_mode=parse_mode,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                reply_markup=reply_markup,
                progress=progress,
                progress_args=progress_args,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                title=title,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.DOCUMENT:
            return await self.send_document(
                chat_id=chat_id,
                document=media,
                caption=caption,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                caption_entities=caption_entities,
                thumb=thumb,
                file_name=file_name,
                force_document=force_document,
                parse_mode=parse_mode,
                progress=progress,
                progress_args=progress_args,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                reply_markup=reply_markup,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.PHOTO:
            return await self.send_photo(
                chat_id=chat_id,
                photo=media,
                caption=caption,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                has_spoiler=has_spoiler,
                caption_entities=caption_entities,
                parse_mode=parse_mode,
                progress=progress,
                progress_args=progress_args,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                reply_markup=reply_markup,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                ttl_seconds=ttl_seconds,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.VIDEO:
            return await self.send_video(
                chat_id=chat_id,
                video=media,
                caption=caption,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                has_spoiler=has_spoiler,
                caption_entities=caption_entities,
                duration=duration,
                file_name=file_name,
                height=height,
                parse_mode=parse_mode,
                progress=progress,
                progress_args=progress_args,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                reply_markup=reply_markup,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                thumb=thumb,
                ttl_seconds=ttl_seconds,
                width=width,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.VIDEO_NOTE:
            return await self.send_video_note(
                chat_id=chat_id,
                video_note=media,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                duration=duration,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                thumb=thumb,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                progress=progress,
                progress_args=progress_args,
                reply_markup=reply_markup,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.VOICE:
            return await self.send_voice(
                chat_id=chat_id,
                voice=media,
                caption=caption,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                caption_entities=caption_entities,
                duration=duration,
                parse_mode=parse_mode,
                progress=progress,
                progress_args=progress_args,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                reply_markup=reply_markup,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif media_type == MessageMediaType.STICKER:
            return await self.send_sticker(
                chat_id=chat_id,
                sticker=media,
                disable_notification=disable_notification,
                schedule_date=schedule_date,
                progress=progress,
                progress_args=progress_args,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                effect_id=effect_id,
                reply_markup=reply_markup,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        else:
            raise ValueError("Unknown media type!")

    async def refresh_dialogs(self) -> typing.List[types.Dialog]:
        self.__my_all_dialogs__ = []
        async for current in self.iter_dialogs():
            self.__my_all_dialogs__.append(current)

        return self.__my_all_dialogs__

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

    async def get_my_dialogs(self) -> typing.List[types.Dialog]:
        if not self.__my_all_dialogs__ or len(self.__my_all_dialogs__) < 2:
            return await self.refresh_dialogs()
        return self.__my_all_dialogs__

    async def scp_listen(self, chat_id, filters=None, timeout=None) -> types.Message:
        """
            Wrapper function for pyromod.listen.
        """
        return await self.listen(chat_id=chat_id, filters=filters, timeout=timeout)

    # from Kantek
    async def resolve_url(self, url: str) -> str:
        if not url.startswith('http'):
            url: str = f'http://{url}'
        async with self.aioclient.get(
            f'http://expandurl.com/api/v1/?url={url}',
        ) as response:
            e = await response.text()
        return e if e != 'false' and e[:-1] != url else None

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

    def is_silent(self, message: types.Message) -> bool:
        return (
            isinstance(message, types.Message)
            and message.command
            and len(message.command) > 0
            and message.command[0x0].endswith('!')
        )

    def _get_inline_button_by_values(self, title: str, value: str) -> types.InlineKeyboardButton:
        _is_web_app = value.startswith("app::")
        value = value.removeprefix("app::")
        if re.findall(self.HTTP_URL_MATCHING, value):
            if _is_web_app:
                return types.InlineKeyboardButton(
                    text=title,
                    web_app=types.WebAppInfo(
                        url=value
                    )
                )
            return types.InlineKeyboardButton(text=title, url=value)
        else:
            return types.InlineKeyboardButton(text=title, callback_data=value)

    def _parse_inline_reply_markup(self, the_value: Union[dict, list]) -> types.InlineKeyboardMarkup:
        """ Parses a dict or a list to a valid reply_markup

        valid dict:
        {
            "hi": "https://google.com"
            "same::another hi": "https://microsoft.com"
            "ok": "callback data"
        }

        valid list:
        [
            {'hello': 'world.com', 'this is on same row': 'ok'},
            {'ok': 'button_data'},
            {'okay': 'https://google.com'}
        ]
        """
        keyboard_buttons: List[List[types.InlineKeyboardButton]] = []

        if isinstance(the_value, dict):
            current_button_index = 0
            for key in the_value:
                if not isinstance(key, str):
                    key = str(key)
                original_value = the_value[key]
                if key.startswith("same::"):
                    key = key.removeprefix("same::")
                    if current_button_index > 0:
                        current_button_index -= 1

                if current_button_index >= len(keyboard_buttons):
                    keyboard_buttons.append([])
                if not keyboard_buttons[current_button_index]:
                    keyboard_buttons[current_button_index] = []
                keyboard_buttons[current_button_index].append(
                    self._get_inline_button_by_values(key, original_value))
                current_button_index += 1
            return types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        elif isinstance(the_value, list):
            current_button_index = 0
            for current in the_value:
                if not isinstance(current, dict):
                    continue
                for current_row_title in current:
                    if current_button_index >= len(keyboard_buttons):
                        keyboard_buttons.append([])
                    keyboard_buttons[current_button_index].append(
                        self._get_inline_button_by_values(
                            current_row_title, current[current_row_title]
                        )
                    )
                current_button_index += 1
            return types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    async def get_user_input(
            self,
            message: types.Message,
            prompt: str = None,
            as_text: bool = True,
            delete_prompt: str = True
    ) -> types.Message:
        if not prompt:
            prompt = self.html_italic("waiting for any kind of input...")

        if message.reply_to_message and message.reply_to_message.from_user:
            replied = message.reply_to_message
            prompt_message = await replied.reply_text(text=prompt)
            result = await message.chat.listen(filters=self.filters.user(replied.from_user.id))
        else:
            prompt_message = await message.reply_text(text=prompt, quote=False)
            result = await self.listen(chat_id=message.chat.id)

        if delete_prompt:
            await prompt_message.delete()

        if as_text:
            return getattr(result, "text", result)

        return result

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional["enums.ParseMode"] = None,
        entities: List["types.MessageEntity"] = None,
        disable_web_page_preview: bool = None,
        disable_notification: bool = None,
        message_thread_id: int = None,
        effect_id: int = None,
        show_caption_above_media: bool = None,
        reply_to_message_id: int = None,
        reply_to_chat_id: Union[int, str] = None,
        reply_to_story_id: int = None,
        quote_text: str = None,
        quote_entities: List["types.MessageEntity"] = None,
        quote_offset: int = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        business_connection_id: str = None,
        allow_paid_broadcast: bool = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None
    ) -> "types.Message":
        if isinstance(reply_markup, (dict, list)):
            reply_markup = self._parse_inline_reply_markup(reply_markup)

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
                business_connection_id=business_connection_id,
                message_thread_id=message_thread_id,
                effect_id=effect_id,
                show_caption_above_media=show_caption_above_media,
                reply_to_chat_id=reply_to_chat_id,
                reply_to_story_id=reply_to_story_id,
                quote_text=quote_text,
                quote_entities=quote_entities,
                quote_offset=quote_offset,
                allow_paid_broadcast=allow_paid_broadcast,
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
                message_thread_id=message_thread_id,
                effect_id=effect_id,
                show_caption_above_media=show_caption_above_media,
                reply_to_story_id=reply_to_story_id,
                quote_text=quote_text,
                quote_entities=quote_entities,
                quote_offset=quote_offset,
                schedule_date=schedule_date,
                protect_content=protect_content,
                business_connection_id=business_connection_id,
                allow_paid_broadcast=allow_paid_broadcast,
                reply_markup=reply_markup
            )


    def get_non_cmd(self, message: types.Message) -> str:
        """
        Extracts the second word from a given message text or caption.

        Args:
            message (telegram.types.Message): The message to extract the second word from.

        Returns:
            str: The second word from the message, or an empty string if there are less than two words.
        """
        my_strs = split_some(message.text or message.caption, 1, ' ', '\n')
        if len(my_strs) < 2:
            return ''
        return my_strs[1]

    def split_some(self, value: str, max_count: int = 0, *delimiters) -> list:
        return split_some(value, max_count, *delimiters)

    def split_message(self, message: types.Message, max_count: int = 0) -> typing.List[str]:
        """
        Splits a given Telegram message into a list of strings, using spaces and newlines as delimiters.

        Args:
            message (telegram.Message): The message to split.
            max_count (int, optional): The maximum number of splits to perform. If 0, all possible splits are performed.

        Returns:
            List[str]: A list of strings resulting from the split operation.
        """
        return split_some(message.text, max_count, ' ', '\n')

    def split_timestamped_message(self, message: types.Message, max_count: int = 0) -> typing.List[str]:
        """
        Splits a timestamped message into a list of strings, using the ' -> ' separator between the timestamp and the message
        and the ' ' and '\n' separators between words.

        Args:
            message (types.Message): The message to split.
            max_count (int, optional): The maximum number of splits to perform. Defaults to 0 (unlimited).

        Returns:
            typing.List[str]: A list of strings containing the split message.
        """
        return split_some(message.text, max_count,  ' -> ', ' ', '\n', '->')

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
    
    def html_pre(self, value, language: str, *argv) -> str:
        return html_pre(value, language, *argv)

    def html_spoiler(self, value, *argv) -> str:
        return html_spoiler(value, *argv)

    async def reply_exception(self, message: types.Message, e: Exception, limit: int = 4, is_private: bool = False):
        ex_str = "".join(format_exception(e, limit=limit, chain=True))
        err_str = f"\n\t{ex_str}"
        txt: str = ''
        target_id = message.chat.id
        reply_id = message.id
        if is_private:
            target_id = 'me'
            reply_id = None

        if len(err_str) >= 4000:
            txt = f'Error: {err_str}'
            return await self.send_document(
                chat_id=target_id,
                reply_to_message_id=reply_id,
                document=to_output_file(txt))

        txt = self.html_bold('Error:') + self.html_mono(f'\n\t{ex_str}')
        return await self.send_message(
            chat_id=target_id, text=txt, reply_to_message_id=reply_id,
            parse_mode=ParseMode.HTML
        )

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
        except Exception:
            return 0

    async def try_get_common_chats_count(self, user_id: Union[int, str]) -> int:
        try:
            return len(await self.get_common_chats(user_id))
        except Exception:
            return 0

    async def try_get_messages_count(self, chat_id: Union[int, str], user_id: Union[int, str]) -> int:
        try:
            message_count = 0
            async for _ in self.search_messages(
                chat_id=chat_id,
                query="",
                from_user=user_id,
            ):
                message_count += 1

            return message_count
        except Exception:
            return 0

    def unpack_inline_message_id(inline_message_id: str) -> Atr:
        return unpack_inline_message(inline_message_id)

    def to_output_file(self, value: Union[str, bytes], file_name: str = "output.txt") -> BytesIO:
        return to_output_file(value=value, file_name=file_name)

    async def invoke(
        self,
        query: raw.core.TLObject,
        retries: int = session.Session.MAX_RETRIES,
        timeout: float = session.Session.WAIT_TIMEOUT,
        sleep_threshold: float = None,
        business_connection_id: str = None
    ) -> raw.core.TLObject:
        while True:
            try:
                return await super().invoke(
                    query=query,
                    retries=retries,
                    timeout=timeout,
                    sleep_threshold=sleep_threshold,
                    business_connection_id=business_connection_id
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
        sleep_threshold: float = None,
        business_connection_id: str = None
    ) -> raw.core.TLObject:
        return await self.invoke(
            query=data,
            retries=retries,
            timeout=timeout,
            sleep_threshold=sleep_threshold,
            business_connection_id=business_connection_id
        )

    def iter_history(
        self,
        chat_id: Union[int, str],
        limit: int = 0,
        offset: int = 0,
        offset_id: int = 0,
        offset_date: datetime = pUtils.zero_datetime()
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        return super().get_chat_history(chat_id, limit, offset, offset_id, offset_date)

    def iter_chat_members(
        self,
        chat_id: Union[int, str],
        query: str = "",
        limit: int = 0,
        filter: "enums.ChatMembersFilter" = enums.ChatMembersFilter.SEARCH
    ) -> Optional[AsyncGenerator["types.ChatMember", None]]:
        return super().get_chat_members(chat_id, query, limit, filter)

    async def fetch_chat_members(
        self,
        chat_id: int | str,
        query: str = "",
        limit: int = 0,
        filter: "enums.ChatMembersFilter" = enums.ChatMembersFilter.SEARCH
    ) -> list["types.ChatMember"]:
        results = []
        async for member in self.get_chat_members(chat_id=chat_id, query=query, limit=limit, filter=filter):
            results.append(member)
        
        return results

    def iter_dialogs(
        self,
        limit: int = 0
    ) -> Optional[AsyncGenerator["types.Dialog", None]]:
        return super().get_dialogs(limit)

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

    async def get_profile_photos_count(self, chat_id: Union[int, str]) -> int:
        return await super().get_chat_photos_count(chat_id)

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
        reply_to_chat_id: Union[int, str] = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        has_spoiler: bool = None,
        business_connection_id: str = None,
        allow_paid_broadcast: bool = None,
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
            # log.warning(f"Service messages cannot be copied. "
            #            f"chat_id: {self.chat.id}, message_id: {self.message_id}")
        elif message.game and not await message._client.storage.is_bot():
            return None
            # log.warning(f"Users cannot send messages with Game media type. "
            #            f"chat_id: {self.chat.id}, message_id: {self.message_id}")
        elif message.empty:
            return None
            # log.warning(f"Empty messages cannot be copied. ")

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
            reply_markup=reply_markup,
            allow_paid_broadcast=allow_paid_broadcast,
            business_connection_id=business_connection_id,
            has_spoiler=has_spoiler,
            reply_to_chat_id=reply_to_chat_id,
        )

    async def forward_messages_with_delay(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_ids: int,
        message_thread_id: int = None,
        disable_notification: bool = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        delay: float = 1,
    ) -> Union["types.Message", List["types.Message"]]:
        await asyncio.sleep(delay=delay)
        return await self.forward_messages(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            schedule_date=schedule_date,
            protect_content=protect_content,
        )

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
    
    async def get_parsed_updates(self, updates, filter_type) -> list:
        if not isinstance(updates, list):
            updates = [updates]
        
        all_parsed_updates = []
        for current_updates in updates:
            # fast path: if this is the exact same type, add and skip
            if isinstance(current_updates, filter_type):
                all_parsed_updates.append(current_updates)
                continue

            chats = getattr(current_updates, "chats", [])
            chats = {c.id: c for c in chats}
            users = getattr(current_updates, "users", [])
            users = {u.id: u for u in users}
                    
            for update in current_updates.updates:
                parser = self.dispatcher.update_parsers.get(type(update), None)
                if not parser:
                   continue
                parsed_update, _ = (
                    await parser(update, users, chats)
                    if parser is not None
                    else (None, type(None))
                )

                if filter_type and not isinstance(parsed_update, filter_type):
                    continue

                all_parsed_updates.append(parsed_update)
        
        return all_parsed_updates
