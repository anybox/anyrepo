import os
import hmac

from flask import Blueprint, request, abort, jsonify, current_app
from issuebot.api.gitlab import GitlabAPI

github_hook = Blueprint("github_hook", __name__)


@github_hook.before_request
def check_validity():
    secret = os.environ.get("GITHUB_HOOK_SECRET")
    header_sign = request.headers.get("X-Hub-Signature")
    if not header_sign:
        current_app.logger.warning("No header sign")
        abort(403)

    sha_name, sign = header_sign.split("=")
    if sha_name != "sha1":
        current_app.logger.warning("Not SHA1")
        abort(501)

    mac = hmac.new(secret.encode("utf-8"), msg=request.data, digestmod="sha1")
    if not hmac.compare_digest(str(mac.hexdigest()), str(sign)):
        current_app.logger.warning("Invalid secret")
        abort(403)

    referer = request.headers.get("User-Agent", "")
    if not referer.startswith("GitHub-Hookshot"):
        current_app.logger.warning("Invalid referer")
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
    elif event_type == "issue_comment":
        response = manage_issue_comment(data)

    return jsonify(response)


def manage_issues(data: dict) -> dict:
    """Manage github issues"""
    gl = GitlabAPI()
    response = {"status": "issues skipped"}

    action = data["action"]
    repo_dict = data["repository"]
    issue_dict = data["issue"]

    repo_name = repo_dict.get("full_name", "").split("/")[-1]
    project = gl.get_project_from_name(repo_name)

    if project:
        issue = gl.get_issue_from_title(project, issue_dict["title"])
        if action == "opened" and not issue:
            project.issues.create(
                {
                    "title": issue_dict["title"],
                    "description": "<br>".join(
                        [issue_dict["html_url"], issue_dict["body"]]
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


def manage_issue_comment(data: dict) -> dict:
    """Manage issue comments"""
    gl = GitlabAPI()
    response = {"status": "issue comment skipped"}

    action = data["action"]
    repo_dict = data["repository"]
    issue_dict = data["issue"]
    comment_dict = data["comment"]

    repo_name = repo_dict.get("full_name", "").split("/")[-1]
    project = gl.get_project_from_name(repo_name)

    if project:
        issue = gl.get_issue_from_title(project, issue_dict["title"])

        if issue:
            comment_list = issue.discussions.list()
            comment = None
            content = "<br>".join(
                [comment_dict["html_url"], comment_dict["body"]]
            )

            for comment in comment_list:
                for note in comment.attributes["notes"]:
                    if note["body"].startswith(comment_dict["html_url"]):
                        comment = comment.notes.get(note["id"])

            if action == "created" and not comment:
                issue.discussions.create({"body": content})
                response["status"] = "done"
            elif action == "edited" and comment:
                comment.body = content
                comment.save()
                response["status"] = "done"
            elif action == "deleted" and comment:
                comment.delete()
                response["status"] = "done"

    return response
