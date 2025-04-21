"""
模块名称：trading.backtesting
功能描述：量化交易回测系统，负责策略回测、性能分析和数据管理
版本：1.0
创建日期：2025-04-20
作者：窗口9.3开发者
"""

from trading.backtesting.backtest_engine import BacktestEngine
from trading.backtesting.performance_analyzer import PerformanceAnalyzer
from trading.backtesting.data_manager import DataManager

__all__ = [
    "BacktestEngine",
    "PerformanceAnalyzer",
    "DataManager",
]