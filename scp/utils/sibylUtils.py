from SibylSystem import PsychoPass
from SibylSystem.types import (
    Ban,
)

from typing import(
    Any,
    Dict,
    Type,
    Union,
    cast,
    List,
    TypeVar, 
    Callable, 
)

from SibylSystem.exceptions import GeneralException
from SibylSystem.types.bans import BanRes
from SibylSystem.types.general_info import GeneralInfo
from SibylSystem.types.permission import Permissions

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
    original_token: str

    def __init__(self, token: str):
        self.original_token = token
        super().__init__(token, show_license=False)

    def revert(self, user_id: int) -> bool:
        return self.delete_ban(user_id)
    
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
    
    def change_token(self, token: str) -> None:
        if not isinstance(token, str):
            raise TypeError("token must be str")
        if len(token) < 20:
            raise ValueError("token must be more than 20 characters long")
        self.token = token
    
    
    def change_host(self, host: str):
        if not host.endswith("/"):
            host += "/"
        if not host.startswith("http"):
            host = "http://" + host
        self.host = host
    
    def change_to_original_token(self):
        self.token = self.original_token
    
    def change_perm(self, user_id: int, permission: int) -> str:
        return self.change_permission(user_id, permission)
    
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

    #------------------------------------------------------
    def get_div(self, target: Union[int, str, GeneralInfo, Ban]) -> int:
        if isinstance(target, int):
            return self.get_div_by_id(target=target)
        elif isinstance(target, GeneralInfo):
            return self.get_div_by_general(target=target)
        elif isinstance(target, Ban):
            return self.get_div_by_id(target=target.user_id)
        
        raise Exception(f"Invalid value passed as target: {target}")

    def get_div_by_general(self, target: GeneralInfo) -> int:
        if not isinstance(target, GeneralInfo):
            raise Exception("target should be of type 'GeneralInfo'")
        if target.result and target.result.division != None:
            if target.result.division < 1:
                return None
            
            str_div = str(target.result.division)
            if len(str_div) < 2:
                return '0' + str_div
            return str_div
        return None
    
    def get_div_by_id(self, target: int) -> int:
        general = self.get_general_info(user_id=target)
        return self.get_div_by_general(target=general)
    

    def get_general_str(self, target: Union[int, str, GeneralInfo, Ban]) -> str:
        if isinstance(target, int):
            return self.get_general_str_by_id(target=target)
        elif isinstance(target, GeneralInfo):
            return self.get_general_str_by_general(target=target)
        elif isinstance(target, Ban):
            return self.get_general_str_by_id(target=target.user_id)
        
        raise Exception(f"Invalid value passed as target: {target}")

    def get_general_str_by_general(self, target: GeneralInfo) -> str:
        if not isinstance(target, GeneralInfo):
            raise Exception("target should be of type 'GeneralInfo'")
        if not target.result:
            return None
        
        return self.get_general_str_by_perm(target.result.permission)
    
    def get_general_str_by_id(self, target: int) -> int:
        general = self.get_general_info(user_id=target)
        return self.get_div_by_general(target=general)

    def get_general_str_by_perm(self, perm: Permissions) -> str:
        if perm == Permissions.ENFORCER or perm == Permissions.ENFORCER.value:
            return "enforcer"
        elif (
            perm == Permissions.INSPECTOR or perm == Permissions.INSPECTOR.value or
            perm == Permissions.OWNER or perm == Permissions.OWNER.value
        ):
            return "inspector"
        
        return None
    
    #------------------------------------------------------






    
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
    
