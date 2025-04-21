"""
模块名称: tests.test_strategies_advanced
功能描述: 高级策略模板测试
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import unittest
import config.paths as pd
import modules.nlp as np
from datetime import datetime, timedelta
from trading.strategies.templates.advanced_strategy import AdvancedStrategy
from trading.strategies.strategy_validator import StrategyValidator


class MockTrade:
    """
    Mock Trade类，用于测试custom_stoploss方法
    """

    def __init__(self, pair, open_rate, amount, open_date):
        self.pair = pair
        self.open_rate = open_rate
        self.amount = amount
        self.open_date = open_date


class TestAdvancedStrategy(unittest.TestCase):
    """
    测试AdvancedStrategy高级策略模板
    """

    def setUp(self):
        """
        测试前准备工作
        """
        self.strategy = AdvancedStrategy()
        self.test_data = self._generate_test_data()

    def test_class_attributes(self):
        """
        测试类属性是否正确设置
        """
        # 检查必要的属性
        self.assertIsInstance(self.strategy.minimal_roi, dict)
        self.assertIsInstance(self.strategy.stoploss, float)
        self.assertIsInstance(self.strategy.timeframe, str)
        self.assertIsInstance(self.strategy.trailing_stop, bool)

        # 如果启用了追踪止损，检查相关配置
        if self.strategy.trailing_stop:
            self.assertIsInstance(self.strategy.trailing_stop_positive, float)
            self.assertGreater(self.strategy.trailing_stop_positive, 0)

    def test_populate_indicators(self):
        """
        测试指标计算功能
        """
        metadata = {"pair": "BTC/USDT"}
        df_indicators = self.strategy.populate_indicators(
            self.test_data.copy(), metadata
        )

        # 检查是否添加了所需指标
        expected_indicators = [
            "sma_5",
            "ema_5",
            "sma_10",
            "ema_10",
            "sma_20",
            "ema_20",
            "sma_50",
            "ema_50",
            "sma_100",
            "ema_100",
            "sma_200",
            "ema_200",
            "volume_mean",
            "volume_ratio",
            "macd",
            "macdsignal",
            "macdhist",
            "rsi",
            "bb_upperband",
            "bb_middleband",
            "bb_lowerband",
            "bb_width",
            "atr",
            "market_state",
            "trend_direction",
        ]

        for indicator in expected_indicators:
            self.assertIn(indicator, df_indicators.columns,
                          f"缺少指标: {indicator}")

        # 检查指标值是否有效
        self.assertFalse(df_indicators["ema_20"].isnull().all())
        self.assertFalse(df_indicators["rsi"].isnull().all())
        self.assertFalse(df_indicators["macd"].isnull().all())

        # 检查RSI范围是否合理
        rsi_values = df_indicators["rsi"].dropna()
        if len(rsi_values) > 0:
            self.assertTrue((rsi_values >= 0).all()
                            and (rsi_values <= 100).all())

        # 检查市场状态是否被正确分类
        market_states = df_indicators["market_state"].dropna().unique()
        self.assertIn("trending", market_states, "市场状态应该包含'trending'")
        self.assertIn("oscillating", market_states, "市场状态应该包含'oscillating'")

    def test_populate_entry_trend(self):
        """
        测试买入信号生成功能
        """
        metadata = {"pair": "BTC/USDT"}
        df_indicators = self.strategy.populate_indicators(
            self.test_data.copy(), metadata
        )
        df_entry = self.strategy.populate_entry_trend(
            df_indicators.copy(), metadata)

        # 检查是否生成了buy列
        self.assertIn("enter_long", df_entry.columns)

        # 买入信号应该是0或1
        buy_signals = df_entry["enter_long"].dropna()
        if len(buy_signals) > 0:
            self.assertTrue(((buy_signals == 0) | (buy_signals == 1)).all())

    def test_populate_exit_trend(self):
        """
        测试卖出信号生成功能
        """
        metadata = {"pair": "BTC/USDT"}
        df_indicators = self.strategy.populate_indicators(
            self.test_data.copy(), metadata
        )
        df_entry = self.strategy.populate_entry_trend(
            df_indicators.copy(), metadata)
        df_exit = self.strategy.populate_exit_trend(df_entry.copy(), metadata)

        # 检查是否生成了sell列
        self.assertIn("exit_long", df_exit.columns)

        # 卖出信号应该是0或1
        sell_signals = df_exit["exit_long"].dropna()
        if len(sell_signals) > 0:
            self.assertTrue(((sell_signals == 0) | (sell_signals == 1)).all())

    def test_custom_stoploss(self):
        """
        测试自定义止损功能
        """
        if hasattr(self.strategy, "custom_stoploss") and callable(
            self.strategy.custom_stoploss
        ):
            # 创建mock交易对象
            trade = MockTrade(
                pair="BTC/USDT",
                open_rate=10000.0,
                amount=0.1,
                open_date=datetime.now() - timedelta(days=1),
            )

            # 测试不同利润率的止损调整
            current_time = datetime.now()

            # 亏损情况
            current_rate = 9500.0
            current_profit = -0.05
            stoploss = self.strategy.custom_stoploss(
                "BTC/USDT", trade, current_time, current_rate, current_profit
            )
            self.assertIsInstance(stoploss, float, "自定义止损应返回浮点数")

            # 小幅盈利情况
            current_rate = 10200.0
            current_profit = 0.02
            stoploss = self.strategy.custom_stoploss(
                "BTC/USDT", trade, current_time, current_rate, current_profit
            )
            self.assertIsInstance(stoploss, float, "自定义止损应返回浮点数")

            # 大幅盈利情况
            current_rate = 11000.0
            current_profit = 0.1
            stoploss = self.strategy.custom_stoploss(
                "BTC/USDT", trade, current_time, current_rate, current_profit
            )
            self.assertIsInstance(stoploss, float, "自定义止损应返回浮点数")

            # 大盈利情况下，自定义止损应该更高（更保守）
            self.assertGreater(
                stoploss, self.strategy.stoploss, "大盈利情况下，自定义止损应该更保守"
            )

    def test_market_classification(self):
        """
        测试市场状态分类功能
        """
        # 测试市场状态分类方法
        metadata = {"pair": "BTC/USDT"}
        df_classified = self.strategy._classify_market_state(
            self.test_data.copy())

        # 检查是否添加了市场状态列
        self.assertIn("market_state", df_classified.columns)

        # 市场状态应该只有两种：trending和oscillating
        market_states = df_classified["market_state"].dropna().unique()
        for state in market_states:
            self.assertIn(state, ["trending", "oscillating"])

        # 如果有trending市场，应该有trend_direction列
        if "trending" in market_states:
            self.assertIn("trend_direction", df_classified.columns)

            # trend_direction应该只有两种：uptrend和downtrend
            trend_directions = (
                df_classified.loc[
                    df_classified["market_state"] == "trending", "trend_direction"
                ]
                .dropna()
                .unique()
            )

            for direction in trend_directions:
                self.assertIn(direction, ["uptrend", "downtrend"])

    def test_strategy_validator(self):
        """
        测试策略验证器
        """
        # 静态验证
        is_valid, issues = StrategyValidator.validate_strategy_class(
            AdvancedStrategy)
        self.assertTrue(is_valid, f"策略验证失败: {issues}")

        # 动态测试
        is_valid, issues, test_results = StrategyValidator.dynamic_test(
            AdvancedStrategy
        )
        self.assertTrue(is_valid, f"策略动态测试失败: {issues}")

        # 检查测试结果
        self.assertIsNotNone(test_results)
        self.assertIn("indicators", test_results)
        self.assertIn("entry_signals", test_results)
        self.assertIn("exit_signals", test_results)

    def _generate_test_data(self, periods: int = 200) -> pd.DataFrame:
        """
        生成测试数据

        参数:
            periods (int): 数据点数量

        返回:
            pd.DataFrame: 测试用OHLCV数据
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


if __name__ == "__main__":
    unittest.main()