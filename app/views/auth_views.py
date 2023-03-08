# 블루포인트
from flask import Blueprint
from flask import current_app

# MySQl 연결
from sqlalchemy import text

# 이메일 발송
import smtplib
from email.message import EmailMessage

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

bp = Blueprint('auth', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'


# 한국시간 리턴
def korea_now_time():
    kst = pytz.timezone('Asia/Seoul')
    utc_now = datetime.utcnow()
    return utc_now.astimezone(kst)

# 엑세스 토큰 발급
def generate_access_token(user_id):
    with current_app.database.connect() as conn:
        stmt = "SELECT uuid FROM users WHERE user_id='" + user_id +"'"
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
    _email = request.json['email']
    _password = request.json['password']

    # 솔트값 생성
    salt = secrets.token_hex(32)
    _password += salt
    # 비번 + 솔트 해시값 얻기
    hash_pw = hashlib.sha256(_password.encode()).hexdigest()

    # users 테이블에 insert
    with current_app.database.connect() as conn:
        stmt = f"INSERT INTO users(email, uuid) VALUES('{_email}', REPLACE(UUID(), '-', ''))" 
        result = conn.execute(text(stmt))
        conn.commit()
        user_id = result.lastrowid

        kst_now = korea_now_time()
        # password 저장
        stmt = f"""INSERT INTO passwords(user_id, password, salt, update_date)
                    VALUES('{user_id}', '{hash_pw}', '{salt}', '{kst_now}')"""
        conn.execute(text(stmt))
        conn.commit()

    # 인증 메일 전송
    email_verification(user_id, _email)
    return jsonify({'msg': '가입완료'})

# 인증 메일 전송
def email_verification(user_id, email):
    # 인증 토큰 생성 후 DB 입력
    _token = secrets.token_hex(32)      # 결과값 자리수 nbyte*x

    kst_now = korea_now_time()
    iat = kst_now                                  # 발급 시간
    exp = kst_now + timedelta(days=1)              # 만료 시간

    with current_app.database.connect() as conn:
        stmt = f"""INSERT INTO email_verification_tokens(user_id, token, token_issued_at, token_expiration_time)
                VALUES('{user_id}', '{_token}', '{iat}', '{exp}')"""
        conn.execute(text(stmt))
        conn.commit()

    # 인증 메일 발송
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    # TLS 암호화
    smtp.starttls()
    # 이메일 로그인
    smtp.login('yjnnn0011@gmail.com', 'riccnlfbvaxrgfmd')
    # 메일 작성
    msg = EmailMessage()
    msg.set_content(svrURL + f'mailauth?authToken={_token}')
    msg['Subject'] = '[MyWalkingPet] 회원가입 이메일 인증'
    msg['From'] = 'yjnnn0011@gmail.com'
    msg['To'] = email

    # 메일 전송
    smtp.send_message(msg)
    # 이메일 연결 종료
    smtp.quit()


# 이메일 중복검사 함수
@bp.route("/check-email-duplication", methods=['POST'])
def check_email_duplication():
    _email = request.json['email']
    # email 검색
    stmt = "SELECT email FROM users WHERE email='" + _email +"'"
    with current_app.database.connect() as conn:
        row = conn.execute(text(stmt)).fetchone()
  
        if row:
            return jsonify({'msg': '중복된 이메일'})
        else:
            return jsonify({'msg': '사용가능한 이메일'})
        


# 이메일 인증 페이지(완료되면 authStatus 변경)
@bp.route('/mailauth', methods=['GET'])
def mailauth():
    _authToken = request.args.get('authToken')

    with current_app.database.connect() as conn:
        stmt = f"SELECT * FROM email_verification WHERE token='{_authToken}'"
        # .fetchone(): 검색결과가 None인지 구분 해주는 메소드
        row = conn.execute(text(stmt)).fetchone()
        if row:
            # 검색 결과가 있을 때 처리
            user_id = row.user_id
            iat = row.token_issued_at
            exp = datetime.strftime(row.token_expiration_time, '%Y-%m-%d %H:%M:%S')

            if exp < datetime.now():
                # 만료 시간보다 현재 시간이 빠를 때
                stmt = f"UPDATE users SET authSatus = 1 WHERE user_id='{user_id}'"
                conn.execute(text(stmt))
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
            return jsonify({'msg': '존재하지 않는 아이디입니다.'})
        user_id = row.user_id
        uuid = row.uuid

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
            return jsonify({'msg': '잘못된 비밀번호.'}), 401

    print(_email + "님이 로그인하였습니다.")
    access_token = generate_access_token(str(user_id))

    return jsonify({'access_token': access_token})