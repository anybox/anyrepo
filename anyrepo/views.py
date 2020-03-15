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

from typing import Optional

import ldap
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import LoginManager, login_required, login_user, logout_user

from anyrepo.forms import ApiForm, HookForm, LoginForm
from anyrepo.models import db
from anyrepo.models.api import ApiModel
from anyrepo.models.hook import HookModel
from anyrepo.models.log import Log
from anyrepo.models.user import User

admin = Blueprint("admin", __name__)
login_manager = LoginManager()
login_manager.login_view = "admin.login"


@login_manager.user_loader
def get_user(userid: int) -> Optional[User]:
    """Get user from its id."""
    if "ldap_user" in session:
        return User(username=session["ldap_user"])

    return User.query.get(userid)


@admin.route("/login/", methods=["GET", "POST"])
def login():
    """Login page."""
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.index"))

        if current_app.config.get("LDAP_PROVIDER_URL"):
            conn = ldap.initialize(current_app.config["LDAP_PROVIDER_URL"])
            bind = current_app.config["LDAP_BIND_FORMAT"].format(
                username=username
            )
            try:
                conn.simple_bind_s(bind, password)
                user = User(username=username)
                session["ldap_user"] = username
                login_user(user)
                return redirect(url_for("admin.index"))
            except ldap.INVALID_CREDENTIALS:
                flash("Invalid username or password", "error")
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html", form=form)


@admin.route("/")
@login_required
def index():
    """List admin page."""
    logs = (
        Log.query.filter(Log.api_id.is_(None), Log.hook_id.is_(None))
        .order_by(Log.created_at)
        .all()
    )
    apicount = ApiModel.query.count()
    hookcount = HookModel.query.count()
    return render_template(
        "index.html", logs=logs, apicount=apicount, hookcount=hookcount
    )


@admin.route("/apis/")
@login_required
def apis():
    """List all the registered APIs."""
    apis = ApiModel.query.all()
    return render_template("apis.html", apis=apis)


@admin.route("/api/details/<apiuuid>/")
@login_required
def api_detail(apiuuid):
    """Show API details."""
    api = ApiModel.query.filter_by(slug=apiuuid).first_or_404()
    return render_template("apidetail.html", api=api)


@admin.route("/api/new/", defaults={"apiuuid": None}, methods=["GET", "POST"])
@admin.route("/api/edit/<apiuuid>/", methods=["GET", "POST"])
@login_required
def api_edit(apiuuid=None):
    """Edit existed api or create a new one."""
    api = (
        ApiModel.query.filter_by(slug=apiuuid).first_or_404()
        if apiuuid
        else ApiModel()
    )
    form = ApiForm(obj=api)
    if request.method == "POST":
        url = form.url.data
        exists = ApiModel.query.filter_by(url=url).first()
        if exists is not None:
            flash("There is already an API for this url", "error")
        elif form.validate_on_submit():
            api.url = url
            api.name = form.name.data
            api.api_type = form.api_type.data
            api.set_token(form.token.data)
            msg = "API successfully modified"

            if not api.id:
                db.session.add(api)
                msg = "API successfully created"

            db.session.commit()
            flash(msg, "success")
            return redirect(url_for("admin.api_detail", apiuuid=api.slug))
        else:
            for field, errors in form.errors.items():
                flash(f"{form[field].name} : {', '.join(errors)}", "error")

    return render_template("apiform.html", form=form, api=api)


@admin.route("/api/delete/", methods=["POST"])
@login_required
def api_delete():
    """Delete an api from its uuid."""
    apiuuid = request.form.get("slug")
    if not apiuuid:
        abort(501)

    api = ApiModel.query.filter_by(slug=apiuuid).first_or_404()
    db.session.delete(api)
    db.session.commit()
    flash("API successfully removed", "success")
    return redirect(url_for("admin.apis"))


@admin.route("/hooks/")
@login_required
def hooks():
    """List registered hooks."""
    hooks = HookModel.query.all()
    hostname = request.url_root[:-1]
    return render_template("hooks.html", hooks=hooks, hostname=hostname)


@admin.route("/hook/edit/<hookuuid>/", methods=["GET", "POST"])
@login_required
def hook_edit(hookuuid):
    """Edit existed hook or create a new one."""
    hook = HookModel.query.filter_by(slug=hookuuid).first_or_404()
    hostname = request.url_root[:-1]
    form = HookForm(obj=hook)
    if request.method == "POST":
        if form.validate_on_submit():
            hook.set_secret(form.secret.data)
            db.session.commit()
            flash("Hook secret successfully modified", "success")
            return redirect(url_for("admin.hook_detail", hookuuid=hook.slug))
        else:
            for field, errors in form.errors.items():
                flash(f"{form[field].name} : {', '.join(errors)}", "error")

    return render_template(
        "hookform.html", form=form, hook=hook, hostname=hostname
    )


@admin.route("/hook/details/<hookuuid>/")
@login_required
def hook_detail(hookuuid):
    """Show Hook detail."""
    hook = HookModel.query.filter_by(slug=hookuuid).first_or_404()
    hostname = request.url_root[:-1]
    return render_template("hookdetail.html", hook=hook, hostname=hostname)


@admin.route("/logout/")
@login_required
def logout():
    """Logout current user."""
    logout_user()
    return redirect(url_for("admin.login"))
