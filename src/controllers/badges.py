from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Badge, User, Role
from src.auth import login_user, login_required, logout_user, current_user

bp = Blueprint('badges', __name__, url_prefix="/badges")

@bp.route('/')
@login_required
def index():
    user_id = request.args.get('user_id', type=int)
    is_active = request.args.get('is_active')  # "1", "0" ou None

    query = db.select(Badge)
    if user_id:
        query = query.where(Badge.user_id == user_id)
    if is_active in ("0", "1"):
        query = query.where(Badge.is_active == is_active)

    badges = db.session.execute(query).scalars().all()
    users = User.query.all()

    return render_template(
        'badges/index.html',
        badges=badges,
        users=users,
        user_id=user_id,
        is_active=is_active
    )


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        uid = request.form['uid']
        user_id = request.form['user_id']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        deactivation_date = request.form['deactivation_date'] or None
        guest_name = request.form['guest_name']
        company_name = request.form['company_name']
        role = request.form["role"]

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
        users = User.query.all()
        roles = Role.query.all()
        return render_template('badges/add.html', users=users, roles=roles)

@bp.route('/edit/<int:badge_id>', methods=['GET', 'POST'])
@login_required
def edit(badge_id):
    if request.method == 'POST':
        uid = request.form['uid']
        user_id = request.form['user_id']
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        deactivation_date = request.form['deactivation_date'] or None
        role = request.form["role"]
        
        dbs.execute(db.update(Badge).where(Badge.id == badge_id).values(uid=uid, user_id=user_id, is_active=is_active, deactivation_date=deactivation_date, role=role))
        dbs.commit()

        return redirect(url_for('badges.index'))
    else:
        badge = dbs.execute(db.select(Badge).where(Badge.id == badge_id)).scalar_one_or_none()
        users = User.query.all()
        roles = Role.query.all()
        return render_template('badges/edit.html', badge=badge, users=users, roles=roles)

@bp.route('/delete/<int:badge_id>', methods=['POST'])
@login_required
def delete(badge_id):
    try:
        dbs.execute(db.delete(Badge).where(Badge.id == badge_id))
        dbs.commit()
        return redirect(url_for('badges.index'))
    except Exception as e:
        dbs.rollback()
        return f"Erreur lors de la suppression : {str(e)}", 500