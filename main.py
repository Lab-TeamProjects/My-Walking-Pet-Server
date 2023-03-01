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

app = create_app()
# 소켓 이벤트 핸들러 등록
from app.socket_views import socket_bp, socketio
#socketio.on_namespace(socket_bp)
app.register_blueprint(socket_bp)

oauth = OAuth(app)

goolge = oauth.remote_app(
    'google',
    consumer_key='YOUR_CLIENT_ID',
    consumer_secret='YOUR_CLIENT_SECRET',
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth'
)

socketio.init_app(app, cors_allowed_origins="*")


if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)