import random

class LootManager:
    def __init__(self, config: dict):
        """
        初始化掉落管理器。

        Args:
            config (dict): 配置字典，包含掉落相关参数，例如：
                - "drop_rates": 掉落概率字典，键为物品类型，值为概率（0-1）
                  例如 {"weapon": 0.2, "rune": 0.15, "gold": 0.4, "potion": 0.15, "treasure": 0.1}
                - "gold_range": 金币生成数量范围，例如 [5, 20]
                - "potion_range": 药水回复值范围，例如 [20, 50]
        """
        self.config = config
        self.drop_rates = config.get("drop_rates", {
            "weapon": 0.2,
            "rune": 0.15,
            "gold": 0.4,
            "potion": 0.15,
            "treasure": 0.1
        })
        self.gold_range = config.get("gold_range", [5, 20])
        self.potion_range = config.get("potion_range", [20, 50])

    def generate_loot(self, monster_level: int) -> list:
        """
        根据怪物等级生成掉落物列表。掉落次数可能与怪物等级有关，
        每次掉落根据配置概率选择掉落物类型，然后生成具体物品数据。

        Args:
            monster_level (int): 怪物等级，用于决定掉落物的数量和质量。

        Returns:
            list: 掉落物列表，每个掉落物为一个数据字典。
        """
        loot = []
        # 定义掉落次数，示例：怪物等级加上随机1-3次
        num_drops = monster_level + random.randint(1, 3)
        for _ in range(num_drops):
            roll = random.random()
            cumulative = 0.0
            item_type = None
            for t, rate in self.drop_rates.items():
                cumulative += rate
                if roll < cumulative:
                    item_type = t
                    break
            if item_type is None:
                item_type = "misc"
            loot_item = self.generate_loot_item(item_type, monster_level)
            if loot_item:
                loot.append(loot_item)
        return loot

    def generate_loot_item(self, item_type: str, monster_level: int) -> dict:
        """
        根据物品类型和怪物等级生成单个掉落物数据字典。
        掉落物品类型包括：
          - "gold": 金币，根据怪物等级调整数量。
          - "potion": 药水，回复值在配置范围内随机生成。
          - "weapon": 掉落武器，基础伤害与怪物等级相关。
          - "rune": 掉落符文， bonus 数值可能与怪物等级挂钩。
          - "treasure": 宝箱，表示其他珍稀掉落物。
          - "misc": 其他杂项物品。

        Args:
            item_type (str): 掉落物品类型。
            monster_level (int): 怪物等级，用于决定数值规模。

        Returns:
            dict: 掉落物数据字典，包含 "type", "name", "effect", "value" 等字段。
        """
        if item_type == "gold":
            amount = random.randint(self.gold_range[0], self.gold_range[1]) * monster_level
            return {"type": "gold", "name": f"{amount} 金币", "effect": "money", "value": amount}
        elif item_type == "potion":
            heal_value = random.randint(self.potion_range[0], self.potion_range[1])
            return {"type": "potion", "name": f"药水 (+{heal_value} HP)", "effect": "heal", "value": heal_value}
        elif item_type == "weapon":
            # 掉落武器的基础伤害在 3-10 之间，加上怪物等级的影响
            damage = random.randint(3, 10) + monster_level
            return {"type": "weapon", "name": "掉落武器", "damage": damage, "description": f"伤害 {damage}"}
        elif item_type == "rune":
            # 掉落符文， bonus 在 1-5 之间，加上怪物等级的部分影响
            bonus = random.randint(1, 5) + monster_level // 2
            return {"type": "rune", "name": "掉落符文", "effect": "rune", "value": bonus}
        elif item_type == "treasure":
            bonus = random.randint(1, 10) + monster_level
            return {"type": "treasure", "name": "宝箱", "effect": "loot", "value": bonus}
        else:
            bonus = random.randint(1, 3)
            return {"type": "misc", "name": "神秘物品", "effect": None, "value": bonus}

    def describe_loot(self, loot_list: list) -> str:
        """
        返回掉落物品列表的描述字符串，便于展示给玩家。

        Args:
            loot_list (list): 掉落物列表，每个物品为一个数据字典。

        Returns:
            str: 掉落物描述文本，每个物品一行。
        """
        descriptions = []
        for item in loot_list:
            desc = f"{item['name']}"
            if item.get("effect"):
                desc += f" (效果: {item['effect']}, 数值: {item['value']})"
            descriptions.append(desc)
        return "\n".join(descriptions)

if __name__ == "__main__":
    config = {
        "drop_rates": {"weapon": 0.2, "rune": 0.15, "gold": 0.4, "potion": 0.15, "treasure": 0.1},
        "gold_range": [5, 20],
        "potion_range": [20, 50]
    }
    lm = LootManager(config)
    # 模拟生成怪物等级为3时的掉落物
    loot_items = lm.generate_loot(3)
    print("生成的掉落物：")
    print(lm.describe_loot(loot_items))
