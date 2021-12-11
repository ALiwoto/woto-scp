from dataclasses import dataclass
from typing import Optional
from .error import Error

@dataclass
class Result:
    user_id: Optional[int] = None
    division: Optional[int] = None
    assigned_by: Optional[int] = None
    assigned_reason: Optional[str] = None
    assigned_at: Optional[str] = None
    permission: Optional[int] = None


@dataclass
class GeneralInfo:
    error: Optional[Error]
    success: Optional[bool] = None
    result: Optional[Result] = None
