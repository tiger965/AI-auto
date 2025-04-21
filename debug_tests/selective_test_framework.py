#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI交易系统选择性测试框架 (已修正路径)
-------------------------
此脚本提供了一个选择性的测试框架，只测试尚未验证的模块。
根据实际项目结构修正了模块导入路径。
"""

import os
import sys
import time
import logging
import unittest
import importlib
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # debug_tests的上一级是项目根目录
sys.path.append(project_root)

# 打印当前Python路径以便调试
print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

# 配置日志
log_dir = os.path.join(current_dir, "test_logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(
        log_file, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("AI_Trading_Test")

# 已测试通过的模块列表
TESTED_MODULES = [
    "api.modules.gpt_claude_bridge",
    "core.evolution.strategy_learner",
    "ui.components.strategy_monitor",
]

# 待测试模块列表 - 已根据实际项目结构修正
PENDING_TEST_MODULES = {
    "数据模块": ["data.collector", "data.processor", "data.storage", "data.validator"],
    "AI分析引擎": ["modules.audio", "modules.nlp", "modules.video", "modules.vision"],
    "交易执行": [
        "trading.connectors",
        "trading.api",
        "trading.strategy",
        "trading.execution",
        "trading.backtest",
    ],
    "UI界面": ["ui.dashboard", "ui.charts", "ui.controls", "ui.reports"],
}


class AITradingTestCase(unittest.TestCase):
    """AI交易系统基础测试类"""

    @classmethod
    def setUpClass(cls):
        logger.info(f"开始测试: {cls.__name__}")
        cls.start_time = time.time()

    @classmethod
    def tearDownClass(cls):
        elapsed = time.time() - cls.start_time
        logger.info(f"完成测试: {cls.__name__}, 耗时: {elapsed:.2f}秒")

    def setUp(self):
        self.start_time = time.time()
        logger.info(f"运行测试: {self._testMethodName}")

    def tearDown(self):
        elapsed = time.time() - self.start_time
        logger.info(f"测试完成: {self._testMethodName}, 耗时: {elapsed:.2f}秒")


class ModuleTestRunner:
    """模块测试运行器"""

    def __init__(self):
        self.results = {}
        self.skipped_modules = []

    def check_module_exists(self, module_path):
        """检查模块是否存在"""
        try:
            importlib.import_module(module_path)
            return True
        except ImportError as e:
            logger.warning(f"模块 {module_path} 不存在: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"检查模块 {module_path} 时出错: {str(e)}")
            return False

    def test_module(self, module_path):
        """测试单个模块"""
        if module_path in TESTED_MODULES:
            logger.info(f"跳过已测试模块: {module_path}")
            self.skipped_modules.append(module_path)
            return None

        if not self.check_module_exists(module_path):
            logger.warning(f"跳过不存在的模块: {module_path}")
            return None

        logger.info(f"开始测试模块: {module_path}")
        test_suite = unittest.TestSuite()

        # 动态创建测试类
        class_name = "".join(x.capitalize() for x in module_path.split("."))
        TestClass = type(f"{class_name}TestCase", (AITradingTestCase,), {})

        # 添加初始化测试方法
        def test_module_init(self):
            """测试模块初始化"""
            try:
                module = importlib.import_module(module_path)
                self.assertIsNotNone(module, f"模块 {module_path} 导入失败")
                logger.info(f"模块 {module_path} 初始化成功")

                # 检测并测试模块中的主要类
                main_class_found = False
                for attr_name in dir(module):
                    if attr_name.startswith("_"):
                        continue
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):
                        try:
                            instance = attr()
                            logger.info(f"成功实例化类: {attr_name}")
                            main_class_found = True
                            # 测试基本方法
                            for method_name in dir(instance):
                                if method_name.startswith("_") or not callable(
                                    getattr(instance, method_name)
                                ):
                                    continue
                                try:
                                    method = getattr(instance, method_name)
                                    # 尝试无参数调用
                                    if (
                                        hasattr(method, "__code__")
                                        and method.__code__.co_argcount == 1
                                    ):  # 只有self参数
                                        logger.info(f"尝试调用方法: {method_name}")
                                        method()
                                        logger.info(f"方法调用成功: {method_name}")
                                except Exception as e:
                                    logger.warning(
                                        f"方法 {method_name} 调用失败: {str(e)}"
                                    )
                        except Exception as e:
                            logger.warning(f"类 {attr_name} 实例化失败: {str(e)}")

                if not main_class_found:
                    logger.warning(f"模块 {module_path} 中未找到可实例化的类")
            except Exception as e:
                self.fail(f"模块 {module_path} 测试失败: {str(e)}")

        setattr(TestClass, "test_module_init", test_module_init)

        # 添加测试到套件
        test = TestClass("test_module_init")
        test_suite.addTest(test)

        # 运行测试
        test_result = unittest.TextTestRunner().run(test_suite)
        self.results[module_path] = {
            "success": test_result.wasSuccessful(),
            "errors": len(test_result.errors),
            "failures": len(test_result.failures),
        }

        return test_result

    def run_tests(self, parallel=False):  # 默认关闭并行测试以简化调试
        """运行所有测试"""
        all_modules = []
        for category, modules in PENDING_TEST_MODULES.items():
            logger.info(f"准备测试类别: {category}")
            all_modules.extend(modules)

        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(self.test_module, all_modules)
        else:
            for module in all_modules:
                self.test_module(module)

        self.report_results()

    def report_results(self):
        """报告测试结果"""
        logger.info("=" * 50)
        logger.info("测试结果汇总")
        logger.info("=" * 50)

        success_count = 0
        failure_count = 0

        for module_path, result in self.results.items():
            status = "通过" if result["success"] else "失败"
            logger.info(f"模块 {module_path}: {status}")
            if result["success"]:
                success_count += 1
            else:
                failure_count += 1

        logger.info("-" * 50)
        logger.info(f"已测试模块: {len(self.results)}")
        logger.info(f"测试通过: {success_count}")
        logger.info(f"测试失败: {failure_count}")
        logger.info(f"跳过模块: {len(self.skipped_modules)}")
        logger.info("=" * 50)


# 自定义数据模块测试
class DataCollectorTest(AITradingTestCase):
    """数据采集模块测试"""

    def test_collector_init(self):
        """测试数据采集器初始化"""
        try:
            from data.collector import DataCollector

            collector = DataCollector()
            self.assertIsNotNone(collector)
            logger.info("DataCollector初始化成功")
        except ImportError:
            self.skipTest("数据采集模块不存在")
        except Exception as e:
            self.fail(f"初始化失败: {str(e)}")

    def test_data_fetch(self):
        """测试数据获取功能"""
        try:
            from data.collector import DataCollector

            collector = DataCollector()
            # 测试基本获取功能
            data = collector.fetch("test_market", "test_symbol")
            self.assertIsNotNone(data)
            self.assertTrue(len(data) > 0)
            logger.info(f"成功获取数据: {len(data)}条记录")
        except ImportError:
            self.skipTest("数据采集模块不存在")
        except AttributeError:
            self.skipTest("fetch方法不存在")
        except Exception as e:
            self.fail(f"数据获取失败: {str(e)}")


# 添加测试单个文件功能
def test_single_file(file_path):
    """测试单个Python文件"""
    logger.info(f"开始测试文件: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    try:
        # 运行文件
        with open(file_path, "r", encoding="utf-8") as f:
            code = compile(f.read(), file_path, "exec")
            exec(code, {})
        logger.info(f"文件测试成功: {file_path}")
        return True
    except Exception as e:
        logger.error(f"文件测试失败: {file_path}, 错误: {str(e)}")
        traceback.print_exc()
        return False


# 主函数
def main():
    """主函数"""
    print("=" * 70)
    print("AI交易系统选择性测试框架")
    print("=" * 70)
    print("1. 测试数据模块")
    print("2. 测试AI分析引擎")
    print("3. 测试交易执行模块")
    print("4. 测试UI界面模块")
    print("5. 测试所有未验证模块")
    print("6. 测试单个Python文件")
    print("7. 导入测试(调试导入问题)")
    print("=" * 70)

    choice = input("请选择测试选项 (1-7): ")

    runner = ModuleTestRunner()

    if choice == "1":
        for module in PENDING_TEST_MODULES["数据模块"]:
            runner.test_module(module)
    elif choice == "2":
        for module in PENDING_TEST_MODULES["AI分析引擎"]:
            runner.test_module(module)
    elif choice == "3":
        for module in PENDING_TEST_MODULES["交易执行"]:
            runner.test_module(module)
    elif choice == "4":
        for module in PENDING_TEST_MODULES["UI界面"]:
            runner.test_module(module)
    elif choice == "5":
        runner.run_tests()
    elif choice == "6":
        file_path = input("请输入要测试的Python文件路径: ")
        test_single_file(file_path)
    elif choice == "7":
        # 尝试导入各种模块用于调试
        print("\n测试模块导入...")
        test_modules = [
            "data",
            "data.collector",
            "data.processor",
            "data.storage",
            "data.validator",
            "modules",
            "modules.audio",
            "modules.nlp",
            "modules.video",
            "modules.vision",
            "trading",
            "trading.connectors",
            "trading.api",
            "trading.strategy",
            "ui",
            "ui.dashboard",
            "ui.charts",
        ]

        for module in test_modules:
            try:
                print(f"尝试导入 {module}...")
                imported_module = importlib.import_module(module)
                print(f"成功导入 {module}")
                # 打印模块路径
                if hasattr(imported_module, "__file__"):
                    print(f"  模块路径: {imported_module.__file__}")
                # 打印模块内容
                print(f"  模块内容: {dir(imported_module)}")
            except ImportError as e:
                print(f"无法导入 {module}: {str(e)}")
            except Exception as e:
                print(f"导入 {module} 时出错: {str(e)}")
            print("-" * 40)
    else:
        print("无效选择")


if __name__ == "__main__":
    main()