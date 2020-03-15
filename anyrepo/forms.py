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


from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import InputRequired, Regexp

from anyrepo.models.api import ApiType

URLREGEX = (
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]"
    + r"[0-9a-fA-F]))+"
)


class LoginForm(FlaskForm):
    """FlaskForm to log into the app."""

    username = StringField("Username", [InputRequired()])
    password = PasswordField("Password", [InputRequired()])


class ApiForm(FlaskForm):
    """Api model form."""

    name = StringField("Name", [InputRequired()])
    url = StringField("Url", [InputRequired(), Regexp(URLREGEX)])
    api_type = SelectField(
        "Type",
        choices=[
            (ApiType.GITHUB.name, ApiType.GITHUB.value),
            (ApiType.GITLAB.name, ApiType.GITLAB.value),
        ],
    )
    token = PasswordField("Token", [InputRequired()])


class HookForm(FlaskForm):
    """Hook model form."""

    secret = PasswordField("Secret", [InputRequired()])
