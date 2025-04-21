"""
模块名称：trading.optimization.objective_functions
功能描述：定义优化算法使用的目标函数，包括各种性能指标
版本：1.0
创建日期：2025-04-20
作者：窗口9.4
"""

import modules.nlp as np
from typing import Dict, List, Any, Union, Optional, Callable
import config.paths as pd
from abc import ABC, abstractmethod


class ObjectiveFunction(ABC):
    """
    目标函数基类，定义目标函数的基本接口

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
    """

    def __init__(self, name: str, direction: str = "maximize"):
        """
        初始化目标函数

        参数:
            name (str): 目标函数名称
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'maximize'

        异常:
            ValueError: 如果方向不是 'minimize' 或 'maximize'
        """
        if direction not in ["minimize", "maximize"]:
            raise ValueError("优化方向必须是 'minimize' 或 'maximize'")
        self.name = name
        self.direction = direction

    @abstractmethod
    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算目标函数值

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 目标函数值

        异常:
            NotImplementedError: 子类必须实现此方法
        """
        pass

    def __call__(self, backtest_result: Dict[str, Any]) -> float:
        """
        使目标函数对象可调用

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 目标函数值
        """
        return self.calculate(backtest_result)

    def to_dict(self) -> Dict[str, Any]:
        """
        将目标函数转换为字典表示

        返回:
            Dict[str, Any]: 目标函数的字典表示
        """
        return {
            "name": self.name,
            "direction": self.direction,
            "type": self.__class__.__name__,
        }


class ProfitObjective(ObjectiveFunction):
    """
    净利润目标函数，评估策略总体盈利能力

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
    """

    def __init__(self, direction: str = "maximize"):
        """
        初始化净利润目标函数

        参数:
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'maximize'
        """
        super().__init__("profit", direction)

    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算净利润

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据，应包含 'profit_percent' 字段

        返回:
            float: 净利润百分比

        异常:
            KeyError: 如果回测结果不包含所需数据
        """
        try:
            return backtest_result["profit_percent"]
        except KeyError:
            raise KeyError("回测结果中未找到 'profit_percent' 字段")


class SharpeObjective(ObjectiveFunction):
    """
    夏普比率目标函数，评估风险调整后的收益

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
        risk_free_rate (float): 无风险利率
    """

    def __init__(self, risk_free_rate: float = 0.0, direction: str = "maximize"):
        """
        初始化夏普比率目标函数

        参数:
            risk_free_rate (float): 无风险利率，默认为0.0
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'maximize'
        """
        super().__init__("sharpe", direction)
        self.risk_free_rate = risk_free_rate

    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算夏普比率

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 夏普比率

        异常:
            KeyError: 如果回测结果不包含所需数据
            ValueError: 如果标准差为0
        """
        try:
            # 从回测结果中获取所需数据
            if "sharpe" in backtest_result:
                return backtest_result["sharpe"]

            # 如果没有直接提供夏普比率，则计算
            returns = pd.Series(backtest_result["trade_returns"])

            if len(returns) < 2:
                return 0.0

            excess_returns = returns - self.risk_free_rate
            mean_excess_return = excess_returns.mean()
            std_excess_return = excess_returns.std()

            if std_excess_return == 0:
                return 0.0

            return mean_excess_return / std_excess_return

        except KeyError:
            raise KeyError("回测结果中未找到计算夏普比率所需的数据")


class SortinoObjective(ObjectiveFunction):
    """
    索提诺比率目标函数，只考虑下行风险的夏普比率变体

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
        risk_free_rate (float): 无风险利率
    """

    def __init__(self, risk_free_rate: float = 0.0, direction: str = "maximize"):
        """
        初始化索提诺比率目标函数

        参数:
            risk_free_rate (float): 无风险利率，默认为0.0
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'maximize'
        """
        super().__init__("sortino", direction)
        self.risk_free_rate = risk_free_rate

    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算索提诺比率

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 索提诺比率

        异常:
            KeyError: 如果回测结果不包含所需数据
            ValueError: 如果下行偏差为0
        """
        try:
            # 从回测结果中获取所需数据
            if "sortino" in backtest_result:
                return backtest_result["sortino"]

            # 如果没有直接提供索提诺比率，则计算
            returns = pd.Series(backtest_result["trade_returns"])

            if len(returns) < 2:
                return 0.0

            excess_returns = returns - self.risk_free_rate
            mean_excess_return = excess_returns.mean()

            # 计算下行偏差 (只考虑负收益)
            negative_returns = excess_returns[excess_returns < 0]

            if len(negative_returns) == 0:
                return float("inf") if mean_excess_return > 0 else 0.0

            downside_deviation = np.sqrt(np.mean(negative_returns**2))

            if downside_deviation == 0:
                return 0.0

            return mean_excess_return / downside_deviation

        except KeyError:
            raise KeyError("回测结果中未找到计算索提诺比率所需的数据")


class CalmarObjective(ObjectiveFunction):
    """
    卡玛比率目标函数，使用最大回撤来衡量风险

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
    """

    def __init__(self, direction: str = "maximize"):
        """
        初始化卡玛比率目标函数

        参数:
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'maximize'
        """
        super().__init__("calmar", direction)

    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算卡玛比率

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 卡玛比率

        异常:
            KeyError: 如果回测结果不包含所需数据
            ValueError: 如果最大回撤为0
        """
        try:
            # 从回测结果中获取所需数据
            if "calmar" in backtest_result:
                return backtest_result["calmar"]

            # 如果没有直接提供卡玛比率，则计算
            annual_return = backtest_result.get("annual_return", 0.0)
            max_drawdown = backtest_result.get("max_drawdown", 0.0)

            if max_drawdown == 0:
                return 0.0

            return annual_return / abs(max_drawdown)

        except KeyError:
            raise KeyError("回测结果中未找到计算卡玛比率所需的数据")


class DrawdownObjective(ObjectiveFunction):
    """
    最大回撤目标函数，评估策略的风险承受能力

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
    """

    def __init__(self, direction: str = "minimize"):
        """
        初始化最大回撤目标函数

        参数:
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'minimize'
        """
        super().__init__("drawdown", direction)

    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算最大回撤

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 最大回撤(百分比)

        异常:
            KeyError: 如果回测结果不包含所需数据
        """
        try:
            # 从回测结果中获取所需数据
            return abs(backtest_result["max_drawdown"])
        except KeyError:
            raise KeyError("回测结果中未找到 'max_drawdown' 字段")


class ProfitDrawdownRatioObjective(ObjectiveFunction):
    """
    利润回撤比目标函数，平衡收益和风险

    属性:
        name (str): 目标函数名称
        direction (str): 优化方向，'minimize' 或 'maximize'
    """

    def __init__(self, direction: str = "maximize"):
        """
        初始化利润回撤比目标函数

        参数:
            direction (str): 优化方向，'minimize' 或 'maximize'，默认为 'maximize'
        """
        super().__init__("profit_drawdown_ratio", direction)

    def calculate(self, backtest_result: Dict[str, Any]) -> float:
        """
        计算利润回撤比

        参数:
            backtest_result (Dict[str, Any]): 回测结果数据

        返回:
            float: 利润回撤比

        异常:
            KeyError: 如果回测结果不包含所需数据
            ValueError: 如果最大回撤为0
        """
        try:
            profit = backtest_result["profit_percent"]
            max_drawdown = abs(backtest_result["max_drawdown"])

            if max_drawdown == 0:
                return float("inf") if profit > 0 else 0.0

            return profit / max_drawdown

        except KeyError:
            raise KeyError("回测结果中未找到计算利润回撤比所需的数据")


class ObjectiveFactory:
    """
    目标函数工厂，用于创建和管理各种目标函数
    """

    @staticmethod
    def create(objective_type: str, **kwargs) -> ObjectiveFunction:
        """
        创建目标函数对象

        参数:
            objective_type (str): 目标函数类型
            **kwargs: 传递给目标函数构造器的额外参数

        返回:
            ObjectiveFunction: 目标函数对象

        异常:
            ValueError: 如果目标函数类型不受支持
        """
        if objective_type.lower() == "profit":
            return ProfitObjective(**kwargs)
        elif objective_type.lower() == "sharpe":
            return SharpeObjective(**kwargs)
        elif objective_type.lower() == "sortino":
            return SortinoObjective(**kwargs)
        elif objective_type.lower() == "calmar":
            return CalmarObjective(**kwargs)
        elif objective_type.lower() == "drawdown":
            return DrawdownObjective(**kwargs)
        elif objective_type.lower() in ["profit_drawdown_ratio", "profit_drawdown"]:
            return ProfitDrawdownRatioObjective(**kwargs)
        else:
            raise ValueError(f"不支持的目标函数类型: {objective_type}")

    @staticmethod
    def get_available_objectives() -> List[str]:
        """
        获取所有可用的目标函数类型

        返回:
            List[str]: 可用目标函数类型列表
        """
        return [
            "profit",
            "sharpe",
            "sortino",
            "calmar",
            "drawdown",
            "profit_drawdown_ratio",
        ]