# -*- coding: utf-8 -*-
"""
系统功能模块包初始化文件
版本: 1.0
创建日期: 2025-04-17
"""


# 添加项目根目录到Python路径
from .cache import CacheManager
from .security import SecurityManager
from .scheduler import TaskScheduler
from .monitor import SystemMonitor
import os
import sys

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../" * __file__.count("/"))
)
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)

__all__ = ["SystemMonitor", "TaskScheduler", "SecurityManager", "CacheManager"]

# 版本信息
__version__ = "1.0.0"