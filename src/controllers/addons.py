from flask import Blueprint, Response, redirect, render_template, request, url_for, current_app
from random import randbytes
from datetime import datetime

from src.models import db, dbs, Badge, User, Role, Addon
from src.auth import login_user, admin_required, logout_user, current_user
from src.gateways import Gateways
from src.plugins import Plugins
from src.addons import Addons

import os
import sys
import time
import threading

bp = Blueprint('addons', __name__, url_prefix="/addons")

# Restart the server when new gateways or plugins are added
# Needed to fix after start blueprint usage
def restart():
    def thread():
        time.sleep(1)
        # 
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    threading.Thread(target=thread).start()
    
    return "The server is restarting... You will be redirected in 5s<script>setTimeout(() => window.location.href = '/', 5000)</script>"

@bp.route('/')
@admin_required
def index():
    addons = dbs.execute(db.select(Addon)).scalars().all()
    return render_template('addons/index.html', addons=addons)

@bp.route('/import', methods=["GET", "POST"])
@admin_required
def import_():

    if request.method == "POST":
        git_url = request.form["git_url"]
        Addons.import_new(git_url, current_app)

        return restart()        

    return render_template('addons/import.html')

@bp.route('/update/<addon_uid>', methods=["POST"])
@admin_required
def update(addon_uid):
    Addons.update(addon_uid)
    return restart()

@bp.route('/delete/<addon_uid>', methods=['POST'])
@admin_required
def delete(addon_uid):
    Addons.remove(addon_uid)
    return redirect(url_for('addons.index'))