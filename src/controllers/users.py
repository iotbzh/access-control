from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, User, Badge
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
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        user = User(name=name, is_active=is_active)
        dbs.add(user)
        dbs.commit()
        
        return redirect(url_for('users.index'))
    else:
        return render_template('users/add.html')


@bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit(user_id):
    if request.method == 'POST':
        name = request.form['name']
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        dbs.execute(db.update(User).where(User.id == user_id).values(name=name, is_active=is_active))
        dbs.commit()
        return redirect(url_for('users.index'))
    else:
        user = dbs.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
        return render_template('users/edit.html', user=user)

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
    
@bp.route("/badges/<int:user_id>")
@login_required
def badges(user_id):
    user_badges = dbs.execute(db.select(Badge).where(Badge.user_id == user_id)).scalars().all()
    return str(user_badges)