
# 添加项目根目录到Python路径
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿""""
Web中间件包初始化文件
用于导入和配置所有中间件组件
""""

def init_middlewares(app):
    pass
""""
    初始化所有中间件
    
    Args:
        app: Flask应用实例
    """"
    # 导入各个中间件模块
    from . import auth
    from . import response
    
    # 初始化各个中间件
    auth.init_app(app)
    response.init_app(app)
    
    # 注册日志中间件
    register_logging_middleware(app)

def register_logging_middleware(app):
    pass
""""
    注册日志记录中间件
    """"
    @app.after_request
    def log_response(response):
    pass
"""记录请求响应信息"""
        from flask import request, g
        import time
        
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
    pass
elapsed = time.time() - g.start_time
            app.logger.info(f"Request completed in {elapsed:.4f}s: {request.method} {request.path}")
        
        return response