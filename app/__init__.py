from flask      import Flask
from sqlalchemy import create_engine
from datetime import timedelta

from app.routes import routes_list


def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = '221124104'
    
    app.debug = True

    app.config.from_pyfile('config.py')
    database = create_engine(app.config['DB_URL'], max_overflow=0)
    app.database = database
    database = 'mywalkingpet'
    
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60) # 로그인 시간 60분

    # 라우트 함수 가져오기
    app = routes_list(app)

    return app