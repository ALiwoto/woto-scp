from io import BytesIO
from typing import List
import re
import time
import json
import asyncio
import datetime
from scp import bot, user, ScpClient
from pyrogram.types import (
    ChatMemberUpdated, 
    ChatEventFilter,
    User,
    Message,
    InputMediaPhoto,
    InputMediaDocument,
)
from pyrogram.enums import ParseMode
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
    url = getattr(message, 'target_media_url', None)
    if not url:
        return
    
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
            my_file = BytesIO()
            my_file.name = f'pic_{illust_id}_{current_counter}.jpg'
            pixiv_api.download(large_url, name=my_file)
            all_files_input.append(InputMediaPhoto(
                media=my_file,
                caption=(caption if current_counter == 1 else ""),
                parse_mode=ParseMode.HTML,
            ))
            
            my_file = BytesIO()
            my_file.name = original_url.split('/')[-1]
            pixiv_api.download(original_url, name=my_file)
            all_large_inputs.append(InputMediaDocument(
                media=my_file
            ))

            # telegram's limit is 10
            if len(all_files_input) >= 10:
                break
            
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
        my_file = BytesIO()
        my_file.name = f'pic_{illust_id}.jpg'
        pixiv_api.download(illust.illust.image_urls.large, name=my_file)
        
        # send the picture
        sent_photo_msg: Message = None
        try:
            sent_photo_msg = await bot.send_photo(
                chat_id=message.chat.id, 
                photo=my_file,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
        except:
            my_file = BytesIO()
            my_file.name = f'pic_medium_{illust_id}.jpg'
            pixiv_api.download(illust.illust.image_urls.medium, name=my_file)
            sent_photo_msg = await bot.send_photo(chat_id=message.chat.id, photo=my_file)

        try:
            original_url = illust.illust.meta_single_page.original_image_url
            my_file = BytesIO()
            my_file.name = original_url.split('/')[-1]
            pixiv_api.download(original_url, name=my_file)
            await bot.send_document(
                chat_id=message.chat.id,
                document=my_file,
                reply_to_message_id=sent_photo_msg.message_id,
            )
        except: pass


@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & (user.owner | user.sudo)
    # & user.wfilters.twitter
    & user.command(
        ['tw', 'twitter'],
        prefixes=user.cmd_prefixes,
    ),
)
@bot.on_message(
    user.wfilters.twitter
    & user.special_channels
)
async def twitter_handler(client: "ScpClient", message: Message):
    url = message.text
    non_cmd = user.get_non_cmd(message)
    if non_cmd:
        url = non_cmd
    parsed_url = urlparse(url)
    extractor = find_extractor(url)
    if not extractor:
        return
    
    if not non_cmd:
        # not a command
        await message.delete()
    direct_urls: List[str] = []
    # extractor is found
    for msg in extractor:
        if not isinstance(msg, tuple):
            # unexpected, should be checked in the future
            continue

        if msg[0] == ExtractorMessage.Url:
            direct_urls.append(msg[1])
    
    if not direct_urls:
        # couldn't fetch any direct url...
        # perhaps add a log or something in here in the future
        return
    
    caption = user.html_link("Artist", url)
    if not non_cmd:
        caption += "\n@" + (user.html_normal(message.chat.username) \
            if message.chat.username \
            else (message.chat.usernames[0].username if message.chat.usernames else ""))

    if len(direct_urls) == 1:
        # single pic
        async with user.aioclient.get(
            url=direct_urls[0]
        ) as response:
            my_pic = BytesIO(await response.read())
            setattr(my_pic, 'name', f"{parsed_url.path.split('/')[-1]}.jpg")
        
        sent_photo = await client.send_photo(
            chat_id=message.chat.id,
            photo=my_pic,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        await client.send_document(
            chat_id=message.chat.id,
            document=my_pic,
            reply_to_message_id=sent_photo.message_id,
        )
        my_pic.close()
    else:
        # we have to send them as album
        all_files_input = []
        all_large_inputs = []
        all_memory_files: List[BytesIO] = []
        current_counter = 0
        for current_url in direct_urls:
            current_counter += 1
            async with user.aioclient.get(
                url=current_url
            ) as response:
                my_pic = BytesIO(await response.read())
                setattr(my_pic, 'name', f"{parsed_url.path.split('/')[-1]}_{current_counter}.jpg")
                all_memory_files.append(my_pic)
            
            all_files_input.append(InputMediaPhoto(
                media=my_pic,
                caption=(caption if current_counter == 1 else ""),
                parse_mode=ParseMode.HTML,
            ))
            
            all_large_inputs.append(InputMediaDocument(
                media=my_pic
            ))

            if len(all_files_input) >= 10:
                break
        
        sent_album = await client.send_media_group(
            chat_id=message.chat.id, 
            media=all_files_input,
        )
        await client.send_media_group(
            chat_id=message.chat.id, 
            media=all_large_inputs,
            reply_to_message_id=sent_album[0].message_id,
        )

        # clean up the memory
        for current_file in all_memory_files:
            current_file.close()


