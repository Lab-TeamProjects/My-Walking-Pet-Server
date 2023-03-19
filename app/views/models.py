import uuid
from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from datetime import datetime
import random

from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from sqlalchemy.ext.declarative import declarative_base

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

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    uuid: Mapped[str] = mapped_column(String(32), nullable=False, default=generate_uuid)
    authStatus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

class Passwords(Base):
    __tablename__ = 'passwords'

    pw_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    password: Mapped[str] = mapped_column(String(64), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    update_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class EmailVerificationTokens(Base):
    __tablename__ = 'email_verification_tokens'

    # ORM 방식
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    token_issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    token_expiration_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class AccessTokens(Base):
    __tablename__ = 'access_tokens'

    # ORM 방식
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    access_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    access_token_issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    access_token_expiration_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Core 방식
    # user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    # access_token = Column(String(64), unique=True, nullable=False)
    # access_token_issued_at = Column(DateTime, nullable=False)
    # access_token_expiration_time = Column(DateTime, nullable=False)

class Profiles(Base):
    __tablename__ = 'profiles'

    profile_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    nickname: Mapped[str] = mapped_column(String(10), nullable=False)
    status_message: Mapped[str] = mapped_column(String(64), nullable=False)
    sex: Mapped[str] = mapped_column(String(6), nullable=False)
    birthday: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)
    weight: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    height: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    user_tag: Mapped[str] = mapped_column(String(6), nullable=False, default='{:04d}'.format(random.randint(0,9999)))
    profile_img_path: Mapped[str] = mapped_column(String(100), nullable=True)
    
    
    

