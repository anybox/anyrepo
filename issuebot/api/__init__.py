from abc import ABC, abstractmethod
from typing import Optional


class Comment(ABC):
    """API comment wrapper"""

    @property
    @abstractmethod
    def body(self) -> str:
        pass


class Issue(ABC):
    """API issue wrapper"""

    @abstractmethod
    def get_comment_from_body(self, body: str) -> Optional[Comment]:
        pass

    @abstractmethod
    def create_comment(self, body: str) -> Comment:
        pass

    @property
    @abstractmethod
    def state(self):
        pass


class Project(ABC):
    """API project wrapper"""

    @abstractmethod
    def get_issue_from_title(self, title: str) -> Optional[Issue]:
        pass

    @abstractmethod
    def create_issue(self, title: str, body: str) -> Issue:
        pass


class API(ABC):
    """API wrapper"""

    @abstractmethod
    def get_project_from_name(self, name: str) -> Optional[Project]:
        pass
