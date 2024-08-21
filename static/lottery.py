import random


def weighted_lottery(data):
    """
    根据权重进行抽奖，并考虑数量。

    :param data: 包含字典的列表，每个字典包含'id', 'weight', 'count'键
    :return: 抽取的项目的'id'
    """
    while True:
        # 分离出权重列表用于选择
        weights = [item['weight'] for item in data]

        # 根据权重随机选择一个项目
        selected_item = random.choices(data, weights=weights, k=1)[0]

        # 如果选中的项目数量大于0，则返回其'id'
        if selected_item['count'] > 0:
            selected_item['count'] -= 1  # 减少该项目的数量
            return selected_item['id']
        # 如果数量为0，继续循环直到选中有效的项目


# 示例用法
if __name__ == "__main__":
    data = [
        {'id': 1, 'weight': 0.5, 'count': 1},
        {'id': 2, 'weight': 0.3, 'count': 1},
        {'id': 3, 'weight': 0.2, 'count': 3}
    ]

    for _ in range(5):
        print("抽奖结果:", weighted_lottery(data))