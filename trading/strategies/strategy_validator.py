"""
模块名称: strategies.strategy_validator
功能描述: 策略验证器，用于验证策略的有效性和兼容性
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import logging
import importlib
import inspect
import config.paths as pd
import modules.nlp as np
from typing import Dict, List, Type, Optional, Tuple, Any
from config.paths import DataFrame

# 设置日志
logger = logging.getLogger(__name__)


class StrategyValidator:
    """
    策略验证器，用于验证策略的有效性和兼容性

    提供静态分析和动态测试功能，确保策略符合Freqtrade框架要求
    """

    # 必需的方法列表
    REQUIRED_METHODS = [
        "populate_indicators",
        "populate_entry_trend",
        "populate_exit_trend",
    ]

    # 可选的方法列表
    OPTIONAL_METHODS = [
        "custom_stoploss",
        "custom_entry_price",
        "custom_exit_price",
        "custom_stake_amount",
        "confirm_trade_entry",
        "confirm_trade_exit",
    ]

    @classmethod
    def validate_strategy_class(cls, strategy_class: Type) -> Tuple[bool, List[str]]:
        """
        验证策略类是否符合Freqtrade框架要求

        参数:
            strategy_class (Type): 策略类

        返回:
            Tuple[bool, List[str]]: 验证结果和问题列表
        """
        issues = []

        # 检查必需的方法
        for method_name in cls.REQUIRED_METHODS:
            if not hasattr(strategy_class, method_name):
                issues.append(f"缺少必要方法: {method_name}")
            else:
                method = getattr(strategy_class, method_name)
                if not callable(method):
                    issues.append(f"{method_name} 不是一个可调用方法")

        # 检查必需的属性
        required_attributes = ["minimal_roi", "stoploss", "timeframe"]
        for attr in required_attributes:
            if not hasattr(strategy_class, attr):
                issues.append(f"缺少必要属性: {attr}")

        # 检查方法签名
        if hasattr(strategy_class, "populate_indicators"):
            try:
                signature = inspect.signature(
                    strategy_class.populate_indicators)
                params = signature.parameters
                if "dataframe" not in params or "metadata" not in params:
                    issues.append(
                        "populate_indicators 方法应接受 dataframe 和 metadata 参数"
                    )
            except (ValueError, TypeError):
                issues.append("无法检查 populate_indicators 方法签名")

        return len(issues) == 0, issues

    @classmethod
    def validate_strategy_file(
        cls, file_path: str
    ) -> Tuple[bool, List[str], Optional[Type]]:
        """
        从文件加载并验证策略

        参数:
            file_path (str): 策略文件路径

        返回:
            Tuple[bool, List[str], Optional[Type]]: 验证结果、问题列表和策略类（如果成功）
        """
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                "strategy_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找策略类
            strategy_class = None
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and name not in ["DataFrame", "Series"]
                    and any(method in dir(obj) for method in cls.REQUIRED_METHODS)
                ):
                    strategy_class = obj
                    break

            if strategy_class is None:
                return False, ["在文件中未找到有效的策略类"], None

            # 验证策略类
            is_valid, issues = cls.validate_strategy_class(strategy_class)
            return is_valid, issues, strategy_class

        except Exception as e:
            logger.error(f"验证策略文件时出错: {e}")
            return False, [f"验证策略文件时出错: {e}"], None

    @classmethod
    def dynamic_test(
        cls, strategy_class: Type, test_data: DataFrame = None
    ) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        对策略进行动态测试，验证其功能

        参数:
            strategy_class (Type): 策略类
            test_data (DataFrame, optional): 测试数据，若不提供则生成模拟数据

        返回:
            Tuple[bool, List[str], Optional[Dict]]: 测试结果、问题列表和测试详情
        """
        issues = []
        test_results = {}

        try:
            # 如果未提供测试数据，则生成模拟数据
            if test_data is None:
                test_data = cls._generate_test_data()

            # 创建策略实例
            strategy = strategy_class()

            # 测试populate_indicators
            try:
                metadata = {"pair": "BTC/USDT"}
                df_indicators = strategy.populate_indicators(
                    test_data.copy(), metadata)
                test_results["indicators"] = list(df_indicators.columns)

                # 检查是否添加了新的指标
                new_columns = set(df_indicators.columns) - \
                    set(test_data.columns)
                if len(new_columns) == 0:
                    issues.append("populate_indicators 方法没有添加任何新指标")

            except Exception as e:
                issues.append(f"测试 populate_indicators 时出错: {e}")

            # 测试populate_entry_trend
            try:
                df_entry = strategy.populate_entry_trend(
                    df_indicators.copy(), metadata)
                if "enter_long" not in df_entry.columns:
                    issues.append("populate_entry_trend 方法没有生成 'enter_long' 列")

                # 检查是否生成了买入信号
                if (
                    "enter_long" in df_entry.columns
                    and not df_entry["enter_long"].any()
                ):
                    issues.append("策略没有生成任何买入信号")

                test_results["entry_signals"] = (
                    int(df_entry["enter_long"].sum())
                    if "enter_long" in df_entry.columns
                    else 0
                )

            except Exception as e:
                issues.append(f"测试 populate_entry_trend 时出错: {e}")

            # 测试populate_exit_trend
            try:
                df_exit = strategy.populate_exit_trend(
                    df_entry.copy(), metadata)
                if "exit_long" not in df_exit.columns:
                    issues.append("populate_exit_trend 方法没有生成 'exit_long' 列")

                test_results["exit_signals"] = (
                    int(df_exit["exit_long"].sum())
                    if "exit_long" in df_exit.columns
                    else 0
                )

            except Exception as e:
                issues.append(f"测试 populate_exit_trend 时出错: {e}")

            return len(issues) == 0, issues, test_results

        except Exception as e:
            logger.error(f"对策略进行动态测试时出错: {e}")
            return False, [f"对策略进行动态测试时出错: {e}"], None

    @staticmethod
    def _generate_test_data(periods: int = 200) -> DataFrame:
        """
        生成用于测试的模拟价格数据

        参数:
            periods (int): 数据点数量

        返回:
            DataFrame: 模拟OHLCV数据
        """
        np.random.seed(42)  # 确保可重复性

        # 生成随机价格和交易量
        base_price = 10000.0
        price_changes = np.random.normal(0, 200, periods).cumsum()
        prices = base_price + price_changes

        # 确保价格为正
        prices = np.maximum(prices, 100)

        # 创建OHLCV数据
        data = {
            "open": prices + np.random.normal(0, 10, periods),
            "high": prices + np.random.normal(50, 30, periods),
            "low": prices + np.random.normal(-50, 30, periods),
            "close": prices,
            "volume": np.random.lognormal(10, 1, periods),
        }

        # 确保high >= open, close, low 且 low <= open, close
        for i in range(periods):
            data["high"][i] = max(
                data["high"][i], data["open"][i], data["close"][i])
            data["low"][i] = min(
                data["low"][i], data["open"][i], data["close"][i])

        # 创建日期索引
        date_range = pd.date_range(
            end=pd.Timestamp.now(), periods=periods, freq="1h")

        # 创建DataFrame
        df = pd.DataFrame(data, index=date_range)

        return df


# 导出类
__all__ = ["StrategyValidator"]