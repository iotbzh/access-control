import sys
from datetime import datetime, timedelta
from src.models import db, dbs, Reader, Badge, User, RoleReader, Log, Role

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
    print(reader_instance)
    print(reader_instance.reader)
    print(reader_instance.reader.id)
    reader_id = reader_instance.reader.id
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    print(f"UID reçu : {badge_uid} pour le lecteur : {reader.name}")

    if not reader.is_active:
        log_access(reader.id, badge_uid, None, None, "denied", "Inactive Reader")
        print("Access refused. Inactive Reader.")
        gateway.event(reader_instance, False, badge_uid)
        return

    badge = dbs.execute(db.select(Badge).where(Badge.uid == badge_uid)).scalar_one_or_none()

    if not badge:
        log_access(reader.id, badge_uid, None, None, "denied", "Invalid Badge")
        print("Access refused. Invalid Badge.")
        gateway.event(reader_instance, False, badge_uid)
        return
    
    user = dbs.execute(db.select(User).where(User.id == badge.user_id)).scalar_one_or_none()

    if not user:
        log_access(reader.id, badge_uid, None, badge.user_id, "denied", "Badge not assigned")
        print("Access refused. Badge not assigned.")
        gateway.event(reader_instance, False, badge_uid)
        return

    now = datetime.now()
    now_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

    # DEBUG : Affiche le badge récupéré
    # print("Badge récupéré :", badge.uid)
    # print("Rôle de l'utilisateur :", badge.role)

    if not badge.is_active:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Inactive Badge")
        print("Access refused. Inactive Badge.")
        gateway.event(reader_instance, False, badge_uid)
        return
    elif badge.deactivation_date and badge.deactivation_date < now:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Expired badge")
        print("Access refused. Expired badge.")
        gateway.event(reader_instance, False, badge_uid)
        return
    elif not user.is_active:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Inactive user")
        print("Access refused. Inactive user.")
        gateway.event(reader_instance, False, badge_uid)
        return

    role = dbs.execute(db.select(Role).where(Role.id == badge.role)).scalar_one_or_none()
    access_start = convert_time_to_timedelta(role.access_start)
    access_end = convert_time_to_timedelta(role.access_end)
    weekday = datetime.now().weekday()

    if str(weekday) not in role.access_days:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access days")
        print("Access refused. Out of access days.")
        gateway.event(reader_instance, False, badge_uid)
        return

    if access_start is not None and access_end is not None:
        if not (access_start <= now_time <= access_end):
            log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access time")
            print("Access refused. Out of access time.")
            gateway.event(reader_instance, False, badge_uid)
            return
    elif access_start is not None:
        if now_time < access_start:
            log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access time")
            print("Access refused. Out of access time.")
            gateway.event(reader_instance, False, badge_uid)
            return
    elif access_end is not None:
        if now_time > access_end:
            log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access time")
            print("Access refused. Out of access time.")
            gateway.event(reader_instance, False, badge_uid)
            return

    print(dbs.execute(db.select(RoleReader).where(RoleReader.role == badge.role).where(RoleReader.reader_id == reader_id)).scalars().all())
    role_reader = dbs.execute(db.select(RoleReader).where(RoleReader.role == badge.role).where(RoleReader.reader_id == reader_id)).scalar_one_or_none()

    if not role_reader:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Unauthorized access")
        print("Access refused. Unauthorized access.")
        gateway.event(reader_instance, False, badge_uid)
        return

    log_access(reader.id, badge_uid, user.name, user.id, "authorized", "OK")
    print("Authorized...")
    gateway.event(reader_instance, True, badge_uid)
