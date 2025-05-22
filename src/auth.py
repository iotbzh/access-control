from flask import session, redirect, url_for, request
from functools import wraps

def login_user(user):
    session["user"] = user

def login_required(func):
    def wrap(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login", next=request.path))
        return func(*args, **kwargs)
    wrap.__name__ = func.__name__
    return wrap

def logout_user():
    session.pop("user")

def current_user():
    return session.get("user")