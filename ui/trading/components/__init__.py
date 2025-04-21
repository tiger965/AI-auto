"""
Trading UI components for the quantitative trading system.

This package contains UI components for visualizing trading strategies,
displaying performance metrics, and interacting with the trading system.
"""

from ui.trading.components.strategy_viewer import StrategyViewer
from ui.trading.components.performance_dashboard import PerformanceDashboard

__all__ = [
    "StrategyViewer",
    "PerformanceDashboard",
]