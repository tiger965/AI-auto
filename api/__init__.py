# 添加项目根目录到Python路径
from .base_api import BaseAPI
from .api_utils import APIClient
from .api_manager import APIManager
import os
import sys

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../" * __file__.count("/"))
)
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
"""
API Package

This package provides a modular API system for the AI automation platform.
"""


# Create a singleton API manager instance
api_manager = APIManager()

__all__ = ["APIManager", "APIClient", "BaseAPI", "api_manager"]