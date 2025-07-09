from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Setting
from src.auth import login_user, admin_required, logout_user, current_user
from src.settings import Settings
from src.ldap import ldap_retrieve_users
from src.smtp import SMTP

bp = Blueprint('settings', __name__, url_prefix="/settings")

@bp.route('/', methods=["GET", "POST"])
@admin_required
def index():

    if request.method == "POST":
        enable_add_user = bool(request.form.get("enable-add-user"))

        ldap_enabled = bool(request.form.get("ldap-enabled"))
        ldap_server = request.form.get("ldap-server")
        ldap_base = request.form.get("ldap-base")
        ldap_admin_filter = request.form.get("ldap-admin-filter")

        openid_enabled = bool(request.form.get("openid-enabled"))
        openid_client_id = request.form.get("openid-client-id")
        openid_client_secret = request.form.get("openid-client-secret")
        openid_metadata_url = request.form.get("openid-metadata-url")

        smtp_server = request.form.get("smtp-server")
        smtp_from_email = request.form.get("smtp-from-email")

        dbs.execute(db.update(Setting).values(
            enable_add_user=enable_add_user,

            ldap_enabled = ldap_enabled,
            ldap_server = ldap_server,
            ldap_base=ldap_base,
            ldap_admin_filter=ldap_admin_filter,

            openid_enabled = openid_enabled,
            openid_client_id = openid_client_id,
            openid_client_secret = openid_client_secret,
            openid_metadata_url = openid_metadata_url,

            smtp_server=smtp_server,
            smtp_from_email=smtp_from_email
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

    ldap_retrieve_users()
    
    return redirect(url_for("users.index"))

@bp.route("/test_email", methods=["POST"])
@admin_required
def test_email():
    to_email = request.form.get("to_email")
    SMTP.send_to([to_email], "Test Email", "Hello, this is a test email from the Access Control server!")
    return redirect(url_for("settings.index"))