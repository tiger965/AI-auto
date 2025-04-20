# 视觉测试模块初始化文件
# 确保测试发现能正确工作

# 导入测试类，以便在运行测试时能够自动发现
from .test_image_processor import TestImageProcessor
from .test_object_detection import TestObjectDetection

# 导出测试类，方便在需要时直接导入
__all__ = ['TestImageProcessor', 'TestObjectDetection']# 视觉测试初始化文件
