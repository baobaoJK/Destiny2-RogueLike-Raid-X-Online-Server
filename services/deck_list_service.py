import math
import random

from flask_socketio import emit, send

from entitys.card_type import CardType
from services import get_room, get_player, get_player_by_role_id
from socketio_instance import socketio
from utils import get_card_list_by_type, shuffle_list
from utils.card import check_card_in_player_deck_list
from utils.lottery import lottery, lottery_by_count
from utils.special_event import special_by_tribute, special_by_tyrant, special_by_personal, special_by_money

# 十三幺
thirteenList = [
    'Osteo-Striga',
    'All-Out',
    'Darkness-Servant-1',
    'Darkness-Servant-2',
    'Light-Bringer-1',
    'Light-Bringer-2',
    'Light-Bringer-3',
    'Paladin',
    'Armory',
    'Reicher-Playboy',
    'Assassin',
    'Protect-Target',
    'Weaken'
]


# 抽取随机卡牌
@socketio.on('getRandomCard')
def get_random_card(data):
    room_id = data['roomId']
    player_name = data['playerName']
    card_type = data['cardType']
    room = get_room(room_id)

    game_config = room.game_config
    game_card_list = game_config['cardList']
    card_list = [item for item in game_card_list if item['cardType'] == CardType.get_type_by_num(card_type)]

    card = lottery_by_count(card_list)
    if card is not None:
        new_data = {'roomId': room_id, 'playerName': player_name, 'card': card}
        save_card(new_data)


# 获取卡牌列表
@socketio.on('getCardList')
def get_card_list(data):
    room_id = data['roomId']
    room = get_room(room_id)

    game_config = room.game_config
    card_list = get_card_list_by_type(game_config['cardList'])

    emit('getCardList', {'cardList': card_list})


# 保存卡牌到列表
@socketio.on('saveCard')
def save_card(data):
    room_id = data['roomId']
    player_name = data['playerName']
    card = data['card']

    # 获取玩家
    player = get_player(room_id, player_name)
    card_type = card['cardType']
    room = get_room(room_id)

    # # 判断是否是舍己为人
    # if card['cardName'] == 'Altruism':
    #     for p_name, p_config in room.players.items():
    #         p = p_config['playerConfig']
    #         for card_type, card_list in p.deck_list.items():
    #             if card_type != CardType.unacceptable:
    #                 continue
    #
    #             for c in card_list:
    #                 if c['cardName'] == 'Altruism':
    #                     delete_card({
    #                         "roomId": room_id,
    #                         "playerName": p_name,
    #                         "card": c
    #                     })

    # 判断玩家是否有舍己为人
    if card['cardType'] == CardType.micro_discomfort or card['cardType'] == CardType.strong_discomfort or card[
        'cardType'] == CardType.unacceptable:
        for p_name, p_config in room.players.items():
            p = p_config['playerConfig']
            if p.player_attributes['compensate']:
                break
            if p.role_id == player.role_id:
                continue
            for c_type, c_list in p.deck_list.items():
                if c_type != CardType.unacceptable:
                    continue

                for c in c_list:
                    if c['cardName'] == 'Altruism':
                        player = p
                        emit('message', {"message": f"因为有玩家身上携带舍己为人，此次的减益卡牌不会添加到你的卡组里",
                                         'messageType': 'warning', 'stage': [1, 2]})
                        emit('message', {'message': f"因为你是身上携带舍己为人，并且别人抽到了减益卡牌，将由你来承担",
                                         'messageType': 'warning', 'stage': [1, 2]}, room=p.sid)
    # 添加卡牌
    if check_deck_list(player.deck_list[card_type], card):
        player.deck_list[card_type].append(card)

        card_item = next((item for item in room.game_config['cardList'] if item['cardName'] == card['cardName']), None)
        if card_item is not None:
            card_item['count'] -= 1

        # 有福同享
        if player.blessing != 0:
            if card_type == CardType.micro_gain or card_type == CardType.strong_gain or card_type == CardType.opportunity:
                and_player = get_player_by_role_id(room_id, player.blessing)
                # and_player.deck_list[card_type].append(card)
                emit('message', {'message': f"因为你和 {player.role_id} 号玩家"
                                            f"有福同享 添加 {card['cardCnName']} 成功", 'stage': [1, 2]},
                     room=and_player.sid)

        # 有难同当
        if player.disaster != 0:
            if card_type == CardType.micro_discomfort or card_type == CardType.strong_discomfort or card_type == CardType.unacceptable:
                and_player = get_player_by_role_id(room_id, player.disaster)
                # and_player.deck_list[card_type].append(card)
                emit('message', {'message': f"因为你和 {player.role_id} 号玩家"
                                            f"有难同当 添加 {card['cardCnName']} 成功", 'stage': [1, 2]},
                     room=and_player.sid)

        emit('message', {'type': 'saveCard', 'message': f"添加卡牌 {card['cardCnName']} 成功",
                         'messageType': 'success', 'stage': [1, 2]}, room=player.sid)

        special_card_handle(room_id, player_name, card)

        get_card_list({
            "roomId": room_id
        })
    else:
        emit('message', {'type': 'fail', 'message': f"卡牌 {card['cardCnName']} 已存在，添加失败",
                         'messageType': 'error'}, room=player.sid)

    if card['cardName'] == 'Thirteen-Orphans' or card['cardName'] == 'Quit-Gambling' or card['cardName'] == 'Gambler':
        player.player_status = 'wait'
        player.draw_card_type = ''
        room.card_status = ''
        emit('message', {'stage': [1, 2]})


# 删除卡牌
@socketio.on('deleteCard')
def delete_card(data):
    room_id = data['roomId']
    player_name = data['playerName']
    card = data['card']

    # 获取玩家
    room = get_room(room_id)
    player = get_player(room_id, player_name)
    card_type = card['cardType']

    # 苦肉计
    if (card['cardName'] != 'The-Self-Torture-Scheme' and player.player_attributes['torture'] and
            (card_type == CardType.micro_gain or
             card_type == CardType.strong_gain or
             card_type == CardType.opportunity)):
        player.draw_count += 2
        emit('message', {'type': 'torture', 'message': "已触发苦肉计，获取 2 次抽卡机会",
                         'messageType': 'warning', 'stage': [1, 2]})

    # 十三幺
    if card['cardName'] == 'Thirteen-Orphans':
        for c_name in thirteenList:
            card_item = next((item for item in room.game_config['cardList'] if item['cardName'] == c_name), None)
            player.deck_list[card_item['cardType']].remove(card_item)

    # 卡牌回收计划
    if card['cardName'] != 'Card-Recycling-Program' and player.player_attributes['program']:
        temp_str = ''
        if card['cardType'] == CardType.micro_gain:
            player.player_money += 1
            temp_str = '您已出售微弱增益卡牌，获得 1 货币'
        if card['cardType'] == CardType.strong_gain:
            player.player_money += 3
            temp_str = '您已出售强大增益卡牌，获得 3 货币'
        if card['cardType'] == CardType.opportunity:
            player.player_money += 6
            temp_str = '您已出售欧皇增益卡牌，获得 6 货币'
        emit('message', {'type': 'program', 'message': temp_str,
                         'messageType': 'warning', 'stage': [1, 2]})

    # 有福同享
    if player.blessing != 0:
        if card_type == CardType.micro_gain or card_type == CardType.strong_gain or card_type == CardType.opportunity:
            and_player = get_player_by_role_id(room_id, player.blessing)
            emit('message', {'message': f"因为你和 {player.role_id} 号玩家"
                                        f"有福同享 删除 {card['cardCnName']} 成功", 'stage': [1, 2]},
                 room=and_player.sid)

    # 有难同当
    if player.disaster != 0:
        if card_type == CardType.micro_discomfort or card_type == CardType.strong_discomfort or card_type == CardType.unacceptable:
            and_player = get_player_by_role_id(room_id, player.disaster)
            emit('message', {'message': f"因为你和 {player.role_id} 号玩家"
                                        f"有难同当 删除 {card['cardCnName']} 成功", 'stage': [1, 2]},
                 room=and_player.sid)

    # 删除卡牌
    player.deck_list[card_type].remove(card)

    emit('message', {'type': 'deleteCard', 'message': f"删除卡牌 {card['cardCnName']} 成功",
                     'messageType': 'success', 'stage': [1, 2]}, room=player.sid)


# 根据卡牌类型生成随机卡牌
def get_random_card_by_type(room_id, type_num, by_count):
    card = {
        'cardType': None
    }
    card_type = CardType.get_type_by_num(type_num)
    room = get_room(room_id)

    MAX_COUNT = 1000
    try_count = 0
    while card['cardType'] != card_type and try_count < MAX_COUNT:
        card_list = room.game_config['cardList']

        if by_count:
            card = lottery_by_count(card_list)
        else:
            card = lottery(card_list)
        # print(card)
        try_count += 1

    return card


# 根据卡牌类型和玩家列表生成随机卡牌
def get_random_card_by_type_and_player_deck_list(room_id, player_name, type_num, by_count):
    card = {
        'cardType': None
    }
    card_type = CardType.get_type_by_num(type_num)
    room = get_room(room_id)

    loop = True
    while loop:
        card_list = room.game_config['cardList']
        if by_count:
            card = lottery_by_count(card_list)
        else:
            card = lottery(card_list)

        if (card['cardType'] == card_type and
                not (check_card_in_player_deck_list(room_id, player_name, card))):
            loop = False

        print(card)

    return card


# 卡牌去重
def check_deck_list(deck_list, card):
    if len(deck_list) == 0:
        return True
    card_item = next((item for item in deck_list if item['cardId'] == card['cardId']), None)
    return card_item is None


# 玩家卡牌去重
def check_player_deck_list(player_list, card):
    for deck_type, deck_list in player_list.items():
        if len(deck_list) == 0:
            return True
        card_item = next((item for item in deck_list if item['cardId'] == card['cardId']), None)
        if card_item is not None:
            return False
    return True


# 根据卡牌名称寻找卡牌
def find_card_by_name_in_player_card_list(player, card_name):
    for type_name, card_list in player.deck_list.items():
        for card in card_list:
            if card['cardName'] == card_name:
                return card
    return None


# 特殊卡牌处理
def special_card_handle(room_id, player_name, card):
    room = get_room(room_id)
    player = get_player(room_id, player_name)
    card_name = card['cardName']

    players_id = [1, 2, 3, 4, 5, 6]
    loop = True
    while loop:
        players_id = shuffle_list(players_id)
        if players_id[0] != player.role_id:
            loop = False

    send_type = 'emit'
    message_str = ''
    message_type = 'warning'

    # -----------------------------------
    # 特殊效果
    # -----------------------------------
    # 不吃这套
    if player.player_attributes['noDeal']:
        if (card['cardType'] == CardType.micro_discomfort or
                card['cardType'] == CardType.strong_discomfort or
                card['cardType'] == CardType.unacceptable):
            temp_card = find_card_by_name_in_player_card_list(player, 'I-Wont-Eat-This')
            player.deck_list[temp_card['cardType']].remove(temp_card)
            player.deck_list[card['cardType']].remove(card)
            message_str = f"因身上携带 {temp_card['cardCnName']} 卡牌，此次的减益卡牌已被消除"

    # 不是哥们
    if player.player_attributes['noBuddy']:
        if (card['cardType'] == CardType.micro_gain or
                card['cardType'] == CardType.strong_gain or
                card['cardType'] == CardType.opportunity):
            temp_card = find_card_by_name_in_player_card_list(player, 'No-Buddy')
            player.deck_list[temp_card['cardType']].remove(temp_card)
            player.deck_list[card['cardType']].remove(card)
            message_str = f"因身上携带 {temp_card['cardCnName']} 卡牌，此次的增益卡牌已被消除",

    # 卡牌低效 免死金牌和帝王禁令
    if player.player_attributes['counteract']:
        card_1 = find_card_by_name_in_player_card_list(player, 'The-Medallion')
        card_2 = find_card_by_name_in_player_card_list(player, 'Imperial-Ban')
        player.deck_list[card_1['cardType']].remove(card_1)
        player.deck_list[card_2['cardType']].remove(card_2)
        message_str = f"你已拥有 免死金牌 和 帝王禁令，这两张牌互相抵消，已被移除卡牌列表"

    # -----------------------------------
    # 欧皇增益
    # -----------------------------------
    # 这不是很简单吗
    if card_name == 'Easy':
        count = room.raid_config['raidLevelPoint']

        for _ in range(count):
            num = random.randint(1, 3)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, num, True)
            player.deck_list[random_card['cardType']].append(random_card)

        message_str = f"因抽到 {card['cardCnName']} 卡牌，当前是第 {count} 关, 已经随机生成 {count} 张增益卡牌"

    # -----------------------------------
    # 反人类
    # -----------------------------------
    # 重重难关
    if card_name == 'Many-Difficulties' and not player.player_attributes['compensate']:
        count = room.raid_config['raidLevelPoint']

        for _ in range(count):
            num = random.randint(4, 6)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, num, True)
            player.deck_list[random_card['cardType']].append(random_card)
        message_str = f"因抽到 {card['cardCnName']} 卡牌，当前是第 {count} 关, 已经随机生成 {count} 张不适卡牌"

    # 舍己为人
    if card_name == 'Altruism' and not player.player_attributes['compensate']:
        deck_list = []
        for p_name, p_config in room.players.items():
            p = p_config['playerConfig']
            if p.role_id == player.role_id:
                continue
            for card_type, card_list in p.deck_list.items():
                if card_type == CardType.micro_discomfort or card_type == CardType.strong_discomfort or card_type == CardType.unacceptable:
                    cards_to_remove = card_list[:]
                    for card in cards_to_remove:
                        if check_deck_list(deck_list, card):
                            deck_list.append(card)

                        delete_card({
                            "roomId": room_id,
                            "playerName": p_name,
                            "card": card
                        })
            emit('message', {'message': f"因为 {player.role_id} 号玩家抽到了 舍己为人，你身上的减益卡牌已被转移",
                             'messageType': 'warning', 'stage': [1, 2]}, room=p.sid)

        for card in deck_list:
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": card
            })

        emit('message',
             {'message': f"因为你抽到了舍己为人，你将承受所有玩家的减益卡牌", 'messageType': 'warning', 'stage': [1, 2]})

    # 堕落之血
    if card_name == 'Corrupted-Blood':
        message_str = "你的欧皇增益将不生效，同时每一轮遭遇战结束会将你身上除这张卡外的一张减益卡牌传播给队友。（此卡在被圣水清除前不会被无效）"

    # -----------------------------------
    # 重度不适
    # -----------------------------------
    if card_name == 'Lost-Wallet':
        player.deck_list[card['cardType']].remove(card)
        player.player_money = 0
        message_str = '杂鱼~你的货币全没了哦~'

    # -----------------------------------
    # 特殊卡牌
    # -----------------------------------
    # 收过路费
    if card_name == 'Capitalism':
        player.deck_list[card['cardType']].remove(card)
        player_1_role_id = player.role_id + 2 - 6 if player.role_id + 2 > 6 else player.role_id + 2
        player_2_role_id = player.role_id - 2 + 6 if player.role_id - 2 < 1 else player.role_id - 2

        player_1 = next(
            (p['playerConfig'] for n, p in room.players.items() if p['playerConfig'].role_id == player_1_role_id))
        player_2 = next(
            (p['playerConfig'] for n, p in room.players.items() if p['playerConfig'].role_id == player_2_role_id))

        player_1_money = math.ceil(player_1.player_money / 2)
        player_2_money = math.ceil(player_2.player_money / 2)

        player_1.player_money = player_1.player_money - player_1_money
        player_2.player_money = player_2.player_money - player_2_money

        player.player_money += (player_1_money + player_2_money)

        message_str = (f"玩家 {player.player_name} 抽到了 收过路费卡牌，获得 {player_1_role_id} 号"
                       f"和 {player_2_role_id} 号玩家 一半的货币")

    # 生财有道
    if card_name == 'Make-Wealth':
        player.deck_list[card['cardType']].remove(card)
        player.player_money += 6
        message_str = f"已为你添加 6 货币"

    # 起手换牌
    if card_name == 'Change-Card':
        player.deck_list[card['cardType']].remove(card)

        draw_count = 0
        for card_type, card_list in player.deck_list.items():
            cards_to_remove = card_list[:]  # 复制整个列表
            for card in cards_to_remove:
                draw_count += 1
                delete_card({
                    "roomId": room_id,
                    "playerName": player_name,
                    "card": card
                })

        player.draw_count += draw_count

        message_str = f"回收了 {draw_count} 张卡牌，已兑换成 {draw_count} 次抽卡机会"

    # 恶魔契约
    if card_name == 'Devils-Pact':
        player.deck_list[card['cardType']].remove(card)
        player.devilspact = 2
        message_str = "恶魔契约已启用：每在商店购买一次装备就获得一次抽卡机会（至多触发两次）"

    # 上贡
    if card_name == 'Tribute':
        player.deck_list[card['cardType']].remove(card)

        list_1 = player.deck_list[CardType.micro_gain]
        list_2 = player.deck_list[CardType.strong_gain]
        list_3 = player.deck_list[CardType.opportunity]

        if len(list_1) == 0 and len(list_2) == 0 and len(list_3) == 0:
            emit('message', {'message': '你没有卡牌可以提供！此卡牌作废', 'messageType': 'error', 'stage': [1, 2]})
        else:
            message_str = f"从你的增益卡牌中挑选一张送给 {players_id[0]} 号玩家"
            player.special_config = {
                'send': player.role_id,
                'to': players_id[0],
            }
            special_by_tribute(room_id, player_name, player.special_config)

    # 决斗
    if card_name == 'Duel':
        player.deck_list[card['cardType']].remove(card)
        message_str = (f"你与 {players_id[0]} 号玩家签订决斗协议，你们立即前往私人熔炉竞技场的生存使用当前拥有的武器技能"
                       f"决斗，获得第一个回合胜利的玩家得到失败者的一半货币，不许认输！")

    # 等价交换
    if card_name == 'Equivalent-Exchange':
        player.deck_list[card['cardType']].remove(card)
        message_str = f"你需要和 {players_id[0]} 号玩家进行所有卡牌互换，立即生效"
        change_player = get_player_by_role_id(room_id, players_id[0])
        if change_player is not None:
            temp_deck_list_1 = []
            temp_deck_list_2 = []

            for type_name, deck_list in player.deck_list.items():
                for card in deck_list:
                    temp_deck_list_1.append(card)
                    delete_card({
                        'roomId': room_id,
                        'playerName': player_name,
                        'card': card
                    })

            for type_name, deck_list in change_player.deck_list.items():
                for card in deck_list:
                    temp_deck_list_2.append(card)
                    delete_card({
                        'roomId': room_id,
                        'playerName': player_name,
                        'card': card
                    })

            for card in temp_deck_list_1:
                save_card({
                    "roomId": room_id,
                    "playerName": change_player.player_name,
                    "card": card
                })

            for card in temp_deck_list_2:
                save_card({
                    "roomId": room_id,
                    "playerName": player_name,
                    "card": card
                })

    # 有福同享
    if card_name == 'Blessed-To-Share':
        player.deck_list[card['cardType']].remove(card)
        message_str = f"你需要和 {players_id[0]} 号玩家共享所有增益卡牌，立即生效"

        and_player = get_player_by_role_id(room_id, players_id[0])

        if and_player is not None:
            player.blessing = players_id[0]
            and_player.blessing = player.role_id

            player.deck_list[CardType.micro_gain] += and_player.deck_list[CardType.micro_gain]
            player.deck_list[CardType.strong_gain] += and_player.deck_list[CardType.strong_gain]
            player.deck_list[CardType.opportunity] += and_player.deck_list[CardType.opportunity]

            and_player.deck_list[CardType.micro_gain] = player.deck_list[CardType.micro_gain]
            and_player.deck_list[CardType.strong_gain] = player.deck_list[CardType.strong_gain]
            and_player.deck_list[CardType.opportunity] = player.deck_list[CardType.opportunity]

            emit('message', {'message': f"{player.role_id} 号玩家抽到了有福同享，并绑定为你", 'stage': [1, 2]},
                 room=and_player.sid)

    # 有难同当
    if card_name == 'Share-The-Difficulties':
        player.deck_list[card['cardType']].remove(card)
        message_str = f"你需要和 {players_id[0]} 号玩家共享所有减益卡牌，立即生效"

        and_player = get_player_by_role_id(room_id, players_id[0])

        if and_player is not None:
            player.disaster = players_id[0]
            and_player.disaster = player.role_id

            player.deck_list[CardType.micro_discomfort] += and_player.deck_list[CardType.micro_discomfort]
            player.deck_list[CardType.strong_discomfort] += and_player.deck_list[CardType.strong_discomfort]
            player.deck_list[CardType.unacceptable] += and_player.deck_list[CardType.unacceptable]

            and_player.deck_list[CardType.micro_discomfort] = player.deck_list[CardType.micro_discomfort]
            and_player.deck_list[CardType.strong_discomfort] = player.deck_list[CardType.strong_discomfort]
            and_player.deck_list[CardType.unacceptable] = player.deck_list[CardType.unacceptable]

            emit('message', {'message': f"{player.role_id} 号玩家抽到了有难同当，并绑定为你", 'stage': [1, 2]},
                 room=and_player.sid)

    # 鱿鱼游戏
    if card_name == 'Squid-Game':
        message_str = card['cardDescription']

    # 赌徒
    if card_name == 'Gambler':
        message_str = card['cardDescription']

    # 十三幺
    if card_name == 'Thirteen-Orphans':
        player.reset_deck_list()
        for c_name in thirteenList:
            card_item = next((item for item in room.game_config['cardList'] if item['cardName'] == c_name), None)
            player.deck_list[card_item['cardType']].append(card_item)
        player.deck_list[card['cardType']].append(card)
        message_str = f"你抽到了十三幺卡牌，你的卡牌列表已被清空，你需要携带这十三张卡牌完成遭遇战，但十三幺卡牌可以被消除"

    # 欧皇附体
    if card_name == 'Lucky-Man':
        player.deck_list[card['cardType']].remove(card)
        message_str = '你可以直接从冲卡池中选取一张欧皇增益'

    # 倒霉蛋
    if card_name == 'Unlucky-Man':
        player.deck_list[card['cardType']].remove(card)
        random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, 5, True)
        player.deck_list[random_card['cardType']].append(random_card)
        message_str = f"已添加 {random_card['cardCnName']} 卡牌至重度不适中"

    # 天选者
    if card_name == 'The-Chosen-One':
        message_str = card['cardDescription']

    # 暴君
    if card_name == 'Tyrant':
        player.deck_list[card['cardType']].remove(card)

        all_count = 0
        for p_name, player_config in room.players.items():
            p = player_config['playerConfig']
            if p.role_id == player.role_id:
                continue
            for type_name, deck_list in p.deck_list.items():
                for card in deck_list:
                    card_type = card['cardType']
                    if card_type == CardType.micro_gain or card_type == CardType.strong_gain or card_type == CardType.opportunity:
                        if not (check_card_in_player_deck_list(room_id, player.player_name, card)):
                            all_count += 1

        if all_count == 0:
            emit('message', {'message': '当前没有任何人有增益卡牌，此卡作废', 'messageType': 'error', 'stage': [1, 2]})
        else:
            message_str = "你可以拿取任意一名玩家的增益卡片"
            player.special_config = {
                'send': player.role_id,
                'to': -1
            }
            special_by_tyrant(room_id, player.player_name, player.special_config)

    # 天使
    if card_name == 'Angel':
        player.deck_list[card['cardType']].remove(card)
        message_str = "你可以帮助任意一名玩家消除一张减益卡片"

    # 恶魔
    if card_name == 'Devil':
        player.deck_list[card['cardType']].remove(card)
        message_str = "你可以让任意一名玩家抽取一次对赌博弈"

    # 未来市场
    if card_name == "Future's-Market":
        message_str = card['cardDescription']

    # 强买强卖
    if card_name == 'Hard-Sells':
        player.deck_list[card['cardType']].remove(card)
        message_str = "你可以让任意一名队友购买你的异域武器售价为 10 货币"

    # 低帧率模式
    if card_name == 'Low-FPS':
        message_str = card['cardDescription']

    # 你在逗我吗？
    if card_name == 'Are-You-Kidding-Me':
        player.deck_list[card['cardType']].remove(card)

        list_number = [0, 0, 0, 0, 0, 0]

        for card_type, card_list in player.deck_list.items():
            cards_to_remove = card_list[:]
            for item in cards_to_remove:
                if item['cardType'] == CardType.micro_gain:
                    list_number[0] += 1
                if item['cardType'] == CardType.strong_gain:
                    list_number[1] += 1
                if item['cardType'] == CardType.opportunity:
                    list_number[2] += 1
                if item['cardType'] == CardType.micro_discomfort:
                    list_number[3] += 1
                if item['cardType'] == CardType.strong_discomfort:
                    list_number[4] += 1
                if item['cardType'] == CardType.unacceptable:
                    list_number[5] += 1
                delete_card({
                    "roomId": room_id,
                    "playerName": player_name,
                    "card": item
                })

        for index, i in enumerate(list_number):
            temp_list = [4, 5, 6, 1, 2, 3]
            for _ in range(list_number[index]):
                random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, temp_list[index], True)
                save_card({
                    "roomId": room_id,
                    "playerName": player_name,
                    "card": random_card
                })
                index += 1

        message_str = (f"你有 {list_number[0]} 张微弱增益，{list_number[1]} 张强大增益，"
                       f"{list_number[2]} 张欧皇增益，{list_number[3]} 张微弱不适，"
                       f"{list_number[4]} 张重度不适，{list_number[5]} 张反人类"
                       f"已替换成"
                       f"{list_number[3]} 张微弱增益，{list_number[4]} 张强大增益，"
                       f"{list_number[5]} 张欧皇增益，{list_number[0]} 张微弱不适，"
                       f"{list_number[1]} 张重度不适，{list_number[2]} 张反人类")

    # 力量的代价
    if card_name == 'The-Price-of-Power':
        message_str = card['cardDescription']

    # 苦肉计
    if card_name == 'The-Self-Torture-Scheme':
        message_str = card['cardDescription']

    # 这不是个人恩怨
    if card_name == 'This-isnt-a-Personal':
        player.deck_list[card['cardType']].remove(card)
        message_str = '指定一名队友去熔炉竞技场PM，先到7杀的玩家可以获取对方身上所有的正面效果卡牌，并把自己所有负面效果卡牌转移给对方'
        special_by_personal(room_id, player.player_name)

    # 不，你不能
    if card_name == 'You-Cant':
        message_str = card['cardDescription']

    # 忘了就是开了？
    if card_name == 'Forget':
        player.deck_list[card['cardType']].remove(card)
        random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, 1, True)
        player.draw_count += 1
        save_card({
            "roomId": room_id,
            "playerName": player_name,
            "card": random_card
        })
        message_str = '抽到此卡牌后，随机生成一张微弱增益替换该卡牌，同时额外获得一次卡牌抽取次数'

    # 光能庇护
    if card_name == 'Light-Blessing':
        player.deck_list[card['cardType']].remove(card)
        for card_type, card_list in player.deck_list.items():
            cards_to_remove = card_list[:]  # 复制整个列表
            for card in cards_to_remove:
                if (card['cardType'] == CardType.micro_discomfort or
                        card['cardType'] == CardType.strong_discomfort or
                        card['cardType'] == CardType.unacceptable):
                    delete_card({
                        "roomId": room_id,
                        "playerName": player_name,
                        "card": card
                    })

    # 观星
    if card_name == 'Stargazing':
        message_str = card['cardDescription']

    # 全局BP
    if card_name == 'Global-BP':
        message_str = card['cardDescription']

    # 卡牌回收计划
    if card_name == 'Card-Recycling-Program':
        message_str = card['cardDescription']

    # 海马的特殊规则
    if card_name == 'Special-Rules-For-Seahorses':
        player.deck_list[card['cardType']].remove(card)
        message_str = '把自己的卡池打乱，将第一张牌送入墓地（删除）并检索一张相同类型的牌'

    # 谢谢，不吃这套
    if card_name == 'I-Wont-Eat-This':
        message_str = card['cardDescription']

    # 不是，哥们
    if card_name == 'No-Buddy':
        message_str = card['cardDescription']

    # 人为财死
    if card_name == 'People-Die-For-Money':
        player.deck_list[card['cardType']].remove(card)
        message_str = '你可以直接获取一张增益卡牌，作为代价，你会随机获取一张与你的增益卡牌相对应级别的不适卡牌'

        player.special_config = {
            'send': player.role_id,
            'to': 0
        }

        special_by_money(room_id, player.player_name, player.special_config)

    # 拉姆蕾萨尔·华伦泰
    if card_name == 'Ramresar-Valentine':
        message_str = card['cardDescription']

    # 感觉不如
    if card_name == 'Feeling-Not-As-Good-As':
        player.deck_list[card['cardType']].remove(card)

        card_count = 0
        for card_type, card_list in player.deck_list.items():
            cards_to_remove = card_list[:]  # 复制整个列表
            for card in cards_to_remove:
                if (card['cardType'] == CardType.micro_gain or
                        card['cardType'] == CardType.strong_gain or
                        card['cardType'] == CardType.opportunity):
                    card_count += 1
                    delete_card({
                        "roomId": room_id,
                        "playerName": player_name,
                        "card": card
                    })

        for _ in range(card_count):
            random_num = random.randint(1, 8)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player_name,
                "card": random_card
            })

        message_str = f"已删除 {card_count} 张增益卡牌 已兑换成 {card_count} 张随机卡牌"

    # 上帝宽恕你
    if card_name == 'God-Forgive-You':
        player.deck_list[card['cardType']].remove(card)
        card_count = 0

        for c_name, c_list in player.deck_list.items():
            if c_name == CardType.micro_discomfort or c_name == CardType.strong_discomfort or c_name == CardType.unacceptable:
                c_to_remove = c_list[:]
                for c in c_to_remove:
                    card_count += 1
                    delete_card({
                        "roomId": room_id,
                        "playerName": player_name,
                        "card": c
                    })

        final_count = card_count // 2
        for _ in range(final_count):
            random_num = random.randint(1, 3)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player_name,
                "card": random_card
            })

        message_str = f"已删除 {card_count} 张不适卡牌 已兑换成 {final_count} 张随机增益卡牌"

    # 忧愁加冕
    if card_name == 'Crowning-Of-Sorrow':
        message_str = "取决于你的不适卡牌数量，每有2张可以依次选择获得一件忧愁武器（荆棘，恶意触碰，枯骨鳞片，渎职，枯萎囤积）"

    # 商店促销
    if card_name == 'Store-Promotions':
        message_str = "当你有这张卡牌的时候，你在商店购买东西全部为---五折!!!"

    # 分发信息
    if message_str == '':
        return
    if send_type == 'send':
        send({'type': 'specialCard', 'message': message_str, 'messageType': message_type, 'stage': [1, 2]}, to=room)
    else:
        emit('message', {'type': 'specialCard', 'message': message_str, 'messageType': message_type,
                         'stage': [1, 2]}, room=player.sid)
