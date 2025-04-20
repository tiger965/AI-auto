# -*- coding: utf-8 -*-
"""
功能模块: 主模块包初始化
功能描述: 提供AI系统中的核心功能模块集合，包括自然语言处理、视觉处理、音频处理、数据处理和视频处理
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-18
"""

from pathlib import Path

# 定义模块根目录
MODULE_ROOT = Path(__file__).parent.absolute()

# 从配置加载器加载模块配置
try:
    from ..config.config_loader import ConfigLoader
    # 初始化配置加载器
    config_loader = ConfigLoader()
    MODULE_CONFIG = config_loader.load("modules")
except ImportError:
    import warnings
    warnings.warn("配置加载器未找到，使用默认配置")
    MODULE_CONFIG = {}

# 版本信息
__version__ = "1.0.0"

# 导出子模块
__all__ = [
    "nlp",
    "vision",
    "audio",
    "data",
    "video"  # 新增的视频模块
]

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"功能模块初始化完成，版本 {__version__}")

def get_module_info():
    """
    获取功能模块包信息
    
    返回:
        dict: 包含模块版本、可用子模块等信息的字典
    """
    return {
        "version": __version__,
        "modules": __all__,
        "root_path": str(MODULE_ROOT)
    }