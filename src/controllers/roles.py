from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Role, Reader, RoleReader
from src.auth import login_user, login_required, logout_user, current_user

bp = Blueprint('roles', __name__, url_prefix="/roles")

@bp.route('/')
@login_required
def index():
    roles = Role.query.all()
    return render_template('roles/index.html', roles=roles)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name:
            db.session.add(Role(name=name))
            db.session.commit()
        return redirect(url_for('roles.index'))
    return render_template('roles/add.html')

@bp.route('/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit(role_id):
    if request.method == 'POST':
        name = request.form['name']

        dbs.execute(db.update(Role).where(Role.id == role_id).values(name=name))
        dbs.commit()
        return redirect(url_for('roles.index'))
    else:
        role = dbs.execute(db.select(Role).where(Role.id == role_id)).scalar_one_or_none()
        return render_template('roles/edit.html', role=role)

@bp.route('/delete/<int:role_id>', methods=['POST'])
@login_required
def delete(role_id):
    try:
        dbs.execute(db.delete(Role).where(Role.id == role_id))
        dbs.commit()
        return redirect(url_for('roles.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500

@bp.route('/readers/<string:role>', methods=['GET', 'POST'])
@login_required
def readers(role):
    if request.method == 'POST':
        dbs.execute(db.delete(RoleReader).where(RoleReader.role == role))
        dbs.commit()
        
        selected_readers = request.form.getlist('readers')
        for reader_id in selected_readers:
            dbs.add(RoleReader(role=role, reader_id=reader_id))

        dbs.commit()
        return redirect(url_for('roles.index'))
    
    readers = Reader.query.all()
    allowed_readers = [r.reader_id for r in dbs.execute(db.select(RoleReader).where(RoleReader.role == role)).scalars().all()]
    
    return render_template('roles/readers.html', 
                         role=role, 
                         readers=readers, 
                         allowed_readers=allowed_readers)