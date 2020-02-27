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

from urllib.parse import urlparse

from flask import Blueprint, abort, current_app, jsonify, request

gitlab_hook = Blueprint("gitlab_hook", __name__)


@gitlab_hook.before_request
def check_validity():
    """Check secret and headers validity or raise an error."""
    hooks = current_app.config["hooks"]
    endpoint = request.url_rule.rule
    secret = hooks[endpoint]

    header_sign = request.headers.get("X-Gitlab-Token")
    if not header_sign:
        current_app.logger.warning("No header sign")
        abort(403)

    if secret != header_sign:
        current_app.logger.warning("Invalid secret")
        abort(403)


@gitlab_hook.route("/", methods=["POST"])
def index():
    data = request.get_json()
    event_type = request.headers.get("X-Gitlab-Event", "ping")

    response = {"status": "skipped"}
    if event_type == "ping":
        response = {"msg": "pong"}
    elif event_type == "Issue Hook":
        response = manage_issues(data)
    elif event_type == "Note Hook":
        response = manage_issue_comment(data)

    return jsonify(response)


def manage_issues(data: dict) -> dict:
    """Manage issues."""
    apis = current_app.config["apis"]
    response = {}
    for api in apis:
        response[api.name] = {"status": "issues skipped"}

        action = data["object_attributes"]["state"]
        project_dict = data["project"]
        issue_dict = data["object_attributes"]

        repo_url = urlparse(project_dict["git_http_url"])
        api_url = urlparse(api.url)
        if repo_url.hostname == api_url.hostname:
            continue

        repo_name = project_dict.get("path_with_namespace", "").split("/")[-1]
        project = api.get_project_from_name(repo_name)
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

    return response


def manage_issue_comment(data: dict) -> dict:
    """Manage issue comments.
    :NB: Only created action is managed by Gitlab Webhook for now
    """
    apis = current_app.config["apis"]
    response = {}
    for api in apis:
        response[api.name] = {"status": "issue comment skipped"}

        project_dict = data["project"]
        issue_dict = data["issue"]
        comment_dict = data["object_attributes"]

        repo_url = urlparse(project_dict["git_http_url"])
        api_url = urlparse(api.url)
        if repo_url.hostname == api_url.hostname:
            continue

        repo_name = project_dict.get("path_with_namespace", "").split("/")[-1]
        project = api.get_project_from_name(repo_name)

        if project:
            issue = project.get_issue_from_title(issue_dict["title"])

            if issue:
                comment = issue.get_comment_from_body(comment_dict["note"])
                if comment is None:
                    issue.create_comment(comment_dict["note"])
                    response[api.name]["status"] = "done"

    return response
