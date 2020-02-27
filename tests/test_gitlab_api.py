# Issuebot
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

from issuebot.api.gitlab_api import (
    GitlabAPI,
    GitlabComment,
    GitlabIssue,
    GitlabProject,
)

Repo = namedtuple("RepoTuple", "name")
Issue = namedtuple("IssueTuple", "title")
Comment = namedtuple("CommentTuple", "attributes notes")


class FakeProject:

    issues = MagicMock()


class FakeIssue:

    state_event = "opened"
    discussions = MagicMock()
    save = MagicMock()


class FakeComment:

    body = "This is a test"
    save = MagicMock()
    delete = MagicMock()


@patch("gitlab.Gitlab")
def test_create_api_without_url(gitlab_patched):
    api_ = GitlabAPI("gitlab", None, "mytoken")
    assert gitlab_patched.called_with("https://gitlab.com/", "mytoken")
    assert api_.url == "https://gitlab.com/"


@patch("gitlab.Gitlab")
def test_create_api(gitlab_patched):
    api_ = GitlabAPI("gitlab", "http://gitlab.mycompany.com", "mytoken")
    assert gitlab_patched.called_with("http://gitlab.mycompany.com", "mytoken")
    assert api_.url == "http://gitlab.mycompany.com"


@patch("gitlab.Gitlab")
def test_get_repo_empty(gitlab_patched):
    gitlab_patched.projects.list.return_value = []

    api_ = GitlabAPI("gitlab", None, "mytoken")
    res = api_.get_project_from_name("test")
    assert res is None
    assert gitlab_patched.projects.list.called_with({"search": "test"})


@patch("gitlab.Gitlab")
def test_get_repo(gitlab_patched):
    api_ = GitlabAPI("gitlab", None, "mytoken")
    api_._client.projects.list = MagicMock()
    api_._client.projects.list.return_value = [Repo(name="test")]

    res = api_.get_project_from_name("test")
    assert res is not None
    assert isinstance(res, GitlabProject)
    assert api_._client.projects.list.called_with({"search": "test"})


def test_get_issue_empty():
    project = FakeProject()
    project.issues.list.return_value = []

    gl_project_ = GitlabProject(project)
    res = gl_project_.get_issue_from_title("test")
    assert res is None
    assert project.issues.list.called_with({"state": "all"})


def test_get_issue_not_found():
    project = FakeProject()
    project.issues.list.return_value = [Issue(title="test2")]

    gl_project_ = GitlabProject(project)
    res = gl_project_.get_issue_from_title("test")
    assert res is None
    assert project.issues.list.called


def test_get_issue():
    project = FakeProject()
    project.issues.list.return_value = [Issue(title="test")]

    gl_project_ = GitlabProject(project)
    res = gl_project_.get_issue_from_title("test")
    assert res is not None
    assert isinstance(res, GitlabIssue)
    assert project.issues.list.called


def test_create_issue():
    project = FakeProject()

    gl_project_ = GitlabProject(project)
    gl_project_.create_issue("A title", "A body")

    assert project.issues.create_issue.called_with(
        {"title": "A title", "description": "A body"}
    )


def test_get_issue_comment_empty():
    issue = FakeIssue()
    issue.discussions.list.return_value = []

    gl_issue_ = GitlabIssue(issue)
    res = gl_issue_.get_comment_from_body("test")

    assert res is None
    assert issue.discussions.list.called


def test_get_issue_comment_not_found():
    issue = FakeIssue()
    issue.discussions.list.return_value = [
        Comment(attributes={"notes": [{"id": "1", "body": "test2"}]}, notes={})
    ]

    gl_issue_ = GitlabIssue(issue)
    res = gl_issue_.get_comment_from_body("test")

    assert res is None
    assert issue.discussions.list.called


def test_get_issue_comment():
    issue = FakeIssue()
    issue.discussions.list.return_value = [
        Comment(
            attributes={
                "notes": [
                    {"id": "1", "body": "test"},
                    {"id": "2", "body": "test2"},
                ]
            },
            notes={"1": "test"},
        )
    ]

    gl_issue_ = GitlabIssue(issue)
    res = gl_issue_.get_comment_from_body("test")

    assert res is not None
    assert isinstance(res, GitlabComment)
    assert issue.discussions.list.called


def test_create_comment():
    issue = FakeIssue()

    gl_issue_ = GitlabIssue(issue)
    gl_issue_.create_comment("test")

    assert issue.discussions.create.called_with({"body": "test"})


def test_issue_state():
    issue = FakeIssue()
    gl_issue_ = GitlabIssue(issue)

    assert gl_issue_.state == "opened"

    gl_issue_.state = "another value"

    assert issue.save.called


def test_comment_body():
    comment = FakeComment()
    gl_comment_ = GitlabComment(comment)

    assert gl_comment_.body == "This is a test"

    gl_comment_.body = "Mama, just killed a man"

    assert comment.save.called


def test_comment_delete():
    comment = FakeComment()
    gl_comment_ = GitlabComment(comment)

    gl_comment_.delete()
    assert comment.delete.called
