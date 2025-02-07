import random
from .dice import skill_check

class SkillManager:
    def __init__(self, config: dict):
        """
        初始化技能管理器。

        Args:
            config (dict): 配置字典，包含默认技能列表等参数。
                示例：
                  {
                    "skill_list": ["斩击", "火球术", "穿刺", "防御"],
                    "default_skill_db": {
                        "斩击": {
                            "type": "physical",
                            "base_multiplier": 1.2,
                            "cost": 0,
                            "description": "挥剑攻击，伤害略高于普通攻击。"
                        },
                        "火球术": {
                            "type": "magic",
                            "base_multiplier": 1.5,
                            "cost": 10,
                            "description": "发射火球，对敌人造成火属性法术伤害。"
                        },
                        "穿刺": {
                            "type": "physical",
                            "base_multiplier": 1.1,
                            "cost": 0,
                            "description": "快速穿刺，攻击速度快，但伤害较低。"
                        },
                        "防御": {
                            "type": "buff",
                            "base_multiplier": 0,
                            "cost": 0,
                            "description": "加强防御，减少受到的伤害。"
                        }
                    }
                  }
        """
        self.config = config
        # 默认技能数据库，可从配置中扩展
        self.skill_db = config.get("default_skill_db", {
            "斩击": {
                "type": "physical",
                "base_multiplier": 1.2,
                "cost": 0,
                "description": "挥剑攻击，伤害略高于普通攻击。"
            },
            "火球术": {
                "type": "magic",
                "base_multiplier": 1.5,
                "cost": 10,
                "description": "发射火球，对敌人造成火属性法术伤害。"
            },
            "穿刺": {
                "type": "physical",
                "base_multiplier": 1.1,
                "cost": 0,
                "description": "快速穿刺，攻击速度快，但伤害较低。"
            },
            "防御": {
                "type": "buff",
                "base_multiplier": 0,
                "cost": 0,
                "description": "加强防御，减少受到的伤害。"
            }
        })

    def get_skill_info(self, skill_name: str) -> dict:
        """
        返回指定技能的详细信息。

        Args:
            skill_name (str): 技能名称

        Returns:
            dict: 技能信息字典，如果技能不存在，则返回一个默认描述。
        """
        return self.skill_db.get(skill_name, {
            "name": skill_name,
            "type": "unknown",
            "base_multiplier": 1.0,
            "cost": 0,
            "description": "未知技能"
        })

    def use_skill(self, character: dict, skill_name: str, target: dict, difficulty: int) -> dict:
        """
        模拟角色使用技能。根据技能类型，进行技能检定后计算伤害。
        
        对于攻击技能（physical 或 magic），伤害计算公式示例：
          damage = max(0, (角色攻击属性 * base_multiplier + 检定总值) - (目标防御 + 目标相应抗性))
        检定采用 dice 模块的 skill_check 函数。
        
        Args:
            character (dict): 使用技能的角色数据。
            skill_name (str): 使用的技能名称。
            target (dict): 目标（例如怪物）的数据字典，需包含相应防御值（physical_defense 或 magic_defense）以及额外抗性（例如 fire、ice、poison）。
            difficulty (int): 技能检定难度。
        
        Returns:
            dict: 包含技能使用过程详细信息，包括检定结果、计算后的伤害和最终效果描述。
        """
        # 检查角色是否拥有该技能
        if skill_name not in character.get("skills", []):
            return {"error": f"你尚未学会技能 {skill_name}。"}
        
        skill_info = self.get_skill_info(skill_name)
        result = {}
        
        # 根据技能类型选择使用对应的攻击属性
        if skill_info["type"] == "physical":
            base_value = character.get("attack", 0)
            target_defense = target.get("physical_defense", 0)
        elif skill_info["type"] == "magic":
            base_value = character.get("magic_attack", 0)
            target_defense = target.get("magic_defense", 0)
        else:
            # buff 或其他技能类型直接返回描述信息
            result["outcome"] = f"你使用了 {skill_name}，效果：{skill_info['description']}"
            return result
        
        # 进行技能检定：使用 dice.skill_check 函数
        check = skill_check(modifier=base_value, difficulty=difficulty, dice_sides=20)
        result["check"] = check
        
        # 根据检定结果调整伤害：若检定失败则伤害降低
        multiplier = skill_info.get("base_multiplier", 1.0)
        if not check["success"]:
            multiplier *= 0.5
        
        # 计算伤害（此处为简化公式，后续可根据具体要求调整）
        damage = max(0, int((base_value * multiplier) + check["total"] - target_defense))
        result["damage"] = damage
        
        # 生成效果描述
        if damage >= target.get("hp", 0):
            outcome = f"你使用 {skill_name} 击败了 {target['name']}，造成 {damage} 点伤害！"
        else:
            outcome = f"你使用 {skill_name} 对 {target['name']} 造成 {damage} 点伤害。（目标剩余 HP: {max(target.get('hp', 0) - damage, 0)}）"
        result["outcome"] = outcome
        
        return result

    def learn_skill(self, character: dict, skill_name: str) -> str:
        """
        使角色学习新技能，若角色尚未拥有该技能，则加入技能列表。

        Args:
            character (dict): 角色数据字典。
            skill_name (str): 要学习的技能名称。

        Returns:
            str: 学习结果描述。
        """
        if skill_name in character.get("skills", []):
            return f"你已经学会了 {skill_name}。"
        character.setdefault("skills", []).append(skill_name)
        return f"你成功学会了 {skill_name}！"

if __name__ == "__main__":
    # 简单测试
    config = {
        "skill_list": ["斩击", "火球术", "穿刺", "防御"],
        "default_skill_db": {
            "斩击": {
                "type": "physical",
                "base_multiplier": 1.2,
                "cost": 0,
                "description": "挥剑攻击，伤害略高于普通攻击。"
            },
            "火球术": {
                "type": "magic",
                "base_multiplier": 1.5,
                "cost": 10,
                "description": "发射火球，对敌人造成火属性法术伤害。"
            },
            "穿刺": {
                "type": "physical",
                "base_multiplier": 1.1,
                "cost": 0,
                "description": "快速穿刺，攻击速度快，但伤害较低。"
            },
            "防御": {
                "type": "buff",
                "base_multiplier": 0,
                "cost": 0,
                "description": "加强防御，减少受到的伤害。"
            }
        }
    }
    sm = SkillManager(config)
    # 模拟角色数据
    character = {
        "name": "TestHero",
        "attack": 10,
        "magic_attack": 8,
        "skills": ["斩击"],
    }
    # 模拟目标数据
    target = {
        "name": "TestMonster",
        "hp": 50,
        "physical_defense": 5,
        "magic_defense": 4
    }
    result = sm.use_skill(character, "火球术", target, difficulty=15)
    print("技能使用结果：", result)
    learn_result = sm.learn_skill(character, "防御")
    print("学习技能结果：", learn_result)
    print("当前技能列表：", character["skills"])
