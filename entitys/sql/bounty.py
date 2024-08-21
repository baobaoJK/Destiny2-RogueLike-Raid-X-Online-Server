from sqlalchemy import Column, Integer, String, Double
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Bounty(Base):
    __tablename__ = 'bounty_list'

    bounty_id = Column(String, primary_key=True)
    bounty_type = Column(String)
    bounty_label = Column(String)
    bounty_name = Column(String)
    bounty_cn_name = Column(String)
    bounty_description = Column(String)
    bounty_status = Column(String)
    weight = Column(Double)
    count = Column(Integer)
    idea = Column(String)

    def to_dict(self):
        return {
            'bountyId': self.bounty_id,
            'bountyType': self.bounty_type,
            'bountyLabel': self.bounty_label,
            'bountyName': self.bounty_name,
            'bountyCnName': self.bounty_cn_name,
            'bountyDescription': self.bounty_description,
            'bountyStatus': self.bounty_status,
            'weight': self.weight,
            'count': self.count,
            'idea': self.idea
        }
