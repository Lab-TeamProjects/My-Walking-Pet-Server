from flask import Blueprint
from flask import current_app
from sqlalchemy.orm import Session
from flask_apscheduler import APScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler

from datetime import datetime
from app.sql_models import AccessTokens
from .auth import now_kr, to_pytz
from .extensions import scheduler

time_cnt = 0
bp = Blueprint('scheduler', __name__)

# 디버그 모드로 서버를 열면 스케줄러가 두번작동함 (멀티스레드로 되는듯.. 그래서 이상함)


@scheduler.task(
    "interval",
    id="job_sync",
    seconds=5,
    max_instances=1,
    start_date="2000-01-01 12:19:00",
)
def remove_expired_tokens():
    with scheduler.app.app_context():
        with Session(current_app.database) as session:
            tokens = session.query(AccessTokens).filter(AccessTokens.access_token_expiration_time < now_kr()).all()
            if len(tokens) > 0:
                for token in tokens:
                    session.delete(token)
                    print(token.user_id, "의 토큰 삭제")
                try:
                    session.commit()
                    print("만료된 엑세스 토큰 삭제 완료")
                except:
                    session.rollback()
                    print("엑세스토큰 제거 스케줄링 오류 발생")

@scheduler.task(
    "interval",
    id="job_2",
    seconds=1,
    max_instances=1,
    start_date="2000-01-01 12:19:00",
)
def timer():
    global time_cnt
    time_cnt += 1
    print(time_cnt)
