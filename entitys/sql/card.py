from sqlalchemy import Column, Integer, String, Double
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Card(Base):
    __tablename__ = 'card_list'

    card_id = Column(String, primary_key=True)
    card_type = Column(String)
    card_label = Column(String)
    card_level = Column(Integer)
    card_name = Column(String)
    card_cn_name = Column(String)
    card_description = Column(String)
    card_special = Column(String)
    weight = Column(Double)
    count = Column(Integer)
    all_count = Column(Integer)
    idea = Column(String)

    def to_dict(self):
        return {
            'cardId': self.card_id,
            'cardType': self.card_type,
            'cardLabel': self.card_label,
            'cardLevel': self.card_level,
            'cardName': self.card_name,
            'cardCnName': self.card_cn_name,
            'cardDescription': self.card_description,
            'cardSpecial': self.card_special,
            'weight': self.weight,
            'count': self.count,
            'allCount': self.all_count,
            'idea': self.idea,
        }
