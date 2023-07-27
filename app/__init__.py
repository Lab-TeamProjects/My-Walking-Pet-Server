from flask      import Flask
from sqlalchemy import create_engine
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy.pool import QueuePool

from app.routes import set_routes_list
from flask_apscheduler import APScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .extensions import scheduler

db = SQLAlchemy()
#scheduler = APScheduler()

def create_app(test_config=None):
    app = Flask(__name__)

    app.secret_key = '221124104'
    
    app.debug = True

    app.config.from_pyfile('config.py')
    app.config['SCHEDULER_API_ENABLED'] = True
    # db.init_app(app)
    database = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], poolclass=QueuePool, pool_size=5, max_overflow=10, pool_recycle=3600)
    app.database = database

    scheduler.init_app(app)
    db.init_app(app)

    # 라우트 함수 블루프린트 연결
    app = set_routes_list(app)
    with app.app_context():
        from . import schedule_tasks
        scheduler.start()
        #scheduler.add_job(id='my_task', func=tasks.remove_expired_tokens, trigger='interval', seconds=1)
        # with app.app_context():
        #     scheduler.init_app(app)
        #     scheduler.add_job(func=scd.remove_expired_tokens, trigger=IntervalTrigger(seconds=10), id='remove_expired_tokens')
        #     scheduler.add_job(func=scd.timer, trigger=IntervalTrigger(seconds=1), id='timer')
            
        #     scheduler.start()


        return app