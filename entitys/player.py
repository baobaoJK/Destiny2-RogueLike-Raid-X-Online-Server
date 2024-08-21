from entitys.card_type import CardType


class Player:
    def __init__(self, data):
        self.room_id = ''  # 房间 Id
        self.room = None  # 房间
        self.role = data['role']  # 角色
        self.role_id = data['roleId']  # 角色 Id
        self.is_captain = False  # 是否是队长
        self.player_name = data['playerName']  # 玩家名称
        self.player_money = 0  # 玩家金钱
        self.draw_count = 0  # 抽卡次数
        self.player_status = "nothing"  # 玩家状态
        self.special_config = ""  # 特殊事件信息
        self.draw_card_type = ""  # 抽卡类型
        self.raid_chest = 0  # 获取隐藏箱数量
        self.devilspact = 0  # 恶魔契约
        self.blessing = 0  # 有福同享
        self.disaster = 0  # 有难同当
        self.zero_buy = 0  # 零元购
        self.give_up = False  # 开摆
        self.punish_count = 0  # 惩罚次数
        self.sab_list = []  # 苦尽甘来列表
        self.deck_list = {}  # 卡牌列表
        self.bounty_list = []  # 赏金列表
        self.player_event_list = []  # 个人事件列表
        self.global_event_list = []  # 全局事件列表
        self.backpack = []  # 背包

        # 设置卡牌列表
        self.reset_deck_list()

        # 设置悬赏列表
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
        self.bounty_list = bounty_list

    def __str__(self):
        return f"id：{self.role_id} | 名称：{self.player_name}"

    def to_dict(self):
        return {
            "role": self.role,
            "roleId": self.role_id,
            "isCaptain": self.is_captain,
            "playerName": self.player_name,
            "playerMoney": self.player_money,
            "drawCount": self.draw_count,
            "playerStatus": self.player_status,
            "specialConfig": self.special_config,
            "drawCardType": self.draw_card_type,
            "raidChest": self.raid_chest,
            "devilspact": self.devilspact,
            "blessing": self.blessing,
            "disaster": self.disaster,
            "zeroBuy": self.zero_buy,
            "giveUp": self.give_up,
            "punishCount": self.punish_count,
            "sabList": self.sab_list,
            "deckList": self.deck_list,
            "bountyList": self.bounty_list,
            "playerEventList": self.player_event_list,
            "globalEventList": self.global_event_list,
            "backpack": self.backpack,
            "playerAttributes": self.player_attributes
        }

    # 重置卡牌列表
    def reset_deck_list(self):
        self.deck_list['MicroGain'] = []
        self.deck_list['StrongGain'] = []
        self.deck_list['Opportunity'] = []
        self.deck_list['MicroDiscomfort'] = []
        self.deck_list['StrongDiscomfort'] = []
        self.deck_list['Unacceptable'] = []
        self.deck_list['Technology'] = []
        self.deck_list['Support'] = []

    # 玩家属性
    @property
    def player_attributes(self):
        return {
            "market": self.market,  # 未来市场
            "profiteer": self.profiteer,  # 纨绔子弟
            "shopClosed": self.shop_closed,  # 静水监狱
            "gambler": self.gambler,  # 赌徒
            "deckClosed": self.deck_closed,  # 戒赌
            "compensate": self.compensate,  # 免死金牌
            "torture": self.torture,  # 苦肉计
            "is_random": self.is_random,  # 不，你不能
            "program": self.program,  # 卡牌回收计划
            "stargazing": self.stargazing,  # 观星
            "noDeal": self.no_deal,  # 不吃这套
            "noBuddy": self.no_buddy,  # 不是哥们
            "thirteen": self.thirteen,  # 十三幺
            "counteract": self.counteract,  # 免死金牌与帝王禁令
            "difficult": self.difficult,  # 重重难关
            "easy": self.easy,  # 这不是很简单吗
            "lastCount": self.last_count  # 卡池剩余数量
        }

    # 未来市场
    @property
    def market(self):
        return any(item['cardName'] == "Future's-Market" for item in self.deck_list[CardType.technology])

    # 纨绔子弟
    @property
    def profiteer(self):
        return any(item['cardName'] == "Reicher-Playboy" for item in self.deck_list[CardType.strong_discomfort])

    # 静水监狱
    @property
    def shop_closed(self):
        return any(item['cardName'] == "Stillwater-Prison" for item in self.deck_list[CardType.unacceptable])

    # 赌徒
    @property
    def gambler(self):
        return any(item['cardName'] == "Gambler" for item in self.deck_list[CardType.technology])

    # 戒赌
    @property
    def deck_closed(self):
        return any(item['cardName'] == "Quit-Gambling" for item in self.deck_list[CardType.unacceptable])

    # 免死金牌
    @property
    def compensate(self):
        return any(item['cardName'] == 'The-Medallion' for item in self.deck_list[CardType.opportunity])

    # 苦肉计
    @property
    def torture(self):
        return any(item['cardName'] == 'The-Self-Torture-Scheme' for item in self.deck_list[CardType.technology])

    # 不，你不能
    @property
    def is_random(self):
        return any(item['cardName'] == 'You-Cant' for item in self.deck_list[CardType.technology])

    # 卡牌回收计划
    @property
    def program(self):
        return any(item['cardName'] == 'Card-Recycling-Program' for item in self.deck_list[CardType.technology])

    # 观星
    @property
    def stargazing(self):
        return any(item['cardName'] == 'Stargazing' for item in self.deck_list[CardType.technology])

    # 不吃这套
    @property
    def no_deal(self):
        return any(item['cardName'] == 'I-Wont-Eat-This' for item in self.deck_list[CardType.technology])

    # 不是哥们
    @property
    def no_buddy(self):
        return any(item['cardName'] == 'No-Buddy' for item in self.deck_list[CardType.technology])

    # 十三幺
    @property
    def thirteen(self):
        return any(item['cardName'] == 'Thirteen-Orphans' for item in self.deck_list[CardType.technology])

    # 免死金牌和帝王禁令
    @property
    def counteract(self):
        return (any(item['cardName'] == 'The-Medallion' for item in self.deck_list[CardType.opportunity])
                and
                any(item['cardName'] == 'Imperial-Ban' for item in self.deck_list[CardType.unacceptable]))

    # 重重难关
    @property
    def difficult(self):
        return any(item['cardName'] == 'Many-Difficulties' for item in self.deck_list[CardType.unacceptable])

    # 这不是很简单吗
    @property
    def easy(self):
        return any(item['cardName'] == 'Easy' for item in self.deck_list[CardType.opportunity])

    # 卡池剩余数量
    @property
    def last_count(self):
        last_count_list = {}

        if self.room is None:
            return last_count_list

        def check_deck_list(player, item):
            for card_type, card_list in player.deck_list.items():
                for card in card_list:
                    if item['cardName'] == card['cardName']:
                        return True

        last_count_list[CardType.micro_gain] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.micro_gain])
        last_count_list[CardType.strong_gain] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.strong_gain])
        last_count_list[CardType.opportunity] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.opportunity])
        last_count_list[CardType.micro_discomfort] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.micro_discomfort])
        last_count_list[CardType.strong_discomfort] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.strong_discomfort])
        last_count_list[CardType.unacceptable] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.unacceptable])
        last_count_list[CardType.technology] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.technology])
        last_count_list[CardType.support] = len(
            [item for item in self.room.game_config['cardList'] if
             not (check_deck_list(self, item)) and item['cardType'] == CardType.support])

        return last_count_list
