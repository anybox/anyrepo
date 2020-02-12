import os

from flask import Blueprint, request, abort, jsonify, current_app
from issuebot.api.github_api import GithubAPI

gitlab_hook = Blueprint("gitlab_hook", __name__)


@gitlab_hook.before_request
def check_validity():
    secret = os.environ.get("GITLAB_HOOK_SECRET")
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
    """Manage gitlab issues received from Github's API."""
    gh = GithubAPI()
    response = {"status": "issues skipped"}

    action = data["object_attributes"]["state"]
    project_dict = data["project"]
    issue_dict = data["object_attributes"]

    repo_name = project_dict.get("path_with_namespace", "").split("/")[-1]
    project = gh.get_project_from_name(repo_name)
    if project:
        issue = project.get_issue_from_title(issue_dict["title"])

        if action == "opened" and not issue:
            project.create_issue(issue_dict["title"], issue_dict["description"])
            response["status"] = "done"
        elif action == "opened" and issue:
            issue.state = "opened"
            response["status"] = "done"
        elif action == "closed" and issue:
            issue.state = "closed"
            response["status"] = "done"

    return response


def manage_issue_comment(data: dict) -> dict:
    """Manage issue comments
    :NB: Only created action is managed by Gitlab Webhook for now
    """
    gh = GithubAPI()
    response = {"status": "issue comment skipped"}

    project_dict = data["project"]
    issue_dict = data["issue"]
    comment_dict = data["object_attributes"]

    repo_name = project_dict.get("path_with_namespace", "").split("/")[-1]
    project = gh.get_project_from_name(repo_name)

    if project:
        issue = project.get_issue_from_title(issue_dict["title"])

        if issue:
            comment = issue.get_comment_from_body(comment_dict["note"])
            if comment is None:
                issue.create_comment(comment_dict["note"])
                response["status"] = "done"

    return response
