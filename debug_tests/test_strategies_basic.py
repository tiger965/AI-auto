import sys
import os
import unittest

# 确保项目根目录在Python路径中
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 手动加载特定的测试文件（跳过test_strategies_basic.py）
test_loader = unittest.TestLoader()
test_suite = unittest.TestSuite()

# 加载test_core目录下的测试
test_core_path = os.path.join(project_root, 'tests', 'test_core')
if os.path.exists(test_core_path):
    for file in os.listdir(test_core_path):
        if file.startswith('test_') and file.endswith('.py') and file != 'test_strategies_basic.py':
            module_name = f'tests.test_core.{file[:-3]}'
            try:
                tests = test_loader.loadTestsFromName(module_name)
                test_suite.addTest(tests)
                print(f"已加载测试模块: {module_name}")
            except Exception as e:
                print(f"加载 {module_name} 失败: {e}")

# 运行测试
test_runner = unittest.TextTestRunner(verbosity=2)
test_runner.run(test_suite)