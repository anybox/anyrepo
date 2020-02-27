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

import hmac
import json

import pytest


@pytest.fixture
def gh_secret() -> bytes:
    return b"mysecondsecret"


@pytest.fixture
def gh_headers(gh_secret: bytes) -> dict:
    hash_object = hmac.new(gh_secret, None, "sha1")
    hex_dig = hash_object.hexdigest()
    return {
        "HTTP_USER_AGENT": "GitHub-Hookshot",
        "HTTP_X_HUB_SIGNATURE": f"sha1={hex_dig}",
    }


@pytest.fixture
def new_gh_issue_comment_str() -> str:
    with open("tests/fixtures/ghissuecomment.data.json", "r") as data:
        comment_ = data.read()

    return comment_


@pytest.fixture
def edited_gh_issue_comment_str(new_gh_issue_comment_str: str) -> str:
    data_ = json.loads(new_gh_issue_comment_str)
    data_["action"] = "edited"
    return json.dumps(data_)


@pytest.fixture
def deleted_gh_issue_comment_str(new_gh_issue_comment_str: str) -> str:
    data_ = json.loads(new_gh_issue_comment_str)
    data_["action"] = "deleted"
    return json.dumps(data_)


@pytest.fixture
def new_gh_issue_str() -> str:
    with open("tests/fixtures/ghissues.data.json", "r") as data:
        issue_ = data.read()

    return issue_


@pytest.fixture
def reopened_gh_issue_str(new_gh_issue_str: str) -> str:
    reopened_issue_ = json.loads(new_gh_issue_str)
    reopened_issue_["action"] = "reopened"
    return json.dumps(reopened_issue_)


@pytest.fixture
def closed_gh_issue_str(new_gh_issue_str: str) -> str:
    closed_issue_ = json.loads(new_gh_issue_str)
    closed_issue_["action"] = "closed"
    return json.dumps(closed_issue_)
