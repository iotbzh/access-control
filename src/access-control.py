# -*- coding: utf-8 -*-
import sys
import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime, timedelta

# --- CONFIGURATION ---

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "utilisateur_mqtt"
MQTT_PASS = "root"
MQTT_TOPIC_UID = "controle_acces/+/uid"  # Wildcard pour toutes les portes

# MySQL
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASS = "root"
MYSQL_DB   = "controle_acces"

# --- FIN CONFIGURATION ---

# Nom de la zone/porte (argument ou valeur par défaut)
ZONE_NAME = sys.argv[1] if len(sys.argv) > 1 else "porte1"
STATUS_TOPIC = f"lecteur/{ZONE_NAME}/status"

# Connexion à la base MySQL
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASS,
    database=MYSQL_DB,
    charset='utf8mb4'
)
cursor = db.cursor(dictionary=True)

def get_zone_info(zone_name):
    cursor.execute("SELECT id, is_active FROM access_zones WHERE name=%s", (zone_name,))
    return cursor.fetchone()  # dict: {'id': ..., 'is_active': ...}

def log_access(uid, badge_id, user_id, user_name, zone_id, resultat, raison):
    try:
        cursor.execute(
            "INSERT INTO logs (uid, badge_id, user_id, user_name, zone_id, result, reason, date_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
            (uid, badge_id, user_id, user_name, zone_id, resultat, raison)
        )
        db.commit()
    except Exception as e:
        print("Erreur lors de la création du log :", e, flush=True)

def convert_time_to_timedelta(t):
    """Convertit un objet time ou timedelta en timedelta (ou None)."""
    if t is None:
        return None
    if isinstance(t, timedelta):
        return t
    # Si c'est un time, convertit en timedelta
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

def on_message(client, userdata, message):
    uid = message.payload.decode().strip()
    topic_parts = message.topic.split('/')
    if len(topic_parts) < 3:
        print("Topic inattendu :", message.topic, flush=True)
        return
    zone_name = topic_parts[1]
    print(f"UID reçu : {uid} pour la zone : {zone_name}", flush=True)

    zone_info = get_zone_info(zone_name)
    if not zone_info:
        print(f"Zone '{zone_name}' inconnue.", flush=True)
        return

    zone_id = zone_info['id']
    zone_active = zone_info['is_active']

    MQTT_TOPIC_CMD = f"controle_acces/{zone_name}/commande"
    MQTT_TOPIC_LED = f"controle_acces/{zone_name}/led"

    # --- Vérification : lecteur activé ? ---
    if not zone_active:
        log_access(uid, None, None, None, zone_id, "denied", "Lecteur désactivé")
        print("Accès refusé. Lecteur désactivé.", flush=True)
        client.publish(MQTT_TOPIC_LED, "NO")
        return

    # --- Recherche du badge ---
    cursor.execute("""
    SELECT b.id AS badge_id, b.is_active AS badge_active, b.deactivation_date,
           u.id AS user_id, u.name AS user_name, u.is_active AS user_active, 
           r.name AS role_name, u.access_start, u.access_end,
           (SELECT COUNT(*) FROM role_zones rz WHERE rz.role = r.name AND rz.zone_id = %s) AS zone_authorized
    FROM badges b
    JOIN users u ON b.user_id = u.id
    JOIN roles r ON u.role = r.id
    WHERE b.uid = %s
    LIMIT 1
    """, (zone_id, uid))
    badge = cursor.fetchone()

    now = datetime.now()
    now_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

    # --- Cas Badge inconnu ---
    if not badge:
        user_name = None
        log_access(uid, None, None, user_name, zone_id, "denied", "Badge inconnu")
        print("Badge inconnu.", flush=True)
        client.publish(MQTT_TOPIC_LED, "NO")
        return

    # DEBUG : Affiche le badge récupéré
    print("Badge récupéré :", badge, flush=True)
    print("Rôle de l'utilisateur :", badge['role_name'], flush=True)
    print("Zone autorisée (role_zones) :", badge['zone_authorized'], flush=True)

    user_name = badge['user_name']

    # --- Vérifications avancées ---
    if not badge['badge_active']:
        log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Badge désactivé")
        print("Accès refusé. Badge désactivé.", flush=True)
        client.publish(MQTT_TOPIC_LED, "NO")
        return
    elif badge['deactivation_date'] and badge['deactivation_date'] < now:
        log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Badge expiré")
        print("Accès refusé. Badge expiré.", flush=True)
        client.publish(MQTT_TOPIC_LED, "NO")
        return
    elif not badge['user_active']:
        log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Utilisateur désactivé")
        print("Accès refusé. Utilisateur désactivé.", flush=True)
        client.publish(MQTT_TOPIC_LED, "NO")
        return

    # --- Vérification horaire (améliorée) ---
    access_start = convert_time_to_timedelta(badge['access_start'])
    access_end = convert_time_to_timedelta(badge['access_end'])
    access_granted = True

    if access_start is not None and access_end is not None:
        if not (access_start <= now_time <= access_end):
            log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Hors plage horaire")
            print("Accès refusé. Hors plage horaire.", flush=True)
            client.publish(MQTT_TOPIC_LED, "NO")
            return
    elif access_start is not None:
        if now_time < access_start:
            log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Accès pas encore ouvert")
            print("Accès refusé. Accès pas encore ouvert.", flush=True)
            client.publish(MQTT_TOPIC_LED, "NO")
            return
    elif access_end is not None:
        if now_time > access_end:
            log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Accès terminé")
            print("Accès refusé. Accès terminé.", flush=True)
            client.publish(MQTT_TOPIC_LED, "NO")
            return

    # --- Vérification de la zone (sauf admin) ---
    if badge['role_name'] == 'admin':
        print("C'est un admin, accès autorisé partout.", flush=True)
    if badge['role_name'] != 'admin' and badge['zone_authorized'] == 0:
        print("Condition refus : rôle =", badge['role_name'], "zone_authorized =", badge['zone_authorized'], flush=True)
        log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Zone non autorisée")
        print("Accès refusé. Zone non autorisée.", flush=True)
        client.publish(MQTT_TOPIC_LED, "NO")
        return

    # --- Accès autorisé ---
    log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "authorized", "OK")
    print("Accès autorisé, ouverture...", flush=True)
    client.publish(MQTT_TOPIC_CMD, "ON")
    client.publish(MQTT_TOPIC_LED, "OK")

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connecté au broker MQTT", flush=True)
    client.subscribe(MQTT_TOPIC_UID)
    print(f"Abonnement au topic {MQTT_TOPIC_UID}", flush=True)
    # Dès connexion, publie online (important si reconnexion)
    client.publish(STATUS_TOPIC, payload='online', retain=True)

client = mqtt.Client(client_id=f"lecteur-{ZONE_NAME}", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.will_set(STATUS_TOPIC, payload='offline', retain=True)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("Contrôleur prêt, en attente d'UIDs pour toutes les portes...", flush=True)
client.publish(STATUS_TOPIC, payload='online', retain=True)  # Première publication
client.loop_forever()