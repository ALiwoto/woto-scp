import re
import time
import json
import asyncio
import datetime
from scp import bot, user
from pyrogram.types import (
    ChatMemberUpdated, 
    ChatEventFilter,
    User,
    Message
)
from urllib.parse import parse_qs, urlparse
from pixivpy3 import AppPixivAPI

pixiv_api = AppPixivAPI()
setattr(user, 'pixiv_api', pixiv_api)
setattr(bot, 'pixiv_api', pixiv_api)

@bot.on_message(
    user.wfilters.pixiv &
    user.special_channels
)
async def pixiv_handler(_, message: Message):
    pixiv_api = getattr(user, 'pixiv_api', None)
    if not isinstance(pixiv_api, AppPixivAPI):
        return
    
    if not pixiv_api.access_token and user.scp_config.pixiv_access_token:
        try:
            pixiv_api.set_auth(
                refresh_token=user.scp_config.pixiv_refresh_token,
                access_token=user.scp_config.pixiv_access_token,
            )
            pixiv_api.auth()
        except: pass
    # parse the url
    url = message.text
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    illust_id: str = None
    try:
        # get the illust id
        illust_id = query_params['illust_id'][0]
    except: pass

    if not illust_id:
        # get the illust id from the url
        illust_id = parsed_url.path.split('/')[-1]
    
    if not illust_id:
        return
    
    # get the illust
    illust = pixiv_api.illust_detail(illust_id)
    if not illust:
        return
    
    # get the medium picture
    file_path = f'pic_{illust_id}.jpg'
    if not pixiv_api.download(illust.illust.image_urls.large, path='.', name=file_path):
        return
    
    await message.delete()
    caption = user.html_link("Artist", url)
    caption += "\n@" + user.html_normal(message.chat.username) \
        if message.chat.username \
        else (message.chat.usernames[0] if message.chat.usernames else "")
    # send the picture
    sent_photo_msg: Message = None
    try:
        sent_photo_msg = await bot.send_photo(
            chat_id=message.chat.id, 
            photo=file_path,
            caption=caption
        )
    except:
        medium_file_path = f'pic_medium_{illust_id}.jpg'
        if not pixiv_api.download(illust.illust.image_urls.medium, path='.', name=file_path):
            return
        await bot.send_photo(chat_id=message.chat.id, photo=file_path)
        user.remove_file(medium_file_path)

    try:
        if (illust.illust.meta_single_page.original_image_url):
            original_url = illust.illust.meta_single_page.original_image_url
            file_original_path = original_url.split('/')[-1]
            if pixiv_api.download(original_url, path='.', name=file_original_path):
                user.remove_file(file_path)
                file_path = file_original_path
    except: pass

    await bot.send_document(
        chat_id=message.chat.id,
        document=file_path,
        reply_to_message_id=sent_photo_msg.message_id,
    )
    user.remove_file(file_path)

    

