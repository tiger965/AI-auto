# -*- coding: utf-8 -*-
"""
视觉模块: 视觉处理子包初始化
功能描述: 提供图像处理和对象检测功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

# 版本信息
__version__ = "1.0.0"

# 导出子模块类和函数
from .image_processor import ImageProcessor, ImageConfig, resize_image, normalize_image
from .object_detection import ObjectDetector, DetectionResult

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"视觉处理模块初始化完成，版本 {__version__}")

# 从配置加载器加载视觉模块特定配置
try:
    from ...config.config_loader import ConfigLoader
    # 初始化配置加载器
    config_loader = ConfigLoader()
    VISION_CONFIG = config_loader.load("modules.vision")
except ImportError:
    import warnings
    warnings.warn("配置加载器未找到，使用默认视觉模块配置")
    VISION_CONFIG = {
        "image_processor": {
            "default_format": "RGB",
            "max_size": 1024,
            "cache_enabled": True,
            "cache_size": 100
        },
        "object_detection": {
            "model_path": "models/detection/default",
            "confidence_threshold": 0.5,
            "enable_gpu": False
        }
    }

# 导出的模块、类和函数
__all__ = [
    "ImageProcessor",
    "ImageConfig",
    "resize_image",
    "normalize_image",
    "ObjectDetector",
    "DetectionResult",
    "get_vision_config"
]

def get_vision_config():
    """
    获取视觉模块配置
    
    返回:
        dict: 视觉模块的配置字典
    """
    return VISION_CONFIG