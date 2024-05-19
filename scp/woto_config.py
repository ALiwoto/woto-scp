
from configparser import ConfigParser
import typing
import logging
import io
import os
import sys
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from base64 import b64encode, b64decode
from os import urandom
import hashlib


def list_map(func, iterator):
    if not iterator: return []
    return list(map(func, iterator))



class AESCipher:
    def __init__(self, key: str, fav_letter: str):
        if len(key) > 32:
            raise ValueError("Key length must be 32 bytes or less")
        elif len(key) < 32:
            key = key.ljust(len(key) + (32 - len(key) % 32), fav_letter)

        key = key.encode('utf-8')
        if len(key) != 32:
            raise ValueError("Key length must be 32 bytes")
        
        self.key = key
        self.backend = default_backend()

    def encrypt(self, plaintext):
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        iv = urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return b64encode(iv + ciphertext).decode('utf-8')

    def decrypt(self, b64_encrypted_data):
        encrypted_data = b64decode(b64_encrypted_data)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        unpadder = padding.PKCS7(128).unpadder()
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext


class WotoConfig:
    _the_config: ConfigParser = None
    _encrypted_magic_str: str = "_RFL4"
    _passing_key_magic_str = "_P4SS"

    api_id: str = ''
    api_hash: str = ''
    device_model: str = ''
    app_version: str = ''
    no_input: bool = False

    _sudo_users: typing.List[int] = []
    _owner_users: typing.List[int] = []
    _special_users: typing.List[int] = []
    _special_channels: typing.List[int] = []
    _rfl_value: str = None
    prefixes: typing.List[str] = []
    log_channel: int = 0
    chat_join_shield: typing.List[int] = []
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
    wp_host: str = None
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

    pixiv_access_token : str = ''
    pixiv_refresh_token : str = ''

    def __init__(self, config_file='config.ini') -> None:
        self._the_config = ConfigParser()
        self._the_config.read_string(self._load_config_content(config_file))

        self.api_id = self._the_config.get('pyrogram', 'api_id')
        self.api_hash = self._the_config.get('pyrogram', 'api_hash')
        self.device_model = self._the_config.get('pyrogram', 'device_model', fallback='Kaizoku v1.2')
        self.app_version = self._the_config.get('pyrogram', 'app_version', fallback='woto-scp v0.0.1')
        self.no_input = self._the_config.getboolean('pyrogram', 'no_input', fallback=False)

        self._owner_users = list_map(int, self._the_config.get('woto-scp', 'owner_list').split())
        self._sudo_users = list_map(int, self._the_config.get('woto-scp', 'sudo_list').split())
        self._special_users = list_map(int, self._the_config.get('woto-scp', 'special_users').split())
        self._special_channels = list_map(int, self._the_config.get('woto-scp', 'special_channels', fallback='').split())
        
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
        
        # pixiv configuration
        try:
            self.load_pixiv()
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
    
    def load_pixiv(self) -> None:
        self.pixiv_access_token = self._the_config.get('pixiv', 'access_token', fallback='')
        self.pixiv_refresh_token = self._the_config.get('pixiv', 'refresh_token', fallback='')

    def _get_suitable_rfl(self) -> str:
        for current in sys.argv:
            if current.startswith(self._passing_key_magic_str):
                return current[len(self._passing_key_magic_str):]
        return None
    
    def _decompress_rfl(self, rfl: str) -> typing.Tuple[str, str]:
        if not rfl:
            raise ValueError("No suitable rfl found")
        
        aes_cipher = AESCipher(
            self._passing_key_magic_str + self.__class__.__name__, "w")
        decrypted = aes_cipher.decrypt(b64decode(rfl.encode("utf-8")))
        return decrypted[32:64].decode("utf-8"), decrypted[64:].decode('utf-8')
    
    def _load_config_content(self, file_path: str) -> str:
        is_encrypted = False
        # first check if file.enc exists
        if os.path.exists(file_path+".enc"):
            file_path += ".enc"
            is_encrypted = True
        
        the_content: str = None
        with open(file_path, 'r') as f:
            the_content = f.read()
            # check if it starts with the magic string
            if the_content and the_content.startswith(self._encrypted_magic_str):
                is_encrypted = True
        
        if is_encrypted:
            the_content = the_content[len(self._encrypted_magic_str):]
            the_content = b64decode(the_content).decode('utf-8')
            suitable_rfl = self._get_suitable_rfl()
            if not suitable_rfl:
                user_key = input("Password-protected config file detected. Enter your key:")
                fav_letter = input("Enter your favorite letter: ")
            else:
                user_key, fav_letter = self._decompress_rfl(suitable_rfl)
            return self.decrypt_config(the_content, user_key, fav_letter)

        return the_content
    
    def decrypt_config(self, file_content: str, key: str, fav_letter: str) -> str:
        all_strs = file_content.split("\n")
        encrypted_content = all_strs[0x05]
        content_signature = all_strs[0x0a]

        aes_cipher = AESCipher(key, fav_letter)
        decrypted = aes_cipher.decrypt(encrypted_content)
        sha512_signature = hashlib.sha512(decrypted).hexdigest()

        if sha512_signature != content_signature:
            raise ValueError("Content has been tampered with. Signature mismatch")
        
        self._rfl_value = self._passing_key_magic_str
        rfl_aes_cipher = AESCipher(
            self._passing_key_magic_str + self.__class__.__name__, "w")
        
        self._rfl_value += b64encode(
            rfl_aes_cipher.encrypt(
                urandom(32) +
                aes_cipher.key +
                fav_letter.encode("utf-8")
            ).encode("utf-8")).decode('utf-8')
        return decrypted.decode('utf-8')

    def gen_encrypted_config(self, file_path: str, key: str, fav_letter: str) -> None:
        the_content = io.StringIO()
        self._the_config.write(the_content)
        the_content = the_content.getvalue()
        aes_cipher = AESCipher(key, fav_letter)
        encrypted = aes_cipher.encrypt(the_content)
        sha512_signature = hashlib.sha512(the_content.encode("utf-8")).hexdigest()

        output_str =  "-------------------------------\n"
        output_str += "-----BEGIN ENCRYPTED BLOCK-----\n"
        output_str += "--THIS FILE IS AUTO GENERATED--\n"
        output_str += "-----DO NOT EDIT OR MODIFY-----\n"
        output_str += "-------------------------------\n"
        output_str += f"{encrypted}\n"
        output_str += "-------------------------------\n"
        output_str += "-----END ENCRYPTED BLOCK-------\n"
        output_str += "-------------------------------\n"
        output_str += "-----BEGIN SIGNATURE BLOCK-----\n"
        output_str += f"{sha512_signature}\n"
        output_str += "-----END SIGNATURE BLOCK-------\n"
        output_str += "-------------------------------\n"

        with open(file_path, 'w') as f:
            f.write(self._encrypted_magic_str + b64encode(output_str.encode("utf-8")).decode('utf-8'))

    def is_sudo(self, user: int) -> bool:
        return user in self._owner_users or user in self._sudo_users
    
    def is_owner(self, user: int) -> bool:
        return user in self._owner_users
    
    def is_only_sudo(self, user: int) -> bool:
        return user in self._sudo_users


the_config: WotoConfig = WotoConfig()
