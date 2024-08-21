from entitys.card_type import CardType
from services import get_player, get_room
from services.deck_list_service import check_deck_list, save_card
from socketio_instance import socketio
from flask_socketio import emit, send

from utils import shuffle_list
from utils.lottery import lottery_by_count

# 抽取最大次数
DRAW_MAX_COUNT = 1000


# 显示卡组列表
@socketio.on('showDeckList')
def show_deck_list(data):
    room_id = data['roomId']
    player_name = data['playerName']
    list_type = data['listType']

    print(f"room_id - {room_id} - player_name - {player_name} - list_type - {list_type}")
    # 判断有没有人在抽卡
    room = get_room(room_id)
    if room.card_status != "" and room.card_status != player_name:
        emit("showDeckList", {'type': 'hasPlayer', 'message': f"{room.card_status} 当前正在抽卡，请稍等！",
                              'messageType': 'error'})
        return

    # 判断玩家是否有抽卡次数
    player = get_player(room_id, player_name)
    if player.draw_count <= 0:
        emit('showDeckList', {'status': 'fail', 'message': '你没有抽卡机会！', 'messageType': 'error'})
        player.player_status = 'wait'
        player.draw_card_type = ''
        room.card_status = ''
        return

    deck_list_name = None
    deck_list = None
    # 判断卡组类型
    if list_type == 'safe':
        deck_list_name = '稳妥起见'
        deck_list = get_safe_deck_list(room_id, player_name)
    elif list_type == 'danger':
        deck_list_name = '险中求胜'
        deck_list = get_danger_deck_list(room_id, player_name)
    elif list_type == 'gambit':
        deck_list_name = '对赌博弈'
        deck_list = get_gambit_deck_list(room_id, player_name)
    elif list_type == 'luck':
        deck_list_name = '时来运转'
        deck_list = get_luck_deck_list(room_id, player_name)
    elif list_type == 'devote':
        deck_list_name = '身心奉献'
        deck_list = get_devote_deck_list(room_id, player_name)

    # 判断卡组列表是否充足
    if deck_list is None or len(deck_list) != 12:
        emit('showDeckList', {'type': 'empty', 'message': '卡牌数量不够无法抽取', 'messageType': 'error'})
        return

    # 修改玩家状态
    player.player_status = 'draw'
    player.draw_card_type = list_type
    room.card_status = player_name

    deck_list = shuffle_list(deck_list)
    emit('showDeckList', {'type': 'success', 'message': '已生成 12 张卡牌', 'messageType': 'success',
                          'deckListName': deck_list_name, 'deckList': deck_list})
    send({'type': 'message', 'message': f"当前 {player_name} 正在抽卡", 'stage': [1, 2]}, to=room)


# 关闭卡组列表
@socketio.on('closeDeckList')
def close_deck_list(data):
    room_id = data['roomId']
    player_name = data['playerName']
    player = get_player(room_id, player_name)
    room = get_room(room_id)
    player.player_status = 'wait'
    player.draw_card_type = ''
    room.card_status = ''
    send({'type': 'message', 'message': f"玩家 {player_name} 退出了抽卡", 'messageType': 'warning',
          'stage': [1, 2]}, to=room)


# 点击卡牌
@socketio.on('clickCard')
def click_card(data):
    room_id = data['roomId']
    player_name = data['playerName']
    card = data['card']

    # 获取玩家
    player = get_player(room_id, player_name)
    room = get_room(room_id)

    # 判断玩家是否有抽卡次数
    if player.draw_count <= 0:
        emit('showDeckList', {'status': 'fail', 'message': '你没有抽卡机会！', 'messageType': 'error'})
        player.player_status = 'wait'
        player.draw_card_type = ''
        room.card_status = ''
        return

    player.draw_count -= 1

    if player.player_attributes['is_random']:
        random_list = [item for item in room.game_config['cardList'] if
                       not (check_card_in_player_deck_list(room_id, player_name, item))]
        random_card = lottery_by_count(random_list)

        save_card({
            "roomId": room_id,
            "playerName": player_name,
            "card": random_card
        })
        emit('message', {'type': 'message', 'message': "你拥有无法控制的卡牌，所以你的卡牌已被替换",
                         'messageType': 'warning', 'stage': [1, 2]})
    else:
        save_card({
            "roomId": room_id,
            "playerName": player_name,
            "card": card
        })

    emit('cardClick', {'type': 'cardClick', 'card': card})


# 获取当前卡牌列表的标签等级数量
def get_deck_list_tag_level_count(deck_list, tag_level):
    deck_list_count = [item for item in deck_list if item['cardLevel'] == tag_level and item['count'] > 0]
    return len(deck_list_count)


# 根据卡牌等级获取卡牌列表
def get_deck_list_tag_level_list(room_id, player_name, card_type, tag_level):
    tag_level_deck_list = []

    room = get_room(room_id)
    # game_card_list = [item for item in room.game_config['cardList'] if item['cardType'] == card_type
    #                   and not (check_card_in_player_deck_list(room_id, player_name, item))]
    game_card_list = [item for item in room.game_config['cardList'] if item['cardType'] == card_type
                      and not (check_card_in_player_deck_list(room_id, player_name, item))]
    # for card in game_card_list:
    # print(f"{card['cardCnName']} - 在列表里面吗：{check_card_in_player_deck_list(room_id, player_name, card)}")

    # T1 T2 T3 自适应
    t1 = get_deck_list_tag_level_count(game_card_list, 1)
    t2 = get_deck_list_tag_level_count(game_card_list, 2)
    t3 = get_deck_list_tag_level_count(game_card_list, 3)

    if t1 + t2 + t3 < sum(tag_level):
        return []

    if t1 < tag_level[0]:
        temp_count = tag_level[0] - t1
        tag_level[1] += temp_count
        tag_level[0] = t1

    if t2 < tag_level[1]:
        temp_count = tag_level[1] - t2
        tag_level[2] += temp_count
        tag_level[1] = t2

    if t3 < tag_level[2]:
        temp_count = tag_level[2] - t3
        tag_level[1] += temp_count
        tag_level[2] = t3

    if t2 < tag_level[1]:
        temp_count = tag_level[1] - t2
        if t3 > tag_level[2]:
            tag_level[2] += temp_count
        else:
            tag_level[0] += temp_count

        tag_level[1] = t2

    # print('----------------------------------')
    # print(f'{card_type} - T1 - {t1}')
    # print(f'{card_type} - T2 - {t2}')
    # print(f'{card_type} - T3 - {t3}')
    # print('----------------------------------')
    # print(f'{card_type} - T1 - {tag_level[0]}')
    # print(f'{card_type} - T2 - {tag_level[1]}')
    # print(f'{card_type} - T3 - {tag_level[2]}')
    # print('----------------------------------')

    if t1 < tag_level[0]:
        return []
    if t2 < tag_level[1]:
        return []
    if t3 < tag_level[2]:
        return []

    tag_level_list_count = 0
    for i, level in enumerate(tag_level):
        tag_level_list_count += level
        while len(tag_level_deck_list) < tag_level_list_count:
            card = lottery_by_count(game_card_list)
            if (check_deck_list(tag_level_deck_list, card) and
                    not (check_card_in_player_deck_list(room_id, player_name, card)) and
                    card['count'] > 0 and card['cardLevel'] == i + 1):
                tag_level_deck_list.append(card)

    return tag_level_deck_list


# 获取 稳妥起见 列表 6张微弱增益 1张强大增益 4张微弱不适 1张特殊卡牌
def get_safe_deck_list(room_id, player_name):
    room = get_room(room_id)
    game_config = room.game_config
    card_list = game_config['cardList']

    player_can_draw_count = get_player_can_draw_count(room_id, player_name, card_list)
    mg_count = player_can_draw_count['mg_count']
    sg_count = player_can_draw_count['sg_count']
    md_count = player_can_draw_count['md_count']
    t_count = player_can_draw_count['t_count']

    if mg_count < 6 or sg_count < 1 or md_count < 4 or t_count < 1:
        return []

    mg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.micro_gain, [2, 2, 2])
    sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain, shuffle_list([0, 0, 1]))
    md_list = get_deck_list_tag_level_list(room_id, player_name, CardType.micro_discomfort, [1, 1, 2])
    t_list = get_deck_list_tag_level_list(room_id, player_name, CardType.technology, [1, 0, 0])

    safe_deck_list = mg_list + sg_list + md_list + t_list

    return safe_deck_list


# 获取 险中求胜 列表 4张微弱增益 3张强大增益 1张欧皇增益 1张微弱不适 2张重度不适 1张特殊卡牌
def get_danger_deck_list(room_id, player_name):
    room = get_room(room_id)
    game_config = room.game_config
    card_list = game_config['cardList']

    player_can_draw_count = get_player_can_draw_count(room_id, player_name, card_list)
    mg_count = player_can_draw_count['mg_count']
    sg_count = player_can_draw_count['sg_count']
    md_count = player_can_draw_count['md_count']
    sd_count = player_can_draw_count['sd_count']
    t_count = player_can_draw_count['t_count']

    if mg_count < 4 or sg_count < 2 or md_count < 1 or sd_count < 2 or t_count < 1:
        return []
    mg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.micro_gain, [1, 1, 2])
    sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain, shuffle_list([0, 1, 1]))
    md_list = get_deck_list_tag_level_list(room_id, player_name, CardType.micro_discomfort, shuffle_list([0, 1, 1]))
    sd_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_discomfort,
                                           shuffle_list([0, 1, 1]))
    t_list = get_deck_list_tag_level_list(room_id, player_name, CardType.technology, [1, 0, 0])

    danger_deck_list = mg_list + sg_list + md_list + sd_list + t_list

    temp_count = 0
    while len(danger_deck_list) < 12 and temp_count < DRAW_MAX_COUNT:
        o_count = player_can_draw_count['o_count']
        if o_count < 1:
            if o_count == 0 and temp_count == (DRAW_MAX_COUNT - 1):
                return []
            sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain,
                                                   shuffle_list([0, 0, 1]))
            if len(sg_list) != 0 and not (check_card_in_player_deck_list(room_id, player_name, sg_list[0])):
                danger_deck_list += sg_list
        else:
            o_list = get_deck_list_tag_level_list(room_id, player_name, CardType.opportunity, shuffle_list([0, 0, 1]))
            if len(o_list) != 0 and not (check_card_in_player_deck_list(room_id, player_name, o_list[0])):
                danger_deck_list += o_list

        temp_count += 1

    return danger_deck_list


# 获取 对赌博弈 列表 5张强大增益 1张欧皇增益 5张重度不适 1张反人类
def get_gambit_deck_list(room_id, player_name):
    room = get_room(room_id)
    game_config = room.game_config
    card_list = game_config['cardList']

    player_can_draw_count = get_player_can_draw_count(room_id, player_name, card_list)
    sg_count = player_can_draw_count['sg_count']
    sd_count = player_can_draw_count['sd_count']

    if sg_count < 5 or sd_count < 5:
        return []

    sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain, [1, 2, 2])
    sd_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_discomfort, [1, 2, 2])

    gambit_deck_list = sg_list + sd_list

    temp_count = 0
    while len(gambit_deck_list) < 11 and temp_count < DRAW_MAX_COUNT:
        o_count = player_can_draw_count['o_count']
        if o_count < 1:
            if o_count == 0 and temp_count == (DRAW_MAX_COUNT - 1):
                return []
            sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain,
                                                   shuffle_list([0, 0, 1]))
            if len(sg_list) != 0 and not (check_card_in_player_deck_list(room_id, player_name, sg_list[0])):
                gambit_deck_list += sg_list
        else:
            o_list = get_deck_list_tag_level_list(room_id, player_name, CardType.opportunity,
                                                  shuffle_list([0, 0, 1]))
            if len(o_list) != 0 and not (check_card_in_player_deck_list(room_id, player_name, o_list[0])):
                gambit_deck_list += o_list
        temp_count += 1

    temp_count = 0
    while len(gambit_deck_list) < 12 and temp_count < DRAW_MAX_COUNT:
        u_count = player_can_draw_count['u_count']
        if u_count < 1:
            if u_count == 0 and temp_count == (DRAW_MAX_COUNT - 1):
                return []
            sd_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_discomfort,
                                                   shuffle_list([0, 0, 1]))
            if len(sd_list) != 0 and not (check_card_in_player_deck_list(room_id, player_name, sd_list[0])):
                gambit_deck_list += sd_list
        else:
            u_list = get_deck_list_tag_level_list(room_id, player_name, CardType.unacceptable,
                                                  shuffle_list([0, 0, 1]))
            if len(u_list) != 0 and not (check_card_in_player_deck_list(room_id, player_name, u_list[0])):
                gambit_deck_list += u_list
        temp_count += 1

    return gambit_deck_list


# 获取 时来运转 列表 1张强大增益 1张欧皇增益 1张重度不适 1张反人类 8张特殊卡牌
def get_luck_deck_list(room_id, player_name):
    room = get_room(room_id)
    game_config = room.game_config
    card_list = game_config['cardList']

    player_can_draw_count = get_player_can_draw_count(room_id, player_name, card_list)
    sg_count = player_can_draw_count['sg_count']
    o_count = player_can_draw_count['o_count']
    sd_count = player_can_draw_count['sd_count']
    u_count = player_can_draw_count['u_count']
    t_count = player_can_draw_count['t_count']

    if sg_count < 1 or sd_count < 1 or t_count < 8:
        return

    sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain, shuffle_list([0, 0, 1]))
    sd_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_discomfort,
                                           shuffle_list([0, 0, 1]))
    t_list = get_deck_list_tag_level_list(room_id, player_name, CardType.technology, [8, 0, 0])

    luck_deck_list = sg_list + sd_list + t_list

    if o_count != 0:
        o_list = get_deck_list_tag_level_list(room_id, player_name, CardType.opportunity, shuffle_list([0, 0, 1]))
        luck_deck_list += o_list
    else:
        sg_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_gain, shuffle_list([0, 0, 1]))
        luck_deck_list += sg_list

    if u_count != 0:
        u_list = get_deck_list_tag_level_list(room_id, player_name, CardType.unacceptable, shuffle_list([0, 0, 1]))
        luck_deck_list += u_list
    else:
        sd_list = get_deck_list_tag_level_list(room_id, player_name, CardType.strong_discomfort,
                                               shuffle_list([0, 0, 1]))
        luck_deck_list += sd_list

    return luck_deck_list


# 获取 身心奉献 列表 8张辅助卡牌 4张微弱不适
def get_devote_deck_list(room_id, player_name):
    room = get_room(room_id)
    game_config = room.game_config
    card_list = game_config['cardList']

    player_can_draw_count = get_player_can_draw_count(room_id, player_name, card_list)
    md_count = player_can_draw_count['md_count']
    s_count = player_can_draw_count['s_count']
    t_count = player_can_draw_count['t_count']

    if s_count < 1 or md_count < 4:
        return

    md_list = get_deck_list_tag_level_list(room_id, player_name, CardType.micro_discomfort, [1, 1, 2])

    devote_deck_list = md_list

    # while len(devote_deck_list) - len(md_list) != s_count:
    support_list = [item for item in card_list if item['cardType'] == CardType.support]
    devote_deck_list += support_list

    if t_count < 8:
        return

    while len(devote_deck_list) < 12:
        t_list = get_deck_list_tag_level_list(room_id, player_name, CardType, [1, 0, 0])
        devote_deck_list += t_list

    return devote_deck_list


# 检查 卡牌是否在 玩家列表里
def check_card_in_player_deck_list(room_id, player_name, item):
    player = get_player(room_id, player_name)

    for card_type, card_list in player.deck_list.items():
        for card in card_list:
            if item['cardName'] == card['cardName']:
                # 类型判断
                print(f"类型判断 {item['cardName']} == {card['cardName']}: {item['cardName'] == card['cardName']}")
                return True

    return False


# 获取卡牌列表的卡牌数量
def get_deck_list_count(room_id, player_name, card_list, card_type):
    return len([item for item in card_list if (item['cardType'] == card_type and item['count'] > 0
                                               and not (check_card_in_player_deck_list(room_id, player_name, item)))])


# 获取特殊卡牌列表
def get_technology_deck_list(room_id, player_name, size):
    room = get_room(room_id)
    game_config = room.game_config
    card_list = game_config['cardList']

    t_count = get_deck_list_tag_level_count(card_list, CardType.technology)

    if t_count < size:
        return []

    t_list = get_deck_list_tag_level_list(room_id, player_name, CardType.technology, [size, 0, 0])

    technology_deck_list = t_list

    return technology_deck_list


# 输出玩家可以抽取的数量
def get_player_can_draw_count(room_id, player_name, card_list):
    player_can_draw_count = {
        "mg_count": get_deck_list_count(room_id, player_name, card_list, CardType.micro_gain),
        "sg_count": get_deck_list_count(room_id, player_name, card_list, CardType.strong_gain),
        "o_count": get_deck_list_count(room_id, player_name, card_list, CardType.opportunity),
        "md_count": get_deck_list_count(room_id, player_name, card_list, CardType.micro_discomfort),
        "sd_count": get_deck_list_count(room_id, player_name, card_list, CardType.strong_discomfort),
        "u_count": get_deck_list_count(room_id, player_name, card_list, CardType.unacceptable),
        "t_count": get_deck_list_count(room_id, player_name, card_list, CardType.technology),
        "s_count": get_deck_list_count(room_id, player_name, card_list, CardType.support),
    }

    print(f"微弱增益 - {player_can_draw_count['mg_count']}")
    print(f"强大增益 - {player_can_draw_count['sg_count']}")
    print(f"欧皇增益 - {player_can_draw_count['o_count']}")
    print(f"微弱不适 - {player_can_draw_count['md_count']}")
    print(f"重度不适 - {player_can_draw_count['sd_count']}")
    print(f"反人类 - {player_can_draw_count['u_count']}")
    print(f"特殊卡 - {player_can_draw_count['t_count']}")
    print(f"辅助卡 - {player_can_draw_count['s_count']}")

    return player_can_draw_count
