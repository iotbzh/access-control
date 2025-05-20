from flask import session, abort
from functools import wraps

def login_user(user):
    session["user"] = user["username"]

def login_required(func):
    def wrap(*args, **kwargs):
        if not current_user():
            abort(401)
        return func(*args, **kwargs)
    wrap.__name__ = func.__name__
    return wrap

def logout_user():
    session.pop("user")

def current_user():
    return session.get("user")