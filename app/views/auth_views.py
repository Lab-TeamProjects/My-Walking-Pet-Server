# 블루포인트
from flask import Blueprint
from flask import current_app

# MySQl 연결
from sqlalchemy import text
from sqlalchemy.orm import Session
from flask_sqlalchemy import SQLAlchemy
# 데이터 모델 객체
from .models import Users, Passwords, EmailVerificationTokens, AccessTokens, Profiles

# 환경 변수
from dotenv import load_dotenv

from . import protocol
# 이메일 발송

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# 시간 객체
from datetime import datetime, timedelta, timezone

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

bp = Blueprint('auth', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'

# 환경변수 로드
load_dotenv()

# 한국시간 리턴
def korea_now_time():
    kst = pytz.timezone('Asia/Seoul')
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    korea_now = utc_now.astimezone(kst)
    return korea_now

# 회원가입
@bp.route("/sign-up", methods=['POST'])
def sign_up():
    _email = request.json['email']
    _password = request.json['password']

    # 솔트값 생성
    salt = secrets.token_hex(32)
    _password += salt
    # 비번 + 솔트 해시값 얻기
    hash_pw = hashlib.sha256(_password.encode()).hexdigest()

    print(f'해쉬된 비밀번호: {hash_pw}')
    # 신규 유저 데이터 객체 생성
    with Session(current_app.database) as session:
        # 신규유저 정보 삽입
        new_user = Users(email=_email)
        session.add(new_user)
        session.commit()

        session.refresh(new_user)

        # 비밀번호 정보 삽입
        new_pw = Passwords(
            user_id=new_user.user_id,
            password=hash_pw,
            salt=salt,
            update_date= korea_now_time()
        )
        session.add(new_pw)
        session.commit()

        # 인증 링크 생성
        auth_url = email_verification(new_user.user_id)
        
    # 인증 메일 발송
    send_result = send_email(_email, auth_url)
    
    if send_result:
        print(f"'{new_user.email}'님의 회원가입했습니다.")
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
        return True
    except Exception as e:
        print('메일전송실패: ' + str(e))
        return False

# 메일 인증 링크 생성
def email_verification(user_id):
    # 인증 토큰 생성 후 DB 입력
    token = secrets.token_hex(32)      # 결과값 자리수 nbyte*x

    kst_now = korea_now_time()
    iat = kst_now                                  # 발급 시간
    exp = kst_now + timedelta(days=1)              # 만료 시간

    with Session(current_app.database) as session:
        new_email_token = EmailVerificationTokens(
            user_id=user_id,
            token=token,
            token_issued_at=iat,
            token_expiration_time=exp
        )
        session.add(new_email_token)
        session.commit()

    return svrURL + f'mailauth?authToken={token}'


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
            return jsonify({'result': protocol.EMAIL_IS_DUPLICATION})
        else:
            return jsonify({'result': protocol.OK})    

# 이메일 인증 페이지(완료되면 authStatus 변경)
@bp.route('/mailauth', methods=['GET'])
def mailauth():
    _authToken = request.args.get('authToken')

    with Session(current_app.database) as session:
        mail_auth_token = session.query(EmailVerificationTokens).filter(EmailVerificationTokens.token == _authToken).first()

        if mail_auth_token:
            # 토큰의 만료기간이 지나지 않았을 때
            kst = pytz.timezone('Asia/Seoul')
            expiration_time_str = mail_auth_token.token_expiration_time.strftime('%Y-%m-%d %H:%M:%S')
            expiration_time_kst = datetime.strptime(expiration_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC).astimezone(kst)

            if expiration_time_kst > korea_now_time():
                user = session.query(Users).filter(Users.user_id == mail_auth_token.user_id).first()
                user.authStatus = True
                session.commit()

                return jsonify({'result': 'ok'})
    return jsonify({'result': 'fail'})

# 로그인
@bp.route('/login', methods=['POST'])
def login():    
    _email = request.json['email']
    _password = request.json['password']
    
    with Session(current_app.database) as session:
        user = session.query(Users).filter(Users.email == _email).first()

        # 유저 정보 검색 실패
        if not user:
            return jsonify({'result': protocol.NOT_FOUND_EMAIL})
        
        pw = session.query(Passwords).filter(Passwords.user_id == user.user_id).first()

        # 비밀번호가 검색되지 않음
        if not pw:
            print(f"예외발생: 비밀번호가 검색되지 않는 유저 user_id: {user.user_id}")
            return jsonify({}), 400

        # _password + salt를 해싱

        hashed_pw = hashlib.sha256(((_password + pw.salt).encode())).hexdigest()

        if pw.password != hashed_pw:
            # 비밀번호 오류!
            return jsonify({'result': protocol.NOT_CORRECT_PASSWORD})

        # 엑세스토큰 검색
        access_token = session.query(AccessTokens).filter(AccessTokens.user_id == user.user_id).first()

    if access_token:
        print(f"'{user.email}' 유저의 엑세스 토큰이 이미 존재하므로 기존의 토큰을 전송합니다.")
        return jsonify({'result': protocol.OK, 'access_token': access_token.access_token})
    
    print(f"'{user.email}' 유저의 엑세스 토큰이 검색되지 않았으므로 엑세스 토큰을 발급합니다.")

    access_token = generate_access_token(user.user_id, user.uuid)
    print(_email + "님이 로그인하였습니다.")

    return jsonify({'result': protocol.OK, 'access_token': access_token})

# 엑세스 토큰 발급
def generate_access_token(user_id, uuid):
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

    stmt = AccessTokens(user_id=user_id, access_token=access_token, access_token_issued_at=iat, access_token_expiration_time=exp)

    # merge는 replace into 와 같은 역할
    with Session(current_app.database) as session:
        session.merge(stmt)
        session.commit()

    return access_token

# 유저 정보 등록 및 수정
@bp.route('/users/profile/edit', methods=['POST'])
def profile_edit():
    # 헤더 정보 가져오기
    auth_header = request.headers.get('Authorization')

    if auth_header:
        access_token = auth_header.split(" ")[1]

        user_id = verify_access_token(access_token)
        if user_id:
            with Session(current_app.database) as session:
                search_profile = session.query(Profiles).filter(Profiles.user_id == user_id).first()

                if search_profile:
                    search_profile.nickname = request.json['nickname']
                    search_profile.status_message = request.json['status_message']
                    search_profile.sex = request.json['sex']
                    search_profile.birthday = request.json['birthday']
                    search_profile.weight = request.json['weight']
                    search_profile.height = request.json['height']
                else:
                    new_profile = Profiles(
                        user_id = user_id,
                        nickname = request.json['nickname'],
                        status_message = request.json['status_message'],
                        sex = request.json['sex'],
                        birthday = request.json['birthday'],
                        weight = request.json['weight'],
                        height = request.json['height']
                    )
                    session.add(new_profile)
                session.commit()
                return jsonify({'result': protocol.OK})
        else:
            return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    else:
        return jsonify({}), 400


# 유저 정보 열람
@bp.route('/users/profile/view', methods=['POST'])
def profile_view():
    # 헤더 정보 가져오기
    auth_header = request.headers.get('Authorization')
    if auth_header:
        access_token = auth_header.split(" ")[1]

        user_id = verify_access_token(access_token)
        if user_id:
            with Session(current_app.database) as session:
                profile = session.query(Profiles).filter(Profiles.user_id == user_id).first()

                data = {
                    'result': protocol.OK,
                    'nickname': profile.nickname,
                    'status_message': profile.status_message,
                    'sex': profile.sex,
                    'birthday': profile.birthday,
                    'weight': profile.weight,
                    'height': profile.height,
                    'user_tag': profile.user_tag,
                    'img_path': profile.profile_img_path
                }
                return jsonify(data)
        else:
            return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    else:
        # 헤더에 인증정보가 없을 때
        return jsonify({}), 400
    
def verify_access_token(access_token):
    decoded = jwt.decode(access_token, '221124104', algorithms='HS256')
    iat = datetime.fromtimestamp(decoded['iat'])
    exp = datetime.fromtimestamp(decoded['exp'])
    
    print(access_token)
    with Session(current_app.database) as session:
        DB_token = session.query(AccessTokens).filter(AccessTokens.access_token == access_token).first()

        if DB_token:
            kst = pytz.timezone('Asia/Seoul')
            exp_time_str = DB_token.access_token_expiration_time.strftime('%Y-%m-%d %H:%M:%S')
            exp_time_kst = datetime.strptime(exp_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC).astimezone(kst)

            # 만료시간 확인
            if exp_time_kst > korea_now_time():
                # 토큰이 변형되지 않았는지 검증
                if DB_token.access_token_issued_at == iat and DB_token.access_token_expiration_time == exp:
                    return DB_token.user_id
                else:
                    pass
                    # print("변형된 엑세스 토큰")
            else:
                pass
                # print("엑세스 토큰 만료")
        else:
            pass
            # print('엑세스토큰 검색결과 없음')
    return None