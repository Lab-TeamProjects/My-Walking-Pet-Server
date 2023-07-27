# 블루포인트 관련(파일 정리를 위한)
from flask import Blueprint
from flask import current_app

# MySQl 연결 관련
from sqlalchemy import text

# 클라이언트 통신 관련
from flask import render_template, request

# 소켓 통신
from flask_socketio import emit

# 시간 객체
from datetime import datetime

# Token생성 JWT라이브러리
import jwt

# json형식 http응답
from flask import jsonify

bp = Blueprint('main', __name__, url_prefix='/')

svrURL = 'http://203.232.193.164:5000/'
#svrURL = 'http://localhost:5000/'



@bp.route("/socket")
def socket_test():
    return render_template('socketTest.html')

@bp.route('/')
def index():
    return 'Pybo index'

@bp.route('/login-test', methods=['GET'])
def login_test():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        # Authorization 헤더가 존재하는 경우 처리
        access_token = auth_header.split(" ")[1]

        # 엑세스 토큰 디코딩 및 검증
        decoded = jwt.decode(access_token, '221124104', algorithms='HS256')
        # iat = decoded['iat']
        # exp = decoded['exp']
        iat = datetime.fromtimestamp(decoded['iat'])
        exp = datetime.fromtimestamp(decoded['exp'])

        with current_app.database.connect() as conn:
            stmt = f"SELECT * FROM access_tokens WHERE access_token='{access_token}'"
            row = conn.execute(text(stmt)).fetchone()

            if row:
                user_id = row.user_id
                db_iat = row.access_token_issued_at
                db_exp = row.access_token_expiration_time

                print(f"DB 발급시간: {db_iat}, 토큰 발급시간: {iat}")
                print(f"DB 만료시간: {db_exp}, 토큰 만료시간: {exp}")

                # access token의 payload 정보가 db의 정보와 같은지
                # if db_iat == iat and db_exp == exp:
                #     kst_now = korea_now_time()
                #     # 만료 기간 지났는지 확인
                #     if db_exp > kst_now:
                #         pass

                stmt = f"SELECT * FROM users WHERE user_id='{user_id}'"
                row = conn.execute(text(stmt)).fetchone()
                
                email = row.email

                return jsonify({'msg': "'" + email + "'님 안녕하세요."})
            else:
                return jsonify({'msg': '유효한 토큰이 아닙니다.'}), 401
    else:
        return jsonify({'msg': '인증 정보가 존재하지 않습니다.'}), 401