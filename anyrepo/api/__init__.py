# AnyRepo
# Copyright (C) 2020  Anybox
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod
from typing import Optional


class Comment(ABC):
    """API comment wrapper."""

    @property
    @abstractmethod
    def body(self) -> str:
        pass


class Issue(ABC):
    """API issue wrapper."""

    @abstractmethod
    def get_comment_from_body(self, body: str) -> Optional[Comment]:
        pass

    @abstractmethod
    def create_comment(self, body: str):
        pass

    @property
    @abstractmethod
    def state(self):
        pass


class Project(ABC):
    """API project wrapper."""

    @abstractmethod
    def get_issue_from_title(self, title: str) -> Optional[Issue]:
        pass

    @abstractmethod
    def create_issue(self, title: str, body: str):
        pass


class API(ABC):
    """API wrapper."""

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

    @abstractmethod
    def get_project_from_name(self, name: str) -> Optional[Project]:
        pass
