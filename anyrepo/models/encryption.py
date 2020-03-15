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


from cryptography.fernet import Fernet
from flask import current_app


def encrypt_data(data: str) -> bytes:
    """Encrypt data using app secret key."""
    key = current_app.secret_key
    assert key is not None
    if isinstance(key, str):
        key = key.encode("utf-8")
    fernet = Fernet(key)
    return fernet.encrypt(data.encode("utf-8"))


def decrypt_data(enc: bytes) -> str:
    """Decrypt encrypted data."""
    key = current_app.secret_key
    assert key is not None
    if isinstance(key, str):
        key = key.encode("utf-8")
    fernet = Fernet(key)
    data = fernet.decrypt(enc)
    return data.decode("utf-8")
