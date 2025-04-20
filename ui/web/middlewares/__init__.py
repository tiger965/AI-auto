"""
Web中间件包初始化文件
用于导入和配置所有中间件组件
"""

def init_middlewares(app):
    """
    初始化所有中间件
    
    Args:
        app: Flask应用实例
    """
    # 导入各个中间件模块
    from . import auth
    from . import response
    
    # 初始化各个中间件
    auth.init_app(app)
    response.init_app(app)
    
    # 注册日志中间件
    register_logging_middleware(app)

def register_logging_middleware(app):
    """
    注册日志记录中间件
    """
    @app.after_request
    def log_response(response):
        """记录请求响应信息"""
        from flask import request, g
        import time
        
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            app.logger.info(f"Request completed in {elapsed:.4f}s: {request.method} {request.path}")
        
        return response