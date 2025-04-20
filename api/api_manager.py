"""
API 管理器

API模块的中央管理系统，负责处理注册、发现和API请求的路由。
"""

import logging
import importlib
import os
import inspect
from flask import Flask, Blueprint, jsonify, request
from typing import Dict, List, Type, Optional, Any

from config import config
from .base_api import BaseAPI

class APIManager:
    """
    API 管理器，处理API模块的注册和路由
    """
    
    def __init__(self):
        """初始化API管理器"""
        self.logger = logging.getLogger(__name__)
        self.modules: Dict[str, BaseAPI] = {}
        self.app: Optional[Flask] = None
        self.enabled = config.get("api.enabled", True)
        self.host = config.get("api.host", "127.0.0.1")
        self.port = config.get("api.port", 5000)
        
        self.logger.info("API 管理器已初始化")
    
    def register_module(self, module: BaseAPI) -> None:
        """
        注册API模块
        
        参数:
            module: 要注册的API模块
        """
        module_name = module.name
        if module_name in self.modules:
            self.logger.warning(f"API模块'{module_name}'已注册。正在覆盖。")
        
        self.modules[module_name] = module
        self.logger.info(f"已注册API模块: {module_name}")
    
    def discover_modules(self) -> None:
        """
        发现并注册所有可用的API模块
        """
        # 获取API模块目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, "modules")
        
        if not os.path.exists(modules_dir):
            self.logger.warning(f"API模块目录未找到: {modules_dir}")
            return
        
        # 查找模块目录中的所有Python文件
        module_files = [f[:-3] for f in os.listdir(modules_dir) 
                        if f.endswith('.py') and not f.startswith('__')]
        
        for module_name in module_files:
            try:
                # 导入模块
                module_path = f"api.modules.{module_name}"
                module = importlib.import_module(module_path)
                
                # 查找所有继承自BaseAPI的类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseAPI) and 
                        obj is not BaseAPI):
                        
                        # 实例化并注册API模块
                        api_module = obj()
                        self.register_module(api_module)
                        
            except ImportError as e:
                self.logger.error(f"导入API模块{module_name}失败: {e}")
            except Exception as e:
                self.logger.error(f"加载API模块{module_name}时出错: {e}")
    
    def setup_app(self) -> Optional[Flask]:
        """
        设置包含所有已注册API模块的Flask应用程序
        
        返回:
            Flask: 配置好的Flask应用程序，如果API禁用则为None
        """
        if not self.enabled:
            self.logger.info("API在配置中已禁用")
            return None
        
        try:
            from flask import Flask
        except ImportError:
            self.logger.error("未安装Flask。无法设置API服务器。")
            return None
        
        # 创建Flask应用
        self.app = Flask(__name__)
        
        # 注册基本API端点
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """返回API状态"""
            return jsonify({
                "status": "online",
                "version": "1.0.0",
                "modules": list(self.modules.keys())
            })
        
        @self.app.route('/api/modules', methods=['GET'])
        def get_modules():
            """返回可用API模块列表"""
            modules_info = {}
            for name, module in self.modules.items():
                modules_info[name] = {
                    "description": module.description,
                    "version": module.version,
                    "endpoints": module.get_endpoints_info()
                }
            return jsonify(modules_info)
        
        # 注册所有API模块
        for name, module in self.modules.items():
            bp = module.create_blueprint()
            if bp:
                self.app.register_blueprint(bp)
                self.logger.info(f"已为API模块注册蓝图: {name}")
        
        # 添加错误处理
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "Not found", "message": "The requested resource does not exist"}), 404
        
        @self.app.errorhandler(500)
        def server_error(error):
            return jsonify({"error": "Server error", "message": "An internal server error occurred"}), 500
        
        # 添加CORS支持
        @self.app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response
        
        self.logger.info("API应用程序设置完成")
        return self.app
    
    def start_server(self) -> None:
        """
        启动API服务器
        """
        if not self.enabled:
            self.logger.info("API服务器在配置中已禁用")
            return
        
        if not self.modules:
            self.logger.warning("未注册API模块。正在发现模块...")
            self.discover_modules()
        
        if not self.app:
            self.setup_app()
        
        if not self.app:
            self.logger.error("设置Flask应用程序失败")
            return
        
        # 启动服务器
        try:
            self.logger.info(f"正在启动API服务器，地址: {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port)
        except Exception as e:
            self.logger.error(f"启动API服务器失败: {e}")
    
    def get_module(self, name: str) -> Optional[BaseAPI]:
        """
        通过名称获取API模块
        
        参数:
            name: API模块的名称
            
        返回:
            API模块，如果未找到则为None
        """
        return self.modules.get(name)
    
    def get_available_modules(self) -> List[str]:
        """
        获取可用API模块的列表
        
        返回:
            模块名称列表
        """
        return list(self.modules.keys())
    
    def handle_api_request(self, module_name: str, endpoint: str, method: str, data: Any = None) -> Dict[str, Any]:
        """
        处理API请求（用于内部调用）
        
        参数:
            module_name: API模块名称
            endpoint: 端点路径
            method: HTTP方法（GET, POST等）
            data: 请求数据
            
        返回:
            响应数据
        """
        module = self.get_module(module_name)
        if not module:
            return {"error": f"未找到模块: {module_name}"}, 404
        
        # 这里你可以添加更复杂的路由逻辑
        # 但通常这种内部调用会直接使用模块的方法
        # 这是一个简化的示例
        
        return {"module": module_name, "endpoint": endpoint, "method": method, "status": "not_implemented"}, 501