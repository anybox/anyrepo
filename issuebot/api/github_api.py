import os
from typing import Optional

import github
from issuebot.api import API, Project, Comment, Issue


class GithubAPI(API):
    """Github client wrapper"""

    def __init__(self):
        url = os.environ.get("GITHUB_URL")
        token = os.environ.get("GITHUB_TOKEN")
        if url:
            self._client = github.Github(base_url=url, login_or_token=token)
        else:
            self._client = github.Github(token)
        self._user = self._client.get_user()

    def get_project_from_name(self, name: str) -> Optional[Project]:
        """Get project by its name"""
        repo_list = self._user.get_repos()
        for repo in repo_list:
            if repo.name == name:
                return GithubProject(repo)
        return None


class GithubProject(Project):
    """Github project wrapper"""

    def __init__(self, project: github.Repository.Repository):
        self._project = project

    def get_issue_from_title(self, title: str) -> Optional[Issue]:
        """Get issue from its name"""
        issues_list = self._project.get_issues(state="all")
        for issue in issues_list:
            if issue.title == title:
                return GithubIssue(issue)
        return None

    def create_issue(self, title: str, body: str) -> Issue:
        """Create project issue"""
        return self._project.create_issue(title=title, description=body)


class GithubIssue(Issue):
    """Github issue wrapper"""

    def __init__(self, issue: github.Issue.Issue):
        self._issue = issue

    def get_comment_from_body(self, body: str) -> Optional[Comment]:
        """Get issue comment from its body"""
        comment_list = self._issue.get_comments()
        for comment in comment_list:
            if comment.body == body:
                return GithubComment(comment)
        return None

    def create_comment(self, body: str) -> Comment:
        """Create a comment for this issue"""
        res = self._issue.create_comment(body=body)
        return GithubComment(res)

    @property
    def state(self):
        """Issue state"""
        return self._issue.state

    @state.setter
    def state(self, value: str):
        """Issue state setter"""
        self._issue.edit(state=value)


class GithubComment(Comment):
    """Github comment wrapper"""

    def __init__(self, comment: github.IssueComment.IssueComment):
        self._comment = comment

    @property
    def body(self) -> str:
        """Comment body"""
        return self._comment.body

    @body.setter
    def body(self, value: str):
        """Comment body setter"""
        self._comment.edit(body=value)
