from astrbot.api.all import *
import random

# 定义四个方向及其反向映射
DIRECTIONS = ["north", "south", "east", "west"]
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}

@register("rpg_bot", "Your Name", "一个大型RPG文字跑团机器人插件：包含大世界地图、房间穿越、角色创建、武器技能、动态升级、战斗、物品交互、休息、装备替换、技能学习和LLM叙事", "3.1.0", "repo url")
class RPGPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        # 每个会话存储：玩家列表、游戏日志、角色信息、以及构成“世界”的房间字典（键为 (x, y) 坐标）
        self.game_sessions = {}

    # -------------------------------
    # 指令组：rpg
    # -------------------------------
    @command_group("rpg")
    def rpg(self):
        """RPG 相关子命令"""
        pass

    # -------------------------------
    # 辅助函数：房间生成与管理
    # -------------------------------
    def generate_room(self, coord: tuple, entry_direction: str = None):
        """
        生成一个房间数据。
          - coord: 房间坐标 (x, y)
          - entry_direction: 若非空，则保证入口对应的反向门开启（玩家刚进入的方向）
        房间包含：描述、各方向门（随机生成）、以及房间内的物品（一定概率生成）
        """
        descriptions = [
            "一片荒芜之地", "绿意盎然的森林", "神秘的遗迹", "阴暗的地下室",
            "开阔的草原", "崎岖的山路", "雾气缭绕的沼泽", "破败的城堡遗址"
        ]
        room_desc = random.choice(descriptions)
        # 随机生成每个方向是否有门；若为入口反方向，门必须开启
        doors = {}
        for d in DIRECTIONS:
            if entry_direction and d == OPPOSITE.get(entry_direction):
                doors[d] = True
            else:
                doors[d] = random.random() < 0.5  # 50%概率开启
        # 房间内物品：30%概率生成1～2个物品
        items = []
        if random.random() < 0.3:
            count = random.randint(1, 2)
            for _ in range(count):
                items.append(self.generate_room_item())
        room = {
            "coord": coord,
            "description": room_desc,
            "doors": doors,
            "items": items  # 房间内待拾取的物品列表（均为字典）
        }
        return room

    def generate_room_item(self):
        """随机生成房间内可拾取的物品：药水、金币、宝箱或卷轴"""
        item_types = ["宝箱", "药水", "卷轴", "金币"]
        adjectives = ["闪亮的", "古老的", "破旧的", "神秘的"]
        item_type = random.choice(item_types)
        adj = random.choice(adjectives)
        bonus = random.randint(1, 10)
        if item_type == "药水":
            return {"type": "consumable", "name": f"{adj}{item_type}", "effect": "heal", "value": bonus * 10}
        elif item_type == "金币":
            return {"type": "money", "name": f"{bonus} {item_type}", "effect": "money", "value": bonus}
        elif item_type == "宝箱":
            return {"type": "loot", "name": f"{adj}{item_type}", "effect": "loot", "value": bonus}
        elif item_type == "卷轴":
            skill = random.choice(self.config.get("skill_list", ["斩击", "穿刺", "防御", "火球术"]))
            return {"type": "scroll", "name": f"{adj}{item_type}", "effect": "skill", "value": skill}
        return {"type": "misc", "name": f"{adj}{item_type}", "effect": None, "value": bonus}

    def get_current_room(self, session, sender_id):
        """
        根据当前会话和玩家ID返回玩家所在的房间数据。
        """
        char = session["characters"].get(sender_id)
        if char:
            pos = char["position"]
            return session["world"].get(pos)
        return None

    # -------------------------------
    # 辅助函数：武器与技能
    # -------------------------------
    def generate_weapon(self):
        """随机生成一把武器，其伤害在配置范围内"""
        weapon_types = ["剑", "斧", "锤", "弓", "匕首"]
        adjectives = ["锋利的", "重型的", "轻盈的", "破旧的", "神秘的"]
        chosen_item = random.choice(weapon_types)
        adj = random.choice(adjectives)
        dmg_min, dmg_max = self.config.get("weapon_damage_range", [2, 8])
        damage = random.randint(dmg_min, dmg_max)
        return {"type": "weapon", "name": f"{adj}{chosen_item}", "damage": damage, "description": f"伤害 {damage}"}

    def generate_skill(self):
        """从配置中随机选取一个技能"""
        skill_list = self.config.get("skill_list", ["斩击", "穿刺", "防御", "火球术"])
        return random.choice(skill_list)

    # -------------------------------
    # 子命令：骰子判定
    # -------------------------------
    @rpg.command("roll")
    async def roll_dice(self, event: AstrMessageEvent, num_dice: int = 1, dice_sides: int = None):
        '''/rpg roll [骰子数量] [面数] - 骰子判定；若未指定面数则使用配置默认。'''
        if dice_sides is None:
            dice_sides = self.config.get("default_dice_sides", 6)
        results = [random.randint(1, dice_sides) for _ in range(num_dice)]
        total = sum(results)
        yield event.plain_result(f"你掷出了 {num_dice} 个 {dice_sides} 面骰，结果：{results}，总和：{total}")

    # -------------------------------
    # 子命令：启动游戏会话
    # -------------------------------
    @rpg.command("startgame")
    async def start_game(self, event: AstrMessageEvent):
        '''/rpg startgame - 启动游戏会话，初始化大世界地图，从 (0,0) 开始。'''
        session_id = event.session_id
        if session_id in self.game_sessions:
            yield event.plain_result("游戏会话已存在，请使用 /rpg status 查看状态。")
        else:
            world = {}
            start_coord = (0, 0)
            world[start_coord] = self.generate_room(start_coord)
            self.game_sessions[session_id] = {
                "players": [event.get_sender_name()],
                "log": ["游戏开始！"],
                "characters": {},
                "world": world
            }
            yield event.plain_result("新游戏会话已启动！欢迎踏入这无限广阔的世界。")

    # -------------------------------
    # 子命令：创建角色
    # -------------------------------
    @rpg.command("create_character")
    async def create_character(self, event: AstrMessageEvent, name: str = None):
        '''/rpg create_character [角色名] - 创建角色；若未提供则用发送者昵称。'''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name()
        if session_id not in self.game_sessions:
            yield event.plain_result("请先启动游戏会话：/rpg startgame")
            return
        session = self.game_sessions[session_id]
        if sender_id in session["characters"]:
            yield event.plain_result("你已创建过角色。")
            return
        if not name:
            name = sender_name
        hp = self.config.get("default_character_hp", 100)
        attack = self.config.get("default_character_attack", 10)
        defense = self.config.get("default_character_defense", 5)
        character = {
            "name": name,
            "hp": hp,
            "max_hp": hp,
            "attack": attack,
            "defense": defense,
            "level": 1,
            "exp": 0,
            "position": (0, 0),
            "weapon": self.generate_weapon(),
            "skills": [self.generate_skill()],
            "inventory": [],
            "money": 0
        }
        session["characters"][sender_id] = character
        yield event.plain_result(
            f"角色创建成功！名称：{name}, HP: {hp}, 攻击: {attack}, 防御: {defense}\n"
            f"初始武器：{character['weapon']['name']}（{character['weapon']['description']}），技能：{character['skills'][0]}"
        )

    # -------------------------------
    # 子命令：查看角色信息
    # -------------------------------
    @rpg.command("character")
    async def character_info(self, event: AstrMessageEvent):
        '''/rpg character - 查看你的角色信息。'''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        if session_id not in self.game_sessions or sender_id not in self.game_sessions[session_id]["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
        else:
            char = self.game_sessions[session_id]["characters"][sender_id]
            info = (
                f"名称: {char['name']}\n"
                f"HP: {char['hp']} / {char['max_hp']}\n"
                f"攻击: {char['attack']} + 武器({char['weapon']['damage']})\n"
                f"防御: {char['defense']}\n"
                f"等级: {char['level']}\n"
                f"经验: {char['exp']}\n"
                f"技能: {', '.join(char['skills'])}\n"
                f"位置: {char['position']}\n"
                f"金币: {char.get('money', 0)}\n"
                f"当前武器: {char['weapon']['name']}\n"
                "库存: " + (
                    ", ".join(
                        f"[{i}] {item['name']}（{item.get('description','')}）" if isinstance(item, dict) else f"[{i}] {item}"
                        for i, item in enumerate(char["inventory"])
                    ) if char["inventory"] else "空"
                )
            )
            yield event.plain_result(info)

    # -------------------------------
    # 子命令：查看库存
    # -------------------------------
    @rpg.command("inventory")
    async def inventory_info(self, event: AstrMessageEvent):
        '''/rpg inventory - 查看你的库存。'''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        if session_id not in self.game_sessions or sender_id not in self.game_sessions[session_id]["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
        else:
            inv = self.game_sessions[session_id]["characters"][sender_id]["inventory"]
            if not inv:
                yield event.plain_result("你的库存为空。")
            else:
                msg = "你的库存：\n"
                for i, item in enumerate(inv):
                    if isinstance(item, dict):
                        msg += f"[{i}] {item['name']}（{item.get('description','')}）\n"
                    else:
                        msg += f"[{i}] {item}\n"
                yield event.plain_result(msg)

    # -------------------------------
    # 子命令：生成道具装备
    # -------------------------------
    @rpg.command("item")
    async def generate_item(self, event: AstrMessageEvent):
        '''/rpg item - 生成随机道具装备，并加入你的库存（需先创建角色）。'''
        item_types = ["剑", "盾牌", "法杖", "弓", "盔甲", "戒指", "项链"]
        adjectives = ["神秘的", "古老的", "光辉的", "暗影的", "锋利的", "坚固的"]
        stats = ["力量", "敏捷", "智力", "体力", "幸运"]
        chosen_item = random.choice(item_types)
        adj = random.choice(adjectives)
        stat = random.choice(stats)
        bonus = random.randint(1, 10)
        # 如果属于武器则标记为 weapon，否则 accessory
        item_type = "weapon" if chosen_item in ["剑", "斧", "锤", "弓", "匕首"] else "accessory"
        generated_item = {
            "type": item_type,
            "name": f"{adj}{chosen_item}",
            "stat": stat,
            "bonus": bonus,
            "description": f"增加 {bonus} 点 {stat}"
        }
        session_id = event.session_id
        sender_id = event.get_sender_id()
        if session_id in self.game_sessions and sender_id in self.game_sessions[session_id]["characters"]:
            self.game_sessions[session_id]["characters"][sender_id]["inventory"].append(generated_item)
            yield event.plain_result(
                f"生成的道具装备：{generated_item['name']}（{generated_item['description']}）已加入你的库存。"
            )
        else:
            yield event.plain_result(
                f"生成的道具装备：{generated_item['name']}（{generated_item['description']}）\n提示：请先创建角色（/rpg create_character）"
            )

    # -------------------------------
    # 子命令：拾取房间内物品
    # -------------------------------
    @rpg.command("pickup")
    async def pickup_item(self, event: AstrMessageEvent, index: int = None):
        '''
        /rpg pickup [编号] - 拾取当前房间内物品。
         - 不指定编号则列出房间内所有物品；
         - 指定编号则拾取该物品，若为金币则自动增加角色金币，否则加入库存。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        room = self.get_current_room(session, sender_id)
        if not room or not room.get("items"):
            yield event.plain_result("当前房间内没有可拾取的物品。")
            return
        items = room["items"]
        if index is None:
            msg = "当前房间内的物品：\n"
            for i, item in enumerate(items):
                msg += f"[{i}] {item['name']}\n"
            msg += "使用 /rpg pickup <编号> 来拾取物品。"
            yield event.plain_result(msg)
        else:
            if index < 0 or index >= len(items):
                yield event.plain_result("无效的物品编号。")
                return
            item = items.pop(index)
            char = session["characters"][sender_id]
            if item.get("effect") == "money":
                char["money"] += item.get("value", 0)
                yield event.plain_result(f"你拾取了金币，获得 {item.get('value', 0)} 金币。")
            else:
                char["inventory"].append(item)
                yield event.plain_result(f"你拾取了：{item['name']}")

    # -------------------------------
    # 子命令：丢弃库存物品到房间
    # -------------------------------
    @rpg.command("drop")
    async def drop_item(self, event: AstrMessageEvent, index: int):
        '''
        /rpg drop <编号> - 将库存中的物品丢弃到当前房间内。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        inv = session["characters"][sender_id]["inventory"]
        if index < 0 or index >= len(inv):
            yield event.plain_result("无效的库存编号。")
            return
        item = inv.pop(index)
        room = self.get_current_room(session, sender_id)
        if room is not None:
            if "items" not in room:
                room["items"] = []
            room["items"].append(item)
        yield event.plain_result(f"你丢弃了：{item['name']} 到当前房间。")

    # -------------------------------
    # 子命令：装备库存中的武器
    # -------------------------------
    @rpg.command("equip")
    async def equip_item(self, event: AstrMessageEvent, index: int):
        '''
        /rpg equip <编号> - 装备库存中武器（仅限 weapon 类型），装备后原武器放入库存。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        inv = char["inventory"]
        if index < 0 or index >= len(inv):
            yield event.plain_result("无效的库存编号。")
            return
        item = inv[index]
        if not isinstance(item, dict) or item.get("type") != "weapon":
            yield event.plain_result("该物品无法装备。")
            return
        old_weapon = char["weapon"]
        char["weapon"] = item
        inv.pop(index)
        if old_weapon:
            inv.append(old_weapon)
        yield event.plain_result(f"你已装备 {item['name']}（{item['description']}），原武器 {old_weapon['name']}已存入库存。")

    # -------------------------------
    # 子命令：使用库存物品（例如药水）
    # -------------------------------
    @rpg.command("use_item")
    async def use_item(self, event: AstrMessageEvent, index: int):
        '''
        /rpg use_item <编号> - 使用库存中的物品，例如药水恢复生命。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        inv = char["inventory"]
        if index < 0 or index >= len(inv):
            yield event.plain_result("无效的库存编号。")
            return
        item = inv.pop(index)
        if isinstance(item, dict) and item.get("effect") == "heal":
            heal_value = item.get("value", 0)
            old_hp = char["hp"]
            char["hp"] = min(char["hp"] + heal_value, char["max_hp"])
            yield event.plain_result(f"你使用了 {item['name']}，生命值从 {old_hp} 恢复到 {char['hp']}。")
        else:
            yield event.plain_result(f"你使用了 {item['name'] if isinstance(item, dict) else item}，但没有产生明显效果。")

    # -------------------------------
    # 子命令：学习技能（使用卷轴）
    # -------------------------------
    @rpg.command("learn_skill")
    async def learn_skill(self, event: AstrMessageEvent, index: int):
        '''
        /rpg learn_skill <编号> - 使用库存中的卷轴学习技能，若成功则加入技能列表。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        inv = char["inventory"]
        if index < 0 or index >= len(inv):
            yield event.plain_result("无效的库存编号。")
            return
        item = inv[index]
        if isinstance(item, dict) and item.get("effect") == "skill":
            skill = item.get("value")
            if skill in char["skills"]:
                yield event.plain_result(f"你已经学会了 {skill}。")
            else:
                char["skills"].append(skill)
                inv.pop(index)
                yield event.plain_result(f"你使用了 {item['name']}，成功学会了技能 {skill}。")
        else:
            yield event.plain_result("该物品不是技能卷轴，无法学习技能。")

    # -------------------------------
    # 子命令：查看整体游戏状态
    # -------------------------------
    @rpg.command("status")
    async def game_status(self, event: AstrMessageEvent):
        '''
        /rpg status - 查看当前游戏会话状态，包括玩家列表和各角色基本信息。
        '''
        session_id = event.session_id
        session = self.game_sessions.get(session_id)
        if not session:
            yield event.plain_result("当前没有游戏会话。")
            return
        msg = "游戏会话状态：\n玩家：" + ", ".join(session["players"]) + "\n"
        for uid, char in session["characters"].items():
            msg += f"{char['name']} (位置: {char['position']}, 等级: {char['level']}, HP: {char['hp']}/{char['max_hp']}, 金币: {char.get('money',0)})\n"
        yield event.plain_result(msg)

    # -------------------------------
    # 子命令：查看世界地图（已探索区域）
    # -------------------------------
    @rpg.command("worldmap")
    async def world_map(self, event: AstrMessageEvent):
        '''
        /rpg worldmap - 显示当前会话中已探索的房间坐标地图：
         "X" 表示你所在位置，"O" 表示已探索房间，"." 表示未探索区域。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        world = session["world"]
        xs = [coord[0] for coord in world.keys()]
        ys = [coord[1] for coord in world.keys()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        char_pos = session["characters"][sender_id]["position"]
        map_str = ""
        for y in range(min_y, max_y + 1):
            row = ""
            for x in range(min_x, max_x + 1):
                if (x, y) in world:
                    row += " X " if (x, y) == char_pos else " O "
                else:
                    row += " . "
            map_str += row + "\n"
        yield event.plain_result("世界地图（O：已探索，X：你的位置）：\n" + map_str)

    # -------------------------------
    # 子命令：移动（穿越房间的门）
    # -------------------------------
    @rpg.command("move")
    async def move(self, event: AstrMessageEvent, direction: str):
        '''/rpg move [方向] - 移动到指定方向（north, south, east, west）。'''
        direction = direction.lower()
        if direction not in DIRECTIONS:
            yield event.plain_result("无效方向，请使用 north, south, east, west。")
            return
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        current_pos = char["position"]
        current_room = session["world"].get(current_pos)
        if not current_room:
            yield event.plain_result("当前房间数据丢失，请重启游戏。")
            return
        if not current_room["doors"].get(direction, False):
            yield event.plain_result(f"当前房间没有通往 {direction} 的门。")
            return
        # 计算新房间坐标（north: y-1, south: y+1, east: x+1, west: x-1）
        x, y = current_pos
        if direction == "north":
            new_pos = (x, y - 1)
        elif direction == "south":
            new_pos = (x, y + 1)
        elif direction == "east":
            new_pos = (x + 1, y)
        elif direction == "west":
            new_pos = (x - 1, y)
        if new_pos not in session["world"]:
            new_room = self.generate_room(new_pos, entry_direction=direction)
            session["world"][new_pos] = new_room
            session["log"].append(f"新房间 {new_pos} 被生成。")
        else:
            new_room = session["world"][new_pos]
        char["position"] = new_pos
        msg = f"你穿过 {direction} 的门，来到房间 {new_pos}。\n描述：{new_room['description']}\n可通往方向："
        available = [d for d, open_ in new_room["doors"].items() if open_]
        msg += ", ".join(available)
        if new_room.get("items"):
            msg += f"\n房间内有：{', '.join(item['name'] for item in new_room['items'])}"
        yield event.plain_result(msg)

    # -------------------------------
    # 子命令：回合制战斗
    # -------------------------------
    @rpg.command("battle")
    async def battle(self, event: AstrMessageEvent):
        '''/rpg battle - 与怪物战斗，计算伤害、经验奖励，并有概率获得掉落奖励。'''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        monster = self._generate_monster(char["level"])
        battle_log = []
        battle_log.append(f"战斗开始！你遇到了 Lv{monster['level']} 的 {monster['name']}！")
        round_num = 1
        while char["hp"] > 0 and monster["hp"] > 0:
            battle_log.append(f"【回合 {round_num}】")
            player_damage = max(0, char["attack"] + char["weapon"]["damage"] - monster["defense"] + random.randint(-2, 2))
            monster["hp"] -= player_damage
            battle_log.append(f"你攻击 {monster['name']}，造成 {player_damage} 点伤害。（怪物剩余 HP: {max(monster['hp'],0)})")
            if monster["hp"] <= 0:
                battle_log.append(f"你击败了 {monster['name']}！")
                gained_exp = monster["level"] * 15
                char["exp"] += gained_exp
                battle_log.append(f"获得经验：{gained_exp} 点。")
                exp_growth = self.config.get("exp_growth_factor", 1.2)
                required_exp = int(100 * (char["level"] ** exp_growth))
                if char["exp"] >= required_exp:
                    char["level"] += 1
                    char["exp"] -= required_exp
                    char["max_hp"] += 10
                    char["hp"] += 10
                    char["attack"] += 2
                    char["defense"] += 1
                    battle_log.append(f"恭喜升级！你现在等级 {char['level']}。（升级所需经验：{required_exp}）")
                if random.random() < 0.5:
                    loot = self.generate_weapon()
                    char["inventory"].append(loot)
                    battle_log.append(f"战斗奖励：获得武器 {loot['name']}（{loot['description']}）")
                break
            monster_damage = max(0, monster["attack"] - (char["defense"] // 2) + random.randint(-2, 2))
            char["hp"] -= monster_damage
            battle_log.append(f"{monster['name']} 攻击你，造成 {monster_damage} 点伤害。（你剩余 HP: {max(char['hp'],0)})")
            if char["hp"] <= 0:
                battle_log.append("你被击败了！战斗结束。")
                break
            round_num += 1
        yield event.plain_result("\n".join(battle_log))

    def _generate_monster(self, level: int):
        """生成怪物信息，属性基于指定等级"""
        monster_names = ["哥布林", "骷髅", "恶魔", "巨魔", "吸血鬼"]
        name = random.choice(monster_names)
        hp = level * random.randint(20, 30)
        attack = level * random.randint(3, 7)
        defense = level * random.randint(1, 3)
        return {"name": name, "level": level, "hp": hp, "attack": attack, "defense": defense}

    # -------------------------------
    # 子命令：休息恢复
    # -------------------------------
    @rpg.command("rest")
    async def rest(self, event: AstrMessageEvent):
        '''
        /rpg rest - 休息命令，恢复一定生命值（不超过最大HP），恢复量由配置决定。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        recover = self.config.get("rest_recover", 10)
        old_hp = char["hp"]
        char["hp"] = min(char["hp"] + recover, char["max_hp"])
        yield event.plain_result(f"你休息后，生命值从 {old_hp} 恢复到 {char['hp']}。")

    # -------------------------------
    # 子命令：使用技能
    # -------------------------------
    @rpg.command("use_skill")
    async def use_skill(self, event: AstrMessageEvent, skill_name: str = None):
        '''
        /rpg use_skill [技能名称] - 使用技能。
         - 不指定则显示你当前拥有的技能列表；
         - 指定后调用 LLM 生成技能效果叙事，并写入游戏日志。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        if not skill_name:
            yield event.plain_result("你当前拥有的技能：" + ", ".join(char["skills"]))
            return
        if skill_name not in char["skills"]:
            yield event.plain_result(f"你尚未学会技能 {skill_name}。")
            return
        provider = self.context.get_using_provider()
        if not provider:
            yield event.plain_result("未启用LLM提供商，无法生成技能描述。")
            return
        prompt = f"玩家使用技能 {skill_name}，释放出惊人的力量，请生成一段描述技能效果和战斗气势的叙事文本。"
        response = await provider.text_chat(prompt, session_id=event.session_id)
        narrative = response.completion_text.strip()
        session["log"].append(narrative)
        yield event.plain_result(narrative)

    # -------------------------------
    # 子命令：使用库存物品
    # -------------------------------
    @rpg.command("use_item")
    async def use_item(self, event: AstrMessageEvent, index: int):
        '''
        /rpg use_item <编号> - 使用库存中的物品，例如药水恢复生命。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        inv = char["inventory"]
        if index < 0 or index >= len(inv):
            yield event.plain_result("无效的库存编号。")
            return
        item = inv.pop(index)
        if isinstance(item, dict) and item.get("effect") == "heal":
            heal_value = item.get("value", 0)
            old_hp = char["hp"]
            char["hp"] = min(char["hp"] + heal_value, char["max_hp"])
            yield event.plain_result(f"你使用了 {item['name']}，生命值从 {old_hp} 恢复到 {char['hp']}。")
        else:
            yield event.plain_result(f"你使用了 {item['name'] if isinstance(item, dict) else item}，但没有产生明显效果。")

    # -------------------------------
    # 子命令：学习技能（使用卷轴）
    # -------------------------------
    @rpg.command("learn_skill")
    async def learn_skill(self, event: AstrMessageEvent, index: int):
        '''
        /rpg learn_skill <编号> - 使用库存中的卷轴学习技能，若成功则加入技能列表。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        inv = char["inventory"]
        if index < 0 or index >= len(inv):
            yield event.plain_result("无效的库存编号。")
            return
        item = inv[index]
        if isinstance(item, dict) and item.get("effect") == "skill":
            skill = item.get("value")
            if skill in char["skills"]:
                yield event.plain_result(f"你已经学会了 {skill}。")
            else:
                char["skills"].append(skill)
                inv.pop(index)
                yield event.plain_result(f"你使用了 {item['name']}，成功学会了技能 {skill}。")
        else:
            yield event.plain_result("该物品不是技能卷轴，无法学习技能。")

    # -------------------------------
    # 子命令：查看整体游戏状态
    # -------------------------------
    @rpg.command("status")
    async def game_status(self, event: AstrMessageEvent):
        '''
        /rpg status - 查看当前游戏会话状态，包括玩家列表和各角色基本信息。
        '''
        session_id = event.session_id
        session = self.game_sessions.get(session_id)
        if not session:
            yield event.plain_result("当前没有游戏会话。")
            return
        msg = "游戏会话状态：\n玩家：" + ", ".join(session["players"]) + "\n"
        for uid, char in session["characters"].items():
            msg += f"{char['name']} (位置: {char['position']}, 等级: {char['level']}, HP: {char['hp']}/{char['max_hp']}, 金币: {char.get('money',0)})\n"
        yield event.plain_result(msg)

    # -------------------------------
    # 子命令：查看世界地图（已探索区域）
    # -------------------------------
    @rpg.command("worldmap")
    async def world_map(self, event: AstrMessageEvent):
        '''
        /rpg worldmap - 显示当前会话中已探索的世界地图：
         "X" 表示你所在位置，"O" 表示已探索房间，"." 表示未探索区域。
        '''
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        world = session["world"]
        xs = [coord[0] for coord in world.keys()]
        ys = [coord[1] for coord in world.keys()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        char_pos = session["characters"][sender_id]["position"]
        map_str = ""
        for y in range(min_y, max_y + 1):
            row = ""
            for x in range(min_x, max_x + 1):
                if (x, y) in world:
                    row += " X " if (x, y) == char_pos else " O "
                else:
                    row += " . "
            map_str += row + "\n"
        yield event.plain_result("世界地图（O：已探索，X：你的位置）：\n" + map_str)

    # -------------------------------
    # 子命令：调用 LLM 生成叙事
    # -------------------------------
    @rpg.command("narrative")
    async def generate_narrative(self, event: AstrMessageEvent, prompt: str):
        '''
        /rpg narrative <提示> - 使用 LLM 生成叙事文本，并将其追加到游戏日志中，
        融合当前房间信息和游戏日志生成引人入胜的故事情节。
        '''
        provider = self.context.get_using_provider()
        if not provider:
            yield event.plain_result("未启用LLM提供商。")
            return
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        char = session["characters"][sender_id]
        pos = char["position"]
        room = session["world"].get(pos, {})
        room_desc = room.get("description", "未知")
        doors = room.get("doors", {})
        available_doors = ", ".join([d for d, open_ in doors.items() if open_])
        context_text = "\n".join(session["log"])
        full_prompt = (
            f"当前房间坐标：{pos}，描述：{room_desc}，可通往：{available_doors}\n"
            f"游戏日志：{context_text}\n"
            f"玩家提示：{prompt}\n"
            "请生成一段引人入胜的游戏叙事。"
        )
        response = await provider.text_chat(full_prompt, session_id=event.session_id)
        narrative = response.completion_text.strip()
        session["log"].append(narrative)
        yield event.plain_result(narrative)

    # -------------------------------
    # LLM 工具：生成怪物信息（function-calling）
    # -------------------------------
    @llm_tool(name="get_monster")
    async def get_monster(self, event: AstrMessageEvent, level: int) -> MessageEventResult:
        '''生成怪物信息工具。
        
        Args:
            level(number): 怪物等级
        '''
        monster = self._generate_monster(level)
        desc = (f"怪物: {monster['name']} | 等级: {monster['level']} | "
                f"HP: {monster['hp']} | 攻击: {monster['attack']} | 防御: {monster['defense']}")
        yield event.plain_result(desc)

    # -------------------------------
    # 子命令：显示帮助信息
    # -------------------------------
    @rpg.command("help")
    async def help_command(self, event: AstrMessageEvent):
        '''/rpg help - 显示所有指令帮助信息。'''
        help_text = (
            "RPG 文字跑团机器人插件指令列表（需以 /rpg 开头）：\n"
            "rpg roll [骰子数量] [面数] - 骰子判定\n"
            "rpg startgame - 启动游戏会话（初始化大世界）\n"
            "rpg create_character [角色名] - 创建角色\n"
            "rpg character - 查看角色信息\n"
            "rpg inventory - 查看库存\n"
            "rpg item - 生成道具装备并加入库存\n"
            "rpg pickup [编号] - 拾取房间内物品（不指定则列出）\n"
            "rpg drop <编号> - 丢弃库存物品到当前房间\n"
            "rpg equip <编号> - 装备库存中武器（仅限武器）\n"
            "rpg use_item <编号> - 使用库存中的物品（如药水）\n"
            "rpg learn_skill <编号> - 使用卷轴学习技能\n"
            "rpg status - 查看整体游戏状态\n"
            "rpg worldmap - 显示已探索的世界地图\n"
            "rpg move <方向> - 移动到指定方向（north, south, east, west）\n"
            "rpg room - 查看当前房间详情\n"
            "rpg battle - 与怪物战斗\n"
            "rpg rest - 休息恢复生命\n"
            "rpg use_skill [技能名称] - 使用技能（不指定则列出技能）\n"
            "rpg narrative <提示> - 调用LLM生成叙事，并追加日志\n"
            "LLM工具: get_monster - 生成指定等级怪物信息\n"
        )
        yield event.plain_result(help_text)

    # -------------------------------
    # 全局事件钩子：调试日志输出
    # -------------------------------
    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        # 构造详细的调试日志信息
        debug_info = (
            f"[DEBUG] 收到事件：\n"
            f"发送者 ID: {event.get_sender_id()}\n"
            f"发送者名称: {event.get_sender_name()}\n"
            f"消息内容: {event.message_str}\n"
            f"原始消息: {event.message_obj.raw_message}\n"
            f"时间戳: {event.timestamp}"
        )
        # 输出到日志（依赖 context.logger.debug 方法）
        self.context.logger.debug(debug_info)
