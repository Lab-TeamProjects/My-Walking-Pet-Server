# 블루포인트
from flask import Blueprint
from flask import current_app

# MySQl 연결
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
# 데이터 모델 객체
from ..sql_models import *
# from models import Users, Passwords, Profiles, ProfilePhotos, Moneys
# from models import EmailVerificationTokens, AccessTokens, password_reset_tokens

# 사용자 지정 Exception 객체
from ..exception import *
# 프로토콜 선언 파일
from .. import protocol
# 인증 함수
from ..auth import *

# 환경 변수
from dotenv import load_dotenv

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

# http 요청, 응답
from flask import jsonify, request

# 한국 시간 계산
import pytz

# 메일 전송 api
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# 이미지 인코딩
import base64

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

    # print(f'해쉬된 비밀번호: {hash_pw}')
    # 신규 유저 데이터 객체 생성

    with Session(current_app.database) as session:
        # 신규유저 정보 삽입
        new_user = Users(email=_email)
        session.add(new_user)
        session.commit()

        # 비밀번호 정보 삽입
        new_pw = Passwords(
            user_id=new_user.user_id,
            password=hash_pw,
            salt=salt,
            update_date= korea_now_time()
        )
        session.add(new_pw)
        try:
            session.commit()
        except IntegrityError as e:
            print(e) 
            session.rollback()
            return jsonify({'result': protocol.DATABASE_ERROR})
        

        # 인증 링크 생성
        try:
            auth_url = email_verification(new_user.user_id)
        except IntegrityError:
            session.delete(new_user)
            session.commit()
            return jsonify({'result': protocol.DATABASE_ERROR})
            
        # 인증 메일 발송
        try:
            send_email(_email,'[MyWalkingPet] 회원가입 이메일 인증', auth_url)
            print(f"'{new_user.email}'님의 회원가입했습니다.")
            return jsonify({'result': protocol.OK })
        except SendEmailFail:
            session.delete(new_user)
            session.commit()
            return jsonify({'result': protocol.EMAIL_SEND_FAIL})
        

# 메일 발송
def send_email(recipient, subject, body):
    message = Mail(
        from_email=os.environ.get('EMAIL'),
        to_emails=recipient,
        subject=subject,
        html_content=body)

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # print(response.status_code)
        # print(response.body)
        # print(response.headers)
        
    except Exception as e:
        print('메일전송실패: ' + str(e))
        raise SendEmailFail("Send email failed")

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

def email_check(email):
    with Session(current_app.database) as session:
        result = session.query(Users).filter(Users.email == email).first()

        if result:
            return True
        else:
            return False
        

# 이메일 중복검사 함수
@bp.route("/check-email-duplication", methods=['POST'])
def check_email_duplication():
    _email = request.json['email']
    # print(_email)
    # email 검색
    if email_check(_email):
        return jsonify({'result': protocol.EMAIL_IS_DUPLICATION})        
    else:
        return jsonify({'result': protocol.OK})    

# 이메일 인증 페이지(완료되면 authStatus 변경)
@bp.route('/mailauth', methods=['GET'])
def mail_auth():
    _authToken = request.args.get('authToken')

    with Session(current_app.database) as session:
        mail_auth_token = session.query(EmailVerificationTokens).filter(EmailVerificationTokens.token == _authToken).first()

        if mail_auth_token:
            kst = pytz.timezone('Asia/Seoul')
            expiration_time_str = mail_auth_token.token_expiration_time.strftime('%Y-%m-%d %H:%M:%S')
            expiration_time_kst = datetime.strptime(expiration_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC).astimezone(kst)

            # 토큰의 만료기간이 지나지 않았을 때
            if expiration_time_kst > korea_now_time():
                user = session.query(Users).filter(Users.user_id == mail_auth_token.user_id).first()
                user.authStatus = True
                # 유저 데이터 초기화 작업
                tables_init(user.user_id)
                session.commit()

                return jsonify({'result': 'ok'})
    return jsonify({'result': 'fail'})

def tables_init(user_id):
    new_money = Moneys(
        user_id=user_id
    )
    with Session(current_app.database) as session:
        session.add(new_money)

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
        kst = pytz.timezone('Asia/Seoul')
        exp_time_str = access_token.access_token_expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        exp_time_kst = datetime.strptime(exp_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC).astimezone(kst)

        # 만료시간 확인
        print(exp_time_str)
        print(korea_now_time())
        if exp_time_kst > korea_now_time():
            # 만료안됨
            print(f"'{user.email}' 유저의 만료되지 않은 엑세스 토큰이 이미 존재하므로 기존의 토큰을 전송합니다.")
            print(access_token.access_token)
            return jsonify({'result': protocol.OK, 'access_token': access_token.access_token})
    
    print(f"'{user.email}' 유저의 엑세스 토큰이 검색되지 않았으므로 엑세스 토큰을 발급합니다.")

    access_token = generate_access_token(user.user_id, user.uuid)
    print(access_token)
    print(_email + "님이 로그인하였습니다.")

    return jsonify({'result': protocol.OK, 'access_token': access_token})

# 엑세스 토큰 발급
def generate_access_token(user_id, uuid):
    kst_now = korea_now_time()
    iat = kst_now
    exp = kst_now + timedelta(days=1)
    print(f"생성된 발급시간: {iat}, 생성된 만료시간: {exp}")

    payload = {
        'user_id': uuid,
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

# 이메일 찾기
@bp.route('/find-email', methods=['POST'])
def email_find():
    _email = request.json['email']
    with Session(current_app.database) as session:
        email = session.query(Users).filter(Users.email == _email).first()
        if email:
            return jsonify({"result": protocol.OK})
        else:
            return jsonify({'result': protocol.FAIL})

# 비밀번호 찾기
@bp.route('/password/reset/request', methods=['POST'])
def pw_reset_request():
    _email = request.json['email']
    print(_email)
    if email_check(_email):
        token = secrets.token_hex(32)
        iat = korea_now_time()
        exp = iat + timedelta(minutes=1)

        with Session(current_app.database) as session:
            user = session.query(Users).filter(Users.email == _email).first()
            old_token = session.query(PasswordResetTokens).filter(PasswordResetTokens.user_id == user.user_id).first()
            if old_token:
                old_token.isVerified = False
                old_token.password_reset_token = token
                old_token.password_reset_token_issued_at=iat
                old_token.password_reset_token_expiration_time=exp
            else: 
                new_token = PasswordResetTokens(
                    user_id=user.user_id,
                    password_reset_token=token,
                    password_reset_token_issued_at=iat,
                    password_reset_token_expiration_time=exp
                )
                session.add(new_token)
            session.commit()
            body = svrURL + f'password/reset/auth?authToken={token}'
            try:
                send_email(_email, '[MyWalkingPet] 비밀번호 변경 인증', body)
                return jsonify({'result': protocol.OK})
            except SendEmailFail:
                session.rollback()
                return jsonify({'result': protocol.EMAIL_SEND_FAIL})

    else:
        return jsonify({'result': protocol.NOT_FOUND_EMAIL})
        

# 비밀번호 변경 이메일 인증 페이지
@bp.route('/password/reset/auth', methods=['GET'])
def pw_reset_auth():
    token = request.args.get('authToken')
    with Session(current_app.database) as session:
        token_data = session.query(PasswordResetTokens).filter(PasswordResetTokens.password_reset_token == token).first()
        # 존재하는 토큰이면
        if token_data:
            kst = pytz.timezone('Asia/Seoul')
            exp_time_str = token_data.password_reset_token_expiration_time.strftime('%Y-%m-%d %H:%M:%S')
            exp_time_kst = datetime.strptime(exp_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC).astimezone(kst)

            # 만료 시간 검증
            if exp_time_kst > korea_now_time():
                token_data.isVerified = True
                session.commit()
                return "인증이 완료되었습니다. 앱으로 돌아가서 비밀번호 변경을 진행해주세요."
            else:
                return "인증시간이 지났습니다. 다시 요청해주세요."
        else:
            return "유효하지 않은 토큰"

# 비밀번호 변경 인증 확인
@bp.route('/password/reset/auth-check', methods=['POST'])
def password_auth_check():
    email = request.json['email']
    with Session(current_app.database) as session:
        user = session.query(Users).filter(Users.email == email).first()
        if not user:
            return jsonify({'result' : protocol.NOT_USER})
        is_auth = session.query(PasswordResetTokens).filter(PasswordResetTokens.user_id == user.user_id).first()
        if is_auth:
            if is_auth.isVerified:
                return ok_json()
            else:
                return jsonify({'result': protocol.NOT_AUTH_PASSWORD_RESET})
        else:
            return jsonify({'result' : protocol.NOT_AUTH_PASSWORD_RESET})

# 비밀번호 변경
@bp.route('/password/reset', methods=['POST'])
def password_reset():
    email = request.json['email']
    password = request.json['password']

    with Session(current_app.database) as session:
        user = session.query(Users).filter(Users.email == email).first()

        # 유저 정보 검색 실패
        if not user:
            return jsonify({'result': protocol.NOT_FOUND_EMAIL})

        is_auth = session.query(PasswordResetTokens).filter(PasswordResetTokens.user_id == user.user_id).first()
        if is_auth:
            if not is_auth.isVerified:
                return jsonify({'result': protocol.NOT_AUTH_PASSWORD_RESET})
        else:
            return jsonify({'result' : protocol.NOT_AUTH_PASSWORD_RESET})

        pw = session.query(Passwords).filter(Passwords.user_id == user.user_id).first()

        # 비밀번호가 검색되지 않음
        if not pw:
            print(f"예외발생: 비밀번호가 검색되지 않는 유저 user_id: {user.user_id}")
            return jsonify({}), 400

        # password + salt를 해싱
        hashed_pw = hashlib.sha256(((password + pw.salt).encode())).hexdigest()

        # 비밀번호 변경
        pw.password = hashed_pw
        session.commit()
    return jsonify({'result': protocol.OK})


# 유저 정보 등록 및 수정
@bp.route('/users/profile', methods=['POST'])
def profile_edit():
    # 헤더 정보 가져오기
    auth_header = request.headers.get('Authorization')
    print(request.data)
    print(request.content_type)
    if auth_header:
        access_token = auth_header.split(" ")[1]
        user_id = verify_access_token(access_token)
        if user_id:
            print(f'인증된 유저입니다. user_id: {user_id}')
            with Session(current_app.database) as session:
                search_profile = session.query(Profiles).filter(Profiles.user_id == user_id).first()

                if search_profile:
                    print('프로필을 수정합니다.')
                    search_profile.nickname = request.json['nickname']
                    search_profile.status_message = request.json['status_message']
                    search_profile.sex = request.json['sex']
                    search_profile.birthday = request.json['birthday']
                    search_profile.weight = request.json['weight']
                    search_profile.height = request.json['height']
                else:
                    print('프로필을 새로 만듭니다.')
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
            print('잘못된 인증정보입니다.')
            return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    return '', 401

# 유저 정보 열람
@bp.route('/users/profile', methods=['GET'])
def profile_view():
    try:
        user_id = get_user_id(request.headers.get('Authorization'))
        with Session(current_app.database) as session:
                profile = session.query(Profiles).filter(Profiles.user_id == user_id).first()
                if profile:
                    data = {
                        'result': protocol.OK,
                        'nickname': profile.nickname,
                        'status_message': profile.status_message,
                        'sex': profile.sex,
                        'birthday': profile.birthday,
                        'weight': profile.weight,
                        'height': profile.height,
                        'user_tag': profile.user_tag
                    }
                    return jsonify(data)
                else:
                    return jsonify({'result': protocol.NOT_FOUND_PROFILE})
    except InvalidAccessToken as e:
        return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    except NoHeaderInfo as e:
        return '', 401
    except ExpiredAccessToken:
        return jsonify({'result': protocol.EXPIRED_ACCESS_TOKEN})


    # 헤더 정보 가져오기
    auth_header = request.headers.get('Authorization')
    if auth_header:
        access_token = auth_header.split(" ")[1]

        user_id = verify_access_token(access_token)
        if user_id:
            with Session(current_app.database) as session:
                profile = session.query(Profiles).filter(Profiles.user_id == user_id).first()
                if profile:
                    data = {
                        'result': protocol.OK,
                        'nickname': profile.nickname,
                        'status_message': profile.status_message,
                        'sex': profile.sex,
                        'birthday': profile.birthday,
                        'weight': profile.weight,
                        'height': profile.height,
                        'user_tag': profile.user_tag
                    }
                    return jsonify(data)
                else:
                    return jsonify({'result': protocol.NOT_FOUND_PROFILE})
        else:
            return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    else:
        # 헤더에 인증정보가 없을 때
        return '', 401

# 프로필 사진 업로드
@bp.route('/users/profile/photo', methods=['POST'])
def profile_img_upload():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        access_token = auth_header.split(" ")[1]

        user_id = verify_access_token(access_token)
        print(user_id)
        if user_id:
            encode_img = request.json['image']
            # 잘못된 이미지 요청
            try:
                decoded_img = base64.b64decode(encode_img)
            except ValueError:
                return jsonify({'result': protocol.INVALID_IMAGE_DATA})
            
            # 파일명(user_id) 암호화
            heshed_id = hashlib.sha256((str(user_id).encode())).hexdigest()

            with open(f'C:\Profile_Photos\{heshed_id}.png', 'wb') as f:
                f.write(decoded_img)
            
            with Session(current_app.database) as session:
                photo = session.query(ProfilePhotos).filter(ProfilePhotos.user_id == user_id).first()

                if photo:
                    photo.image_path = f'{heshed_id}.png'
                else:
                    new_photo = ProfilePhotos(
                        user_id = user_id,
                        image_path = f'{heshed_id}.png'
                    )
                    session.add(new_photo)
                session.commit()
            return jsonify({'result': protocol.OK})
        else:
            return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    return '', 401
    
@bp.route('/users/profile/photo', methods=['GET'])
def profile_img_view():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        access_token = auth_header.split(" ")[1]

        user_id = verify_access_token(access_token)
        if user_id:
            with Session(current_app.database) as session:
                photo = session.query(ProfilePhotos).filter(ProfilePhotos.user_id == user_id).first()
                
                if photo:
                    with open(f'C:\Profile_Photos\{photo.image_path}', 'rb') as f:
                        imgdata = f.read()
                    # base64 인코딩된 이미지 데이터 인코딩
                    imgdata_encoded = base64.b64encode(imgdata)
                    return jsonify({'result': protocol.OK, 'image': imgdata_encoded.decode('utf-8')})
                else:
                    return jsonify({'result': protocol.OK, 'image': ''})
        else:
            return jsonify({'result': protocol.INVALID_ACCESS_TOKEN})
    return '', 401
