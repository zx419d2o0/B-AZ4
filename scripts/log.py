from pathlib import Path
import logging
import shutil
from functools import cache
from typing import List
import re

# 日志目录和文件路径
LOG_DIR = Path(__file__).parent.parent / "assets"
CURRENT_LOG = LOG_DIR / "current.log"
BACKUP_LOG = LOG_DIR / "backup.log"

# **日志级别映射**
LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

# **匹配 "时间 - 级别 - 内容" 的格式**
LOG_PATTERN = re.compile(r" - (DEBUG|INFO|WARNING|ERROR) - ")

@cache
def setup_logging() -> logging.Logger:
    """初始化日志系统，所有日志存入文件，控制台日志可筛选"""
    LOG_DIR.mkdir(exist_ok=True)

    # 备份旧日志
    if CURRENT_LOG.exists():
        BACKUP_LOG.unlink(missing_ok=True)
        shutil.move(CURRENT_LOG, BACKUP_LOG)

    # 日志格式
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # 获取 logger
    logger = logging.getLogger("flet")
    logger.setLevel(logging.DEBUG)  # **文件存储 DEBUG 及以上的所有日志**

    if not logger.handlers:
        # **文件处理器（所有日志）**
        file_handler = logging.FileHandler(CURRENT_LOG, encoding="utf-8")
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)  # **确保所有日志存入文件**
        logger.addHandler(file_handler)

        # **控制台处理器（默认 INFO）**
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.INFO)  # **默认显示 INFO 及以上的日志**
        logger.addHandler(console_handler)

    return logger

def set_console_level(level: str):
    """动态调整控制台日志级别"""
    logger = logging.getLogger("flet")
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):  # 只调整控制台的日志级别
            handler.setLevel(getattr(logging, level.upper(), logging.INFO))

def get_log(level: str = "INFO", max_lines: int = 100) -> List[str]:
    """
    读取日志文件并按级别过滤，返回最近的 `max_lines` 条日志。
    :param level: 需要显示的最低日志级别 ("DEBUG", "INFO", "WARNING", "ERROR")
    :param max_lines: 返回的日志条数
    :return: 过滤后的日志列表
    """
    min_level = LEVEL_MAP.get(level.upper(), logging.INFO)  # 默认为 INFO 级别
    log_lines = []

    if CURRENT_LOG.exists():
        with CURRENT_LOG.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[::-1]:  # 从文件尾部开始（即时间倒序）
                match = LOG_PATTERN.search(line)  # 查找日志级别
                if match:
                    log_level = match.group(1)  # 获取日志级别
                    if LEVEL_MAP[log_level] >= min_level:
                        log_lines.append(line.strip())  # 只保留符合级别的日志
                if len(log_lines) >= max_lines:  # 限制返回最大条数
                    break

    return log_lines

# **初始化 logger**
logger = setup_logging()
logger.debug("日志系统已初始化")
