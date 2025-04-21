# ui/cli/mock_engine.py
"""模拟引擎模块"""


class MockEngine:
    """模拟引擎类"""

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