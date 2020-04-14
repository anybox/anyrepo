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
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from anyrepo.forms import ApiForm, HookForm, LoginForm, UserForm
from anyrepo.models import db
from anyrepo.models.api import ApiModel
from anyrepo.models.hook import HookModel
from anyrepo.models.request import RequestModel
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

        user = User.query.filter_by(username=username).one_or_none()
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
    apicount = ApiModel.query.count()
    hookcount = HookModel.query.count()
    usercount = User.query.count()
    badrequests = RequestModel.query.filter(RequestModel.status != 200).count()
    goodrequests = RequestModel.query.filter_by(status=200).count()
    return render_template(
        "index.html",
        apicount=apicount,
        hookcount=hookcount,
        usercount=usercount,
        badrequests=badrequests,
        goodrequests=goodrequests,
    )


@admin.route("/apis/")
@login_required
def apis():
    """List all the registered APIs."""
    apis = ApiModel.query.all()
    return render_template("apis.html", apis=apis)


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
        api_id = api.id or 0
        exists = ApiModel.query.filter(
            ApiModel.url == url, ApiModel.id != api_id
        ).one_or_none()
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
            return redirect(url_for("admin.apis"))
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
        abort(404)

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


@admin.route("/users/")
@login_required
def users():
    """List users."""
    users = User.query.all()
    return render_template(
        "users.html",
        users=users,
        ldap=current_app.config.get("LDAP_PROVIDER_URL"),
    )


@admin.route(
    "/user/new/", defaults={"useruuid": None}, methods=["GET", "POST"]
)
@admin.route("/user/edit/<useruuid>/", methods=["GET", "POST"])
@login_required
def user_edit(useruuid=None):
    """Create or edit a user."""
    ldap_provider = current_app.config.get("LDAP_PROVIDER_URL")
    if ldap_provider is not None:
        flash("Users are managed by a LDAP provider", "error")
        return redirect(url_for("admin.users"))

    if useruuid is not None and useruuid != current_user.slug:
        msg = "You can only edit your own data"
        abort(make_response(jsonify(message=msg), 403))

    user = (
        User.query.filter_by(slug=useruuid).first_or_404()
        if useruuid
        else User()
    )
    form = UserForm(obj=user)
    if request.method == "POST":
        userid = user.id or 0
        exists = User.query.filter(
            User.username == form.username.data, User.id != userid
        ).one_or_none()
        if exists is not None:
            flash("There is already a User with this username", "error")
        elif form.validate_on_submit():
            user.username = form.username.data
            user.set_password(form.password.data)
            msg = "User successfully modified"

            if not user.id:
                db.session.add(user)
                msg = "User successfully created"

            db.session.commit()
            flash(msg, "success")
            return redirect(url_for("admin.users"))
        else:
            for field, errors in form.errors.items():
                flash(f"{form[field].name} : {', '.join(errors)}", "error")

    return render_template("userform.html", form=form, user=user)


@admin.route("/user/delete/", methods=["POST"])
@login_required
def user_delete():
    """Delete a user from its uuid."""
    ldap = current_app.config.get("LDAP_PROVIDER_URL")
    if ldap is not None:
        flash("Users are managed by a LDAP provider", "error")
        return redirect(url_for("admin.users"))

    useruuid = request.form.get("slug")
    if not useruuid:
        abort(404)

    count = User.query.count()
    if count == 1:
        msg = "You can not delete the only user"
        abort(make_response(jsonify(message=msg), 403))

    user = User.query.filter_by(slug=useruuid).first_or_404()
    db.session.delete(user)
    db.session.commit()
    flash("User successfully removed", "success")
    return redirect(url_for("admin.users"))


@admin.route("/logout/")
@login_required
def logout():
    """Logout current user."""
    logout_user()
    return redirect(url_for("admin.login"))
