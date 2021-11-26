import os
import sys
import signal
import psutil
from pyrogram.types import InlineKeyboardButton
from pyrogram import Client

class _KB(InlineKeyboardButton):
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


async def restart_scp(user: Client, update_req: bool = False, hard: bool = False) -> None:
        """ Restart the woto-scp """
        await user.stop()
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
            sys.exit()
