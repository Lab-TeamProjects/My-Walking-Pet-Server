# 블루포인트
from flask import Blueprint
from flask import current_app

# http 응답
from flask import jsonify
from flask import request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import protocol
from ..auth import *
from ..sql_models import *

import datetime

bp = Blueprint('store', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'

def is_valid_date(date_string):
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@bp.route("/users/money", methods=['GET', 'PUT'])
def user_money():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        with Session(current_app.database) as session:
            money = session.query(Moneys).filter(Moneys.user_id == user_id).first()

            if money:
                # GET 요청시 총 걸음 수 리턴
                if request.method == 'GET':
                    return jsonify({'result': protocol.OK, 'money': money.money})
                
                # PUT 요청시 변경
                elif request.method == 'PUT':
                    add_money = request.json['money']
                    money.money += add_money
                    session.commit()
                    return jsonify({'result': protocol.OK})
            else:
                return '이상한 유저', 401
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401


# GET일 땐 검색정보 리턴
@bp.route("/users/steps", methods=['GET'])
def get_user_steps():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        with Session(current_app.database) as session:
            start_day = request.args.get('start_day')
            end_day = request.args.get('end_day')

            # 둘 중 하나가 잘못된 날짜데이터일 때
            if (not is_valid_date(start_day)) or (not is_valid_date(end_day)):
                return jsonify({'result': protocol.INVALUD_DATE})
            # 시작날짜가 더 늦은 날짜일때
            if start_day > end_day:
                return jsonify({'result': protocol.INVALUD_DATE_RANGE})

            # 요청한 유저의 입력받은 시작 날짜 ~ 끝나는 날짜만큼의 데이터만 검색
            step_data = session.query(DailyStepCounts).filter(
                (DailyStepCounts.user_id == user_id) &
                (DailyStepCounts.date.between(start_day, end_day))
                ).all()
            
            step_list = [step.to_dict() for step in step_data]

            return jsonify({'result': protocol.OK, 'steps': step_list})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

def steps_update(session: Session, user_id, step_date: dict):
    date = step_date['date']
    step = step_date['step']
    goal = step_date['goal']
    kcal = step_date['kcal']
    distance = step_date['distance']

    step_for_db = session.query(DailyStepCounts).filter((DailyStepCounts.user_id == user_id) & (DailyStepCounts.date == date)).first()

    if step_for_db:
        # 당일 데이터면 수정
        if datetime.date.fromisoformat(date) == datetime.date.today():
            step_for_db.step += step
            step_for_db.goal = goal
            step_for_db.kcal = kcal
            step_for_db.distance = distance
            session.commit()
            
            return {"result": protocol.OK, "date": date}
        
        # 당일 데이터가 아닌데 이미 DB에 존재한다면 수정 불가
        else:
            return {"result": protocol.UNCORRECTABLE_DATA, "date": date}
        
    # DB에 데이터가 없다면 날짜 상관없이 추가
    else:
        new_step = DailyStepCounts(
            user_id=user_id,
            date=date,
            step=step,
            goal=goal,
            kcal=kcal,
            distance=distance
        )
        session.add(new_step)
        session.commit()
        
        return {"result": protocol.OK, "date": date}

# PUT일 땐 정보 수정 및 추가            
@bp.route("/users/steps", methods=['PUT'])
def update_user_step():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        steps = request.json['steps']
        result_list = []

        with Session(current_app.database) as session:
            # 여러 데이터가 들어올 수 있으니 배열로 받음.
            for step_date in steps:
                date = step_date['date']

                # 이상한 날짜 입력시 다음 반복 수행
                if not is_valid_date(date):
                    result_list.append({"result": protocol.INVALUD_DATE, "date": date})
                    continue
                
                # DB 내용 변경 후, 배열에 결과 추가
                result_list.append(steps_update(session, user_id, step_date))
                
        return jsonify({'results': result_list})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 상점의 아이템 조회
@bp.route("/store/items", methods=['GET'])
def get_item_list():
    with Session(current_app.database) as session:
        # items 테이블에서 모든 항목 검색
        # 검색 결과 json으로 변환
        # return 결과
        items = session.query(Items).all()

        item_list = []
        for e in items:
            item_list.append(e.to_dict())
    return jsonify({'result': protocol.OK, 'items': item_list})

# 아이템 검색
@bp.route("/store/items/<int:item_id>", methods=["GET"])
def item_search(item_id):
    with Session(current_app.database) as session:
        item = session.query(Items).filter(Items.item_id == item_id).first()
        effect = session.query(ItemEffects).filter(ItemEffects.item_id == item_id).first()

    return jsonify({'result': protocol.OK, 'item_info': item.to_dict().update(effect.to_dict())})

# 아이템 구매
@bp.route("/store/items/<int:item_id>/purchase", methods=['POST'])
def purchase_item(item_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        quantity = request.json['quantity']

        with Session(current_app.database) as session:
            item = session.query(Items).filter(Items.item_id == item_id).first()
            money = session.query(Moneys).filter(Moneys.user_id == user_id).first()
            
            total = item.item_price * quantity

            # 금액 확인
            if money.money - total > 0:
                money.money - total
            else:
                return jsonify({'result': protocol.NO_MONEY})
            
            user_item = session.query(UserItems).filter((UserItems.user_id == user_id) & (UserItems.item_id == item_id)).first()
            # 아이템 테이블이 있으면 개수만 변경 없으면 테이블 추가
            if user_item:
                user_item.item_quantity += quantity
            else:
                new_item = UserItems(user_id=user_id, item_id=item_id, quantity=quantity)
                session.add(new_item)

            # item_purchase_history 테이블에 구매 이력 추가
            try:
                session.commit()
                return jsonify({'result': protocol.OK})
            except IntegrityError:
                session.rollback()
                return jsonify({'result': protocol.DATABASE_ERROR})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    
# 상점의 알 조회
@bp.route("/store/eggs", methods=["GET"])
def get_store_egg():
    egg_list = []
    with Session(current_app.database) as session:
        eggs = session.query(Eggs).all()
        
        for egg in eggs:
            egg_list.append(egg.to_dict())
    
    return jsonify({'result': protocol.OK, 'eggs': egg_list})

@bp.route("/store/eggs/<int:egg_id>/purchase", methods=["POST"])
def egg_purchase(egg_id):
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        with Session(current_app.database) as session:
            egg = session.query(Eggs).filter(Eggs.egg_id == egg_id).first()
            if egg is None:
                return jsonify({'result': protocol.INVALID_ITEM_ID})
            

            user_money = session.query(Moneys).filter(Moneys.user_id == user_id).first()

            if user_money is None:
                print("돈 레코드 없는 유저")
                return jsonify({'result': protocol.FAIL})

            if user_money.money < egg.egg_price:
                return jsonify({'result': protocol.NO_MONEY})
            else:
                user_money.money -= egg.egg_price
                
                new_egg = HatchingEggs(user_id=user_id, egg_id=egg_id)
                session.add(new_egg)

                new_history = EggPurchaseHistory(user_id=user_id, egg_id=egg_id, egg_purchase_date=now_kr(), price=egg.egg_price)
                session.add(new_history)

                session.commit()
            return ok_json()

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 소유한 아이템 조회
@bp.route("/users/items", methods=['GET'])
def user_items():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        with Session(current_app.database) as session:
            items = session.query(UserItems, Items).\
                join(Items, UserItems.item_id == Items.item_id).\
                filter(UserItems.user_id == user_id).all()

            item_list = []
            for e in items:
                item_list.append({
                    'id': e.items.item_id,
                    'quantity': e.useritems.item_quantity,
                    'name': e.items.item_name
                })
        return jsonify({'result': protocol.OK, 'items': item_list})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    