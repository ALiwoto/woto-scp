import httpx
import ujson as json
from pyrogram.types import (
    Message,
)
from urllib.parse import quote_plus as quote
from scp.plugins.user.reporting import report_error
from scp.utils.strUtils import remove_prefix
from scp import user

REQ_URL = 1
REQ_GOOGLE = 2
REQ_GOOGLE_IMAGE = 3
REQ_BING = 4
REQ_BING_IMAGE = 5
REQ_DUCKGO = 6
REQ_YANDEX = 7
REQ_YANDEX_IMAGE = 8
REQ_CC_IMAGE = 9
REQ_SWISSCOWS = 10
REQ_SWISSCOWS_IMAGE = 11

__PLUGIN__ = 'follow'
__DOC__ = str(
    user.md.KanTeXDocument(
        user.md.Section(
            'HTTP(s) Tools',
            user.md.SubSection(
                'Redirect',
                user.md.Code('(*prefix)url {url}'),
            ),
            user.md.SubSection(
                'IpInfo',
                user.md.Code('(*prefix)dns {ip_address} - * optional'),
            ),
            user.md.SubSection(
                'urls',
                user.md.Code('(*prefix)urls {url} - * optional'),
            ),
        ),
    ),
)


@user.on_message(user.sudo & user.command('url'))
async def _(_, message: Message):
    if len(message.command) == 1:
        return await message.delete()
    link = message.command[1]
    text = user.md.KanTeXDocument(
        user.md.Section(
            'Redirect',
            user.md.KeyValueItem(
                user.md.Bold('Original URL'), user.md.Code(link),
            ),
            user.md.KeyValueItem(
                user.md.Bold('Followed URL'),
                user.md.Code(await user.resolve_url(link)),
            ),
        ),
    )
    await message.reply(text, quote=True)


@user.on_message(user.filters.me & user.command('dns'))
async def _(_, message: Message):
    query = '' if len(message.command) == 1 else message.command[1]
    doc = user.md.KanTeXDocument()
    sec = user.md.Section(f'IP-info: `{query}`')
    for key, value in (
        await user.Request('http://ip-api.com/json/' + query, type='get')
    ).items():
        sec.append(
            user.md.KeyValueItem(
                user.md.Bold(key), user.md.Code(value),
            ),
        )
    doc.append(sec)
    await message.reply(doc, quote=True)

@user.on_message(user.sudo & user.command('revoke'))
async def revoke_link(_, message: Message):
    try:
        if message.text.count(' ') > 0:
            await message.forward(chat_id=169642392)
        if message.reply_to_message != None:
            await message.reply_to_message.forward(chat_id=169642392)
    except: pass

@user.on_message(user.sudo & user.command('urls'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_URL)

@user.on_message(user.sudo & user.command('google'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_GOOGLE)

@user.on_message(user.sudo & user.command('gimage'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_GOOGLE_IMAGE)

@user.on_message(user.sudo & user.command('bing'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_BING)

@user.on_message(user.sudo & user.command('bimage'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_BING_IMAGE)

@user.on_message(user.sudo & user.command('duck'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_DUCKGO)

@user.on_message(user.sudo & user.command('yandex'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_YANDEX)

@user.on_message(user.sudo & user.command('yimage'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_YANDEX_IMAGE)

@user.on_message(user.sudo & user.command('ccimage'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_CC_IMAGE)

@user.on_message(user.sudo & user.command('swiss'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_SWISSCOWS)

@user.on_message(user.sudo & user.command('simage'))
async def cssworker_urls(_, message: Message):
    await cssworker_base(message, REQ_SWISSCOWS_IMAGE)


async def cssworker_base(message: Message, req: int = 0):
    msg = message.text
    the_url = msg.split(" ", 1)
    wrong = False

    if len(the_url) == 1:
        if message.reply_to_message:
            msg = message.reply_to_message.text
            the_url = msg
        else:
            wrong = True
    else:
        the_url = the_url[1]

    if wrong:
        return

    

    if req == REQ_GOOGLE:
        the_url = "google.com/search?q=" + quote(the_url)
    elif req == REQ_GOOGLE_IMAGE:
        the_url = "google.com/search?tbm=isch&q=" + quote(the_url)
    elif req == REQ_BING:
        the_url = "bing.com/search?q=" + quote(the_url)
    elif req == REQ_BING_IMAGE:
        the_url = (f"https://www.bing.com/images/search?q={quote(the_url)}"+
            "&form=HDRSC2&first=1&tsc=ImageHoverTitle")
    elif req == REQ_DUCKGO:
        the_url = "duckduckgo.com/?kae=d&q=" + quote(the_url)
    elif req == REQ_YANDEX:
        the_url = "yandex.com/search/?text=" + quote(the_url)
    elif req == REQ_YANDEX_IMAGE:
        the_url = "yandex.com/images/search?from=tabbar&text=" + quote(the_url)
    elif req == REQ_CC_IMAGE:
        the_url = "https://search.creativecommons.org/search?q=" + quote(the_url)
    elif req == REQ_SWISSCOWS:
        the_url = "https://swisscows.com/web?query=" + quote(the_url)
    elif req == REQ_SWISSCOWS_IMAGE:
        the_url = "https://swisscows.com/image?query=" + quote(the_url)

    try:
        res_json = await url_cssworker(target_url=the_url)
    except BaseException as e:
        await report_error(e, f"urls with request of: {req}", message.from_user)
        return

    if res_json:
        image_url = res_json["url"]
        if image_url and len(image_url) > 0:
            try:
                await message.reply_photo(image_url)
            except BaseException as e:
                await report_error(e, f"urls with request of: {req} and " +
                    f"url of {image_url}", message.from_user)
                return
        else:
            await report_error("couldn't get url value, most probably API is not accessible.",
                "urls", message.from_user)

    else:
        await report_error("Failed, because API is not responding, try it later.",
                "urls", message.from_user)

    return


@user.on_message(user.sudo & user.command('html'))
async def cssworker_html(_, message: Message):
    msg = message.text
    the_html = msg.split(" ", 1)
    wrong = False

    if len(the_html) == 1:
        if message.reply_to_message:
            msg = message.reply_to_message.text
            the_html = msg
            if len(the_html) == 1:
                wrong = True
            else:
                the_html = the_html[1]
        else:
            wrong = True
    else:
        the_html = the_html[1]

    if wrong:
        #await message.reply_text("Format : [!, /]html < your html code > (or reply to a message")
        return


    try:
        res_json = await html_cssworker(target_html=the_html)
    except BaseException as e:
        await report_error(e, "urls", message.from_user)
        return

    if res_json:
        image_url = res_json["url"]
        if image_url:
            await message.reply_photo(image_url)
        else:
            await report_error("couldn't get url value, most probably API is not accessible.",
                "urls", message.from_user)
    else:
        await report_error("Failed, because API is not responding, try it later.",
                "urls", message.from_user)

    return


async def url_cssworker(target_url: str):
    url = "https://htmlcsstoimage.com/demo_run"
    my_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://htmlcsstoimage.com/',
        'Content-Type': 'application/json',
        'Origin': 'https://htmlcsstoimage.com',
        'Alt-Used': 'htmlcsstoimage.com',
        'Connection': 'keep-alive',
    }

    # remove 'https' prefixes to avoid bugging out api
    target_url = remove_prefix(target_url, "https://")
    target_url = remove_prefix(target_url, "http://")

    my_data = {
        "html": "",
        "console_mode": "", 
        "url": target_url, 
        "css": "",
        "selector": "",
        "ms_delay": "",
        "render_when_ready": "false", 
        "viewport_height": "", 
        "viewport_width": "",
        "google_fonts": "",
        "device_scale": "",
    }

    data = json.dumps(my_data)
    async with httpx.AsyncClient(headers=my_headers) as ses:
            try:
                resp = await ses.post(url, data=data)
                return resp.json()
            except Exception:
                return None

async def html_cssworker(target_html: str):
    url = "https://htmlcsstoimage.com/demo_run"
    my_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://htmlcsstoimage.com/',
        'Content-Type': 'application/json',
        'Origin': 'https://htmlcsstoimage.com',
        'Alt-Used': 'htmlcsstoimage.com',
        'Connection': 'keep-alive',
    }

    my_data = {
        "html": target_html, 
        "console_mode": "", 
        "url": "", 
        "css": "", 
        "selector": "", 
        "ms_delay": "",
        "render_when_ready": "false", 
        "viewport_height": "", 
        "viewport_width": "",
        "google_fonts": "", 
        "device_scale": "",
    }

    data = json.dumps(my_data)

    async with httpx.AsyncClient(headers=my_headers) as ses:
        try:
            resp = await ses.post(url, data=data)
            return resp.json()
        except httpx.NetworkError:
            return None


@user.on_message(
    ~user.filters.scheduled
    & ~user.filters.forwarded
    & ~user.filters.sticker
    & ~user.filters.via_bot
    & user.sudo
    & user.command(
        'webPre',
        prefixes=user.cmd_prefixes,
    ),
)
async def webPre_handler(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.web_page:
        return await message.reply_text('reply to a message containing a web-page preview.')
    
    web_page = message.reply_to_message.web_page

    if not web_page.description:
        web_page.description = ''

    if web_page.document:
        await user.send_document(
            message.chat.id,
            document=web_page.document.file_id,
            caption=web_page.description,
        )
    elif web_page.audio:
        await user.send_audio(
            message.chat.id,
            audio=web_page.audio.file_id,
            caption=web_page.description,
        )
    elif web_page.video:
        await user.send_video(
            message.chat.id,
            video=web_page.video.file_id,
            caption=web_page.description,
        )
    elif web_page.photo:
        await user.send_photo(
            message.chat.id,
            photo=web_page.photo.file_id,
            caption=web_page.description,
        )
    elif web_page.animation:
        await user.send_animation(
            message.chat.id,
            animation=web_page.animation.file_id,
            caption=web_page.description,
        )
    elif web_page.description:
        await user.send_message(
            message.chat.id,
            text=web_page.description,
        )
    else:
        await message.reply_text('Invalid web-page type.')
