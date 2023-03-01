from flask      import Flask
from sqlalchemy import create_engine
from datetime import timedelta


# 블루 프린트 리스트



def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = '221124104'
    
    app.debug = True

    app.config.from_pyfile('config.py')
    database = create_engine(app.config['DB_URL'], max_overflow=0)
    app.database = database
    database = 'mywalkingpet'
    
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60) # 로그인 시간 60분

    from .views import main_views
    app.register_blueprint(main_views.bp)

    # 라우트 함수 등록 후 리턴
    return app