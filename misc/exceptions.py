# -*- coding: utf-8 -*-
"""
自定义异常模块

此模块定义了项目中使用的所有自定义异常类，提供详细的错误信息和上下文，
便于准确追踪和诊断问题。每个异常类应包含明确的错误消息、错误代码和其他
相关上下文信息。

版本: 1.0
作者: 窗口8
创建日期: 2025-04-19
"""

import inspect
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

from .constants import ApiErrorCode

# ============================================================================
# 基础异常类
# ============================================================================

class BaseError(Exception):
    """
    所有自定义异常的基类
    
    提供错误代码、详细错误信息和错误上下文的基本结构。
    自动捕获错误发生的文件、行号和函数名等信息。
    
    属性:
        message (str): 错误描述信息
        code (int): 错误代码
        details (dict): 错误的详细信息和上下文
        traceback_info (dict): 追踪信息，包含文件、行号和函数名
    """
    
    def __init__(self, 
                 message: str = "An error occurred", 
                 code: int = 1000, 
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化异常
        
        Args:
            message: 错误描述信息
            code: 错误代码
            details: 错误的详细信息和上下文
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.traceback_info = self._get_traceback_info()
    
    def _get_traceback_info(self) -> Dict[str, Any]:
        """
        获取错误发生的文件、行号和函数名
        
        Returns:
            包含错误位置详细信息的字典
        """
        # 获取调用栈帧
        frame = inspect.currentframe()
        try:
            # 获取出错的栈帧（跳过异常类内部的帧）
            frame = frame.f_back.f_back
            
            # 获取文件名、行号和函数名
            filename = os.path.basename(frame.f_code.co_filename)
            lineno = frame.f_lineno
            function = frame.f_code.co_name
            
            # 获取调用栈摘要
            stack_trace = traceback.extract_stack()[:-2]  # 排除本函数和调用者
            formatted_stack = []
            for frame in stack_trace:
                file = os.path.basename(frame.filename)
                formatted_stack.append(f"{file}:{frame.lineno} in {frame.name}")
            
            return {
                'file': filename,
                'line': lineno,
                'function': function,
                'stack': formatted_stack
            }
        except (AttributeError, IndexError):
            return {'file': 'unknown', 'line': 0, 'function': 'unknown', 'stack': []}
        finally:
            # 清理引用，防止内存泄漏
            del frame
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常信息转换为字典格式
        
        Returns:
            包含异常完整信息的字典
        """
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details,
                'location': self.traceback_info
            }
        }
    
    def __str__(self) -> str:
        """
        返回格式化的错误信息
        
        Returns:
            格式化的错误信息字符串
        """
        location = f"{self.traceback_info['file']}:{self.traceback_info['line']} in {self.traceback_info['function']}"
        return f"[Error {self.code}] {self.message} (at {location})"

# ============================================================================
# 配置相关异常
# ============================================================================

class ConfigError(BaseError):
    """配置错误基类"""
    def __init__(self, message: str = "Configuration error", 
                 code: int = 2000, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ConfigNotFoundError(ConfigError):
    """配置文件不存在"""
    def __init__(self, config_path: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Configuration file not found: {config_path}"
        super().__init__(message, 2001, details or {'config_path': config_path})

class ConfigParseError(ConfigError):
    """配置文件解析错误"""
    def __init__(self, config_path: str, 
                 parse_error: Optional[Exception] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Failed to parse configuration file: {config_path}"
        error_details = {'config_path': config_path}
        if parse_error:
            error_details['parse_error'] = str(parse_error)
        if details:
            error_details.update(details)
        super().__init__(message, 2002, error_details)

class ConfigValidationError(ConfigError):
    """配置验证错误"""
    def __init__(self, invalid_keys: List[str], 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Configuration validation failed for keys: {', '.join(invalid_keys)}"
        super().__init__(message, 2003, details or {'invalid_keys': invalid_keys})

# ============================================================================
# API相关异常
# ============================================================================

class ApiError(BaseError):
    """API错误基类"""
    def __init__(self, 
                 message: str = "API error", 
                 code: int = ApiErrorCode.UNKNOWN_ERROR.value, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ApiAuthenticationError(ApiError):
    """API认证错误"""
    def __init__(self, 
                 message: str = "API authentication failed", 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ApiErrorCode.AUTHENTICATION_FAILED.value, details)

class ApiRateLimitError(ApiError):
    """API速率限制错误"""
    def __init__(self, 
                 limit: int, 
                 reset_time: Optional[int] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"API rate limit exceeded. Limit: {limit}"
            if reset_time:
                message += f", reset in {reset_time} seconds"
        error_details = {'limit': limit}
        if reset_time:
            error_details['reset_time'] = reset_time
        if details:
            error_details.update(details)
        super().__init__(message, ApiErrorCode.RATE_LIMIT_EXCEEDED.value, error_details)

class ApiTimeoutError(ApiError):
    """API超时错误"""
    def __init__(self, 
                 endpoint: str, 
                 timeout: float, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"API request timed out after {timeout}s: {endpoint}"
        error_details = {'endpoint': endpoint, 'timeout': timeout}
        if details:
            error_details.update(details)
        super().__init__(message, ApiErrorCode.TIMEOUT_ERROR.value, error_details)

class ApiResponseError(ApiError):
    """API响应错误"""
    def __init__(self, 
                 endpoint: str, 
                 status_code: int, 
                 response_body: Optional[str] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"API returned error response: {status_code} from {endpoint}"
        error_details = {'endpoint': endpoint, 'status_code': status_code}
        if response_body:
            error_details['response_body'] = response_body
        if details:
            error_details.update(details)
        super().__init__(message, ApiErrorCode.SERVER_ERROR.value, error_details)

# ============================================================================
# 数据处理相关异常
# ============================================================================

class DataError(BaseError):
    """数据处理错误基类"""
    def __init__(self, 
                 message: str = "Data processing error", 
                 code: int = 3000, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class DataValidationError(DataError):
    """数据验证错误"""
    def __init__(self, 
                 field: str, 
                 value: Any, 
                 constraints: Optional[Dict[str, Any]] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Data validation failed for field '{field}'"
        error_details = {'field': field, 'value': str(value)}
        if constraints:
            error_details['constraints'] = constraints
        if details:
            error_details.update(details)
        super().__init__(message, 3001, error_details)

class DataFormatError(DataError):
    """数据格式错误"""
    def __init__(self, 
                 expected_format: str, 
                 received_format: Optional[str] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Invalid data format. Expected: {expected_format}"
            if received_format:
                message += f", received: {received_format}"
        error_details = {'expected_format': expected_format}
        if received_format:
            error_details['received_format'] = received_format
        if details:
            error_details.update(details)
        super().__init__(message, 3002, error_details)

class DataSourceError(DataError):
    """数据源错误"""
    def __init__(self, 
                 source: str, 
                 error_type: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Data source error: {error_type} with source {source}"
        error_details = {'source': source, 'error_type': error_type}
        if details:
            error_details.update(details)
        super().__init__(message, 3003, error_details)

# ============================================================================
# 系统相关异常
# ============================================================================

class SystemError(BaseError):
    """系统错误基类"""
    def __init__(self, 
                 message: str = "System error", 
                 code: int = 4000, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ResourceNotFoundError(SystemError):
    """资源不存在错误"""
    def __init__(self, 
                 resource_type: str, 
                 resource_id: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Resource not found: {resource_type} with id {resource_id}"
        error_details = {'resource_type': resource_type, 'resource_id': resource_id}
        if details:
            error_details.update(details)
        super().__init__(message, 4001, error_details)

class ResourceExhaustedError(SystemError):
    """资源耗尽错误"""
    def __init__(self, 
                 resource_type: str, 
                 limit: Union[int, str], 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Resource exhausted: {resource_type}, limit: {limit}"
        error_details = {'resource_type': resource_type, 'limit': limit}
        if details:
            error_details.update(details)
        super().__init__(message, 4002, error_details)

class PermissionDeniedError(SystemError):
    """权限拒绝错误"""
    def __init__(self, 
                 operation: str, 
                 resource: str, 
                 required_permission: Optional[str] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Permission denied for operation '{operation}' on resource '{resource}'"
            if required_permission:
                message += f", required permission: {required_permission}"
        error_details = {'operation': operation, 'resource': resource}
        if required_permission:
            error_details['required_permission'] = required_permission
        if details:
            error_details.update(details)
        super().__init__(message, 4003, error_details)

class SystemConfigurationError(SystemError):
    """系统配置错误"""
    def __init__(self, 
                 component: str, 
                 issue: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"System configuration error in {component}: {issue}"
        error_details = {'component': component, 'issue': issue}
        if details:
            error_details.update(details)
        super().__init__(message, 4004, error_details)

# ============================================================================
# 模块特定异常
# ============================================================================

class ModuleError(BaseError):
    """模块错误基类"""
    def __init__(self, 
                 module_name: str, 
                 message: str = "Module error", 
                 code: int = 5000, 
                 details: Optional[Dict[str, Any]] = None):
        error_details = {'module': module_name}
        if details:
            error_details.update(details)
        super().__init__(message, code, error_details)

class ModuleInitializationError(ModuleError):
    """模块初始化错误"""
    def __init__(self, 
                 module_name: str, 
                 reason: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Failed to initialize module '{module_name}': {reason}"
        error_details = {'reason': reason}
        if details:
            error_details.update(details)
        super().__init__(module_name, message, 5001, error_details)

class ModuleDependencyError(ModuleError):
    """模块依赖错误"""
    def __init__(self, 
                 module_name: str, 
                 dependency: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Module '{module_name}' has unsatisfied dependency: {dependency}"
        error_details = {'dependency': dependency}
        if details:
            error_details.update(details)
        super().__init__(module_name, message, 5002, error_details)

class ModuleOperationError(ModuleError):
    """模块操作错误"""
    def __init__(self, 
                 module_name: str, 
                 operation: str, 
                 reason: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Module '{module_name}' operation '{operation}' failed: {reason}"
        error_details = {'operation': operation, 'reason': reason}
        if details:
            error_details.update(details)
        super().__init__(module_name, message, 5003, error_details)

# ============================================================================
# 工作流相关异常
# ============================================================================

class WorkflowError(BaseError):
    """工作流错误基类"""
    def __init__(self, 
                 workflow_id: str, 
                 message: str = "Workflow error", 
                 code: int = 6000, 
                 details: Optional[Dict[str, Any]] = None):
        error_details = {'workflow_id': workflow_id}
        if details:
            error_details.update(details)
        super().__init__(message, code, error_details)

class WorkflowDefinitionError(WorkflowError):
    """工作流定义错误"""
    def __init__(self, 
                 workflow_id: str, 
                 issue: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Workflow definition error for workflow '{workflow_id}': {issue}"
        error_details = {'issue': issue}
        if details:
            error_details.update(details)
        super().__init__(workflow_id, message, 6001, error_details)

class WorkflowExecutionError(WorkflowError):
    """工作流执行错误"""
    def __init__(self, 
                 workflow_id: str, 
                 step_id: str, 
                 error: Optional[Exception] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Workflow execution error in workflow '{workflow_id}' at step '{step_id}'"
            if error:
                message += f": {str(error)}"
        error_details = {'step_id': step_id}
        if error:
            error_details['error'] = str(error)
            error_details['error_type'] = type(error).__name__
        if details:
            error_details.update(details)
        super().__init__(workflow_id, message, 6002, error_details)

class WorkflowTimeoutError(WorkflowError):
    """工作流超时错误"""
    def __init__(self, 
                 workflow_id: str, 
                 timeout: float, 
                 current_step: Optional[str] = None, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Workflow '{workflow_id}' timed out after {timeout}s"
            if current_step:
                message += f" at step '{current_step}'"
        error_details = {'timeout': timeout}
        if current_step:
            error_details['current_step'] = current_step
        if details:
            error_details.update(details)
        super().__init__(workflow_id, message, 6003, error_details)

# ============================================================================
# 测试相关异常
# ============================================================================

class TestError(BaseError):
    """测试错误基类"""
    def __init__(self, 
                 test_id: str, 
                 message: str = "Test error", 
                 code: int = 7000, 
                 details: Optional[Dict[str, Any]] = None):
        error_details = {'test_id': test_id}
        if details:
            error_details.update(details)
        super().__init__(message, code, error_details)

class TestSetupError(TestError):
    """测试设置错误"""
    def __init__(self, 
                 test_id: str, 
                 setup_step: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Test setup error for test '{test_id}' at step '{setup_step}'"
        error_details = {'setup_step': setup_step}
        if details:
            error_details.update(details)
        super().__init__(test_id, message, 7001, error_details)

class TestExecutionError(TestError):
    """测试执行错误"""
    def __init__(self, 
                 test_id: str, 
                 execution_step: str, 
                 expected: Any, 
                 actual: Any, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Test execution error for test '{test_id}' at step '{execution_step}'"
            message += f"\nExpected: {expected}\nActual: {actual}"
        error_details = {
            'execution_step': execution_step,
            'expected': str(expected),
            'actual': str(actual)
        }
        if details:
            error_details.update(details)
        super().__init__(test_id, message, 7002, error_details)

class TestCleanupError(TestError):
    """测试清理错误"""
    def __init__(self, 
                 test_id: str, 
                 cleanup_step: str, 
                 message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"Test cleanup error for test '{test_id}' at step '{cleanup_step}'"
        error_details = {'cleanup_step': cleanup_step}
        if details:
            error_details.update(details)
        super().__init__(test_id, message, 7003, error_details)

# ============================================================================
# 异常处理函数
# ============================================================================

def format_exception(exc: Exception) -> Dict[str, Any]:
    """
    格式化异常信息为统一字典格式
    
    Args:
        exc: 异常对象
    
    Returns:
        格式化后的异常信息字典
    """
    if isinstance(exc, BaseError):
        return exc.to_dict()
    
    # 对于非自定义异常，提取基本信息
    tb = traceback.extract_tb(sys.exc_info()[2])
    if tb:
        last_frame = tb[-1]
        location = {
            'file': os.path.basename(last_frame.filename),
            'line': last_frame.lineno,
            'function': last_frame.name
        }
    else:
        location = {'file': 'unknown', 'line': 0, 'function': 'unknown'}
    
    return {
        'error': {
            'code': 9999,  # 非自定义异常的通用代码
            'message': str(exc),
            'type': type(exc).__name__,
            'location': location
        }
    }

def handle_exception(exc: Exception, reraise: bool = False) -> Dict[str, Any]:
    """
    统一异常处理函数
    
    Args:
        exc: 捕获的异常
        reraise: 是否重新抛出异常
    
    Returns:
        格式化后的异常信息
    
    Raises:
        异常将被重新抛出，如果reraise为True
    """
    error_info = format_exception(exc)
    
    # 输出错误信息到标准错误
    error_message = f"[{error_info['error']['code']}] {error_info['error']['message']}"
    location = error_info['error']['location']
    error_message += f" (at {location['file']}:{location['line']} in {location['function']})"
    print(error_message, file=sys.stderr)
    
    # 如果需要，重新抛出异常
    if reraise:
        raise exc
    
    return error_info

# ============================================================================
# 导出所有异常类
# ============================================================================

__all__ = [
    # 基础异常
    'BaseError',
    
    # 配置相关异常
    'ConfigError', 'ConfigNotFoundError', 'ConfigParseError', 'ConfigValidationError',
    
    # API相关异常
    'ApiError', 'ApiAuthenticationError', 'ApiRateLimitError', 
    'ApiTimeoutError', 'ApiResponseError',
    
    # 数据处理相关异常
    'DataError', 'DataValidationError', 'DataFormatError', 'DataSourceError',
    
    # 系统相关异常
    'SystemError', 'ResourceNotFoundError', 'ResourceExhaustedError',
    'PermissionDeniedError', 'SystemConfigurationError',
    
    # 模块特定异常
    'ModuleError', 'ModuleInitializationError', 'ModuleDependencyError', 'ModuleOperationError',
    
    # 工作流相关异常
    'WorkflowError', 'WorkflowDefinitionError', 'WorkflowExecutionError', 'WorkflowTimeoutError',
    
    # 测试相关异常
    'TestError', 'TestSetupError', 'TestExecutionError', 'TestCleanupError',
    
    # 异常处理函数
    'format_exception', 'handle_exception',
]