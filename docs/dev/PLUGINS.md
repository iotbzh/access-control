# Developper Documentation - Plugins

## Basic Usage

Here's the code to create a Hello World plugin

`plugins/hello/__init__.py`
```py
from flask import Blueprint
from src.lib.plugin import BasePlugin

class Plugin(BasePlugin):
    uid = "hello"
    bp = Blueprint('hello', __name__, url_prefix="/hello", template_folder="..")

bp = Plugin.bp

@bp.route('/')
def index():
    return "Hello World!"
```

## Protected routes

You can protect routes so only "logged" or "admin" users can view it.

`plugins/hello/__init__.py`
```py
from src.auth import login_required, admin_required

...

@bp.route('/everyone')
def everyone():
    return "Everyone can see this route"

@bp.route('/logged')
@login_required
def logged():
    return "Only logged users can see this route"

@bp.route('/admin')
@admin_required
def admin():
    return "Only admins can see this route"
```

## Plugin configuration

This will create a string variable that can be configured on the webui at `/plugins/hello`

`plugins/hello/__init__.py`
```py
class Plugin(BasePlugin):
    ...
    class Config:
        message: str = "Hello World!"

@bp.route('/')
def index():
    return Plugin.get_var("message")
```

## Links in navbar

To add links in the navbar, you can use the `navlinks` attribute

`plugins/hello/__init__.py`
```py
class Plugin(BasePlugin):
    ...
    navlinks = {
        "Hello", "/hello"
    }
```