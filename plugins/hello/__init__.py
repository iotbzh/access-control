from flask import Blueprint
from src.lib.plugin import BasePlugin

class Plugin(BasePlugin):
    uid = "hello"
    bp = Blueprint('hello', __name__, url_prefix="/hello", template_folder="..")

    class Config:
        message: str = "Hello World!"

bp = Plugin.bp

@bp.route('/')
def index():
    return Plugin.get_var("message")