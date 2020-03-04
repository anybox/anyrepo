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

import toml
from flask import Flask

from anyrepo.api.github_api import GithubAPI
from anyrepo.api.gitlab_api import GitlabAPI
from anyrepo.hooks.github_hook import github_hook
from anyrepo.hooks.gitlab_hook import gitlab_hook


class ConfigError(Exception):
    pass


def create_app():
    """App factory."""
    app = Flask(__name__)

    # config
    configfile = os.environ.get(
        "ANYREPO_CONFIG", "/usr/local/share/anyrepo/config.toml"
    )
    if not os.path.isfile(configfile):
        raise ConfigError("Config file not found")

    try:
        config = toml.load(configfile)
    except toml.decoder.TomlDecodeError:
        raise ConfigError("Config file must be a valid TOML file")

    app.config.update(config.get("anyrepo", {}))

    # logs
    level = app.config.get("loglevel", "INFO")
    app.logger.setLevel(getattr(logging, level))

    # blueprints
    try:
        app.config["hooks"] = {}
        hooks = config.get("hook", {})
        for _, hook in hooks.items():
            endpoint = hook["endpoint"]
            if hook["type"] == "github":
                app.register_blueprint(github_hook, url_prefix=endpoint)
            elif hook["type"] == "gitlab":
                app.register_blueprint(gitlab_hook, url_prefix=endpoint)
            app.config["hooks"][endpoint] = hook["secret"]
            app.logger.info(
                f"Registered a blueprint for a {hook['type']} at "
                + f"{hook['endpoint']}"
            )
    except KeyError as err:
        msg = "Invalid hook part in config file"
        raise ConfigError(msg) from err

    # apis
    try:
        app.config["apis"] = []
        apis = config.get("api", {})
        for name, api in apis.items():
            if api["type"] == "github":
                app.config["apis"].append(
                    GithubAPI(name, api.get("url"), api["token"])
                )
            elif api["type"] == "gitlab":
                app.config["apis"].append(
                    GitlabAPI(name, api.get("url"), api["token"])
                )
    except KeyError as err:
        msg = "Invalid api part in config file"
        raise ConfigError(msg) from err

    return app
