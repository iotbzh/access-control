from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_mysqldb import MySQL
from flask_migrate import Migrate, upgrade
import MySQLdb
import threading
import time
import os
from flask_socketio import SocketIO
from sqlalchemy import create_engine, func, desc
from sqlalchemy_utils import database_exists, create_database

from src.models import db, dbs, User, Role, Badge, Reader, Log, Plugin
from src.auth import is_admin, login_user, login_required, logout_user, current_user, admin_required
from src.settings import Settings
from src.schedules import init as init_schedules
from src.smtp import SMTP
from src.gateways import Gateways
from src.plugins import Plugins
import src.socketio as socketio
import src.openid as openid
from src.lib.gateway import BaseGateway

from src.controllers.users import bp as users_controller
from src.controllers.badges import bp as badges_controller
from src.controllers.readers import bp as readers_controller
from src.controllers.roles import bp as roles_controller
from src.controllers.settings import bp as settings_controller
from src.controllers.gateways import bp as gateways_controller
from src.controllers.plugins import bp as plugins_controller
from src.controllers.openid import bp as openid_controller
from src.controllers.map import bp as map_controller
from src.controllers.actions import bp as actions_controller

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_and_secret_string"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI", "sqlite:///database.sqlite") #f'mysql://root:root@172.17.0.2/access_control'

Gateways.app = app
openid.app = app
socketio.sock = SocketIO(app)
sock = socketio.sock

app.register_blueprint(users_controller)
app.register_blueprint(badges_controller)
app.register_blueprint(readers_controller)
app.register_blueprint(roles_controller)
app.register_blueprint(settings_controller)
app.register_blueprint(gateways_controller)
app.register_blueprint(openid_controller)
app.register_blueprint(plugins_controller)
app.register_blueprint(map_controller)
app.register_blueprint(actions_controller)

db.init_app(app)
migrate = Migrate(app, db)

users_dict = {'admin': {
    "id": 0,
    "username": "admin",
    "password": "password",
    "ac_local": True
}}

def safe_url_for(endpoint, **values):
    try:
        return url_for(endpoint, **values)
    except:
        return None

app.jinja_env.globals['safe_url_for'] = safe_url_for

@app.context_processor
def inject_globals():
    return dict(is_admin=is_admin(current_user()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_dict.get(username)
        if user and user["password"] == password:  # Utilise un hash en prod !
            login_user(user)
            next_url = request.args.get("next", url_for("index"))
            return redirect(next_url)
        flash('Invalid username or password')

    if Settings.get("openid_enabled"):
        return redirect(url_for("openid.login"))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/zones_socketio')
@login_required
def zones_socketio():
    readers = Reader.query.all()
    return render_template('zones_socketio.html', readers=readers)

@app.route('/')
@login_required
def index():
    plugins = Plugin.query.all()
    return render_template('index.html', user=current_user, plugins=plugins)

@app.route('/logs/<reader_id>')
@admin_required
def reader_logs(reader_id):
    logs = dbs.execute(db.select(Log).where(Log.reader_id == reader_id).order_by(desc(Log.id)).limit(20)).scalars().all()
    return render_template('logs_modal.html', logs=logs)

@app.route('/logs')
@admin_required
def logs():
    per_page = int(request.args.get('per_page', 20))
    page = int(request.args.get('page', 1))
    offset = (page - 1) * per_page

    total_logs = db.session.execute(db.select(func.count()).select_from(Log)).one()[0]
    logs = db.session.execute(db.select(Log).offset(offset).limit(per_page).order_by(desc(Log.id))).scalars().all()

    total_pages = (total_logs + per_page - 1) // per_page

    return render_template(
        'logs.html',
        logs=logs,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_logs=total_logs
    )

@sock.on("updateReadersStatus")
@login_required
def on_update():
    readers_instance = BaseGateway.readers.values()
    status = {}
    for reader_instance in readers_instance:
        status[reader_instance.reader.id] = reader_instance.is_online
    sock.emit("readersStatus", status)

def startup():
    with app.app_context():
        upgrade()

        Gateways.init_all(app)
        Plugins.init_all(app)
        Settings.init()
        SMTP.init()

    init_schedules(app)

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        startup()
    sock.run(app, host="0.0.0.0", port=5000, debug=True)
else:
    print("[DEBUG] Running with an other Werkzeug server")