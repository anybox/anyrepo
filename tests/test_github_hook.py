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
from unittest.mock import patch


def regenerate_headers_hash_from_data(secret: bytes, data: str) -> str:
    hash_object = hmac.new(secret, data.encode("utf-8"), "sha1")
    hex_dig = hash_object.hexdigest()
    return f"sha1={hex_dig}"


def test_ping(client, gh_headers):
    gh_headers["HTTP_X_GITHUB_EVENT"] = "ping"
    response = client.post("/github/", environ_base=gh_headers)
    data = response.get_json()
    assert "msg" in data
    assert data["msg"] == "pong"


def test_without_header(client):
    response = client.post("/github/")
    assert response.status_code == 403


def test_wrong_digest(client, gh_headers):
    gh_headers["HTTP_X_GITHUB_EVENT"] = "ping"
    data = gh_headers["HTTP_X_HUB_SIGNATURE"]
    gh_headers["HTTP_X_HUB_SIGNATURE"] = data.replace("sha1", "md5")
    response = client.post("/github/", environ_base=gh_headers)
    assert response.status_code == 501


def test_wrong_ua(client, gh_headers):
    gh_headers["HTTP_X_GITHUB_EVENT"] = "ping"
    gh_headers["HTTP_USER_AGENT"] = "Chrome"
    response = client.post("/github/", environ_base=gh_headers)
    assert response.status_code == 403


def test_wrong_secret(client, gh_headers):
    gh_headers["HTTP_X_GITHUB_EVENT"] = "ping"
    gh_headers["HTTP_X_HUB_SIGNATURE"] = "sha1=test"
    response = client.post("/github/", environ_base=gh_headers)
    assert response.status_code == 403


def test_unknown_event(client, gh_headers):
    gh_headers["HTTP_X_GITHUB_EVENT"] = "random event"
    response = client.post("/github/", environ_base=gh_headers)
    data = response.get_json()
    assert "status" in data
    assert data["status"] == "skipped"


def test_wrong_data(
    app, client, gh_headers, gh_secret, new_gh_issue_str, github_hook
):
    with app.app_context():
        data_dict = json.loads(new_gh_issue_str)
        del data_dict["action"]
        data = json.dumps(data_dict)

        gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
            gh_secret, data
        )
        gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"
        response = client.post(
            "/github/",
            data=data,
            content_type="application/json",
            environ_base=gh_headers,
        )

        json_data = response.get_json()
        assert json_data == {"status": "error"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_message_dispatch(
    get_client, client, api, dbapi, gh_headers, gh_secret, new_gh_issue_str
):
    get_client.return_value = api
    data = new_gh_issue_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"
    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "issues skipped"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_issue(
    get_client,
    client,
    api,
    dbapi,
    project,
    gh_secret,
    gh_headers,
    new_gh_issue_str,
):
    get_client.return_value = api
    data = new_gh_issue_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"

    project.get_issue_from_title = lambda x: None

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_issue_error(
    get_client,
    client,
    dbapi,
    project,
    gh_secret,
    gh_headers,
    new_gh_issue_str,
):
    api = get_client.return_value
    api.get_project_from_name.side_effect = Exception("test")
    data = new_gh_issue_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"
    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "error"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_issues_api_with_same_url(
    get_client, client, api, dbapi, gh_headers, gh_secret, new_gh_issue_str
):
    get_client.return_value = api
    data = new_gh_issue_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"

    api.url = "https://github.com"

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    assert response.status_code == 200


@patch("anyrepo.models.api.ApiModel.get_client")
def test_repoen_issue(
    get_client,
    client,
    api,
    dbapi,
    gh_secret,
    gh_headers,
    reopened_gh_issue_str,
    issue,
):
    get_client.return_value = api
    data = reopened_gh_issue_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}
    assert issue.state == "reopen"


@patch("anyrepo.models.api.ApiModel.get_client")
def test_close_issue(
    get_client,
    client,
    api,
    dbapi,
    gh_secret,
    gh_headers,
    closed_gh_issue_str,
    issue,
):
    get_client.return_value = api
    data = closed_gh_issue_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issues"

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}
    assert issue.state == "close"


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_comment(
    get_client,
    client,
    api,
    dbapi,
    gh_secret,
    gh_headers,
    new_gh_issue_comment_str,
    issue,
):
    get_client.return_value = api
    data = new_gh_issue_comment_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issue_comment"

    issue.get_comment_from_body = lambda x: None

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_comment_error(
    get_client, client, dbapi, gh_secret, gh_headers, new_gh_issue_comment_str,
):
    api = get_client.return_value
    api.get_project_from_name.side_effect = Exception("test")
    data = new_gh_issue_comment_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issue_comment"
    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "error"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_edit_comment(
    get_client,
    api,
    dbapi,
    client,
    gh_secret,
    gh_headers,
    edited_gh_issue_comment_str,
    comment,
):
    get_client.return_value = api
    data = json.loads(edited_gh_issue_comment_str)
    data["changes"] = {"body": {"from": data["comment"]["body"]}}
    data["comment"]["body"] = "New value"
    data_str = json.dumps(data)

    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data_str
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issue_comment"

    response = client.post(
        "/github/",
        data=data_str,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}
    assert comment.body == "New value"


@patch("anyrepo.models.api.ApiModel.get_client")
def test_delete_comment(
    get_client,
    api,
    dbapi,
    client,
    gh_secret,
    gh_headers,
    deleted_gh_issue_comment_str,
    comment,
):
    get_client.return_value = api
    data = deleted_gh_issue_comment_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issue_comment"

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert comment.delete.called
    assert json_data["FakeAPI"] == {"status": "done"}


@patch("anyrepo.models.api.ApiModel.get_client")
def test_comment_api_with_same_url(
    get_client,
    client,
    api,
    dbapi,
    gh_secret,
    gh_headers,
    new_gh_issue_comment_str,
):
    get_client.return_value = api
    data = new_gh_issue_comment_str
    gh_headers["HTTP_X_HUB_SIGNATURE"] = regenerate_headers_hash_from_data(
        gh_secret, data
    )
    gh_headers["HTTP_X_GITHUB_EVENT"] = "issue_comment"

    api.url = "https://github.com"

    response = client.post(
        "/github/",
        data=data,
        content_type="application/json",
        environ_base=gh_headers,
    )

    assert response.status_code == 200
