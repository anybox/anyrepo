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

import pytest
import toml

from anyrepo import ConfigError, create_app
from anyrepo.api.github_api import GithubAPI
from anyrepo.api.gitlab_api import GitlabAPI


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
    updated_config = config.copy()
    del updated_config["hook"]["gitlab"]["endpoint"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid hook part in config file" in str(excinfo)


def test_invalid_api_in_config_file(config, confpath):
    updated_config = config.copy()
    del updated_config["api"]["gitlab"]["token"]
    with open(confpath, "w") as fi:
        toml.dump(updated_config, fi)

    with pytest.raises(ConfigError) as excinfo:
        create_app()
    assert "Invalid api part in config file" in str(excinfo)


def test_apis(app):
    apis = app.config["apis"]
    assert len(apis) == 3

    gl_apis = [api for api in apis if isinstance(api, GitlabAPI)]
    assert len(gl_apis) == 2

    gh_apis = [api for api in apis if isinstance(api, GithubAPI)]
    assert len(gh_apis) == 1


def test_hooks(app):
    hooks = app.config["hooks"]
    assert len(hooks) == 2
    assert "/github/" in hooks
    assert "/gitlab/" in hooks
    assert hooks["/gitlab/"] == "mysecret"
    assert hooks["/github/"] == "mysecondsecret"
