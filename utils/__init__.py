import random
import string

# 生成 4 位由字母大小写和数字随机组合
def random_room_name():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=4))


# 打乱列表顺序
def shuffle_list(data_list):
    random.shuffle(data_list)
    return data_list


# 根据类型获取卡牌列表
def get_card_list_by_type(data_list):
    card_list = {
        'MicroGain': [card for card in data_list if card['cardType'] == 'MicroGain'],
        'StrongGain': [card for card in data_list if card['cardType'] == 'StrongGain'],
        'Opportunity': [card for card in data_list if card['cardType'] == 'Opportunity'],
        'MicroDiscomfort': [card for card in data_list if card['cardType'] == 'MicroDiscomfort'],
        'StrongDiscomfort': [card for card in data_list if card['cardType'] == 'StrongDiscomfort'],
        'Unacceptable': [card for card in data_list if card['cardType'] == 'Unacceptable'],
        'Technology': [card for card in data_list if card['cardType'] == 'Technology'],
        'Support': [card for card in data_list if card['cardType'] == 'Support']}

    return card_list

from .sql_connect import *
