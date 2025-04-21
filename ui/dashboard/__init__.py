# -*- coding: utf-8 -*-
"""
仪表盘UI模块
"""


class Dashboard:
    """
    仪表盘组件
    """

    def __init__(self, title="AI交易系统仪表盘"):
        """初始化仪表盘"""
        self.title = title
        self.widgets = []

    def add_widget(self, widget):
        """添加组件"""
        self.widgets.append(widget)
        return True

    def render(self):
        """渲染仪表盘"""
        return {"title": self.title, "widgets": len(self.widgets), "status": "rendered"}

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认仪表盘实例
default_dashboard = Dashboard()