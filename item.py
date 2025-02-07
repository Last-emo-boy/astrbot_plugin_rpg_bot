import random

class ItemManager:
    def __init__(self, config: dict):
        """
        初始化物品管理器。

        Args:
            config (dict): 配置字典，包含生成物品相关参数，例如：
                - "potion_range": [min, max]，药水回复值范围
                - "gold_range": [min, max]，金币生成数量范围
                - "skill_list": 可生成卷轴的技能列表
                - "item_types": 可生成的物品类型列表，例如 ["potion", "scroll", "treasure", "gold", "misc"]
        """
        self.config = config
        self.potion_range = config.get("potion_range", [10, 50])
        self.gold_range = config.get("gold_range", [5, 20])
        self.skill_list = config.get("skill_list", ["斩击", "火球术", "穿刺"])
        self.item_types = config.get("item_types", ["potion", "scroll", "treasure", "gold", "misc"])

    def generate_item(self, item_type: str = None) -> dict:
        """
        随机生成一个物品数据字典。

        Args:
            item_type (str, optional): 指定生成的物品类型；可选类型包括：
                - "potion": 药水，效果为恢复 HP
                - "scroll": 卷轴，效果为学习技能
                - "treasure": 宝箱，效果为掉落奖励
                - "gold": 金币，效果为增加金钱
                - "misc": 其他杂项
              若未指定，则随机选择。

        Returns:
            dict: 物品数据字典，包含以下字段：
                - "type": 物品类型
                - "name": 物品名称
                - "effect": 物品效果（例如 "heal", "skill", "loot", "money"）
                - "value": 数值，视具体效果而定（例如恢复的HP、金币数量、奖励数值）
        """
        if not item_type:
            item_type = random.choice(self.item_types)
        if item_type == "potion":
            heal_value = random.randint(self.potion_range[0], self.potion_range[1])
            return {"type": "potion", "name": f"药水 (+{heal_value} HP)", "effect": "heal", "value": heal_value}
        elif item_type == "scroll":
            skill = random.choice(self.skill_list)
            return {"type": "scroll", "name": f"卷轴 ({skill})", "effect": "skill", "value": skill}
        elif item_type == "treasure":
            bonus = random.randint(1, 10)
            return {"type": "treasure", "name": f"宝箱 (价值 {bonus})", "effect": "loot", "value": bonus}
        elif item_type == "gold":
            amount = random.randint(self.gold_range[0], self.gold_range[1])
            return {"type": "gold", "name": f"{amount} 金币", "effect": "money", "value": amount}
        else:
            bonus = random.randint(1, 5)
            return {"type": "misc", "name": f"神秘物品 (+{bonus})", "effect": None, "value": bonus}

    def use_item(self, character: dict, item: dict) -> str:
        """
        使用一个物品，根据物品效果对角色数据进行相应处理。

        Args:
            character (dict): 角色数据字典。
            item (dict): 物品数据字典。

        Returns:
            str: 使用结果描述信息。
        """
        if item["effect"] == "heal":
            old_hp = character["hp"]
            character["hp"] = min(character["hp"] + item["value"], character["max_hp"])
            return f"你使用了 {item['name']}，HP 从 {old_hp} 恢复到 {character['hp']}。"
        elif item["effect"] == "money":
            character["money"] += item["value"]
            return f"你获得了 {item['value']} 金币。"
        elif item["effect"] == "skill":
            # 卷轴学习技能由技能模块进一步处理，这里只返回提示信息
            return f"你使用了 {item['name']}，可通过 /rpg learn_skill 命令学习技能 {item['value']}。"
        elif item["effect"] == "loot":
            return f"你打开了 {item['name']}，发现了一些宝物！"
        else:
            return f"你使用了 {item['name']}，但似乎没有产生任何效果。"

    def describe_item(self, item: dict) -> str:
        """
        返回物品的详细描述字符串。

        Args:
            item (dict): 物品数据字典。

        Returns:
            str: 描述字符串。
        """
        desc = f"{item['name']}"
        if item.get("effect"):
            desc += f" (效果: {item['effect']}, 数值: {item['value']})"
        return desc

if __name__ == "__main__":
    # 测试示例
    config = {
        "potion_range": [20, 50],
        "gold_range": [10, 30],
        "skill_list": ["斩击", "火球术", "穿刺"],
        "item_types": ["potion", "scroll", "treasure", "gold", "misc"]
    }
    im = ItemManager(config)
    for t in ["potion", "scroll", "treasure", "gold", "misc"]:
        item = im.generate_item(t)
        print("生成物品：", im.describe_item(item))
        # 构造简单角色数据用于测试 use_item
        character = {"hp": 50, "max_hp": 100, "money": 0}
        result = im.use_item(character, item)
        print("使用结果：", result)
