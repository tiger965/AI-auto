
# 添加项目根目录到Python路径
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿""""
测试数据处理模块 - 测试包初始化文件
包含数据加载和转换功能的测试
""""

# 确保测试包可以正确导入相关模块
import os
import sys

# 添加项目根目录到搜索路径，以便测试可以导入被测试的模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))