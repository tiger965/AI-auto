"""
测试运行器

提供简单的命令行接口来运行测试，自动处理Python路径问题。
"""

import unittest
import sys
import os


def setup_python_path():
    """设置Python路径以便能找到项目模块"""
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 查找项目根目录（假设是tests目录的父目录）
    if os.path.basename(current_dir) == "test_core":
        # 当前在test_core目录
        project_root = os.path.dirname(os.path.dirname(current_dir))
    else:
        # 当前在tests目录
        project_root = os.path.dirname(current_dir)

    # 将项目根目录添加到Python路径
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"项目根目录已添加到Python路径: {project_root}")


def run_tests(pattern=None, start_dir=None):
    """运行测试"""
    # 如果没有指定起始目录，使用当前目录
    if start_dir is None:
        start_dir = os.path.dirname(os.path.abspath(__file__))

    # 发现测试
    if pattern:
        suite = unittest.defaultTestLoader.discover(
            start_dir, pattern=f"*{pattern}*.py"
        )
    else:
        suite = unittest.defaultTestLoader.discover(start_dir)

    # 运行测试
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # 设置Python路径
    setup_python_path()

    # 简单的命令行参数处理
    args = sys.argv[1:]
    test_name = None
    start_dir = None

    for arg in args:
        if arg.startswith("--dir="):
            start_dir = arg[6:]
        elif not arg.startswith("--"):
            test_name = arg

    print(f"开始运行{'所有' if not test_name else test_name}测试...")
    success = run_tests(test_name, start_dir)

    # 返回适当的退出代码
    sys.exit(0 if success else 1)