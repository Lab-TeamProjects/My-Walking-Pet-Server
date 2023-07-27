import uuid
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, DECIMAL
from datetime import datetime
import decimal
import random
import enum

from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import MetaData
metadata_obj = MetaData()

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

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

class PasswordResetTokens(Base):
    __tablename__ = 'password_reset_tokens'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    password_reset_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_reset_token_issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    password_reset_token_expiration_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    isVerified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=0)

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
    main_pet_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=True)

    def to_dict(self):
        return {
            'nickname': self.nickname,
            'status_message': self.status_message,
            'user_tag': self.user_tag
        }

class ProfilePhotos(Base):
    __tablename__ = 'profile_photos'

    photo_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    image_path: Mapped[str] = mapped_column(String(100), nullable=False)

class Moneys(Base):
    __tablename__ = 'moneys'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    money: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, default=0)

class DailyStepCounts(Base):
    __tablename__ = 'daily_step_counts'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    walk_date: Mapped[datetime.date] = mapped_column(DateTime, primary_key=True)
    goal: Mapped[int] = mapped_column(INTEGER, nullable=False, default=7000)

    step: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)
    kcal: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    distance: Mapped[decimal.Decimal] = mapped_column(DECIMAL(6, 4), nullable=False, default=0)
    sec: Mapped[int] = mapped_column(INTEGER, nullable=False)

    #운동 데이터
    exer_step: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)
    exer_kcal: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    exer_distance: Mapped[decimal.Decimal] = mapped_column(DECIMAL(6, 4), nullable=False, default=0)
    exer_sec: Mapped[int] = mapped_column(INTEGER, nullable=False)

    def to_dict(self):
        return {
            'date': self.walk_date.strftime("%Y-%m-%d"),
            'goal': self.step,
            'count': self.step,
            'kcal': self.kcal,
            'distance': self.distance,
            'sec': self.sec,
            'exercise_count': self.exer_step,
            'exercise_kcal': self.exer_kcal,
            'exercise_distance': self.exer_distance,
            'exercise_sec': self.exer_sec,
        }
    
class Friends(Base):
    __tablename__ = 'friends'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    friend_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)

class FriendRequests(Base):
    __tablename__ = 'friend_requests'

    friend_request_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    requestor_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    target_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)

# 아이템

class AnimalAttribute(enum.Enum):
    THIRST = "thirst"
    HUNGER = "hunger"
    CLEAN = "clean"
    FEEL = "feel"

class Items(Base):
    __tablename__ = 'items'

    item_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String(20), nullable=False)
    item_type: Mapped[AnimalAttribute] = mapped_column(Enum(AnimalAttribute, length=6), nullable=False)
    item_price: Mapped[int] = mapped_column(INTEGER, nullable=False)
    item_description: Mapped[str] = mapped_column(String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.item_id,
            'name': self.item_name,
            'price': self.item_price,
            'description': self.item_description
        }

class ItemEffects(Base):
    __tablename__ = 'item_effects'

    item_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('items.item_id'), primary_key=True)
    attribute_type: Mapped[AnimalAttribute] = mapped_column(Enum(AnimalAttribute, length=6), nullable=False, primary_key=True)
    attribute_value: Mapped[int] = mapped_column(INTEGER, nullable=False)

    def to_dict(self):
        return {
            'id': self.item_id,
            'attribute_type': self.attribute_type,
            'increment': self.attribute_value
        }

class UserItems(Base):
    __tablename__ = 'user_items'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    item_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('items.item_id'), primary_key=True)
    item_quantity: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)

    def to_dict(self):
        return {
            'id': self.item_id,
            'quantity': self.item_quantity
        }

class ItemPurchaseHistory(Base):
    __tablename__ = 'item_purchase_history'

    purchase_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    item_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('items.item_id'), nullable=False)
    purchase_time: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)
    purchase_count: Mapped[int] = mapped_column(INTEGER, nullable=False)
    item_type: Mapped[AnimalAttribute] = mapped_column(Enum(AnimalAttribute, length=6), nullable=False)
    total_price: Mapped[int] = mapped_column(INTEGER, nullable=False)

# 동물 테이블
class PetCollections(Base):
    __tablename__ = 'pet_collections'
    
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    brood_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('pets.pet_id'), primary_key=True)
    level: Mapped[int] = mapped_column(INTEGER, nullable=False, default=1)

    def to_dict(self):
        return {
            'brood_id': self.brood_id,
            'level': self.level
        }
    
class PetBroods(Base):
    __tablename__ = 'pet_broods'
    
    brood_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    brood_name: Mapped[str] = mapped_column(String(20), nullable=False)
    brood_description: Mapped[str] = mapped_column(String(100), nullable=False)
    brood_max_growth: Mapped[int] = mapped_column(INTEGER, nullable=False)
    brood_next_level: Mapped[int] = mapped_column(INTEGER, ForeignKey('pet_broods.brood_id'), nullable=True)
    def to_dict(self):
        return {
            'id': self.brood_id,
            'name': self.brood_name,
            'description': self.brood_description,
            'max_growth': self.brood_max_growth,
            'next_level': self.brood_next_level
        }

class Pets(Base):
    __tablename__ = 'pets'

    pet_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    brood_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('pet_broods.brood_id'), nullable=False)
    pet_name: Mapped[str] = mapped_column(String(10), nullable=False)
    is_runaway: Mapped[bool] = mapped_column(Boolean, nullable=False, default=0)
    pet_birthday: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)
    
class PetAttributes(Base):
    __tablename__ = 'pet_attributes'
    
    pet_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('pets.pet_id'), primary_key=True)
    level: Mapped[int] = mapped_column(TINYINT, nullable=False, default=0)
    growth: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)
    hunger: Mapped[int] = mapped_column(TINYINT, nullable=False, default=100)
    thirsty: Mapped[int] = mapped_column(TINYINT, nullable=False, default=100)
    clean: Mapped[int] = mapped_column(TINYINT, nullable=False, default=100)
    feel: Mapped[int] = mapped_column(TINYINT, nullable=False, default=100)

    def to_dict(self):
        return {
            'id': self.pet_id,
            'level': self.level,
            'growth': self.growth,
            'hunger': self.hunger,
            'thirsty': self.thirsty,
            'clean': self.clean,
            'feel': self.feel,
        }

class PetAdoptionHistory(Base):
    __tablename__ = 'pet_adoption_history'
    
    adoption_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    pet_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('pets.pet_id'), nullable=False)
    adoption_date: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)


# 알
class EggTypes(Base):
    __tablename__ = 'egg_types'

    egg_type_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    egg_type: Mapped[str] = mapped_column(String(20), nullable=False)
    need_growth_value: Mapped[int] = mapped_column(INTEGER, nullable=False)

class Eggs(Base):
    __tablename__ = 'eggs'

    egg_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    egg_name: Mapped[str] = mapped_column(String(20), nullable=False)
    egg_price: Mapped[int] = mapped_column(INTEGER, nullable=False)
    egg_description: Mapped[str] = mapped_column(String(100), nullable=False)
    need_growth_value: Mapped[int] = mapped_column(INTEGER, nullable=False)

    def to_dict(self):
        return {
            'id': self.egg_id,
            'name': self.egg_name,
            'price': self.egg_price,
            'description': self.egg_description,
            'need_growth': self.need_growth_value,
        }


class UserEggs(Base):
    __tablename__ = 'user_eggs'

    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), primary_key=True)
    egg_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('eggs.egg_id'), primary_key=True)
    egg_quantity: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)

class HatchingEggs(Base):
    __tablename__ = 'hatching_eggs'

    hatch_egg_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    egg_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('eggs.egg_id'), nullable=False)
    hatch_egg_growth: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)
    
class EggPurchaseHistory(Base):
    __tablename__ = 'egg_purchase_historys'

    egg_purchase_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), ForeignKey('users.user_id'), nullable=False)
    egg_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('eggs.egg_id'), nullable=False)
    egg_purchase_date: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)
    price: Mapped[int] = mapped_column(INTEGER, nullable=False)

