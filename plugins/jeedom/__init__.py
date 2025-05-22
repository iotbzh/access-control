from flask import Blueprint, redirect, render_template, request, url_for, current_app
import requests
import schedule

from src.auth import login_required
from src.socketio import sock
from src.configs import Configs
from src.lib.plugin import BasePlugin
from src.smtp import SMTP
from src.schedules import app_schedule

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

bp = Plugin.bp
doors_status = {}
doors_opened_time = {
    "front_door": 0,
    "lab_door": 0,
    "bike_door": 0,
}
time_before_mail = 30
update_interval = 3

if time_before_mail % update_interval != 0:
    print("!!! WARNING !!!")
    print(r"time_before_mail % update_interval should be equal to 0")
    print("The mail warning will not work")
    print("!!! WARNING !!!")

def get_status(var):
    return bool(requests.get(Plugin.get_var(var)).json().get("data"))

def get_all_status():
    all_status = {}
    elements = {
        "shutters": "shutters_status_api",
        "front_door": "front_door_status_api",
        "lab_door": "lab_door_status_api",
        "bike_door": "bike_door_status_api",
    }
    for element in elements:
        all_status[element] = get_status(elements[element])
    return all_status

def update_doors_status():
    global doors_status
    elements = {
        "front_door": "front_door_status_api",
        "lab_door": "lab_door_status_api",
        "bike_door": "bike_door_status_api",
    }
    for element in elements:
        doors_status[element] = get_status(elements[element])

def toggle_shutters():
    status = get_status("shutters_status_api")
    url = Plugin.get_var(f"shutters_{'close' if status else 'open'}_api")
    requests.get(url)

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
def doors():
    update_doors_status()
    for door in doors_status:
        if doors_status[door]:
            doors_opened_time[door] += 5
            print(f"Door have when opened for {doors_opened_time[door]}s")
            if doors_opened_time[door] % time_before_mail == 0:
                display_name = door.capitalize().replace("_", " ")
                SMTP.send_to(
                    "alex.zalo@iot.bzh", 
                    f"[DoorStatus] {display_name} has been opened for about {doors_opened_time[door] // 60} minutes", 
                    f"{display_name} has been open for about {doors_opened_time[door] // 60} minutes.\n\nPlease close it if you are near."
                )
        else:
            if doors_opened_time[door] != 0:
                if doors_opened_time[door] >= time_before_mail:
                    display_name = door.capitalize().replace("_", " ")
                    SMTP.send_to(
                        "alex.zalo@iot.bzh", 
                        f"[DoorStatus] {display_name} is closed!", 
                        f"Lab door has been opened for about {doors_opened_time[door] // 60} minutes.\n\nNow it's closed."
                    )
                doors_opened_time[door] = 0

schedule.every(5).seconds.do(doors)