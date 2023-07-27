from app import create_app

import eventlet
eventlet.monkey_patch()
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)