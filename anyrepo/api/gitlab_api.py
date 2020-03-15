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

from typing import Optional

import gitlab
import gitlab.v4.objects

from anyrepo.api import API, Comment, Issue, Project


class GitlabAPI(API):
    """Wrapper for gitlab client."""

    def __init__(self, url: str, token: str):
        super().__init__(url, token)
        self._client = gitlab.Gitlab(self.url, private_token=token)

    def get_project_from_name(self, name: str) -> Optional[Project]:
        """Get project by its name."""
        repo_list = self._client.projects.list(search=name)
        repo = next(iter(repo_list), None)
        return GitlabProject(repo) if repo else None


class GitlabProject(Project):
    """Gitlab project wrapper"""

    def __init__(self, project: gitlab.v4.objects.Project):
        self._project = project

    def get_issue_from_title(self, title: str) -> Optional[Issue]:
        """Get issue from its name."""
        issues_list = self._project.issues.list()
        for issue in issues_list:
            if issue.title == title:
                return GitlabIssue(issue)
        return None

    def create_issue(self, title: str, body: str):
        """Create project issue."""
        self._project.issues.create({"title": title, "description": body})


class GitlabIssue(Issue):
    """Gitlab issue wrapper"""

    def __init__(self, issue: gitlab.v4.objects.ProjectIssue):
        self._issue = issue

    def get_comment_from_body(self, body: str) -> Optional[Comment]:
        """Get issue comment from its body."""
        comment_list = self._issue.discussions.list()
        for comment in comment_list:
            for note in comment.attributes["notes"]:
                if note["body"] == body:
                    glcomment = comment.notes.get(note["id"])
                    return GitlabComment(glcomment)
        return None

    def create_comment(self, body: str):
        """Create a comment for this issue."""
        self._issue.discussions.create({"body": body})

    @property
    def state(self):
        """Issue state."""
        return self._issue.state_event

    @state.setter
    def state(self, value: str):
        """Issue state setter."""
        self._issue.state_event = value
        self._issue.save()


class GitlabComment(Comment):
    """Gitlab comment wrapper."""

    def __init__(self, comment: gitlab.v4.objects.ProjectIssueDiscussionNote):
        self._comment = comment

    @property
    def body(self) -> str:
        """Comment body."""
        return self._comment.body

    @body.setter
    def body(self, value: str):
        """Comment body setter."""
        self._comment.body = value
        self._comment.save()

    def delete(self):
        """Delete comment."""
        self._comment.delete()
