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
    txt += user.html_bold(f"\n• FROM:", f" {message.from_user.first_name[:16]} (")
    txt += user.html_mono(message.from_user.id, ")")
    txt += user.html_bold(f"\n• MESSAGE: {await get_message_content(message)}")

    keyboard = [
        {"↩️ Reply": f"reply_{message.from_user.id}_{message.id}", "▶️ Send message": f"msg_{message.from_user.id}"},
        {"❌ Block": f"block_{message.from_user.id}", f"💢 Delete": "delete_msg"},
        {"🌀 React": f"react_{message.from_user.id}_{message.id}", "✅ Mark as read": f"read_{message.from_user.id}_{message.id}"},
        {"🖼 Send media here": f"sendMedia_{message.from_user.id}_{message.id}"} if message.media else None
    ]

    await user.send_message(
        chat_id=user.scp_config.pm_log_channel,
        text=txt,
        reply_markup=keyboard
    )
    

async def get_message_content(message: Message) -> str:
    if message.text:
        return message.text[:1024]
    elif message.media:
        return (await user.get_media_file_id(
            message=message,
            delay=1,
        )) + (message.caption[:1024] if message.caption else "")
    else:
        return "UNKNOWN MESSAGE TYPE"

