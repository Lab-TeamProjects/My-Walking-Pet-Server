# 블루포인트
from flask import Blueprint
from flask import current_app

from sqlalchemy.orm import Session
from .sql_models import AccessTokens

import jwt
from datetime import datetime
import pytz
# 사용자 지정 Exception 객체
from .exception import *
from flask import jsonify
from . import protocol
import os

kst = pytz.timezone('Asia/Seoul')
# 한국시간 리턴
def now_kr():
    return datetime.now(kst)

def to_pytz(time: datetime):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC).astimezone(kst)

# 엑세스 토큰 검증
def verify_access_token(access_token):
    try:
        secret_key = os.environ.get('SECRET_KEY')
        decoded = jwt.decode(access_token, secret_key, algorithms='HS256')
        iat = datetime.fromtimestamp(decoded['iat'])
        exp = datetime.fromtimestamp(decoded['exp'])

        if iat > exp:
            raise InvalidAccessToken("Invalid Access Token")

        # 토큰이 변형되지 않았는지 검증
        if validate_token_in_database(access_token, iat, exp):
            return decoded['user_id']
        else:
            raise InvalidAccessToken("Modified Access Token")
        
    except jwt.ExpiredSignatureError:
        raise ExpiredAccessToken("Expired Access Token")
    except jwt.InvalidSignatureError:
        raise InvalidAccessToken("Invalid Access Token")
        
def validate_token_in_database(access_token, iat, exp):
    with Session(current_app.database) as session:
        db_token = session.query(AccessTokens).filter(AccessTokens.access_token == access_token).first()

        if db_token:
            # 토큰이 데이터베이스에 저장된 값과 일치하는지 확인
            if db_token.access_token_issued_at == iat and db_token.access_token_expiration_time == exp:
                return True
    return False

def get_user_id(auth_header):
    if auth_header:
        access_token = auth_header.split(" ")[1]
        try:
            return verify_access_token(access_token)
        # 예외 떠넘기기
        except InvalidAccessToken as e:
            raise InvalidAccessToken(str(e))
        except ExpiredAccessToken:
            raise ExpiredAccessToken("Expired Access Token")
    else:
        raise NoHeaderInfo("No header info")
    
def ok_json():
    return jsonify({'result': protocol.OK})
def fail_json():
    return jsonify({'result': protocol.OK})