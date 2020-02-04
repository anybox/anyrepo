import os
import hmac
import logging

from flask import Blueprint, request, abort, jsonify, current_app
from issuebot.utils import get_gitlab_client

github_hook = Blueprint("github_hook", __name__)


@github_hook.before_request
def check_validity():
    secret = os.environ.get("GITHUB_HOOK_SECRET")
    header_sign = request.headers.get("X-Hub-Signature")
    if not header_sign:
        current_app.logger.info("No header sign")
        abort(403)

    sha_name, sign = header_sign.split("=")
    if sha_name != "sha1":
        current_app.logger.info("Not SHA1")
        abort(501)

    mac = hmac.new(secret.encode("utf-8"), msg=request.data, digestmod="sha1")
    if not hmac.compare_digest(str(mac.hexdigest()), str(sign)):
        current_app.logger.info("Invalid secret")
        abort(403)

    referer = request.headers.get("User-Agent", "")
    if not referer.startswith("GitHub-Hookshot"):
        current_app.logger.info("Invalid referer")
        abort(403)


@github_hook.route("/", methods=["POST"])
def index():
    data = request.get_json()
    event_type = request.headers.get("X-GitHub-Event", "ping")

    response = {"status": "skipped"}
    if event_type == "ping":
        response = {"msg": "pong"}
    elif event_type == "issues":
        response = manage_issues(data)

    return jsonify(response)


def manage_issues(data: dict) -> dict:
    """Manage github issues"""
    gl = get_gitlab_client()
    response = {"status": "issues skipped"}

    action = data.get("action")
    repo = data.get("repository")
    issue = data.get("issue")

    repo_name = repo.get("full_name", "").split("/")[-1]
    gl_project = next(
        iter(gl.projects.list(search=repo_name)), None
    )
    issue = next(
        iter(gl_project.issues.list(title=issue.get("title"))), None
    )
    if gl_project:
        if action == "opened":
            gl_project.issues.create(
                {
                    "title": issue.get("title"),
                    "description": "<br>".join(
                        [issue.get("url"), issue.get("body")]
                    ),
                }
            )
            response["status"] = "done"
        elif action == "reopened" and issue:            
            issue.state_event = "reopen"
            issue.save()
            response["status"] = "done"
        elif action == "closed" and issue:
            issue.state_event = "close"
            issue.save()
            response["status"] = "done"            

    return response
