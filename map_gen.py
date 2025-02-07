import random

# 定义四个方向及其反向映射
DIRECTIONS = ["north", "south", "east", "west"]
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}

class MapManager:
    def __init__(self, config: dict):
        """
        初始化地图管理器

        Args:
            config (dict): 配置字典，包含房间生成的参数：
                - door_probability: 各方向门开启的概率（默认 0.5）
                - item_probability: 房间内生成物品的概率（默认 0.3）
                - room_descriptions: 房间描述列表
        """
        self.config = config
        self.door_probability = config.get("door_probability", 0.5)
        self.item_probability = config.get("item_probability", 0.3)
        self.room_descriptions = config.get("room_descriptions", [
            "一片荒芜之地",
            "绿意盎然的森林",
            "神秘的遗迹",
            "阴暗的地下室",
            "开阔的草原",
            "崎岖的山路",
            "雾气缭绕的沼泽",
            "破败的城堡遗址"
        ])

    def generate_room(self, coord: tuple, entry_direction: str = None) -> dict:
        """
        根据坐标生成一个房间数据。
        
        Args:
            coord (tuple): 房间坐标 (x, y)。
            entry_direction (str, optional): 如果非空，则表示玩家从该方向进入，
                                             对应反向门（OPPOSITE[entry_direction]）必须开启。
        
        Returns:
            dict: 房间数据字典，包含：
                - "coord": 坐标
                - "description": 随机房间描述
                - "doors": dict，键为 DIRECTIONS 中的方向，值为布尔值，表示该方向是否有门
                - "items": 列表，可能包含随机生成的物品（此处以字符串表示）
        """
        description = random.choice(self.room_descriptions)
        doors = {}
        for d in DIRECTIONS:
            if entry_direction and d == OPPOSITE.get(entry_direction):
                doors[d] = True
            else:
                doors[d] = random.random() < self.door_probability
        # 房间内物品：以 item_probability 概率生成 1～2 个物品（这里只用简单字符串表示，后续可调用物品模块）
        items = []
        if random.random() < self.item_probability:
            count = random.randint(1, 2)
            for i in range(count):
                items.append(f"神秘物品{i+1}")
        room = {
            "coord": coord,
            "description": description,
            "doors": doors,
            "items": items
        }
        return room

    def move_character(self, session: dict, sender_id: str, direction: str) -> str:
        """
        根据指定方向移动角色。如果新房间不存在，则自动生成新房间，并更新角色所在位置。

        Args:
            session (dict): 当前会话数据，其中包含 "characters" 与 "world" 键。
            sender_id (str): 玩家ID，必须在 session["characters"] 中存在。
            direction (str): 移动方向，必须为 "north"、"south"、"east" 或 "west"。

        Returns:
            str: 移动结果描述消息，包括新房间坐标、房间描述、可通往方向以及房间内物品信息。
        """
        # 获取当前角色位置
        char = session["characters"][sender_id]
        current_pos = char["position"]
        x, y = current_pos
        if direction == "north":
            new_pos = (x, y - 1)
        elif direction == "south":
            new_pos = (x, y + 1)
        elif direction == "east":
            new_pos = (x + 1, y)
        elif direction == "west":
            new_pos = (x - 1, y)
        else:
            return "无效的方向。"
        
        # 如果新房间不存在，则生成之
        if new_pos not in session["world"]:
            new_room = self.generate_room(new_pos, entry_direction=direction)
            session["world"][new_pos] = new_room
            session["log"].append(f"新房间 {new_pos} 被生成。")
        else:
            new_room = session["world"][new_pos]
        
        # 更新角色位置
        char["position"] = new_pos
        
        # 构造返回描述信息
        available_doors = [d for d, open_ in new_room["doors"].items() if open_]
        message = f"你向 {direction} 移动，来到房间 {new_pos}。\n描述：{new_room['description']}\n可通往方向：{', '.join(available_doors)}"
        if new_room["items"]:
            message += f"\n房间内发现：{', '.join(new_room['items'])}"
        return message

if __name__ == "__main__":
    # 简单测试
    config = {
        "door_probability": 0.6,
        "item_probability": 0.5,
        "room_descriptions": ["测试房间 A", "测试房间 B", "测试房间 C"]
    }
    mm = MapManager(config)
    start_room = mm.generate_room((0, 0))
    print("初始房间：")
    print(start_room)
    
    # 模拟会话数据结构
    session = {
        "players": ["测试玩家"],
        "log": [],
        "characters": {"test_id": {"position": (0, 0)}},
        "world": {(0, 0): start_room}
    }
    
    # 测试移动功能
    result = mm.move_character(session, "test_id", "north")
    print("移动结果：")
    print(result)
