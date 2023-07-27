# 블루포인트
from flask import Blueprint
from flask import current_app
# MySQl 연결
from sqlalchemy.orm import Session, joinedload
# http 응답
from flask import jsonify
from flask import request

import base64

from ..sql_models import Pets, PetCollections, PetAttributes, PetAdoptionHistory, PetBroods, ItemEffects, Items
from .. import protocol

# 헤더 인증 정보
from ..auth import *

bp = Blueprint('pet', __name__, url_prefix='/')

def pet_to_dict(pet: Pets, brood: PetBroods, attribute: PetAttributes):
    return {
        'id': pet.pet_id,
        'name': pet.pet_name,
        'brood_name': brood.brood_name,
        'is_runaway': pet.is_runaway,
        'birthday' : pet.pet_birthday,
        'level' : attribute.level,
        'growth' : attribute.growth,
        'max_growth' : brood.brood_max_growth,
        'hunger': attribute.hunger,
        'thirsty': attribute.thirsty,
        'clean': attribute.clean,
        'feel': attribute.feel
    }

def pet_detail_to_dict(pet: Pets, attribute: PetAttributes, brood: PetBroods):
    return {
        'id': pet.pet_id,
        'name': pet.pet_name,
        'birthday': pet.pet_birthday,
        'brood_name': brood.brood_name,
        'level': attribute.level,
        'growth': attribute.growth,
        'is_runaway': pet.is_runaway,
        'hunger': attribute.hunger,
        'thirsty': attribute.thirsty,
        'clean': attribute.clean,
        'feel': attribute.feel
    }

# 유저가 가지고 있는 펫정보 가져오기
@bp.route("/users/pets", methods=["GET"])
def get_pets():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        with Session(current_app.database) as session:
            pets = session.query(Pets).filter(Pets.owner_id == user_id).all()
            pet_list = []
            for pet in pets:
                attribute = session.query(PetAttributes).filter(PetAttributes().pet_id == pet.pet_id).first()
                brood = session.query(PetBroods).filter(PetBroods.brood_id == pet.brood_id).first()
                pet_list.append(pet_to_dict(pet, brood, attribute))

            return jsonify({'result': protocol.OK, 'pets': pet_list})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    
@bp.route("/users/pets/<int:pet_id>", methods=["GET"])
def get_pet(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        with Session(current_app.database) as session:
            # 조인
            # query = session.query(Pets, PetAttributes, PetBroods).\
            #     join(PetAttributes, Pets.pet_id == PetAttributes.pet_id).\
            #     join(PetBroods, Pets.brood_id == PetBroods.brood_id).\
            #     filter(Pets.pet_id == 1).\
            #     first()

            # pet, attributes, broods = query


            # 개별적인 검색
            pet = session.query(Pets).filter((Pets.owner_id == user_id) & (Pets.pet_id == pet_id)).first()
            if pet is None:
                return jsonify({'result': protocol.NOT_MY_PET})
            attribute = session.query(PetAttributes).filter(PetAttributes.pet_id == pet_id).first()
            brood = session.query(PetBroods).filter(PetBroods.brood_id == pet.brood_id).first()

            return jsonify({'result': protocol.OK, 'pet': pet_detail_to_dict(pet, attribute, brood)})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401    

# 펫 정보수정(이름변경)
@bp.route("/users/pets/<int:pet_id>/name", methods=["PUT"])
def update_pet_name(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        name = request.json['name']

        with Session(current_app.database) as session:
            pet = session.query(Pets).filter(Pets.pet_id == pet_id).first()
            
            if pet.owner_id == user_id:
                pet.pet_name = name
                session.commit()

                return ok_json()
            else:
                return jsonify({'result': protocol.NOT_MY_PET})
     
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# pet attribute change
@bp.route("/users/pets/<int:pet_id>/attributes", methods=['PUT'])
def update_pet_attribute(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        growth = request.json['growth']
        hunger = request.json['hunger']
        thirsty = request.json['thirsty']
        clean = request.json['clean']
        feel = request.json['feel']

        with Session(current_app.database) as session:
            pet = session.query(Pets).filter((Pets.pet_id == pet_id) & (Pets.owner_id == user_id)).first()

            if pet:
                attribute = session.query(PetAttributes).filter(PetAttributes.pet_id == pet_id).first()

                attribute.growth = growth
                attribute.hunger = hunger
                attribute.thirsty = thirsty
                attribute.clean = clean
                attribute.feel = feel

                session.commit()

                return ok_json()
            else:
                return jsonify({'result': protocol.NOT_MY_PET})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    
# pet attribute change
@bp.route("/users/pets/<int:pet_id>/attributes", methods=['PATCH'])
def patch_pet_attribute(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        growth = request.json.get('growth')
        hunger = request.json.get('hunger')
        thirsty = request.json.get('thirsty')
        clean = request.json.get('clean')
        feel = request.json.get('feel')

        with Session(current_app.database) as session:
            pet = session.query(Pets).filter((Pets.pet_id == pet_id) & (Pets.owner_id == user_id)).first()

            if pet:
                attribute = session.query(PetAttributes).filter(PetAttributes.pet_id == pet_id).first()

                if growth:
                    attribute.growth = growth
                if hunger:
                    attribute.hunger = hunger
                if thirsty:
                    attribute.thirsty = thirsty
                if clean:
                    attribute.clean = clean
                if feel:
                    attribute.feel = feel
                session.commit()

                return ok_json()
            else:
                return jsonify({'result': protocol.NOT_MY_PET})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 펫 파양?
@bp.route("/users/pets/<int:pet_id>", methods=["DELETE"])
def del_pet(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        with Session(current_app.database) as session:
            pet, attribute = session.query(Pets, PetAttributes).join(PetAttributes, Pets.pet_id == PetAttributes.pet_id).\
                filter((Pets.owner_id == user_id) & (Pets.pet_id == pet_id))
            
            if pet is None or attribute is None:
                return jsonify({'resulut': protocol.NOT_MY_PET})
            else:
                session.delete(attribute)
                session.delete(pet)
                session.commit()
                # 히스토리 추가
                return ok_json()
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 동물 속성만 반환 (허기, 갈증, 성장치 등)
@bp.route("/users/pets/<int:pet_id>/attributes", methods=["GET"])
def get_pet_attribute(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        with Session(current_app.database) as session:
            pet = session.query(Pets).filter((Pets.pet_id == pet_id) & (Pets.owner_id == user_id)).first()

            if pet:
                attribute = session.query(PetAttributes).filter(PetAttributes.pet_id == pet_id).first()

                return jsonify({'result': protocol.OK, 'attribute': attribute.to_dict()})
            else:
                return jsonify({'result': protocol.NOT_MY_PET})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401


# 성장 속성값 가져오기
@bp.route("/users/pets/<int:pet_id>/attributes/growth", methods=["GET"])
def get_pet_growth():
    pass

# 허기 속성값 가져오기
@bp.route("/users/pets/<int:pet_id>/attributes/hunger", methods=["GET"])
def get_pet_hunger():
    pass

# 갈증 속성값 가져오기
@bp.route("/users/pets/<int:pet_id>/attributes/thirsty", methods=["GET"])
def get_pet_thirsty():
    pass

# 청결 속성값 가져오기
@bp.route("/users/pets/<int:pet_id>/attributes/clean", methods=["GET"])
def get_pet_clean():
    pass

# 기분 속성값 가져오기
@bp.route("/users/pets/<int:pet_id>/attributes/feel", methods=["GET"])
def get_pet_feel():
    pass

# 펫에게 아이템 사용
@bp.route("/users/pets/<int:pet_id>/item-use", methods=["POST"])
def pet_item_use(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        item_id = request.json['item_id']

        with Session(current_app.database) as session:
            pass
            item_effect = session.query(ItemEffects).filter(ItemEffects.item_id == item_id).all()
            pet_attr = session.query(PetAttributes).filter((PetAttributes.pet_id == pet_id) & (Pets.owner_id == user_id)).first()

            for e in item_effect:
                if e.attribute_type == 'growth':
                    if pet_attr.growth + 25 < 100: 
                        pet_attr.growth += 25
                    else: 
                        pet_attr.growth = 100
                elif e.attribute_type == 'hunger':
                    if pet_attr.hunger + 25 < 100: 
                        pet_attr.hunger += 25
                    else: 
                        pet_attr.hunger = 100
                elif e.attribute_type == 'thirsty':
                    if pet_attr.thirsty + 25 < 100: 
                        pet_attr.thirsty += 25
                    else: 
                        pet_attr.thirsty = 100
                elif e.attribute_type == 'clean':
                    if pet_attr.clean + 25 < 100: 
                        pet_attr.clean += 25
                    else: 
                        pet_attr.clean = 100
                elif e.attribute_type == 'feel':
                    if pet_attr.feel + 25 < 100: 
                        pet_attr.feel += 25
                    else: 
                        pet_attr.feel = 100

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 쓰다듬기
@bp.route("/users/pets/<int:pet_id>/petting", methods=["POST"])
def pet_petting(pet_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        with Session(current_app.database) as session:
            pet_attr = session.query(PetAttributes).filter((PetAttributes.pet_id == pet_id) & (Pets.owner_id == user_id)).first()
            
            if pet_attr.feel + 25 < 100:
                pet_attr.feel += 25
                # 쿨타임 테이블에 기록 작성
            else:
                pet_attr.feel = 100
            return ok_json()

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 컬렉션 가져오기
@bp.route("/users/collections", methods=["GET"])
def get_pet_collections():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        with Session(current_app.database) as session:
            collec = session.query(PetCollections).filter(PetCollections.user_id == user_id).all()
            collect_list = []
            for e in collec:
                collect_list.append(e.to_dict())
        return jsonify({'result': protocol.OK, 'collections': collect_list})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    
@bp.route("/broods/<int:brood_name>", methods=["GET"])
def get_brood_detail(brood_name):
    with Session(current_app.database) as session:
        brood = session.query(PetBroods).filter(PetBroods.brood_id == brood_name).first()
        return jsonify({'result': protocol.OK, 'brood':brood.to_dict()})