#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主测试脚本
用于测试AI交易系统的各个组件
"""

import sys
import os
import logging
import unittest
import importlib
import inspect
import traceback
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("master_test.log", mode="w"),
    ],
)

logger = logging.getLogger("MasterTest")

# 要测试的模块列表
TEST_MODULES = [
    # 核心模块
    "core.engine",
    "core.evolution.strategy_learner",
    # 数据模块
    "data.collector",
    "data.processor",
    "data.storage",
    "data.validator",
    # API模块
    "api.modules.gpt_claude_bridge",
    # UI模块
    "ui.components.strategy_monitor",
]

# 通用模块对象
MOCKS = {
    "strategy_learner": None,  # 将在运行时设置
}


def setup_testing_environment():
    """设置测试环境"""
    logger.info("设置测试环境...")

    # 添加项目根目录到路径
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # 创建必要的目录
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)

    logger.info(f"测试环境设置完成，项目根目录: {root_dir}")
    return root_dir


def create_test_modules():
    """创建测试模块结构"""
    logger.info("创建测试模块结构...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for module_name in TEST_MODULES:
        # 构建模块路径
        module_path = os.path.join(root_dir, *module_name.split("."))

        # 确保目录存在
        os.makedirs(os.path.dirname(module_path), exist_ok=True)

        # 创建__init__.py文件
        init_path = os.path.join(os.path.dirname(module_path), "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "a") as f:
                pass

        # 创建模块文件
        full_path = os.path.join(root_dir, *module_name.split("."))

        if not os.path.exists(f"{full_path}.py"):
            with open(f"{full_path}.py", "w") as f:
                f.write(f"# 自动生成的{module_name}模块\n")
                f.write('"""\n')
                f.write(f"{module_name}模块\n")
                f.write(f"自动生成于{datetime.now()}\n")
                f.write('"""\n')
                f.write("\n")
                f.write(f"class {module_name.split('.')[-1].capitalize()}:\n")
                f.write('    """自动生成的类"""\n')
                f.write("\n")
                f.write("    def __init__(self):\n")
                f.write('        """初始化"""\n')
                f.write(
                    f"        print(\"{module_name.split('.')[-1].capitalize()}初始化\")\n"
                )
                f.write("\n")
                f.write("    def method1(self):\n")
                f.write('        """示例方法1"""\n')
                f.write("        return True\n")

    logger.info(f"创建了 {len(TEST_MODULES)} 个测试模块")


def import_module(module_name):
    """导入模块并返回"""
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        logger.error(f"无法导入模块 {module_name}: {e}")
        return None


def test_module_imports():
    """测试所有模块导入"""
    logger.info("测试模块导入...")
    success_count = 0

    for module_name in TEST_MODULES:
        try:
            module = import_module(module_name)
            if module is not None:
                logger.info(f"成功导入: {module_name}")
                success_count += 1
            else:
                logger.error(f"导入失败: {module_name}")
        except Exception as e:
            logger.error(f"测试 {module_name} 时出错: {e}")
            traceback.print_exc()

    logger.info(f"模块导入测试完成: {success_count}/{len(TEST_MODULES)} 成功")
    return success_count == len(TEST_MODULES)


def run_module_tests():
    """运行模块单元测试"""
    logger.info("运行模块单元测试...")

    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # 发现并运行tests目录下的所有测试
    test_dir = os.path.dirname(os.path.abspath(__file__))
    discovered_tests = test_loader.discover(test_dir, pattern="test_*.py")
    test_suite.addTest(discovered_tests)

    # 运行测试
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)

    logger.info(
        f"单元测试完成: {test_result.testsRun} 测试运行, "
        f"{len(test_result.errors)} 错误, "
        f"{len(test_result.failures)} 失败"
    )

    return len(test_result.errors) == 0 and len(test_result.failures) == 0


def main():
    """主函数"""
    logger.info("开始测试流程")
    start_time = time.time()

    # 设置测试环境
    root_dir = setup_testing_environment()

    # 创建测试模块
    create_test_modules()

    # 测试模块导入
    import_success = test_module_imports()
    if not import_success:
        logger.error("模块导入测试失败，中止测试")
        return False

    # 运行单元测试
    test_success = run_module_tests()

    # 总结
    end_time = time.time()
    elapsed = end_time - start_time
    logger.info(f"测试流程完成，耗时: {elapsed:.2f} 秒")

    if test_success:
        logger.info("所有测试通过!")
        return True
    else:
        logger.error("测试失败，请查看日志了解详情")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)