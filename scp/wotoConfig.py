
from configparser import ConfigParser
import typing

class WotoConfig:
    _the_config: ConfigParser = None
    _sudo_users: typing.List[int] = []
    _owner_users: typing.List[int] = []
    prefixes: typing.List[str] = []
    log_channel: int = 0
    api_id: str = ''
    api_hash: str = ''
    _enforcers = []
    _inspectors = []
    dump_usernames = []
    private_resources: int = 0
    sibyl_token: int = 0
    public_listener: int = 0
    public_logger: int = 0
    private_listener: int = 0
    private_logger:int =0
    wp_username: str = ''
    wp_password: str = ''
    wp_host: str = 'wotoplatform.hakai.animekaizoku.com'
    wp_port: int = 50100

    def __init__(self) -> None:
        self._the_config = ConfigParser()
        self._the_config.read('config.ini')

        self.api_id = self._the_config.get('pyrogram', 'api_id')
        self.api_hash = self._the_config.get('pyrogram', 'api_hash')

        for x in self._the_config.get('scp-5170', 'OwnerList').split():
            self._owner_users.append(int(x))
        
        for x in self._the_config.get('scp-5170', 'SudoList').split():
            self._sudo_users.append(int(x))
        
        self.prefixes = (
            self._the_config.get('scp-5170', 'Prefixes').split() or ['!', '.']
        )
        self.log_channel = self._the_config.getint('scp-5170', 'log_channel')

        try:
            for x in self._the_config.get('sibyl-system', 'enforcers').split():
                self._enforcers.append(int(x))
        except Exception as e:
            print(e)
        
        try:
            for x in self._the_config.get('sibyl-system', 'inspectors').split():
                self._inspectors.append(int(x))
        except Exception as e:
            print(e)
        
        for x in self._the_config.get('scp-5170', 'public_dumps').split():
            self.dump_usernames.append(x)

        self.private_resources = self._the_config.getint('scp-5170', 'private_resources')
        # sibyl configuration stuff:
        self.sibyl_token = self._the_config.get('sibyl-system', 'token')
        self.public_listener = self._the_config.getint('sibyl-system', 'public_listener')
        self.public_logger = self._the_config.get('sibyl-system', 'public_logger')
        self.private_listener = self._the_config.get('sibyl-system', 'private_listener')
        self.private_logger = self._the_config.get('sibyl-system', 'private_logger')


        self.wp_username = self._the_config.get('woto-platform', 'username')
        self.wp_password = self._the_config.get('woto-platform', 'password')
        self.wp_host = self._the_config.get(
            'woto-platform', 
            'host', 
            fallback='wotoplatform.hakai.animekaizoku.com'
        )
        self.wp_port = self._the_config.getint('woto-platform', 'port', fallback=50100)
    
    def is_sudo(self, user: int) -> bool:
        return user in self._owner_users or user in self._sudo_users
    
    def is_owner(self, user: int) -> bool:
        return user in self._owner_users
    
    def is_only_sudo(self, user: int) -> bool:
        return user in self._sudo_users



the_config: WotoConfig = WotoConfig()
