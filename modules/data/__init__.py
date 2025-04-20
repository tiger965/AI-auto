# -*- coding: utf-8 -*-
"""
数据模块: 数据处理子包初始化
功能描述: 提供数据加载和转换功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

# 版本信息
__version__ = "1.0.0"

# 导出子模块类和函数
from .data_loader import DataLoader, LoaderConfig
from .data_transformer import DataTransformer, TransformerConfig

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"数据处理模块初始化完成，版本 {__version__}")

# 从配置加载器加载数据模块特定配置
try:
    from ...config.config_loader import ConfigLoader
    # 初始化配置加载器
    config_loader = ConfigLoader()
    DATA_CONFIG = config_loader.load("modules.data")
except ImportError:
    import warnings
    warnings.warn("配置加载器未找到，使用默认数据处理模块配置")
    DATA_CONFIG = {
        "data_loader": {
            "cache_enabled": True,
            "cache_size": 100,
            "default_format": "auto"
        },
        "data_transformer": {
            "default_output_format": "json",
            "preserve_original": True
        }
    }

# 导出的模块、类和函数
__all__ = [
    "DataLoader",
    "LoaderConfig",
    "DataTransformer",
    "TransformerConfig",
    "get_data_config"
]

def get_data_config():
    """
    获取数据模块配置
    
    返回:
        dict: 数据模块的配置字典
    """
    return DATA_CONFIG