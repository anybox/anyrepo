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


def test_ping(client, gl_headers):
    gl_headers["HTTP_X_GITLAB_EVENT"] = "ping"
    response = client.post("/gitlab/", environ_base=gl_headers)
    data = response.get_json()
    assert "msg" in data
    assert data["msg"] == "pong"


def test_without_header(client):
    response = client.post("/gitlab/")
    assert response.status_code == 403


def test_wrong_secret(client, gl_headers):
    gl_headers["HTTP_X_GITLAB_EVENT"] = "ping"
    gl_headers["HTTP_X_GITLAB_TOKEN"] = "test"
    response = client.post("/gitlab/", environ_base=gl_headers)
    assert response.status_code == 403


def test_unknown_event(client, gl_headers):
    gl_headers["HTTP_X_GITLAB_EVENT"] = "random event"
    response = client.post("/gitlab/", environ_base=gl_headers)
    data = response.get_json()
    assert "status" in data
    assert data["status"] == "skipped"


def test_create_issue(client, api, project, gl_headers, new_gl_issue_str):
    data = new_gl_issue_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

    project.get_issue_from_title = lambda x: None

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}


def test_issues_api_with_same_url(client, api, gl_headers, new_gl_issue_str):
    data = new_gl_issue_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

    api.url = "http://example.com"

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "issues skipped"}


def test_repoen_issue(client, api, gl_headers, new_gl_issue_str, issue):
    data = new_gl_issue_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}
    assert issue.state == "opened"


def test_close_issue(client, api, gl_headers, closed_gl_issue_str, issue):
    data = closed_gl_issue_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}
    assert issue.state == "closed"


def test_create_comment(
    client, api, gl_headers, new_gl_issue_comment_str, issue
):
    data = new_gl_issue_comment_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Note Hook"

    issue.get_comment_from_body = lambda x: None

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "done"}


def test_comment_api_with_same_url(
    client, api, gl_headers, new_gl_issue_comment_str, issue
):
    data = new_gl_issue_comment_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Note Hook"

    issue.get_comment_from_body = lambda x: None
    api.url = "http://example.com"

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "issue comment skipped"}
