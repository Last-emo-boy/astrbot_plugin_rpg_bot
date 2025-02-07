import random

class WeaponManager:
    def __init__(self, config: dict):
        """
        初始化武器管理器。

        Args:
            config (dict): 配置字典，包含默认武器生成参数、升级参数等。
                      例如：
                        - "weapon_types": ["剑", "斧", "锤", "弓", "匕首"]
                        - "weapon_adjectives": ["锋利的", "重型的", "轻盈的", "破旧的", "神秘的"]
                        - "damage_range": [2, 8]
                        - "upgrade_factor": 1.1  (每次升级伤害提升系数)
                        - "max_upgrade_level": 10
        """
        self.config = config
        self.weapon_types = config.get("weapon_types", ["剑", "斧", "锤", "弓", "匕首"])
        self.weapon_adjectives = config.get("weapon_adjectives", ["锋利的", "重型的", "轻盈的", "破旧的", "神秘的"])
        self.damage_range = config.get("damage_range", [2, 8])
        self.upgrade_factor = config.get("upgrade_factor", 1.1)
        self.max_upgrade_level = config.get("max_upgrade_level", 10)

    def generate_weapon(self) -> dict:
        """
        随机生成一把武器。

        返回一个武器数据字典，包含以下字段：
            - name: 武器名称，由随机形容词与武器类型拼接而成
            - damage: 武器基础伤害，在配置的 damage_range 内随机生成
            - description: 描述字符串，例如 "伤害 X"
            - level: 武器初始等级，默认为 1
            - exp: 武器经验，初始为 0
            - upgrade_level: 当前升级次数，初始为 0
            - extra_effects: 可扩展字段，用于存储符文或其他附加效果（初始为空列表）
        """
        weapon_type = random.choice(self.weapon_types)
        adjective = random.choice(self.weapon_adjectives)
        damage = random.randint(self.damage_range[0], self.damage_range[1])
        weapon = {
            "name": f"{adjective}{weapon_type}",
            "damage": damage,
            "description": f"伤害 {damage}",
            "level": 1,
            "exp": 0,
            "upgrade_level": 0,
            "extra_effects": []  # 例如符文附加效果
        }
        return weapon

    def upgrade_weapon(self, weapon: dict, upgrade_points: int) -> dict:
        """
        对指定武器进行升级，使用一定的升级点数提升武器属性。

        升级后，武器的 damage 乘以 upgrade_factor 的对应次幂，
        同时增加武器等级和升级次数。若超过最大升级次数，则不再升级。

        Args:
            weapon (dict): 要升级的武器数据字典。
            upgrade_points (int): 可用于升级的点数，实际升级次数根据配置与当前状态计算。

        Returns:
            dict: 升级后的武器数据字典。
        """
        current_level = weapon.get("upgrade_level", 0)
        max_upgrade = self.max_upgrade_level
        # 允许升级的次数为 min(upgrade_points, max_upgrade - current_level)
        upgrade_times = min(upgrade_points, max_upgrade - current_level)
        if upgrade_times <= 0:
            return weapon

        # 升级计算：武器伤害乘以 upgrade_factor^upgrade_times
        new_damage = int(weapon["damage"] * (self.upgrade_factor ** upgrade_times))
        weapon["damage"] = new_damage
        weapon["description"] = f"伤害 {new_damage}"
        weapon["upgrade_level"] = current_level + upgrade_times
        weapon["level"] += upgrade_times  # 简单地将武器等级与升级次数挂钩
        return weapon

    def apply_rune(self, weapon: dict, rune: dict) -> dict:
        """
        将一个符文应用到武器上。该函数将符文数据添加到武器的 extra_effects 列表中，
        并更新武器的属性（如增加额外伤害、增加暴击率等）。
        
        Args:
            weapon (dict): 要附加符文的武器数据。
            rune (dict): 符文数据，格式由符文模块定义，通常包括：
                - name: 符文名称
                - effect: 符文效果描述
                - bonus: 增加的伤害或属性加成

        Returns:
            dict: 附加符文后的武器数据。
        """
        if "extra_effects" not in weapon:
            weapon["extra_effects"] = []
        weapon["extra_effects"].append(rune)
        # 示例：将符文 bonus 加到武器伤害上
        bonus = rune.get("bonus", 0)
        weapon["damage"] += bonus
        weapon["description"] = f"伤害 {weapon['damage']}, 附加 {rune.get('name')}"
        return weapon

if __name__ == "__main__":
    # 简单测试
    config = {
        "weapon_types": ["剑", "斧", "弓"],
        "weapon_adjectives": ["锋利的", "沉重的", "轻盈的"],
        "damage_range": [3, 10],
        "upgrade_factor": 1.2,
        "max_upgrade_level": 5
    }
    wm = WeaponManager(config)
    weapon = wm.generate_weapon()
    print("生成武器：")
    print(weapon)
    # 模拟升级
    upgraded_weapon = wm.upgrade_weapon(weapon, upgrade_points=3)
    print("升级后武器：")
    print(upgraded_weapon)
    # 模拟应用符文
    rune = {"name": "火焰符文", "effect": "fire_bonus", "bonus": 4}
    weapon_with_rune = wm.apply_rune(upgraded_weapon, rune)
    print("附加符文后的武器：")
    print(weapon_with_rune)
