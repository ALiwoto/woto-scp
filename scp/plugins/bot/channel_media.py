from io import BytesIO
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
    Message,
    InputMediaPhoto,
    InputMediaDocument,
)
from scp.utils.media_utils import PixivIllustInfo
from urllib.parse import parse_qs, urlparse
from pixivpy3 import AppPixivAPI
from gallery_dl.extractor import find as find_extractor
from gallery_dl.extractor.message import Message as ExtractorMessage

pixiv_api = AppPixivAPI()
setattr(user, 'pixiv_api', pixiv_api)
setattr(bot, 'pixiv_api', pixiv_api)

def do_pixiv_auth(pixiv_api: AppPixivAPI):
    if not pixiv_api.access_token and user.scp_config.pixiv_access_token:
        try:
            pixiv_api.set_auth(
                refresh_token=user.scp_config.pixiv_refresh_token,
                access_token=user.scp_config.pixiv_access_token,
            )
            auth_result = pixiv_api.auth()

            auth_date = datetime.datetime.now()
            expires_in = auth_result.expires_in
            setattr(pixiv_api, "auth_date", auth_date)
            setattr(pixiv_api, "auth_expires_in", expires_in)
            setattr(pixiv_api, "auth_expiration_date", 
                    auth_date + datetime.timedelta(seconds=expires_in))
        except: pass
    elif pixiv_api.refresh_token:
        # we know that we have already authorized, but we need
        # to check if the authorization still valid or not
        if getattr(pixiv_api, "auth_expiration_date", None) and \
            datetime.datetime.now() < pixiv_api.auth_expiration_date:
            # not expired yet
            return
        
        # expired, so we need to re-auth, with recursive
        pixiv_api.access_token = None
        return do_pixiv_auth(pixiv_api)

@bot.on_message(
    user.wfilters.pixiv &
    user.special_channels
)
async def pixiv_handler(_, message: Message):
    pixiv_api = getattr(user, 'pixiv_api', None)
    if not isinstance(pixiv_api, AppPixivAPI):
        return
    
    # parse the url
    url = message.text
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    await message.delete()

    do_pixiv_auth(pixiv_api)
    
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
    
    illust_info = PixivIllustInfo(illust)
    if illust_info.has_error:
        do_pixiv_auth(pixiv_api)

        # repeat it one more time
        illust = pixiv_api.illust_detail(illust_id)
        if not illust:
            return
        
        illust_info = PixivIllustInfo(illust)
        if illust_info.has_error:
            # just give up at this point
            print(f"failed to get illust info: {illust}")
            return
    caption = user.html_link("Artist", url)
    caption += "\n@" + (user.html_normal(message.chat.username) \
        if message.chat.username \
        else (message.chat.usernames[0].username if message.chat.usernames else ""))
    
    if illust_info.is_multiple:
        current_counter = 0
        all_files_input = []
        all_large_inputs = []
        for current_meta in illust_info.meta_pages:
            current_counter += 1
            large_url = current_meta.image_urls.large
            original_url = current_meta.image_urls.original
            file_path = f'pic_{illust_id}_{current_counter}.jpg'
            pixiv_api.download(large_url, path='.', name=file_path)
            all_files_input.append(InputMediaPhoto(
                media=file_path,
                caption=(caption if current_counter == 1 else "")
            ))
            if len(all_files_input) >= 10:
                break
            
            file_path = original_url.split('/')[-1]
            pixiv_api.download(original_url, path='.', name=file_path)
            all_large_inputs.append(InputMediaDocument(
                media=file_path
            ))
            
        sent_album = await bot.send_media_group(
            chat_id=message.chat.id, 
            media=all_files_input
        )
        await bot.send_media_group(
            chat_id=message.chat.id, 
            media=all_large_inputs,
            reply_to_message_id=sent_album[0].message_id,
        )
    else:
        # get the medium picture
        file_path = f'pic_{illust_id}.jpg'
        pixiv_api.download(illust.illust.image_urls.large, path='.', name=file_path)
        
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
            pixiv_api.download(illust.illust.image_urls.medium, path='.', name=file_path)
            await bot.send_photo(chat_id=message.chat.id, photo=file_path)
            user.remove_file(medium_file_path)

        try:
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

@bot.on_message(
    user.wfilters.twitter &
    user.special_channels
)
async def twitter_handler(_, message: Message):
    parsed_url = urlparse(message.text)
    extractor = find_extractor(message.text)
    if not extractor:
        return
    
    await message.delete()
    direct_url: str = None
    # extractor is found
    for msg in extractor:
        if not isinstance(msg, tuple):
            # unexpected, should be checked in the future
            continue

        if msg[0] == ExtractorMessage.Url:
            direct_url = msg[1]
            break
    
    if not direct_url:
        return
    
    caption = user.html_link("Artist", message.text)
    caption += "\n@" + (user.html_normal(message.chat.username) \
        if message.chat.username \
        else (message.chat.usernames[0].username if message.chat.usernames else ""))
    
    async with user.aioclient.get(
        url=direct_url
    ) as response:
        my_pic = BytesIO(await response.read())
        setattr(my_pic, 'name', f"{parsed_url.path.split('/')[-1]}.jpg")
    
    sent_photo = await bot.send_photo(
        chat_id=message.chat.id,
        photo=my_pic,
        caption=caption,
    )
    await bot.send_document(
        chat_id=message.chat.id,
        document=my_pic,
        reply_to_message_id=sent_photo.message_id,
    )

