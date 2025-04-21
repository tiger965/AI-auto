# -*- coding: utf-8 -*-
"""
交易策略模块
"""


class TradingStrategy:
    """
    交易策略基类
    """

    def __init__(self, name="test_strategy"):
        """初始化交易策略"""
        self.name = name
        self.parameters = {}

    def set_parameter(self, key, value):
        """设置策略参数"""
        self.parameters[key] = value
        return True

    def generate_signals(self, market_data):
        """生成交易信号"""
        return {"symbol": market_data["symbol"], "signal": "buy"}

    def evaluate(self, market_data):
        """评估策略表现"""
        return {"profit": 100.0, "win_rate": 0.65}

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认策略实例
default_strategy = TradingStrategy()