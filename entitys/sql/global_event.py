from sqlalchemy import Column, Integer, String, Double
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GlobalEvent(Base):
    __tablename__ = 'global_event_list'

    event_id = Column(String, primary_key=True)
    event_type = Column(String)
    event_name = Column(String)
    event_cn_name = Column(String)
    event_description = Column(String)
    event_status = Column(String)
    weight = Column(Double)
    count = Column(Integer)
    idea = Column(String)

    def to_dict(self):
        return {
            'eventId': self.event_id,
            'eventType': self.event_type,
            'eventName': self.event_name,
            'eventCnName': self.event_cn_name,
            'eventDescription': self.event_description,
            'eventStatus': self.event_status,
            'weight': self.weight,
            'count': self.count,
            'idea': self.idea,
        }
