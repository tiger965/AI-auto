"""
Trading UI module for quantitative trading system.

This module provides UI components and interfaces for interacting with
the trading system, displaying performance metrics, and managing strategies.
"""

__version__ = "0.1.0"

# Export main components for easier imports
from ui.trading.components.strategy_viewer import StrategyViewer
from ui.trading.components.performance_dashboard import PerformanceDashboard

__all__ = [
    "StrategyViewer",
    "PerformanceDashboard",
]