import random

def roll_dice(num_dice: int, dice_sides: int) -> dict:
    """
    投掷指定数量和面数的骰子。

    Args:
        num_dice (int): 投掷骰子的数量。
        dice_sides (int): 骰子的面数。

    Returns:
        dict: 包含"results"（每个骰子的结果列表）和"total"（所有骰子结果之和）。
    """
    results = [random.randint(1, dice_sides) for _ in range(num_dice)]
    return {"results": results, "total": sum(results)}

def skill_check(modifier: int, difficulty: int, dice_sides: int = 20) -> dict:
    """
    进行一次技能检定。使用单个骰子（默认为 d20），将结果加上修正值后与难度比较，
    同时判断是否为暴击（骰子结果等于骰子面数）或致命失败（骰子结果为 1）。

    Args:
        modifier (int): 技能修正值（例如角色的属性加成）。
        difficulty (int): 检定难度值。
        dice_sides (int, optional): 骰子面数，默认为20。

    Returns:
        dict: 包含以下信息：
            - "roll": 投掷骰子的结果（单个数值）。
            - "modifier": 修正值。
            - "total": 骰子结果与修正值之和。
            - "difficulty": 检定难度。
            - "success": 布尔值，表示是否成功（total >= difficulty）。
            - "critical": 布尔值，表示是否暴击（roll == dice_sides）。
            - "fumble": 布尔值，表示是否致命失败（roll == 1）。
    """
    roll_result = random.randint(1, dice_sides)
    total = roll_result + modifier
    success = total >= difficulty
    critical = (roll_result == dice_sides)
    fumble = (roll_result == 1)
    return {
        "roll": roll_result,
        "modifier": modifier,
        "total": total,
        "difficulty": difficulty,
        "success": success,
        "critical": critical,
        "fumble": fumble
    }

if __name__ == "__main__":
    print("投掷 3 个 6 面骰：", roll_dice(3, 6))
    print("技能检定（modifier 3, difficulty 15）：", skill_check(3, 15))
