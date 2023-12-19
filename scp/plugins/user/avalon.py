from scp import user
from pyrogram.types import Message
from enum import Enum

"""
Avalon centralized system.
Get back your focus.
"""

__PLUGIN__ = 'avalon'

__HELP__ = f"""
Avalon is a centralized system that allows you to get back your focus by
reducing the number of chats you have to check.
It is based on the idea of having a single chat where all the messages
from all the chats you are in are forwarded to.
You can then choose to mute all the chats you are in and focus only on
the forwarded messages.
You can also choose to mute only some chats and keep others unmuted.
This way you can get back your focus without losing the ability to
communicate with your friends.
"""

__DOC__ = str(
    user.md.KanTeXDocument(
        user.md.Section(
            'Avalon',
            user.md.SubSection(
                'Avalon is a centralized system that allows you to get back your focus by reducing the number of chats you have to check.',
                user.md.SubSection(
                    'It is based on the idea of having a single chat where all the messages from all the chats you are in are forwarded to.',
                    user.md.SubSection(
                        'You can then choose to mute all the chats you are in and focus only on the forwarded messages.',
                        user.md.SubSection(
                            'You can also choose to mute only some chats and keep others unmuted.',
                            user.md.SubSection(
                                'This way you can get back your focus without losing the ability to communicate with your friends.',
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)

class AvalonMode(Enum):
    PM = 0
    BOT = 1
    TAG = 2

class PermaMessageContent:
    """
    Represents semi-perma message content.
    """
    message: Message
    content: str
    keyboard_data: str
    def __init__(self, message: Message, content: str, keyboard_data: str = None):
        self.message = message
        self.content = content
        self.keyboard_data = keyboard_data
    
    def __str__(self):
        return self.message.text or \
            self.message.caption or \
            self.message.media.name or 'UNKNOWN MESSAGE TYPE'

@user.on_message(
    ~(
        user.filters.group |
        user.filters.channel |
        user.filters.me |
        user.filters.bot
    ),
    group=100,
)
async def pm_log_handler(_, message: Message):
    if not user.scp_config.avalon_pms or not user.avalon_system_enabled:
        return
    
    if message.from_user.id == 777000:
        # ignore messages coming from telegram itself.
        return
    
    txt, keyboard = await get_txt_and_keyboard(message)

    await user.send_message(
        chat_id=user.scp_config.avalon_pms,
        text=txt,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@user.on_message(
    user.filters.bot &
    user.filters.private,
    group=101,
)
async def bots_log_handler(_, message: Message):
    if not user.scp_config.avalon_bots or not user.avalon_system_enabled:
        return
    
    txt, keyboard = await get_txt_and_keyboard(message)

    await user.send_message(
        chat_id=user.scp_config.avalon_bots,
        text=txt,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@user.on_message(
    user.wfilters.tagged &
    ~(
        user.filters.private |
        user.filters.me |
        user.owner
    ),
    group=100,
)
async def tags_log_handler(_, message: Message):
    if not user.scp_config.avalon_tags or not user.avalon_system_enabled:
        return
    elif not message.from_user:
        return
    
    txt, keyboard = await get_txt_and_keyboard(message, AvalonMode.TAG)

    await user.send_message(
        chat_id=user.scp_config.avalon_tags,
        text=txt,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )



async def get_message_content(message: Message) -> PermaMessageContent:
    the_content = PermaMessageContent(message, '')
    if message.text:
        the_content.content = user.html_normal(message.text[:1024])
        return the_content
    elif message.contact:
        c = message.contact
        mentioned = f'({await user.html_mention(c.user_id, str(c.user_id))})' if c.user_id else ''
        the_content.content = f"{c.first_name.strip() if c.first_name else ''}" \
            f"{c.last_name.strip() if c.last_name else ''}" \
            f"{mentioned} - {user.html_mono(c.phone_number.strip())}"
        return the_content
    elif message.media:
        perma_msg = await user.get_bot_perspective(message, delay=1)
        the_content.message = perma_msg
        file_id = getattr(getattr(perma_msg, perma_msg.media.name.lower(), None), "file_id", None)
        the_content.content = user.html_mono(file_id)
        the_content.keyboard_data = f"sendBotMedia_{perma_msg.from_user.id}_{perma_msg.id}"
        return the_content
    
    return the_content

def get_formatted_forward(message: Message) -> str:
    if message.forward_from:
        f_user = message.forward_from
        txt = user.html_link(f_user.first_name[:16], f"https://t.me/{f_user.username}", " (")
        txt += user.html_mono(f_user.id, ")")
        return txt
    elif message.forward_sender_name:
        return user.html_mono(message.forward_sender_name)
    elif message.forward_from_chat:
        f_chat = message.forward_from_chat
        if f_chat.username:
            txt = user.html_link(f_chat.title, f"https://t.me/{f_chat.username}/{message.forward_from_message_id}", " (")
            txt += user.html_mono(f_chat.id, ")")
            return txt
        
        # no username; use the id
        # the link format is https://t.me/c/CHAT_ID/MSG_ID here.
        txt = user.html_link(f_chat.title, f"https://t.me/c/{str(f_chat.id)[4:]}/{message.forward_from_message_id}", " (")
        txt += user.html_mono(f_chat.id, ")")
        return txt

    return None

async def get_txt_and_keyboard(message: Message, mode: AvalonMode = AvalonMode.PM):
    sender = message.from_user
    ttl_value = getattr(getattr(message, message.media.name.lower(), None), \
                        "ttl_seconds", None) if is_real_media else None
    is_real_media = user.is_real_media(message)
    txt = ''
    if mode == AvalonMode.PM:
        txt += user.html_normal(f"#PM #{user.me.first_name} (")
    elif mode == AvalonMode.TAG:
        txt += user.html_normal(f"#TAG #{user.me.first_name} (")

    txt += user.html_mono(user.me.id, ")")
    txt += user.html_bold(f"\n• FROM: ")
    if sender.username:
        txt += user.html_link(message.from_user.first_name[:16], \
                              f"https://t.me/{message.from_user.username}", " (")
    else:
        txt += user.html_normal(sender.first_name[:16], " (")
    txt += user.html_mono(sender.id, ")")

    if ttl_value:
        txt += user.html_bold("\n• TTL: ") + user.html_mono(f"{ttl_value}")

    if message.chat.id != sender.id:
        txt += user.html_bold("\n• CHAT: ")
        if message.chat.username:
            txt += user.html_link(message.chat.title, f"https://t.me/{message.chat.username}", " (")
        else:
            txt += user.html_normal(message.chat.title, " (")
        txt += user.html_mono(message.chat.id, ")")

    if mode == AvalonMode.TAG:
        txt += user.html_bold("\n• LINK: ")
        txt += user.html_link("here", message.link)

    if message.forward_from_chat or message.forward_from:
        txt += user.html_bold("\n• FORWARD FROM: ") + get_formatted_forward(message)
    if message.caption:
        txt += user.html_bold("\n• CAPTION:", message.caption[:900])
    
    txt += user.html_bold("\n• MESSAGE: ", (f"({message.media.name.lower()}) " if is_real_media else None))
    msg_content = await get_message_content(message)
    txt += msg_content.content if (msg_content and msg_content.content) else \
        user.html_italic("UNKNOWN MESSAGE TYPE")
    media_btn_data: str = None
    if is_real_media:
        media_btn_data = f"sendMedia_{message.from_user.id}_{message.id}" if \
            not msg_content.keyboard_data else \
            msg_content.keyboard_data

    keyboard = [
        {"↩️ Reply": f"reply_{message.from_user.id}_{message.id}", "▶️ Send message": f"msg_{message.from_user.id}"},
        {"❌ Block": f"block_{message.from_user.id}", f"💢 Delete": "delete_msg"},
        {"🌀 React": f"react_{message.from_user.id}_{message.id}", "✅ Mark as read": f"read_{message.from_user.id}_{message.id}"},
        ({"🖼 Send media here": media_btn_data} if is_real_media else None)
    ]

    return txt, keyboard
