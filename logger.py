import logging
import sys

def get_logger(name: str = "RPGPlugin") -> logging.Logger:
    """
    获取一个配置好的 Logger 实例。

    Args:
        name (str): 日志记录器名称，默认 "RPGPlugin"。

    Returns:
        logging.Logger: 配置好的 Logger 实例，日志级别为 DEBUG。
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # 避免重复添加 Handler
    if not logger.handlers:
        # 创建控制台 Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

if __name__ == "__main__":
    # 简单测试
    logger = get_logger("TestLogger")
    logger.debug("这是一条 DEBUG 级别日志。")
    logger.info("这是一条 INFO 级别日志。")
    logger.error("这是一条 ERROR 级别日志。")
