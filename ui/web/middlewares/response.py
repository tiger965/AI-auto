""""
响应处理中间件
负责统一处理HTTP响应格式、添加响应头和性能监控
""""

from flask import request, g, jsonify
from functools import wraps
import time

def init_app(app):
    """"
    初始化响应处理中间件
    
    Args:
        app: Flask应用实例
    """"
   @app.after_request
def handle_static_assets(response):
    """处理静态资源缓存和加载"""
    if request.path.startswith('/static/'):
        # 为静态资源添加长期缓存
        if not app.debug:
            # 一年缓存
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        
        # 对于主题CSS文件，不设置缓存，确保切换主题后立即生效
        if '/static/css/themes/' in request.path:
            response.headers['Cache-Control'] = 'no-cache, no-store'
    
    return response
    
    @app.after_request
    def add_performance_headers(response):
        """添加性能相关的响应头"""
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            
            # 添加服务器处理时间头部
            response.headers['X-Process-Time'] = f"{elapsed:.4f}"
            
            # 记录完成信息到日志
            app.logger.info(f"Request completed in {elapsed:.4f}s")
        
        return response

def rate_limiter(max_requests=100, time_window=60):
    """"
    请求频率限制装饰器
    
    Args:
        max_requests: 时间窗口内允许的最大请求数
        time_window: 时间窗口长度（秒）
    """"
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # 获取用户IP
            ip = request.remote_addr
            
            # 检查该IP的请求频率
            # 实际应用中可能需要使用Redis等缓存系统来存储请求计数
            current_time = time.time()
            key = f"rate_limit:{ip}:{int(current_time / time_window)}"
            
            # 这里简化处理，实际应用中应使用Redis或类似系统
            if hasattr(g, 'rate_limit_counters'):
                counters = g.rate_limit_counters
            else:
                counters = {}
                g.rate_limit_counters = counters
            
            # 检查和增加计数
            count = counters.get(key, 0) + 1
            counters[key] = count
            
            if count > max_requests:
                # 超过频率限制，返回429状态码
                return {"error": "请求过于频繁，请稍后再试"}, 429
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def format_json_response(f):
    """"
    格式化JSON响应装饰器
    统一API响应格式
    """"
    @wraps(f)
    def wrapped(*args, **kwargs):
        result = f(*args, **kwargs)
        
        # 如果结果已经是Response对象，直接返回
        from flask import Response
        if isinstance(result, Response):
            return result
        
        # 处理元组形式的结果 (data, status_code)
        status_code = 200
        if isinstance(result, tuple) and len(result) == 2:
            result, status_code = result
        
        # 构建统一的响应格式
        response = {
            "success": 200 <= status_code < 300,
            "data": result,
            "timestamp": int(time.time())
        }
        
        if not response["success"]:
            response["error"] = result.get("error", "未知错误") if isinstance(result, dict) else str(result)
            response["data"] = None
        
        return jsonify(response), status_code
    
    return wrapped# 响应处理中间件