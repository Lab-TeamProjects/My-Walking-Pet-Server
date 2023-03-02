# 블루포인트 관련(파일 정리를 위한)
from flask import Blueprint
from flask import current_app

# MySQl 연결 관련
from sqlalchemy import text, MetaData, update, exc

# 클라이언트 통신 관련
from flask import render_template, request, redirect, url_for, session

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


bp = Blueprint('main', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'

def generate_access_token(uuid):
    payload = {
        'sub': uuid,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    access_token = jwt.encode(payload, '221124104', algorithm='HS256')
    return access_token.decode('utf-8')

@bp.route("/socket")
def socket_test():
    return render_template('socketTest.html')

@bp.route("/token")
def create_token():
    return secrets.token_hex(16)

@bp.route('/hello')
def hello_pybo():
    return 'Hello, Pybo!'

@bp.route('/')
def index():
    if 'email' in session:
        return session['email'] + '님 환영합니다.'
    return 'Pybo index'

@bp.route("/sign-up-page")
def sign_up_page():
    return render_template('sign-up.html')

@bp.route("/sign-up", methods=['POST'])
def sign_up():
    _email = request.json['email']
    _password = request.json['password']

    # email 검색
    stmt = "SELECT email FROM users WHERE email='" + _email +"'"
    with current_app.database.connect() as conn:
        result = conn.execute(text(stmt)).all()
    if len(result) > 0:
        return '이미 사용중인 이메일입니다.'

    # 이메일, 비밀번호 DB 입력
    stmt = f"INSERT INTO users(email, password) VALUES('{_email}', '{_password}')" 
    with current_app.database.connect() as conn:
        result = conn.execute(text(stmt))
        conn.commit()

    # uuid 값 가져오기
    stmt = "SELECT uuid FROM users WHERE email='" + _email +"'"
    with current_app.database.connect() as conn:
        for row in conn.execute(text(stmt)):
            _uuid = row.uuid
    
    # 인증 토큰 생성 후 DB 입력
    _token = secrets.token_hex(16)
    stmt = f"INSERT INTO signup_auths(uuid, authToken) VALUES('{_uuid}', '{_token}')"
    with current_app.database.connect() as conn:
        result = conn.execute(text(stmt))
        conn.commit()

    # 인증 메일 발송
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    # TLS 암호화
    smtp.starttls()
    # 이메일 로그인
    smtp.login('yjnnn0011@gmail.com', 'riccnlfbvaxrgfmd')
    # 메일 작성
    msg = EmailMessage()
    msg.set_content(svrURL + f'mailauth?email={_email}&authToken={_token}')
    msg['Subject'] = '[MyWalkingPet] 회원가입 이메일 인증'
    msg['From'] = 'yjnnn0011@gmail.com'
    msg['To'] = _email

    smtp.send_message(msg)
    smtp.quit()

    return 'sign-up'

@bp.route('/mailauth', methods=['GET'])
def mailauth():
    _email = request.args.get('email')
    _authToken = request.args.get('authToken')

    stmt = "SELECT uuid FROM users WHERE email='" + _email +"'"
    with current_app.database.connect() as conn:
        for row in conn.execute(text(stmt)):
            _uuid = row.uuid

    # 토큰 검색
    stmt = f"SELECT authToken, issueTime FROM signup_auths WHERE uuid='{_uuid}'"
    with current_app.database.connect() as conn:
        for row in conn.execute(text(stmt)):
            authToken = row.authToken
            issueTime = row.issueTime

    how_long = datetime.now() - issueTime
    if _authToken == authToken:
       if how_long.seconds // 60 <= 5:     
            stmt = f"UPDATE users SET authSatus = 1 WHERE uuid='{_uuid}'"
            with current_app.database.connect() as conn:
                result = conn.execute(text(stmt))
                conn.commit()
       else:
           return '토큰이 만료되었습니다.'
    return '이메일 인증 완료. 회원가입 되었습니다.'
        
@bp.route('/login-page')
def login_info():
    return render_template('login.html')

@bp.route('/login', methods=['POST'])
def login():
    _email = request.form['email']
    _password = request.form['password']
    if (_email == 'admin' and _password == 'admin'):
        return 'login!'
    else:
        if 'email' in session:
            print(_email + "님은 이미 로그인 중입니다.")
            return '이미 로그인 중입니다.'
        else:
            print(_email + "님이 로그인하였습니다.")
            session['email'] = _email
            return '로그인 성공'

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