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


from enum import Enum
from typing import TYPE_CHECKING, List
from uuid import uuid4

from anyrepo.models import db
from anyrepo.models.encryption import decrypt_data, encrypt_data

if TYPE_CHECKING:
    from anyrepo.models.request import RequestModel  # noqa: F401


class HookType(Enum):
    """API supported by the app."""

    GITHUB = "github"
    GITLAB = "gitlab"


class HookModel(db.Model):
    """Hook table."""

    __tablename__ = "hook"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(
        db.String, nullable=False, default=lambda: uuid4().hex, unique=True
    )
    endpoint = db.Column(db.String, nullable=False, unique=True)
    hook_type = db.Column(db.Enum(HookType), nullable=False, name="type")
    secret_encrypted = db.Column(db.LargeBinary, nullable=False, name="secret")

    requests = db.relationship("RequestModel", backref="hook", lazy=True)

    def set_secret(self, secret_value: str):
        """Encrypt secret using app secret key and store it into
        secret_encrypted field.
        """
        self.secret_encrypted = encrypt_data(secret_value)

    def get_secret(self) -> str:
        """Get decrypted data from secret_encrypted_field."""
        return decrypt_data(self.secret_encrypted)

    @property
    def good_requests(self) -> List["RequestModel"]:
        """Get good requests list."""
        return [request for request in self.requests if request.status == 200]

    @property
    def bad_requests(self) -> List["RequestModel"]:
        """Get bad requests list."""
        return [request for request in self.requests if request.status != 200]
