from flask import Flask, redirect, url_for, session, Blueprint

from src.auth import login_user
from src.openid import get_oauth

bp = Blueprint('openid', __name__, url_prefix="/openid")

@bp.route('/login')
def login():
    oauth = get_oauth()
    redirect_uri = url_for('openid.auth', _external=True)
    return oauth.openid_app.authorize_redirect(redirect_uri)

@bp.route('/auth')
def auth():
    oauth = get_oauth()
    if not oauth: redirect(url_for("login"))
    token = oauth.openid_app.authorize_access_token()
    nonce = token.get("userinfo").get("nonce")
    user_info = oauth.openid_app.parse_id_token(token, nonce)
    login_user(user_info)
    return redirect(url_for('index'))
