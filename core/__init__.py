# core/__init__.py
"""核心模块初始化文件"""

from config import config
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)

# 使用绝对导入
try:
    pass
except ImportError:
    pass
# 如果无法导入，定义一个简单的配置对象
    config = {
        "app_name": "AI自动化系统",
        "version": "1.0.0",
        "debug": False
    }

# 定义模块版本
__version__ = "1.0.0"

# 导出的函数或类
__all__ = []