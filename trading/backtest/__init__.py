# -*- coding: utf-8 -*-
"""
回测模块
"""


class Backtester:
    """
    策略回测器
    """

    def __init__(self, strategy=None):
        """初始化回测器"""
        self.strategy = strategy or "default_strategy"
        self.results = {}

    def run_backtest(self, market_data, start_date, end_date):
        """运行回测"""
        self.results = {
            "profit": 200.0,
            "max_drawdown": 50.0,
            "win_rate": 0.7,
            "sharpe_ratio": 1.5,
        }
        return self.results

    def get_performance_metrics(self):
        """获取性能指标"""
        return self.results

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认回测器实例
default_backtester = Backtester()