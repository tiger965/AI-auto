# -*- coding: utf-8 -*-
"""
视频模块: 视频处理子包初始化
功能描述: 提供视频加载、帧提取和视频分析功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-18
"""

# 版本信息
__version__ = "1.0.0"

# 导出子模块类和函数
from .video_processor import VideoProcessor, create_video_from_frames, extract_video_metadata

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"视频处理模块初始化完成，版本 {__version__}")

# 从配置加载器加载视频模块特定配置
try:
    from ...config.config_loader import ConfigLoader
    # 初始化配置加载器
    config_loader = ConfigLoader()
    VIDEO_CONFIG = config_loader.load("modules.video")
except ImportError:
    import warnings
    warnings.warn("配置加载器未找到，使用默认视频模块配置")
    VIDEO_CONFIG = {
        "video_processor": {
            "default_fps": 1,
            "cache_enabled": True,
            "cache_size": 50,
            "temp_dir": None,
            "default_format": "mp4"
        }
    }

# 导出的模块、类和函数
__all__ = [
    "VideoProcessor",
    "create_video_from_frames",
    "extract_video_metadata",
    "get_video_config"
]

def get_video_config():
    """
    获取视频模块配置
    
    返回:
        dict: 视频模块的配置字典
    """
    return VIDEO_CONFIG