# SibylSystem-py

# Copyright (C) 2021 Sayan Biswas, AnonyIndian

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import httpx
import typing
import json
from datetime import datetime

from .exceptions import(
    GeneralException,
    InvalidTokenException,
    InvalidPermissionRangeException,
)

from .types import(
    Ban, 
    Token,
    BanRes, 
    BanResult, 
    GeneralInfo,
    StatsResult, 
    MultiBanInfo,
    ReportResponse,
    TokenValidation,
    PermissionResponse, 
) 

__version__ = '0.0.12'


class PsychoPass:
    """
    Class for the Sibyl API client
    
    Args:
        token (:obj:`str`): Sibyl API token
        host (:obj:`str`, optional): Sibyl API service URL.
        client (:obj:`httpx.Client`, optional): HTTPX client class.
        show_license (:obj:`bool`, optional): Defaults to true, set to false to hide copyright message
    """

    def __init__(self, token: str, host: typing.Optional[str] = "https://psychopass.animekaizoku.com/",
                 client: typing.Optional[httpx.Client] = None, show_license: bool = True) -> None:
        if show_license:
            l = '''
    SibylSystem-Py Copyright (C) 2021 Sayan Biswas, AnonyIndian, AliWoto
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions.
            '''
            print(l)
        if not host.endswith("/"):
            host += "/"
        if not host.startswith("http"):
            host = "http://" + host
        self.host = host
        self.token = token
        self.client = client
        if not self.client:
            self.client = httpx.Client()
        if not self.check_token(self.token):
            raise InvalidTokenException()

    def check_token(self, token: str) -> bool:
        """
        Check if Sibyl API token is valid
        
        Args:
            token (:obj:`str`): Sibyl API token

        Raises:
            InvalidTokenException

        Returns:
            bool: if the token is valid, it will return True, else False
        """
        params = {'token': token}
        r = self.client.get(f"{self.host}checkToken", params=params)
        x = TokenValidation(**r.json())
        if not x.success:
            raise InvalidTokenException()
        return x.result

    def create_token(self, user_id: int, permission: int = 0) -> Token:
        """
        Create new token, with a user id and permission number
        
            0 = User,
            1 = Enforcer,
            2 = Inspector
        
        Args:
            user_id (:obj:`int`): User Id of the user for the token to be assigned to.
            permission (:obj:`int`, optional): [Permission of user]. Defaults to 0.

        Raises:
            InvalidPermissionRangeException
            GeneralException

        Returns:
            Token
        """
        if permission > 2:
            raise InvalidPermissionRangeException("Permission can be 0, 1, 2, not {}".format(permission))
        d = self._prepare_url(
            'createToken', user_id, permission
        )

        return Token(**d["result"])

    def revoke_token(self, user_id: int):
        return self._token_method(
            'revokeToken', user_id
        )

    def change_permission(self, user_id: int, permission: int) -> PermissionResponse:
        """Change permission of given user
            
            0 = User,
            1 = Enforcer,
            2 = Inspector
            
        Args:
            user_id (:obj:`int`): User Id of the user to be promoted/demoted
            permission (:obj:`int`): new permission of user, can be 0, 1, 2

        Raises:
            GeneralException

        Returns:
            PermissionResponse
        """
        d = self._prepare_url(
            'changePerm', user_id, permission
        )

        return PermissionResponse(**d)

    def _prepare_url(self, method: str, user_id: int, permission: int):
        params = {
            'token': self.token,
            'user-id': str(user_id),
            'permission': str(permission)
        }
        r = self.client.get(url=f'{self.host}{method}', params=params)

        result = r.json()
        if not result['success']:
            raise GeneralException(result['error']['message'])
        return result

    def get_token(self, user_id: int):
        return self._token_method('getToken?token=', user_id)

    def _token_method(self, method: str, user_id: int):
        headers = {
            'token': self.token,
            'user-id': str(user_id)
        }
        r = self.client.get(f'{self.host}{method}', headers=headers)
        d = r.json()
        if not d["success"]:
            raise GeneralException(d['error']["message"])
        return Token(**d['result'])

    def multi_ban(self, info: typing.List[MultiBanInfo]) -> str:
        """Add multiple ban to sibyl system.

        Args:
            info (:obj:`dict[MultiBanInfo]`): The multiban info.

        Raises:
            GeneralException

        Returns:
            str
        """
        headers = {
            'token': self.token,
        }

        infoList = [i.to_dict() for i in info]
        jData = json.dumps({"users": infoList})

        r = self.client.post(
            f"{self.host}multiBan", headers=headers, data=jData)

        j = r.json()

        if not j["success"]:
            raise GeneralException(j["error"]["message"])
        return j["result"]

    def multi_unban(self, users: typing.List[int]) -> str:
        """push multiple unban request to sibyl system.

        Args:
            users (:obj:`dict[int]`): The users IDs to be unbanned.

        Raises:
            GeneralException

        Returns:
            str
        """
        headers = {
            'token': self.token,
        }
        
        
        jData = json.dumps({"users": users})
        
        r = self.client.post(
            f"{self.host}multiUnBan", headers=headers, data=jData)
            
        j = r.json()

        if not j["success"]:
            raise GeneralException(j["error"]["message"])
        return j["result"]

    def add_ban(self, user_id: int, reason: str, message: typing.Optional[str] = None,
                source: typing.Optional[str] = None,
                is_bot: typing.Optional[bool] = False) -> BanRes:
        """Add a new ban to database

        Args:
            user_id (:obj:`int`): User Id of the user to be banned
            reason (:obj:`str`): reason of the ban
            message (:obj:`str`, optional): [Ban message, basically the message the given user was banned upon.]. Defaults to None.
            source (:obj:`str`, optional): [Ban source, the message link to the message the user was banned upon]. Defaults to None.
            is_bot (:obj:`str`, optional): Define whether the user being banned is a bot or not, defaults to False

        Raises:
            GeneralException

        Returns:
            BanResult
        """
        params = {
            'token': self.token,
            'user-id': str(user_id),
            'isBot': str(is_bot)
        }
        if message is not None:
            params['message'] = message
        if reason is not None:
            params['reason'] = reason
        if source is not None:
            params['source'] = source

        r = self.client.get(
            f"{self.host}addBan", params=params)
        d = BanResult(**r.json())
        if not d.success:
            raise GeneralException(d.error["message"])
        return d.result


    def delete_ban(self, user_id: int) -> bool:
        """Unban a user

        Args:
            user_id (:obj:`int`): User ID of the user to be unbanned

        Raises:
            GeneralException

        Returns:
            bool
        """
        self._check_response('removeBan', user_id)
        return True

    def get_info(self, user_id: int) -> Ban:
        """Get info about a user on the API

        Args:
            user_id (:obj:`int`): User ID of the user to be looked up

        Raises:
            GeneralException

        Returns:
            Ban
        """
        r = self._check_response('getInfo', user_id).json()["result"]
        r["date"] = datetime.strptime(r["date"], "%Y-%m-%d at %H:%M:%S")
        return Ban(**r)

    def _check_response(self, method, user_id):
        params = {
            'token': self.token,
            'user-id': str(user_id)
        }
        result = self.client.get(f'{self.host}{method}', params=params)
        d = result.json()
        if not d['success']:
            raise GeneralException(d['error']['message'])
        return result

    def report_user(self, user_id: int, reason: str, message: str, source_url: str = None,
                    is_bot: typing.Optional[bool] = False) -> bool:
        """Report a user, on the API, to be worked upon by the inspectors

        Args:
            user_id (:obj:`int`): User Id of the user to be report
            reason (:obj:`str`): reason of the ban
            message (:obj:`str`): Ban message, basically the message the given user to be banned upon.
            source_url (:obj:`str`, optional): Ban source, the message link to the message the user was banned upon.
            is_bot (:obj:`bool`, optional): Define whether the user being banned is a bot or not, defaults to False.

        Raises:
            GeneralException

        Returns:
            bool
        """
        data = {
            'token': self.token,
            'user-id': str(user_id),
            'reason': reason,
            'message': message,
            'isBot': str(is_bot)
        }
        if source_url is not None:
            data['src'] = source_url

        r = self.client.get(
            f"{self.host}reportUser", params=data)
        d = ReportResponse(**r.json())
        if d.success:
            return True
        raise GeneralException(d.error["message"])

    def get_stats(self) -> StatsResult:
        """Get stats from API

        Raises:
            GeneralException

        Returns:
            StatsResult
        """
        params = {
            'token': self.token
        }
        r = self.client.get(f"{self.host}stats", params=params)
        d = StatsResult(**r.json())
        if d.success:
            return d
        raise GeneralException(d.error["message"])
    
    def get_general_info(self, user_id: int) -> GeneralInfo:
        """

        Args:
            user_id (:obj:`int`): User ID of the user to be looked up

        Raises:
            GeneralException

        Returns:
            GeneralInfo
        """
        params = {
            'token': self.token,
            'user-id': str(user_id)
        }
        r = self.client.get(f"{self.host}getGeneralInfo", params=params)
        d = GeneralInfo(**r.json())
        if d.success:
            return d
        raise GeneralException(d.error["message"])