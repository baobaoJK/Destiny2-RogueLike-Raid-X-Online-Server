from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RaidMap(Base):
    __tablename__ = 'raid_list'

    raid_id = Column(String, primary_key=True)
    raid_name = Column(String)
    raid_check = Column(Integer)
    raid_level = Column(Integer)
    riad_level_point = 0
    raid_chest = Column(Integer)
    raid_img = Column(String)
    weight = Column(Integer)
    count = Column(Integer)

    def to_dict(self):
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

# class RaidMap:
#
#     def __init__(self, sql=None):
#         if sql is None:
#             return
#         self.raid_id = sql['raid_id']  # 突袭 Id
#         self.raid_type = sql['raid_type']  # 突袭类型
#         self.raid_name = sql['raid_name']  # 突袭名称
#         self.raid_check = sql['raid_check']  # 突袭检查点数量
#         self.raid_level = sql['raid_level']  # 突袭关卡数量
#         self.raid_level_point = 0  # 突袭当前关卡
#         self.raid_check_point = 0  # 突袭当前检查点
#         self.raid_chest = sql['raid_chest']  # 突袭隐藏箱数量
#         self.raid_chest_point = 0  # 已获取隐藏箱数量
#         self.raid_img = sql['raid_img']  # 突袭图片
#         self.weight = sql['weight']  # 权重
#         self.count = sql['count']  # 数量
#
#     def to_dict(self):
#         return {
#             'raidId': self.raid_id,
#             'raidType': self.raid_type,
#             'raidName': self.raid_name,
#             'raidCheck': self.raid_check,
#             'raidLevel': self.raid_level,
#             'raidLevelPoint': self.raid_level_point,
#             'raidCheckPoint': self.raid_check_point,
#             'raidChest': self.raid_chest,
#             'raidChestPoint': self.raid_chest_point,
#             'raidImg': self.raid_img,
#             'weight': self.weight,
#             'count': self.count,
#         }
#
#     def from_dict(self, data):
#         self.raid_id = data.get('raidId')
#         self.raid_type = data.get('raidType')
#         self.raid_name = data.get('raidName')
#         self.raid_check = data.get('raidCheck')
#         self.raid_level = data.get('raidLevel')
#         self.raid_level_point = data.get('raidLevelPoint')
#         self.raid_check_point = data.get('raidCheckPoint')
#         self.raid_chest = data.get('raidChest')
#         self.raid_chest_point = data.get('raidChestPoint')
#         self.raid_img = data.get('raidImg')
#         self.weight = data.get('weight')
#         self.count = data.get('count')
