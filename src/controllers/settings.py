from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Setting
from src.auth import login_user, admin_required, logout_user, current_user
from src.settings import Settings
from src.ldap import ldap_retrieve_users

bp = Blueprint('settings', __name__, url_prefix="/settings")

@bp.route('/', methods=["GET", "POST"])
@admin_required
def index():

    if request.method == "POST":
        ldap_enabled = bool(request.form.get("ldap-enabled"))
        ldap_server = request.form.get("ldap-server")

        openid_enabled = bool(request.form.get("openid-enabled"))
        openid_client_id = request.form.get("openid-client-id")
        openid_client_secret = request.form.get("openid-client-secret")
        openid_metadata_url = request.form.get("openid-metadata-url")

        dbs.execute(db.update(Setting).values(
            ldap_enabled = ldap_enabled,
            ldap_server = ldap_server,

            openid_enabled = openid_enabled,
            openid_client_id = openid_client_id,
            openid_client_secret = openid_client_secret,
            openid_metadata_url = openid_metadata_url,
        ))
        dbs.commit()

        return redirect(url_for("settings.index"))

    settings = dbs.execute(db.select(Setting).limit(1)).scalar_one_or_none()
    return render_template('settings/index.html', settings=settings)

@bp.route("/ldap_retrieve", methods=["POST"])
@admin_required
def ldap_retrieve():
    ldap_enabled = Settings.get("ldap_enabled")

    if not ldap_enabled:
        return redirect(url_for("settings.index"))

    ldap_server = Settings.get("ldap_server")
    ldap_retrieve_users(ldap_server)
    
    return redirect(url_for("users.index"))