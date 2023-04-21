from scp import user
from pyrogram.types import Message


@user.on_message(
    ~(
        user.filters.group |
        user.filters.channel |
        user.filters.me
    ),
    group=100,
)
async def pm_log_handler(_, message: Message):
    if not user.scp_config.pm_log_channel or not user.pm_log_enabled:
        return
    
    txt = user.html_normal(f"#PM #{user.me.first_name} (")
    txt += user.html_mono(user.me.id, ")")
    txt += user.html_bold(f"\n• FROM: ", " (")
    if message.from_user.username:
        txt += user.html_link(message.from_user.first_name[:16], f"https://t.me/{message.from_user.username}", " (")
    else:
        txt += user.html_normal(message.from_user.first_name[:16], " (")
    txt += user.html_mono(message.from_user.id, ")")
    if message.forward_from_chat or message.forward_from:
        txt += user.html_bold("\n• FORWARD FROM: ") + get_formatted_forward(message)
    if message.caption:
        txt += user.html_bold("\n• CAPTION:", message.caption[:900])
    txt += user.html_bold("\n• MESSAGE: ")
    txt += await get_message_content(message)

    keyboard = [
        {"↩️ Reply": f"reply_{message.from_user.id}_{message.id}", "▶️ Send message": f"msg_{message.from_user.id}"},
        {"❌ Block": f"block_{message.from_user.id}", f"💢 Delete": "delete_msg"},
        {"🌀 React": f"react_{message.from_user.id}_{message.id}", "✅ Mark as read": f"read_{message.from_user.id}_{message.id}"},
        ({"🖼 Send media here": f"sendMedia_{message.from_user.id}_{message.id}"} if user.is_real_media(message) else None)
    ]

    await user.send_message(
        chat_id=user.scp_config.pm_log_channel,
        text=txt,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
    

async def get_message_content(message: Message) -> str:
    if message.text:
        return user.html_normal(message.text[:1024])
    elif message.media:
        return user.html_mono(await user.get_media_file_id(
            message=message,
            delay=1,
        ))
    else:
        return "UNKNOWN MESSAGE TYPE"


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
