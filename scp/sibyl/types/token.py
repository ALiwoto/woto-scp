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

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TokenValidation:
    success: Optional[bool] = None
    result: Optional[bool] = None
    error: Optional[str] = None


@dataclass
class Token:
    user_id: Optional[int] = None
    hash: Optional[str] = None
    permission: Optional[int] = None
    created_at: Optional[datetime] = None
    accepted_reports: Optional[int] = None
    denied_reports: Optional[int] = None
