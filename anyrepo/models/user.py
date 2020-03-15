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


from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from anyrepo.models import db


class User(db.Model, UserMixin):
    """User model."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password_hash = db.Column(db.String, name="password")

    def check_password(self, password: str) -> bool:
        """Check password with stored hash."""
        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str):
        """Hash password and store it in db."""
        self.password_hash = generate_password_hash(password)
