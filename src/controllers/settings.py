from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Setting, Role
from src.auth import login_user, login_required, logout_user, current_user
from src.settings import Settings
from src.ldap import ldap_retrieve_users

bp = Blueprint('settings', __name__, url_prefix="/settings")

@bp.route('/', methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":
        ldap_enabled = bool(request.form.get("ldap-enabled"))
        ldap_server = request.form.get("ldap-server")
        ldap_default_role = request.form.get("ldap-default-role")

        dbs.execute(db.update(Setting).values(
            ldap_enabled = ldap_enabled,
            ldap_server = ldap_server,
            ldap_default_role = ldap_default_role
        ))
        dbs.commit()

        return redirect(url_for("settings.index"))

    settings = dbs.execute(db.select(Setting).limit(1)).scalar_one_or_none()
    roles = Role.query.all()
    return render_template('settings/index.html', roles=roles, settings=settings)

@bp.route("/ldap_retrieve", methods=["POST"])
@login_required
def ldap_retrieve():
    ldap_enabled = Settings.get("ldap_enabled")

    if not ldap_enabled:
        return redirect(url_for("settings.index"))

    ldap_server = Settings.get("ldap_server")
    ldap_default_role = Settings.get("ldap_default_role")
    ldap_retrieve_users(ldap_server, ldap_default_role)
    
    return redirect(url_for("users.index"))