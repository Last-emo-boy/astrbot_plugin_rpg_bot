import random
from dice import roll_dice, skill_check

class CombatManager:
    def __init__(self, config: dict, game_sessions: dict, character_manager, map_manager):
        """
        初始化战斗管理器。

        Args:
            config (dict): 配置字典，包含升级曲线、伤害系数等参数。
            game_sessions (dict): 当前游戏会话数据。
            character_manager: 角色管理器实例，用于访问角色数据。
            map_manager: 地图管理器实例，用于访问房间等信息。
        """
        self.config = config
        self.game_sessions = game_sessions
        self.character_manager = character_manager
        self.map_manager = map_manager

    def start_battle(self, session: dict, sender_id: str, attack_mode: str = "physical") -> list:
        """
        开始一场物理战斗（近战或远程），返回战斗过程日志列表。

        物理伤害计算公式示例：
          damage = max(0, (角色物理攻击 + 武器伤害 + 属性加成) - 怪物物理防御 + 随机浮动)

        Args:
            session (dict): 当前游戏会话数据。
            sender_id (str): 玩家ID。
            attack_mode (str): 攻击模式，默认为 "physical"（可扩展为 "ranged"）。

        Returns:
            list: 战斗过程中的详细日志信息列表。
        """
        char = session["characters"][sender_id]
        # 生成怪物数据（物理和法术属性均包含在内）
        monster = self._generate_monster(char["level"])
        log = []
        log.append(f"战斗开始！你遇到了 Lv{monster['level']} 的 {monster['name']}。")
        round_num = 1
        while char["hp"] > 0 and monster["hp"] > 0:
            log.append(f"【回合 {round_num}】")
            # 计算属性加成（例如角色可能有额外的物理攻击加成，默认值 0）
            attr_bonus = char.get("physical_bonus", 0)
            base_damage = char["attack"] + char["weapon"]["damage"] + attr_bonus
            # 随机波动，模拟战斗中的随机性
            rand_factor = random.randint(-2, 2)
            damage = max(0, base_damage - monster.get("physical_defense", 0) + rand_factor)
            monster["hp"] -= damage
            log.append(f"你攻击 {monster['name']}，造成 {damage} 点物理伤害。（怪物剩余 HP: {max(monster['hp'], 0)})")
            if monster["hp"] <= 0:
                log.append(f"你击败了 {monster['name']}！")
                gained_exp = monster["level"] * 15
                char["exp"] += gained_exp
                log.append(f"获得经验：{gained_exp} 点。")
                # 升级判定：所需经验 = 100 * (当前等级 ^ exp_growth_factor)
                exp_growth = self.config.get("exp_growth_factor", 1.2)
                required_exp = int(100 * (char["level"] ** exp_growth))
                if char["exp"] >= required_exp:
                    char["level"] += 1
                    char["exp"] -= required_exp
                    char["max_hp"] += 10
                    char["hp"] += 10
                    char["attack"] += 2
                    char["defense"] += 1
                    log.append(f"恭喜升级！你现在等级 {char['level']}。（升级所需经验：{required_exp}）")
                # 掉落奖励示例：50%概率获得一件武器
                if random.random() < 0.5:
                    loot = {"name": "掉落武器", "damage": random.randint(5, 10), "description": "蕴含神秘力量"}
                    char["inventory"].append(loot)
                    log.append(f"战斗奖励：获得武器 {loot['name']}（{loot['description']}）")
                break
            # 怪物回击：同样考虑随机波动
            m_rand = random.randint(-2, 2)
            m_damage = max(0, monster["physical_attack"] - char["defense"] + m_rand)
            char["hp"] -= m_damage
            log.append(f"{monster['name']} 回击你，造成 {m_damage} 点伤害。（你剩余 HP: {max(char['hp'], 0)})")
            if char["hp"] <= 0:
                log.append("你被击败了！战斗结束。")
                break
            round_num += 1
        return log

    def cast_spell(self, session: dict, sender_id: str, element: str, difficulty: int = 15) -> list:
        """
        进行一次法术攻击。使用骰子模块进行技能检定，
        计算法术伤害，考虑角色魔法攻击、人格影响和目标怪物的魔法防御及该元素抗性。

        法术伤害计算公式示例：
          damage = max(0, (角色魔法攻击 + 检定总值) - (怪物魔法防御 + 怪物该元素抗性))

        Args:
            session (dict): 当前会话数据。
            sender_id (str): 玩家ID。
            element (str): 法术元素（例如 fire, ice, poison）。
            difficulty (int): 技能检定难度。

        Returns:
            list: 法术攻击过程日志列表。
        """
        element = element.lower()
        char = session["characters"][sender_id]
        base_modifier = char["magic_attack"]
        # 根据人格调整修正： calm +2, irritable -2, neutral 0
        temperament = char.get("temperament", "neutral")
        if temperament == "calm":
            modifier = base_modifier + 2
        elif temperament == "irritable":
            modifier = base_modifier - 2
        else:
            modifier = base_modifier
        check = skill_check(modifier, difficulty, dice_sides=20)
        log = []
        log.append(f"法术检定：骰子 {check['roll']} + 修正 {modifier} = {check['total']}（难度 {difficulty}）")
        if check["fumble"]:
            log.append("致命失败！法术完全失效。")
            return log
        if not check["success"]:
            log.append("检定失败，法术效果大打折扣。")
            bonus = 0
        else:
            if check["critical"]:
                log.append("暴击成功！法术效果大幅提升。")
                bonus = check["total"] * 2
            else:
                bonus = check["total"]
        # 生成怪物目标数据
        monster = self._generate_monster(char["level"])
        monster_mag_def = monster.get("magic_defense", 0)
        monster_resist = monster.get("elemental_resistances", {}).get(element, 0)
        damage = max(0, (char["magic_attack"] + bonus) - (monster_mag_def + monster_resist))
        log.append(f"你施放 {element} 法术，对 {monster['name']} 造成 {damage} 点法术伤害。")
        if damage >= monster["hp"]:
            log.append(f"你击败了 {monster['name']}！")
        else:
            log.append(f"{monster['name']} 受到攻击后剩余 HP: {max(monster['hp'] - damage, 0)}。")
        return log

    def _generate_monster(self, level: int) -> dict:
        """
        生成怪物数据，包含物理和法术属性、以及各元素抗性。

        Returns:
            dict: 包含以下字段：
                - name, level, hp
                - physical_attack, physical_defense
                - magic_attack, magic_defense
                - elemental_resistances: dict，包含 "fire", "ice", "poison"
        """
        monster_names = ["哥布林", "骷髅", "恶魔", "巨魔", "吸血鬼"]
        name = random.choice(monster_names)
        hp = level * random.randint(20, 30)
        physical_attack = level * random.randint(3, 7)
        physical_defense = level * random.randint(1, 3)
        magic_attack = level * random.randint(1, 5)
        magic_defense = level * random.randint(1, 5)
        elemental_resistances = {
            "fire": random.randint(0, 5),
            "ice": random.randint(0, 5),
            "poison": random.randint(0, 5)
        }
        return {
            "name": name,
            "level": level,
            "hp": hp,
            "physical_attack": physical_attack,
            "physical_defense": physical_defense,
            "magic_attack": magic_attack,
            "magic_defense": magic_defense,
            "elemental_resistances": elemental_resistances
        }

if __name__ == "__main__":
    # 模拟简单测试
    config = {"exp_growth_factor": 1.2}
    game_sessions = {}
    # 创建一个模拟角色数据
    char = {
        "name": "TestHero",
        "hp": 100,
        "max_hp": 100,
        "attack": 10,
        "defense": 5,
        "magic_attack": 8,
        "magic_defense": 5,
        "physical_bonus": 3,  # 额外物理攻击加成
        "temperament": "irritable",
        "skills": ["斩击"],
        "weapon": {"name": "初始剑", "damage": 5, "description": "伤害 5"},
        "position": (0, 0),
        "inventory": [],
        "money": 0
    }
    session = {
        "players": ["TestHero"],
        "log": [],
        "characters": {"test_id": char},
        "world": {(0, 0): {
            "description": "起始房间",
            "doors": {"north": True, "south": False, "east": True, "west": False},
            "items": []
        }}
    }
    game_sessions["session_test"] = session

    cm = CombatManager(config, game_sessions, None, None)
    print("=== 物理战斗测试 ===")
    battle_log = cm.start_battle(session, "test_id", attack_mode="physical")
    for line in battle_log:
        print(line)
    print("\n=== 法术攻击测试 ===")
    spell_log = cm.cast_spell(session, "test_id", element="fire", difficulty=15)
    for line in spell_log:
        print(line)
