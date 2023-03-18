from flask      import Flask
from sqlalchemy import create_engine
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy.pool import QueuePool

from app.routes import routes_list

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = '221124104'
    
    app.debug = True

    app.config.from_pyfile('config.py')
    # db.init_app(app)
    database = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], poolclass=QueuePool, pool_size=5, max_overflow=10, pool_recycle=3600)
    app.database = database

    # 라우트 함수 가져오기
    app = routes_list(app)

    return app