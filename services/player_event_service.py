import random

from flask_socketio import emit

from services import get_player, get_room, check_card_in_player_deck_list, get_player_by_role_id, \
    get_random_card_by_type_and_player_deck_list, save_card, delete_card
from socketio_instance import socketio
from utils import shuffle_list
from utils.special_event import special_by_take_others, special_by_win_or_loss, special_by_lucky_number, special_by_spy, \
    special_by_self, special_by_alex_mercer, special_by_you_know, special_by_preservation


# 接受个人事件
@socketio.on('acceptPlayerEvent')
def accept_player_event(data):
    room_id = data['roomId']
    player_name = data['playerName']
    event_index = data['eventIndex']

    # 获取事件，设置事件状态
    player = get_player(room_id, player_name)
    player_event = player.player_event_list[event_index]
    player_event['eventStatus'] = 'active'

    # 苦尽甘来
    if player_event['eventName'] == 'Sweet-After-Bitter':
        for _ in range(3):
            random_num = random.randint(4, 6)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, random_num, True)
            player.sab_list.append(random_card)
            save_card({
                "roomId": room_id,
                "playerName": player_name,
                "card": random_card
            })

        emit('message', {'message': f"以为你生成三张不适卡牌，事件完成后清除", 'messageType': 'warning',
                         'stage': [1, 2]})

    run_player_event(room_id, player_name, player_event)

    emit('message', {'type': 'acceptPlayerEvent', 'message': f"已接受 {player_event['eventCnName']} 事件",
                     'stage': [1, 2]})


# 完成个人事件
@socketio.on('finishPlayerEvent')
def finish_global_event(data):
    room_id = data['roomId']
    player_name = data['playerName']
    event_index = data['eventIndex']

    # 获取事件，设置事件状态
    player = get_player(room_id, player_name)
    player_event = player.player_event_list[event_index]
    player_event_name = player_event['eventName']

    # 内鬼
    if player_event_name == 'Spy':
        special_by_spy(room_id, player_name)

    # 饮鸩止渴
    if player_event_name == 'Drinking-Poison-to-Quench-Thirst':
        random_card_1 = get_random_card_by_type_and_player_deck_list(room_id, player_name, 5, True)
        random_card_2 = get_random_card_by_type_and_player_deck_list(room_id, player_name, 6, True)
        save_card({
            "roomId": room_id,
            "playerName": player_name,
            "card": random_card_1
        })
        save_card({
            "roomId": room_id,
            "playerName": player_name,
            "card": random_card_2
        })

    # 噶点放心飞，出事自己背
    if player_event_name == 'By-Self':
        special_by_self(room_id, player_name)

    # Alex Mercer
    if player_event_name == 'Alex-Mercer':
        special_by_alex_mercer(room_id, player_name)

    # 你知道的，这是交易
    if player_event_name == 'This-Is-The-Deal':
        special_by_you_know(room_id, player_name)

    # 以存护之名
    if player_event_name == 'In-The-Name-of-Preservation':
        special_by_preservation(room_id, player_name)

    # 苦尽甘来
    if player_event_name == 'Sweet-After-Bitter':
        for sab_c in player.sab_list:
            delete_card({
                "roomId": room_id,
                "playerName": player_name,
                "card": sab_c
            })
        player.sab_list = []
        emit('message', {'message': f"以为你删除之前的三张卡牌", 'messageType': 'success',
                         'stage': [1, 2]})

    # 开摆
    if player_event_name == 'Open1':
        player.give_up = False
        player.player_money += 6
        player.draw_count += 2
        emit('message', {'message': f"你完成开摆事件，获得 2 次抽卡机会与 6 个货币", 'messageType': 'warning', 'stage': [1, 2]})

    del player.player_event_list[event_index]

    emit('message',
         {'type': 'finishPlayerEvent', 'message': f"已完成 {player_event['eventCnName']} 事件",
          'messageType': 'success', 'stage': [1, 2]})


# 放弃个人事件
@socketio.on('dropPlayerEvent')
def drop_global_event(data):
    room_id = data['roomId']
    player_name = data['playerName']
    event_index = data['eventIndex']

    # 获取事件，设置事件状态
    player = get_player(room_id, player_name)
    player.punish_count += 1
    player_event = player.player_event_list[event_index]
    del player.player_event_list[event_index]

    t_list = []
    for _ in range(12):
        random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, 7, True)
        t_list.append(random_card)

    player.player_status = 'runPunish'
    special_config = {
        'eventType': 'runPunish',
        'tList': t_list
    }
    player.special_config = special_config

    emit('message', {'type': 'showDeckDialog', 'message': f"已放弃 {player_event['eventCnName']} 事件，需要抽取一次特殊卡牌",
                     'messageType': 'error', 'specialConfig': special_config, 'stage': [1, 2]})


# 放弃惩罚
@socketio.on('runPunish')
def run_punish(data):
    room_id = data['roomId']
    player_name = data['playerName']
    card = data['card']

    # 获取玩家，更改配置
    player = get_player(room_id, player_name)
    player.punish_count -= 1

    save_card({
        "roomId": room_id,
        "playerName": player_name,
        "card": card
    })

    if player.punish_count == 0:
        player.special_config = ""

    emit('message', {'type': 'runPunish', 'stage': [1, 2]})


# 执行个人事件
def run_player_event(room_id, player_name, player_event):
    player_event_name = player_event['eventName']
    message_str = ''
    loop = True

    room = get_room(room_id)
    player = get_player(room_id, player_name)

    player_list = [1, 2, 3, 4, 5, 6]
    while loop:
        player_list = shuffle_list(player_list)
        if player_list[0] != player.role_id:
            loop = False

    # 亚托克斯
    if player_event_name == 'Aatrox':
        aatrox_card = {
            'cardId': 'Aatrox',
            'cardType': 'StrongDiscomfort',
            'cardLabel': 'god',
            'cardLevel': 999,
            'cardName': 'Aatrox',
            'cardCnName': '亚托克斯',
            'cardDescription': '获得一把挽歌且绑定威能位无法更换，可被【贱卖】【重铸】和2阶圣水解除，前二者失去挽歌，后者保留',
            'cardSpecial': 'god',
            'weight': 0,
            'count': 0,
            'all_count': 0,
            'idea': '来自亚托克斯'
        }
        message_str = f"亚托克斯：啊↑↓？"
        player.deck_list[aatrox_card['cardType']].append(aatrox_card)

    # 顺手牵羊
    if player_event_name == 'Take-Others':
        to_player = get_player_by_role_id(room_id, player_list[0])
        all_count = 0

        for type_name, deck_list in to_player.deck_list.items():
            for card in deck_list:
                if not (check_card_in_player_deck_list(room_id, player.player_name, card)):
                    all_count += 1

        if all_count <= 0:
            emit('message', {'message': '当前他没有卡牌，此事件作废', 'messageType': 'error', 'stage': [1, 2]})
        else:
            message_str = f"你可以抽取 {player_list[0]} 号玩家的卡牌"
            special_config = {
                'send': player.role_id,
                'to': player_list[0]
            }
            player.special_config = special_config

            special_by_take_others(room_id, player.player_name, player.special_config)

    # 无中生有
    if player_event_name == 'Create-Nothing':
        player.draw_count += 2
        message_str = f"已为你添加两次抽卡机会"

    # 零元购
    if player_event_name == '0-Money-Buy':
        player.zero_buy = 3
        message_str = f"已经为你添加 3 次零元购机会！去玩吧！"

    # 扫雷
    if player_event_name == 'Minesweeper':
        message_str = f"你需要去玩一把扫雷"

    # 赢下所有或一无所有
    if player_event_name == 'Win-or-Loss':
        message_str = f'使用 steam /random 20 大成功（数字20）获得三个额外强大增益/大失败（数字1）获得三个额外强大减益其余无事发生',
        special_by_win_or_loss(room_id, player_name)

    # 幸运数字
    if player_event_name == 'Lucky-Number':
        message_str = '使用 steam /random 20，若点数为 7，14，17 获得一个额外增益 若点数为 2 的倍数获得一个额外减益其余无事发生'
        special_by_lucky_number(room_id, player_name)

    # 开摆
    if player_event_name == 'Open1':
        player.give_up = True



    # 判断消息是否为空
    if message_str != '':
        emit('message', {'type': 'runPlayerEvent', 'message': message_str, 'stage': [1, 2]})

