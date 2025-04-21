# 添加项目根目录到Python路径
from .reorganize_project_py import *
from .module_extractor_py import *
from .module_extractor import *
from .init import *
from .improved_reorganize_tool import *
import os
import sys

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../" * __file__.count("/"))
)
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
"""
misc 模块
"""