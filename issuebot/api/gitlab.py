import os
import gitlab
from typing import Optional


class GitlabAPI:
    """Wrapper for gitlab client"""

    def __init__(self):
        url = os.environ.get("GITLAB_URL")
        token = os.environ.get("GITLAB_TOKEN")
        self._client = gitlab.Gitlab(url, private_token=token)

    def get_project_from_name(
        self, name: str
    ) -> Optional[gitlab.base.RESTObject]:
        """Get project from its name"""
        return next(iter(self._client.projects.list(search=name)), None)

    def get_issue_from_title(
        self, project: gitlab.base.RESTObject, title: str
    ) -> Optional[gitlab.base.RESTObject]:
        """Get project issue from its title"""
        return next(
            iter(
                [
                    issue
                    for issue in project.issues.list()
                    if issue.title == title
                ]
            ),
            None,
        )
