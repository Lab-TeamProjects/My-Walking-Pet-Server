import uuid
from __init__ import db

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

class Users(db.Model):
    user_id = db.Column(INTEGER(unsigned=True), primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False)
    uuid = db.Column(db.String(32), nullable=False, default=generate_uuid)
    authStatus = db.Column(db.Boolean, default=False, nullable=False)

class Passwords(db.Model):
    pw_id = db.Column(INTEGER(unsigned=True), primary_key=True)
    user_id = db.Column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    update_date = db.Column(db.DateTime, nullable=False)

    user = db.relationship('Users', backref=db.backref('passwords', lazy=True))

class email_verification_tokens(db.Model):
    user_id = db.Column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    token_issued_at = db.Column(db.DateTime, nullable=False)
    token_expiration_time = db.Column(db.DateTime, nullable=False)

    user = db.relationship('Users', backref=db.backref('passwords', lazy=True))

class access_tokens(db.Model):
    user_id = db.Column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    access_token = db.Column(db.String(64), unique=True, nullable=False)
    access_token_issued_at = db.Column(db.DateTime, nullable=False)
    access_token_expiration_time = db.Column(db.DateTime, nullable=False)

    user = db.relationship('Users', backref=db.backref('passwords', lazy=True))