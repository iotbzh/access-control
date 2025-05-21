import sys
from datetime import datetime, timedelta
from src.models import db, dbs, Reader, Badge, User, RoleReader, Log

def log_access(reader_id, badge_uid, user_name, user_id, result, reason):
    try:
        dbs.add(Log(reader_id=reader_id, badge_uid=badge_uid, user_name=user_name, user_id=user_id, result=result, reason=reason))
        dbs.commit()
    except Exception as e:
        print("Erreur lors de la création du log :", e)

def convert_time_to_timedelta(t):
    """Convertit un objet time ou timedelta en timedelta (ou None)."""
    if t is None:
        return None
    if isinstance(t, timedelta):
        return t
    # Si c'est un time, convertit en timedelta
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

def access_control(gateway, reader_instance, badge_uid):
    reader_id = reader_instance.reader.id
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    print(f"UID reçu : {badge_uid} pour le lecteur : {reader.name}")

    if not reader.is_active:
        log_access(reader.id, badge_uid, None, None, "denied", "Lecteur désactivé")
        print("Accès refusé. Lecteur désactivé.")
        # REPLY TO GATEWAY
        return

    badge = dbs.execute(db.select(Badge).where(Badge.uid == badge_uid)).scalar_one_or_none()

    if not badge:
        log_access(reader.id, badge_uid, None, None, "denied", "Badge invalide")
        print("Accès refusé. Badge invalide.")
        # REPLY TO GATEWAY
        return
    
    user = dbs.execute(db.select(User).where(User.id == badge.user_id)).scalar_one_or_none()

    if not user:
        log_access(reader.id, badge_uid, None, badge.user_id, "denied", "Badge non assigné")
        print("Accès refusé. Badge non assigné.")
        # REPLY TO GATEWAY
        return

    now = datetime.now()
    now_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

    # DEBUG : Affiche le badge récupéré
    print("Badge récupéré :", badge.uid)
    print("Rôle de l'utilisateur :", user.role)

    if not badge.is_active:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Badge désactivé")
        print("Accès refusé. Badge désactivé.")
        # REPLY TO GATEWAY
        return
    elif badge.deactivation_date and badge.deactivation_date < now:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Badge expiré")
        print("Accès refusé. Badge expiré.")
        # REPLY TO GATEWAY
        return
    elif not user.is_active:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Utilisateur désactivé")
        print("Accès refusé. Utilisateur désactivé.")
        # REPLY TO GATEWAY
        return

    # -------
    # A faire, mettre les horraire sur le role et pas le user/badge
    # ------- 
    # access_start = convert_time_to_timedelta(badge['access_start'])
    # access_end = convert_time_to_timedelta(badge['access_end'])
    # access_granted = True

    # if access_start is not None and access_end is not None:
    #     if not (access_start <= now_time <= access_end):
    #         log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Hors plage horaire")
    #         print("Accès refusé. Hors plage horaire.")
    #         client.publish(MQTT_TOPIC_LED, "NO")
    #         return
    # elif access_start is not None:
    #     if now_time < access_start:
    #         log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Accès pas encore ouvert")
    #         print("Accès refusé. Accès pas encore ouvert.")
    #         client.publish(MQTT_TOPIC_LED, "NO")
    #         return
    # elif access_end is not None:
    #     if now_time > access_end:
    #         log_access(uid, badge['badge_id'], badge['user_id'], user_name, zone_id, "denied", "Accès terminé")
    #         print("Accès refusé. Accès terminé.")
    #         client.publish(MQTT_TOPIC_LED, "NO")
    #         return

    role_reader = dbs.execute(db.select(RoleReader).where(RoleReader.role == user.role)).scalar_one_or_none()

    if not role_reader:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Zone non autorisée")
        print("Accès refusé. Zone non autorisée.")
        # REPLY TO GATEWAY
        return

    log_access(reader.id, badge_uid, user.name, user.id, "authorized", "OK")
    print("Accès autorisé, ouverture...")
    # REPLY TO GATEWAY  
