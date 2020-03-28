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


from typing import Any, Dict

from cryptography.fernet import Fernet
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from anyrepo.hooks.github_hook import github_hook
from anyrepo.hooks.gitlab_hook import gitlab_hook
from anyrepo.models.api import ApiModel, ApiType
from anyrepo.models.hook import HookModel, HookType
from anyrepo.models.user import User


class ConfigError(Exception):
    pass


def check_config(app: Flask):
    """Check if config is valid."""
    app.logger.debug("Check if mandatory values are in config")
    if app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:":
        raise ConfigError("Missing database uri in config file")

    try:
        app.logger.debug("Check if secret key is valid for cryptography")
        key = app.config["SECRET_KEY"]
        if not key:
            raise ConfigError("Missing secret key in config file")

        if not isinstance(key, bytes):
            key = key.encode("utf-8")

        Fernet(key)
    except ValueError as err:
        msg = str(err)
        raise ConfigError(msg) from err


def parse_config_hooks(config: Dict[str, Any], app: Flask, db: SQLAlchemy):
    """Pre populate Hook table with config and register blueprints."""
    try:
        app.logger.debug("Parse config hook part")
        hooks = config.get("hook", {})
        for _, hook in hooks.items():
            endpoint = hook["endpoint"]
            dbhook = HookModel.query.filter_by(endpoint=endpoint).one_or_none()
            if hook["type"] == "github":
                hook_type = HookType.GITHUB
                app.register_blueprint(github_hook, url_prefix=endpoint)
            elif hook["type"] == "gitlab":
                hook_type = HookType.GITLAB
                app.register_blueprint(gitlab_hook, url_prefix=endpoint)
            else:
                raise ConfigError("Invalid hook type")

            if not dbhook:
                dbhook = HookModel(endpoint=endpoint, hook_type=hook_type)
                db.session.add(dbhook)

            dbhook.set_secret(hook["secret"])
            app.logger.info(
                f"Registered a blueprint for a {hook['type']} hook at "
                f"{hook['endpoint']}"
            )
    except KeyError as err:
        msg = "Invalid hook part in config file"
        raise ConfigError(msg) from err
    except ConfigError:
        raise
    else:
        db.session.commit()


def parse_config_apis(config: Dict[str, Any], app: Flask, db: SQLAlchemy):
    """Pre polulate API table with config."""
    try:
        app.logger.debug("Parse config api part")
        apis = config.get("api", {})
        for name, api in apis.items():
            url = api.get("url")
            if api["type"] == "github":
                api_type = ApiType.GITHUB
                url = url or "https://github.com/"
            elif api["type"] == "gitlab":
                api_type = ApiType.GITLAB
                url = url or "https://gitlab.com/"
            else:
                raise ConfigError("Invalid api type")

            dbapi = ApiModel.query.filter_by(url=url).one_or_none()
            if not dbapi:
                dbapi = ApiModel(name=name, url=url, api_type=api_type)
                db.session.add(dbapi)

            dbapi.set_token(api["token"])
    except KeyError as err:
        msg = "Invalid api part in config file"
        raise ConfigError(msg) from err
    except ConfigError:
        raise
    else:
        db.session.commit()


def parse_config_users(config: Dict[str, Any], app: Flask, db: SQLAlchemy):
    """Pre populate User table with config."""
    try:
        app.logger.debug("Parse config user part")
        if "ldap_provider_url" in config["anyrepo"]:
            app.logger.debug("LDAP configuration found, skip creating user")
            return

        users = config["users"]
        if not users:
            app.logger.warning("No user registered for the app")
        for _, user in users.items():
            username = user["username"]
            dbuser = User.query.filter_by(username=username).one_or_none()
            if not dbuser:
                dbuser = User(username=username)
                db.session.add(dbuser)

            dbuser.set_password(user["password"])
    except KeyError as err:
        msg = "Invalid user part in config file"
        raise ConfigError(msg) from err
    else:
        db.session.commit()
