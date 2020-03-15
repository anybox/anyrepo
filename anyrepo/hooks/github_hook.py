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

import hmac
from urllib.parse import urlparse

from flask import Blueprint, abort, current_app, g, jsonify, request

from anyrepo.models.api import ApiModel
from anyrepo.models.hook import HookModel

github_hook = Blueprint("github_hook", __name__)


@github_hook.before_request
def check_validity():
    """Check secret and headers validity or raise an error."""
    endpoint = request.url_rule.rule
    hook = HookModel.query.filter_by(endpoint=endpoint).first_or_404()
    secret = hook.get_secret()
    g.hook = hook

    header_sign = request.headers.get("X-Hub-Signature")
    if not header_sign:
        current_app.logger.error("No header sign", {"hook_id": hook.id})
        abort(403)

    sha_name, sign = header_sign.split("=")
    if sha_name != "sha1":
        current_app.logger.error("Not SHA1", {"hook_id": hook.id})
        abort(501)

    mac = hmac.new(secret.encode("utf-8"), msg=request.data, digestmod="sha1")
    if not hmac.compare_digest(str(mac.hexdigest()), str(sign)):
        current_app.logger.error("Invalid secret", {"hook_id": hook.id})
        abort(403)

    referer = request.headers.get("User-Agent", "")
    if not referer.startswith("GitHub-Hookshot"):
        current_app.logger.error("Invalid referer", {"hook_id": hook.id})
        abort(403)


@github_hook.route("/", methods=["POST"])
def index():
    data = request.get_json()
    event_type = request.headers.get("X-GitHub-Event", "ping")

    try:
        response = {"status": "skipped"}
        if event_type == "ping":
            response = {"msg": "pong"}
        elif event_type == "issues":
            response = manage_issues(data)
        elif event_type == "issue_comment":
            response = manage_issue_comment(data)
    except Exception as err:
        current_app.logger.error(str(err), {"hook_id": g.hook.id})
        response = {"status": "error"}

    return jsonify(response)


def manage_issues(data: dict) -> dict:
    """Manage issues received."""
    action = data["action"]
    repo_dict = data["repository"]
    issue_dict = data["issue"]
    repo_url = urlparse(repo_dict["html_url"])
    repo_name = repo_dict.get("full_name", "").split("/")[-1]

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
                        issue_dict["title"], issue_dict["body"]
                    )
                    response[api.name]["status"] = "done"
                elif action == "reopened" and issue:
                    issue.state = "reopen"
                    response[api.name]["status"] = "done"
                elif action == "closed" and issue:
                    issue.state = "close"
                    response[api.name]["status"] = "done"
        except Exception as err:
            current_app.logger.error(str(err), {"api_id": api.id})
            response[api.name] = {"status": "error"}

    return response


def manage_issue_comment(data: dict) -> dict:
    """Manage issue comments."""
    action = data["action"]
    repo_dict = data["repository"]
    issue_dict = data["issue"]
    comment_dict = data["comment"]
    repo_url = urlparse(repo_dict["html_url"])
    repo_name = repo_dict.get("full_name", "").split("/")[-1]
    content = comment_dict["body"]
    if "body" in data.get("changes", {}):
        content = data["changes"]["body"]["from"]

    apidb = ApiModel.query.all()
    apis = [
        api for api in apidb if urlparse(api.url).hostname != repo_url.hostname
    ]

    response = {}
    for api in apis:
        client = api.get_client()
        response[api.name] = {"status": "issue comment skipped"}

        try:
            project = client.get_project_from_name(repo_name)

            if project:
                issue = project.get_issue_from_title(issue_dict["title"])

                if issue:
                    comment = issue.get_comment_from_body(content)
                    if action == "created" and not comment:
                        issue.create_comment(comment_dict["body"])
                        response[api.name]["status"] = "done"
                    elif action == "edited" and comment:
                        comment.body = comment_dict["body"]
                        response[api.name]["status"] = "done"
                    elif action == "deleted" and comment:
                        comment.delete()
                        response[api.name]["status"] = "done"
        except Exception as err:
            current_app.logger.error(str(err), {"api_id": api.id})
            response[api.name] = {"status": "error"}

    return response
