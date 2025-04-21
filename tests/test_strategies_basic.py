"""
模块名称: tests.test_strategies_basic
功能描述: 基础策略模板测试
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import unittest
import config.paths as pd
import modules.nlp as np
from trading.strategies.templates.basic_strategy import BasicStrategy
from trading.strategies.strategy_validator import StrategyValidator


class TestBasicStrategy(unittest.TestCase):
    """
    测试BasicStrategy策略模板
    """

    def setUp(self):
        """
        测试前准备工作
        """
        self.strategy = BasicStrategy()
        self.test_data = self._generate_test_data()

    def test_class_attributes(self):
        """
        测试类属性是否正确设置
        """
        # 检查必要的属性
        self.assertIsInstance(self.strategy.minimal_roi, dict)
        self.assertIsInstance(self.strategy.stoploss, float)
        self.assertIsInstance(self.strategy.timeframe, str)

        # 检查属性值
        self.assertLess(self.strategy.stoploss, 0, "止损应为负值")
        self.assertGreaterEqual(
            len(self.strategy.minimal_roi), 1, "minimal_roi应至少有一个时间点"
        )

    def test_populate_indicators(self):
        """
        测试指标计算功能
        """
        metadata = {"pair": "BTC/USDT"}
        df_indicators = self.strategy.populate_indicators(
            self.test_data.copy(), metadata
        )

        # 检查是否添加了所需指标
        self.assertIn("sma7", df_indicators.columns)
        self.assertIn("sma25", df_indicators.columns)
        self.assertIn("sma99", df_indicators.columns)
        self.assertIn("rsi", df_indicators.columns)

        # 检查指标值是否有效
        self.assertFalse(df_indicators["sma7"].isnull().all())
        self.assertFalse(df_indicators["rsi"].isnull().all())

        # 检查RSI范围是否合理
        rsi_values = df_indicators["rsi"].dropna()
        if len(rsi_values) > 0:
            self.assertTrue((rsi_values >= 0).all()
                            and (rsi_values <= 100).all())

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

    def test_strategy_validator(self):
        """
        测试策略验证器
        """
        # 静态验证
        is_valid, issues = StrategyValidator.validate_strategy_class(
            BasicStrategy)
        self.assertTrue(is_valid, f"策略验证失败: {issues}")

        # 动态测试
        is_valid, issues, test_results = StrategyValidator.dynamic_test(
            BasicStrategy)
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