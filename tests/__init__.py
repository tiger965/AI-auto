"""
全局测试框架初始化文件
-------------------
提供测试框架的基础设施、异常处理和错误追踪机制。
该框架旨在提供详细的错误定位和上下文信息，确保测试覆盖所有关键路径。
"""

import os
import sys
import inspect
import logging
import traceback
import time
import functools
import unittest
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union, Tuple

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"test_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TestFramework")

# 测试结果和性能数据存储
TEST_RESULTS = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "performance": {}
}

# 错误追踪类
class ErrorTracker:
    """
    错误追踪和定位类
    提供详细的错误上下文信息，包括源文件、行号、函数名、错误类型等
    """
    
    @staticmethod
    def get_error_context(exc_info=None) -> Dict[str, Any]:
        """
        获取当前异常的详细上下文信息
        
        Returns:
            Dict: 包含错误详细信息的字典
        """
        if exc_info is None:
            exc_info = sys.exc_info()
            
        exc_type, exc_value, exc_traceback = exc_info
        
        # 获取最详细的错误位置信息
        tb_frame = traceback.extract_tb(exc_traceback)
        
        # 查找实际测试代码中的错误位置（跳过框架代码）
        source_file = None
        line_number = None
        function_name = None
        
        for frame in reversed(tb_frame):
            if 'tests/' in frame.filename and '_init_.py' not in frame.filename:
                source_file = frame.filename
                line_number = frame.lineno
                function_name = frame.name
                break
        
        # 如果没找到测试文件中的错误，使用最后一个帧
        if source_file is None and tb_frame:
            last_frame = tb_frame[-1]
            source_file = last_frame.filename
            line_number = last_frame.lineno
            function_name = last_frame.name
        
        # 获取错误发生时的局部变量
        local_vars = {}
        if exc_traceback:
            try:
                frame = exc_traceback.tb_frame
                while frame:
                    # 只收集基本类型的变量，避免大对象
                    for key, value in frame.f_locals.items():
                        if isinstance(value, (str, int, float, bool)) and not key.startswith('__'):
                            local_vars[key] = value
                    frame = frame.f_back
            except Exception:
                # 捕获获取局部变量时的任何错误
                pass
                
        return {
            "error_type": exc_type.__name__ if exc_type else "Unknown",
            "error_message": str(exc_value),
            "source_file": source_file,
            "line_number": line_number,
            "function_name": function_name,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exception(*exc_info) if exc_info[0] else [],
            "local_variables": local_vars
        }
        
    @staticmethod
    def log_error(error_context: Dict[str, Any]) -> None:
        """
        记录错误信息到日志
        
        Args:
            error_context: 由get_error_context()返回的错误上下文信息
        """
        # 构建错误消息
        error_message = [
            "\n" + "="*80,
            f"ERROR DETECTED: {error_context['error_type']}: {error_context['error_message']}",
            f"SOURCE: {error_context['source_file']}:{error_context['line_number']} in {error_context['function_name']}()",
            f"TIMESTAMP: {error_context['timestamp']}",
            "TRACEBACK:",
        ]
        
        # 添加堆栈信息
        error_message.extend([f"  {line}" for line in error_context['traceback']])
        
        # 添加局部变量信息
        if error_context['local_variables']:
            error_message.append("LOCAL VARIABLES:")
            for key, value in error_context['local_variables'].items():
                error_message.append(f"  {key} = {value}")
                
        error_message.append("="*80)
        
        # 记录到日志系统
        logger.error("\n".join(error_message))
        
    @classmethod
    def track(cls, func):
        """
        装饰器：用于追踪函数执行中的错误
        
        Args:
            func: 被装饰的函数
            
        Returns:
            包装后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = cls.get_error_context()
                cls.log_error(error_context)
                # 重新抛出异常，保持原始堆栈
                raise
        return wrapper


# 性能测试装饰器
def benchmark(label: Optional[str] = None):
    """
    性能基准测试装饰器
    测量函数执行时间并记录结果
    
    Args:
        label: 性能测试标签，默认为函数名
    
    Returns:
        包装后的函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal label
            if label is None:
                label = func.__name__
                
            # 开始计时
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            # 计算执行时间
            execution_time = end_time - start_time
            
            # 记录性能数据
            if label not in TEST_RESULTS["performance"]:
                TEST_RESULTS["performance"][label] = []
            
            TEST_RESULTS["performance"][label].append(execution_time)
            
            # 记录到日志
            logger.info(f"性能测试 - {label}: {execution_time:.6f} 秒")
            
            return result
        return wrapper
    return decorator


# 测试用例基类
class TestBase(unittest.TestCase):
    """
    测试用例基类
    提供共用的测试功能和断言方法
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类开始前的设置"""
        logger.info(f"开始测试类: {cls.__name__}")
        cls.start_time = time.time()
    
    @classmethod
    def tearDownClass(cls):
        """测试类结束后的清理"""
        execution_time = time.time() - cls.start_time
        logger.info(f"完成测试类: {cls.__name__}, 用时: {execution_time:.6f}秒")
    
    def setUp(self):
        """每个测试用例开始前的设置"""
        self.test_start_time = time.time()
        self.test_name = self._testMethodName
        logger.info(f"开始测试: {self.test_name}")
        TEST_RESULTS["total"] += 1
    
    def tearDown(self):
        """每个测试用例结束后的清理"""
        execution_time = time.time() - self.test_start_time
        status = "未知"
        
        # 获取测试结果
        if hasattr(self, '_outcome'):  # Python 3.4+
            result = self._outcome.result
            if len(result.errors) > 0 and result.errors[-1][0]._testMethodName == self.test_name:
                status = "错误"
                TEST_RESULTS["errors"] += 1
            elif len(result.failures) > 0 and result.failures[-1][0]._testMethodName == self.test_name:
                status = "失败"
                TEST_RESULTS["failed"] += 1
            elif len(result.skipped) > 0 and result.skipped[-1][0]._testMethodName == self.test_name:
                status = "跳过"
                TEST_RESULTS["skipped"] += 1
            else:
                status = "通过"
                TEST_RESULTS["passed"] += 1
        
        logger.info(f"完成测试: {self.test_name}, 状态: {status}, 用时: {execution_time:.6f}秒")

    def assertPerformance(self, func, max_time_seconds, *args, **kwargs):
        """
        性能断言：确保函数在指定时间内完成
        
        Args:
            func: 要测试的函数
            max_time_seconds: 最大允许执行时间（秒）
            args, kwargs: 传递给被测试函数的参数
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        self.assertLessEqual(
            execution_time, 
            max_time_seconds, 
            f"性能测试失败: {func.__name__} 用时 {execution_time:.6f}秒, 超过了最大允许时间 {max_time_seconds}秒"
        )
        
        return result, execution_time


# 模拟器工具类
class MockUtils:
    """
    提供模拟对象和环境的工具类
    用于创建测试固件和模拟外部依赖
    """
    
    @staticmethod
    def create_mock_response(status_code=200, json_data=None, text="", headers=None, cookies=None):
        """
        创建模拟的HTTP响应对象
        
        Args:
            status_code: HTTP状态码
            json_data: JSON响应数据
            text: 文本响应数据
            headers: 响应头
            cookies: 响应cookies
            
        Returns:
            模拟的响应对象
        """
        class MockResponse:
            def __init__(self, json_data, text, status_code, headers, cookies):
                self.json_data = json_data
                self.text = text
                self.status_code = status_code
                self.headers = headers or {}
                self.cookies = cookies or {}
                
            def json(self):
                return self.json_data
                
            def raise_for_status(self):
                if self.status_code >= 400:
                    raise Exception(f"HTTP Error: {self.status_code}")
        
        return MockResponse(json_data, text, status_code, headers, cookies)


# 测试运行器
def run_tests(test_modules=None, pattern=None, failfast=False):
    """
    运行测试并收集结果
    
    Args:
        test_modules: 要测试的模块列表，默认为None（测试所有）
        pattern: 测试文件匹配模式，默认为"test_*.py"
        failfast: 是否在第一个测试失败后停止，默认为False
        
    Returns:
        测试结果摘要
    """
    try:
        # 重置测试结果
        global TEST_RESULTS
        TEST_RESULTS = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "performance": {}
        }
        
        start_time = time.time()
        logger.info(f"开始测试运行: {datetime.now().isoformat()}")
        
        # 创建测试套件
        if test_modules:
            suite = unittest.TestSuite()
            for module in test_modules:
                suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))
        else:
            # 自动发现并加载测试
            current_dir = os.path.dirname(os.path.abspath(__file__))
            pattern = pattern or "test_*.py"
            suite = unittest.defaultTestLoader.discover(current_dir, pattern=pattern)
        
        # 运行测试
        runner = unittest.TextTestRunner(failfast=failfast, verbosity=2)
        result = runner.run(suite)
        
        # 更新测试结果（以防某些用例没有通过setUp/tearDown）
        TEST_RESULTS["passed"] = len(result.successes) if hasattr(result, 'successes') else result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        TEST_RESULTS["failed"] = len(result.failures)
        TEST_RESULTS["errors"] = len(result.errors)
        TEST_RESULTS["skipped"] = len(result.skipped)
        TEST_RESULTS["total"] = result.testsRun
        
        # 计算执行时间
        execution_time = time.time() - start_time
        TEST_RESULTS["execution_time"] = execution_time
        
        # 记录摘要
        summary = [
            "\n" + "="*80,
            f"测试运行结束: {datetime.now().isoformat()}",
            f"总用时: {execution_time:.6f}秒",
            f"总测试数: {TEST_RESULTS['total']}",
            f"通过: {TEST_RESULTS['passed']}",
            f"失败: {TEST_RESULTS['failed']}",
            f"错误: {TEST_RESULTS['errors']}",
            f"跳过: {TEST_RESULTS['skipped']}",
        ]
        
        # 添加性能测试结果
        if TEST_RESULTS["performance"]:
            summary.append("\n性能测试结果:")
            for label, times in TEST_RESULTS["performance"].items():
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                summary.append(f"  {label}:")
                summary.append(f"    运行次数: {len(times)}")
                summary.append(f"    平均时间: {avg_time:.6f}秒")
                summary.append(f"    最小时间: {min_time:.6f}秒")
                summary.append(f"    最大时间: {max_time:.6f}秒")
        
        summary.append("="*80)
        summary_text = "\n".join(summary)
        logger.info(summary_text)
        print(summary_text)
        
        return TEST_RESULTS
        
    except Exception:
        # 捕获并记录测试运行器本身的错误
        error_context = ErrorTracker.get_error_context()
        ErrorTracker.log_error(error_context)
        raise


# 测试数据生成器
class TestDataGenerator:
    """
    测试数据生成工具
    提供创建各种测试数据的方法
    """
    
    @staticmethod
    def generate_api_request_data(endpoint, method="GET", params=None, headers=None, body=None):
        """
        生成API请求测试数据
        
        Args:
            endpoint: API端点
            method: HTTP方法
            params: URL参数
            headers: 请求头
            body: 请求体
            
        Returns:
            请求数据字典
        """
        request_data = {
            "endpoint": endpoint,
            "method": method,
            "params": params or {},
            "headers": headers or {"Content-Type": "application/json"},
            "body": body or {}
        }
        return request_data# 测试套件初始化文件
