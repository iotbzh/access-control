from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, User, Role
from src.auth import login_user, login_required, logout_user, current_user

bp = Blueprint('users', __name__, url_prefix="/users")

@bp.route('/')
@login_required
def index():
    users = User.query.all()
    return render_template('users/index.html', users=users)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        user = User(name=name, role=role, is_active=is_active)
        dbs.add(user)
        dbs.commit()
        
        return redirect(url_for('users.index'))
    else:
        roles = Role.query.all()
        return render_template('users/add.html', roles=roles)


@bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit(user_id):
    if request.method == 'POST':
        name = request.form['name']
        role_id = request.form['role']
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        dbs.execute(db.update(User).where(User.id == user_id).values(name=name, role=role_id, is_active=is_active))
        dbs.commit()
        return redirect(url_for('users.index'))
    else:
        user = dbs.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
        roles = Role.query.all()
        return render_template('users/edit.html', user=user, roles=roles)

@bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete(user_id):
    try:
        # TODO: Check if cascade for user_zones is working
        dbs.execute(db.delete(User).where(User.id == user_id))
        dbs.commit()
        return redirect(url_for('users.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500