from services.room_service import get_room
from socketio_instance import socketio
from flask_socketio import emit

from utils.lottery import lottery, lottery_by_count


# 抽取地图
@socketio.on('rollMap')
def handle_roll_map(data):
    # 获取房间
    room_id = data['roomId']
    room_obj = get_room(room_id)

    # 判断地图数量
    raid_list = room_obj.game_config['raidList']
    raid_maps_count = sum(item['count'] for item in raid_list)
    if raid_maps_count == 0:
        emit('rollMap', {'type': 'error', 'message': '已经没有那么多地图可以抽取了'})
        return

    # 抽取地图
    lottery_count = 50
    map_list = []
    for i in range(lottery_count):
        if i == lottery_count - 7:
            map_obj = lottery_by_count(raid_list)
            map_obj['count'] -= 1
            map_list.append(map_obj)
            room_obj.set_raid_config(map_obj)
        else:
            map_obj = lottery(raid_list)
            map_list.append(map_obj)

    emit('rollMap', {'type': 'success', 'message': '正在抽取地图，不要切换其他页面', 'mapList': map_list})


# 更改地图事件
@socketio.on('changeMap')
def handle_change_map(data):
    # 获取房间
    room_id = data['roomId']
    room_obj = get_room(room_id)

    # 获取房间配置
    raid_config = room_obj.get_raid_config()

    # 更新玩家隐藏箱数量
    room = get_room(room_id)
    players = room.players
    for player_name in players:
        player = players[player_name]['playerConfig']
        player.raid_chest = 0

    # 更新房间阶段
    room.room_stage = "next"

    # 分发信息
    emit('message', {'type': 'setMap', 'message': f"已选择 {raid_config['raidName']} 进行本次突袭",
                     'messageType': 'warning', 'stage': [1, 2]}, room=room_obj)
