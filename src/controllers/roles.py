from flask import Blueprint, redirect, render_template, request, url_for
from datetime import datetime

from src.models import db, dbs, Role, Reader, RoleReader
from src.auth import login_user, admin_required, logout_user, current_user

bp = Blueprint('roles', __name__, url_prefix="/roles")

@bp.route('/')
@admin_required
def index():
    is_active = request.args.get('is_active', '1')

    query = db.select(Role)
    if is_active in ("0", "1"):
        query = query.where(Role.is_active == is_active)
    
    roles = dbs.execute(query).scalars().all()
    return render_template('roles/index.html', roles=roles)

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        name = request.form['name'].strip()
        access_start = request.form['access_start'] or None
        access_end = request.form['access_end'] or None
        access_days = "".join(request.form.getlist("access_days"))
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        if access_start:
            access_start = datetime.strptime(access_start, '%H:%M').time()
        if access_end:
            access_end = datetime.strptime(access_end, '%H:%M').time()

        if name:
            db.session.add(Role(name=name, access_start=access_start, access_end=access_end, access_days=access_days, is_active=is_active))
            db.session.commit()
        return redirect(url_for('roles.index'))
    return render_template('roles/add.html')

@bp.route('/edit/<int:role_id>', methods=['GET', 'POST'])
@admin_required
def edit(role_id):
    if request.method == 'POST':
        name = request.form['name']
        access_start = request.form['access_start'] or None
        access_end = request.form['access_end'] or None
        access_days = "".join(request.form.getlist("access_days"))
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        if access_start:
            access_start = datetime.strptime(
                access_start[:-3] if len(access_start.split(":")) > 2 else access_start, 
            '%H:%M').time()
        if access_end:
            access_end = datetime.strptime(
                access_end[:-3] if len(access_end.split(":")) > 2 else access_end, 
            '%H:%M').time()

        dbs.execute(db.update(Role).where(Role.id == role_id).values(name=name, access_start=access_start, access_end=access_end, access_days=access_days, is_active=is_active))
        dbs.commit()
        return redirect(url_for('roles.index'))
    else:
        role = dbs.execute(db.select(Role).where(Role.id == role_id)).scalar_one_or_none()
        return render_template('roles/edit.html', role=role)

@bp.route('/delete/<int:role_id>', methods=['POST'])
@admin_required
def delete(role_id):
    try:
        dbs.execute(db.delete(Role).where(Role.id == role_id))
        dbs.commit()
        return redirect(url_for('roles.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500

@bp.route('/readers/<string:role_id>', methods=['GET', 'POST'])
@admin_required
def readers(role_id):
    if request.method == 'POST':
        dbs.execute(db.delete(RoleReader).where(RoleReader.role == role_id))
        dbs.commit()
        
        selected_readers = request.form.getlist('readers')
        for reader_id in selected_readers:
            dbs.add(RoleReader(role=role_id, reader_id=reader_id))

        dbs.commit()
        return redirect(url_for('roles.index'))
    
    readers = Reader.query.all()
    allowed_readers = [r.reader_id for r in dbs.execute(db.select(RoleReader).where(RoleReader.role == role_id)).scalars().all()]
    role = dbs.execute(db.select(Role).where(Role.id == role_id)).scalar_one_or_none()
    
    return render_template('roles/readers.html', 
                         role=role, 
                         readers=readers, 
                         allowed_readers=allowed_readers)