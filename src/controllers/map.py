from flask import Flask, redirect, url_for, session, Blueprint, render_template, request

from src.models import db, dbs, Reader
from src.auth import login_required, admin_required
from src.gateways import Gateways
from src.lib.gateway import BaseGateway

bp = Blueprint('map', __name__, url_prefix="/map")

@bp.route('/')
def index():
    readers_instance = BaseGateway.readers
    readers = Reader.query.all()
    return render_template('map/index.html', readers=readers, readers_instance=readers_instance)

@bp.route('/update', methods=['POST'])
@admin_required
def update():
    data = request.json
    for reader in data:
        dbs.execute(db.update(Reader).where(Reader.id == reader["id"]).values(pos_x = reader["x"], pos_y = reader["y"]))
    dbs.commit()
    return {}, 200

@bp.route('/open/<reader_id>', methods=['POST'])
@admin_required
def open(reader_id):
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    if not reader: return "Not found"
    gateway = Gateways.get(reader.gateway)
    reader_instance = gateway.get_reader_instance(reader.id)
    gateway.event(reader_instance, True, 0)
    return redirect(url_for("map.index"))

@bp.route('/restart/<reader_id>', methods=['POST'])
@admin_required
def restart(reader_id):
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    if not reader: return "Not found"
    gateway = Gateways.get(reader.gateway)
    reader_instance = gateway.get_reader_instance(reader.id)
    gateway.restart(reader_instance)
    return redirect(url_for("map.index"))

@bp.route("/actions/<reader_id>")
def actions(reader_id):
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    if not reader: return "Not found"
    gateway = Gateways.get(reader.gateway)
    actions = [ action for action in gateway.get_all_actions() if hasattr(action, "is_button_action") ]
    return render_template("map/actions.html", gateway_uid=gateway.uid, actions=actions, reader_id=reader_id)

@bp.route('/change', methods=['POST'])
@admin_required
def change():
    map_file = request.files.get('map_file')

    if not map_file:
        return "No map file"
    
    map_file.save("static/map.svg")
    return redirect(url_for("map.index"))