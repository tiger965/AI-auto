# ui/cli/__init__.py
"""命令行界面模块"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 尝试导入readline以支持命令行编辑功能
readline_available = False
try:
    # 尝试导入pyreadline3（Windows平台）
    import pyreadline3 as readline

    readline_available = True
except ImportError:
    try:
        # 尝试导入原生readline（Unix/Mac平台）
        import readline

        readline_available = True
    except ImportError:
        # 如果都不可用，不需要做任何事情
        # 我们会通过后续代码处理这种情况
        pass

if not readline_available:
    print("警告: readline模块不可用，高级命令行功能将被禁用")
    print("提示: 在Windows上可以使用 pip install pyreadline3")

# 导入核心引擎
try:
    from core.engine import Engine
except ImportError:
    # 如果无法导入，创建一个简单的模拟引擎
    from .mock_engine import MockEngine as Engine

    print("警告: 无法导入核心引擎，使用模拟引擎")


def initialize_cli():
    """初始化命令行界面"""
    try:
        from ui.cli.commands import CommandProcessor
    except ImportError:
        # 如果无法导入，使用简单的命令处理器
        from .simple_commands import SimpleCommandProcessor as CommandProcessor

        print("警告: 无法导入命令处理器，使用简单命令处理器")

    # 创建和初始化核心引擎
    engine = Engine()

    # 创建命令处理器
    cmd_processor = CommandProcessor(engine)

    # 显示欢迎信息
    try:
        from config import config

        app_name = config.get("app_name", "AI自动化系统")
        version = config.get("version", "1.0.0")
    except ImportError:
        app_name = "AI自动化系统"
        version = "1.0.0"

    print(f"\n欢迎使用 {app_name} v{version}")
    print("输入 'help' 查看可用命令，输入 'exit' 退出系统\n")

    # 启动命令行循环
    cmd_processor.start_cli()

    return True


# 简单的模拟引擎类（在ui/cli/mock_engine.py中）
class MockEngine:
    """模拟引擎，当无法导入真实引擎时使用"""

    def __init__(self):
        self.running = False
        self.modules = {}
        print("警告: 使用模拟引擎")

    def start(self):
        self.running = True
        print("模拟引擎已启动")
        return True

    def stop(self):
        self.running = False
        print("模拟引擎已停止")
        return True

    def status(self):
        return {"running": self.running, "uptime": 0, "modules": 0, "module_list": []}


# 简单的命令处理器（在ui/cli/simple_commands.py中）
class SimpleCommandProcessor:
    """简单的命令处理器，当无法导入真实命令处理器时使用"""

    def __init__(self, engine):
        self.engine = engine
        self.running = False

    def start_cli(self):
        self.running = True
        print("警告: 使用简单命令处理器")

        while self.running:
            try:
                cmd = input("> ").strip()

                if cmd == "exit" or cmd == "quit":
                    print("再见！")
                    self.running = False
                elif cmd == "help":
                    print("\n可用命令:")
                    print("  help - 显示此帮助信息")
                    print("  exit, quit - 退出系统")
                    print("  start - 启动引擎")
                    print("  stop - 停止引擎")
                    print("  status - 显示状态")
                elif cmd == "start":
                    self.engine.start()
                elif cmd == "stop":
                    self.engine.stop()
                elif cmd == "status":
                    status = self.engine.status()
                    print(f"引擎状态: {'运行中' if status['running'] else '已停止'}")
                else:
                    print(f"未知命令: {cmd}")

            except KeyboardInterrupt:
                print("\n操作已取消")
            except EOFError:
                print("\n再见！")
                self.running = False
            except Exception as e:
                print(f"错误: {str(e)}")

        # 确保引擎停止
        if self.engine.running:
            self.engine.stop()


# 将需要导出的函数添加到__all__
__all__ = ["initialize_cli"]

# 为了便于测试
if __name__ == "__main__":
    initialize_cli()