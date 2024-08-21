# 卡组列表
class CardType:
    micro_gain = 'MicroGain'
    strong_gain = 'StrongGain'
    opportunity = 'Opportunity'
    micro_discomfort = 'MicroDiscomfort'
    strong_discomfort = 'StrongDiscomfort'
    unacceptable = 'Unacceptable'
    technology = 'Technology'
    support = 'Support'

    @classmethod
    def get_type_by_num(cls, type_num):
        if type_num == 1:
            return cls.micro_gain
        if type_num == 2:
            return cls.strong_gain
        if type_num == 3:
            return cls.opportunity
        if type_num == 4:
            return cls.micro_discomfort
        if type_num == 5:
            return cls.strong_discomfort
        if type_num == 6:
            return cls.unacceptable
        if type_num == 7:
            return cls.technology
        if type_num == 8:
            return cls.support
