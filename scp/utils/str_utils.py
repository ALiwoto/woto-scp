from pyrogram.types.user_and_chats.chat_permissions import ChatPermissions
from random import randint, choice

_all_cups = [chr(0x2615), chr(0x1f942), chr(0x1f964), chr(0x1f375), chr(0x1f37e)]
_all_username_repr = ['@{0}', 't.me/{0}', 'https://t.me/{0}', 'https://telegram.dog/{0}', 'https://telegram.me/{0}']
_all_username_strs = [
    "uname", "the uname", "cool username", "the username", 
    "username", "user-name", "UserName", "target username",
    "the owo username", "ayo username", "the username of the chat",
]
_all_format_strs = ["format", "the format", "ForMat", "for-mat", "format of"]
_all_stuff_strs = [
    "stuff", "some stuff", "some content", "some things", "texts",
    "target stuff", "target contents", "target things", "target messages"
]
_all_sad_emojis = ["😔", "😞", "😟", "😠", "😡", "😢", "😣", "😤", "😥", "😦", "😧", "😨", "😩", "😪", "😫", "😭"]
_all_note_strs = ["✍️", "📔", "📓", "🗒", "📝"]
_all_right_arrow_strs = [
    "->", "→", "➡️", "➡", "⮕", "⇨", "⇢", "⇾", "⇝", "⇛",
    "⇰", "⇴", "⇶", "⇸", "⇹", "⇻", "⇼", "⇽", "⇿",
    "⇀", "⇁", "⇂", "⇃", "⇄", "⇅", "⇆", "⇇", "⇈", "⇉", "⇊",
    "⇋", "⇌", "⇍", "⇎", "⇏", "⇑", "⇒", "⇓", "⇕",
    "⇖", "⇗", "⇘", "⇙", "⇚", "⇜", "⇞", "⇟", "⇔", 
    "⇡", "⇣", "⇥", "⇦", "⇧", "⇩", "⇪", "⇫", "", 
    "⇬", "⇭", "⇮", "⇯", "⇲", "⇳", "⇵", "⇷", "⇺"
]

def get_random_emoji() -> str:
    return chr(0x1F601 + randint(0, 78))

def get_random_cup() -> str:
    return choice(_all_cups)

def get_random_username_repr(username: str) -> str:
    if not username:
        return "😩no username"
    return choice(_all_username_repr).format(username)

def get_random_username_str() -> str:
    return choice(_all_username_strs)

def get_random_format_str() -> str:
    return choice(_all_format_strs)

def get_random_stuff_str() -> str:
    return choice(_all_stuff_strs)

def get_random_sad_emoji() -> str:
    return choice(_all_sad_emojis)

def get_random_note_str() -> str:
    return choice(_all_note_strs)

def get_random_right_arrow() -> str:
    return choice(_all_right_arrow_strs)

def name_check(username: str = None):
    if username:
        return '@'+username
    return None


def bool_check(var: bool):
    if var:
        return '✅'
    else:
        return '❌'


def parse_permission_as_str(perms: ChatPermissions) -> str:
    if not isinstance(perms, ChatPermissions): return ""
    text = ''
    text += 'Message: ' + bool_check(perms.can_send_messages) + '\n'
    text += 'Media: ' + bool_check(perms.can_send_media_messages) + '\n'
    text += 'Media: ' + bool_check(perms.can_send_media_messages) + '\n'
    text += 'Inline: ' + bool_check(perms.can_send_other_messages) + '\n'
    text += 'Web: ' + bool_check(perms.can_add_web_page_previews) + '\n'
    text += 'Poll: ' + bool_check(perms.can_send_polls) + '\n'
    text += 'Info: ' + bool_check(perms.can_change_info) + '\n'
    text += 'invite: ' + bool_check(perms.can_invite_users) + '\n'
    text += 'Pin: ' + bool_check(perms.can_pin_messages) + '\n'
    return text

def replace_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    return text.replace('"', "").replace("\\r", "").replace("\\n", "").replace("\\", "")

def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        text = text.replace(prefix, "", 1)
    return text


# removes invisible characters from a text so we can match it correctly.
def remove_invisible(value: str) -> str:
    #from \u2060 to \u2069
    #from \u200C to \u200F; \u061C
    result = ""
    ocurrent = 0x0
    for current in value:
        ocurrent = ord(current)
        if ocurrent >= 0x2060 and ocurrent <= 0x2069:
            continue
        elif ocurrent >= 0x200C and ocurrent <= 0x200F:
            continue
        elif ocurrent == 0x061C:
            continue
        result += current
    return result
