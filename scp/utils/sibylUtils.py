from pyrogram.types.user_and_chats.user import User
from sibylsystem.SibylSystem import PsychoPass
from sibylsystem.SibylSystem.types import (
    Ban,
)
from typing import List, Dict, Any, TypeVar, Callable, Type, cast
from sibylsystem.SibylSystem.exceptions import GeneralException
from sibylsystem.SibylSystem.types.bans import BanRes

class StatsResult:
    banned_count: int
    trolling_ban_count: int
    spam_ban_count: int
    evade_ban_count: int
    custom_ban_count: int
    psycho_hazard_ban_count: int
    mal_imp_ban_count: int
    nsfw_ban_count: int
    spam_bot_ban_count: int
    raid_ban_count: int
    mass_add_ban_count: int
    cloudy_count: int
    token_count: int
    inspectors_count: int
    enforces_count: int

    def __init__(
            self, banned_count: int, 
            trolling_ban_count: int, 
            spam_ban_count: int, 
            evade_ban_count: int, 
            custom_ban_count: int, 
            psycho_hazard_ban_count: int, 
            mal_imp_ban_count: int, 
            nsfw_ban_count: int, 
            spam_bot_ban_count: int, 
            raid_ban_count: int, 
            mass_add_ban_count: int, 
            cloudy_count: int, 
            token_count: int, 
            inspectors_count: int, 
            enforces_count: int) -> None:
        self.banned_count = banned_count
        self.trolling_ban_count = trolling_ban_count
        self.spam_ban_count = spam_ban_count
        self.evade_ban_count = evade_ban_count
        self.custom_ban_count = custom_ban_count
        self.psycho_hazard_ban_count = psycho_hazard_ban_count
        self.mal_imp_ban_count = mal_imp_ban_count
        self.nsfw_ban_count = nsfw_ban_count
        self.spam_bot_ban_count = spam_bot_ban_count
        self.raid_ban_count = raid_ban_count
        self.mass_add_ban_count = mass_add_ban_count
        self.cloudy_count = cloudy_count
        self.token_count = token_count
        self.inspectors_count = inspectors_count
        self.enforces_count = enforces_count

    @staticmethod
    def from_dict(obj: Any) -> 'StatsResult':
        assert isinstance(obj, dict)
        banned_count = from_int(obj.get("banned_count"))
        trolling_ban_count = from_int(obj.get("trolling_ban_count"))
        spam_ban_count = from_int(obj.get("spam_ban_count"))
        evade_ban_count = from_int(obj.get("evade_ban_count"))
        custom_ban_count = from_int(obj.get("custom_ban_count"))
        psycho_hazard_ban_count = from_int(obj.get("psycho_hazard_ban_count"))
        mal_imp_ban_count = from_int(obj.get("mal_imp_ban_count"))
        nsfw_ban_count = from_int(obj.get("nsfw_ban_count"))
        spam_bot_ban_count = from_int(obj.get("spam_bot_ban_count"))
        raid_ban_count = from_int(obj.get("raid_ban_count"))
        mass_add_ban_count = from_int(obj.get("mass_add_ban_count"))
        cloudy_count = from_int(obj.get("cloudy_count"))
        token_count = from_int(obj.get("token_count"))
        inspectors_count = from_int(obj.get("inspectors_count"))
        enforces_count = from_int(obj.get("enforces_count"))
        return StatsResult(
            banned_count, 
            trolling_ban_count, 
            spam_ban_count, 
            evade_ban_count,
            custom_ban_count, 
            psycho_hazard_ban_count, 
            mal_imp_ban_count, 
            nsfw_ban_count, 
            spam_bot_ban_count, 
            raid_ban_count, 
            mass_add_ban_count, 
            cloudy_count, 
            token_count, 
            inspectors_count, 
            enforces_count
        )

    def to_dict(self) -> dict:
        result: dict = {}
        result["banned_count"] = from_int(self.banned_count)
        result["trolling_ban_count"] = from_int(self.trolling_ban_count)
        result["spam_ban_count"] = from_int(self.spam_ban_count)
        result["evade_ban_count"] = from_int(self.evade_ban_count)
        result["custom_ban_count"] = from_int(self.custom_ban_count)
        result["psycho_hazard_ban_count"] = from_int(self.psycho_hazard_ban_count)
        result["mal_imp_ban_count"] = from_int(self.mal_imp_ban_count)
        result["nsfw_ban_count"] = from_int(self.nsfw_ban_count)
        result["spam_bot_ban_count"] = from_int(self.spam_bot_ban_count)
        result["raid_ban_count"] = from_int(self.raid_ban_count)
        result["mass_add_ban_count"] = from_int(self.mass_add_ban_count)
        result["cloudy_count"] = from_int(self.cloudy_count)
        result["token_count"] = from_int(self.token_count)
        result["inspectors_count"] = from_int(self.inspectors_count)
        result["enforces_count"] = from_int(self.enforces_count)
        return result


class StatsResponse:
    success: bool
    result: StatsResult
    error: None

    def __init__(self, success: bool, result: StatsResult, error: None) -> None:
        self.success = success
        self.result = result
        self.error = error

    @staticmethod
    def from_dict(obj: Any) -> 'StatsResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        result = StatsResult.from_dict(obj.get("result"))
        error = from_none(obj.get("error"))
        return StatsResponse(success, result, error)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        result["result"] = to_class(StatsResult, self.result)
        result["error"] = from_none(self.error)
        return result


def stats_from_dict(s: Any) -> StatsResponse:
    return StatsResponse.from_dict(s)


class SibylClient(PsychoPass):
    def __init__(self, token: str):
        super().__init__(token, show_license=False)

    def revert(self, user_id: int) -> bool:
        raise self.delete_ban(user_id)
    
    def revert_ban(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
    def remove_ban(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
    def clear_ban(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
    def user_info(self, user_id: int) -> Ban:
        return self.get_info(user_id)
    
    def ban(self, user_id: int, reason: str, message: str=None, source: str=None) -> BanRes:
        return self.add_ban(user_id, reason, message, source)
    
    def ban_user(self, user_id: int, reason: str, message: str=None, source: str=None) -> BanRes:
        return self.add_ban(user_id, reason, message, source)

    def stats(self) -> StatsResult:
        resp = self.invoke_request(f"{self.host}stats?token={self.token}")
        if not self.is_success(resp):
            raise GeneralException(resp["error"]["message"])
        the_resp = stats_from_dict(resp)
        return the_resp.result
    
    def change_token(self, token: str):
        self.token = token
    
    def change_host(self, host: str):
        self.host = host
    
    def change_perm(self, user_id: int, permission: int) -> str:
        self.change_permission
        resp = self.invoke_request((f"{self.host}changePerm?token={self.token}"+
            f"&user-id={user_id}&permission={permission}"))
        if not self.is_success(resp):
            raise GeneralException(resp["error"]["message"])
        return resp['result']
    
    def to_inspector(self, user_id: int) -> str:
        return self.change_perm(user_id, 2)
    
    def to_enforcer(self, user_id: int) -> str:
        return self.change_perm(user_id, 1)
    
    def to_civilian(self, user_id: int) -> str:
        return self.change_perm(user_id, 0)

    def is_success(self, jsonResp) -> bool:
        return jsonResp['success']
    
    def invoke_request(self, url: str):
        return self.client.get(url).json()
    
    
# helper functions:

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

def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }

def from_none(x: Any) -> Any:
    assert x is None
    return x
    
