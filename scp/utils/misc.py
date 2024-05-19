import os
import sys
import signal
import psutil
from pyrogram import types
import pyrogram

from scp.utils.str_utils import remove_invisible

class _KB(types.InlineKeyboardButton):
    def __eq__(self, other):
        return self.text == other.text

    def __lt__(self, other):
        return self.text < other.text

    def __gt__(self, other):
        return self.text > other.text


def paginate_modules(_, module_dict, prefix, chat=None):
    if not chat:
        modules = sorted(
            [
                _KB(
                    x.__PLUGIN__,
                    callback_data='{}_module({})'.format(
                        prefix, x.__PLUGIN__.lower(),
                    ),
                )
                for x in module_dict.values()
            ],
        )
    else:
        modules = sorted(
            [
                _KB(
                    x.__MODULE__,
                    callback_data='{}_module({},{})'.format(
                        prefix, chat, x.__MODULE__.lower(),
                    ),
                )
                for x in module_dict.values()
            ],
        )

    pairs = [
        modules[
            i * 3: (i + 1) * 3
        ] for i in range(
            (len(modules) + 3 - 1) // 3,
        )
    ]
    round_num = len(modules) / 3
    calc = len(modules) - round(round_num)
    if calc in [1, 2]:
        pairs.append((modules[-1],))
    return pairs

def can_user_match(user: types.User, query: str) -> bool:
    query = remove_special_chars(query)
    if not user or len(query) < 2:
        return False

    if user.first_name and len(user.first_name) > 0 and can_str_param_match(user.first_name, query):
        return True
    
    if user.last_name and len(user.last_name) > 0 and can_str_param_match(user.last_name, query):
        return True
    
    if user.username and len(user.username) > 0 and can_str_param_match(user.username, query):
        return True
    
    if user.status and len(user.status) > 0 and can_str_param_match(user.status, query):
        return True

    return False


async def can_member_match(m: types.ChatMember, client: pyrogram.Client, query: str) -> bool:
    user = m.user
    query = remove_special_chars(query)
    if not user or len(query) < 2:
        return False

    if user.first_name and len(user.first_name) > 0 and can_str_param_match(user.first_name, query):
        return True
    
    if user.last_name and len(user.last_name) > 0 and can_str_param_match(user.last_name, query):
        return True
    
    if user.username and len(user.username) > 0 and can_str_param_match(user.username, query):
        return True
    
    if user.status and len(user.status) > 0 and can_str_param_match(user.status, query):
        return True
    
    if m.title and len(m.title) > 0 and can_str_param_match(m.title, query):
        return True
    
    if not client: return False
    ch = await client.get_chat(user.id)

    if ch:
        if ch.bio and len(ch.bio) > 0 and can_str_param_match(ch.bio, query):
            return True

    return False


def can_str_param_match(param: str, query: str) -> bool:
    return remove_special_chars(param).find(query) != -1

def remove_special_chars(value: str) -> str:
    if isinstance(value, list):
        value = ' '.join(value)
    value = remove_invisible(value.lower().strip())
    last_space = False
    result = ''
    for current in value:
        o = ord(current)
        if current == " ":
            if last_space:
                continue
            last_space = True
            result += " "
            continue
        elif last_space:
            last_space = False
        
        if current.isspace() or o < 65:
            continue
        if o > 122 and o < 250:
            continue
        if o > 90 and o < 97:
            result += " "
            continue
        
        result += current
    
    return result

def restart_scp(update_req: bool = False, hard: bool = False, extra_args = None) -> bool:
    """ Restart the woto-scp """
    if update_req:
        os.system(  # nosec
            "pip install -U pip && pip install -r requirements.txt --quiet",
        )
    
    if hard:
        os.kill(os.getpid(), signal.SIGUSR1)
    else:
        c_p = psutil.Process(os.getpid())
        for handler in c_p.open_files() + c_p.connections():
            try:
                # check if handler is stdin or stdout or stderr
                if handler.fd == 0 or handler.fd == 1 or handler.fd == 2:
                    continue
                os.close(handler.fd)
                
            except Exception:
                continue
        
        the_arg = "scp"
        if extra_args:
            for arg in extra_args:
                the_arg += f" {arg}"
        os.execl(sys.executable, sys.executable, '-m', the_arg)  # nosec
    
    return True
    
