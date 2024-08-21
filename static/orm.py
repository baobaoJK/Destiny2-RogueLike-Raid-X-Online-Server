from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()


class RaidMap(Base):
    __tablename__ = 'raid_list'

    raid_id = Column(Integer, primary_key=True)
    raid_name = Column(String)
    raid_check = Column(Integer)
    raid_level = Column(Integer)
    riad_level_point = 0
    raid_chest = Column(Integer)
    raid_img = Column(String)
    weight = Column(Integer)
    count = Column(Integer)

    def to_dict(self):
        """Convert the object to a dictionary with camelCase keys."""
        return {
            'raidId': self.raid_id,
            'raidName': self.raid_name,
            'raidCheck': self.raid_check,
            'raidLevel': self.raid_level,
            'raidLevelPoint': self.riad_level_point,
            'raidChest': self.raid_chest,
            'raidImg': self.raid_img,
            'weight': self.weight,
            'count': self.count
        }


if __name__ == "__main__":
    room_id = "s6wS"
    # 数据库引擎和会话创建
    engine = create_engine(f'sqlite:///../database/temp/raid_{room_id}.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # 查询数据
    raid_maps = session.query(RaidMap).all()

    # 转换为字典列表
    raid_maps_dict = [raid_map.to_dict() for raid_map in raid_maps]

    # 转换为 JSON
    json_result = json.dumps(raid_maps_dict, ensure_ascii=False, indent=4)

    # 输出 JSON
    print(json_result)
