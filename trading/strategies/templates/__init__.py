"""
模块名称: strategies.templates
功能描述: 策略模板集合，提供基础和高级策略模板
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

from trading.strategies.templates.basic_strategy import BasicStrategy
from trading.strategies.templates.advanced_strategy import AdvancedStrategy

__all__ = [
    "BasicStrategy",
    "AdvancedStrategy",
]