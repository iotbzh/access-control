from flask import Blueprint, redirect, render_template, request, url_for, flash, current_app

from src.models import db, dbs, Badge, User, Reader, Gateway
from src.auth import login_user, admin_required, logout_user, current_user
from src.gateways import Gateways
from src.lib.gateway import BaseGateway

bp = Blueprint('readers', __name__, url_prefix="/readers")

def get_reader_status(zone_name):
    return "online"

@bp.route('/')
@admin_required
def index():
    readers = Reader.query.all()
    return render_template('readers/index.html', readers=readers, readers_instance=BaseGateway.readers)

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        gateway = request.form.get("gateway")

        gateway_interface = Gateways.gateways.get(gateway)
        gateway_reader_configs = gateway_interface.reader_class.__annotations__
        gateway_configs = {}

        for config in gateway_reader_configs:
            gateway_configs[config] = getattr(gateway_interface.reader_class, config, None)

        try:
            reader = Reader(name=name, description=description, is_active=is_active, gateway=gateway, gateway_configs=gateway_configs)
            dbs.add(reader)
            dbs.commit()

            gateway_interface = Gateways.gateways.get(gateway)
            Gateways.init_reader(current_app, gateway_interface, reader)
            
            return redirect(url_for('readers.index'))
        except Exception as err:
            dbs.rollback()
            flash(f"Erreur : {err}", 'danger')

    gateways = Gateway.query.all()
    return render_template('readers/add.html', gateways=gateways)

@bp.route('/edit/<int:reader_id>', methods=['GET', 'POST'])
@admin_required
def edit(reader_id):    
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        gateway = request.form.get("gateway")
        gateway_interface = Gateways.gateways.get(gateway)

        gateway_reader_configs = gateway_interface.reader_class.__annotations__
        gateway_configs = {}

        for config in gateway_reader_configs:
            gateway_configs[config] = gateway_reader_configs[config](request.form.get("gateway-" + config))

        dbs.execute(db.update(Reader).where(Reader.id == reader_id).values(name=name, description=description, is_active=is_active, gateway=gateway, gateway_configs=gateway_configs))
        dbs.commit()

        reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
        Gateways.init_reader(current_app, gateway_interface, reader)

        return redirect(url_for('readers.index'))

    reader = dbs.execute(db.select(Reader).where(Reader.id == reader_id)).scalar_one_or_none()
    gateways = Gateway.query.all()
    reader_annotations = Gateways.gateways.get(reader.gateway).reader_class.__annotations__
    return render_template('readers/edit.html', reader=reader, gateways=gateways, reader_annotations=reader_annotations)

@bp.route('/delete/<int:reader_id>', methods=['POST'])
@admin_required
def delete(reader_id):
    try:
        if reader_id in BaseGateway.readers:
            del BaseGateway.readers[reader_id]
        dbs.execute(db.delete(Reader).where(Reader.id == reader_id))
        dbs.commit()
        return redirect(url_for('readers.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500