from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Gateway, Reader
from src.auth import login_required
from src.gateways import Gateways

bp = Blueprint('gateways', __name__, url_prefix="/gateways")

@bp.route('/')
@login_required
def index():
    gateways = Gateways.get_all_gateways()
    return render_template('gateways/index.html', gateways=gateways.values())

@bp.route('/<gateway_uid>', methods=["GET", "POST"])
@login_required
def view(gateway_uid):

    if request.method == "POST":
        gateway_interface = Gateways.gateways.get(gateway_uid)
        configs = {}

        for config in gateway_interface.configs:
            configs[config.name] = config.type(request.form.get(config.name))
        
        dbs.execute(db.update(Gateway).where(Gateway.uid == gateway_uid).values(configs=configs))
        dbs.commit()

    gateway_interface = Gateways.gateways.get(gateway_uid)
    gateway = dbs.execute(db.select(Gateway).where(Gateway.uid == gateway_uid)).scalar_one_or_none()

    if not gateway or not gateway_interface:
        return "Not found", 404
    
    readers = dbs.execute(db.select(Reader).where(Reader.gateway == gateway_uid)).scalars().all()
    return render_template("gateways/view.html", gateway=gateway, gateway_interface=gateway_interface, readers=readers)