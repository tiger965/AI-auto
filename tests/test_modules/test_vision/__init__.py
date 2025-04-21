
# 添加项目根目录到Python路径
from .test_object_detection import TestObjectDetection
from .test_image_processor import TestImageProcessor
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿  # 视觉测试模块初始化文件
# 确保测试发现能正确工作

# 导入测试类，以便在运行测试时能够自动发现

# 导出测试类，方便在需要时直接导入
__all__ = ['TestImageProcessor', 'TestObjectDetection']  # 视觉测试初始化文件