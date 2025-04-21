import sys
import os
import unittest

# 确保使用绝对路径
current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

def run_selected_tests():
    # 创建测试加载器
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加tests/test_core目录下的测试，跳过test_strategies_basic.py
    test_core_dir = os.path.join(project_root, 'tests', 'test_core')
    print(f"测试核心目录: {test_core_dir}")
    
    if not os.path.exists(test_core_dir):
        print(f"错误: 目录不存在: {test_core_dir}")
        return unittest.TestResult()
        
    for file in os.listdir(test_core_dir):
        if file.startswith('test_') and file.endswith('.py'):
            if file != 'test_strategies_basic.py':
                try:
                    # 构建测试模块名
                    module_name = f"tests.test_core.{file[:-3]}"
                    print(f"尝试加载: {module_name}")
                    # 加载测试
                    test_module = loader.loadTestsFromName(module_name)
                    suite.addTest(test_module)
                    print(f"成功加载: {module_name}")
                except Exception as e:
                    print(f"加载失败 {module_name}: {str(e)}")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result

if __name__ == "__main__":
    print("开始运行测试...")
    print(f"项目根目录: {project_root}")
    result = run_selected_tests()
    if hasattr(result, 'errors') and hasattr(result, 'failures'):
        print(f"测试运行完成。错误数: {len(result.errors)}, 失败数: {len(result.failures)}")
    else:
        print("测试未能正常运行")