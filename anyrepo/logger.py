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

from anyrepo.models import db
from anyrepo.models.log import Log


class SQLAlchemyLoggerFormatter(logging.Formatter):
    def format(self, record):
        """Add extra args to log record"""
        record.api_id = None
        record.hook_id = None
        if record.args:
            record.api_id = record.args.get("api_id")
            record.hook_id = record.args.get("hook_id")
        return super().format(record)


class SQLAlchemyHandler(logging.Handler):
    """Log app events into a db table."""

    def emit(self, record):
        self.format(record)
        log = Log(
            level=record.levelname,
            msg=record.msg,
            api_id=record.api_id,
            hook_id=record.hook_id,
        )
        db.session.add(log)
        db.session.commit()
