import os
import gitlab


def get_gitlab_client():
    """Get gitlab bot client"""
    url = os.environ.get("GITLAB_URL")
    token = os.environ.get("GITLAB_TOKEN")

    return gitlab.Gitlab(url, private_token=token)
