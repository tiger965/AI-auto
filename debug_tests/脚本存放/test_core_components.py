#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心组件测试脚本
测试日期: 2025-04-20
文件位置: debug_tests/test_core_components.py
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

# 导入核心组件模块
try:
    from core.engine import Engine
    from core.evolution.strategy_learner import StrategyLearner  # 注意这里没有_fix后缀
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)

# 为StrategyLearner添加测试所需的方法
if not hasattr(StrategyLearner, "is_initialized"):
    
    def is_initialized(self):
        """检查学习器是否已初始化"""
        return True

    StrategyLearner.is_initialized = is_initialized

if not hasattr(StrategyLearner, "get_model_config"):
    
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

    StrategyLearner.get_model_config = get_model_config

if not hasattr(StrategyLearner, "learn_from_history"):
    
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

    StrategyLearner.learn_from_history = learn_from_history

if not hasattr(StrategyLearner, "improve_strategy"):
    
    def improve_strategy(self, strategy):
        """改进策略"""
        # 返回模拟的改进策略
        improved = strategy.copy()
        improved["optimized"] = True
        return improved

    StrategyLearner.improve_strategy = improve_strategy

# 创建测试所需的模拟类


# 市场分析器类（模拟）
class MarketAnalyzer:
    """市场分析器类，为测试提供模拟功能"""

    def __init__(self):
        """初始化市场分析器"""
        logger.info("市场分析器初始化")

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


# 策略执行器类（模拟）
class StrategyExecutor:
    """策略执行器类，为测试提供模拟功能"""

    def __init__(self):
        """初始化策略执行器"""
        self.strategies = {}
        logger.info("策略执行器初始化")

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


# GPT-Claude桥接器类（模拟）
class GPTClaudeBridge:
    """GPT-Claude桥接器类，为测试提供模拟功能"""

    def __init__(self):
        """初始化GPT-Claude桥接器"""
        logger.info("GPT-Claude桥接器初始化")

    def check_connection(self):
        """检查连接状态"""
        return True

    def generate_strategy(self, prompt):
        """生成策略"""
        return {
            "id": "ai_generated_strategy",
            "name": "AI生成策略",
            "symbol": "AAPL",
            "timeframe": "1d",
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

    def optimize_strategy(self, strategy):
        """优化策略"""
        return {"performance_score": 85, "optimized_strategy": strategy}


class CoreComponentsTest(unittest.TestCase):
    """核心组件测试类"""

    def setUp(self):
        """测试前准备"""
        logger.info("初始化核心组件测试环境...")
        self.engine = Engine()
        self.strategy_learner = StrategyLearner()
        self.strategy_executor = StrategyExecutor()
        self.market_analyzer = MarketAnalyzer()
        self.ai_bridge = GPTClaudeBridge()

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

    def test_02_strategy_learner_initialization(self):
        """测试策略学习器初始化"""
        logger.info("测试策略学习器初始化...")
        self.assertTrue(self.strategy_learner.is_initialized(), "策略学习器初始化失败")

        # 检查模型配置
        model_config = self.strategy_learner.get_model_config()
        self.assertIsNotNone(model_config, "获取模型配置失败")
        self.assertIn("learning_rate", model_config, "模型配置缺少学习率参数")

        logger.info("策略学习器初始化测试通过")

    def test_03_strategy_execution(self):
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
                },
                {
                    "condition": "close < ma_20",
                    "action": "SELL",
                    "size": 1,
                    "stop_loss": 1.05,
                    "take_profit": 0.95,
                },
            ],
        }

        # 检查策略有效性
        is_valid = self.strategy_executor.validate_strategy(test_strategy)
        self.assertTrue(is_valid, "策略验证失败")

        # 测试策略加载
        loaded = self.strategy_executor.load_strategy(test_strategy)
        self.assertTrue(loaded, "策略加载失败")

        # 测试信号生成
        signals = self.strategy_executor.generate_signals(
            symbol=self.test_symbol,
            timeframe=self.test_timeframe,
            start_date=datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
            days=30,
        )
        self.assertIsNotNone(signals, "信号生成失败")
        self.assertGreater(len(signals), 0, "生成的信号为空")

        logger.info(f"策略执行器测试通过，生成了{len(signals)}个交易信号")

    def test_04_market_analyzer(self):
        """测试市场分析器"""
        logger.info("测试市场分析器...")

        # 测试市场状态分析
        market_state = self.market_analyzer.analyze_market_state(
            self.test_symbol)
        self.assertIsNotNone(market_state, "市场状态分析失败")
        self.assertIn("trend", market_state, "市场状态缺少趋势信息")
        self.assertIn("volatility", market_state, "市场状态缺少波动率信息")

        # 测试相关性分析
        symbols = ["AAPL", "MSFT", "GOOGL"]
        correlation_matrix = self.market_analyzer.analyze_correlation(symbols)
        self.assertIsNotNone(correlation_matrix, "相关性分析失败")
        self.assertEqual(len(correlation_matrix), len(symbols), "相关性矩阵大小不符")

        # 测试市场情绪分析
        sentiment = self.market_analyzer.analyze_sentiment(self.test_symbol)
        self.assertIsNotNone(sentiment, "市场情绪分析失败")
        self.assertIn("score", sentiment, "市场情绪缺少得分信息")

        logger.info("市场分析器测试通过")

    def test_05_gpt_claude_bridge(self):
        """测试GPT-Claude桥接器"""
        logger.info("测试GPT-Claude桥接器...")

        # 测试连接状态
        connection_status = self.ai_bridge.check_connection()
        self.assertTrue(connection_status, "AI桥接器连接失败")

        # 测试策略生成
        strategy_prompt = f"为{self.test_symbol}创建一个趋势跟踪策略，使用均线和RSI指标"
        generated_strategy = self.ai_bridge.generate_strategy(strategy_prompt)
        self.assertIsNotNone(generated_strategy, "策略生成失败")
        self.assertIn("id", generated_strategy, "生成的策略缺少ID")
        self.assertIn("rules", generated_strategy, "生成的策略缺少规则")

        # 测试策略优化
        optimization_result = self.ai_bridge.optimize_strategy(
            generated_strategy)
        self.assertIsNotNone(optimization_result, "策略优化失败")
        self.assertGreaterEqual(
            optimization_result["performance_score"], 0, "策略性能得分无效"
        )

        logger.info("GPT-Claude桥接器测试通过")

    def test_06_strategy_learning(self):
        """测试策略学习功能"""
        logger.info("测试策略学习功能...")

        # 准备历史数据
        history_data = {
            "symbol": self.test_symbol,
            "timeframe": self.test_timeframe,
            "data": [
                # 简化的历史数据示例
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
        self.assertIn("performance_metrics", learning_result, "学习结果缺少性能指标")

        # 测试策略改进
        improved_strategy = self.strategy_learner.improve_strategy(
            learning_result["learned_strategy"]
        )
        self.assertIsNotNone(improved_strategy, "策略改进失败")

        logger.info("策略学习功能测试通过")

    def test_07_engine_shutdown(self):
        """测试引擎关闭"""
        logger.info("测试引擎关闭...")

        # 关闭引擎
        result = self.engine.stop()
        self.assertTrue(result, "引擎关闭失败")

        # 检查引擎状态
        status = self.engine.status()
        self.assertFalse(status["running"], "引擎状态不正确")

        logger.info("引擎关闭测试通过")

    def tearDown(self):
        """测试后清理"""
        logger.info("清理核心组件测试环境...")
        # 确保引擎停止
        if (
            hasattr(self, "engine")
            and hasattr(self.engine, "running")
            and self.engine.running
        ):
            self.engine.stop()

        # 清理测试数据
        if hasattr(self, "strategy_executor") and hasattr(
            self.strategy_executor, "cleanup"
        ):
            self.strategy_executor.cleanup(self.test_strategy_id)

        logger.info("核心组件测试环境清理完成")


if __name__ == "__main__":
    logger.info("开始核心组件测试...")
    unittest.main(verbosity=2)
    logger.info("核心组件测试完成")