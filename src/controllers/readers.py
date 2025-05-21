from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Badge, User, Reader, Gateway
from src.auth import login_user, login_required, logout_user, current_user
from src.gateways import Gateways

bp = Blueprint('readers', __name__, url_prefix="/readers")

def get_reader_status(zone_name):
    return "online"

@bp.route('/')
@login_required
def index():
    readers = Reader.query.all()
    status = []
    for reader in readers:
        status.append(get_reader_status(reader.id))
    return render_template('readers/index.html', readers=readers, status=status)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        gateway = request.form.get("gateway")

        try:
            db.session.add(Reader(name=name, description=description, is_active=is_active, gateway=gateway))
            db.session.commit()
            return redirect(url_for('readers.index'))
        except Exception as err:
            db.session.rollback()
            flash(f"Erreur : {err}", 'danger')

    gateways = Gateway.query.all()
    return render_template('readers/add.html', gateways=gateways)

@bp.route('/edit/<int:reader_id>', methods=['GET', 'POST'])
@login_required
def edit(reader_id):    
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        gateway = request.form.get("gateway")
        gateway_interface = Gateways.gateways.get(gateway)

        gateway_reader_configs = gateway_interface.reader_class.__annotations__
        gateway_configs = {}

        for config in gateway_reader_configs:
            gateway_configs[config] = gateway_reader_configs[config](request.form.get("gateway-" + config))

        dbs.execute(db.update(Reader).where(Reader.id == reader_id).values(name=name, description=description, is_active=is_active, gateway=gateway, gateway_configs=gateway_configs))
        dbs.commit()
        return redirect(url_for('readers.index'))

    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    gateways = Gateway.query.all()
    reader_interface = Gateways.gateways.get(reader.gateway).reader_class.__annotations__
    return render_template('readers/edit.html', reader=reader, gateways=gateways, reader_interface=reader_interface)

@bp.route('/delete/<int:reader_id>', methods=['POST'])
@login_required
def delete(reader_id):
    try:
        dbs.execute(db.delete(Reader).where(Reader.id == reader_id))
        dbs.commit()
        return redirect(url_for('readers.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500


# @bp.route('/<reader_name>/open', methods=['POST'])
# @login_required
# def open(reader_name):
#     topic_cmd = f"controle_acces/{zone_name}/commande"
#     topic_led = f"controle_acces/{zone_name}/led"
#     try:
#         auth = {'username': MQTT_USER, 'password': MQTT_PASS}
#         publish.multiple([
#             {'topic': topic_cmd, 'payload': "ON"},
#             {'topic': topic_led, 'payload': "OK"}
#         ], hostname=MQTT_BROKER, port=MQTT_PORT, auth=auth)
#         # Récupère l'ID de la zone
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT id FROM access_zones WHERE name=%s", (zone_name,))
#         row = cur.fetchone()
#         zone_id = row[0] if row else None

#         # Enregistre le log comme les autres opérations
#         if zone_id is not None:
#             cur.execute("""
#                 INSERT INTO logs (uid, badge_id, user_id, user_name, zone_id, result, reason, date_time)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
#             """, (
#                 None,  # uid
#                 None,  # badge_id
#                 current_user.id,
#                 current_user.username,
#                 zone_id,
#                 "authorized",
#                 "Ouverture via webapp"
#             ))
#             mysql.connection.commit()
#         else:
#             app.logger.warning(f"Zone '{zone_name}' introuvable pour le log.")
#         cur.close()
#         flash(f"Porte '{zone_name}' ouverte et LED verte allumée.", "success")
#     except Exception as e:
#         flash(f"Erreur lors de l'ouverture : {e}", "danger")
#     app.logger.info("Ouverture manuelle de la porte '%s' via webapp par '%s'", zone_name, current_user.username)
#     return redirect(url_for('zones'))


# def check_access(user_role, zone_id):
#     if user_role == 'admin':
#         return True  # Les admins ont tout accès
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT 1 FROM role_zones WHERE role=%s AND zone_id=%s", (user_role, zone_id))
#     result = cur.fetchone()
#     cur.close()
#     return result is not None

# @bp.route('/open_door/<int:door_id>')
# @login_required
# def open_door(door_id):
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
#     user_role = cur.fetchone()[0]
    
#     if check_access(user_role, door_id):
#         # Code pour déclencher l'ouverture physique
#         log_access(session['user_id'], door_id, "granted")
#         return "Porte ouverte !"
#     else:
#         log_access(session['user_id'], door_id, "denied")
#         return "Accès refusé", 403