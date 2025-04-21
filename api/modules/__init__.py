# 添加项目根目录到Python路径
import os
import sys

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../" * __file__.count("/"))
)
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
"""
API 模块包

包含所有可用的API模块。
"""

# 此文件保持为空
# API管理器将自动发现和加载此目录中的模块