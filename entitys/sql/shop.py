from sqlalchemy import Column, Integer, String, Double
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ShopItem(Base):
    __tablename__ = 'shop_list'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String)
    cn_name = Column(String)
    kind = Column(Integer)
    rarity = Column(String)
    type_name = Column(String)
    description = Column(String)
    sell = Column(Integer)
    count = Column(Integer)
    all_count = Column(Integer)
    weight = Column(Double)

    def to_dict(self):
        return {
            'itemId': self.item_id,
            'itemName': self.item_name,
            'cnName': self.cn_name,
            'kind': self.kind,
            'rarity': self.rarity,
            'typeName': self.type_name,
            'description': self.description,
            'sell': self.sell,
            'count': self.count,
            'allCount': self.all_count,
            'weight': self.weight
        }


class ExoticArmor(Base):
    __tablename__ = 'exotic_armor_list'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String)
    cn_name = Column(String)
    kind = Column(Integer)
    rarity = Column(String)
    type_name = Column(String)
    description = Column(String)
    sell = Column(Integer)
    role = Column(String)
    count = Column(Integer)
    weight = Column(Double)

    def to_dict(self):
        return {
            'itemId': self.item_id,
            'itemName': self.item_name,
            'cnName': self.cn_name,
            'kind': self.kind,
            'rarity': self.rarity,
            'typeName': self.type_name,
            'description': self.description,
            'sell': self.sell,
            'role': self.role,
            'count': self.count,
            'weight': self.weight
        }


class ExoticWeapon(Base):
    __tablename__ = 'exotic_weapon_list'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String)
    cn_name = Column(String)
    kind = Column(Integer)
    rarity = Column(String)
    type_name = Column(String)
    description = Column(String)
    sell = Column(Integer)
    count = Column(Integer)
    weight = Column(Double)

    def to_dict(self):
        return {
            'itemId': self.item_id,
            'itemName': self.item_name,
            'cnName': self.cn_name,
            'kind': self.kind,
            'rarity': self.rarity,
            'typeName': self.type_name,
            'description': self.description,
            'sell': self.sell,
            'count': self.count,
            'weight': self.weight
        }
