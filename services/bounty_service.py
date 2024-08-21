import random

from flask_socketio import emit

from socketio_instance import socketio
from services import get_player


# 完成赏金任务
@socketio.on('finishBounty')
def finish_bounty(data):
    room_id = data['roomId']
    player_name = data['playerName']

    # 清空赏金列表
    bounty_list = []
    for _ in range(3):
        bounty_list.append({
            "bountyId": "V0",
            "bountyType": "Value",
            "bountyLabel": "",
            "bountyName": "",
            "bountyCnName": "",
            "bountyDescription": "",
            "bountyStatus": "",
            "weight": 0,
            "count": 0,
            "idea": "D2RRX"
        })

    player = get_player(room_id, player_name)

    money = random.randint(3, 5)
    player.player_money += money
    player.draw_count += 1
    player.bounty_list = bounty_list

    emit('message', {'type': 'finishBounty', 'message': f'已完成悬赏，获得 {money} 货币，并获得 1 次抽卡机会', 'stage': [1, 2]})
