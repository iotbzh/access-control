from flask import session, redirect, url_for, request
from functools import wraps
from src.ldap import ldap_is_admin
from src.settings import Settings

def login_user(user):
    enabled = Settings.get("ldap_enabled")
    if enabled:
        email = user.get("email")
        server = Settings.get("ldap_server")
        if ldap_is_admin(server, email):
            user["admin"] = True

    session["user"] = user

def login_required(func):
    def wrap(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login", next=request.path))
        return func(*args, **kwargs)
    wrap.__name__ = func.__name__
    return wrap

def admin_required(func):
    def wrap(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login", next=request.path))
        
        user = current_user()
        if is_admin(user):
            return func(*args, **kwargs)
        
        return redirect(url_for("index"))
    wrap.__name__ = func.__name__
    return wrap

def is_admin(user):
    if not user:
        return False
    if user.get("ac_local"):
        return True
    if user.get("admin") == True:
        return True
    return False

def logout_user():
    session.pop("user")

def current_user():
    return session.get("user")