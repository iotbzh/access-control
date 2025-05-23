from flask import Blueprint, redirect, render_template, request, url_for, current_app
import requests
import schedule
import urllib3
import time

from src.auth import login_required, admin_required
from src.socketio import sock
from src.configs import Configs
from src.lib.plugin import BasePlugin
from src.smtp import SMTP
from src.schedules import app_schedule
from src.models import db, dbs, Reader, Badge

class Plugin(BasePlugin):
    uid = "cn56"
    bp = Blueprint('cn56', __name__, url_prefix="/cn56", template_folder="..")
    
    class Config:
        shutters_open_api: str = "http://localhost:5001/open"
        shutters_close_api: str = "http://localhost:5001/close"
        shutters_status_api: str = "http://localhost:5001/state"
        front_door_status_api: str = "http://localhost:5001/fd_state"
        lab_door_status_api: str = "http://localhost:5001/ld_state"
        bike_door_status_api: str = "http://localhost:5001/bd_state"

bp = Plugin.bp

@bp.route("/write/<reader_id>")
@admin_required
def write(reader_id):
    badges = Badge.query.all()
    return render_template("cn56/write.html", reader_id=reader_id, badges=badges)