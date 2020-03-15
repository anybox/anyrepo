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


from unittest.mock import patch

import ldap

from anyrepo.models.api import ApiModel
from anyrepo.models.hook import HookModel


@patch("ldap.initialize")
def test_login(fakeldap, app, client, user):
    conn = fakeldap.return_value
    conn.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS

    data = {"username": user.username, "password": "test"}
    res = client.post("/login/", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"username" not in res.data

    res = client.get("/logout/", follow_redirects=True)
    assert res.status_code == 200
    assert b"username" in res.data

    data = {"username": user.username, "password": "invalidPassw0rd"}
    res = client.post("/login/", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data

    data = {"username": "invaliduser", "password": "test"}
    res = client.post("/login/", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data


@patch("ldap.initialize")
def test_login_ldap(fakeldap, client, user):
    data = {"username": "anotheruser", "password": "test"}
    res = client.post("/login/", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" not in res.data


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"3 registered APIs" in res.data
    assert b"2 registered Hooks" in res.data
    assert b"Registered a blueprint for a gitlab hook at /gitlab/" in res.data
    assert b"Registered a blueprint for a github hook at /github/" in res.data


def test_api_list(client):
    res = client.get("/apis/")
    assert res.status_code == 200
    assert b"github" in res.data
    assert b"gitlab" in res.data
    assert b"anothergitlab" in res.data


def test_api_details(client, dbapi):
    res = client.get(f"/api/details/{dbapi.slug}/")
    token = dbapi.get_token()
    assert res.status_code == 200
    assert dbapi.name.encode() in res.data
    assert dbapi.url.encode() in res.data
    assert token.encode() not in res.data

    res = client.get(f"/api/details/notaslug/")
    assert res.status_code == 404


def test_hooks(client):
    res = client.get("/hooks/")
    assert res.status_code == 200
    assert b"/gitlab/" in res.data
    assert b"/github/" in res.data
    assert b"gitlab" in res.data
    assert b"github" in res.data


def test_hook_details(app, client, github_hook):
    with app.app_context():
        res = client.get(f"/hook/details/{github_hook.slug}/")
        secret = github_hook.get_secret()
        assert res.status_code == 200
        assert github_hook.endpoint.encode() in res.data
        assert github_hook.hook_type.value.encode() in res.data
        assert secret.encode() not in res.data

        res = client.get("/hook/details/notaslug/")
        assert res.status_code == 404


def test_api_edit(app, client, dbapi):
    res = client.get(f"/api/edit/{dbapi.slug}/")
    token = dbapi.get_token()
    assert res.status_code == 200
    assert dbapi.name.encode() in res.data
    assert dbapi.url.encode() in res.data
    assert token.encode() not in res.data

    res = client.get(f"/api/edit/notaslug/")
    assert res.status_code == 404

    data = {
        "name": "This is a test",
        "api_type": "GITHUB",
        "url": "http://testapi.com/",
        "token": "A new token",
    }
    res = client.post(
        f"/api/edit/{dbapi.slug}/", data=data, follow_redirects=True
    )

    assert res.status_code == 200
    assert dbapi.name == "This is a test"
    assert dbapi.url == "http://testapi.com/"
    assert dbapi.get_token() == "A new token"

    invalid_data = {
        "name": "This is a second test",
        "api_type": "GITHUB",
        "url": "not a url",
        "token": "A newer token",
    }
    res = client.post(
        f"/api/edit/{dbapi.slug}/", data=invalid_data, follow_redirects=True
    )

    assert res.status_code == 200
    assert dbapi.name != "This is a second test"
    assert dbapi.url != "not a url"
    assert dbapi.get_token() != "A newer token"


def test_new_api(app, client, dbapi):
    with app.app_context():
        apicount = ApiModel.query.count()
        data = {
            "name": "This is a test",
            "api_type": "GITHUB",
            "url": "http://testapi.com/",
            "token": "A new token",
        }
        res = client.post("/api/new/", data=data, follow_redirects=True)

        assert res.status_code == 200
        assert apicount + 1 == ApiModel.query.count()

        apicount = ApiModel.query.count()
        data = {
            "name": "This is a test",
            "api_type": "GITHUB",
            "url": dbapi.url,
            "token": "A new token",
        }
        res = client.post("/api/new/", data=data, follow_redirects=True)

        assert res.status_code == 200
        assert apicount == ApiModel.query.count()
        assert b"There is already an API for this url" in res.data


def test_delete_api(app, client, dbapi):
    with app.app_context():
        apicount = ApiModel.query.count()
        res = client.post("/api/delete/", data={"slug": dbapi.slug})
        assert res.status_code == 302
        assert apicount - 1 == ApiModel.query.count()

        res = client.post("/api/delete/", data={"slug": "notaslug"})
        assert res.status_code == 404

        res = client.post("/api/delete/", data={})
        assert res.status_code == 501


def test_hook_edit(app, client, github_hook):
    with app.app_context():
        res = client.get(f"/hook/edit/{github_hook.slug}/")
        assert res.status_code == 200
        assert github_hook.endpoint.encode() in res.data
        assert github_hook.hook_type.value.encode() in res.data

        res = client.get("/hook/edit/notaslug/")
        assert res.status_code == 404

        data = {"secret": "this is a secret"}
        res = client.post(
            f"/hook/edit/{github_hook.slug}/", data=data, follow_redirects=True
        )
        hook = HookModel.query.get(github_hook.id)
        assert res.status_code == 200
        assert hook.get_secret() == "this is a secret"

        res = client.post(f"/hook/edit/{github_hook.slug}/", data={})
        assert res.status_code == 200
