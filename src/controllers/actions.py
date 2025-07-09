from flask import Flask, redirect, url_for, session, Blueprint, render_template, request

from src.models import db, dbs, Reader
from src.auth import admin_required
from src.gateways import Gateways

bp = Blueprint('actions', __name__, url_prefix="/actions")

@bp.route("/<gateway_uid>/<action_name>", methods=["POST"])
def run(gateway_uid, action_name):
    gateway = Gateways.get(gateway_uid)
    action = gateway.get_action(action_name)
    if action.admin: action = admin_required(action)
    res = action(gateway, **request.args, **request.form)
    if res:
        return res
    return "OK"

@bp.route("/map/<gateway_uid>/<action_name>/<reader_id>", methods=["POST"])
def map(action_name, gateway_uid, reader_id):
    gateway = Gateways.get(gateway_uid)
    action = gateway.get_action(action_name)
    if action.admin: action = admin_required(action)
    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    res = action(gateway, reader, **request.args, **request.form)
    if res:
        return res
    return redirect(url_for("map.index"))