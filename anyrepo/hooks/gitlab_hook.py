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
from urllib.parse import urlparse

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    jsonify,
    make_response,
    request,
)

from anyrepo.models import db
from anyrepo.models.api import ApiModel
from anyrepo.models.hook import HookModel
from anyrepo.models.request import RequestModel

gitlab_hook = Blueprint("gitlab_hook", __name__)


@gitlab_hook.before_request
def check_validity():
    """Check secret and headers validity or raise an error."""
    endpoint = request.url_rule.rule
    hook = HookModel.query.filter_by(endpoint=endpoint).first_or_404()
    secret = hook.get_secret()

    header_sign = request.headers.get("X-Gitlab-Token")
    if not header_sign:
        msg = "No header sign"
        current_app.logger.error(msg)
        abort(make_response(jsonify(message=msg), 403))

    if secret != header_sign:
        msg = "Invalid secret"
        current_app.logger.error(msg)
        abort(make_response(jsonify(message=msg), 403))


@gitlab_hook.route("/", methods=["POST"])
def index():
    data = request.get_json()
    event_type = request.headers.get("X-Gitlab-Event", "ping")

    try:
        response = {"status": "skipped"}
        if event_type == "ping":
            response = {"msg": "pong"}
        elif event_type == "Issue Hook":
            response = manage_issues(data)
        elif event_type == "Note Hook":
            response = manage_issue_comment(data)
    except Exception as err:
        current_app.logger.error(str(err))
        response = {"status": "error"}

    return jsonify(response)


def manage_issues(data: dict) -> dict:
    """Manage issues."""
    action = data["object_attributes"]["state"]
    project_dict = data["project"]
    issue_dict = data["object_attributes"]
    repo_name = project_dict.get("path_with_namespace", "").split("/")[-1]
    repo_url = urlparse(project_dict["git_http_url"])

    apidb = ApiModel.query.all()
    apis = [
        api for api in apidb if urlparse(api.url).hostname != repo_url.hostname
    ]

    response = {}
    for api in apis:
        client = api.get_client()
        response[api.name] = {"status": "issues skipped"}
        try:
            project = client.get_project_from_name(repo_name)
            if project:
                issue = project.get_issue_from_title(issue_dict["title"])

                if action == "opened" and not issue:
                    project.create_issue(
                        issue_dict["title"], issue_dict["description"]
                    )
                    response[api.name]["status"] = "done"
                elif action == "opened" and issue:
                    issue.state = "opened"
                    response[api.name]["status"] = "done"
                elif action == "closed" and issue:
                    issue.state = "closed"
                    response[api.name]["status"] = "done"
        except Exception as err:
            current_app.logger.error(str(err))
            response[api.name] = {"status": "error"}

    return response


def manage_issue_comment(data: dict) -> dict:
    """Manage issue comments.
    :NB: Only created action is managed by Gitlab Webhook for now
    """
    project_dict = data["project"]
    issue_dict = data["issue"]
    comment_dict = data["object_attributes"]
    repo_url = urlparse(project_dict["git_http_url"])
    repo_name = project_dict.get("path_with_namespace", "").split("/")[-1]

    apidb = ApiModel.query.all()
    apis = [
        api for api in apidb if urlparse(api.url).hostname != repo_url.hostname
    ]

    response = {}
    for api in apis:
        client = api.get_client()
        response[api.name] = {"status": "issue comments skipped"}
        try:
            project = client.get_project_from_name(repo_name)
            if project:
                issue = project.get_issue_from_title(issue_dict["title"])

                if issue:
                    comment = issue.get_comment_from_body(comment_dict["note"])
                    if comment is None:
                        issue.create_comment(comment_dict["note"])
                        response[api.name]["status"] = "done"
        except Exception as err:
            current_app.logger.error(str(err))
            response[api.name] = {"status": "error"}

    return response


@gitlab_hook.after_request
def save_request(response: Response):
    """Save request in db."""
    if request.url_rule:
        endpoint = request.url_rule.rule
        hook = HookModel.query.filter_by(endpoint=endpoint).first_or_404()

        request_model = RequestModel(
            hook_id=hook.id,
            headers=json.dumps(
                {key: value for key, value in request.headers.items()}
            ),
            body=request.data.decode("utf-8"),
            status=response.status_code,
            response=response.data.decode("utf-8"),
        )
        db.session.add(request_model)
        db.session.commit()

    return response
