# 블루포인트
from flask import Blueprint
from flask import current_app
# MySQl 연결
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
# http 응답
from flask import jsonify
from flask import request

from ..sql_models import Eggs, EggTypes, Moneys, UserEggs, EggPurchaseHistory, HatchingEggs, Pets, PetBroods, PetAttributes, PetCollections
from .. import protocol
from ..exception import *

# 헤더 인증 정보
from ..auth import *

import random

bp = Blueprint('egg', __name__, url_prefix='/users/eggs')


    
@bp.route("", methods=["GET"])
def get_user_eggs():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        user_egg_list = []
        with Session(current_app.database) as session:
            hatch_eggs = session.query(HatchingEggs).filter(HatchingEggs.owner_id == user_id).all()
            
            for user_egg in hatch_eggs:
                egg = session.query(Eggs).filter(Eggs.egg_id == user_egg.egg_id).first()

                user_egg_list.append({
                    'id': egg.egg_id,
                    'name': egg.egg_name,
                    'growth': user_egg.hatch_egg_growth,
                    'need_growth': egg.need_growth_value
                })
        return jsonify({'result': protocol.OK, 'eggs': user_egg_list})

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

@bp.route("/<int:egg_id>", methods=["GET"])
def get_user_egg(egg_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        with Session(current_app.database) as session:
            egg = session.query(HatchingEggs).filter((HatchingEggs.owner_id == user_id) & (HatchingEggs.egg_id == egg_id)).first()

            if egg is None:
                return jsonify({'result': protocol.NO_EGG})
            
            egg_info = session.query(Eggs).filter(Eggs.egg_id == egg.egg_id).first()

            egg_dict = {
                'id': egg_info.egg_id,
                'name': egg_info.egg_name,
                'growth': egg.hatch_egg_growth,
                'need_growth': egg_info.need_growth_value
            }
            return jsonify({'result': protocol.OK, 'egg': egg_dict})

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

@bp.route("/<int:egg_id>/growth", methods=["GET"])
def get_user_egg_growth(egg_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        with Session(current_app.database) as session:
            egg = session.query(HatchingEggs).filter((HatchingEggs.owner_id == user_id) & (HatchingEggs.egg_id == egg_id)).first()

            if egg is None:
                return jsonify({'result': protocol.NO_EGG})
            
            return jsonify({'result': protocol.OK, 'growth': egg.hatch_egg_growth})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

@bp.route("/<int:egg_id>/growth", methods=["POST"])
def set_user_egg_growth(egg_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        add_value = request.json['value']
        with Session(current_app.database) as session:
            egg = session.query(HatchingEggs).filter((HatchingEggs.owner_id == user_id) & (HatchingEggs.egg_id == egg_id)).first()
            egg_info = session.query(Eggs).filter(Eggs.egg_id == egg.egg_id).first()

            egg.hatch_egg_growth += add_value
            if egg.hatch_egg_growth > egg_info.need_growth_value:
                egg.hatch_egg_growth  = egg_info.need_growth_value

            session.commit()
            
            return ok_json()
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

egg1 = ["cat", "웰시코기"]

@bp.route("/<int:egg_id>/awake", methods=["POST"])
def awake_user_egg(egg_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        with Session(current_app.database) as session:
            egg = session.query(HatchingEggs).filter((HatchingEggs.owner_id == user_id) & (HatchingEggs.egg_id == egg_id)).first()
            egg_info = session.query(Eggs).filter(Eggs.egg_id == egg.egg_id).first()
            
            if egg.hatch_egg_growth == egg_info.need_growth_value:
                choice_brood = random.choice(egg1)

                brood_info = session.query(PetBroods).filter(PetBroods.brood_name == choice_brood).first()
                
                new_pet = Pets(owner_id=user_id, brood_id=brood_info.brood_id, pet_name=choice_brood, pet_birthday=korea_now_time())
                new_pet_attr = PetAttributes(pet_id=new_pet.pet_id)
                session.add(new_pet)
                session.add(new_pet_attr)
                session.delete(egg)
                session.commit()

                # 컬렉션 추가
                new_collec = PetCollections(user_id=user_id, brood_id=brood_info.brood_id)
                session.add(new_collec)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()

                return jsonify({'result': protocol.OK, 'brood': choice_brood})
            return jsonify({'result': protocol.SHORTFALL_VALUE})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401