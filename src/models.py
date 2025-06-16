from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
from sqlalchemy import MetaData

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

dbs = db.session

class Reader(db.Model):
    __tablename__ = 'readers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    pos_x = db.Column(db.Integer, default=100)
    pos_y = db.Column(db.Integer, default=100)
    gateway = db.Column(db.String(64))
    gateway_configs = db.Column(db.JSON)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    access_start = db.Column(db.Time)
    access_end = db.Column(db.Time)
    access_days = db.Column(db.String(7), default="")


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    deactivation_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    guest_name = db.Column(db.String(64))
    company_name = db.Column(db.String(64))
    role = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)


class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, default=datetime.now)
    reader_id = db.Column(db.Integer, db.ForeignKey('readers.id'))
    badge_uid = db.Column(db.String(32))
    user_name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    guest = db.Column(db.String(128))
    result = db.Column(db.String(16))
    reason = db.Column(db.String(255))

class RoleReader(db.Model):
    __tablename__ = 'role_readers'

    role = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    reader_id = db.Column(db.Integer, db.ForeignKey('readers.id'), primary_key=True)

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)

    ldap_enabled = db.Column(db.Boolean, default=False)
    ldap_server = db.Column(db.String(255))

    openid_enabled = db.Column(db.Boolean, default=False)
    openid_client_id = db.Column(db.String(255))
    openid_client_secret = db.Column(db.String(255))
    openid_metadata_url = db.Column(db.String(255))

class Gateway(db.Model):
    __tablename__ = "gateways"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    configs = db.Column(db.JSON)

class Plugin(db.Model):
    __tablename__ = "plugins"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64), nullable=False)
    configs = db.Column(db.JSON)

class Addon(db.Model):
    __tablename__ = "addons"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64), nullable=False)
    git_url = db.Column(db.String(128))