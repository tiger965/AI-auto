# -*- coding: utf-8 -*-
"""
图表UI模块
"""


class Chart:
    """
    图表组件
    """

    def __init__(self, chart_type="line", title="交易数据图表"):
        """初始化图表"""
        self.chart_type = chart_type
        self.title = title
        self.data = []

    def set_data(self, data):
        """设置图表数据"""
        self.data = data
        return True

    def render(self):
        """渲染图表"""
        return {
            "type": self.chart_type,
            "title": self.title,
            "data_points": len(self.data),
            "status": "rendered",
        }

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认图表实例
default_chart = Chart()