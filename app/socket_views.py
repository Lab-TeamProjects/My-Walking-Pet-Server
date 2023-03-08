# 블루프린트 관련(파일 정리를 위한)
from flask import Blueprint

# 소켓 통신
from flask_socketio import SocketIO, emit
from flask      import Flask
from flask import session

import asyncio

import eventlet
eventlet.monkey_patch()

socket_bp = Blueprint('socketio', __name__)

socketio = SocketIO(async_mode='eventlet')

HOST = 'localhost'
PORT = 8000

# async def handle_client(reader, writer):
#     # 클라이언트와의 소켓 통신을 위한 코루틴 함수
#     while True:
#         # 클라이언트로부터 데이터를 읽음
#         data = await reader.read(1024)
#         if not data:
#             # 데이터를 더 이상 받을 수 없을 때, 소켓 종료
#             writer.close()
#             break
#         # 데이터를 처리
#         message = data.decode().strip()
#         print(f"Received message: {message}")
#         # 클라이언트에게 데이터를 보냄
#         writer.write(f"You said: {message}\n".encode())
#         await writer.drain()

# async def run_server():
#     # 이벤트 루프 생성
#     loop = asyncio.get_running_loop()

#     # 비동기 TCP 서버 생성
#     server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)

#     # 서버 주소 출력
#     print(f"Serving on {server.sockets[0].getsockname()}")

#     # 이벤트 루프에서 비동기 코루틴 등록
#     async with server:
#         await server.serve_forever()


@socketio.on('connect', namespace='/test')
def handle_connect():
    print('connected')

@socketio.on('disconnect', namespace='/test')
def handle_disconnect():
    print('disconnected')

@socketio.on('my_event', namespace='/test')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    emit('my_response', json)