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

from anyrepo.config import (
    ConfigError,
    check_config,
    parse_config_apis,
    parse_config_hooks,
    parse_config_users,
)
from anyrepo.models import db
from anyrepo.views import admin, login_manager


def create_app():
    """App factory."""
    app = Flask(__name__)

    # config
    configfile = os.environ.get(
        "ANYREPO_CONFIG", "/usr/local/share/anyrepo/config.toml"
    )

    if not os.path.exists(configfile):
        raise ConfigError("Config file not found")

    try:
        config = toml.load(configfile)
    except toml.decoder.TomlDecodeError:
        raise ConfigError("Config file must be a valid TOML file")

    anyrepoconfig = config.get("anyrepo", {})
    converted_config = {k.upper(): v for k, v in anyrepoconfig.items()}

    app.config.update(converted_config)
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    # logs
    level = app.config.get("LOGLEVEL", "INFO")
    app.logger.setLevel(getattr(logging, level))

    # admin
    app.register_blueprint(admin)
    with app.app_context():
        check_config(app)
        parse_config_apis(config, app, db)
        parse_config_hooks(config, app, db)
        parse_config_users(config, app, db)

    return app
