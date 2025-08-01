from flask import Flask, Response, send_file, render_template, request, redirect, url_for, flash, jsonify, current_app, sessions
from flask_migrate import Migrate, upgrade
import os
from flask_socketio import SocketIO
from sqlalchemy import func, desc
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime

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
from src.lib.reader import BaseReader
from src.access import access_control
from src.addons import Addons

# Import all controllers
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
from src.controllers.addons import bp as addons_controller

# Init logger after all logger init from external modules
from src.logger import Logger
Logger.init()

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI", "sqlite:///database.sqlite")

# Add references to app
Gateways.app = app
Plugins.app = app
openid.app = app

socketio.sock = SocketIO(app)
sock = socketio.sock

dev_mode = bool(os.getenv("DEV", False))

# Import all controllers
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
app.register_blueprint(addons_controller)

db.init_app(app)
migrate = Migrate(app, db)

# A safe url_for to not crash when route not found
def safe_url_for(endpoint, **values):
    try:
        return url_for(endpoint, **values)
    except:
        return None

# Make the safe_url_for function available inside templates
app.jinja_env.globals['safe_url_for'] = safe_url_for

# With app context add global variables for templates
@app.context_processor
def inject_globals():
    plugin_instances = Plugins.plugins
    return {
        "is_admin": is_admin(current_user()), 
        "is_logged": bool(current_user()),
        "plugin_instances": plugin_instances,
        "dev_mode": dev_mode
    }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and os.getenv("ADMIN_PASSWORD") == password:
            login_user({
                "username": "admin",
                "ac_local": True
            })
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
    return redirect(url_for('index'))

@app.route('/status')
def status():
    readers = Reader.query.all()
    return render_template('status.html', readers=readers)

@app.route('/')
def index():
    plugins = Plugin.query.all()
    return render_template('index.html', user=current_user, plugins=plugins, current_app=current_app)

# TODO: Move to logs controller
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
    logs = db.session.execute(db.select(Log, Reader.name).join(Reader).offset(offset).limit(per_page).order_by(desc(Log.id))).all()

    total_pages = (total_logs + per_page - 1) // per_page

    return render_template(
        'logs.html',
        logs=logs,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_logs=total_logs
    )

@app.route("/logs/export")
def logs_export():
    logs = dbs.execute(db.select(Log, User).join(User, isouter=True)).all()
    formated_logs = []
    for log, user in logs:
        formated_logs.append(f"[ {log.date_time} ] {user.name if user else '-'} {log.guest or ''} ({log.badge_uid}) {log.result} on reader {log.reader_id} ({log.reason})".encode())
    return  send_file(
        BytesIO(b"\n".join(formated_logs)), 
        as_attachment=True,
        download_name=f'access-logs_{datetime.now().strftime("%d-%m-%Y")}.txt',
        mimetype='text/txt'
    )

# This route if for tests
@app.route("/tests/access/<gateway_uid>/<reader_id>/<badge_uid>")
def tests_access(gateway_uid, reader_id, badge_uid):
    gateway = Gateways.get(gateway_uid)
    reader_instance = gateway.get_reader_instance(reader_id)
    return str(access_control(gateway, reader_instance, badge_uid))

@sock.on("updateReadersStatus")
def on_update():
    readers_instance = BaseGateway.readers.values()
    status = {}
    for reader_instance in readers_instance:
        status[reader_instance.reader.id] = reader_instance.is_online
    sock.emit("readersStatus", status)

def startup():
    with app.app_context():
        upgrade()

        Logger.init_app("access")

        Gateways.init_all()
        Plugins.init_all()
        Settings.init()

    init_schedules(app)

def main():
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # This will run once
        startup()
    elif not dev_mode:
        startup()
    sock.run(app, host="0.0.0.0", port=5000, debug=dev_mode)

if __name__ == '__main__':
    main()