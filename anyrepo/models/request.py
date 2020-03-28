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

from uuid import uuid4

from sqlalchemy.sql import func

from anyrepo.models import db


class RequestModel(db.Model):
    """Request table."""

    __tablename__ = "request"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(
        db.String, nullable=False, default=lambda: uuid4().hex, unique=True
    )
    headers = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)
    response = db.Column(db.String, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    hook_id = db.Column(db.Integer, db.ForeignKey("hook.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
