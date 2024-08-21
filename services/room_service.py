from flask import jsonify, request
from flask_socketio import emit, join_room, leave_room, send

import utils
from entitys.player import Player
from entitys.room import Room
from socketio_instance import socketio, app

# 存放房间的列表
room_list = {}


# 返回房间列表
def get_room_list():
    return room_list


# 返回房间
def get_room(room_id):
    return room_list[room_id]


# 返回当前所有房间列表的信息
def get_room_list_info():
    room_list_info = []
    for r_name, r_info in room_list.items():
        if r_info.room_status != 'playing':
            r = {
                "playerName": r_info.room_owner,
                "players": len(r_info.players),
                "roomId": r_info.room_id
            }
            room_list_info.append(r)
    # return [room.to_dict() for room_name, room in room_list.items() if room.room_status != 'playing']
    return room_list_info


# 获取玩家实体
def get_player(room_id, player_name):
    room = room_list[room_id]
    player = room.players[player_name]['playerConfig']
    return player


# 根据 role_id 获取玩家
def get_player_by_role_id(room_id, role_id):
    room = room_list[room_id]
    player = next((p_config['playerConfig'] for p_name, p_config in room.players.items() if
                   p_config['playerConfig'].role_id == role_id), None)
    return player


# 输出当前在房间的玩家
def show_online_list(room):
    print("--------------------------------")
    print(f"当前房间 {room.room_id} 有：")
    for p in room.players:
        print(p)
    print("--------------------------------")


# 连接触发
@socketio.on('connect')
def handle_connect():
    current_connections = len(socketio.server.manager.rooms['/'])
    print(f"Socket 连接数量: {current_connections}")
    emit('connection_count', {'count': current_connections})
    emit('message', {'type': 'message', 'stage': [1, 2]})
    emit('message', {'type': 'roomList', 'roomList': get_room_list_info()})


# 创建房间
@socketio.on('createRoom')
def handle_create_room(data):
    # 随机生成 4 位房间名
    room_id = utils.random_room_name()
    # 玩家信息
    player_data = {
        "role": data['player']['role'],
        "roleId": data['player']['roleId'],
        "playerName": data['player']['playerName'],
    }
    # 创建一个玩家对象
    player = Player(player_data)

    # 判断是否有房间了
    # for r_name in room_list:
    #     if room_list[r_name].room_owner == player.player_name:
    #         room_id = get_player_room_id(player.player_name)
    #         room = room_list[room_id]
    #         emit('message',
    #              {'type': 'hasRoom', 'message': f'你已经有一个房间了', 'room_id': room_id})
    #         return

    print(f"玩家 {player.player_name} 创建房间 {room_id}")

    # 创建一个房间，并设置所有者
    room_list[room_id] = Room(room_id, player.player_name)

    # 传递信息
    data = {
        'roomId': room_id,
        'player': player
    }
    handle_join_room(data)


# 加入房间
@socketio.on('joinRoom')
def handle_join_room(data):
    # 用户信息
    room_id = data['roomId']
    player_data = data['player']

    # 判断用户信息是否转换
    if isinstance(player_data, Player):
        player_data = data['player'].to_dict()

    # 创建一个玩家对象
    player = Player(player_data)

    if room_id is None or player is None:
        return

    if not (room_id in room_list):
        emit('message', {'type': 'idNone', 'message': f'房间号不存在'})
        return

    # 获取房间
    room = room_list[room_id]

    # 判断玩家是不是队长
    if room.room_owner == player.player_name:
        player.is_captain = True

    # 判断玩家是否在房间中
    if player.player_name in room.players:
        join_room(room)
        room.players[player.player_name]['sid'] = request.sid
        room.players[player.player_name]['playerConfig'].sid = request.sid
        room.players[player.player_name]['playerConfig'].room_id = room_id
        room.players[player.player_name]['playerConfig'].room = room
        # emit('message', {'message': f'你已经在房间中了'})
        return

    # 判断加入该房间前人数是否为 Max
    if Room.get_players(room) < Room.MAX_USERS_PER_ROOM:
        # 加入房间
        join_room(room)

        # 添加玩家
        room.players[player.player_name] = {'sid': request.sid, 'playerConfig': player}
        room.players[player.player_name]['playerConfig'].sid = request.sid
        room.players[player.player_name]['playerConfig'].room_id = room_id
        room.players[player.player_name]['playerConfig'].room = room
        print(f"玩家 {player.player_name} 加入 {room_id} 房间成功 sid 是 {request.sid}")
        show_online_list(room)

        send({'type': 'joinRoom', 'message': f"玩家 {player.player_name} 加入房间", 'roomId': room_id, 'stage': [1, 2]},
             to=room)

        # 分发信息
        raid_map = room.get_raid_config()
        if raid_map is not None and raid_map['raidName'] is not None:
            emit('message',
                 {'type': 'setMap', 'message': f"已选择 {raid_map['raidName']} 进行本次突袭", 'stage': [1, 2]})
    else:
        emit('message', {'message': '房间已满无法加入'})

    emit('message', {'type': 'roomList', 'roomList': get_room_list_info()}, broadcast=True)


# 退出房间
@socketio.on('leaveRoom')
def handle_leave_room(data):
    # 房间 id
    room_id = data['roomId']
    # 玩家信息
    player_name = data['playerName']

    if room_id is None or player_name is None:
        return

    if not (room_id in room_list):
        return

    room = get_room(room_id)

    if player_name not in room.players:
        return

    # 退出房间
    leave_room(room)

    # 移除玩家
    # for index, p in enumerate(room.players):
    #     if p['playerName'] == player.player_name:
    del room.players[player_name]

    print(f"玩家 {player_name} 退出 {room_id} 房间了 ")

    # 替换位置信息
    for i, s in enumerate(room.seats):
        if s is None:
            continue

        if s['playerName'] == player_name:
            room.seats[i] = None

    send({'type': 'leaveRoom', 'message': f'{player_name} 离开了房间', 'stage': [1, 2]}, to=room)

    show_online_list(room)

    # 如果房间没人了
    if room.get_players() == 0:
        del room_list[room_id]

        print(f"房间 {room_id} 因为没人而被销毁了")
    elif player_name == room.room_owner:
        # 如果是房主退出房间
        p = next((p_config['playerConfig'] for p_name, p_config in room.players.items()), None)
        if p is not None:
            # 更换房主
            room.room_owner = p.player_name
            p.is_captain = True
            send({'type': 'changeRoomOwner', 'message': f'{room.room_owner} 成为新的房主', 'stage': [1, 2]}, to=room)

    emit('message', {'type': 'roomList', 'roomList': get_room_list_info()}, broadcast=True)


# 坐下
@socketio.on('clickSeat')
def handle_click_seat(data):
    # 房间号
    room_id = data['roomId']
    # 座位号
    seat_index = data['seatIndex']
    # 玩家名称
    player_name = data['playerName']

    # 获取房间
    room = room_list[room_id]
    # 获取玩家列表
    players = room.players
    # 获取玩家
    player = players[player_name]['playerConfig']

    if room.seats[seat_index]:
        emit('message', {'message': f'这个位置已经有人了！'})
        return

    # 替换位置
    for i, seat in enumerate(room.seats):
        if seat is None:
            continue

        if seat['playerName'] == player.player_name:
            room.seats[i] = None

    # 设置玩家座位
    player.role_id = seat_index + 1
    room.seats[seat_index] = {
        "role": player.role,
        "roleId": player.role_id,
        "playerName": player.player_name
    }

    # room.players[seat_index] = player

    # 分发信息
    send({'message': f"{player.player_name} 选择了 {player.role_id} 号位置", 'type': 'clickSeat', 'stage': [1, 2]},
         to=room)


# 开始游戏
@socketio.on('startGame')
def handle_start_game(data):
    # 获取房间
    room_id = data['roomId']
    room_obj = room_list[room_id]

    # if room.get_players() == Room.MAX_USERS_PER_ROOM:
    if room_obj.get_players() >= 1 and room_obj.room_status is "waiting":
        # 切换房间状态
        room_obj.room_status = "playing"
        emit('message', {'type': 'startGame', 'message': '游戏开始', 'messageType': 'success', 'stage': [2]})
    elif room_obj.room_status is "playing":
        emit('message', {'type': 'error', 'message': '游戏正在进行中', 'messageType': 'error'})
    else:
        emit('message', {'type': 'error', 'message': '玩家数量不足，无法开始游戏', 'messageType': 'error'},
             room=room_obj)
    emit('message', {'type': 'roomList', 'roomList': get_room_list_info()}, broadcast=True)


# 减除玩家
@socketio.on('kickPlayer')
def handel_kick_player(data):
    room_id = data['roomId']
    player_name = data['playerName']

    room = get_room(room_id)

    player_data = next((p_data for p_name, p_data in room.players.items() if p_name == player_name), None)
    sid = player_data['sid']
    emit('message', {'type': 'kickPlayer', 'message': '你以被减除', 'messageType': 'error'}, room=sid)

    leave_room(room, sid=sid)
    del room.players[player_name]

    # 替换位置信息
    for i, s in enumerate(room.seats):
        if s is None:
            continue

        if s['playerName'] == player_name:
            room.seats[i] = None

    show_online_list(room)

    send({'message': f'{player_name} 被减除了！', 'messageType': 'warning', 'stage': [1, 2]}, to=get_room(room_id))


# 获取用户信息
@socketio.on('getUserInfo')
def handle_get_user_info(data):
    room_id = data['roomId']
    player_name = data['playerName']

    if room_id == '' or room_id is None or room_id not in room_list:
        return

    room = get_room(room_id)

    if player_name not in room.players:
        return

    player = room.players[player_name]['playerConfig']

    emit('message', {'type': 'getUserInfo', 'userInfo': player.to_dict()})


# 获取房间信息
@socketio.on('getRoomInfo')
def handle_get_room_info(data):
    room_id = data['roomId']

    if room_id == '' or room_id is None or room_id not in room_list:
        return

    room = get_room(room_id)
    emit('message', {'type': 'getRoomInfo', 'roomInfo': room.to_dict()})


# 退出链接
@socketio.on('disconnect')
def handle_disconnect():
    pass


# 获取当前玩家手上的卡牌
@socketio.on('getPlayerDeckList')
def handle_get_player_deck_list(data):
    room_id = data['roomId']
    player_name = data['playerName']

    if room_id == '' or room_id is None:
        return

    room = get_room(room_id)

    if player_name not in room.players:
        return

    player = room.players[player_name]['playerConfig']

    all_deck_list = []

    for c_type, c_list in player.deck_list.items():
        all_deck_list += c_list

    emit('message', {'type': 'getPlayerDeckList', 'playerDeckList': all_deck_list, 'playerName': player_name})


# @app.route('/rooms', methods=['GET'])
# def get_rooms():
#     """返回所有房间的列表"""
#     return jsonify(list(room_list))
#
#
# @app.route('/rooms/<room_name>', methods=['GET'])
# def get_room_users(room_name):
#     """返回指定房间的用户列表"""
#     for r in room_list:
#         room = room_list[r]
#         if room_name == room.room_id:
#             # print(room.to_dict()['players'])
#             players_list = [player['playerConfig'].to_dict() for player in room.players.values()]
#
#             # print(player.to_dict())
#             # players = [player['playerConfig'].to_dict() for player in room.players]
#             return jsonify(players_list)
#     else:
#         return jsonify([]), 404
