import os
from typing import Optional

import gitlab
from issuebot.api import API, Project, Comment, Issue


class GitlabAPI(API):
    """Wrapper for gitlab client"""

    def __init__(self):
        url = os.environ.get("GITLAB_URL")
        token = os.environ.get("GITLAB_TOKEN")
        self._client = gitlab.Gitlab(url, private_token=token)

    def get_project_from_name(self, name: str) -> Optional[Project]:
        """Get project by its name"""
        repo = next(iter(self._client.projects.list(search=name)), None)
        return GitlabProject(repo) if repo else None


class GitlabProject(Project):
    """Gitlab project wrapper"""

    def __init__(self, project):
        self._project = project

    def get_issue_from_title(self, title: str) -> Optional[Issue]:
        """Get issue from its name"""
        issues_list = self._project.issues.list()
        for issue in issues_list:
            if issue.title == title:
                return GitlabIssue(issue)
        return None

    def create_issue(self, title: str, body: str) -> Issue:
        """Create project issue"""
        return self._project.issues.create({"title": title, "description": body})


class GitlabIssue(Issue):
    """Gitlab issue wrapper"""

    def __init__(self, issue):
        self._issue = issue

    def get_comment_from_body(self, body: str) -> Optional[Comment]:
        """Get issue comment from its body"""
        comment_list = self._issue.discussions.list()
        for comment in comment_list:
            for note in comment.attributes["notes"]:
                if note["body"] == body:
                    glcomment = comment.notes.get(note["id"])
                    return GitlabComment(glcomment)
        return None

    def create_comment(self, body: str) -> Comment:
        """Create a comment for this issue"""
        res = self._issue.discussions.create({"body": body})
        return GitlabComment(res)

    @property
    def state(self):
        """Issue state"""
        return self._issue.state_event

    @state.setter
    def state(self, value: str):
        """Issue state setter"""
        self._issue.state_event = value
        self._issue.save()


class GitlabComment(Comment):
    """Gitlab comment wrapper"""

    def __init__(self, comment):
        self._comment = comment

    @property
    def body(self) -> str:
        """Comment body"""
        return self._comment.body

    @body.setter
    def body(self, value: str):
        """Comment body setter"""
        self._comment.body = value
        self._comment.save()

    def delete(self):
        """Delete comment"""
        self._comment.delete()
