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

import json
from unittest.mock import patch

from anyrepo.models import db
from anyrepo.models.log import Log


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


def test_wrong_data(app, client, gl_headers, new_gl_issue_str, gitlab_hook):
    with app.app_context():
        data_dict = json.loads(new_gl_issue_str)
        del data_dict["object_attributes"]
        hook_log_count = Log.query.filter_by(hook_id=gitlab_hook.id).count()
        gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

        response = client.post(
            "/gitlab/",
            data=json.dumps(data_dict),
            content_type="application/json",
            environ_base=gl_headers,
        )

        json_data = response.get_json()

        new_count = Log.query.filter_by(hook_id=gitlab_hook.id).count()
        assert json_data == {"status": "error"}
        assert new_count > hook_log_count


def test_unknown_event(client, gl_headers):
    gl_headers["HTTP_X_GITLAB_EVENT"] = "random event"
    response = client.post("/gitlab/", environ_base=gl_headers)
    data = response.get_json()
    assert "status" in data
    assert data["status"] == "skipped"


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_issue(
    get_client, client, api, dbapi, project, gl_headers, new_gl_issue_str
):
    get_client.return_value = api
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


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_issue_error(
    get_client, client, dbapi, gl_headers, new_gl_issue_str
):
    api = get_client.return_value
    api.get_project_from_name.side_effect = Exception("test")
    api_log_count = Log.query.filter_by(api_id=dbapi.id).count()
    data = new_gl_issue_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()
    new_log_count = Log.query.filter_by(api_id=dbapi.id).count()

    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "error"}
    assert new_log_count > api_log_count


@patch("anyrepo.models.api.ApiModel.get_client")
def test_issues_api_with_same_url(
    get_client, client, api, dbapi, gl_headers, new_gl_issue_str
):
    get_client.return_value = api
    data = new_gl_issue_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Issue Hook"

    dbapi.url = "http://example.com"
    db.session.commit()

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    assert response.status_code == 200


@patch("anyrepo.models.api.ApiModel.get_client")
def test_repoen_issue(
    get_client, client, api, dbapi, gl_headers, new_gl_issue_str, issue
):
    get_client.return_value = api
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


@patch("anyrepo.models.api.ApiModel.get_client")
def test_close_issue(
    get_client, client, api, dbapi, gl_headers, closed_gl_issue_str, issue
):
    get_client.return_value = api
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


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_comment(
    get_client, client, api, dbapi, gl_headers, new_gl_issue_comment_str, issue
):
    get_client.return_value = api
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


@patch("anyrepo.models.api.ApiModel.get_client")
def test_create_comment_error(
    get_client, client, dbapi, gl_headers, new_gl_issue_comment_str
):
    api = get_client.return_value
    api.get_project_from_name.side_effect = Exception("test")
    api_log_count = Log.query.filter_by(api_id=dbapi.id).count()
    data = new_gl_issue_comment_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Note Hook"

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    json_data = response.get_json()
    new_log_count = Log.query.filter_by(api_id=dbapi.id).count()

    assert "FakeAPI" in json_data
    assert json_data["FakeAPI"] == {"status": "error"}
    assert new_log_count > api_log_count


@patch("anyrepo.models.api.ApiModel.get_client")
def test_comment_api_with_same_url(
    get_client, client, api, dbapi, gl_headers, new_gl_issue_comment_str, issue
):
    get_client.return_value = api
    data = new_gl_issue_comment_str
    gl_headers["HTTP_X_GITLAB_EVENT"] = "Note Hook"

    issue.get_comment_from_body = lambda x: None
    dbapi.url = "http://example.com"
    db.session.commit()

    response = client.post(
        "/gitlab/",
        data=data,
        content_type="application/json",
        environ_base=gl_headers,
    )

    assert response.status_code == 200
