def name_check(username: str = None):
    if username:
        return '@'+username
    return None


def bool_check(var: bool):
    if var:
        return '✅'
    else:
        return '❌'


def permissionParser(perms):
    text = ''
    text += 'Message: ' + bool_check(perms.can_send_messages) + '\n'
    text += 'Media: ' + bool_check(perms.can_send_media_messages) + '\n'
    text += 'Sticker: ' + bool_check(perms.can_send_stickers) + '\n'
    text += 'GIF: ' + bool_check(perms.can_send_animations) + '\n'
    text += 'Game: ' + bool_check(perms.can_send_games) + '\n'
    text += 'Inline: ' + bool_check(perms.can_use_inline_bots) + '\n'
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
