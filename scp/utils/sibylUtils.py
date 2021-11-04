from sibylsystem.SibylSystem import PsychoPass
from httpx import Response
from sibylsystem.SibylSystem.exceptions import GeneralException
from sibylsystem.SibylSystem.types import (
    Ban,
    BanResult,
)

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
    
    def ban(self, user_id: int, reason: str, message: str=None, source: str=None) -> BanResult:
        r = self.client.get(f"{self.host}addBan?token={self.token}&user-id={user_id}&reason={reason}&message={message}&source={source}")
        j = r.json()
        if not self.is_success(j):
            raise GeneralException(j["error"]["message"])
        return BanResult(**j["result"])
    
    def ban_user(self, user_id: int, reason: str, message: str=None, source: str=None) -> BanResult:
        return self.ban(user_id, reason, message, source)

    def is_success(self, jsonResp) -> bool:
        return jsonResp['success']
    
    
    
    


