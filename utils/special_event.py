from flask_socketio import emit, send

from entitys.card_type import CardType
from services import get_room, get_player, get_player_by_role_id
from utils import shuffle_list
from utils.card import check_card_in_player_deck_list
from utils.lottery import lottery_by_count


# 上贡
def special_by_tribute(room_id, player_name, special_config):
    room = get_room(room_id)
    player = get_player(room_id, player_name)
    to = special_config['to']

    list_1 = player.deck_list[CardType.micro_gain]
    list_2 = player.deck_list[CardType.strong_gain]
    list_3 = player.deck_list[CardType.opportunity]

    if len(list_1) == 0 and len(list_2) == 0 and len(list_3) == 0:
        player.player_status = ''
        player.special_config = ''
        emit('message', {'message': '你没有卡牌可以提供！此卡牌作废', 'messageType': 'error', 'stage': [1, 2]})
    else:
        tribute_list = list_1 + list_2 + list_3

        player.player_status = 'Tribute'
        special_config = {
            'title': '上贡',
            'description': f'从你的增益卡牌中挑选一张送给 {to} 号玩家',
            'type': 'cardList',
            'eventType': 'Tribute',
            'send': player.role_id,
            'to': to,
            'deckList': tribute_list,
        }
        player.special_config = special_config
        player.draw_card_type = ''
        room.card_status = ''

        emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 暴君
def special_by_tyrant(room_id, player_name, special_config):
    room = get_room(room_id)
    player = get_player(room_id, player_name)
    to = special_config['to']

    all_deck_list = []
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
                        card['roleId'] = p.role_id
                        all_deck_list.append(card)
                        all_count += 1

    if all_count == 0:
        player.player_status = ''
        player.special_config = ''
        emit('message', {'message': '当前没有任何人有增益卡牌，此卡作废', 'messageType': 'error', 'stage': [1, 2]})
    else:
        player.player_status = 'Tyrant'
        special_config = {
            'title': '暴君',
            'description': f'你可以拿取任意一名玩家的增益卡片',
            'type': 'cardList',
            'eventType': 'Tyrant',
            'send': player.role_id,
            'to': to,
            'deckList': all_deck_list,
        }
        player.special_config = special_config
        player.draw_card_type = ''
        room.card_status = ''

        emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 这不是个人恩怨
def special_by_personal(room_id, player_name):
    room = get_room(room_id)
    player = get_player(room_id, player_name)

    player_list = room.seats
    options_list = [
        {
            "text": "赢了",
            "value": True
        },
        {
            "text": "输了",
            "value": False
        }
    ]
    player.player_status = 'Personal'
    special_config = {
        'title': '这不是个人恩怨',
        'description': f'指定一名队友去熔炉竞技场PM，先到7杀的玩家可以获取对方身上所有的正面效果卡牌，并把自己所有负面效果卡牌转移给对方',
        'type': 'playerList',
        'eventType': 'Personal',
        'send': player.role_id,
        'to': -1,
        'playerList': player_list,
        'optionsList': options_list
    }
    player.special_config = special_config
    player.draw_card_type = ''
    room.card_status = ''

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 人为财死
def special_by_money(room_id, player_name, special_config):
    room = get_room(room_id)
    player = get_player(room_id, player_name)
    to = special_config['to']

    deck_list = [
        {
            'cardType': CardType.micro_gain,
            'cardCnName': '微弱增益',
            'cardDescription': '选择微弱增益',
        },
        {
            'cardType': CardType.strong_gain,
            'cardCnName': '强大增益',
            'cardDescription': '选择强大增益',
        },
        {
            'cardType': CardType.opportunity,
            'cardCnName': '欧皇增益',
            'cardDescription': '选择欧皇增益',
        }
    ]
    player.player_status = 'Die-For-Money'
    special_config = {
        'title': '人为财死',
        'description': f'你可以直接获取一张增益卡牌，作为代价，你会随机获取一张与你的增益卡牌相对应级别的不适卡牌',
        'type': 'cardList',
        'eventType': 'Die-For-Money',
        'send': player.role_id,
        'to': to,
        'deckList': deck_list
    }
    player.special_config = special_config
    player.draw_card_type = ''
    room.card_status = ''

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 顺手牵羊
def special_by_take_others(room_id, player_name, special_config):
    room = get_room(room_id)
    player = get_player(room_id, player_name)
    to = special_config['to']

    to_player = get_player_by_role_id(room_id, to)
    all_deck_list = []
    all_count = 0
    for type_name, deck_list in to_player.deck_list.items():
        for card in deck_list:
            if not (check_card_in_player_deck_list(room_id, player.player_name, card)):
                card['roleId'] = to_player.role_id
                all_count += 1
                all_deck_list.append(card)

    if all_count <= 0:
        player.player_status = ''
        player.special_config = ''
        emit('message', {'message': '当前没有任何人有卡牌，此事件作废', 'messageType': 'error', 'stage': [1, 2]})
    else:
        all_deck_list = shuffle_list(all_deck_list)
        player.player_status = 'Take-Others'
        special_config = {
            'title': '顺手牵羊',
            'description': f'你可以拿取 {to} 号玩家的一张卡片',
            'type': 'cardList',
            'eventType': 'Take-Others',
            'send': player.role_id,
            'to': to,
            'deckList': all_deck_list,
        }
        player.special_config = special_config

        emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 赢下所有或一无所有
def special_by_win_or_loss(room_id, player_name):
    player = get_player(room_id, player_name)

    options_list = [
        {
            "text": 20,
            "value": 20
        },
        {
            "text": 1,
            "value": 1
        },
        {
            "text": "无事发生",
            "value": 0
        }
    ]
    player.player_status = 'Win-or-Loss'
    special_config = {
        'title': '赢下所有或一无所有',
        'description': f'使用 steam /random 20 大成功（数字20）获得三个额外强大增益/大失败（数字1）获得三个额外强大减益其余无事发生',
        'type': 'optionsList',
        'eventType': 'Win-or-Loss',
        'send': player.role_id,
        'to': 0,
        'optionsList': options_list,
    }
    player.special_config = special_config

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 幸运数字
def special_by_lucky_number(room_id, player_name):
    player = get_player(room_id, player_name)

    options_list = [
        {
            "text": "7/14/17",
            "value": 7
        },
        {
            "text": "2的倍数",
            "value": 2
        },
        {
            "text": "无事发生",
            "value": 0
        }
    ]
    player.player_status = 'Win-or-Loss'
    special_config = {
        'title': '幸运数字',
        'description': f'使用 steam /random 20，若点数为 7，14，17 获得一个额外增益 若点数为 2 的倍数获得一个额外减益其余无事发生',
        'type': 'optionsList',
        'eventType': 'Lucky-Number',
        'send': player.role_id,
        'to': 0,
        'optionsList': options_list,
    }
    player.special_config = special_config

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 内鬼
def special_by_spy(room_id, player_name):
    player = get_player(room_id, player_name)

    options_list = [
        {
            "text": "成功",
            "value": True
        },
        {
            "text": "失败",
            "value": False
        }
    ]
    player.player_status = 'Spy'
    special_config = {
        'title': '内鬼',
        'description': f'本次遭遇战中，你必须使队伍团灭一次（仅限机制强灭），如果成功将获得增益buff，失败将获得减益buff（你的队友不能知道这张卡牌的存在，如果知道并配合团灭，直接失败！）',
        'type': 'optionsList',
        'eventType': 'Spy',
        'send': player.role_id,
        'to': 0,
        'optionsList': options_list,
    }
    player.special_config = special_config

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 噶点放心飞，出事自己背
def special_by_self(room_id, player_name):
    player = get_player(room_id, player_name)

    options_list = [
        {
            "text": "死亡 1 次",
            "value": 1
        },
        {
            "text": "死亡 2 次",
            "value": 2
        },
        {
            "text": "死亡 3 次",
            "value": 3
        },
        {
            "text": "未死亡",
            "value": 0
        }
    ]
    player.player_status = 'Self'
    special_config = {
        'title': '噶点放心飞，出事自己背',
        'description': f'在当前遭遇战中，你如果死亡将会根据死亡次数获得对应的减益buff数量，你如果未死亡将会获得一张增益卡和一把异域武器',
        'type': 'optionsList',
        'eventType': 'Self',
        'send': player.role_id,
        'to': 0,
        'optionsList': options_list,
    }
    player.special_config = special_config

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# Alex Mercer
def special_by_alex_mercer(room_id, player_name):
    room = get_room(room_id)
    player = get_player(room_id, player_name)

    player_list = room.seats
    options_list = [
        {
            "text": "指定的人死亡了",
            "value": True
        },
        {
            "text": "指定的人未死亡",
            "value": False
        }
    ]
    player.player_status = 'Alex-Mercer'
    special_config = {
        'title': 'Alex-Mercer',
        'description': f'你可以指定一个号码玩家，若该名玩家在遭遇战中死亡，则你会获得他身上的所有物品（货币，抽取卡牌次数，手卡，商店所购买的物品）',
        'type': 'playerList',
        'eventType': 'Alex-Mercer',
        'send': player.role_id,
        'to': -1,
        'playerList': player_list,
        'optionsList': options_list
    }
    player.special_config = special_config
    player.draw_card_type = ''
    room.card_status = ''

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 你知道的，这是交易
def special_by_you_know(room_id, player_name):
    room = get_room(room_id)
    player = get_player(room_id, player_name)

    player_list = room.seats
    options_list = [
        {
            "text": "完成",
            "value": True
        },
        {
            "text": "拒绝/未完成",
            "value": False
        }
    ]
    player.player_status = 'This-Is-The-Deal'
    special_config = {
        'title': '你知道的，这是交易',
        'description': f'请选择你指定的玩家',
        'type': 'playerList',
        'eventType': 'This-Is-The-Deal',
        'send': player.role_id,
        'to': -1,
        'playerList': player_list,
        'optionsList': options_list
    }
    player.special_config = special_config
    player.draw_card_type = ''
    room.card_status = ''

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 以存护之名
def special_by_preservation(room_id, player_name):
    room = get_room(room_id)
    player = get_player(room_id, player_name)

    player_list = room.seats
    options_list = [
        {
            "text": "成功",
            "value": True
        },
        {
            "text": "失败",
            "value": False
        }
    ]
    player.player_status = 'In-The-Name-of-Preservation'
    special_config = {
        'title': '以存护之名',
        'description': f'请选择你指定的玩家',
        'type': 'playerList',
        'eventType': 'In-The-Name-of-Preservation',
        'send': player.role_id,
        'to': -1,
        'playerList': player_list,
        'optionsList': options_list
    }
    player.special_config = special_config
    player.draw_card_type = ''
    room.card_status = ''

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})


# 五谷丰登
def special_by_bumper_harvest(room_id, players):
    room = get_room(room_id)

    all_deck_list = []
    player_list = players[:]
    for _ in range(6):
        random_card = lottery_by_count(room.game_config['cardList'])
        all_deck_list.append(random_card)

    all_deck_list = shuffle_list(all_deck_list)
    special_config = {
        'title': '五谷丰登',
        'description': f'每个玩家都能拿走一张卡牌',
        'type': 'cardList',
        'eventType': 'Bumper-Harvest',
        'send': 7,
        'to': -1,
        'players': player_list,
        'nowPlayer': 0,
        'deckList': all_deck_list,
    }

    for p_name, p_config in room.players.items():
        p = p_config['playerConfig']
        p.player_status = 'Bumper-Harvest'
        p.special_config = special_config

    send({'type': 'showSpecialDialog', 'specialConfig': special_config})

# 移形换位
def special_by_move(room_id, player_name):
    room = get_room(room_id)
    player = get_player(room_id, player_name)

    player_list = room.seats
    options_list = [
        {
            "text": "确认",
            "value": True
        }
    ]
    player.player_status = 'Transposition'
    special_config = {
        'title': '移形换位',
        'description': f'指定两名队友，让他们所有的卡牌互换',
        'type': 'playerList',
        'eventType': 'Transposition',
        'send': player.role_id,
        'to': -1,
        'playerList': player_list,
        'optionsList': options_list
    }
    player.special_config = special_config
    player.draw_card_type = ''
    room.card_status = ''

    emit('message', {'type': 'showSpecialDialog', 'specialConfig': special_config})

# 生化母体
def special_by_matrix(room_id, players):
    room = get_room(room_id)

    all_deck_list = []
    player_list = players[:]
    while len(all_deck_list) < 6:
        random_card = lottery_by_count(room.game_config['cardList'])
        random_card_type = random_card['cardType']
        if random_card_type == CardType.micro_discomfort or random_card_type == CardType.strong_discomfort or random_card_type == CardType.unacceptable:
            all_deck_list.append(random_card)

    all_deck_list = shuffle_list(all_deck_list)
    special_config = {
        'title': '生化母体',
        'description': f'每个玩家都能拿走一张卡牌',
        'type': 'cardList',
        'eventType': 'Biochemical-Matrix',
        'send': 7,
        'to': -1,
        'players': player_list,
        'nowPlayer': 0,
        'deckList': all_deck_list,
    }

    for p_name, p_config in room.players.items():
        p = p_config['playerConfig']
        p.player_status = 'Biochemical-Matrix'
        p.special_config = special_config

    send({'type': 'showSpecialDialog', 'specialConfig': special_config})
