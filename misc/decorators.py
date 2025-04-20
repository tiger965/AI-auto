# -*- coding: utf-8 -*-
"""
装饰器模块

此模块提供了一系列实用的装饰器，用于增强函数和方法的功能，
如性能监控、缓存、重试机制、权限验证等，无需修改原始代码。

版本: 1.0
作者: 窗口8
创建日期: 2025-04-19
"""

import functools
import inspect
import logging
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from .constants import LogLevel
from .exceptions import (
    ApiRateLimitError, ApiTimeoutError, BaseError, 
    PermissionDeniedError, ResourceExhaustedError
)

# 设置日志器
logger = logging.getLogger(__name__)

# 类型变量定义
F = TypeVar('F', bound=Callable[..., Any])

# ============================================================================
# 性能监控装饰器
# ============================================================================

def timer(func: F) -> F:
    """
    计时装饰器，记录函数执行时间
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @timer
        def process_data(data):
            # 处理数据...
            return result
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 获取调用者信息
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_code.co_filename
            caller_line = frame.f_back.f_lineno
            caller_info = f"called from {caller_file}:{caller_line}"
        else:
            caller_info = "unknown caller"
        
        logger.info(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds ({caller_info})")
        
        # 清理引用，防止内存泄漏
        del frame
        
        return result
    
    return cast(F, wrapper)

def performance_monitor(threshold: float = 1.0, 
                        log_level: int = LogLevel.WARNING.value) -> Callable[[F], F]:
    """
    性能监控装饰器，当函数执行时间超过阈值时记录警告
    
    Args:
        threshold: 执行时间阈值（秒）
        log_level: 日志级别
    
    Returns:
        装饰器函数
    
    示例:
        @performance_monitor(threshold=0.5)
        def complex_calculation(data):
            # 复杂计算...
            return result
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > threshold:
                # 获取函数参数信息
                arg_names = inspect.getfullargspec(func).args
                if arg_names and arg_names[0] in ('self', 'cls'):
                    is_method = True
                    if len(arg_names) > 1:
                        arg_values = args[1:] if len(args) > 1 else []
                    else:
                        arg_values = []
                else:
                    is_method = False
                    arg_values = args
                
                # 格式化参数信息（限制长度以防日志过大）
                arg_info = []
                for i, arg in enumerate(arg_values):
                    if i < len(arg_names) - (1 if is_method else 0):
                        arg_name = arg_names[i + (1 if is_method else 0)]
                        arg_str = str(arg)
                        if len(arg_str) > 50:
                            arg_str = arg_str[:47] + "..."
                        arg_info.append(f"{arg_name}={arg_str}")
                
                # 格式化关键字参数信息
                for key, value in kwargs.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    arg_info.append(f"{key}={value_str}")
                
                # 确定函数全名
                if is_method and args and hasattr(args[0], '__class__'):
                    class_name = args[0].__class__.__name__
                    func_name = f"{class_name}.{func.__name__}"
                else:
                    func_name = func.__name__
                
                # 记录性能警告
                logger.log(
                    log_level,
                    f"Performance warning: {func_name}({', '.join(arg_info)}) "
                    f"took {execution_time:.4f}s (threshold: {threshold:.4f}s)"
                )
            
            return result
        
        return cast(F, wrapper)
    
    return decorator

def memory_usage(func: F) -> F:
    """
    内存使用监控装饰器
    
    需要psutil库支持，如果不可用则只记录函数执行
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @memory_usage
        def process_large_dataset(dataset):
            # 处理大型数据集...
            return result
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            logger.warning("psutil not available, memory usage monitoring disabled")
            memory_before = None
        
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if memory_before is not None:
            try:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_diff = memory_after - memory_before
                
                # 记录内存使用情况
                logger.info(
                    f"Memory usage - {func.__name__}: "
                    f"Before: {memory_before:.2f}MB, After: {memory_after:.2f}MB, "
                    f"Diff: {memory_diff:.2f}MB, Time: {execution_time:.4f}s"
                )
            except Exception as e:
                logger.error(f"Error monitoring memory usage: {e}")
        
        return result
    
    return cast(F, wrapper)

# ============================================================================
# 缓存装饰器
# ============================================================================

def memoize(max_size: int = 128, expiry: Optional[float] = None) -> Callable[[F], F]:
    """
    函数结果缓存装饰器，带有最大缓存大小和过期时间控制
    
    Args:
        max_size: 缓存的最大条目数
        expiry: 缓存条目的过期时间（秒），None表示永不过期
    
    Returns:
        装饰器函数
    
    示例:
        @memoize(max_size=100, expiry=3600)  # 缓存100条结果，1小时过期
        def fetch_user_data(user_id):
            # 获取用户数据...
            return user_data
    """
    def decorator(func: F) -> F:
        cache: Dict[str, Any] = {}
        timestamps: Dict[str, float] = {}
        call_order: List[str] = []
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 创建缓存键
            key_parts = [str(arg) for arg in args]
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{func.__name__}:{':'.join(key_parts)}"
            
            # 检查是否在缓存中且未过期
            current_time = time.time()
            if cache_key in cache:
                if expiry is None or current_time - timestamps[cache_key] < expiry:
                    # 更新调用顺序（LRU策略）
                    if cache_key in call_order:
                        call_order.remove(cache_key)
                    call_order.append(cache_key)
                    return cache[cache_key]
                else:
                    # 过期，从缓存中移除
                    del cache[cache_key]
                    del timestamps[cache_key]
                    if cache_key in call_order:
                        call_order.remove(cache_key)
            
            # 计算结果
            result = func(*args, **kwargs)
            
            # 更新缓存
            cache[cache_key] = result
            timestamps[cache_key] = current_time
            call_order.append(cache_key)
            
            # 如果超过最大缓存大小，移除最旧的条目
            while len(cache) > max_size:
                oldest_key = call_order.pop(0)
                del cache[oldest_key]
                del timestamps[oldest_key]
            
            return result
        
        # 添加清除缓存的方法
        def clear_cache() -> None:
            """清除函数的缓存"""
            cache.clear()
            timestamps.clear()
            call_order.clear()
        
        # 添加获取缓存统计的方法
        def get_cache_stats() -> Dict[str, Any]:
            """获取缓存统计信息"""
            return {
                'size': len(cache),
                'max_size': max_size,
                'expiry': expiry,
                'hit_rate': getattr(wrapper, '_hits', 0) / 
                           (getattr(wrapper, '_hits', 0) + getattr(wrapper, '_misses', 0))
                           if hasattr(wrapper, '_hits') and 
                             (getattr(wrapper, '_hits', 0) + getattr(wrapper, '_misses', 0)) > 0
                           else 0
            }
        
        wrapper.clear_cache = clear_cache  # type: ignore
        wrapper.get_cache_stats = get_cache_stats  # type: ignore
        wrapper._hits = 0  # type: ignore
        wrapper._misses = 0  # type: ignore
        
        return cast(F, wrapper)
    
    return decorator

def volatile_cache(func: F) -> F:
    """
    简单的易失性缓存装饰器，只缓存最后一次调用结果
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @volatile_cache
        def get_latest_status():
            # 获取最新状态...
            return status
    """
    last_call = {
        'args': None,
        'kwargs': None,
        'result': None,
        'timestamp': 0.0
    }
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 检查参数是否与上次调用相同
        if (last_call['args'] == args and 
            last_call['kwargs'] == kwargs and 
            last_call['result'] is not None):
            return last_call['result']
        
        # 计算新结果
        result = func(*args, **kwargs)
        
        # 更新缓存
        last_call['args'] = args
        last_call['kwargs'] = kwargs
        last_call['result'] = result
        last_call['timestamp'] = time.time()
        
        return result
    
    return cast(F, wrapper)

# ============================================================================
# 错误处理装饰器
# ============================================================================

def retry(max_attempts: int = 3, 
          delay: float = 1.0, 
          backoff_factor: float = 2.0,
          exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception) -> Callable[[F], F]:
    """
    重试机制装饰器，自动重试失败的函数调用
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟增长因子
        exceptions: 需要重试的异常类型
    
    Returns:
        装饰器函数
    
    示例:
        @retry(max_attempts=5, exceptions=[ConnectionError, TimeoutError])
        def fetch_external_data(url):
            # 获取外部数据...
            return data
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = delay
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__} "
                            f"after error: {str(e)}. Waiting {current_delay:.2f}s."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"Max retry attempts ({max_attempts}) reached for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
            
            # 这行代码在逻辑上应该无法执行到
            return None
        
        return cast(F, wrapper)
    
    return decorator

def fallback(default_value: Any) -> Callable[[F], F]:
    """
    失败回退装饰器，在函数出错时返回默认值
    
    Args:
        default_value: 出错时返回的默认值
    
    Returns:
        装饰器函数
    
    示例:
        @fallback(default_value=[])
        def get_user_preferences(user_id):
            # 获取用户偏好，可能失败...
            return preferences
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Function {func.__name__} failed with error: {str(e)}. "
                    f"Returning fallback value: {default_value}"
                )
                return default_value
        
        return cast(F, wrapper)
    
    return decorator

def exception_handler(handler_func: Callable[[Exception, Callable, tuple, dict], Any]) -> Callable[[F], F]:
    """
    自定义异常处理装饰器
    
    Args:
        handler_func: 处理异常的函数，接收异常、原始函数和调用参数
    
    Returns:
        装饰器函数
    
    示例:
        def my_exception_handler(e, func, args, kwargs):
            logger.error(f"Error in {func.__name__}: {e}")
            # 自定义处理逻辑...
            return None
        
        @exception_handler(my_exception_handler)
        def risky_operation():
            # 有风险的操作...
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handler_func(e, func, args, kwargs)
        
        return cast(F, wrapper)
    
    return decorator

def log_exceptions(log_level: int = LogLevel.ERROR.value, 
                   reraise: bool = True) -> Callable[[F], F]:
    """
    异常日志记录装饰器
    
    Args:
        log_level: 日志级别
        reraise: 是否重新抛出异常
    
    Returns:
        装饰器函数
    
    示例:
        @log_exceptions(log_level=LogLevel.ERROR.value, reraise=True)
        def critical_operation():
            # 关键操作...
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取完整的异常信息
                exc_info = sys.exc_info()
                tb_str = "".join(traceback.format_exception(*exc_info))
                
                # 获取调用者信息
                stack = traceback.extract_stack()
                if len(stack) >= 2:
                    caller = stack[-2]
                    caller_info = f"{os.path.basename(caller.filename)}:{caller.lineno}"
                else:
                    caller_info = "unknown"
                
                # 记录详细的异常信息
                logger.log(
                    log_level,
                    f"Exception in {func.__name__} (called from {caller_info}): {str(e)}\n{tb_str}"
                )
                
                if reraise:
                    raise
                return None
        
        return cast(F, wrapper)
    
    return decorator

# ============================================================================
# 权限和安全装饰器
# ============================================================================

def require_permissions(*required_permissions: str) -> Callable[[F], F]:
    """
    权限检查装饰器
    
    Args:
        *required_permissions: 需要的权限列表
    
    Returns:
        装饰器函数
    
    示例:
        @require_permissions('user.read', 'user.write')
        def update_user_profile(user_id, data):
            # 更新用户资料...
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取当前用户（假设在某处可以获取）
            current_user = kwargs.get('current_user') or getattr(args[0], 'current_user', None)
            
            if current_user is None:
                # 如果找不到当前用户，尝试从全局上下文获取
                from core.context import get_current_user
                current_user = get_current_user()
            
            if current_user is None:
                raise PermissionDeniedError(
                    operation=func.__name__,
                    resource="unknown",
                    message="No authenticated user found"
                )
            
            # 检查用户权限
            user_permissions = getattr(current_user, 'permissions', [])
            if not isinstance(user_permissions, (list, tuple, set)):
                user_permissions = []
            
            # 检查是否有所有需要的权限
            missing_permissions = set(required_permissions) - set(user_permissions)
            if missing_permissions:
                resource_name = func.__name__
                raise PermissionDeniedError(
                    operation=func.__name__,
                    resource=resource_name,
                    required_permission=", ".join(missing_permissions),
                    message=f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator

def rate_limit(max_calls: int, 
               time_period: float = 60.0, 
               per_user: bool = True) -> Callable[[F], F]:
    """
    速率限制装饰器
    
    Args:
        max_calls: 时间段内的最大调用次数
        time_period: 时间段长度（秒）
        per_user: 是否按用户限制（而非全局）
    
    Returns:
        装饰器函数
    
    示例:
        @rate_limit(max_calls=5, time_period=60.0)  # 每分钟最多5次
        def send_notification(user_id, message):
            # 发送通知...
            pass
    """
    def decorator(func: F) -> F:
        # 记录调用历史
        call_history: Dict[str, List[float]] = {}
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_time = time.time()
            
            # 确定限制键（用户标识或"global"）
            if per_user:
                # 尝试获取用户标识符
                user_id = kwargs.get('user_id') or kwargs.get('current_user')
                if user_id is None and args:
                    if hasattr(args[0], 'current_user'):
                        user_id = getattr(args[0], 'current_user')
                    elif len(args) > 1:
                        # 假设第二个参数可能是用户ID
                        user_id = args[1]
                
                limit_key = str(user_id) if user_id is not None else "anonymous"
            else:
                limit_key = "global"
            
            # 获取该键的调用历史
            if limit_key not in call_history:
                call_history[limit_key] = []
            
            # 清理过期的调用记录
            call_history[limit_key] = [
                timestamp for timestamp in call_history[limit_key]
                if current_time - timestamp < time_period
            ]
            
            # 检查是否超过限制
            if len(call_history[limit_key]) >= max_calls:
                # 计算重置时间
                reset_time = time_period - (current_time - min(call_history[limit_key]))
                
                # 获取受限资源信息
                resource_info = f"{func.__name__} ({limit_key})"
                
                raise ApiRateLimitError(
                    limit=max_calls,
                    reset_time=int(reset_time),
                    message=f"Rate limit exceeded for {resource_info}. "
                            f"Limit: {max_calls} calls per {time_period}s.",
                    details={
                        'limit': max_calls,
                        'time_period': time_period,
                        'reset_time': int(reset_time),
                        'function': func.__name__,
                        'limit_key': limit_key
                    }
                )
            
            # 记录本次调用
            call_history[limit_key].append(current_time)
            
            # 执行函数
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator

def timeout(seconds: float, 
            error_message: Optional[str] = None) -> Callable[[F], F]:
    """
    超时控制装饰器
    
    Args:
        seconds: 超时时间（秒）
        error_message: 自定义错误消息
    
    Returns:
        装饰器函数
    
    示例:
        @timeout(5.0)  # 5秒超时
        def slow_operation():
            # 可能耗时的操作...
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import signal
            
            def handler(signum: int, frame: Any) -> None:
                """超时信号处理器"""
                message = error_message or f"Function '{func.__name__}' timed out after {seconds} seconds"
                raise ApiTimeoutError(
                    endpoint=func.__name__,
                    timeout=seconds,
                    message=message
                )
            
            # 设置信号处理器和闹钟
            original_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, handler)
            signal.setitimer(signal.ITIMER_REAL, seconds)
            
            try:
                return func(*args, **kwargs)
            finally:
                # 取消闹钟并还原原始信号处理器
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, original_handler)
        
        return cast(F, wrapper)
    
    return decorator

def resource_check(resource_type: str, 
                  max_usage: Union[int, float], 
                  current_usage_func: Callable[..., Union[int, float]]) -> Callable[[F], F]:
    """
    资源使用检查装饰器
    
    Args:
        resource_type: 资源类型名称
        max_usage: 最大允许使用量
        current_usage_func: 获取当前使用量的函数
    
    Returns:
        装饰器函数
    
    示例:
        def get_disk_usage():
            # 获取磁盘使用情况...
            return usage_in_mb
        
        @resource_check('disk', 1024, get_disk_usage)  # 限制磁盘使用为1GB
        def save_large_file(file_data):
            # 保存大文件...
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取当前资源使用量
            current_usage = current_usage_func()
            
            # 检查是否超过限制
            if current_usage >= max_usage:
                raise ResourceExhaustedError(
                    resource_type=resource_type,
                    limit=max_usage,
                    message=f"Resource '{resource_type}' exhausted. "
                            f"Current usage: {current_usage}, limit: {max_usage}.",
                    details={
                        'resource_type': resource_type,
                        'current_usage': current_usage,
                        'max_usage': max_usage,
                        'function': func.__name__
                    }
                )
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator

# ============================================================================
# 调试和开发装饰器
# ============================================================================

def deprecated(reason: str) -> Callable[[F], F]:
    """
    标记函数为已弃用
    
    Args:
        reason: 弃用原因
    
    Returns:
        装饰器函数
    
    示例:
        @deprecated("Use 'new_function' instead")
        def old_function():
            # 旧函数实现...
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取调用者信息
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = os.path.basename(frame.f_back.f_code.co_filename)
                caller_line = frame.f_back.f_lineno
                caller_info = f"{caller_file}:{caller_line}"
            else:
                caller_info = "unknown"
            
            # 记录警告
            logger.warning(
                f"Deprecated function '{func.__name__}' called from {caller_info}. "
                f"Reason: {reason}"
            )
            
            # 清理引用，防止内存泄漏
            del frame
            
            return func(*args, **kwargs)
        
        # 添加装饰器元数据
        if not hasattr(wrapper, '__deprecated__'):
            wrapper.__deprecated__ = True  # type: ignore
            wrapper.__deprecated_reason__ = reason  # type: ignore
        
        return cast(F, wrapper)
    
    return decorator

def trace(log_level: int = LogLevel.DEBUG.value) -> Callable[[F], F]:
    """
    函数调用跟踪装饰器
    
    Args:
        log_level: 日志级别
    
    Returns:
        装饰器函数
    
    示例:
        @trace()
        def process_step(data):
            # 处理步骤...
            return result
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 格式化参数信息（简短版）
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            # 获取调用者信息
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = os.path.basename(frame.f_back.f_code.co_filename)
                caller_line = frame.f_back.f_lineno
                caller_info = f"{caller_file}:{caller_line}"
            else:
                caller_info = "unknown"
            
            # 记录函数调用开始
            logger.log(
                log_level, 
                f"CALL: {func.__name__}({signature}) from {caller_info}"
            )
            
            # 记录调用时间
            start_time = time.time()
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 计算执行时间
                execution_time = time.time() - start_time
                
                # 格式化结果（简短版）
                result_repr = repr(result)
                if len(result_repr) > 100:
                    result_repr = result_repr[:97] + "..."
                
                # 记录函数调用结束和结果
                logger.log(
                    log_level,
                    f"RETURN: {func.__name__} -> {result_repr} (took {execution_time:.4f}s)"
                )
                
                return result
            except Exception as e:
                # 计算执行时间
                execution_time = time.time() - start_time
                
                # 记录函数调用异常
                logger.log(
                    log_level,
                    f"EXCEPTION: {func.__name__} -> {type(e).__name__}: {str(e)} (took {execution_time:.4f}s)"
                )
                
                # 重新抛出异常
                raise
            finally:
                # 清理引用，防止内存泄漏
                del frame
        
        return cast(F, wrapper)
    
    return decorator

def debug(func: F) -> F:
    """
    调试辅助装饰器，记录详细的函数调用信息
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @debug
        def complex_function(a, b, c=None):
            # 复杂函数实现...
            return result
    """
    sig = inspect.signature(func)
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取调用者信息
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = os.path.basename(frame.f_back.f_code.co_filename)
            caller_line = frame.f_back.f_lineno
            caller_function = frame.f_back.f_code.co_name
            caller_info = f"{caller_file}:{caller_line} in {caller_function}"
        else:
            caller_info = "unknown"
        
        # 将位置参数和关键字参数绑定到签名
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # 格式化参数信息
        args_str = []
        for name, value in bound_args.arguments.items():
            value_str = repr(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            args_str.append(f"{name}={value_str}")
        
        # 记录函数调用开始
        logger.debug(
            f"DEBUG: Calling {func.__name__}({', '.join(args_str)}) from {caller_info}"
        )
        
        # 记录调用时间和内存使用
        start_time = time.time()
        try:
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            memory_before = None
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 计算执行时间和内存使用
            execution_time = time.time() - start_time
            
            if memory_before is not None:
                try:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_diff = memory_after - memory_before
                    memory_info = f", Memory: {memory_before:.1f}MB -> {memory_after:.1f}MB ({memory_diff:+.1f}MB)"
                except Exception:
                    memory_info = ""
            else:
                memory_info = ""
            
            # 格式化结果
            result_repr = repr(result)
            if len(result_repr) > 100:
                result_repr = result_repr[:97] + "..."
            
            # 记录函数调用结束和结果
            logger.debug(
                f"DEBUG: {func.__name__} returned {result_repr} "
                f"(Time: {execution_time:.4f}s{memory_info})"
            )
            
            return result
        except Exception as e:
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 获取异常信息
            exc_info = sys.exc_info()
            tb_str = "".join(traceback.format_exception(*exc_info))
            
            # 记录函数调用异常
            logger.debug(
                f"DEBUG: {func.__name__} raised {type(e).__name__}: {str(e)} "
                f"(Time: {execution_time:.4f}s)\n{tb_str}"
            )
            
            # 重新抛出异常
            raise
        finally:
            # 清理引用，防止内存泄漏
            del frame
    
    return cast(F, wrapper)

# ============================================================================
# 文档和验证装饰器
# ============================================================================

def type_check(func: F) -> F:
    """
    类型检查装饰器，验证参数和返回值类型注解
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @type_check
        def add_numbers(a: int, b: int) -> int:
            return a + b
    """
    sig = inspect.signature(func)
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 将位置参数和关键字参数绑定到签名
        bound_args = sig.bind(*args, **kwargs)
        
        # 验证参数类型
        for name, param in sig.parameters.items():
            if param.annotation is not inspect.Parameter.empty:
                if name in bound_args.arguments:
                    value = bound_args.arguments[name]
                    if not isinstance(value, param.annotation) and value is not None:
                        raise TypeError(
                            f"Argument '{name}' must be of type {param.annotation.__name__}, "
                            f"got {type(value).__name__}"
                        )
        
        # 调用原始函数
        result = func(*args, **kwargs)
        
        # 验证返回值类型
        if sig.return_annotation is not inspect.Signature.empty:
            if not isinstance(result, sig.return_annotation) and result is not None:
                raise TypeError(
                    f"Return value must be of type {sig.return_annotation.__name__}, "
                    f"got {type(result).__name__}"
                )
        
        return result
    
    return cast(F, wrapper)

def validate_args(**validators: Callable[[Any], bool]) -> Callable[[F], F]:
    """
    参数验证装饰器
    
    Args:
        **validators: 参数名到验证函数的映射
    
    Returns:
        装饰器函数
    
    示例:
        def positive(x):
            return x > 0
        
        @validate_args(a=positive, b=positive)
        def divide(a, b):
            return a / b
    """
    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 将位置参数和关键字参数绑定到签名
            bound_args = sig.bind(*args, **kwargs)
            
            # 验证参数
            for name, validator in validators.items():
                if name in bound_args.arguments:
                    value = bound_args.arguments[name]
                    if not validator(value):
                        raise ValueError(
                            f"Argument '{name}' failed validation: {validator.__name__}({value!r}) is False"
                        )
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator

def enforce_types(func: F) -> F:
    """
    强制类型转换装饰器，根据类型注解自动转换参数
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @enforce_types
        def process_data(user_id: int, active: bool = True):
            # 处理数据...
            pass
    """
    sig = inspect.signature(func)
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 将位置参数和关键字参数绑定到签名
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # 转换参数类型
        for name, param in sig.parameters.items():
            if param.annotation is not inspect.Parameter.empty:
                if name in bound_args.arguments:
                    try:
                        # 尝试转换类型
                        bound_args.arguments[name] = param.annotation(bound_args.arguments[name])
                    except (ValueError, TypeError):
                        # 如果转换失败，保持原值并记录警告
                        logger.warning(
                            f"Could not convert argument '{name}' to {param.annotation.__name__}: "
                            f"{bound_args.arguments[name]!r}"
                        )
        
        # 使用转换后的参数调用函数
        return func(*bound_args.args, **bound_args.kwargs)
    
    return cast(F, wrapper)

# ============================================================================
# 辅助函数和类
# ============================================================================

def synchronized(lock: Optional[Any] = None) -> Callable[[F], F]:
    """
    同步装饰器，确保函数在同一时间只能由一个线程执行
    
    Args:
        lock: 可选的锁对象，默认为新建的线程锁
    
    Returns:
        装饰器函数
    
    示例:
        @synchronized()
        def update_shared_resource(data):
            # 更新共享资源...
            pass
    """
    import threading
    
    def decorator(func: F) -> F:
        # 使用提供的锁或创建新锁
        func_lock = lock or threading.RLock()
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with func_lock:
                return func(*args, **kwargs)
        
        # 存储锁对象供外部使用
        wrapper.__lock__ = func_lock  # type: ignore
        
        return cast(F, wrapper)
    
    return decorator

def async_execution(func: F) -> F:
    """
    异步执行装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    示例:
        @async_execution
        def long_running_task(data):
            # 耗时任务...
            return result
    """
    import threading
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> threading.Thread:
        # 创建结果容器
        result_container = {'result': None, 'exception': None, 'completed': False}
        
        # 包装函数以捕获结果或异常
        def task_wrapper() -> None:
            try:
                result_container['result'] = func(*args, **kwargs)
            except Exception as e:
                result_container['exception'] = e
            finally:
                result_container['completed'] = True
        
        # 创建线程
        thread = threading.Thread(target=task_wrapper)
        thread.daemon = True  # 设置为守护线程
        
        # 添加结果容器到线程对象
        thread.result_container = result_container  # type: ignore
        
        # 添加获取结果的方法
        def get_result(timeout: Optional[float] = None) -> Any:
            """
            获取异步执行结果
            
            Args:
                timeout: 等待超时时间（秒）
            
            Returns:
                函数执行结果
            
            Raises:
                任何函数执行过程中抛出的异常
            """
            thread.join(timeout)
            
            if not result_container['completed']:
                raise TimeoutError(f"Async execution did not complete within {timeout}s")
            
            if result_container['exception']:
                raise result_container['exception']
            
            return result_container['result']
        
        thread.get_result = get_result  # type: ignore
        
        # 启动线程
        thread.start()
        
        return thread
    
    return cast(F, wrapper)

class Profiled:
    """
    方法性能分析装饰器类，记录方法执行时间和调用次数
    
    示例:
        class MyClass:
            @Profiled()
            def my_method(self, arg1, arg2):
                # 方法实现...
                pass
    """
    
    profiles: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, threshold: float = 0.0) -> None:
        """
        初始化装饰器
        
        Args:
            threshold: 记录警告的时间阈值（秒）
        """
        self.threshold = threshold
    
    def __call__(self, method: F) -> F:
        """
        装饰方法
        
        Args:
            method: 被装饰的方法
        
        Returns:
            装饰后的方法
        """
        method_name = method.__name__
        
        # 确保方法有统计信息
        if method_name not in self.profiles:
            self.profiles[method_name] = {
                'calls': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'avg_time': 0.0
            }
        
        @functools.wraps(method)
        def wrapper(self_or_cls: Any, *args: Any, **kwargs: Any) -> Any:
            # 记录开始时间
            start_time = time.time()
            
            # 执行方法
            result = method(self_or_cls, *args, **kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 更新统计信息
            profile = Profiled.profiles[method_name]
            profile['calls'] += 1
            profile['total_time'] += execution_time
            profile['min_time'] = min(profile['min_time'], execution_time)
            profile['max_time'] = max(profile['max_time'], execution_time)
            profile['avg_time'] = profile['total_time'] / profile['calls']
            
            # 如果超过阈值，记录警告
            if self.threshold > 0 and execution_time > self.threshold:
                logger.warning(
                    f"Method '{method_name}' took {execution_time:.4f}s, "
                    f"exceeding threshold of {self.threshold:.4f}s"
                )
            
            return result
        
        return cast(F, wrapper)
    
    @classmethod
    def get_profile(cls, method_name: str) -> Dict[str, Any]:
        """
        获取方法的性能统计信息
        
        Args:
            method_name: 方法名称
        
        Returns:
            性能统计信息字典
        
        Raises:
            KeyError: 如果方法未被分析
        """
        if method_name not in cls.profiles:
            raise KeyError(f"No profile data for method '{method_name}'")
        
        return cls.profiles[method_name]
    
    @classmethod
    def print_profiles(cls) -> None:
        """打印所有方法的性能统计信息"""
        if not cls.profiles:
            print("No profiling data available")
            return
        
        print("\nMethod Profiles:")
        print("-" * 80)
        print(f"{'Method':<30} {'Calls':>8} {'Avg Time':>12} {'Min Time':>12} {'Max Time':>12}")
        print("-" * 80)
        
        for name, data in sorted(cls.profiles.items()):
            print(
                f"{name:<30} {data['calls']:>8d} {data['avg_time']:>12.4f}s "
                f"{data['min_time']:>12.4f}s {data['max_time']:>12.4f}s"
            )
        
        print("-" * 80)
        
        # 计算总调用次数和总时间
        total_calls = sum(data['calls'] for data in cls.profiles.values())
        total_time = sum(data['total_time'] for data in cls.profiles.values())
        
        print(f"Total: {len(cls.profiles)} methods, {total_calls} calls, {total_time:.4f}s")
        
    @classmethod
    def reset_profiles(cls) -> None:
        """重置所有性能统计信息"""
        cls.profiles.clear()

# ============================================================================
# 导出所有装饰器
# ============================================================================

__all__ = [
    # 性能监控装饰器
    'timer', 'performance_monitor', 'memory_usage',
    
    # 缓存装饰器
    'memoize', 'volatile_cache',
    
    # 错误处理装饰器
    'retry', 'fallback', 'exception_handler', 'log_exceptions',
    
    # 权限和安全装饰器
    'require_permissions', 'rate_limit', 'timeout', 'resource_check',
    
    # 调试和开发装饰器
    'deprecated', 'trace', 'debug',
    
    # 文档和验证装饰器
    'type_check', 'validate_args', 'enforce_types',
    
    # 辅助函数和类
    'synchronized', 'async_execution', 'Profiled',
]