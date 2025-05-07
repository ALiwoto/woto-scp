"""

"""
import logging
import asyncio
import sys
import time
from scp.utils.git_tools import getVersion
from pyromod import listen
from rich.logging import RichHandler
from .core.clients import (
    ScpClient,
    scp_loop,
)

if not type(listen):
    logging.error('Pyromod is invalid.')
    sys.exit()

RUNTIME = time.time()

__long_version__, __version__ = getVersion()

if sys.version_info[0] < 3 or sys.version_info[1] < 8:
    logging.error('Python version Lower than 3.8! Abort!')
    sys.exit()


LOG_FORMAT = (
    '%(filename)s:%(lineno)s %(levelname)s: %(message)s'
)

logging.basicConfig(
    level=logging.WARNING,
    format=LOG_FORMAT,
    datefmt='%m-%d %H:%M',
    handlers=[RichHandler()],
)
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
formatter = logging.Formatter(LOG_FORMAT)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

log = logging.getLogger()
loop = scp_loop or asyncio.get_event_loop()

bot = ScpClient('woto-scp-bot', True)
user = ScpClient('woto-scp-user', False, bot)
