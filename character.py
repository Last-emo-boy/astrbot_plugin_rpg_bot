import random

class CharacterManager:
    def __init__(self, config: dict):
        """
        初始化角色管理器

        Args:
            config (dict): 配置字典，包含默认武器伤害、初始技能列表等参数
        """
        self.config = config

    def create_character(self,
                         name: str,
                         hp: int,
                         phys_attack: int,
                         phys_defense: int,
                         mag_attack: int,
                         mag_defense: int,
                         extra_attributes: dict,
                         temperament: str,
                         attack_type: str = "melee") -> dict:
        """
        创建一个新角色，返回角色数据字典。

        Args:
            name (str): 角色名称。
            hp (int): 角色初始生命值。
            phys_attack (int): 物理攻击基础值。
            phys_defense (int): 物理防御基础值。
            mag_attack (int): 法术攻击基础值。
            mag_defense (int): 法术防御基础值。
            extra_attributes (dict): 额外属性字典，例如 {"poison": 0, "fire": 0, "ice": 0}，
                                     用于后续计算额外伤害或抗性。
            temperament (str): 人格属性，取值 "calm"（冷静）、"neutral"（中性）、"irritable"（焦躁）。
                               该属性将影响技能检定（如：calm +2，irritable -2）。
            attack_type (str, optional): 攻击类型，默认为 "melee"（近战），也可以为 "ranged"（远程）。

        Returns:
            dict: 角色数据字典，包含以下字段：
                - name, hp, max_hp
                - attack: 物理攻击
                - defense: 物理防御
                - magic_attack: 法术攻击
                - magic_defense: 法术防御
                - extra_attributes: 毒、火、冰等额外属性
                - temperament: 人格属性
                - attack_type: 攻击类型
                - level, exp: 等级与经验
                - position: 当前位置，初始为 (0, 0)
                - weapon: 初始武器数据（由配置决定，若无则使用默认）
                - skills: 角色拥有的技能列表（默认取配置中的第一个技能）
                - inventory: 物品库存，初始为空列表
                - money: 金币数量，初始为 0
        """
        level = 1
        exp = 0
        position = (0, 0)
        
        # 初始武器：使用配置中的默认武器伤害，若未配置则默认 5
        default_weapon_damage = self.config.get("default_weapon_damage", 5)
        weapon = {
            "name": "初始剑",
            "damage": default_weapon_damage,
            "description": f"基础伤害 {default_weapon_damage}"
        }
        
        # 初始技能：默认使用配置中的第一个技能，如果没有则使用 "斩击"
        skill_list = self.config.get("skill_list", ["斩击"])
        skills = [skill_list[0]]
        
        character = {
            "name": name,
            "hp": hp,
            "max_hp": hp,
            "attack": phys_attack,          # 物理攻击
            "defense": phys_defense,        # 物理防御
            "magic_attack": mag_attack,     # 法术攻击
            "magic_defense": mag_defense,   # 法术防御
            "extra_attributes": extra_attributes,  # 例如 {"poison": 0, "fire": 0, "ice": 0}
            "temperament": temperament,     # 人格：决定技能检定修正
            "attack_type": attack_type,     # "melee" 或 "ranged"
            "level": level,
            "exp": exp,
            "position": position,
            "weapon": weapon,
            "skills": skills,
            "inventory": [],
            "money": 0
        }
        return character

if __name__ == "__main__":
    # 简单测试示例
    config = {
        "default_weapon_damage": 5,
        "skill_list": ["斩击", "火球术", "穿刺"]
    }
    cm = CharacterManager(config)
    # 构造额外属性字典
    extra_attrs = {"poison": 0, "fire": 0, "ice": 0}
    # 随机选取一个人格属性
    temperament = random.choice(["calm", "neutral", "irritable"])
    character = cm.create_character("TestHero", 100, 10, 5, 8, 5, extra_attrs, temperament, "melee")
    print("创建的角色数据：")
    print(character)
