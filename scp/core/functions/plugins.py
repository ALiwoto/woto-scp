import importlib
from scp.plugins.bot import ALL_SETTINGS
from scp.plugins.user import ALL_MODULES
from os.path import dirname, basename, isfile
import glob
from pathlib import Path


HELP_COMMANDS = {}


async def load_bot_plugins():
    for setting in ALL_SETTINGS:
        importlib.import_module(
            'scp.plugins.bot.' + setting,
        )


async def load_user_plugins():
    for current_module in ALL_MODULES:
        imported_module = importlib.import_module('scp.plugins.user.' + current_module)
        if hasattr(
            imported_module,
            '__PLUGIN__',
        ) and imported_module.__PLUGIN__:
            imported_module.__PLUGIN__ = imported_module.__PLUGIN__
        if hasattr(
            imported_module,
            '__PLUGIN__',
        ) and imported_module.__PLUGIN__:
            if imported_module.__PLUGIN__.lower() not in HELP_COMMANDS:
                HELP_COMMANDS[
                    imported_module.__PLUGIN__.lower()
                ] = imported_module
            else:
                raise Exception(
                    "Can't have two modules with the same name!",
                )
        if hasattr(imported_module, '__DOC__') and imported_module.__DOC__:
            HELP_COMMANDS[imported_module.__PLUGIN__.lower()] = imported_module


async def load_private_plugins():
    def __list_all_modules():
        mod_paths = glob.glob(
            dirname(Path(__file__).parent.parent) + '/plugins/private/*.py',
        )
        return [
            basename(f)[:-3]
            for f in mod_paths
            if isfile(f) and f.endswith('.py')
        ]
    for current_module in sorted(__list_all_modules()):
        imported_module = importlib.import_module(
            'scp.plugins.private.' + current_module,
        )
        if hasattr(
            imported_module,
            '__PLUGIN__',
        ) and imported_module.__PLUGIN__:
            imported_module.__PLUGIN__ = imported_module.__PLUGIN__
        if hasattr(
            imported_module,
            '__PLUGIN__',
        ) and imported_module.__PLUGIN__:
            if imported_module.__PLUGIN__.lower() not in HELP_COMMANDS:
                HELP_COMMANDS[
                    imported_module.__PLUGIN__.lower()
                ] = imported_module
            else:
                raise Exception(
                    "Can't have two modules with the same name!",
                )
        if hasattr(imported_module, '__DOC__') and imported_module.__DOC__:
            HELP_COMMANDS[imported_module.__PLUGIN__.lower()] = imported_module
