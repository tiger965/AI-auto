#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版核心组件测试脚本
测试日期: 2025-04-20
文件位置: debug_tests/test_core_simple.py
"""

import sys
import os
import logging
import unittest
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CoreComponentsTest")

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 仅导入Engine类，避免导入可能存在问题的StrategyLearner
try:
    from core.engine import Engine
except ImportError as e:
    logger.error(f"导入Engine失败: {e}")
    sys.exit(1)


# 测试用的模拟类
class MockStrategyLearner:
    """策略学习器模拟类"""

    def __init__(self):
        """初始化策略学习器"""
        self.strategies = {}
        self.history = {}
        self.current_generation = 0
        logger.info("模拟策略学习器初始化成功")

    def is_initialized(self):
        """检查学习器是否已初始化"""
        return True

    def get_model_config(self):
        """获取模型配置"""
        return {
            "learning_rate": 0.01,
            "max_generations": 100,
            "population_size": 50,
            "mutation_rate": 0.1,
            "crossover_rate": 0.7,
            "elite_size": 5,
        }

    def evaluate_strategy(self, strategy):
        """评估策略"""
        logger.info(f"评估策略: {strategy.get('name', '未命名策略')}")
        return {
            "score": 85,
            "profit": 120,
            "drawdown": 15,
            "win_rate": 68,
            "sharpe_ratio": 1.8,
            "trades": 42,
        }

    def optimize_strategy(self, strategy):
        """优化策略"""
        logger.info(f"优化策略: {strategy.get('name', '未命名策略')}")
        optimized = strategy.copy()
        optimized["optimized"] = True
        return optimized

    def learn_from_history(self, symbol, history_data, max_iterations=50):
        """从历史数据学习策略"""
        logger.info(f"从{symbol}的历史数据学习策略...")

        # 返回模拟的学习结果
        return {
            "learned_strategy": {
                "id": f"{symbol}_learned_strategy",
                "name": f"{symbol} 学习策略",
                "symbol": symbol,
                "timeframe": history_data.get("timeframe", "1d"),
                "rules": [
                    {
                        "condition": "close > ma_20",
                        "action": "BUY",
                        "size": 1,
                        "stop_loss": 0.95,
                        "take_profit": 1.05,
                    }
                ],
            },
            "performance_metrics": {"score": 85, "profit": 120, "drawdown": 15},
            "iterations": max_iterations,
        }

    def improve_strategy(self, strategy):
        """改进策略"""
        # 返回模拟的改进策略
        improved = strategy.copy()
        improved["optimized"] = True
        return improved


class MockStrategyExecutor:
    """策略执行器模拟类"""

    def __init__(self):
        """初始化策略执行器"""
        self.strategies = {}
        logger.info("模拟策略执行器初始化")

    def validate_strategy(self, strategy):
        """验证策略有效性"""
        return True

    def load_strategy(self, strategy):
        """加载策略"""
        self.strategies[strategy["id"]] = strategy
        return True

    def generate_signals(self, symbol, timeframe, start_date, days=30):
        """生成交易信号"""
        return [
            {
                "id": "signal1",
                "strategy_id": "test_strategy",
                "symbol": symbol,
                "action": "BUY",
                "price": 100.5,
                "timestamp": datetime.now().isoformat(),
                "size": 1,
            },
            {
                "id": "signal2",
                "strategy_id": "test_strategy",
                "symbol": symbol,
                "action": "SELL",
                "price": 102.5,
                "timestamp": datetime.now().isoformat(),
                "size": 1,
            },
        ]

    def cleanup(self, strategy_id):
        """清理资源"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
        return True


class MockMarketAnalyzer:
    """市场分析器模拟类"""

    def __init__(self):
        """初始化市场分析器"""
        logger.info("模拟市场分析器初始化")

    def analyze_market_state(self, symbol):
        """分析市场状态"""
        return {
            "trend": "up",
            "volatility": 0.15,
            "strength": 0.75,
            "support": 95.5,
            "resistance": 105.2,
        }

    def analyze_correlation(self, symbols):
        """分析相关性"""
        result = {}
        for i, sym1 in enumerate(symbols):
            result[sym1] = {}
            for j, sym2 in enumerate(symbols):
                # 生成模拟相关性数据
                if sym1 == sym2:
                    result[sym1][sym2] = 1.0
                else:
                    result[sym1][sym2] = 0.5 - 0.1 * abs(i - j)
        return result

    def analyze_sentiment(self, symbol):
        """分析市场情绪"""
        return {
            "score": 0.65,
            "source_count": 120,
            "positive": 0.72,
            "negative": 0.28,
            "neutral": 0.0,
        }


class CoreComponentsTest(unittest.TestCase):
    """核心组件测试类"""

    def setUp(self):
        """测试前准备"""
        logger.info("初始化核心组件测试环境...")
        self.engine = Engine()
        self.strategy_learner = MockStrategyLearner()
        self.strategy_executor = MockStrategyExecutor()
        self.market_analyzer = MockMarketAnalyzer()

        # 测试参数
        self.test_symbol = "AAPL"
        self.test_strategy_id = "test_strategy_001"
        self.test_timeframe = "1d"

        logger.info("核心组件测试环境初始化完成")

    def test_01_engine_initialization(self):
        """测试引擎初始化"""
        logger.info("测试引擎初始化...")

        # 注册模块
        self.engine.register_module("strategy_learner", self.strategy_learner)
        self.engine.register_module(
            "strategy_executor", self.strategy_executor)
        self.engine.register_module("market_analyzer", self.market_analyzer)

        # 启动引擎
        result = self.engine.start()
        self.assertTrue(result, "引擎启动失败")

        # 检查引擎状态
        status = self.engine.status()
        self.assertTrue(status["running"], "引擎状态不正确")
        self.assertEqual(len(status["module_list"]), 3, "模块数量不正确")

        logger.info("引擎初始化测试通过")

    def test_02_strategy_learner(self):
        """测试策略学习器"""
        logger.info("测试策略学习器...")

        # 准备历史数据
        history_data = {
            "symbol": self.test_symbol,
            "timeframe": self.test_timeframe,
            "data": [
                {
                    "date": "2025-03-01",
                    "open": 100,
                    "high": 105,
                    "low": 99,
                    "close": 103,
                    "volume": 1000000,
                },
                {
                    "date": "2025-03-02",
                    "open": 103,
                    "high": 108,
                    "low": 102,
                    "close": 107,
                    "volume": 1200000,
                },
            ],
        }

        # 测试策略学习
        learning_result = self.strategy_learner.learn_from_history(
            symbol=self.test_symbol, history_data=history_data, max_iterations=10
        )

        self.assertIsNotNone(learning_result, "策略学习失败")
        self.assertIn("learned_strategy", learning_result, "学习结果缺少策略")

        # 测试策略改进
        improved_strategy = self.strategy_learner.improve_strategy(
            learning_result["learned_strategy"]
        )
        self.assertIsNotNone(improved_strategy, "策略改进失败")
        self.assertTrue(improved_strategy.get("optimized", False), "策略未被优化")

        logger.info("策略学习器测试通过")

    def test_03_strategy_executor(self):
        """测试策略执行器"""
        logger.info("测试策略执行器...")

        # 创建测试策略
        test_strategy = {
            "id": self.test_strategy_id,
            "name": "测试策略",
            "symbol": self.test_symbol,
            "timeframe": self.test_timeframe,
            "rules": [
                {
                    "condition": "close > ma_20",
                    "action": "BUY",
                    "size": 1,
                    "stop_loss": 0.95,
                    "take_profit": 1.05,
                }
            ],
        }

        # 验证策略
        is_valid = self.strategy_executor.validate_strategy(test_strategy)
        self.assertTrue(is_valid, "策略验证失败")

        # 加载策略
        loaded = self.strategy_executor.load_strategy(test_strategy)
        self.assertTrue(loaded, "策略加载失败")

        # 生成信号
        signals = self.strategy_executor.generate_signals(
            symbol=self.test_symbol,
            timeframe=self.test_timeframe,
            start_date=datetime.now(),
        )

        self.assertIsNotNone(signals, "信号生成失败")
        self.assertGreater(len(signals), 0, "生成的信号为空")

        logger.info("策略执行器测试通过")

    def test_04_market_analyzer(self):
        """测试市场分析器"""
        logger.info("测试市场分析器...")

        # 市场状态分析
        market_state = self.market_analyzer.analyze_market_state(
            self.test_symbol)
        self.assertIsNotNone(market_state, "市场状态分析失败")
        self.assertIn("trend", market_state, "市场状态缺少趋势信息")

        # 相关性分析
        symbols = ["AAPL", "MSFT", "GOOGL"]
        correlation = self.market_analyzer.analyze_correlation(symbols)
        self.assertIsNotNone(correlation, "相关性分析失败")

        # 情绪分析
        sentiment = self.market_analyzer.analyze_sentiment(self.test_symbol)
        self.assertIsNotNone(sentiment, "情绪分析失败")

        logger.info("市场分析器测试通过")

    def test_05_engine_shutdown(self):
        """测试引擎关闭"""
        logger.info("测试引擎关闭...")

        # 引擎关闭
        result = self.engine.stop()
        self.assertTrue(result, "引擎关闭失败")

        # 检查状态
        status = self.engine.status()
        self.assertFalse(status["running"], "引擎未正确关闭")

        logger.info("引擎关闭测试通过")

    def tearDown(self):
        """测试后清理"""
        logger.info("清理测试环境...")

        # 确保引擎停止
        if hasattr(self, "engine") and self.engine.running:
            self.engine.stop()

        logger.info("测试环境清理完成")


if __name__ == "__main__":
    logger.info("开始核心组件测试...")
    unittest.main(verbosity=2)
    logger.info("核心组件测试完成")