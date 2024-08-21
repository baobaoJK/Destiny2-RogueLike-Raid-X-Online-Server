from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Dungeon(Base):
    __tablename__ = 'dungeon_list'

    dungeon_id = Column(String, primary_key=True)
    dungeon_type = Column(String)
    dungeon_name = Column(String)
    dungeon_check = Column(Integer)
    dungeon_level = Column(Integer)
    dungeon_level_point = 0
    dungeon_chest = Column(Integer)
    dungeon_img = Column(String)
    weight = Column(Integer)
    count = Column(Integer)

    def to_dict(self):
        return {
            'dungeonId': self.dungeon_id,
            'dungeonType': self.dungeon_type,
            'dungeonName': self.dungeon_name,
            'dungeonCheck': self.dungeon_check,
            'dungeonLevel': self.dungeon_level,
            'dungeonLevelPoint': self.dungeon_level_point,
            'dungeonChest': self.dungeon_chest,
            'dungeonImg': self.dungeon_img,
            'weight': self.weight,
            'count': self.count
        }
