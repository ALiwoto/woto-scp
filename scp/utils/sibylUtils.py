from sibylsystem.SibylSystem import PsychoPass
from sibylsystem.SibylSystem.types import (
    Ban,
    BanResult,
)

class SibylClient(PsychoPass):
    def __init__(self, token: str):
        super().__init__(token, show_license=False)

    def revert(self, user_id: int) -> None:
        self.delete_ban(user_id)
    
    def revert_ban(self, user_id: int) -> None:
        self.delete_ban(user_id)
    
    def remove_ban(self, user_id: int) -> None:
        self.delete_ban(user_id)
    
    def clear_ban(self, user_id: int) -> None:
        self.delete_ban(user_id)
    
    def ban(self, user_id: int, reason: str, message: str=None, source: str=None) -> BanResult:
        self.add_ban(user_id, reason, message, source)
    
    def ban_user(self, user_id: int, reason: str, message: str=None, source: str=None) -> BanResult:
        self.add_ban(user_id, reason, message, source)
    
    


