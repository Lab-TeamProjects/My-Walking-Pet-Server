from app import create_app
from flask_oauthlib.client import OAuth

import eventlet
eventlet.monkey_patch()

# 설치 모듈 목록
# flask
# sqlalchmey
# mysql-connector
# pyjwt
# Flask-OAuthlib x
# flask-sqlalchemy

app = create_app()
# 소켓 이벤트 핸들러 등록
from app.socket_views import socket_bp, socketio
#socketio.on_namespace(socket_bp)
#app.register_blueprint(socket_bp)

socketio.init_app(app, cors_allowed_origins="*")

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)