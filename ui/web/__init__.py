
# 添加项目根目录到Python路径
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿""""
Web模块初始化文件
负责初始化Web界面相关组件和路由
""""

from flask import Flask

def create_module(app: Flask, **kwargs):
    pass
""""
    初始化Web模块
    
    Args:
        app: Flask应用实例
        **kwargs: 额外配置参数
    """"
    from . import routes
    from . import websocket
    
    # 注册路由
    routes.init_app(app)
    
    # 初始化WebSocket
    websocket.init_app(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册上下文处理器
    register_context_processors(app)
    
    # 设置静态文件路径 - 添加这行
    app.static_folder = 'ui/web/assets'
    app.static_url_path = '/static'

def register_error_handlers(app: Flask):
    pass
"""注册应用错误处理器"""
    @app.errorhandler(404)
    def page_not_found(e):
    pass
from . import views
        return views.render_404(), 404
    
    @app.errorhandler(500)
    def server_error(e):
    pass
from . import views
        return views.render_500(), 500

def register_context_processors(app: Flask):
    pass
"""注册模板上下文处理器"""
    @app.context_processor
    def inject_globals():
    pass
"""向所有模板注入全局变量"""
        from flask import session
        from ..auth.utils import get_current_user
        
        # 获取当前用户
        user = get_current_user()
        
        # 获取当前主题
        theme = session.get('theme', 'harmony')
        
        # 音效设置 - 添加这部分
        audio_enabled = True
        if user and hasattr(user, 'preferences'):
    pass
audio_enabled = user.preferences.get('enable_sound', True)
        
        return {
            'current_user': user,
            'theme': theme,
            'audio_enabled': audio_enabled, # 添加这行
            'app_name': 'AI助手',
            'version': '1.0.0'
        }