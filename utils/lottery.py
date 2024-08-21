# 抽奖函数(不根据数量)
import random


def lottery(data_list):
    # 分离出权重列表用于选择
    weights = [i['weight'] for i in data_list]

    # 根据权重随机选择一个项目
    return random.choices(data_list, weights=weights, k=1)[0]


# 抽奖函数 (根据数量)
def lottery_by_count(data_list):
    # 判断数量是否大于 0
    all_count = sum(item['count'] for item in data_list)
    if all_count == 0:
        print("已经没有东西可以抽了")
        return None
    else:
        while True:
            # 分离出权重列表用于选择
            weights = [i['weight'] for i in data_list]

            # 根据权重随机选择一个项目
            item = random.choices(data_list, weights=weights, k=1)[0]

            # 如果选中的项目数量大于0，则返回其'id'
            # 如果数量为0，继续循环直到选中有效的项目
            if item['count'] > 0:
                # item['count'] -= 1  # 减少该项目的数量
                return item
