import os
import sys
import signal
import psutil
from pyrogram import types

from scp.utils.strUtils import remove_invisible

class _KB(types.InlineKeyboardButton):
    def __eq__(self, other):
        return self.text == other.text

    def __lt__(self, other):
        return self.text < other.text

    def __gt__(self, other):
        return self.text > other.text


def paginate_modules(_page_n, module_dict, prefix, chat=None):
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


def can_member_match(m: types.ChatMember, query: str) -> bool:
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
    
    if user.status and len(user.status) > 0 and can_str_param_match(user.username, query):
        return True
    
    if m.title and len(m.title) > 0 and can_str_param_match(user.username, query):
        return True

    return False




def can_str_param_match(param: str, query: str) -> bool:
    return remove_special_chars(param).find(query) != -1

def remove_special_chars(value: str) -> str:
    value = remove_invisible(value.lower().strip())
    last_space = False
    result = ''
    for current in value:
        o = ord(current)
        if current == " ":
            if last_space:
                continue
            result += " "
            continue
        elif last_space:
            last_space = False
        if current.isspace() or o < 65:
            continue
        if o > 122 and o < 250:
            continue
        result += value
    
    return result

def restart_scp(update_req: bool = False, hard: bool = False) -> None:
        """ Restart the woto-scp """
        if update_req:
            os.system(  # nosec
                "pip install -U pip && pip install -r requirements.txt --quiet")
        
        if hard:
            os.kill(os.getpid(), signal.SIGUSR1)
        else:
            c_p = psutil.Process(os.getpid())
            for handler in c_p.open_files() + c_p.connections():
                os.close(handler.fd)
            os.execl(sys.executable, sys.executable, '-m', 'scp')  # nosec
