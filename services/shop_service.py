import random

from flask_socketio import send, emit

from entitys.card_type import CardType
from services import get_room, get_player, delete_card
from socketio_instance import socketio
from utils.lottery import lottery


# 刷新商店
@socketio.on('refreshShop')
def refresh_shop(data):
    room_id = data['roomId']
    room = get_room(room_id)
    shop_config = room.shop_config

    refresh_mod = 'free' if shop_config['refreshCount'] >= 1 else 'pay'

    # 判断刷新类型
    if refresh_mod == 'free':
        shop_config['refreshCount'] -= 1
    else:
        need_money = shop_config['refreshMoney'] // 6
        for player_name, player in room.players.items():
            if player['playerConfig'].player_money < need_money:
                send({'message': '在场的玩家有人的货币不足，无法刷新商店', 'messageType': 'error', 'stage': [1, 2]},
                     to=room)
                return

        for player_name, player in room.players.items():
            player['playerConfig'].player_money -= need_money

        shop_config['refreshMoney'] += 6

        send({'message': f'因为没有免费刷新次数，所以花费了 {need_money} 刷新商店物品',
              'messageType': 'warning', 'stage': [1, 2]}, to=room)

    # 重置商店列表
    shop_config['itemList'] = []
    shop_config['weaponList'] = []
    shop_config['exoticList'] = []

    # 物品列表
    for _ in range(9):
        item_list = [i for i in shop_config['shopItem'] if i['typeName'] == 'water']
        item = lottery(item_list)
        item['count'] = 1
        shop_config['itemList'].append(item)

    card_item = (next(i for i in shop_config['shopItem'] if i['typeName'] == 'drawCount'), None)
    card_item[0]['count'] = random.randint(3, 6)
    shop_config['itemList'].append(card_item[0])

    # 武器列表
    for _ in range(10):
        weapon_list = [i for i in shop_config['shopItem'] if i['typeName'] == 'weapon']
        weapon = lottery(weapon_list)
        weapon['count'] = 1
        shop_config['weaponList'].append(weapon)

    # 异域装备列表（武器）
    for _ in range(4):
        while len(shop_config['exoticList']) < 4:
            exotic_weapon = lottery(shop_config['exoticWeaponList'])
            if not (exotic_weapon in shop_config['exoticList']):
                exotic_weapon['count'] = 2
                shop_config['exoticList'].append(exotic_weapon)

    # 异域装备列表（护甲）
    for _ in range(6):
        while len(shop_config['exoticList']) < 10:
            exotic_armor = lottery(shop_config['exoticArmorList'])
            if not (exotic_armor in shop_config['exoticList']):
                exotic_armor['count'] = 2
                shop_config['exoticList'].append(exotic_armor)

    send({'message': '刷新商店成功，去看看有什么东西吧！', 'messageType': 'success', 'stage': [1, 2]}, to=room)


# 购买物品
@socketio.on('buyItem')
def buy_item(data):
    room_id = data['roomId']
    player_name = data['playerName']
    type_list = data['typeList']
    item_index = data['itemIndex']

    room = get_room(room_id)
    shop_config = room.shop_config

    item = shop_config[type_list][item_index]

    sell = item['sell']
    player = get_player(room_id, player_name)

    if player.zero_buy > 0:
        player.zero_buy -= 1
        sell = 0
        send({'message': f"玩家 {player.player_name} 发动了 0 元购技能", 'messageType': 'warning', 'stage': [1, 2]},
             to=room)
    if player.player_attributes['profiteer'] and player.zero_buy <= 0:
        sell += 1
    if player.player_attributes['promotions'] and player.zero_buy <= 0:
        sell = sell / 2

    if player.player_money < sell and player.zero_buy <= 0 and not player.player_attributes['market']:
        emit('message', {'message': '货币不足，无法购买', 'messageType': 'error', 'stage': [1, 2]})
        return

    if player.player_attributes['market'] and item['typeName'] == 'water':
        emit('message', {'message': '未来市场不能买圣水哦！', 'messageType': 'warning', 'stage': [1, 2]})
        return

    if item['typeName'] == 'water':
        buy_water(room_id, player_name, item, item_index, sell)
    if item['typeName'] == 'drawCount':
        buy_draw_count(room_id, player_name, item_index, sell)
    if item['typeName'] == 'weapon':
        buy_weapon(room_id, player_name, item, item_index, sell)
    if item['typeName'] == 'Weapons' or item['typeName'] == 'Armor':
        buy_exotic_item(room_id, player_name, item, item_index, sell)

    send({'message': f"玩家 {player.player_name} 购买了 {item['cnName']}", 'messageType': 'warning', 'stage': [1, 2]},
         to=room)


# 买圣水
def buy_water(room_id, player_name, item, item_index, sell):
    player = get_player(room_id, player_name)
    room = get_room(room_id)
    shop_config = room.shop_config

    del shop_config['itemList'][item_index]
    player.backpack.append(item)
    player.player_money -= sell

    emit('message', {'message': '购买圣水成功', 'messageType': 'success', 'stage': [1, 2]})


# 买抽卡次数
def buy_draw_count(room_id, player_name, item_index, sell):
    player = get_player(room_id, player_name)
    room = get_room(room_id)
    shop_config = room.shop_config

    shop_config['itemList'][item_index]['count'] -= 1
    if shop_config['itemList'][item_index]['count'] == 0:
        del shop_config['itemList'][item_index]

    player.draw_count += 1
    player.player_money -= sell

    emit('message', {'message': '购买抽卡次数成功', 'messageType': 'success', 'stage': [1, 2]})


# 购买武器
def buy_weapon(room_id, player_name, item, item_index, sell):
    player = get_player(room_id, player_name)
    room = get_room(room_id)
    shop_config = room.shop_config

    del shop_config['weaponList'][item_index]

    player.backpack.append(item)
    player.player_money -= sell

    # 恶魔契约
    if player.devilspact != 0:
        player.devilspact -= 1
        player.draw_count += 1
        emit('message', {'message': "触发恶魔契约成功", 'messageType': 'success', 'stage': [1, 2]})

    emit('message', {'message': f"购买 {item['cnName']} 成功", 'messageType': 'success', 'stage': [1, 2]})


# 购买异域装备
def buy_exotic_item(room_id, player_name, item, item_index, sell):
    player = get_player(room_id, player_name)
    room = get_room(room_id)
    shop_config = room.shop_config

    shop_config['exoticList'][item_index]['count'] -= 1
    if shop_config['exoticList'][item_index]['count'] == 0:
        del shop_config['exoticList'][item_index]

    item['count'] = 1
    player.backpack.append(item)
    player.player_money -= sell

    # 恶魔契约
    if player.devilspact != 0:
        player.devilspact -= 1
        player.draw_count += 1
        emit('message', {'message': "触发恶魔契约成功", 'messageType': 'success', 'stage': [1, 2]})

    emit('message', {'message': f"购买 {item['cnName']} 成功", 'messageType': 'success', 'stage': [1, 2]})


# 开启商店
@socketio.on('openShop')
def open_shop(data):
    room_id = data['roomId']
    player_name = data['playerName']

    player = get_player(room_id, player_name)

    if player.player_money < 12:
        emit('message', {'type': 'message', 'message': '你需要 12 个货币才能解锁商店',
                         'messageType': 'error', 'stage': [1, 2]})
        return

    player.player_money -= 12

    card_item = find_card_by_name_in_player_card_list(player, 'Stillwater-Prison')

    delete_card({
        "roomId": room_id,
        "playerName": player_name,
        "card": card_item
    })

    emit('message', {'type': 'message', 'message': '您已重新开启商店系统',
                     'messageType': 'success', 'stage': [1, 2]})


# 根据卡牌名称寻找卡牌
def find_card_by_name_in_player_card_list(player, card_name):
    for type_name, card_list in player.deck_list.items():
        for card in card_list:
            if card['cardName'] == card_name:
                return card
    return None


# 使用圣水
@socketio.on('useItem')
def use_item(data):
    room_id = data['roomId']
    player_name = data['playerName']
    backpack_index = data['backpackIndex']

    player = get_player(room_id, player_name)

    item = player.backpack[backpack_index]

    if item['typeName'] != 'water':
        emit('message', {'message': '这个东西不能使用，别点了', 'messageType': 'error', 'stage': [1, 2]})
        return

    deck_list = []

    if item['itemName'] == 'water1':
        deck_list = player.deck_list[CardType.micro_discomfort]
    elif item['itemName'] == 'water2':
        deck_list = player.deck_list[CardType.strong_discomfort]
    elif item['itemName'] == 'water3':
        deck_list = player.deck_list[CardType.unacceptable]
    elif item['itemName'] == 'water7':
        deck_list = player.deck_list[CardType.technology]

    if len(deck_list) <= 0:
        emit("message", {'message': f"你当前没有可以消除的卡牌", 'messageType': 'error', 'stage': [1, 2]})
        return

    emit("showWaterDeckList", {'message': "请选择要消除的卡牌", 'messageType': 'warning', 'stage': [1, 2],
                               'deckList': deck_list})

    emit("message", {'stage': [1, 2]})


# 删除卡牌
@socketio.on('deleteCardItem')
def delete_card_item(data):
    room_id = data['roomId']
    player_name = data['playerName']
    card_type = data['cardType']
    card_index = data['cardIndex']
    backpack_index = data['backpackIndex']

    player = get_player(room_id, player_name)

    card = player.deck_list[card_type][card_index]
    delete_card({
        "roomId": room_id,
        "playerName": player_name,
        "card": card
    })

    del player.backpack[backpack_index]

    emit("hideWaterDeckList", {'message': f"消除 {card['cardCnName']} 成功", 'messageType': 'success'})
    emit("message", {'stage': [1, 2]})
