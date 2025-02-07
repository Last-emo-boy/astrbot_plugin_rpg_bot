from astrbot.api.all import *
import json
import os
import random

# 导入后续各模块接口（这些模块后续单独实现）
from .dice import roll_dice, skill_check
from .character import CharacterManager
from .map_gen import MapManager
from .combat import CombatManager
from .weapon import WeaponManager
from .skill import SkillManager
from .llm_integration import LLMIntegration
from .item import ItemManager
from .rune import RuneManager
from .loot import LootManager
from .logger import get_logger


# 全局常量：四个方向及其反向映射
DIRECTIONS = ["north", "south", "east", "west"]
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}

# 持久化存储文件（游戏会话数据保存位置）
DATA_FILE = "game_data.json"

def load_game_data():
    """从 DATA_FILE 中加载游戏数据，若不存在则返回空字典"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            # 发生异常时返回空数据
            return {}
    return {}

def save_game_data(data):
    """将游戏数据保存到 DATA_FILE 中"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@register("rpg_bot", "Your Name", "大型RPG文字跑团插件，包含大世界地图、角色个性（远程/近战、物理/法术伤害、毒/火/冰属性）、武器升级、符文、掉落物系统、持久化存储和LLM叙事", "3.2.0", "repo url")
class RPGPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        # 从持久化文件中加载游戏会话数据；若不存在则初始化为空字典
        self.game_sessions = load_game_data()

        # 初始化各个子模块的管理器（这些模块后续分别实现具体逻辑）
        self.character_manager = CharacterManager(self.config)
        self.map_manager = MapManager(self.config)
        self.combat_manager = CombatManager(self.config, self.game_sessions, self.character_manager, self.map_manager)
        self.weapon_manager = WeaponManager(self.config)
        self.skill_manager = SkillManager(self.config)
        self.llm_integration = LLMIntegration(self.context, self.config)

        self.context.logger.info("RPGPlugin 初始化完成。")

    def persist_data(self):
        """将当前游戏会话数据持久化保存到 DATA_FILE 中"""
        save_game_data(self.game_sessions)

    # -------------------------------
    # 命令组：rpg（所有命令均以 /rpg 开头）
    # -------------------------------
    @command_group("rpg")
    def rpg(self):
        """RPG 相关子命令组"""
        pass

    # -------------------------------
    # 子命令：启动游戏会话
    # -------------------------------
    @rpg.command("startgame")
    async def start_game(self, event: AstrMessageEvent):
        """
        /rpg startgame
        启动游戏会话，初始化大世界地图，从坐标 (0,0) 房间开始。
        """
        session_id = event.session_id
        if session_id in self.game_sessions:
            yield event.plain_result("游戏会话已存在，请使用 /rpg status 查看状态。")
        else:
            # 使用 MapManager 创建初始房间
            start_coord = (0, 0)
            world = {start_coord: self.map_manager.generate_room(start_coord)}
            self.game_sessions[session_id] = {
                "players": [event.get_sender_name()],
                "log": ["游戏开始！"],
                "characters": {},
                "world": world
            }
            self.persist_data()
            yield event.plain_result("新游戏会话已启动！欢迎踏入这无限广阔的世界。")

    # -------------------------------
    # 子命令：创建角色（包括个性和属性定义）
    # -------------------------------
    @rpg.command("create_character")
    async def create_character(self, event: AstrMessageEvent, name: str = None):
        """
        /rpg create_character [角色名]
        创建角色；若未提供则使用发送者昵称。
        在角色数据中新增：
          - 攻击类型：默认为 "melee"（近战），也可为 "ranged"（远程）
          - 物理攻击与物理防御
          - 法术攻击与法术防御
          - 额外属性：毒、火、冰（用于额外属性伤害或抗性）
          - 人格（temperament）：随机分配 "calm"、"neutral"、"irritable"，影响技能检定修正
        """
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
        # 从配置中获取基础属性
        hp = self.config.get("default_character_hp", 100)
        phys_attack = self.config.get("default_character_attack", 10)
        phys_defense = self.config.get("default_character_defense", 5)
        mag_attack = self.config.get("default_magic_attack", 8)
        mag_defense = self.config.get("default_magic_defense", 5)
        # 额外属性：毒、火、冰初始抗性或伤害加成，默认设置（后续模块中可扩展升级）
        extra_attributes = {
            "poison": self.config.get("default_poison", 0),
            "fire": self.config.get("default_fire", 0),
            "ice": self.config.get("default_ice", 0)
        }
        temperament = random.choice(["calm", "neutral", "irritable"])
        # 调用 CharacterManager 接口创建角色（具体实现在 character.py 中）
        char = self.character_manager.create_character(
            name=name,
            hp=hp,
            phys_attack=phys_attack,
            phys_defense=phys_defense,
            mag_attack=mag_attack,
            mag_defense=mag_defense,
            extra_attributes=extra_attributes,
            temperament=temperament,
            # 默认近战攻击类型，可后续通过装备或指令更改为远程
            attack_type="melee",
            # 初始武器、技能等由 character_manager 内部处理
        )
        session["characters"][sender_id] = char
        self.persist_data()
        yield event.plain_result(
            f"角色创建成功！\n名称: {char['name']}\nHP: {hp}\n物理攻击: {phys_attack}  防御: {phys_defense}\n"
            f"法术攻击: {mag_attack}  防御: {mag_defense}\n人格: {temperament}\n"
            f"初始武器: {char['weapon']['name']}（{char['weapon']['description']}），技能: {char['skills'][0]}\n"
            f"额外属性: 毒 {extra_attributes['poison']}，火 {extra_attributes['fire']}，冰 {extra_attributes['ice']}"
        )

    # -------------------------------
    # 子命令：查看角色信息
    # -------------------------------
    @rpg.command("character")
    async def character_info(self, event: AstrMessageEvent):
        """
        /rpg character
        查看你的角色信息，包括各项属性、攻击类型、额外属性及库存等。
        """
        session_id = event.session_id
        sender_id = event.get_sender_id()
        if session_id not in self.game_sessions or sender_id not in self.game_sessions[session_id]["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
        else:
            char = self.game_sessions[session_id]["characters"][sender_id]
            info = (
                f"名称: {char['name']}\n"
                f"HP: {char['hp']} / {char['max_hp']}\n"
                f"物理攻击: {char['attack']}  防御: {char['defense']}\n"
                f"法术攻击: {char['magic_attack']}  防御: {char['magic_defense']}\n"
                f"额外属性 - 毒: {char['extra_attributes'].get('poison',0)}, "
                f"火: {char['extra_attributes'].get('fire',0)}, "
                f"冰: {char['extra_attributes'].get('ice',0)}\n"
                f"攻击类型: {char.get('attack_type','melee')}\n"
                f"人格: {char.get('temperament','neutral')}\n"
                f"技能: {', '.join(char['skills'])}\n"
                f"位置: {char['position']}\n"
                f"金币: {char.get('money',0)}\n"
                f"当前武器: {char['weapon']['name']}\n"
                "库存: " + (
                    ", ".join(
                        f"[{i}] {item['name']}（{item.get('description','')}）"
                        if isinstance(item, dict) else f"[{i}] {item}"
                        for i, item in enumerate(char["inventory"])
                    ) if char["inventory"] else "空"
                )
            )
            yield event.plain_result(info)

    # -------------------------------
    # 子命令：移动房间（接口由 MapManager 实现）
    # -------------------------------
    @rpg.command("move")
    async def move(self, event: AstrMessageEvent, direction: str):
        """
        /rpg move [方向]
        移动到指定方向（north, south, east, west），调用 MapManager 接口处理房间生成与连接。
        """
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
        # 调用 MapManager 的移动接口，返回结果字符串
        result = self.map_manager.move_character(session, sender_id, direction)
        self.persist_data()
        yield event.plain_result(result)

    # -------------------------------
    # 子命令：近战/远程战斗（接口由 CombatManager 实现）
    # -------------------------------
    @rpg.command("battle")
    async def battle(self, event: AstrMessageEvent):
        """
        /rpg battle
        发起物理战斗（可区分近战与远程），计算伤害、经验奖励和掉落（具体逻辑由 CombatManager 实现）。
        """
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        battle_log = self.combat_manager.start_battle(session, sender_id, attack_mode="physical")
        self.persist_data()
        yield event.plain_result("\n".join(battle_log))

    # -------------------------------
    # 子命令：法术攻击（元素攻击，由 CombatManager 接口实现）
    # -------------------------------
    @rpg.command("cast")
    async def cast_spell(self, event: AstrMessageEvent, element: str, difficulty: int = 15):
        """
        /rpg cast <元素> [难度]
        使用法术攻击，元素可为 fire、ice、poison。
        调用 CombatManager 中的法术攻击接口，进行技能检定和伤害计算。
        """
        element = element.lower()
        if element not in ["fire", "ice", "poison"]:
            yield event.plain_result("无效元素，请选择 fire、ice 或 poison。")
            return
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        # 调用 CombatManager 的法术攻击接口，返回战斗日志
        log_lines = self.combat_manager.cast_spell(session, sender_id, element, difficulty)
        self.persist_data()
        yield event.plain_result("\n".join(log_lines))

    # -------------------------------
    # 子命令：调用 LLM 生成叙事（接口由 LLMIntegration 实现）
    # -------------------------------
    @rpg.command("narrative")
    async def narrative(self, event: AstrMessageEvent, prompt: str):
        """
        /rpg narrative <提示>
        调用 LLM 生成叙事文本，并追加到游戏日志中（融合当前房间信息与日志）。
        """
        provider = self.llm_integration
        if not provider:
            yield event.plain_result("未启用LLM提供商。")
            return
        session_id = event.session_id
        sender_id = event.get_sender_id()
        session = self.game_sessions.get(session_id)
        if not session or sender_id not in session["characters"]:
            yield event.plain_result("你还没有创建角色，请使用 /rpg create_character 创建。")
            return
        narrative_text = await self.llm_integration.generate_narrative(session, sender_id, prompt)
        session["log"].append(narrative_text)
        self.persist_data()
        yield event.plain_result(narrative_text)

    # -------------------------------
    # 全局事件钩子：输出调试日志
    # -------------------------------
    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        debug_info = (
            f"[DEBUG] 收到事件：\n"
            f"发送者 ID: {event.get_sender_id()}\n"
            f"发送者名称: {event.get_sender_name()}\n"
            f"消息内容: {event.message_str}\n"
            f"原始消息: {event.message_obj.raw_message}\n"
            f"时间戳: {event.timestamp}"
        )
        self.context.logger.debug(debug_info)
