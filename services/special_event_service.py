import random

from flask_socketio import emit, send

from entitys.card_type import CardType
from services import get_player_by_role_id, save_card, get_room, get_player, delete_card, \
    get_random_card_by_type_and_player_deck_list
from socketio_instance import socketio


# 特殊事件处理
@socketio.on('runSpecialByCard')
def run_special_by_card(data):
    room_id = data['roomId']
    special_config = data['specialConfig']
    card = data['card']
    player = get_player_by_role_id(room_id, special_config['send'])

    event_type = special_config['eventType']

    # 上贡
    if event_type == 'Tribute':
        player_1 = get_player_by_role_id(room_id, special_config['send'])
        player_2 = get_player_by_role_id(room_id, special_config['to'])

        if player_1 is not None and player_2 is not None:
            delete_card({
                "roomId": room_id,
                "playerName": player_1.player_name,
                "card": card
            })

            save_card({
                "roomId": room_id,
                "playerName": player_2.player_name,
                "card": card
            })

    # 暴君
    if event_type == 'Tyrant':
        player_1 = get_player_by_role_id(room_id, special_config['send'])
        player_2 = get_player_by_role_id(room_id, special_config['to'])

        if player_1 is not None and player_2 is not None:
            delete_card({
                "roomId": room_id,
                "playerName": player_2.player_name,
                "card": card
            })

            save_card({
                "roomId": room_id,
                "playerName": player_1.player_name,
                "card": card
            })

    # 人为财死
    if event_type == 'Die-For-Money':

        card_type_1 = 0
        card_type_2 = 0
        if special_config['selectType'] == CardType.micro_gain:
            card_type_1 = 1
            card_type_2 = 4
        if special_config['selectType'] == CardType.strong_gain:
            card_type_1 = 2
            card_type_2 = 5
        if special_config['selectType'] == CardType.opportunity:
            card_type_1 = 3
            card_type_2 = 6

        random_card_1 = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, card_type_1, True)
        random_card_2 = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, card_type_2, True)

        save_card({
            "roomId": room_id,
            "playerName": player.player_name,
            "card": random_card_1
        })

        save_card({
            "roomId": room_id,
            "playerName": player.player_name,
            "card": random_card_2
        })

    # 顺手牵羊
    if event_type == 'Take-Others':
        to_player = get_player_by_role_id(room_id, special_config['to'])

        delete_card({
            "roomId": room_id,
            "playerName": to_player.player_name,
            "card": card
        })

        emit('message',
             {'message': f"你的 {card['cardCnName']} 被 {player.role_id} 号玩家抽走了", 'messageType': 'warning',
              'stage': [1, 2]}, room=to_player.sid)

        save_card({
            "roomId": room_id,
            "playerName": player.player_name,
            "card": card
        })

        emit('message', {'message': f"你抽到了 {card['cardCnName']}", 'messageType': 'warning', 'stage': [1, 2]},
             room=player.sid)

    # 五谷丰登
    if event_type == 'Bumper-Harvest':
        players = special_config['players'][:]
        now_player = special_config['nowPlayer']
        print(players)
        to_player = get_player_by_role_id(room_id, players[now_player])

        save_card({
            "roomId": room_id,
            "playerName": to_player.player_name,
            "card": card
        })

        special_config['nowPlayer'] += 1
        special_config['deckList'].remove(card)

        room = get_room(room_id)
        if len(special_config['deckList']) <= 0:
            for p_name, p_config in room.players.items():
                p = p_config['playerConfig']
                p.player_status = ''
                p.special_config = ''
        else:
            for p_name, p_config in room.players.items():
                p = p_config['playerConfig']
                p.player_status = 'Bumper-Harvest'
                p.special_config = special_config

        send({'message': f"{to_player.role_id} 号玩家 拿走了 {card['cardCnName']}", 'messageType': 'warning', 'stage': [1, 2]}, to=room)

    # 生化母体
    if event_type == 'Biochemical-Matrix':
        players = special_config['players'][:]
        now_player = special_config['nowPlayer']
        print(players)
        to_player = get_player_by_role_id(room_id, players[now_player])

        save_card({
            "roomId": room_id,
            "playerName": to_player.player_name,
            "card": card
        })

        special_config['nowPlayer'] += 1
        special_config['deckList'].remove(card)

        room = get_room(room_id)
        if len(special_config['deckList']) <= 0:
            for p_name, p_config in room.players.items():
                p = p_config['playerConfig']
                p.player_status = ''
                p.special_config = ''
        else:
            for p_name, p_config in room.players.items():
                p = p_config['playerConfig']
                p.player_status = 'Biochemical-Matrix'
                p.special_config = special_config

        send({'message': f"{to_player.role_id} 号玩家 拿走了 {card['cardCnName']}", 'messageType': 'warning', 'stage': [1, 2]}, to=room)


    if player is not None:
        player.player_status = ''
        player.special_config = ''

    emit('message', {'type': 'hideSpecialDialog', 'stage': [1, 2]})


# 特殊事件处理
@socketio.on('runSpecialEvent')
def run_special_by_event(data):
    room_id = data['roomId']
    special_config = data['specialConfig']
    player = get_player_by_role_id(room_id, special_config['send'])

    event_type = special_config['eventType']

    # 这不是个人恩怨
    if event_type == 'Personal':
        to_player = get_player_by_role_id(room_id, special_config['to'])

        if special_config['value']:
            to_player_deck_list = []
            for c_type, c_list in to_player.deck_list.items():
                c_to_remove = c_list[:]
                for c in c_to_remove:
                    if c_type == CardType.micro_gain or c_type == CardType.strong_gain or c_type == CardType.opportunity:
                        to_player_deck_list.append(c)
                        delete_card({
                            "roomId": room_id,
                            "playerName": to_player.player_name,
                            "card": c
                        })

            player_deck_list = []
            for c_type, c_list in player.deck_list.items():
                c_to_remove = c_list[:]
                for c in c_to_remove:
                    if c_type == CardType.micro_discomfort or c_type == CardType.strong_discomfort or c_type == CardType.unacceptable:
                        player_deck_list.append(c)
                        delete_card({
                            "roomId": room_id,
                            "playerName": player.player_name,
                            "card": c
                        })

            for c in to_player_deck_list:
                save_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": c
                })

            for c in player_deck_list:
                save_card({
                    "roomId": room_id,
                    "playerName": to_player.player_name,
                    "card": c
                })
        else:
            player_deck_list = []
            for c_type, c_list in player.deck_list.items():
                c_to_remove = c_list[:]
                for c in c_to_remove:
                    if c_type == CardType.micro_gain or c_type == CardType.strong_gain or c_type == CardType.opportunity:
                        player_deck_list.append(c)
                        delete_card({
                            "roomId": room_id,
                            "playerName": player.player_name,
                            "card": c
                        })

            to_player_deck_list = []
            for c_type, c_list in to_player.deck_list.items():
                c_to_remove = c_list[:]
                for c in c_to_remove:
                    if c_type == CardType.micro_discomfort or c_type == CardType.strong_discomfort or c_type == CardType.unacceptable:
                        to_player_deck_list.append(c)
                        delete_card({
                            "roomId": room_id,
                            "playerName": to_player.player_name,
                            "card": c
                        })

            for c in player_deck_list:
                save_card({
                    "roomId": room_id,
                    "playerName": to_player.player_name,
                    "card": c
                })

            for c in to_player_deck_list:
                save_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": c
                })

        emit('message', {'message': '因为 这不是个人恩怨 卡牌已经为你们进行卡牌互换', 'stage': [1, 2]}, room=player.sid)
        emit('message', {'message': '因为 这不是个人恩怨 卡牌已经为你们进行卡牌互换', 'stage': [1, 2]},
             room=to_player.sid)

    # 赢下所有或一无所有
    if event_type == 'Win-or-Loss':
        point = special_config['value']

        if point == 20:
            for _ in range(3):
                random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, 2, True)
                save_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": random_card
                })
            emit('message', {'message': '大成功！获得三张强大增益', 'messageType': 'success', 'stage': [1, 2]})
        elif point == 1:
            for _ in range(3):
                random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, 5, True)
                save_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": random_card
                })
            emit('message', {'message': '大失败！获得三张重度不适', 'messageType': 'error', 'stage': [1, 2]})
        else:
            emit('message', {'message': '无事发生', 'messageType': 'warning', 'stage': [1, 2]})

    # 幸运数字
    if event_type == 'Lucky-Number':
        point = special_config['value']

        if point == 7:
            random_num = random.randint(1, 3)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": random_card
            })
            emit('message', {'message': '777！获得一张增益卡牌', 'messageType': 'success', 'stage': [1, 2]})
        elif point == 2:
            random_num = random.randint(4, 6)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": random_card
            })
            emit('message', {'message': '2倍速！获得一张减益卡牌', 'messageType': 'error', 'stage': [1, 2]})
        else:
            emit('message', {'message': '无事发生', 'messageType': 'warning', 'stage': [1, 2]})

    # 内鬼
    if event_type == 'Spy':
        value = special_config['value']

        if value:
            random_num = random.randint(1, 3)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": random_card
            })
            emit('message', {'message': '恭喜你成功！获得一张增益卡牌', 'messageType': 'success', 'stage': [1, 2]})
        else:
            random_num = random.randint(4, 6)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": random_card
            })
            emit('message', {'message': '这能失败？获得一张减益卡牌', 'messageType': 'error', 'stage': [1, 2]})

    # 噶点放心飞，出事自己背
    if event_type == 'Self':
        value = special_config['value']

        if value > 0:
            for _ in range(value):
                random_num = random.randint(4, 6)
                random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, random_num,
                                                                           True)
                save_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": random_card
                })
            emit('message', {'message': f'出事自己背！获得 {value} 张减益卡牌', 'messageType': 'error', 'stage': [1, 2]})
        else:
            random_num = random.randint(1, 3)
            random_card = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, random_num, True)
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": random_card
            })
            emit('message', {'message': '获得一张增益卡牌和一把异域武器', 'messageType': 'success', 'stage': [1, 2]})

    # Alex - Mercer
    if event_type == 'Alex-Mercer':
        value = special_config['value']
        to = special_config['to']

        if value:
            to_player = get_player_by_role_id(room_id, to)

            player.player_money += to_player.player_money
            to_player.player_money = 0
            player.draw_count += to_player.draw_count
            to_player.draw_count = 0

            for c_type, c_list in to_player.deck_list.items():
                c_to_remove = c_list[:]
                for c in c_to_remove:
                    delete_card({
                        "roomId": room_id,
                        "playerName": to_player.player_name,
                        "card": c
                    })
                    save_card({
                        "roomId": room_id,
                        "playerName": player.player_name,
                        "card": c
                    })

            back_to_remove = to_player.backpack[:]

            for item in back_to_remove:
                player.backpack.append(item)
                to_player.backpack.remove(item)

            emit('message', {'message': '以为你自动获取该玩家物品', 'messageType': 'success', 'stage': [1, 2]})
            emit('message', {'message': '因为你被 Alex_Mercer 选中了，你的所有东西都消失了', 'messageType': 'error',
                             'stage': [1, 2]}, room=to_player.sid)

    # 你知道的，这是交易
    if event_type == 'This-Is-The-Deal':
        value = special_config['value']
        to_player = get_player_by_role_id(room_id, special_config['to'])
        temp_deck_list = []

        if value:
            for c_type, c_list in player.deck_list.items():
                for c in c_list:
                    temp_deck_list.append(c)

            if len(temp_deck_list) <= 0:
                emit('message', {'message': '你当前没有卡牌可以给他', 'messageType': 'error', 'stage': [1, 2]})
                emit('message', {'message': '他当前没有卡牌给你', 'messageType': 'error',
                                 'stage': [1, 2]}, room=to_player.sid)
            else:
                random_card = random.choices(temp_deck_list)

                delete_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": random_card[0]
                })
                save_card({
                    "roomId": room_id,
                    "playerName": to_player.player_name,
                    "card": random_card[0]
                })

                emit('message', {'message': '你损失了一张卡牌', 'messageType': 'error', 'stage': [1, 2]})
                emit('message', {'message': '你获得了一张卡牌', 'messageType': 'success',
                                 'stage': [1, 2]}, room=to_player.sid)
        else:
            for c_type, c_list in to_player.deck_list.items():
                for c in c_list:
                    temp_deck_list.append(c)

            if len(temp_deck_list) <= 0:
                emit('message', {'message': '他当前没有卡牌给你', 'messageType': 'error', 'stage': [1, 2]})
                emit('message', {'message': '你当前没有卡牌可以给他', 'messageType': 'error',
                                 'stage': [1, 2]}, room=to_player.sid)
            else:
                random_card = random.choices(temp_deck_list)

                delete_card({
                    "roomId": room_id,
                    "playerName": to_player.player_name,
                    "card": random_card[0]
                })
                save_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": random_card[0]
                })

                emit('message', {'message': '你获得了一张卡牌', 'messageType': 'success', 'stage': [1, 2]})
                emit('message', {'message': '你损失了一张卡牌', 'messageType': 'error',
                                 'stage': [1, 2]}, room=to_player.sid)

    # 以存护之名
    if event_type == 'In-The-Name-of-Preservation':
        value = special_config['value']
        to_player = get_player_by_role_id(room_id, special_config['to'])

        if value:
            random_card_player = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, 2, True)
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": random_card_player
            })
            random_card_to_player = get_random_card_by_type_and_player_deck_list(room_id, player.player_name, 2, True)
            save_card({
                "roomId": room_id,
                "playerName": to_player.player_name,
                "card": random_card_to_player
            })

            emit('message',
                 {'message': '已完成 以存护之名 事件，获得一张强大增益卡牌', 'messageType': 'success', 'stage': [1, 2]})
            emit('message',
                 {'message': '已完成 以存护之名 事件，获得一张强大增益卡牌', 'messageType': 'success', 'stage': [1, 2]},
                 room=to_player.sid)
        else:
            temp_deck_list = []

            for c_type, c_list in player.deck_list.items():
                for c in c_list:
                    if c['cardType'] == CardType.micro_gain or c['cardType'] == CardType.strong_gain or c[
                        'cardType'] == CardType.opportunity:
                        temp_deck_list.append(c)

            if len(temp_deck_list) <= 0:
                emit('message', {'message': '你当前没有卡牌可以丢弃', 'messageType': 'error', 'stage': [1, 2]})
            else:
                random_card = random.choices(temp_deck_list)
                delete_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": random_card[0]
                })
                emit('message', {'message': '因为你失败了，失去一张增益卡牌', 'messageType': 'error', 'stage': [1, 2]})

    # 移形换位
    if event_type == 'Transposition':
        to_player = get_player_by_role_id(room_id, special_config['to'])

        to_player_deck_list = []
        for c_type, c_list in to_player.deck_list.items():
            c_to_remove = c_list[:]
            for c in c_to_remove:
                to_player_deck_list.append(c)
                delete_card({
                    "roomId": room_id,
                    "playerName": to_player.player_name,
                    "card": c
                })

        player_deck_list = []
        for c_type, c_list in player.deck_list.items():
            c_to_remove = c_list[:]
            for c in c_to_remove:
                player_deck_list.append(c)
                delete_card({
                    "roomId": room_id,
                    "playerName": player.player_name,
                    "card": c
                })

        for c in to_player_deck_list:
            save_card({
                "roomId": room_id,
                "playerName": player.player_name,
                "card": c
            })

        for c in player_deck_list:
            save_card({
                "roomId": room_id,
                "playerName": to_player.player_name,
                "card": c
            })

        room = get_room(room_id)
        for p_name, p_config in room.players.items():
            p = p_config['playerConfig']
            p.player_status = ''
            p.special_config = ''

        emit('message', {'message': f"已触发移形换位时间你的卡牌已被交换", 'messageType': 'warning', 'stage': [1, 2]}, room=player.sid)
        emit('message', {'message': f"已触发移形换位时间你的卡牌已被交换", 'messageType': 'warning', 'stage': [1, 2]},
             room=to_player.sid)

    player.player_status = ''
    player.special_config = ''

    emit('message', {'type': 'hideSpecialDialog', 'stage': [1, 2]})
