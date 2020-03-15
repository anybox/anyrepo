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

import logging
import os
from copy import deepcopy

import pytest
import toml

from anyrepo import ConfigError, create_app
from anyrepo.api.github_api import GithubAPI
from anyrepo.api.gitlab_api import GitlabAPI
from anyrepo.models.api import ApiModel, ApiType
from anyrepo.models.hook import HookModel


def test_config_without_mandatory_values(config, confpath):
    updated_config = deepcopy(config)
    del updated_config["anyrepo"]["secret_key"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Missing secret key in config file" in str(excinfo)

    updated_config = deepcopy(config)
    del updated_config["anyrepo"]["sqlalchemy_database_uri"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Missing database uri in config file" in str(excinfo)


def test_invalid_secret_key(config, confpath):
    updated_config = deepcopy(config)
    updated_config["anyrepo"]["secret_key"] = "tooshort"
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Fernet key must be 32 url-safe base64-encoded bytes" in str(
        excinfo
    )


def test_no_config_file(confpath):
    if os.path.exists(confpath):
        os.remove(confpath)
    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Config file not found" in str(excinfo)


def test_invalid_config_file(confpath):
    with open(confpath, "a+") as fi:
        fi.write("\\ Invalid toml //")

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Config file must be a valid TOML file" in str(excinfo)


def test_app(app):
    assert app is not None


def test_invalid_hook_in_config_file(config, confpath):
    updated_config = deepcopy(config)
    del updated_config["hook"]["gitlab"]["endpoint"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid hook part in config file" in str(excinfo)

    updated_config = deepcopy(config)
    updated_config["hook"]["gitlab"]["type"] = "notsupported"
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid hook type" in str(excinfo)


def test_invalid_api_in_config_file(config, confpath):
    updated_config = deepcopy(config)
    del updated_config["api"]["gitlab"]["token"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid api part in config file" in str(excinfo)

    updated_config = deepcopy(config)
    updated_config["api"]["gitlab"]["type"] = "notsupported"
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid api type" in str(excinfo)


def test_no_users_part(config, confpath):
    updated_config = deepcopy(config)
    del updated_config["users"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid user part in config file" in str(excinfo)


def test_no_users(config, confpath, caplog):
    updated_config = deepcopy(config)
    updated_config["users"] = {}
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with caplog.at_level(logging.WARNING):
        create_app()
    assert "No user registered for the app" in caplog.text


def test_invalid_user_keys(config, confpath):
    updated_config = deepcopy(config)
    del updated_config["users"]["admin"]["username"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid user part in config file" in str(excinfo)


def test_apis(app):
    with app.app_context():
        nbapis = ApiModel.query.count()
        assert nbapis == 3

        gl_nbapis = ApiModel.query.filter_by(api_type=ApiType.GITLAB).count()
        assert gl_nbapis == 2

        gh_nbapis = ApiModel.query.filter_by(api_type=ApiType.GITHUB).count()
        assert gh_nbapis == 1

        gl_api = ApiModel.query.filter_by(api_type=ApiType.GITLAB).first()
        assert isinstance(gl_api.get_client(), GitlabAPI)

        gh_api = ApiModel.query.filter_by(api_type=ApiType.GITHUB).first()
        assert isinstance(gh_api.get_client(), GithubAPI)


def test_hooks(app):
    with app.app_context():
        hooks = HookModel.query.all()
        endpoints = [hook.endpoint for hook in hooks]
        assert len(hooks) == 2
        assert "/github/" in endpoints
        assert "/gitlab/" in endpoints

        gh_hook = HookModel.query.filter_by(endpoint="/github/").first()
        assert gh_hook.secret_encrypted != "mysecondsecret"
        assert gh_hook.get_secret() == "mysecondsecret"

        gl_hook = HookModel.query.filter_by(endpoint="/gitlab/").first()
        assert gl_hook.secret_encrypted != "mysecret"
        assert gl_hook.get_secret() == "mysecret"
