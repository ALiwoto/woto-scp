import base64
import struct
from attrify import Attrify as Atr
from pyrogram.types import Message
from pyrogram.raw.types.web_view_result_url import WebViewResultUrl


class WebViewResultContainer(WebViewResultUrl):

    # the message this web view result belong to.
    message: Message = None

    def __init__(self, *, query_id: int, url: str, message: Message) -> None:
        super().__init__(query_id=query_id, url=url)
        self.message = message
    

def unpack_inline_message(inline_message_id: str) -> Atr:
    temp = {}
    dc_id, message_id, chat_id, query_id = struct.unpack(
        '<iiiq',
        base64.urlsafe_b64decode(
            inline_message_id + '=' * (len(inline_message_id) % 4),
        ),
    )
    temp['dc_id'] = dc_id
    temp['message_id'] = message_id
    temp['chat_id'] = int(str(chat_id).replace('-1', '-1001'))
    temp['query_id'] = query_id
    temp['inline_message_id'] = inline_message_id
    return Atr(temp)
