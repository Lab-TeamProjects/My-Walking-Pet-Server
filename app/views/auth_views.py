# 블루포인트
from flask import Blueprint
from flask import current_app

# MySQl 연결
from sqlalchemy import text, insert, select, update
from flask_sqlalchemy import SQLAlchemy
from . import models

# 환경 변수
from dotenv import load_dotenv

import protocol
# 이메일 발송

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# 시간 객체
from datetime import datetime, timedelta

# Token생성 JWT라이브러리
import jwt
# SHA256
import hashlib
# 토큰 생성
import secrets    

# http 응답
from flask import jsonify
from flask import request

# 한국 시간 계산
import pytz

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# 데이터 모델 클래스
# from models import Users, Passwords, email_verification_tokens, access_tokens

bp = Blueprint('auth', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'
# 환경변수 로드
load_dotenv()

# 한국시간 리턴
def korea_now_time():
    kst = pytz.timezone('Asia/Seoul')
    utc_now = datetime.utcnow()
    return utc_now.astimezone(kst)

# 엑세스 토큰 발급
def generate_access_token(user_id):
    with current_app.database.connect() as conn:
        stmt = select(models.users).where(models.users.c.user_id == user_id)
        row = conn.execute(text(stmt)).fetchone()

        if row:
            uuid = row.uuid

            kst_now = korea_now_time()
            
            iat = kst_now
            exp = kst_now + timedelta(days=1)
            print(f"생성된 발급시간: {iat}, 생성된 만료시간: {exp}")

            payload = {
                'sub': uuid,
                'iat': int(round(iat.timestamp())),
                'exp': int(round(exp.timestamp()))
                # int로 형변환해서 소수점을 버리는 과정에서 데이터가 손실
                # 반올림으로 정확한 값을 유지
            }

            access_token = jwt.encode(payload, '221124104', algorithm='HS256')

            # DB에 access token 저장
            stmt = f"""REPLACE INTO access_tokens(user_id, access_token, access_token_issued_at, access_token_expiration_time)
                    VALUES('{user_id}', '{access_token}', '{iat}', '{exp}')"""
            conn.execute(text(stmt))
            conn.commit()
        else:
            return False

    return access_token

# 회원가입
@bp.route("/sign-up", methods=['POST'])
def sign_up():
    db = current_app.database

    _email = request.json['email']
    _password = request.json['password']

    # 솔트값 생성
    _salt = secrets.token_hex(32)
    _password += _salt
    # 비번 + 솔트 해시값 얻기
    hash_pw = hashlib.sha256(_password.encode()).hexdigest()

    # new_user = Users(email=_email)
    # db.session.add(new_user)
    # db.session.commit()

    kst_now = korea_now_time()
    # new_pw = Passwords()

    with db.connect() as conn:
        # user 정보 입력 
        result = conn.execute(insert(models.users).values(email=_email))
        conn.commit()
        user_id = result.lastrowid
    
        # password 입력
        kst_now = korea_now_time()
        result = conn.execute(insert(models.passwords).values(user_id=user_id, password=hash_pw, salt=_salt, update_date=kst_now))
        conn.commit()

    # 인증 링크 생성
    auth_url = email_verification(user_id, _email)
    # 인증 메일 발송
    send_result = send_email(_email, auth_url)
    if send_result:
        return jsonify({'result': protocol.OK })
    else:
        return jsonify({'result': protocol.EMAIL_SEND_FAIL })

# 메일 발송
def send_email(recipient, body):
    message = Mail(
        from_email='yjnnn0011@gmail.com',
        to_emails=recipient,
        subject='[MyWalkingPet] 회원가입 이메일 인증',
        html_content=body)

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print('메일전송실패: ' + str(e))
        return False

# 메일 인증 링크 생성
def email_verification(user_id, email):
    db = current_app.database
    
    # 인증 토큰 생성 후 DB 입력
    _token = secrets.token_hex(32)      # 결과값 자리수 nbyte*x

    kst_now = korea_now_time()
    iat = kst_now                                  # 발급 시간
    exp = kst_now + timedelta(days=1)              # 만료 시간

    with db.connect() as conn:
        # 이메일 토큰 정보 저장
        result = conn.execute(insert(models.email_verification_tokens).values(user_id=user_id, token=_token, token_issued_at=iat, token_expiration_time=exp))
        conn.commit()

    return svrURL + f'mailauth?authToken={_token}'


# 이메일 중복검사 함수
@bp.route("/check-email-duplication", methods=['POST'])
def check_email_duplication():
    _email = request.json['email']
    print(_email)
    # email 검색
    stmt = "SELECT email FROM users WHERE email='" + _email +"'"
    with current_app.database.connect() as conn:
        row = conn.execute(text(stmt)).fetchone()
  
        if row:
            return jsonify({'result': 'NO'})
        else:
            return jsonify({'result': 'OK'})
        


# 이메일 인증 페이지(완료되면 authStatus 변경)
@bp.route('/mailauth', methods=['GET'])
def mailauth():
    _authToken = request.args.get('authToken')

    with current_app.database.connect() as conn:
        stmt = f"SELECT * FROM email_verification_tokens WHERE token='{_authToken}'"
        # .fetchone(): 검색결과가 None인지 구분 해주는 메소드
        row = conn.execute(text(stmt)).fetchone()
        if row:
            # 검색 결과가 있을 때 처리
            user_id = row.user_id
            iat = row.token_issued_at
            exp = datetime.strftime(row.token_expiration_time, '%Y-%m-%d %H:%M:%S')

            if exp < datetime.now():
                # 만료 시간보다 현재 시간이 빠를 때
                stmt = f"UPDATE users SET authStatus = 1 WHERE user_id='{user_id}'"
                conn.execute(text(stmt))

                # 여기는 응답을 페이지 이동으로 해야할듯.....
                return jsonify({'msg': '이메일 인증 완료'})
            else:
                return jsonify({'msg': '만료된 토큰입니다.'})
        else:
            return jsonify({'msg': '토큰이 유효하지 않습니다.'})
            
# 로그인
@bp.route('/login', methods=['POST'])
def login():
    _email = request.json['email']
    _password = request.json['password']

    # email로 user_id, uuid 검색 쿼리
    with current_app.database.connect() as conn:
        stmt = f"SELECT * FROM users WHERE email='{_email}'"
        row = conn.execute(text(stmt)).fetchone()
        
        if not row:
            return jsonify({'result': 'NoID'})
        user_id = row.user_id
        uuid = row.uuid

        stmt = f"SELECT * FROM access_tokens WHERE user_id='{user_id}'"
        row = conn.execute(text(stmt)).fetchone()
        if row:
            return jsonify({'access_token': row.access_token})

        # user_id로 hash_pw, salt 검색 쿼리
        stmt = f"SELECT * FROM passwords WHERE user_id='{user_id}'"
        row = conn.execute(text(stmt)).fetchone()
        hashed_pw = row.password
        salt = row.salt

        # _password + salt를 해싱 후 hash_password와 비교
        pw_and_salt = _password + salt
        hashed_input_pw = hashlib.sha256(pw_and_salt.encode()).hexdigest()

        if hashed_pw == hashed_input_pw:
            # 맞으면 password 테이블의 update_date 컬럼 update
            kst_now = korea_now_time()
            stmt = f"UPDATE passwords SET update_date ='{kst_now}' WHERE user_id='{user_id}'"
        else:
            return jsonify({'result': 'NoPW'}), 401

    print(_email + "님이 로그인하였습니다.")
    access_token = generate_access_token(str(user_id))

    return jsonify({'result': 'OK', 'access_token': access_token})