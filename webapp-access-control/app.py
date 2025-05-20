from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_mysqldb import MySQL
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import MySQLdb
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish  # Utilise la même config que ton contrôleur
import threading
import time

# --- Flask ---
app = Flask(__name__)
app.secret_key = "change_this_to_a_random_and_secret_string"

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Exemple simple d'utilisateur (remplace par ta BDD)
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password  # Stocke un hash en vrai

users_dict = {'admin': User(1, 'admin', 'password')}

@login_manager.user_loader
def load_user(user_id):
    for user in users_dict.values():
        if user.id == int(user_id):
            return user
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_dict.get(username)
        if user and user.password == password:  # Utilise un hash en prod !
            login_user(user)
            return redirect(url_for('home'))
        flash('Identifiant ou mot de passe incorrect')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

socketio = SocketIO(app)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "utilisateur_mqtt"
MQTT_PASS = "root"
MQTT_TOPIC_STATUS = "lecteur/+/status"  # Wildcard pour tous les lecteurs

# Configuration MySQL
app.config['MYSQL_HOST'] = 'localhost'         # ou l’IP de ton serveur MySQL
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'controle_acces'

mysql = MySQL(app)

# --- Stockage du statut des lecteurs ---
lecteurs_status = {}  # ex: {'porte1': 'online', 'porte2': 'offline'}

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    print("MQTT connected")
    client.subscribe(MQTT_TOPIC_STATUS)

def on_message(client, userdata, msg):
    # topic = lecteur/porte1/status
    parts = msg.topic.split('/')
    if len(parts) == 3:
        lecteur = parts[1]
        status = msg.payload.decode()
        lecteurs_status[lecteur] = status
        # Diffuse à tous les clients connectés
        socketio.emit('status_update', {'lecteur': lecteur, 'status': status})

def mqtt_thread():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# --- Lancer MQTT en thread ---
threading.Thread(target=mqtt_thread, daemon=True).start()

# --- Routes Flask ---
#@app.route('/zones_socketio')
#def index():
#    return render_template('zones_socketio.html', lecteurs=lecteurs_status)

# --- SocketIO event: envoyer le statut initial à la connexion ---
@socketio.on('connect')
def send_initial_status():
    emit('all_status', lecteurs_status)

@app.route('/zones_socketio')
def zones_socketio():
    return render_template('zones_socketio.html', lecteurs=lecteurs_status)

@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

@app.route('/users')
@login_required
def users():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id, u.name, r.name as role_name, u.access_start, u.access_end, u.is_active, u.created_at
        FROM users u
        LEFT JOIN roles r ON u.role = r.id
        ORDER BY u.id
    """)
    users = cur.fetchall()
    cur.close()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        access_start = request.form['access_start'] or None
        access_end = request.form['access_end'] or None
        cur.execute(
            "INSERT INTO users (name, role, is_active, access_start, access_end) VALUES (%s, %s, %s, %s, %s)",
            (name, role, is_active, access_start, access_end)
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('users'))
    else:
        cur.execute("SELECT id, name FROM roles ORDER BY name")
        roles = cur.fetchall()
        cur.close()
        return render_template('add_user.html', roles=roles)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        # Récupérer les nouvelles valeurs du formulaire
        name = request.form['name']
        role_id = request.form['role']  # On récupère l'id du rôle
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        access_start = request.form['access_start'] or None
        access_end = request.form['access_end'] or None
        # Mettre à jour l'utilisateur
        cur.execute("""
            UPDATE users
            SET name=%s, role=%s, access_start=%s, access_end=%s, is_active=%s
            WHERE id=%s
        """, (name, role_id, access_start, access_end, is_active, user_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('users'))  # Redirige vers la liste des utilisateurs
    else:
        # Afficher le formulaire pré-rempli
        cur.execute("SELECT id, name, role, access_start, access_end, is_active FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        # Récupérer la liste des rôles
        cur.execute("SELECT id, name FROM roles ORDER BY name")
        roles = cur.fetchall()
        cur.close()
        return render_template('edit_user.html', user=user, roles=roles)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    cur = mysql.connection.cursor()
    try:
        # Supprimer les liens dans user_zones si nécessaire
        cur.execute("DELETE FROM user_zones WHERE user_id = %s", (user_id,))
        # Supprimer l'utilisateur
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        return redirect(url_for('users'))
    except Exception as e:
        mysql.connection.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500
    finally:
        cur.close()

@app.route('/badges')
@login_required
def badges():
    cur = mysql.connection.cursor()
    user_id = request.args.get('user_id', type=int)
    is_active = request.args.get('is_active')  # "1", "0" ou None

    sql = """
        SELECT b.id, b.uid, u.name as user_name, b.is_active, b.deactivation_date
        FROM badges b
        LEFT JOIN users u ON b.user_id = u.id
        WHERE 1=1
    """
    params = []
    if user_id:
        sql += " AND u.id = %s"
        params.append(user_id)
    if is_active in ("0", "1"):
        sql += " AND b.is_active = %s"
        params.append(is_active)

    cur.execute(sql, params)
    badges_raw = cur.fetchall()

    # Pour la liste déroulante des utilisateurs
    cur.execute("SELECT id, name FROM users ORDER BY name")
    users_raw = cur.fetchall()
    cur.close()

    # On transforme les tuples en dictionnaires pour le template
    badges = [
        {
            'id': row[0],
            'uid': row[1],
            'user_name': row[2],
            'is_active': row[3],
            'deactivation_date': row[4]
        }
        for row in badges_raw
    ]
    users = [
        {'id': row[0], 'name': row[1]}
        for row in users_raw
    ]

    return render_template(
        'badges.html',
        badges=badges,
        users=users,
        user_id=user_id,
        is_active=is_active
    )


@app.route('/add_badge', methods=['GET', 'POST'])
@login_required
def add_badge():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        uid = request.form['uid']
        user_id = request.form['user_id']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        deactivation_date = request.form['deactivation_date'] or None

        # Vérification unicité UID
        cur.execute("SELECT COUNT(*) FROM badges WHERE uid = %s", (uid,))
        (count,) = cur.fetchone()
        if count > 0:
            # UID déjà existant, afficher un message d’erreur
            cur.execute("SELECT id, name FROM users WHERE is_active=1")
            users = cur.fetchall()
            cur.close()
            error = "Ce badge (UID) existe déjà dans la base."
            return render_template('add_badge.html', users=users, error=error, uid=uid, user_id=user_id, is_active=is_active, deactivation_date=deactivation_date)

        # Sinon, insertion normale
        cur.execute(
            "INSERT INTO badges (uid, user_id, is_active, deactivation_date) VALUES (%s, %s, %s, %s)",
            (uid, user_id, is_active, deactivation_date)
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('badges'))
    else:
        cur.execute("SELECT id, name FROM users WHERE is_active=1")
        users = cur.fetchall()
        cur.close()
        return render_template('add_badge.html', users=users)

# Modifier un badge
@app.route('/edit_badge/<int:badge_id>', methods=['GET', 'POST'])
@login_required
def edit_badge(badge_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        uid = request.form['uid']
        user_id = request.form['user_id']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        deactivation_date = request.form['deactivation_date'] or None
        cur.execute("UPDATE badges SET uid=%s, user_id=%s, is_active=%s, deactivation_date=%s WHERE id=%s",
                    (uid, user_id, is_active, deactivation_date, badge_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('badges'))
    else:
        cur.execute("SELECT id, uid, user_id, autorise, deactivation_date, is_active FROM badges WHERE id=%s", (badge_id,))
        badge = cur.fetchone()
        cur.execute("SELECT id, name FROM users WHERE is_active=1")
        users = cur.fetchall()
        cur.close()
        return render_template('edit_badge.html', badge=badge, users=users)

# Supprimer un badge
@app.route('/delete_badge/<int:badge_id>', methods=['POST'])
@login_required
def delete_badge(badge_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM badges WHERE id=%s", (badge_id,))
        mysql.connection.commit()
        return redirect(url_for('badges'))
    except Exception as e:
        mysql.connection.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500
    finally:
        cur.close()

# Liste des rôles
@app.route('/roles')
@login_required
def roles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM roles ORDER BY name")
    roles = cur.fetchall()
    cur.close()
    return render_template('roles.html', roles=roles)

# Création d’un rôle
@app.route('/add_role', methods=['GET', 'POST'])
@login_required
def add_role():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name:
            cur = mysql.connection.cursor()
            cur.execute("INSERT IGNORE INTO roles (name) VALUES (%s)", (name,))
            mysql.connection.commit()
            cur.close()
        return redirect(url_for('roles'))
    return render_template('add_role.html')

# Modification d’un rôle
@app.route('/edit_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name'].strip()
        cur.execute("UPDATE roles SET name=%s WHERE id=%s", (name, role_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('roles'))
    else:
        cur.execute("SELECT id, name FROM roles WHERE id=%s", (role_id,))
        role = cur.fetchone()
        cur.close()
        return render_template('edit_role.html', role=role)

# Suppression d’un rôle
@app.route('/delete_role/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM roles WHERE id=%s", (role_id,))
        mysql.connection.commit()
        return redirect(url_for('roles'))
    except Exception as e:
        mysql.connection.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500
    finally:
        cur.close()

@app.route('/edit_role_zones/<string:role>', methods=['GET', 'POST'])
@login_required
def edit_role_zones(role):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        # Supprime les anciennes associations
        cur.execute("DELETE FROM role_zones WHERE role=%s", (role,))
        # Ajoute les nouvelles sélections
        selected_zones = request.form.getlist('zones')
        for zone_id in selected_zones:
            cur.execute("INSERT INTO role_zones (role, zone_id) VALUES (%s, %s)", (role, zone_id))
        mysql.connection.commit()
        return redirect(url_for('roles'))
    
    # Récupère toutes les zones et celles accessibles au rôle
    cur.execute("SELECT id, name FROM access_zones")
    all_zones = cur.fetchall()
    cur.execute("SELECT zone_id FROM role_zones WHERE role=%s", (role,))
    allowed_zones = {row[0] for row in cur.fetchall()}
    cur.close()
    
    return render_template('edit_role_zones.html', 
                         role=role, 
                         zones=all_zones, 
                         allowed_zones=allowed_zones)

def get_lecteur_status(zone_name):
    status = {'value': 'offline'}
    topic = f'lecteur/{zone_name}/status'

    def on_message(client, userdata, msg):
        status['value'] = msg.payload.decode()

    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic)
    client.loop_start()
    time.sleep(0.3)  # Attendre la réception du message retained
    client.loop_stop()
    client.disconnect()
    return status['value']

# Liste des lecteurs de portes (access_zones)
@app.route('/zones')
@login_required
def zones():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, description, is_active FROM access_zones ORDER BY name")
    zones = cur.fetchall()
    cur.close()
    # Récupère le statut pour chaque zone
    zones_with_status = []
    for zone in zones:
        status = get_lecteur_status(zone[1])
        zones_with_status.append({
            'id': zone[0],
            'name': zone[1],
            'description': zone[2],
            'is_active': zone[3],
            'status': status
        })
    return render_template('zones.html', zones=zones_with_status)


# Ajouter un lecteur de porte
@app.route('/add_zone', methods=['GET', 'POST'])
@login_required
def add_zone():
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO access_zones (name, description, is_active) VALUES (%s, %s, %s)",
                (name, description, is_active)
            )
            mysql.connection.commit()
            return redirect(url_for('zones'))
        except MySQLdb.IntegrityError as err:
            mysql.connection.rollback()
            flash(f"Erreur : {err}", 'danger')
        finally:
            cur.close()

    return render_template('add_zone.html')


# Modifier un lecteur de porte
@app.route('/edit_zone/<int:zone_id>', methods=['GET', 'POST'])
@login_required
def edit_zone(zone_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        try:
            cur.execute(
                "UPDATE access_zones SET name=%s, description=%s, is_active=%s WHERE id=%s",
                (name, description, is_active, zone_id)
            )
            mysql.connection.commit()
            return redirect(url_for('zones'))
        except MySQLdb.IntegrityError as err:
            mysql.connection.rollback()
            flash(f"Erreur : {err}", 'danger')
            # Recharge la zone pour réafficher le formulaire avec les valeurs actuelles
            cur.execute("SELECT id, name, description, is_active FROM access_zones WHERE id=%s", (zone_id,))
            zone = cur.fetchone()
            cur.close()
            return render_template('edit_zone.html', zone=zone)
        finally:
            cur.close()
    else:
        cur.execute("SELECT id, name, description, is_active FROM access_zones WHERE id=%s", (zone_id,))
        zone = cur.fetchone()
        cur.close()
        return render_template('edit_zone.html', zone=zone)

@app.route('/zones/<zone_name>/open', methods=['POST'])
@login_required
def open_zone(zone_name):
    topic_cmd = f"controle_acces/{zone_name}/commande"
    topic_led = f"controle_acces/{zone_name}/led"
    try:
        auth = {'username': MQTT_USER, 'password': MQTT_PASS}
        publish.multiple([
            {'topic': topic_cmd, 'payload': "ON"},
            {'topic': topic_led, 'payload': "OK"}
        ], hostname=MQTT_BROKER, port=MQTT_PORT, auth=auth)
        # Récupère l'ID de la zone
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM access_zones WHERE name=%s", (zone_name,))
        row = cur.fetchone()
        zone_id = row[0] if row else None

        # Enregistre le log comme les autres opérations
        if zone_id is not None:
            cur.execute("""
                INSERT INTO logs (uid, badge_id, user_id, user_name, zone_id, result, reason, date_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                None,  # uid
                None,  # badge_id
                current_user.id,
                current_user.username,
                zone_id,
                "authorized",
                "Ouverture via webapp"
            ))
            mysql.connection.commit()
        else:
            app.logger.warning(f"Zone '{zone_name}' introuvable pour le log.")
        cur.close()
        flash(f"Porte '{zone_name}' ouverte et LED verte allumée.", "success")
    except Exception as e:
        flash(f"Erreur lors de l'ouverture : {e}", "danger")
    app.logger.info("Ouverture manuelle de la porte '%s' via webapp par '%s'", zone_name, current_user.username)
    return redirect(url_for('zones'))


# Supprimer un lecteur de porte
@app.route('/delete_zone/<int:zone_id>', methods=['POST'])
@login_required
def delete_zone(zone_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM access_zones WHERE id=%s", (zone_id,))
        mysql.connection.commit()
    except mysql.connector.Error as err:
        mysql.connection.rollback()
        flash(f"Erreur : {err}", 'danger')
    finally:
        cur.close()
    return redirect(url_for('zones'))

def check_access(user_role, zone_id):
    if user_role == 'admin':
        return True  # Les admins ont tout accès
    cur = mysql.connection.cursor()
    cur.execute("SELECT 1 FROM role_zones WHERE role=%s AND zone_id=%s", (user_role, zone_id))
    result = cur.fetchone()
    cur.close()
    return result is not None

@app.route('/open_door/<int:door_id>')
@login_required
def open_door(door_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
    user_role = cur.fetchone()[0]
    
    if check_access(user_role, door_id):
        # Code pour déclencher l'ouverture physique
        log_access(session['user_id'], door_id, "granted")
        return "Porte ouverte !"
    else:
        log_access(session['user_id'], door_id, "denied")
        return "Accès refusé", 403

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

    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM logs")
    total_logs = cur.fetchone()[0]

    cur.execute("""
        SELECT id, uid, date_time, result, zone_id, reason, badge_id, user_name, user_id
        FROM logs
        ORDER BY date_time DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    logs = cur.fetchall()
    cur.close()

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
    app.run(debug=True)
    socketio.run(app, host='0.0.0.0', port=5000)
