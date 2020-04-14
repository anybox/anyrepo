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
from copy import deepcopy
from typing import Any, Iterator, MutableMapping
from unittest.mock import MagicMock

import pytest
import toml
from cryptography.fernet import Fernet
from flask import Flask
from flask.testing import FlaskClient

from anyrepo import create_app
from anyrepo.models import db
from anyrepo.models.api import ApiModel, ApiType
from anyrepo.models.hook import HookModel
from anyrepo.models.user import User

path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test.toml")

pytest_plugins = [
    "tests.fixtures.github_fixtures",
    "tests.fixtures.gitlab_fixtures",
]


def pytest_generate_tests(metafunc):
    os.environ["ANYREPO_CONFIG"] = path


@pytest.fixture
def dbpath() -> Iterator[str]:
    path = "/tmp/test.db"
    yield f"sqlite:///{path}"
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def confpath() -> str:
    return path


@pytest.fixture
def config(confpath: str, dbpath: str) -> Iterator[MutableMapping[str, Any]]:
    data_ = f"""
[anyrepo]
debug = true
port = 5000
host = "0.0.0.0"
secret_key = "{Fernet.generate_key().decode()}"
sqlalchemy_database_uri = "{dbpath}"
sqlalchemy_track_modifications = false
wtf_csrf_enabled = false
ldap_provider_url = "http://localhost"
ldap_bind_format = "cr=Users,id={{username}}"
login_disabled = true
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

[users]
[users.admin]
username = "test"
password = "test"

[users.user]
username = "test2"
password = "test2"
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
def app_without_ldap(config: dict, confpath: str) -> Flask:
    conf_ = deepcopy(config)
    del conf_["anyrepo"]["ldap_provider_url"]
    with open(confpath, "w") as fi:
        toml.dump(conf_, fi)

    app_ = create_app()
    app_.config["TESTING"] = True
    @app_.login_manager.request_loader
    def load_user_from_request(request):
        return User.query.get(1)

    return app_


@pytest.fixture
def user(app: Flask):
    with app.app_context():
        user_ = User(username="test")
        user_.set_password("test")
        db.session.add(user_)
        db.session.commit()

        yield user_

        db.session.delete(user_)
        db.session.commit()


@pytest.fixture
def client(app: Flask) -> Iterator[FlaskClient]:
    """Returns a test client for our application."""
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
        def get_project_from_name(self, name: str):
            return project

    return API()


@pytest.fixture
def dbapi(app: Flask) -> Iterator[ApiModel]:
    with app.app_context():
        ApiModel.query.delete()
        dbapi_ = ApiModel(
            name="FakeAPI", api_type=ApiType.GITHUB, url="https://fakeapi.com"
        )
        dbapi_.set_token("test")
        db.session.add(dbapi_)
        db.session.commit()

        yield dbapi_

        db.session.delete(dbapi_)
        db.session.commit()


@pytest.fixture
def github_hook(app: Flask) -> HookModel:
    with app.app_context():
        hook_ = HookModel.query.filter_by(endpoint="/github/").first()
        return hook_


@pytest.fixture
def gitlab_hook(app: Flask) -> HookModel:
    with app.app_context():
        hook_ = HookModel.query.filter_by(endpoint="/gitlab/").first()
        return hook_
