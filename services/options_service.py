import random

from entitys.card_type import CardType
from services.deck_list_service import get_random_card_by_type, save_card, get_random_card_by_type_and_player_deck_list
from services.room_service import get_player, get_room
from socketio_instance import socketio
from flask_socketio import emit, send

from utils.lottery import lottery_by_count, lottery


# 获取地图
@socketio.on('getMapList')
def handle_get_map_list(data):
    room_id = data['roomId']
    room = get_room(room_id)
    game_config = room.get_game_config()

    emit('getMapList', {'type': 'getMapList', 'mapList': game_config['raidList']})


# 选择地图
@socketio.on('setMap')
def handle_select_map(data):
    # 获取房间
    room_id = data['roomId']
    room_obj = get_room(room_id)
    # 获取地图 id
    map_id = data['mapId']

    # 搜索地图信息并返回
    game_config = room_obj.get_game_config()
    raid = next((raid for raid in game_config['raidList'] if raid['raidId'] == map_id), None)
    if raid is not None:
        room_obj.set_raid_config(raid)

        # 更新玩家隐藏箱数量
        room = get_room(room_id)
        players = room.players
        for player_name in players:
            player = players[player_name]['playerConfig']
            player.raid_chest = 0

        # 更新房间阶段
        room.room_stage = "next"

        send({'type': 'setMap', 'message': f"你的地图已被更新为{raid['raidName']}", 'messageType': 'success',
              'stage': [1, 2]}, to=room_obj)


# 抵达遭遇战插旗点
@socketio.on('mapDoor')
def handle_map_doop(data):
    room_id = data['roomId']
    room = get_room(room_id)

    # 设置状态
    room.room_stage = "next"

    # 添加抽卡次数
    for player_name, player in room.players.items():
        player = get_player(room_id, player_name)
        player.draw_count += 2

    if room.shop_config['refreshCount'] != 1:
        room.shop_config['refreshCount'] = 1

    # 生成赏金列表
    generate_bounty_list(room_id)
    # 生成个人事件
    generate_player_event(room_id)
    # 生成全局事件
    generate_global_event(room_id)

    send({'type': 'mapDoor', 'message': f'已为你添加了新的赏金任务，2次抽卡机会',
          'messageType': 'success', 'stage': [1, 2]},
         to=room)
    send({'type': 'mapDoor', 'message': f'已生成个人事件和全局事件并添加1次免费刷新商店机会', 'messageType': 'warning', 'stage': [1, 2]},
         to=room)


# 遭遇战通关
@socketio.on('mapNext')
def handle_map_net(data):
    room_id = data['roomId']
    room = get_room(room_id)
    # 获取突袭信息
    raid_config = room.get_raid_config()
    level_point = raid_config['raidLevel']
    level_point_now = raid_config['raidLevelPoint']
    # 判断当前关卡
    if level_point_now < level_point:
        level_point_now += 1
        raid_config['raidLevelPoint'] = level_point_now
        room.room_stage = "door"
        if level_point_now == 1:
            send({'type': 'mapNext', 'stage': [1, 2]}, to=room)
            return

        for player_name, player_data in room.players.items():
            player = get_player(room_id, player_name)
            player_money = random.randint(1, 3)
            player.player_money += player_money
            sid = player_data['sid']

            # 免死金牌
            if not player.player_attributes['compensate']:
                debuff_count = 0

                # 负面补偿
                md_count = len(player.deck_list[CardType.micro_discomfort])
                sd_count = len(player.deck_list[CardType.strong_discomfort])
                u_count = len(player.deck_list[CardType.unacceptable])

                debuff_count += md_count
                debuff_count += sd_count * 2
                debuff_count += u_count * 3

                if debuff_count > 0:
                    player.player_money += debuff_count
                    emit('message', {'type': 'compensate',
                                     'message': f"因携带了负面卡牌通过遭遇战，获得 {debuff_count} 个货币"})
            # 重重难关
            if player.player_attributes['difficult']:
                count = room.raid_config['raidLevelPoint'] - 1

                for _ in range(count):
                    num = random.randint(4, 6)
                    card = get_random_card_by_type_and_player_deck_list(room_id, player_name, num, True)
                    save_card({
                        "roomId": room_id,
                        "playerName": player_name,
                        "card": card
                    })

                emit('message', {'type': 'difficult',
                                 'message': f"因你携带重重难关，已通过第 {count} 关，已经随机生成 {count} 张不适卡牌"})
            # 这不是很简单吗
            if player.player_attributes['easy']:
                count = room.raid_config['raidLevelPoint'] - 1

                for _ in range(count):
                    num = random.randint(1, 3)
                    card = get_random_card_by_type_and_player_deck_list(room_id, player_name, num, True)
                    save_card({
                        "roomId": room_id,
                        "playerName": player_name,
                        "card": card
                    })
                emit('message', {'type': 'easy',
                                 'message': f"因你携带这不是很简单吗，已通过第 {count} 关，已经随机生成 {count} 张增益卡牌"})

            emit('message',
                 {'type': 'mapNext', 'message': f'已通关，你获得了 {player_money} 个光尘货币', 'messageType': 'success',
                  'stage': [1, 2]},
                 room=sid)
    else:
        emit('message', {'type': 'message', 'message': '遭遇战结束了哦，别点了!', 'messageType': 'error'})


# 获取隐藏箱
@socketio.on('getChest')
def handle_get_chest(data):
    room_id = data['roomId']
    player_name = data['playerName']
    # 获取房间
    room = get_room(room_id)
    # 获取突袭信息
    raid_config = room.get_raid_config()
    chest_point = raid_config['raidChest']
    # 获取玩家
    player = get_player(room_id, player_name)
    # 判断隐藏箱数量
    if player.raid_chest < chest_point:
        player_money = random.randint(1, 3)
        player.raid_chest += 1
        player.player_money += player_money
        emit('message', {'type': 'message', 'message': f'已获取隐藏箱，获得 {player_money} 个货币', 'stage': [1, 2]})
    else:
        emit('message', {'type': 'message', 'message': '没有隐藏箱了别点了!', 'messageType': 'error'})


# 设置货币数量
@socketio.on('setMoney')
def handle_set_money(data):
    room_id = data['roomId']
    player_name = data['playerName']
    player = get_player(room_id, player_name)
    player.player_money = data['money']

    emit('message', {'type': 'setMoney', 'stage': [1]})


# 设置抽卡次数
@socketio.on('setDrawCount')
def handle_draw_count(data):
    room_id = data['roomId']
    player_name = data['playerName']
    player = get_player(room_id, player_name)
    player.draw_count = data['drawCount']

    emit('message', {'type': 'setDrawCount', 'stage': [1]})


# 无暇通关
@socketio.on('flawless')
def handle_flawless(data):
    room_id = data['roomId']
    room = get_room(room_id)
    players = room.players

    for player_name in players:
        players[player_name]['playerConfig'].player_money += 6

    send({'type': 'flawless', 'message': '无暇通关，每个人获得 6 个货币', 'stage': [1]}, to=room)


# 生成赏金列表
def generate_bounty_list(room_id):
    # 获取房间
    room = get_room(room_id)

    # 获取赏金列表
    game_config = room.get_game_config()
    for player_name, player_config in room.players.items():
        # 守护者赏金
        guardian_bounty_list = [bounty for bounty in game_config['bountyList'] if bounty['bountyLabel'] == 'guardian']
        # 人类赏金
        human_bounty_list = [bounty for bounty in game_config['bountyList'] if bounty['bountyLabel'] == 'human']
        # 杀手赏金
        killer_bounty_list = [bounty for bounty in game_config['bountyList'] if bounty['bountyLabel'] == 'killer']

        # 设置赏金列表
        bounty_list = [
            lottery(guardian_bounty_list),
            lottery(human_bounty_list),
            lottery(killer_bounty_list)
        ]
        player = get_player(room_id, player_name)
        player.bounty_list = bounty_list


# 生成个人事件
def generate_player_event(room_id):
    # 获取房间
    room = get_room(room_id)

    # 获取个人事件
    game_config = room.get_game_config()
    player_event_list = game_config['playerEventList']
    # 设置玩家事件
    for player_name, player_data in room.players.items():
        # 添加事件
        player = get_player(room_id, player_name)
        player_event = lottery_by_count(player_event_list)
        player_event['count'] -= 1
        print(f"已生成玩家事件 {player_event['eventCnName']}")
        player.player_event_list.append(player_event)


# 生成全局事件
def generate_global_event(room_id):
    # 获取房间
    room = get_room(room_id)

    # 获取全局事件
    game_config = room.get_game_config()
    global_event_list = game_config['globalEventList']
    count = random.randint(1, 2)
    for _ in range(count):
        # 设置全局事件
        global_event = lottery_by_count(global_event_list)
        global_event['count'] -= 1
        print(f"已生成全局事件 {global_event['eventCnName']}")
        # 添加事件
        room.global_event_list.append(global_event)