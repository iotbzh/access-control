from flask import Blueprint, redirect, render_template, request, url_for, current_app
import requests
import schedule
import urllib3

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

urllib3.disable_warnings()

bp = Plugin.bp
closed_doors = {}
doors_opened_time = { # Switch to datetime to keep acurate delta times
    "front_door": 0,
    "lab_door": 0,
    "bike_door": 0,
}
time_before_mail = 30

def get_status(var):
    return False if requests.get(Plugin.get_var(var), verify=False).text == "0" else True

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
    global closed_doors
    elements = {
        "front_door": "front_door_status_api",
        "lab_door": "lab_door_status_api",
        "bike_door": "bike_door_status_api",
    }
    for element in elements:
        closed_doors[element] = get_status(elements[element])

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
    for door in closed_doors:
        if not closed_doors[door]:
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

schedule.every(1).seconds.do(doors)