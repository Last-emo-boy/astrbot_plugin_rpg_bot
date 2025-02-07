import random

class RuneManager:
    def __init__(self, config: dict):
        """
        初始化符文管理器。

        Args:
            config (dict): 配置字典，包含符文相关参数，例如：
                - "rune_types": 可生成的符文类型列表，例如 ["fire", "ice", "poison", "generic"]
                - "rune_adjectives": 符文形容词列表，例如 ["炽热的", "寒冰的", "剧毒的", "神秘的"]
                - "bonus_range": 数值范围，例如 [1, 5]，表示符文增加的数值范围
                - "rune_upgrade_factor": 符文升级时增加的倍率，例如 1.2
                - "max_rune_upgrade_level": 符文最大升级次数，例如 5
        """
        self.config = config
        self.rune_types = config.get("rune_types", ["fire", "ice", "poison", "generic"])
        self.rune_adjectives = config.get("rune_adjectives", ["炽热的", "寒冰的", "剧毒的", "神秘的"])
        self.bonus_range = config.get("bonus_range", [1, 5])
        self.rune_upgrade_factor = config.get("rune_upgrade_factor", 1.2)
        self.max_rune_upgrade_level = config.get("max_rune_upgrade_level", 5)

    def generate_rune(self, rune_type: str = None) -> dict:
        """
        随机生成一个符文数据字典。

        Args:
            rune_type (str, optional): 指定符文类型，例如 "fire", "ice", "poison", "generic"；若未指定则随机选择。

        Returns:
            dict: 包含以下字段：
                - "type": 符文类型
                - "name": 符文名称，由形容词和符文类型拼接而成
                - "bonus": 增加的数值（例如额外伤害加成）
                - "description": 描述符文效果，如 "增加 X 点 fire 属性"
                - "level": 符文当前级别（初始 1）
                - "upgrade_level": 已升级次数（初始 0）
        """
        if not rune_type:
            rune_type = random.choice(self.rune_types)
        adjective = random.choice(self.rune_adjectives)
        bonus = random.randint(self.bonus_range[0], self.bonus_range[1])
        name = f"{adjective}{rune_type.capitalize()}符文"
        description = f"增加 {bonus} 点 {rune_type} 属性"
        rune = {
            "type": rune_type,
            "name": name,
            "bonus": bonus,
            "description": description,
            "level": 1,
            "upgrade_level": 0
        }
        return rune

    def upgrade_rune(self, rune: dict, upgrade_points: int) -> dict:
        """
        升级指定的符文。使用一定的升级点数对符文进行升级，符文的 bonus 按照 upgrade_factor 提升，
        并更新 upgrade_level。若已达到最大升级次数，则不再升级。

        Args:
            rune (dict): 要升级的符文数据字典。
            upgrade_points (int): 可用于升级的点数。

        Returns:
            dict: 升级后的符文数据字典。
        """
        current_upgrade = rune.get("upgrade_level", 0)
        available_upgrades = self.max_rune_upgrade_level - current_upgrade
        if available_upgrades <= 0:
            return rune

        upgrade_times = min(upgrade_points, available_upgrades)
        # 升级公式：bonus 乘以 (rune_upgrade_factor ** upgrade_times)
        new_bonus = int(rune["bonus"] * (self.rune_upgrade_factor ** upgrade_times))
        rune["bonus"] = new_bonus
        rune["upgrade_level"] = current_upgrade + upgrade_times
        # 更新描述文本
        rune["description"] = f"增加 {new_bonus} 点 {rune['type']} 属性"
        return rune

    def describe_rune(self, rune: dict) -> str:
        """
        返回符文的详细描述字符串，便于展示给玩家。

        Args:
            rune (dict): 符文数据字典。

        Returns:
            str: 符文描述信息。
        """
        return (f"{rune['name']} (等级: {rune['level']}, 升级次数: {rune['upgrade_level']}, "
                f"效果: {rune['description']})")

if __name__ == "__main__":
    # 简单测试示例
    config = {
        "rune_types": ["fire", "ice", "poison", "generic"],
        "rune_adjectives": ["炽热的", "寒冰的", "剧毒的", "神秘的"],
        "bonus_range": [1, 5],
        "rune_upgrade_factor": 1.2,
        "max_rune_upgrade_level": 5
    }
    rm = RuneManager(config)
    # 生成一个随机符文
    rune = rm.generate_rune()
    print("生成的符文：")
    print(rm.describe_rune(rune))
    # 模拟升级符文
    upgraded_rune = rm.upgrade_rune(rune, upgrade_points=3)
    print("升级后的符文：")
    print(rm.describe_rune(upgraded_rune))
