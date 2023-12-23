
from configparser import ConfigParser
import typing
import logging


def list_map(func, iterator):
    return list(map(func, iterator))

class WotoConfig:
    _the_config: ConfigParser = None

    api_id: str = ''
    api_hash: str = ''
    device_model: str = ''
    app_version: str = ''
    no_input: bool = False

    _sudo_users: typing.List[int] = []
    _owner_users: typing.List[int] = []
    _special_users: typing.List[int] = []
    prefixes: typing.List[str] = []
    log_channel: int = 0
    avalon_pms: int = 0
    avalon_bots: int = 0
    avalon_tags: int = 0
    dump_usernames = []
    private_resources: int = 0
    shared_channel: int = 0
    auto_read_mode: int =  0
    gdrive_upload_folder_id: str = None
    yt_cookies_file: str = None

    _enforcers = []
    _inspectors = []
    sibyl_token: int = 0
    public_listener: int = 0
    public_logger: int = 0
    private_listener: int = 0
    private_logger:int =0

    wp_username: str = ''
    wp_password: str = ''
    wp_host: str = 'wotoplatform.kaizoku.cyou'
    wp_port: int = 50100

    _azure_sudo_users = []
    azure_api_key: str = ''
    azure_api_region: str = ''

    use_proxy :bool = False
    proxy_scheme : str = ''
    proxy_hostname : str = ''
    proxy_port : int = 0
    proxy_username : str = ''
    proxy_password : str = ''

    def __init__(self, config_file='config.ini') -> None:
        self._the_config = ConfigParser()
        self._the_config.read(config_file)

        self.api_id = self._the_config.get('pyrogram', 'api_id')
        self.api_hash = self._the_config.get('pyrogram', 'api_hash')
        self.device_model = self._the_config.get('pyrogram', 'device_model', fallback='Kaizoku v1.2')
        self.app_version = self._the_config.get('pyrogram', 'app_version', fallback='woto-scp v0.0.1')
        self.no_input = self._the_config.getboolean('pyrogram', 'no_input', fallback=False)

        self._owner_users = list_map(int, self._the_config.get('woto-scp', 'owner_list').split())
        self._sudo_users = list_map(int, self._the_config.get('woto-scp', 'sudo_list').split())
        self._special_users = list_map(int, self._the_config.get('woto-scp', 'special_users').split())
        
        self.prefixes = (
            self._the_config.get('woto-scp', 'Prefixes').split() or ['!', '.']
        )
        self.log_channel = self._the_config.getint('woto-scp', 'log_channel', fallback='')
        self.dump_usernames = self._the_config.get('woto-scp', 'public_dumps', fallback='').split()
        self.private_resources = self._the_config.getint('woto-scp', 'private_resources', fallback=0)
        self.shared_channel = self._the_config.getint('woto-scp', 'shared_channel', fallback=self.private_resources)
        self.auto_read_mode = self._the_config.getint('woto-scp', 'auto_read_mode', fallback=0)
        self.gdrive_upload_folder_id = self._the_config.get('woto-scp', 'gdrive_upload_folder_id', fallback='')
        self.yt_cookies_file = self._the_config.get('woto-scp', 'yt_cookies_file', fallback=None)

        # sibyl configuration
        try:
            self.load_sibyl_config()
        except Exception as e:
            logging.warning(e, stacklevel=3)
        
        # woto-platform configuration
        try:
            self.load_wp_config()
        except Exception as e:
            logging.warning(e, stacklevel=3)

        # microsoft-azure configuration
        try:
            self.load_azure_config()
        except Exception as e:
            logging.warning(e, stacklevel=3)

        # avalon configuration
        try:
            self.load_avalon()
        except Exception as e:
            logging.warning(e, stacklevel=3)

        # proxy configuration
        try:
            self.load_proxy()
        except Exception as e:
            logging.warning(e, stacklevel=3)
    
    def load_sibyl_config(self) -> None:
        self._enforcers = list_map(int, self._the_config.get('sibyl-system', 'enforcers').split())
        self._inspectors = list_map(int, self._the_config.get('sibyl-system', 'enforcers').split())
        self.sibyl_token = self._the_config.get('sibyl-system', 'token')
        self.public_listener = self._the_config.getint('sibyl-system', 'public_listener')
        self.public_logger = self._the_config.get('sibyl-system', 'public_logger')
        self.private_listener = self._the_config.get('sibyl-system', 'private_listener')
        self.private_logger = self._the_config.get('sibyl-system', 'private_logger')
    
    def load_wp_config(self) -> None:
        self.wp_username = self._the_config.get('woto-platform', 'username', fallback=None)
        self.wp_password = self._the_config.get('woto-platform', 'password', fallback=None)
        self.wp_host = self._the_config.get(
            'woto-platform', 
            'host', 
            fallback='wotoplatform.kaizoku.cyou'
        )
        self.wp_port = self._the_config.getint('woto-platform', 'port', fallback=50100)

    def load_azure_config(self) -> None:
        self._azure_sudo_users = list_map(
            int, self._the_config.get('microsoft-azure', 'azure_sudo_users').split())
        self.azure_api_key = self._the_config.get('microsoft-azure', 'azure_api_key')
        self.azure_api_region = self._the_config.get('microsoft-azure', 'azure_api_region')

    def load_avalon(self) -> None:
        self.avalon_pms = self._the_config.getint('avalon', 'avalon_pms', fallback=0)
        self.avalon_bots = self._the_config.getint('avalon', 'avalon_bots', fallback=0)
        self.avalon_tags = self._the_config.getint('avalon', 'avalon_tags', fallback=0)

    def load_proxy(self) -> None:
        self.use_proxy = self._the_config.getboolean('proxy', 'use_proxy', fallback=False)
        self.proxy_scheme = self._the_config.get('proxy', 'scheme', fallback='')
        self.proxy_hostname = self._the_config.get('proxy', 'hostname', fallback='')
        self.proxy_port = self._the_config.getint('proxy', 'port', fallback=0)
        self.proxy_username = self._the_config.get('proxy', 'username', fallback=None)
        self.proxy_password = self._the_config.get('proxy', 'password', fallback=None)


    def is_sudo(self, user: int) -> bool:
        return user in self._owner_users or user in self._sudo_users
    
    def is_owner(self, user: int) -> bool:
        return user in self._owner_users
    
    def is_only_sudo(self, user: int) -> bool:
        return user in self._sudo_users



the_config: WotoConfig = WotoConfig()
