import logging
import os
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from issuebot.github_hook import github_hook


def create_app():
    """App factory"""
    app = Flask(__name__)
    app.config.from_object("issuebot.default_settings")

    app.register_blueprint(github_hook, url_prefix="/hook/")

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
