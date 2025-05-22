# This file is awful, don't worry it will be fixed

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_mysqldb import MySQL
# from flask_login import LoginManager, UserMixin, 
from flask_migrate import Migrate
import MySQLdb
# import paho.mqtt.client as mqtt
# import paho.mqtt.publish as publish  # Utilise la même config que ton contrôleur
import threading
import time
import os
from flask_socketio import SocketIO
from sqlalchemy import create_engine, func
from sqlalchemy_utils import database_exists, create_database

from src.models import db, User, Role, Badge, Reader, Log
from src.auth import login_user, login_required, logout_user, current_user
from src.settings import Settings
from src.schedules import init as init_schedules
from src.smtp import SMTP
from src.gateways import Gateways
from src.plugins import Plugins
import src.socketio as socketio
import src.openid as openid

from src.controllers.users import bp as users_controller
from src.controllers.badges import bp as badges_controller
from src.controllers.readers import bp as readers_controller
from src.controllers.roles import bp as roles_controller
from src.controllers.settings import bp as settings_controller
from src.controllers.gateways import bp as gateways_controller
from src.controllers.plugins import bp as plugins_controller
from src.controllers.openid import bp as openid_controller

# --- Flask ---
app = Flask(__name__)
app.secret_key = "change_this_to_a_random_and_secret_string"
app.config["SQLALCHEMY_DATABASE_URI"] = f'mysql://root:root@172.17.0.2/access_control'

openid.app = app
socketio.sock = SocketIO(app)

app.register_blueprint(users_controller)
app.register_blueprint(badges_controller)
app.register_blueprint(readers_controller)
app.register_blueprint(roles_controller)
app.register_blueprint(settings_controller)
app.register_blueprint(gateways_controller)
app.register_blueprint(openid_controller)
app.register_blueprint(plugins_controller)

# TODO: Auto create database when not initialized
db.init_app(app)
migrate = Migrate(app, db)

# To migrate use "FLASK_MIGRATE=1 flask db migrate"
# To upgrade use "FLASK_MIGRATE=1 flask db upgrade"
if not os.getenv("FLASK_MIGRATE"):
    with app.app_context():
        Settings.init()
        SMTP.init()

    init_schedules(app)

# login_manager = LoginManager()
# login_manager.login_view = 'login'
# login_manager.init_app(app)

# Exemple simple d'utilisateur (remplace par ta BDD)
# class User(UserMixin):
#     def __init__(self, id, username, password):
#         self.id = id
#         self.username = username
#         self.password = password  # Stocke un hash en vrai

users_dict = {'admin': {
    "id": 0,
    "username": "admin",
    "password": "password"
}}

# @login_manager.user_loader
# def load_user(user_id):
#     for user in users_dict.values():
#         if user.id == int(user_id):
#             return user
#     return None

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
        flash('Identifiant ou mot de passe incorrect')

    if Settings.get("openid_enabled"):
        return redirect(url_for("openid.login"))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# MQTT_BROKER = "localhost"
# MQTT_PORT = 1883
# MQTT_USER = "utilisateur_mqtt"
# MQTT_PASS = "root"
# MQTT_TOPIC_STATUS = "lecteur/+/status"  # Wildcard pour tous les lecteurs

# Configuration MySQL
app.config['MYSQL_HOST'] = 'localhost'         # ou l’IP de ton serveur MySQL
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'controle_acces'

mysql = MySQL(app)

# --- Stockage du statut des lecteurs ---
lecteurs_status = {}  # ex: {'porte1': 'online', 'porte2': 'offline'}

# --- MQTT Callbacks ---
# def on_connect(client, userdata, flags, rc):
#     print("MQTT connected")
#     client.subscribe(MQTT_TOPIC_STATUS)

def on_message(client, userdata, msg):
    # topic = lecteur/porte1/status
    parts = msg.topic.split('/')
    if len(parts) == 3:
        lecteur = parts[1]
        status = msg.payload.decode()
        lecteurs_status[lecteur] = status
        # Diffuse à tous les clients connectés
        socketio.emit('status_update', {'lecteur': lecteur, 'status': status})

# def mqtt_thread():
#     client = mqtt.Client()
#     client.username_pw_set(MQTT_USER, MQTT_PASS)
#     client.on_connect = on_connect
#     client.on_message = on_message
#     client.connect(MQTT_BROKER, MQTT_PORT, 60)
#     client.loop_forever()

# --- Lancer MQTT en thread ---
# threading.Thread(target=mqtt_thread, daemon=True).start()

# --- Routes Flask ---
#@app.route('/zones_socketio')
#def index():
#    return render_template('zones_socketio.html', lecteurs=lecteurs_status)

# --- SocketIO event: envoyer le statut initial à la connexion ---
# @socketio.on('connect')
# def send_initial_status():
#     emit('all_status', lecteurs_status)

@app.route('/zones_socketio')
def zones_socketio():
    return render_template('zones_socketio.html', lecteurs=lecteurs_status)

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/plan')
@login_required
def plan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, pos_x, pos_y FROM access_zones")
    lecteurs = cur.fetchall()
    cur.close()
    # On passe aussi les statuts pour initialiser le plan
    return render_template('plan.html', lecteurs=lecteurs, lecteurs_status=lecteurs_status)

@app.route('/update_lecteur_positions', methods=['POST'])
@login_required
def update_lecteur_positions():
    data = request.get_json()
    cur = mysql.connection.cursor()
    for lecteur in data:
        cur.execute(
            "UPDATE access_zones SET pos_x=%s, pos_y=%s WHERE id=%s",
            (lecteur['x'], lecteur['y'], lecteur['id'])
        )
    mysql.connection.commit()
    cur.close()
    return jsonify(success=True)

@app.route('/historique/<zone_name>')
@login_required
def historique_lecteur(zone_name):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT l.date_time, l.user_name, l.result, l.reason
        FROM logs l
        JOIN access_zones z ON l.zone_id = z.id
        WHERE z.name = %s
        ORDER BY l.date_time DESC
        LIMIT 20
    """, (zone_name,))
    logs = cur.fetchall()
    cur.close()
    # Génère un mini-tableau HTML pour la modale
    return render_template('historique_modal.html', logs=logs, zone_name=zone_name)

@app.route('/logs')
@login_required
def logs():
    per_page = int(request.args.get('per_page', 20))
    page = int(request.args.get('page', 1))
    offset = (page - 1) * per_page

    total_logs = db.session.execute(db.select(func.count()).select_from(Log)).one()[0]
    logs = db.session.execute(db.select(Log).offset(offset).limit(per_page))

    total_pages = (total_logs + per_page - 1) // per_page

    return render_template(
        'logs.html',
        logs=logs,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_logs=total_logs
    )

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        with app.app_context():
            Gateways.init_all(app)
            Plugins.init_all(app)
    socketio.sock.run(app, host="0.0.0.0", port=5000, debug=True)
else:
    print("Running with an other Werkzeug server")