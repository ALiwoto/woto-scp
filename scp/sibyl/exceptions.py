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

class GeneralException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidTokenException(GeneralException):
    def __init__(self) -> None:
        super().__init__(message="Token is invalid")


class InvalidPermissionRangeException(GeneralException):
    def __init__(self, message: str) -> None:
        super().__init__(message)
