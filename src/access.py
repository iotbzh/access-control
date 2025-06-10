import sys
import logging
from datetime import datetime, timedelta
from src.models import db, dbs, Reader, Badge, User, RoleReader, Log, Role
from src.logger import Logger

def log_access(reader_id, badge_uid, user_name, user_id, result, reason):
    try:
        dbs.add(Log(reader_id=reader_id, badge_uid=badge_uid, user_name=user_name, user_id=user_id, result=result, reason=reason))
        dbs.commit()
        Logger.get_app("access").info(f"[ {datetime.now()} ] {user_name} ({badge_uid}) {result} on reader {reader_id} ({reason})")
    except Exception as e:
        logging.error("Could not create log", exc_info=True)

def convert_time_to_timedelta(t):
    """Convertit un objet time ou timedelta en timedelta (ou None)."""
    if t is None:
        return None
    if isinstance(t, timedelta):
        return t
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

def access_control(gateway, reader_instance, badge_uid):
    reader_id = reader_instance.reader.id
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    logging.debug(f"UID reçu : {badge_uid} pour le lecteur : {reader.name}")

    if not reader.is_active:
        log_access(reader.id, badge_uid, None, None, "denied", "Inactive Reader")
        logging.debug("Access refused. Inactive Reader.")
        gateway.event(reader_instance, False, badge_uid)
        return False

    badge = dbs.execute(db.select(Badge).where(Badge.uid == badge_uid)).scalar_one_or_none()

    if not badge:
        log_access(reader.id, badge_uid, None, None, "denied", "Invalid Badge")
        logging.debug("Access refused. Invalid Badge.")
        gateway.event(reader_instance, False, badge_uid)
        return False
    
    user = dbs.execute(db.select(User).where(User.id == badge.user_id)).scalar_one_or_none()

    if not user:
        log_access(reader.id, badge_uid, None, badge.user_id, "denied", "Badge not assigned")
        logging.debug("Access refused. Badge not assigned.")
        gateway.event(reader_instance, False, badge_uid)
        return False

    now = datetime.now()
    now_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

    if not badge.is_active:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Inactive Badge")
        logging.debug("Access refused. Inactive Badge.")
        gateway.event(reader_instance, False, badge_uid)
        return False
    elif badge.deactivation_date and badge.deactivation_date < now:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Expired badge")
        logging.debug("Access refused. Expired badge.")
        gateway.event(reader_instance, False, badge_uid)
        return False
    elif not user.is_active:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Inactive user")
        logging.debug("Access refused. Inactive user.")
        gateway.event(reader_instance, False, badge_uid)
        return False

    role = dbs.execute(db.select(Role).where(Role.id == badge.role)).scalar_one_or_none()
    access_start = convert_time_to_timedelta(role.access_start)
    access_end = convert_time_to_timedelta(role.access_end)
    weekday = datetime.now().weekday()

    if str(weekday) not in role.access_days:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access days")
        logging.debug("Access refused. Out of access days.")
        gateway.event(reader_instance, False, badge_uid)
        return False

    if access_start is not None and access_end is not None:
        if not (access_start <= now_time <= access_end):
            log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access time")
            logging.debug("Access refused. Out of access time.")
            gateway.event(reader_instance, False, badge_uid)
            return False
    elif access_start is not None:
        if now_time < access_start:
            log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access time")
            logging.debug("Access refused. Out of access time.")
            gateway.event(reader_instance, False, badge_uid)
            return False
    elif access_end is not None:
        if now_time > access_end:
            log_access(reader.id, badge_uid, user.name, user.id, "denied", "Out of access time")
            logging.debug("Access refused. Out of access time.")
            gateway.event(reader_instance, False, badge_uid)
            return False

    logging.debug(dbs.execute(db.select(RoleReader).where(RoleReader.role == badge.role).where(RoleReader.reader_id == reader_id)).scalars().all())
    role_reader = dbs.execute(db.select(RoleReader).where(RoleReader.role == badge.role).where(RoleReader.reader_id == reader_id)).scalar_one_or_none()

    if not role_reader:
        log_access(reader.id, badge_uid, user.name, user.id, "denied", "Unauthorized access")
        logging.debug("Access refused. Unauthorized access.")
        gateway.event(reader_instance, False, badge_uid)
        return False

    log_access(reader.id, badge_uid, user.name, user.id, "authorized", "OK")
    logging.debug("Authorized...")
    gateway.event(reader_instance, True, badge_uid)
    return True