# api/api_manager.py
"""API管理器模块，负责管理所有API接口"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # 导入配置
    from config import config
except ImportError:
    print("错误: 无法导入config模块")
    # 使用默认配置
    config = {"api": {"enabled": True, "host": "127.0.0.1", "port": 8000}}


class APIManager:
    """API管理器，负责初始化和管理所有API接口"""

    def __init__(self):
        """初始化API管理器"""
        self.api_enabled = config["api"]["enabled"]
        self.api_host = config["api"]["host"]
        self.api_port = config["api"]["port"]

        # API模块实例存储
        self.api_modules = {}

        print(f"API管理器初始化完成，状态: {'启用' if self.api_enabled else '禁用'}")

    def register_api_module(self, name, module_instance):
        """注册API模块"""
        if name in self.api_modules:
            print(f"警告: API模块 '{name}' 已存在，将被覆盖")

        self.api_modules[name] = module_instance
        print(f"API模块 '{name}' 注册成功")

        return True

    def get_api_module(self, name):
        """获取API模块实例"""
        if name not in self.api_modules:
            print(f"错误: API模块 '{name}' 不存在")
            return None

        return self.api_modules[name]

    def start_api_server(self):
        """启动API服务器"""
        if not self.api_enabled:
            print("API服务已禁用，跳过启动")
            return False

        try:
            print(f"正在启动API服务器，地址: {self.api_host}:{self.api_port}")
            # 这里只是模拟API服务器启动
            # 实际项目中，可能使用Flask或FastAPI等框架
            print("API服务器启动成功")
            return True
        except Exception as e:
            print(f"API服务器启动失败: {str(e)}")
            return False

    def stop_api_server(self):
        """停止API服务器"""
        if not self.api_enabled:
            print("API服务已禁用，无需停止")
            return True

        try:
            print("正在停止API服务器")
            # 这里只是模拟API服务器关闭
            print("API服务器已停止")
            return True
        except Exception as e:
            print(f"API服务器停止失败: {str(e)}")
            return False

    def list_api_modules(self):
        """列出所有已注册的API模块"""
        if not self.api_modules:
            print("当前没有注册的API模块")
            return []

        print("已注册的API模块:")
        for name in self.api_modules:
            print(f"  - {name}")

        return list(self.api_modules.keys())


# 为了便于测试
if __name__ == "__main__":
    # 测试API管理器
    api_manager = APIManager()
    api_manager.start_api_server()
    api_manager.list_api_modules()