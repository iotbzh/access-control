from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import func

from src.models import db, dbs, User, Badge, Role
from src.auth import login_user, admin_required, logout_user, current_user
from src.settings import Settings

bp = Blueprint('users', __name__, url_prefix="/users")

@bp.route('/')
@admin_required
def index():
    is_active = request.args.get('is_active', '1')

    query = db.select(User, func.count(Badge.id))
    if is_active in ("0", "1"):
        query = query.where(User.is_active == is_active)
    
    users = dbs.execute(query.outerjoin(Badge, Badge.user_id == User.id).group_by(User.id)).all()
    enable_add_user = Settings.get("enable_add_user")
    return render_template('users/index.html', is_active=is_active, users=users, enable_add_user=enable_add_user)

@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if not Settings.get("enable_add_user"):
        return "Disabled"

    if request.method == 'POST':
        uid = request.form["uid"]
        name = request.form['name']
        email = request.form["email"]
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        user = User(uid=uid, name=name, email=email, is_active=is_active)
        dbs.add(user)
        dbs.commit()
        
        return redirect(url_for('users.index'))
    else:
        return render_template('users/add.html')


@bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit(user_id):
    if request.method == 'POST':
        uid = request.form["uid"]
        name = request.form['name']
        email = request.form["email"]
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        dbs.execute(db.update(User).where(User.id == user_id).values(uid=uid, name=name, email=email, is_active=is_active))
        dbs.commit()
        return redirect(url_for('users.index'))
    else:
        user = dbs.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
        return render_template('users/edit.html', user=user)

@bp.route('/delete/<int:user_id>', methods=['POST'])
@admin_required
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
@admin_required
def badges(user_id):
    user_badges = dbs.execute(db.select(Badge, Role.name).where(Badge.user_id == user_id).join(Role)).all()
    user = dbs.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
    return render_template('users/badges.html', user=user, badges=user_badges)