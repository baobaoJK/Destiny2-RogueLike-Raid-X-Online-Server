from entitys.sql.card import Card
from entitys.sql.bounty import Bounty
from entitys.sql.dungeon import Dungeon
from entitys.sql.global_event import GlobalEvent
from entitys.sql.player_event import PlayerEvent
from entitys.sql.raid_map import RaidMap
from entitys.sql.shop import ShopItem, ExoticWeapon, ExoticArmor
from utils import get_session


class Room:
    MAX_USERS_PER_ROOM = 6  # 设置房间的最大人数

    def __init__(self, room_id, room_owner):
        self.room_id = room_id
        self.room_owner = room_owner
        self.room_stage = "next"
        self.room_status = "waiting"
        self.card_status = ""
        self.seats = []
        self.players = {}
        self.global_event_list = []
        self.raid_config = None
        self.game_config = {}
        self.shop_config = {}

        for _ in range(Room.MAX_USERS_PER_ROOM):
            self.seats.append(None)

        self.set_game_config()
        self.set_shop_config()

    def to_dict(self):
        return {
            'roomId': self.room_id,
            'roomOwner': self.room_owner,
            'roomStage': self.room_stage,
            # 'players': [player['playerName'] for player in self.players],
            'seats': self.seats,
            'roomStatus': self.room_status,
            'cardStatus': self.card_status,
            'players': [player for player in self.players],
            'globalEventList': self.global_event_list,
            'raidConfig': self.raid_config,
            'shopConfig': self.shop_config,
        }

    # 设置房间配置
    def set_game_config(self):
        # 数据库引擎和会话创建
        session = get_session()

        # 设置 raid_list
        sql_raid_list = session.query(RaidMap).all()
        raid_list_dict = [raid_map.to_dict() for raid_map in sql_raid_list]
        self.game_config['raidList'] = raid_list_dict

        # print(self.game_config['raidList'])

        # 设置 dungeon_list
        sql_dungeon_list = session.query(Dungeon).all()
        dungeon_list_dict = [dungeon.to_dict() for dungeon in sql_dungeon_list]
        self.game_config['dungeonList'] = dungeon_list_dict

        # 设置 card_list
        sql_card_list = session.query(Card).all()
        card_list_dict = [card.to_dict() for card in sql_card_list]
        self.game_config['cardList'] = card_list_dict
        # print(self.game_config['cardList'])

        # 设置 bounty_list
        sql_bounty_list = session.query(Bounty).all()
        bounty_list_dict = [bounty.to_dict() for bounty in sql_bounty_list]
        self.game_config['bountyList'] = bounty_list_dict

        # 设置 player_event_list
        sql_player_event_list = session.query(PlayerEvent).all()
        player_event_list_dict = [player_event.to_dict() for player_event in sql_player_event_list]
        self.game_config['playerEventList'] = player_event_list_dict

        # 设置 global_event_list
        sql_global_event_list = session.query(GlobalEvent).all()
        global_event_list_dict = [global_event.to_dict() for global_event in sql_global_event_list]
        self.game_config['globalEventList'] = global_event_list_dict

    # 获取房间配置
    def get_game_config(self):
        return self.game_config

    # 设置商店配置
    def set_shop_config(self):
        # 数据库引擎和会话创建
        session = get_session()

        # 设置 shop_item_list
        sql_shop_item_list = session.query(ShopItem).all()
        shop_item_list_dict = [shop_item.to_dict() for shop_item in sql_shop_item_list]
        self.shop_config['shopItem'] = shop_item_list_dict
        # print(shop_item_list_dict)

        # 设置 exotic_weapon_list
        sql_exotic_weapon_list = session.query(ExoticWeapon).all()
        exotic_weapon_list_dict = [exotic_weapon.to_dict() for exotic_weapon in sql_exotic_weapon_list]
        self.shop_config['exoticWeaponList'] = exotic_weapon_list_dict

        # 设置 exotic_armor_list
        sql_exotic_armor_list = session.query(ExoticArmor).all()
        exotic_armor_list_dict = [exotic_armor.to_dict() for exotic_armor in sql_exotic_armor_list]
        self.shop_config['exoticArmorList'] = exotic_armor_list_dict

        # 设置 item_list
        self.shop_config['itemList'] = []

        # 设置 weapon_list
        self.shop_config['weaponList'] = []

        # 设置 exotix_list
        self.shop_config['exoticList'] = []

        # 设置刷新费用
        self.shop_config['refreshMoney'] = 6

        # 设置免费刷新次数
        self.shop_config['refreshCount'] = 0


    # 获取玩家数量
    def get_players(self):
        return len(self.players)


    # 设置突袭信息
    def set_raid_config(self, data):
        self.raid_config = data


    # 获取突袭信息
    def get_raid_config(self):
        return self.raid_config

