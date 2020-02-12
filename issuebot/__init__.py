import logging
import os
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from issuebot.hooks.github_hook import github_hook
from issuebot.hooks.gitlab_hook import gitlab_hook


def create_app():
    """App factory"""
    app = Flask(__name__)
    app.config.from_object("issuebot.config")

    app.register_blueprint(github_hook, url_prefix="/github/")
    app.register_blueprint(gitlab_hook, url_prefix="/gitlab/")

    if not app.debug:
        file_handler = TimedRotatingFileHandler(
            os.path.join(app.config["LOG_DIR"], "issuebot.log"), "midnight"
        )
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(
            logging.Formatter("<%(asctime)s> <%(levelname)s> %(message)s")
        )
        app.logger.addHandler(file_handler)

    return app
