# 检查 卡牌是否在 玩家列表里
from services import get_player


def check_card_in_player_deck_list(room_id, player_name, item):
    player = get_player(room_id, player_name)

    for card_type, card_list in player.deck_list.items():
        for card in card_list:
            if item['cardName'] == card['cardName']:
                # 类型判断
                # print(f"类型判断 {item['cardName']} == {card['cardName']}: {item['cardName'] == card['cardName']}")
                return True

    return False
