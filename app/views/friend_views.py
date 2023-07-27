# 블루포인트
from flask import Blueprint
from flask import current_app
# MySQl 연결
from sqlalchemy.orm import Session
# http 응답
from flask import jsonify
from flask import request

import base64

from ..sql_models import Profiles, ProfilePhotos, Friends, FriendRequests, Users
from .. import protocol

# 헤더 인증 정보
from ..auth import *

bp = Blueprint('friend', __name__, url_prefix='/')

# 공개가능한 정보만 프로필에서 가져오는 함수
def get_public_profile(session: Session, friend_id):
    profile = session.query(Profiles).filter(Profiles.user_id == friend_id).first()

    if profile:
        # 검색된 프로필 정보 dict으로 변환
        profile_dict = profile.to_dict()

        # 프로필 사진 검색
        requestor_photo = session.query(ProfilePhotos).filter(ProfilePhotos.user_id == friend_id).first()

        # 프로필 사진 dict에 추가
        if requestor_photo:
            with open(f'C:\Profile_Photos\{requestor_photo.image_path}', 'rb') as f:
                imgdata = f.read()
            # base64 인코딩된 이미지 데이터 인코딩
            imgdata_encoded = base64.b64encode(imgdata)
            profile_dict['image'] = imgdata_encoded.decode('utf-8')
        else:
            profile_dict['image'] = ''
        
        return profile_dict
    else:
        raise NotFoundProfile("Not fount profile")

def get_uuid(session: Session, user_id):
    user = session.query(Users).filter(Users.user_id == user_id).first()
    return user.uuid

# 친구 신청
@bp.route("/users/friend_request", methods=["POST"])
def add_friend_request():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        name = request.json['name']
        friend_tag = request.json['friend_tag']

        with Session(current_app.database) as session:
            friend = session.query(Profiles).filter((Profiles.nickname == name) & (Profiles.user_tag == friend_tag)).first()

            if friend:
                # 자기 자신 친구 추가한 경우
                if friend.user_id == user_id:
                    return jsonify({'result': protocol.MYSELF_AN_ETERNAL_FRIEND})

                new_friend_requests = FriendRequests(requestor_id=user_id, target_id=friend.user_id)
                session.add(new_friend_requests)
                session.commit()

                return jsonify({'result': protocol.OK})
            else:
                return jsonify({'result': protocol.NOT_USER})

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 내가 보낸 친구신청 목록
@bp.route("/users/friend_request", methods=["GET"])
def get_friend_request():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        with Session(current_app.database) as session:
            friend_request = session.query(FriendRequests).filter(FriendRequests.requestor_id == user_id).all()

            target_list = []
            for requestor in friend_request:
                try:
                    # 공개가능 프로필 정보만 dict변환 후 리스트에 추가
                    profile_dict = get_public_profile(session, requestor.target_id)
                    profile_dict['request_id'] = requestor.friend_request_id
                    target_list.append(profile_dict)
                except NotFoundProfile as e:
                    # 프로필이 검색되지 않는 유저 발생
                    print(f"DB 무결성 위반: 프로필이 검색되지 않는 유저 (user_id: {requestor.target_id})")
            return jsonify({'result': protocol.OK, 'friend_requests': target_list})

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    
# 보낸 친구 요청 취소
@bp.route("/users/friend_requests", methods=["DELETE"])
def del_friend_request():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        friend_request_id = request.json['friend_request_id']

        with Session(current_app.database) as session:
            friend_request = session.query(FriendRequests).filter(FriendRequests.friend_request_id == friend_request_id).first()
            
            if friend_request:
                session.delete(friend_request)
                session.commit()
                return jsonify({'result': protocol.OK})
            else:
                return jsonify({'result': protocol.FAIL})

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 받은 친구 요청 목록
@bp.route("/users/friend_requests/received", methods=["GET"])
def get_friend_request_received():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        with Session(current_app.database) as session:
            friend_request = session.query(FriendRequests).filter(FriendRequests.target_id == user_id).all()

            requestor_list = []
            for requestor in friend_request:
                try:
                    # 공개가능 프로필 정보만 dict변환 후 리스트에 추가
                    profile_dict = get_public_profile(session, requestor.requestor_id)
                    profile_dict['request_id'] = requestor.friend_request_id
                    requestor_list.append(profile_dict)
                except NotFoundProfile as e:
                    # 프로필이 검색되지 않는 유저 발생
                    print(f"DB 무결성 위반: 프로필이 검색되지 않는 유저 (user_id: {requestor.requestor_id})")
            return jsonify({'result': protocol.OK, 'friend_request_received': requestor_list})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 친구 요청 수락
@bp.route("/users/friend_requests/received/accept", methods=["POST"])
def friend_reveived_accept():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        friend_request_id = request.json['friend_request_id']

        with Session(current_app.database) as session:
            friend_request = session.query(FriendRequests).filter(FriendRequests.friend_request_id == friend_request_id).first()

            if friend_request:
                friend = session.query(Profiles).filter(Profiles.user_id == friend_request.requestor_id).first()

                if friend:
                    requester_to_target = Friends(user_id=friend.user_id, friend_id=user_id)
                    target_to_requester = Friends(user_id=user_id, friend_id=friend.user_id)

                    # 서로의 친구목록에 추가 후
                    session.add(requester_to_target)
                    session.add(target_to_requester)

                    # 친구 요청은 삭제
                    session.delete(friend_request)
                # 검색되지 않는 유저인데 요청이 있으면 무결성이 깨지게 되므로 데이터 삭제
                # 친구 요청이 완료되어도 요청을 삭제해야 하므로 모든 경우에서 delete함.
                session.delete(friend_request)
                session.commit()
            else:
                return jsonify({'result': protocol.FAIL})

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

# 친구 요청 거부
@bp.route("/users/friend_requests/received/decline", methods=["POST"])
def friend_received_decline():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))        
        friend_request_id = request.json['friend_request_id']

        with Session(current_app.database) as session:
            friend_request = session.query(FriendRequests).filter(FriendRequests.friend_request_id == friend_request_id).first()

            if friend_request:
                session.delete(friend_request)
                session.commit()
                return ok_json()
            else:
                return fail_json()

    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    
# 친구 목록 가져오기
@bp.route("/users/friends", methods=["GET"])
def get_friends():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))

        with Session(current_app.database) as session:
            friend_list = session.query(Friends).filter(Friends.user_id == user_id).all()

            friend_profile_list = []
            for friend in friend_list:
                try:
                    # 공개가능 프로필 정보만 dict변환 후 리스트에 추가
                    friend_profile_list.append(get_public_profile(session, friend.friend_id))
                except NotFoundProfile as e:
                    # 프로필이 검색되지 않는 유저 발생
                    print(f"DB 무결성 위반: 프로필이 검색되지 않는 유저 (user_id: {friend.friend_id})")
            return jsonify({'result': protocol.OK, 'friends': friend_profile_list})
        
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401

@bp.route("/users/friends", methods=["DELETE"])
def delete_friends():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        
        name = request.json['name']
        friend_tag = request.json['friend_tag']

        with Session(current_app.database) as session:
            friend = session.query(Profiles).filter((Profiles.nickname == name) & (Profiles.user_tag == friend_tag)).first()

            if friend:
                user_to_friend = session.query(Friends).filter((Friends.user_id == user_id) & (Friends.friend_id == friend.user_id)).first()
                friend_to_user = session.query(Friends).filter((Friends.user_id == friend.user_id) & (Friends.friend_id == user_id)).first()

                if user_to_friend and friend_to_user:
                    session.delete(user_to_friend)
                    session.delete(friend_to_user)
                # 단방향 친구 발생(그럴리 없음)
                # 그래서 삭제
                elif user_to_friend:
                    session.delete(user_to_friend)
                elif friend_to_user:
                    session.delete(friend_to_user)
                session.commit()
                
                return ok_json()
            else:
                # 친구도 아닌 주제에 친구삭제 요청(ㅋㅋ)
                return fail_json()
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401    