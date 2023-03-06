# 블루포인트 관련(파일 정리를 위한)
from flask import Blueprint
from flask import current_app

# MySQl 연결 관련
from sqlalchemy import text

# 클라이언트 통신 관련
from flask import render_template, request, redirect, url_for

# 소켓 통신
from flask_socketio import emit

# 토큰 생성
import secrets      

# 이메일 발송
import smtplib
from email.message import EmailMessage

# 시간 객체
from datetime import datetime, timedelta

# Token생성 JWT라이브러리
import jwt

# json형식 http응답
from flask import jsonify

# SHA256
import hashlib

bp = Blueprint('main', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'

def generate_access_token(user_id):
    stmt = "SELECT uuid FROM users WHERE ='" + user_id +"'"
    with current_app.database.connect() as conn:
        for row in conn.execute(text(stmt)):
            uuid = row.uuid

    iat = datetime.utcnow()
    exp = datetime.utcnow() + timedelta(days=1)
    payload = {
        'sub': uuid,
        'iat': iat,
        'exp': exp
    }
    access_token = jwt.encode(payload, '221124104', algorithm='HS256').decode('utf-8')

    # DB에 access token 저장
    with current_app.database.connect() as conn:
        stmt = f"""REPLACE INTO access_tokens(user_id, access_token, access_token_issued_at, aceess_token_expiration_time)
                VALUES('{user_id}', '{access_token}', '{iat}', '{exp}')"""
        conn.execute(text(stmt))

    return access_token

@bp.route("/socket")
def socket_test():
    return render_template('socketTest.html')

@bp.route('/hello')
def hello_pybo():
    return 'Hello, Pybo!'

@bp.route('/')
def index():
    return 'Pybo index'

@bp.route("/sign-up-page")
def sign_up_page():
    return render_template('sign-up.html')

# 이메일 중복검사 함수
@bp.route("/sign-up/check-email-duplication", methods=['POST'])
def check_email_duplication():
    _email = request.json['email']
    # email 검색
    stmt = "SELECT email FROM users WHERE email='" + _email +"'"
    with current_app.database.connect() as conn:
        result = conn.execute(text(stmt)).all()
    if len(result) > 0:
        return jsonify({'msg': '중복된 이메일', 'result': 0})
    else:
        return jsonify({'msg': '사용가능한 이메일', 'result': 1})

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
        conn.execute(text(stmt))
        user_id = conn.lastrowid

    # password 저장
    with current_app.database.connect() as conn:
        stmt = f"""INSERT INTO password(user_id, hash_password, salt, update_date)
                    VALUES('{user_id}', '{hash_pw}', '{salt}', NOW())"""
        conn.execute(text(stmt))

    # 인증 메일 전송
    email_verification(user_id, _email)
    return jsonify({'msg': '가입완료'})

def email_verification(user_id, email):
    # 인증 토큰 생성 후 DB 입력
    _token = secrets.token_hex(32)      # 결과값 자리수 nbyte*x
    iat = datetime.utcnow()                         # 발급 시간
    exp = datetime.utcnow() + timedelta(minutes=5)  # 만료 시간

    with current_app.database.connect() as conn:
        stmt = f"""INSERT INTO email_verification_tokens(user_id, token, token_issued_at, token_expiration_time)
                VALUES('{user_id}', '{_token}', '{iat}', '{exp}')"""
        conn.execute(text(stmt))

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
            
        
@bp.route('/login-page')
def login_info():
    return render_template('login.html')

@bp.route('/login', methods=['POST'])
def login():
    _email = request.form['email']
    _password = request.form['password']

    # email로 user_id, uuid 검색 쿼리
    # user_id로 hash_pw, salt 검색 쿼리
    # _password + salt를 해싱 후 hash_password와 비교
    # 맞으면 password 테이블의 update_date 컬럼 update

    print(_email + "님이 로그인하였습니다.")
    #access_token = generate_access_token(uuid)
    #return jsonify({'access_token': access_token})

@bp.route('/mypage')
def login():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        # Authorization 헤더가 존재하는 경우 처리
        auth_token = auth_header.split(" ")[1]
        
    else:
        # Authorization 헤더가 존재하지 않는 경우 처리
        pass

@bp.route("/show-all")
def show_teble():
    s = ''
    with current_app.database.connect() as conn:
        for row in conn.execute(text("select * from users")):
            s += str(row._asdict()) + '<br>'
    return s