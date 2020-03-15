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
from typing import Optional
from uuid import uuid4

from anyrepo.api import API
from anyrepo.api.github_api import GithubAPI
from anyrepo.api.gitlab_api import GitlabAPI
from anyrepo.models import db
from anyrepo.models.encryption import decrypt_data, encrypt_data


class ApiType(Enum):
    """API supported by the app."""

    GITHUB = "github"
    GITLAB = "gitlab"


class ApiModel(db.Model):
    """API table."""

    __tablename__ = "api"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(
        db.String, nullable=False, default=lambda: uuid4().hex, unique=True
    )
    name = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False, unique=True)
    api_type = db.Column(db.Enum(ApiType), nullable=False, name="type")
    token_encrypted = db.Column(db.LargeBinary, nullable=False, name="token")

    logs = db.relationship("Log", lazy=True)

    def set_token(self, token_value: str):
        """Encrypt token using app secret key and store it into token_encrypted
        field.
        """
        self.token_encrypted = encrypt_data(token_value)

    def get_token(self) -> str:
        """Get decrypted data from token_encrypted_field."""
        return decrypt_data(self.token_encrypted)

    def get_client(self) -> Optional[API]:
        """Get API client."""
        if self.api_type == ApiType.GITHUB:
            return GithubAPI(self.url, self.get_token())
        elif self.api_type == ApiType.GITLAB:
            return GitlabAPI(self.url, self.get_token())
        return None
