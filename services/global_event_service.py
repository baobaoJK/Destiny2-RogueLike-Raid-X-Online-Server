from flask_socketio import emit, send, leave_room

from services import get_room, get_player, get_room_list
from socketio_instance import socketio
from utils import shuffle_list
from utils.lottery import lottery
from utils.special_event import special_by_bumper_harvest, special_by_move, special_by_matrix


# 接受全局事件
@socketio.on('acceptGlobalEvent')
def accept_global_event(data):
    room_id = data['roomId']
    event_index = data['eventIndex']

    # 获取事件，设置事件状态
    room = get_room(room_id)
    global_event = room.global_event_list[event_index]
    global_event['eventStatus'] = 'active'

    run_global_event(room, global_event)

    send({'type': 'acceptGlobalEvent', 'message': f"已接受 {global_event['eventCnName']} 事件",
          'stage': [1, 2]}, to=room)


# 完成全局事件
@socketio.on('finishGlobalEvent')
def finish_global_event(data):
    room_id = data['roomId']
    event_index = data['eventIndex']

    # 获取事件，设置事件状态
    room = get_room(room_id)
    global_event = room.global_event_list[event_index]
    del room.global_event_list[event_index]

    send(dict(type='finishGlobalEvent', message=f"已完成 {global_event['eventCnName']} 事件", messageType='success',
              stage=[1, 2]), to=room)


# 全局事件执行
def run_global_event(room, global_event):
    # player_list = [player_name for player_name in room.players]
    FLIP_THE_TABLE = False
    player_list = [1, 2, 3, 4, 5, 6]
    player_list = shuffle_list(player_list)

    global_event_name = global_event['eventName']
    message_str = ''

    # 紧急支援
    if global_event_name == 'MAYDAY':
        game_config = room.get_game_config()
        dungeon_list = game_config['dungeonList']
        dungeon = lottery(dungeon_list)
        message_str = (f"玩家 {player_list[0]} | {player_list[1]} | {player_list[2]} "
                       f"需前往 - {dungeon['dungeonName']} - 进行地牢遭遇战")

    # 见者有份
    if global_event_name == 'Shared-gold':
        for player_name, player_config in room.players.items():
            player = get_player(room.room_id, player_name)
            player.player_money += 3

        message_str = "所有玩家获得3单位货币"

    # 金融危机
    if global_event_name == 'Financial-Crisis':
        for player_name, player_config in room.players.items():
            player = get_player(room.room_id, player_name)
            money = player.player_money // 2
            player.player_money = money

        message_str = "所有玩家持有货币数量减半"

    # 五谷丰登
    if global_event_name == 'Bumper-Harvest':
        message_str = (f"抽取顺序为 {player_list[0]} - {player_list[1]} - {player_list[2]} - "
                       f"{player_list[3]} - {player_list[4]} - {player_list[5]}")
        special_by_bumper_harvest(room.room_id, player_list)

    # 各自为营
    if global_event_name == 'Split-Up':
        message_str = (f"{player_list[0]} - {player_list[1]} - {player_list[2]} 需要做为 1 队，"
                       f"{player_list[3]} - {player_list[4]} - {player_list[5]} 需要做为 2 队"
                       "分别完成此次遭遇战")

    # 斗地主
    if global_event_name == 'Dou-Di-Zhu':
        message_str = f"{player_list[0]} - {player_list[1]} - {player_list[2]} 需要前往 斗地主环节"

    # 一二三木头人
    if global_event_name == 'Wood-Man':
        message_str = f"玩家 {player_list[0]} 需要当报数者，剩余玩家当木头人，前往熔炉竞技场进行此活动"

    # 移形换位
    if global_event_name == 'Transposition':
        message_str = "指定两名队友，让他们所有的卡牌互换"
        for p_name, p_config in room.players.items():
            p = p_config['playerConfig']
            if p.is_captain:
                special_by_move(room.room_id, p.player_name)

    # 掀桌
    if global_event_name == 'Flip-The-Table':
        message_str = f"本次 Raid 进度和卡牌将全部清零重置 从头开始"
        FLIP_THE_TABLE = True
        room_list = get_room_list()
        del room_list[room.room_id]


    # 左平行，右......
    if global_event_name == 'Left-Parallel-Right':
        message_str = (f"1队 {player_list[0]} - {player_list[1]} 玩家 | "
                       f"2队 {player_list[2]} - {player_list[3]} 玩家 | " 
                       f"3队 {player_list[4]} - {player_list[5]} 玩家")

    # 生化母体
    if global_event_name == 'Biochemical-Matrix':
        message_str = (f"抽取顺序为 {player_list[0]} - {player_list[1]} - {player_list[2]} - "
                       f"{player_list[3]} - {player_list[4]} - {player_list[5]}")
        special_by_matrix(room.room_id, player_list)

    # 我的我的我的
    if global_event_name == 'Mine-Mine-Mine':
        message_str = (f"本次遭遇战中队友的复活币都是 {player_list[0]} 号位的，"
                       f"复活必须 {player_list[0]} 号位玩家去指定一位有复活币"
                       f"的队友，被指定之人才能复活队友")

    # 判断消息是否为空
    if message_str != '':
        send({'type': 'runGlobalEvent', 'message': message_str, 'stage': [1, 2]}, to=room)

    # 掀桌
    if FLIP_THE_TABLE:
        send({'type': 'flipTheTable', 'message': '因抽到掀桌事件，所有玩家被移除房间！再见！', 'messageType': 'success'})


