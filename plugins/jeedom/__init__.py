from flask import Blueprint, redirect, render_template, request, url_for, current_app
from datetime import datetime, timedelta
import requests
import schedule
import urllib3
import time

from src.auth import login_required
from src.socketio import sock
from src.configs import Configs
from src.lib.plugin import BasePlugin
from src.smtp import SMTP
from src.schedules import app_schedule
from src.models import db, dbs, Reader, Log, User

from gateways.cn56 import Gateway

urllib3.disable_warnings()

class Plugin(BasePlugin):
    uid = "jeedom"
    bp = Blueprint('jeedom', __name__, url_prefix="/jeedom", template_folder="..")
    
    class Config:
        shutters_open_api: str = "http://localhost:5001/open"
        shutters_close_api: str = "http://localhost:5001/close"
        shutters_status_api: str = "http://localhost:5001/state"
        front_door_status_api: str = "http://localhost:5001/fd_state"
        lab_door_status_api: str = "http://localhost:5001/ld_state"
        bike_door_status_api: str = "http://localhost:5001/bd_state"
        seconds_before_mail: int = 30

bp = Plugin.bp

class Element:

    def __init__(self, id, api_var_name):
        self.id = id
        self.api_var_name = api_var_name
    
    def get_api(self):
        return Plugin.get_var(self.api_var_name)

class Door(Element):

    def __init__(self, id, api_var_name):
        super().__init__(id, api_var_name)
        self.opened_time = 0
        self.alerts = 0

    def get_to_addresses(self, closed=False):
        skipail = "alex.zalo+skipail@iot.bzh" # skipail@iot.bzh
        if self.alerts >= (3 - int(closed)):
            return [skipail]
        else:
            emails = dbs.execute(db.select(User.email).join(Log).where(Log.date_time > datetime.now() - timedelta(hours=8)).group_by(User.email)).scalars().all() # TODO: Fix Timedelta doesnt work, getting everything
            return emails

doors = [
    Door("front_door", "front_door_status_api"),
    Door("lab_door", "lab_door_status_api"),
    Door("bike_door", "bike_door_status_api")
]
elements = [
    Element("shutters", "shutters_status_api")
] + doors

doors[0].get_to_addresses()

def get_status(api_url):
    return False if requests.get(api_url, verify=False).text == "0" else True

def get_all_status():
    all_status = {}
    for element in elements:
        all_status[element.id] = get_status(element.get_api())
    return all_status

def get_closed_doors():
    closed_doors = {}
    for door in doors:
        closed_doors[door] = get_status(door.get_api())
    return closed_doors

def toggle_shutters():
    status = get_status("shutters_status_api")
    url = Plugin.get_var(f"shutters_{'close' if status else 'open'}_api")
    requests.get(url, verify=False)

@bp.route('/')
@login_required
def index():
    return render_template('jeedom/index.html')

@sock.on("update")
@login_required
def on_update():
    sock.emit("data", get_all_status())

@sock.on("toggleShutters")
@login_required
def on_toggle_shutters():
    toggle_shutters()

@app_schedule
def check_doors():
    closed_doors = get_closed_doors()
    for door in doors:
        if not closed_doors[door]:
            if door.opened_time == 0:
                door.opened_time = time.time()
            
            now = time.time()
            delta = now - door.opened_time
            if delta >= Plugin.get_var("seconds_before_mail") * (door.alerts + 1):
                door.alerts += 1
                display_name = door.id.capitalize().replace("_", " ")
                SMTP.send_to(
                    door.get_to_addresses(), 
                    f"[DoorStatus] {display_name} has been opened for about {delta // 60:.0f} minutes", 
                    f"{display_name} has been open for about {delta // 60:.0f} minutes.\n\nPlease close it if you are near."
                )

            reader = dbs.execute(db.select(Reader).where(Reader.name == door.id)).scalar_one_or_none()
            if reader:
                reader_instance = Gateway.get_reader_instance(reader.id)
                reader_instance.opened_door_buzzer()

            print(f"Door have when opened for {delta}s")
        else:
            if door.opened_time != 0:
                if door.alerts >= 1:
                    now = time.time()
                    delta = now - door.opened_time
                    display_name = door.id.capitalize().replace("_", " ")
                    SMTP.send_to(
                        door.get_to_addresses(True), 
                        f"[DoorStatus] {display_name} is closed!", 
                        f"Lab door has been opened for about {delta // 60:.0f} minutes.\n\nNow it's closed."
                    )
                    door.alerts = 0
                door.opened_time = 0

schedule.every(1).seconds.do(check_doors)