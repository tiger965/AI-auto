# -*- coding: utf-8 -*-
"""
配置模块
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# 模块级变量
config = {}  # 全局配置对象
config_file = None  # 配置文件路径
logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，None则使用默认路径

    Returns:
        Dict: 配置字典
    """
    global config

    # 确定配置文件路径
    if config_path is None:
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, "config.json")

    # 记录配置文件路径
    global config_file
    config_file = config_path

    # 读取配置文件
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"配置已加载: {config_path}")
    except FileNotFoundError:
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        config = get_default_config()
    except json.JSONDecodeError:
        logger.error(f"配置文件格式错误: {config_path}，使用默认配置")
        config = get_default_config()
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}，使用默认配置")
        config = get_default_config()

    return config


def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置

    Returns:
        Dict: 默认配置字典
    """
    return {
        "app_name": "AI自动化系统",
        "version": "1.0.0",
        "debug": True,
        "log_level": "info",
        "api": {"enabled": True, "port": 8000, "host": "127.0.0.1"},
        "paths": {"data": "data", "logs": "logs", "temp": "temp"},
    }


def save_config() -> bool:
    """
    保存配置到文件

    Returns:
        bool: 是否成功
    """
    global config, config_file

    if config_file is None:
        logger.error("未指定配置文件路径")
        return False

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        # 写入配置
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        logger.info(f"配置已保存: {config_file}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False


def get_config() -> Dict[str, Any]:
    """
    获取当前配置

    Returns:
        Dict: 配置字典
    """
    global config
    return config


def update_config(key: str, value: Any) -> None:
    """
    更新配置项

    Args:
        key: 配置键
        value: 配置值
    """
    global config
    config[key] = value


# 初始化时加载配置
if not config:
    load_config()