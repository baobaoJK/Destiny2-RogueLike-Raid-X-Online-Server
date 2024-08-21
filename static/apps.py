from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3

room_list = []  # 用来存储房间列表

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/card_list', methods=['GET'])
def card_list():
    conn = sqlite3.connect('../database/raid.db')
    c = conn.cursor()
    cursor = c.execute("SELECT * FROM card_list")

    list = []
    for row in cursor:
        card = Card(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10])

        list.append(card.to_dict())

    conn.close()

    return jsonify(list)


@app.route('/card_list/<int:type_num>', methods=['GET'])
def card_list_by_type(type_num):
    conn = sqlite3.connect('../database/raid.db')
    c = conn.cursor()
    type = card_type_list[type_num]
    sql = f"SELECT * FROM {type}"
    cursor = c.execute(sql)

    list = []
    for row in cursor:
        card = Card(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10])

        list.append(card.to_dict())

    conn.close()

    return jsonify(list)


@socketio.on('message')
def handle_message(msg):
    print(f"{msg['username']} sent: {msg['message']}")
    emit('message', f"{msg['username']}: {msg['message']}", broadcast=True)


@app.route('/logout', methods=['POST'])
def logout(user):
    username = user['username']
    print(f"{user} 要退出服务器")
    if username in connected_users:
        print(f"{username} 退出了服务器")
        connected_users.remove(username)
        emit('message', f"{username} has left the chat.", broadcast=True)

    return 1


