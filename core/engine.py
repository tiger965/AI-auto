# core/engine.py
"""AI自动化系统核心引擎"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 使用绝对导入
try:
    from config import config
except ImportError:
    print("警告: 无法导入config模块，使用默认配置")
    config = {"app_name": "AI自动化系统", "version": "1.0.0", "debug": False}


class Engine:
    """AI自动化系统核心引擎"""

    def __init__(self):
        """初始化引擎"""
        self.running = False
        self.modules = {}
        self.start_time = None

        print("核心引擎初始化完成")

    def register_module(self, name, module_instance):
        """注册功能模块"""
        if name in self.modules:
            print(f"警告: 模块 '{name}' 已存在，将被覆盖")

        self.modules[name] = module_instance
        print(f"模块 '{name}' 注册成功")

        return True

    def start(self):
        """启动引擎"""
        if self.running:
            print("引擎已经在运行中")
            return False

        try:
            print("正在启动核心引擎")
            self.running = True
            self.start_time = time.time()

            # 初始化所有已注册模块
            for name, module in self.modules.items():
                print(f"正在初始化模块: {name}")
                if hasattr(module, "initialize"):
                    module.initialize()

            print("核心引擎启动成功")
            return True
        except Exception as e:
            print(f"引擎启动失败: {str(e)}")
            self.running = False
            return False

    def stop(self):
        """停止引擎"""
        if not self.running:
            print("引擎未在运行")
            return True

        try:
            print("正在停止核心引擎")

            # 关闭所有已注册模块
            for name, module in self.modules.items():
                print(f"正在关闭模块: {name}")
                if hasattr(module, "shutdown"):
                    module.shutdown()

            self.running = False
            run_time = time.time() - self.start_time if self.start_time else 0
            print(f"核心引擎已停止，运行时间: {run_time:.2f}秒")
            return True
        except Exception as e:
            print(f"引擎停止失败: {str(e)}")
            return False

    def status(self):
        """获取引擎状态"""
        status_info = {
            "running": self.running,
            "uptime": (
                time.time() - self.start_time if self.running and self.start_time else 0
            ),
            "modules": len(self.modules),
            "module_list": list(self.modules.keys()),
        }

        print(f"引擎状态: {'运行中' if self.running else '已停止'}")
        print(f"已加载模块数量: {status_info['modules']}")

        return status_info


# 为了便于测试
if __name__ == "__main__":
    # 测试引擎
    engine = Engine()
    engine.start()
    print(engine.status())
    engine.stop()