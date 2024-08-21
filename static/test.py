# import sqlite3
#
# # 连接到 SQLite 数据库（如果数据库不存在，会自动创建）
# conn = sqlite3.connect('../database/raid.db')
# c = conn.cursor()
#
# # 插入 50 条数据
# for i in range(1, 133):
#     c.execute("INSERT INTO exotic_armor_list (exotic_armor_id) VALUES (?)", (i,))
#
# # 提交事务并关闭连接
# conn.commit()
# conn.close()
#
# print("50 rows have been inserted into the card_list table.")

from entitys.sql.raid_map import RaidMap
from utils.lottery import lottery

if __name__ == '__main__':
    sql_map_list = [
        {
            "raid_id": "RM1",
            "raid_type": "RaidMap",
            "raid_name": "最后一愿",
            "raid_check": 6,
            "raid_level": 6,
            "raid_chest": 2,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM2",
            "raid_type": "RaidMap",
            "raid_name": "救赎花园",
            "raid_check": 4,
            "raid_level": 4,
            "raid_chest": 2,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM3",
            "raid_type": "RaidMap",
            "raid_name": "深岩墓室",
            "raid_check": 4,
            "raid_level": 4,
            "raid_chest": 2,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM4",
            "raid_type": "RaidMap",
            "raid_name": "玻璃拱顶",
            "raid_check": 5,
            "raid_level": 5,
            "raid_chest": 4,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM5",
            "raid_type": "RaidMap",
            "raid_name": "门徒誓约",
            "raid_check": 4,
            "raid_level": 4,
            "raid_chest": 2,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM6",
            "raid_type": "RaidMap",
            "raid_name": "国王的陨落",
            "raid_check": 5,
            "raid_level": 5,
            "raid_chest": 4,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM7",
            "raid_type": "RaidMap",
            "raid_name": "梦魇根源",
            "raid_check": 4,
            "raid_level": 4,
            "raid_chest": 2,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        },
        {
            "raid_id": "RM8",
            "raid_type": "RaidMap",
            "raid_name": "克洛塔的末日",
            "raid_check": 4,
            "raid_level": 4,
            "raid_chest": 2,
            "raid_img": None,
            "weight": 0.125,
            "count": 1
        }
    ]

    lottery_count = 50
    map_list_data = []

    for i in range(lottery_count):
        if i == lottery_count - 7:
            map_obj = lottery(sql_map_list)
            map_list_data.append(map_obj.to_dict())
            sql_map_list.game_config.raid_config = RaidMap(map_obj.to_dict())
        else:
            map_obj = lottery(sql_map_list)
            map_list_data.append(map_obj.to_dict())

    print(map_list_data)

    # # map_list = [map_obj for map_obj in sql_map_list]
    # map_list = [RaidMap(map_obj) for map_obj in sql_map_list]
    #
    # print(dict(map_list[0].to_dict()))
    # db_path = os.path.join(os.path.dirname(__file__), f'../database/raid.db')
    #
    # conn = sqlite3.connect(db_path)
    # # 设置 row_factory 属性
    # conn.row_factory = sqlite3.Row
    #
    # cursor = conn.cursor()
    # sql_str = "SELECT * FROM raid_list"
    # cursor.execute(sql_str)
    # result = cursor.fetchall()
    # maps = [dict(m) for m in result]
    #
    # print(get_map_obj(conn, 'RM1'))
