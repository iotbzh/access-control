import threading
import schedule
import time
import functools
import logging
from datetime import datetime, timedelta

from src.models import db, dbs, Log, Badge, User
from src.settings import Settings
from src.ldap import ldap_retrieve_users
from src.smtp import SMTP

app = None

# Decorator to have app context inside schedules
def app_schedule(func):
    def wrap(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)
    return wrap

# Decorator to catch potential execptions in scheduled tasks
def catch_exceptions(cancel_on_failure=False):
    def decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return decorator


def schedule_thread():
    logging.debug(f'schedule_thread - Start (pid {threading.get_native_id()})')
    while True:
        schedule.run_pending()
        time_to_next = schedule.idle_seconds()  # returns seconds until next job or None
        if time_to_next is None or time_to_next < 0:
            time_to_next = 10  # No jobs scheduled soon, sleep 10 sec
        time.sleep(time_to_next)


def init(_app):
    global app
    app = _app

    @app_schedule
    @catch_exceptions(cancel_on_failure=False)
    def ldap_retrieve_users_job():
        logging.info('Running Job: LDAP retrieve users')
        enabled = Settings.get("ldap_enabled")

        if not enabled:
            return

        ldap_retrieve_users()

    @app_schedule
    @catch_exceptions(cancel_on_failure=False)
    def rgpd_clean():
        # Delete every logs created 3 years ago
        logging.info('Running Job: Delete old logs')
        dbs.execute(db.delete(Log).where(Log.date_time > (datetime.now() + timedelta(days=1095))))
        dbs.commit()

    @app_schedule
    @catch_exceptions(cancel_on_failure=False)
    def badge_deactivation_job():
        logging.info('Running Job: Deactivate expired badges')
        badges = Badge.query.all()
        for badge in badges:
            # If badge is active and desactivation date is passed, disable the badge
            if badge.is_active and badge.deactivation_date and datetime.now() > badge.deactivation_date:
                # Send an email to the assigned user
                user = dbs.execute(db.select(User).where(User.id == badge.user_id)).scalar_one_or_none()

                logging.debug(f'Desactive badge user: {user}')
                if user:
                    SMTP.send_to([user.email], "[Access Control] Badge has been disabled", f"One of your badges has been automatically disabled.\n\n - UID: {badge.uid}\n - Guest Name: {badge.guest_name}\n - Company Name: {badge.company_name}")
                dbs.execute(db.update(Badge).where(Badge.id == badge.id).values(is_active=False))
        dbs.commit()

    schedule.every().days.do(rgpd_clean)
    schedule.every().days.do(ldap_retrieve_users_job)
    schedule.every().minutes.do(badge_deactivation_job)

    threading.Thread(target=schedule_thread, daemon=True).start()
