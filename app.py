from flask_socketio import emit
from socketio_instance import socketio, app

import services


# # 连接触发
# @socketio.on('connect')
# def handle_connect():
#     current_connections = len(socketio.server.manager.rooms['/'])
#     print(f"Current number of connections: {current_connections}")
#     emit('connection_count', {'count': current_connections})
#     emit('message', {'type': 'message', 'stage': [1, 2]})


# 退出链接
# @socketio.on('disconnect')
# def handle_disconnect():
#     pass
#
#
# @socketio.on('disconnect')
# def handle_disconnect():
#     print("disconnect")
    # room_list = []
    # username = request.sid
    # print(f"{request}")
    # if username in connected_users:
    #     connected_users.remove(username)
    #     emit('message', f"{username} has left the chat.", broadcast=True)


# Flask
@app.route('/')
def index():
    return "Hello, World!"


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
