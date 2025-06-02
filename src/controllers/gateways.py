from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Gateway, Reader
from src.auth import admin_required
from src.gateways import Gateways

bp = Blueprint('gateways', __name__, url_prefix="/gateways")

@bp.route('/')
@admin_required
def index():
    gateways = Gateways.get_all_gateways()
    return render_template('gateways/index.html', gateways=gateways.values())

@bp.route('/<gateway_uid>', methods=["GET", "POST"])
@admin_required
def view(gateway_uid):

    if request.method == "POST":
        gateway = Gateways.gateways.get(gateway_uid)
        gateway_annotations = gateway.Config.__annotations__
        configs = {}

        for config in gateway_annotations:
            configs[config] = gateway_annotations[config](request.form.get(config))
        
        dbs.execute(db.update(Gateway).where(Gateway.uid == gateway_uid).values(configs=configs))
        dbs.commit()

        readers = dbs.execute(db.select(Reader).where(Reader.gateway == gateway.uid)).scalars().all()

        for reader in readers:
            if gateway.readers.get(reader.id):
                gateway.restart(gateway.readers.get(reader.id))
        
        return redirect(url_for("gateways.index"))

    gateway_annotations = Gateways.gateways.get(gateway_uid).Config.__annotations__
    gateway = dbs.execute(db.select(Gateway).where(Gateway.uid == gateway_uid)).scalar_one_or_none()

    if not gateway or gateway_annotations == None:
        return "Not found", 404
    
    readers = dbs.execute(db.select(Reader).where(Reader.gateway == gateway_uid)).scalars().all()
    return render_template("gateways/view.html", gateway=gateway, gateway_annotations=gateway_annotations, readers=readers)