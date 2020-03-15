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


from sqlalchemy.sql import func

from anyrepo.models import db
from anyrepo.models.api import ApiModel
from anyrepo.models.hook import HookModel


class Log(db.Model):
    """Log model for db logging handler."""

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String, nullable=False)
    msg = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    api_id = db.Column(db.Integer, db.ForeignKey(ApiModel.id), nullable=True)
    hook_id = db.Column(db.Integer, db.ForeignKey(HookModel.id), nullable=True)
