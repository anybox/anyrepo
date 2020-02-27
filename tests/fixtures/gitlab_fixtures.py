# Issuebot
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

import json

import pytest


@pytest.fixture
def gl_secret() -> str:
    return "mysecret"


@pytest.fixture
def gl_headers(gl_secret: str) -> dict:
    return {"HTTP_X_GITLAB_TOKEN": gl_secret}


@pytest.fixture
def new_gl_issue_comment_str() -> str:
    with open("tests/fixtures/glissuecomment.data.json", "r") as data:
        comment_ = data.read()

    return comment_


@pytest.fixture
def new_gl_issue_str() -> str:
    with open("tests/fixtures/glissues.data.json", "r") as data:
        issue_ = data.read()

    return issue_


@pytest.fixture
def closed_gl_issue_str(new_gl_issue_str: str) -> str:
    closed_issue_ = json.loads(new_gl_issue_str)
    closed_issue_["object_attributes"]["state"] = "closed"
    return json.dumps(closed_issue_)
