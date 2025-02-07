class LLMIntegration:
    def __init__(self, context, config: dict):
        """
        初始化 LLM 集成模块。

        Args:
            context: 上下文对象，包含 logger、get_using_provider() 等接口。
            config (dict): 配置字典，可能包含 LLM 调用相关参数，例如系统提示、温度等。
        """
        self.context = context
        self.config = config
        # 可从配置中加载额外的 LLM 参数（例如系统提示、温度等），示例：
        self.system_prompt = config.get("llm_system_prompt", "你是一位优秀的游戏叙事编写者，请根据给定提示生成引人入胜的叙事。")
        self.temperature = config.get("llm_temperature", 0.7)

    async def generate_narrative(self, session: dict, sender_id: str, prompt: str) -> str:
        """
        根据当前会话和玩家提示生成一段叙事文本。
        
        构造完整的提示文本，内容包括当前角色所在房间描述、已记录的游戏日志和玩家输入提示，
        并调用 LLM 提供商生成叙事文本。

        Args:
            session (dict): 当前游戏会话数据，需包含 "world"、"log" 及角色数据。
            sender_id (str): 玩家ID，用于定位角色数据。
            prompt (str): 玩家输入的叙事提示。

        Returns:
            str: 生成的叙事文本，如果 LLM 提供商不可用则返回错误提示。
        """
        provider = self.context.get_using_provider()
        if not provider:
            self.context.logger.error("LLM 提供商不可用。")
            return "LLM 提供商不可用。"

        # 提取角色所在房间信息
        char = session["characters"].get(sender_id, {})
        pos = char.get("position", (0, 0))
        room = session["world"].get(pos, {})
        room_desc = room.get("description", "未知")
        doors = room.get("doors", {})
        available_doors = ", ".join([d for d, open_ in doors.items() if open_])
        # 整合游戏日志（若没有日志则为空字符串）
        context_log = "\n".join(session.get("log", []))
        # 构造完整提示文本
        full_prompt = (
            f"{self.system_prompt}\n"
            f"当前房间坐标：{pos}，描述：{room_desc}，可通往：{available_doors}\n"
            f"游戏日志：\n{context_log}\n"
            f"玩家提示：{prompt}\n"
            "请生成一段引人入胜的游戏叙事。"
        )
        self.context.logger.debug(f"LLM 输入提示：{full_prompt}")
        # 调用 LLM 提供商生成文本，注意 session_id 可用于上下文关联（若平台支持）
        response = await provider.text_chat(full_prompt, session_id=session.get("session_id", ""))
        narrative = response.completion_text.strip()
        self.context.logger.debug(f"LLM 生成文本：{narrative}")
        return narrative

if __name__ == "__main__":
    # 模拟测试环境
    import asyncio

    class DummyProvider:
        async def text_chat(self, prompt, session_id=""):
            # 简单模拟 LLM 返回结果
            class Response:
                completion_text = f"生成的叙事文本（基于提示：{prompt[:50]}...）"
            return Response()

    class DummyContext:
        def __init__(self):
            self.logger = self
        def debug(self, msg):
            print("[DEBUG]", msg)
        def error(self, msg):
            print("[ERROR]", msg)
        def info(self, msg):
            print("[INFO]", msg)
        def get_using_provider(self):
            return DummyProvider()

    # 构造模拟数据
    dummy_context = DummyContext()
    config = {"llm_system_prompt": "你是一位擅长写作的叙事大师。", "llm_temperature": 0.8}
    llm_integration = LLMIntegration(dummy_context, config)
    session = {
        "session_id": "session_test",
        "world": {
            (0, 0): {
                "description": "起始房间，光线昏暗。",
                "doors": {"north": True, "south": False, "east": True, "west": False},
                "items": []
            }
        },
        "log": ["游戏开始，冒险者踏上征程。"],
        "characters": {
            "test_id": {"position": (0, 0)}
        }
    }
    prompt = "前方出现了一个神秘的入口。"
    narrative = asyncio.run(llm_integration.generate_narrative(session, "test_id", prompt))
    print("生成叙事：")
    print(narrative)
