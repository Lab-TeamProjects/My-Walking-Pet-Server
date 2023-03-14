import uuid
from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import INTEGER

from sqlalchemy import MetaData
metadata_obj = MetaData()

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

users = Table(
     "users",
     metadata_obj,
     Column("user_id", INTEGER(unsigned=True), primary_key=True),
     Column("email", String(320), unique=True, nullable=False),
     Column("uuid", String(32), nullable=False, default=generate_uuid),
     Column("authStatus", Boolean, nullable=False, default=False)
)

passwords = Table(
    "passwords",
    metadata_obj,
    Column("pw_id", INTEGER(unsigned=True), primary_key=True),
    Column("user_id", INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False),
    Column("password", String(64), nullable=False),
    Column("salt", String(64), nullable=False),
    Column("update_date", DateTime, nullable=False)
)

email_verification_tokens = Table(
    "email_verification_tokens",
    metadata_obj,
    Column("user_id", INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True),
    Column("token", String(64), unique=True, nullable=False),
    Column("token_issued_at", DateTime, nullable=False),
    Column("token_expiration_time", DateTime, nullable=False)
)

access_tokens = Table(
    "access_tokens",
    metadata_obj,
    Column("user_id", INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True),
    Column("access_token", String(64), unique=True, nullable=False),
    Column("access_token_issued_at", DateTime, nullable=False),
    Column("access_token_expiration_time", DateTime, nullable=False)
)