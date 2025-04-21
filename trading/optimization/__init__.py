"""
模块名称：trading.optimization
功能描述：量化交易优化系统，提供参数优化和策略优化功能
版本：1.0
创建日期：2025-04-20
作者：窗口9.4
"""

from .hyperopt import Hyperopt
from .parameter_space import ParameterSpace, Integer, Real, Categorical
from .objective_functions import (
    ProfitObjective,
    SharpeObjective,
    SortinoObjective,
    CalmarObjective,
    DrawdownObjective,
    ProfitDrawdownRatioObjective,
    ObjectiveFactory,
)

__all__ = [
    "Hyperopt",
    "ParameterSpace",
    "Integer",
    "Real",
    "Categorical",
    "ProfitObjective",
    "SharpeObjective",
    "SortinoObjective",
    "CalmarObjective",
    "DrawdownObjective",
    "ProfitDrawdownRatioObjective",
    "ObjectiveFactory",
]