from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time

db = SQLAlchemy()
dbs = db.session

class Reader(db.Model):
    __tablename__ = 'readers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    pos_x = db.Column(db.Integer, default=100)
    pos_y = db.Column(db.Integer, default=100)

    logs = db.relationship('Log', backref='zone', lazy=True)
    role_readers = db.relationship('RoleReader', backref='zone', lazy=True)
    # user_zones = db.relationship('UserZone', backref='zone', lazy=True)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    users = db.relationship('User', backref='role_rel', lazy=True)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    badges = db.relationship('Badge', backref='user', lazy=True)
    # user_zones = db.relationship('UserZone', backref='user', lazy=True)


class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    autorise = db.Column(db.Boolean, default=True)
    deactivation_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)


class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(32))
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(16))
    reader_id = db.Column(db.Integer, db.ForeignKey('readers.id'))
    reason = db.Column(db.String(255))
    badge_id = db.Column(db.Integer)
    user_name = db.Column(db.String(100))
    user_id = db.Column(db.Integer)


class RoleReader(db.Model):
    __tablename__ = 'role_readers'

    role = db.Column(db.String(50), primary_key=True)
    reader_id = db.Column(db.Integer, db.ForeignKey('readers.id'), primary_key=True)


# class UserZone(db.Model):
#     __tablename__ = 'user_zones'

#     user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
#     zone_id = db.Column(db.Integer, db.ForeignKey('access_zones.id', ondelete='CASCADE'), primary_key=True)

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    ldap_enabled = db.Column(db.Boolean, default=False)
    ldap_server = db.Column(db.String(255))
    ldap_default_role = db.Column(db.Integer, default=0)