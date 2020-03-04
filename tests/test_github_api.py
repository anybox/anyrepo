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


from collections import namedtuple
from unittest.mock import MagicMock, patch

from anyrepo.api.github_api import (
    GithubAPI,
    GithubComment,
    GithubIssue,
    GithubProject,
)

Repo = namedtuple("RepoTuple", "name")
Issue = namedtuple("IssueTuple", "title")
Comment = namedtuple("CommentTuple", "body")


class FakeProject:

    get_issues = MagicMock()
    create_issue = MagicMock()


class FakeIssue:

    state = "opened"
    get_comments = MagicMock()
    create_comment = MagicMock()
    edit = MagicMock()


class FakeComment:

    body = "This is a test"
    edit = MagicMock()


@patch("github.Github")
def test_create_api_without_url(github_patched):
    api_ = GithubAPI("github", None, "mytoken")
    assert github_patched.called_with("mytoken")
    assert api_.url == "https://github.com"


@patch("github.Github")
def test_create_api(github_patched):
    api_ = GithubAPI("github", "http://github.mycompany.com", "mytoken")
    assert github_patched.called_with(
        {
            "base_url": "http://github.mycompany.com",
            "login_or_token": "mytoken",
        }
    )
    assert api_.url == "http://github.mycompany.com"


@patch("github.AuthenticatedUser")
def test_get_repo_empty(user_patched):
    user_patched.get_repos.return_value = []

    api_ = GithubAPI("github", None, "mytoken")
    api_._user = user_patched
    res = api_.get_project_from_name("test")
    assert res is None


@patch("github.AuthenticatedUser")
def test_get_repo(user_patched):
    user_patched.get_repos.return_value = [Repo(name="test")]

    api_ = GithubAPI("github", None, "mytoken")
    api_._user = user_patched
    res = api_.get_project_from_name("test")
    assert res is not None
    assert isinstance(res, GithubProject)


@patch("github.AuthenticatedUser")
def test_get_repo_not_found(user_patched):
    user_patched.get_repos.return_value = [Repo(name="test2")]

    api_ = GithubAPI("github", None, "mytoken")
    api_._user = user_patched
    res = api_.get_project_from_name("test")
    assert res is None


def test_get_issue_empty():
    project = FakeProject()
    project.get_issues.return_value = []

    gh_project_ = GithubProject(project)
    res = gh_project_.get_issue_from_title("test")
    assert res is None
    assert project.get_issues.called_with({"state": "all"})


def test_get_issue_not_found():
    project = FakeProject()
    project.get_issues.return_value = [Issue(title="test2")]

    gh_project_ = GithubProject(project)
    res = gh_project_.get_issue_from_title("test")
    assert res is None
    assert project.get_issues.called_with({"state": "all"})


def test_get_issue():
    project = FakeProject()
    project.get_issues.return_value = [Issue(title="test")]

    gh_project_ = GithubProject(project)
    res = gh_project_.get_issue_from_title("test")
    assert res is not None
    assert isinstance(res, GithubIssue)
    assert project.get_issues.called_with({"state": "all"})


def test_create_issue():
    project = FakeProject()

    gh_project_ = GithubProject(project)
    gh_project_.create_issue("A title", "A body")

    assert project.create_issue.called_with(
        {"title": "A title", "description": "A body"}
    )


def test_get_issue_comment_empty():
    issue = FakeIssue()
    issue.get_comments.return_value = []

    gh_issue_ = GithubIssue(issue)
    res = gh_issue_.get_comment_from_body("test")

    assert res is None
    assert issue.get_comments.called


def test_get_issue_comment_not_found():
    issue = FakeIssue()
    issue.get_comments.return_value = [Comment(body="test2")]

    gh_issue_ = GithubIssue(issue)
    res = gh_issue_.get_comment_from_body("test")

    assert res is None
    assert issue.get_comments.called


def test_get_issue_comment():
    issue = FakeIssue()
    issue.get_comments.return_value = [Comment(body="test")]

    gh_issue_ = GithubIssue(issue)
    res = gh_issue_.get_comment_from_body("test")

    assert res is not None
    assert isinstance(res, GithubComment)
    assert issue.get_comments.called


def test_create_comment():
    issue = FakeIssue()

    gh_issue_ = GithubIssue(issue)
    gh_issue_.create_comment("test")

    assert issue.create_comment.called_with({"body": "test"})


def test_issue_state():
    issue = FakeIssue()
    gh_issue_ = GithubIssue(issue)

    assert gh_issue_.state == "opened"

    gh_issue_.state = "another value"

    assert issue.edit.called_with({"state": "another value"})


def test_comment_body():
    comment = FakeComment()
    gh_comment_ = GithubComment(comment)

    assert gh_comment_.body == "This is a test"

    gh_comment_.body = "Mama, just killed a man"

    assert comment.edit.called_with({"body": "Mama, just killed a man"})
