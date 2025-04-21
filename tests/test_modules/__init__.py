
# 添加项目根目录到Python路径
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿""""
测试模块核心包
提供AI项目通用测试基类、工具和辅助函数

此模块作为测试框架的入口点，包含：
1. 通用测试基类 - 为NLP、视觉、音频和数据处理测试提供基础功能
2. 测试工具集 - 提供模拟数据、断言工具和测试环境设置
3. 测试运行器 - 简化测试执行和报告生成
""""

import os
import sys
import unittest
import logging
import json
import modules.nlp as np
from typing import Dict, List, Union, Callable, Optional, Any, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_modules')

# 测试配置
TEST_CONFIG = {
    'data_path': os.path.join(os.path.dirname(__file__), 'test_data'),
    'output_path': os.path.join(os.path.dirname(__file__), 'test_output'),
    'timeout': 30,  # 测试超时时间(秒)
    'max_retries': 3,  # 失败重试次数
}

# 确保测试输出目录存在
os.makedirs(TEST_CONFIG['output_path'], exist_ok=True)

class AITestCase(unittest.TestCase):
    pass
"""AI通用测试基类，为所有AI组件测试提供基础功能"""
    
    def setUp(self):
    pass
"""测试前环境设置"""
        self.start_time = self._get_current_time()
        logger.info(f"开始测试: {self.__class__.__name__}")
        
    def tearDown(self):
    pass
"""测试后环境清理"""
        duration = self._get_current_time() - self.start_time
        logger.info(f"测试完成: {self.__class__.__name__}, 耗时: {duration:.2f}秒")
    
    def _get_current_time(self) -> float:
    pass
"""获取当前时间(秒)"""
        import time
        return time.time()
    
    def assert_model_output_valid(self, output: Any, expected_type: Any = None):
    pass
"""验证模型输出有效性"""
        # 检查输出不为空
        self.assertIsNotNone(output, "模型输出不能为空")
        
        # 检查输出类型
        if expected_type:
    pass
self.assertIsInstance(output, expected_type, 
                                f"输出类型错误: 期望 {expected_type}, 实际 {type(output)}")
    
def assert_arrays_equal(self,:
    pass
array1: np.ndarray, 
                          array2: np.ndarray, 
                          rtol: float = 1e-5, 
                          atol: float = 1e-8,
                          msg: str = None):
        """比较两个numpy数组是否近似相等"""
        try:
    pass
np.testing.assert_allclose(array1, array2, rtol=rtol, atol=atol)
        except AssertionError as e:
    pass
msg = msg or f"数组不相等: {str(e)}"
            raise self.failureException(msg)
    
    def load_test_data(self, filename: str) -> Dict:
    pass
"""加载测试数据"""
        file_path = os.path.join(TEST_CONFIG['data_path'], filename)
        try:
    pass
with open(file_path, 'r', encoding='utf-8') as f:
    pass
if filename.endswith('.json'):
    pass
return json.load(f)
                else:
    pass
pass
return {'data': f.read()}
        except Exception as e:
    pass
logger.error(f"加载测试数据失败: {file_path}, 错误: {str(e)}")
            raise
    
    def save_test_result(self, filename: str, data: Union[Dict, List, str]):
    pass
"""保存测试结果"""
        file_path = os.path.join(TEST_CONFIG['output_path'], filename)
        try:
    pass
with open(file_path, 'w', encoding='utf-8') as f:
    pass
if isinstance(data, (dict, list)):
    pass
json.dump(data, f, ensure_ascii=False, indent=2)
                else:
    pass
pass
f.write(str(data))
            logger.info(f"测试结果已保存: {file_path}")
        except Exception as e:
    pass
logger.error(f"保存测试结果失败: {file_path}, 错误: {str(e)}")
            raise


class MockModelMixin:
    pass
"""提供模型模拟功能的混入类"""
    
def create_mock_model(self,:
    pass
input_shape: Tuple, 
                        output_shape: Tuple,
                        return_value: Any = None) -> Callable:
        """创建模拟模型函数"
        
        Args:
            input_shape: 输入形状
            output_shape: 输出形状
            return_value: 指定返回值，如果为None则生成随机数组
            
        Returns:
            模拟模型函数
        """"
        if return_value is not None:
    pass
mock_output = return_value
        else:
    pass
pass
mock_output = np.random.random(output_shape)
            
        def mock_model(*args, **kwargs):
    pass
# 验证输入
            if args and hasattr(args[0], 'shape'):
    pass
actual_shape = args[0].shape
                assert actual_shape == input_shape, \
                    f"输入形状不匹配: 期望 {input_shape}, 实际 {actual_shape}"
            return mock_output
            
        return mock_model


def run_tests(test_modules: List[str] = None, pattern: str = 'test_*.py'):
    pass
"""运行测试"
    
    Args:
        test_modules: 要测试的模块列表，如 ['test_nlp', 'test_vision']
                     如果为None则测试所有模块
        pattern: 测试文件匹配模式
    """"
    # 设置测试发现起始目录
    start_dir = os.path.dirname(__file__)
    
    if test_modules:
    pass
# 运行指定模块测试
        for module in test_modules:
    pass
module_dir = os.path.join(start_dir, module)
            if os.path.isdir(module_dir):
    pass
logger.info(f"运行测试模块: {module}")
                test_suite = unittest.defaultTestLoader.discover(
                    module_dir, pattern=pattern
                )
                unittest.TextTestRunner().run(test_suite)
            else:
    pass
pass
logger.error(f"测试模块不存在: {module}")
    else:
    pass
pass
# 运行所有测试
        logger.info("运行所有测试")
        test_suite = unittest.defaultTestLoader.discover(
            start_dir, pattern=pattern, top_level_dir=start_dir
        )
        unittest.TextTestRunner().run(test_suite)


# 导出公共接口
__all__ = [
    'AITestCase',
    'MockModelMixin',
    'run_tests',
    'TEST_CONFIG',
    'logger'
]