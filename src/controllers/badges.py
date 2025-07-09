from flask import Blueprint, redirect, render_template, request, url_for
from random import randbytes
from datetime import datetime

from src.models import db, dbs, Badge, User, Role
from src.auth import login_user, admin_required, logout_user, current_user

bp = Blueprint('badges', __name__, url_prefix="/badges")

@bp.route('/')
@admin_required
def index():
    user_id = request.args.get('user_id', type=int)
    is_active = request.args.get('is_active', '1')

    query = db.select(Badge, User.name, Role.name)
    if user_id:
        query = query.where(Badge.user_id == user_id)
    if is_active in ("0", "1"):
        query = query.where(Badge.is_active == is_active)
    
    query = query.join(User).join(Role)
    badges = db.session.execute(query).all()
    users = User.query.all()

    return render_template(
        'badges/index.html',
        badges=badges,
        users=users,
        user_id=user_id,
        is_active=is_active
    )


@bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        uid = request.form['uid']
        user_id = request.form['user_id']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        deactivation_date = request.form['deactivation_date'] or None
        guest_name = request.form['guest_name']
        company_name = request.form['company_name']
        role = request.form["role"]

        if deactivation_date:
            deactivation_date = datetime.strptime(deactivation_date, '%Y-%m-%d')

        db.session.add(Badge(
            uid=uid, 
            user_id=user_id, 
            is_active=is_active, 
            deactivation_date=deactivation_date,
            guest_name=guest_name,
            company_name=company_name,
            role=role
        ))

        try:
            db.session.commit()
        except:
            db.session.rollback()
            error = "Erreur lors de la création du badge, probablement une duplication de UID."
            users = User.query.all()
            return render_template('badges/add.html', users=users, error=error, uid=uid, user_id=user_id, is_active=is_active, deactivation_date=deactivation_date)
        
        return redirect(url_for('badges.index'))
    else:
        uid = randbytes(16).hex()
        users = User.query.all()
        roles = Role.query.all()
        return render_template('badges/add.html', users=users, roles=roles, uid=uid)

@bp.route('/edit/<int:badge_id>', methods=['GET', 'POST'])
@admin_required
def edit(badge_id):
    if request.method == 'POST':
        uid = request.form['uid']
        user_id = request.form['user_id']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        deactivation_date = request.form['deactivation_date'] or None
        guest_name = request.form['guest_name'] or None
        company_name = request.form['company_name'] or None
        role = request.form["role"]
        
        if deactivation_date:
            deactivation_date = datetime.strptime(deactivation_date, '%Y-%m-%d')
        
        dbs.execute(db.update(Badge).where(Badge.id == badge_id).values(uid=uid, user_id=user_id, is_active=is_active, deactivation_date=deactivation_date, role=role, guest_name=guest_name, company_name=company_name))
        dbs.commit()

        return redirect(url_for('badges.index'))
    else:
        badge = dbs.execute(db.select(Badge).where(Badge.id == badge_id)).scalar_one_or_none()
        users = User.query.all()
        roles = Role.query.all()
        return render_template('badges/edit.html', badge=badge, users=users, roles=roles)

@bp.route('/delete/<int:badge_id>', methods=['POST'])
@admin_required
def delete(badge_id):
    try:
        dbs.execute(db.delete(Badge).where(Badge.id == badge_id))
        dbs.commit()
        return redirect(url_for('badges.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500