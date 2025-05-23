import threading
import schedule
import time
from datetime import datetime

from src.models import db, dbs, User, Badge
from src.settings import Settings
from src.ldap import ldap_retrieve_users

app = None

def app_schedule(func):
    def wrap(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)
    return wrap

def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

def init(_app):
    global app
    app = _app

    @app_schedule
    def ldap_retrieve_users_job():
        enabled = Settings.get("ldap_enabled")

        if not enabled:
            return
        
        server = Settings.get("ldap_server")
        ldap_retrieve_users(server)

    @app_schedule
    def badge_deactivation_job():
        badges = Badge.query.all()
        for badge in badges:
            if badge.is_active and badge.deactivation_date and datetime.now() > badge.deactivation_date:
                dbs.execute(db.update(Badge).where(Badge.id == badge.id).values(is_active=False))
        dbs.commit()

    schedule.every().days.do(ldap_retrieve_users_job)
    schedule.every().minutes.do(badge_deactivation_job)

    threading.Thread(target=schedule_thread, daemon=True).start()