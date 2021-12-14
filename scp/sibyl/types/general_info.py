from dataclasses import dataclass
from typing import Optional
from .error import Error
from .permission import Permissions

@dataclass
class Result:
    user_id: Optional[int] = None
    division: Optional[int] = None
    assigned_by: Optional[int] = None
    assigned_reason: Optional[str] = None
    assigned_at: Optional[str] = None
    permission: Optional[Permissions] = None


@dataclass
class GeneralInfo:
    error: Optional[Error]
    success: Optional[bool] = None
    result: Optional[Result] = None

    def to_general_perm(self) -> str:
        if self.result and self.result.permission != None:
            return self.result.permission.to_general()
        return None
    
    def get_div(self) -> str:
        if self.result and self.result.division != None:
            if self.result.division < 1:
                return None
            
            str_div = str(self.result.division)
            if len(str_div) < 2:
                return '0' + str_div
            return str_div
        return None
