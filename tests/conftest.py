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

import os
from typing import Any, Iterator, MutableMapping
from unittest.mock import MagicMock

import pytest
import toml
from flask import Flask
from flask.testing import FlaskClient

from anyrepo import create_app

path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test.toml")

pytest_plugins = [
    "tests.fixtures.github_fixtures",
    "tests.fixtures.gitlab_fixtures",
]


def pytest_generate_tests(metafunc):
    os.environ["ANYREPO_CONFIG"] = path


@pytest.fixture
def confpath() -> str:
    return path


@pytest.fixture
def config(confpath: str) -> Iterator[MutableMapping[str, Any]]:
    data_ = """
[anyrepo]
debug = true
port = 5000
host = "0.0.0.0"
loglevel = "INFO"

[api]

[api.gitlab]
type = "gitlab"
url = "http://gitlab.com/"
token = "mysuperlongtoken"

[api.anothergitlab]
type = "gitlab"
url = "https://gitlab.myurl.cloud"
token = "anothertoken"

[api.github]
type = "github"
url = "http://github.com/"
token = "andanotherone"

[hook]

[hook.gitlab]
endpoint = "/gitlab/"
type = "gitlab"
secret = "mysecret"

[hook.github]
endpoint = "/github/"
type = "github"
secret = "mysecondsecret"
    """
    with open(confpath, "w") as fi:
        fi.write(data_)

    yield toml.loads(data_)
    os.remove(confpath)


@pytest.fixture
def app(config: dict) -> Flask:
    """Create the app"""
    app_ = create_app()
    app_.config["TESTING"] = True
    return app_


@pytest.fixture
def client(app: Flask) -> Iterator[FlaskClient]:
    """Returns a test client for our application"""
    yield app.test_client()


@pytest.fixture
def comment():
    class Comment:
        body_ = "Neque porro quisquam est qui dolorem ipsum quia dolor"

        @property
        def body(self):
            return self.body_

        @body.setter
        def body(self, value):
            self.body_ = value

        def delete(self):
            raise NotImplementedError()

    comment_ = Comment()
    setattr(comment_, "delete", MagicMock())
    return comment_


@pytest.fixture
def issue(comment):
    class Issue:
        state_ = "opened"

        def get_comment_from_body(self, body: str):
            return comment

        def create_comment(self, body: str):
            return comment

        @property
        def state(self):
            return self.state_

        @state.setter
        def state(self, value):
            self.state_ = value

    issue_ = Issue()
    return issue_


@pytest.fixture
def project(issue):
    class Project:
        def get_issue_from_title(self, title: str):
            return issue

        def create_issue(self, title: str, body: str):
            return issue

    project_ = Project()
    return project_


@pytest.fixture
def api(project, app: Flask):
    class API:
        name = "FakeAPI"
        url = "https://fakeapi.com"

        def get_project_from_name(self, name: str):
            return project

    api_ = API()
    app.config["apis"] = [api_]
    return api_
