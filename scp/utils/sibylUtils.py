from sibylsystem.SibylSystem import PsychoPass
from typing import List, Any, TypeVar, Callable, Type, cast
from httpx import Response
from sibylsystem.SibylSystem.exceptions import GeneralException
from sibylsystem.SibylSystem.types.stats import StatsResult























class UserInfo:
    user_id: int
    banned: bool
    reason: str
    message: str
    ban_source_url: str
    banned_by: int
    crime_coefficient: int
    date: str
    ban_flags: List[str]

    def __init__(self, user_id: int, banned: bool, reason: str, message: str, ban_source_url: str, banned_by: int, crime_coefficient: int, date: str, ban_flags: List[str]) -> None:
        self.user_id = user_id
        self.banned = banned
        self.reason = reason
        self.message = message
        self.ban_source_url = ban_source_url
        self.banned_by = banned_by
        self.crime_coefficient = crime_coefficient
        self.date = date
        self.ban_flags = ban_flags

    @staticmethod
    def from_dict(obj: Any) -> 'UserInfo':
        assert isinstance(obj, dict)
        user_id = from_int(obj.get("user_id"))
        banned = from_bool(obj.get("banned"))
        reason = from_str(obj.get("reason"))
        message = from_str(obj.get("message"))
        ban_source_url = from_str(obj.get("ban_source_url"))
        banned_by = from_int(obj.get("banned_by"))
        crime_coefficient = from_int(obj.get("crime_coefficient"))
        date = from_str(obj.get("date"))
        ban_flags = from_list(from_str, obj.get("ban_flags"))
        return UserInfo(user_id, banned, reason, message, ban_source_url, banned_by, crime_coefficient, date, ban_flags)

    def to_dict(self) -> dict:
        result: dict = {}
        result["user_id"] = from_int(self.user_id)
        result["banned"] = from_bool(self.banned)
        result["reason"] = from_str(self.reason)
        result["message"] = from_str(self.message)
        result["ban_source_url"] = from_str(self.ban_source_url)
        result["banned_by"] = from_int(self.banned_by)
        result["crime_coefficient"] = from_int(self.crime_coefficient)
        result["date"] = from_str(self.date)
        result["ban_flags"] = from_list(from_str, self.ban_flags)
        return result


class UserBannedResult:
    previous_ban: UserInfo
    current_ban: UserInfo

    def __init__(self, previous_ban: UserInfo, current_ban: UserInfo) -> None:
        self.previous_ban = previous_ban
        self.current_ban = current_ban

    @staticmethod
    def from_dict(obj: Any) -> 'UserBannedResult':
        assert isinstance(obj, dict)
        previous_ban = UserInfo.from_dict(obj.get("previous_ban"))
        current_ban = UserInfo.from_dict(obj.get("current_ban"))
        return UserBannedResult(previous_ban, current_ban)

    def to_dict(self) -> dict:
        result: dict = {}
        result["previous_ban"] = to_class(UserInfo, self.previous_ban)
        result["current_ban"] = to_class(UserInfo, self.current_ban)
        return result


class BanResponse:
    success: bool
    result: UserBannedResult
    error: None

    def __init__(self, success: bool, result: UserBannedResult, error: None) -> None:
        self.success = success
        self.result = result
        self.error = error

    @staticmethod
    def from_dict(obj: Any) -> 'BanResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        result = UserBannedResult.from_dict(obj.get("result"))
        error = from_none(obj.get("error"))
        return BanResponse(success, result, error)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        result["result"] = to_class(UserBannedResult, self.result)
        result["error"] = from_none(self.error)
        return result


def BanResponse_from_dict(s: Any) -> BanResponse:
    return BanResponse.from_dict(s)






class SibylClient(PsychoPass):
    def __init__(self, token: str):
        super().__init__(token, show_license=False)

    def revert(self, user_id: int) -> bool:
        r = self.client.get(f"{self.host}removeBan?token={self.token}&user-id={user_id}")
        j = r.json()
        if self.is_success(j):
            return j['result']
        raise GeneralException(j['error']['message'])
    
    def revert_ban(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
    def remove_ban(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
    def clear_ban(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
    def ban(self, user_id: int, reason: str, message: str=None, source: str=None) -> UserBannedResult:
        r = self.client.get((f"{self.host}addBan?token={self.token}"+
            f"&user-id={user_id}&reason={reason}&message={message}&source={source}"))
        j = r.json()
        if not self.is_success(j):
            raise GeneralException(j["error"]["message"])
        the_resp = BanResponse_from_dict(j)
        return the_resp.result
    
    def ban_user(self, user_id: int, reason: str, message: str=None, source: str=None) -> UserBannedResult:
        return self.ban(user_id, reason, message, source)

    def stats(self) -> StatsResult:
        resp = self.invoke_request(f"{self.host}stats?token={self.token}")
        if not self.is_success(resp):
            raise GeneralException(resp["error"]["message"])
        return StatsResult(**resp)

    def is_success(self, jsonResp) -> bool:
        return jsonResp['success']
    
    def invoke_request(self, url: str):
        return self.client.get(url).json()
    
    


T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_none(x: Any) -> Any:
    assert x is None
    return x
    
