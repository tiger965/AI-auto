"""
模块名称：example_usage
功能描述：GPT-Claude通信系统的使用示例
版本：1.0
创建日期：2025-04-20
作者：开发窗口9.6
"""

from trading.gpt_claude.templates.strategy_templates import StrategyTemplateManager
from trading.gpt_claude.feedback_system import (
    FeedbackCollector,
    PerformanceEvaluator,
    FeedbackAnalyzer,
)
from trading.gpt_claude.communication import (
    GptCommunicator,
    ClaudeCommunicator,
    CommunicationManager,
)
import json
import logging
import os
import time
from typing import Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 导入GPT-Claude通信模块


def main():
    """
    主函数，演示GPT-Claude通信系统的基本用法
    """
    logger.info("开始GPT-Claude通信系统示例")

    # 创建数据目录
    os.makedirs("data/templates", exist_ok=True)
    os.makedirs("data/feedback", exist_ok=True)

    # 初始化模板管理器
    template_manager = StrategyTemplateManager(templates_dir="data/templates")
    template_manager.load_default_templates()

    # 列出可用模板
    templates = template_manager.list_templates()
    logger.info(f"可用模板: {json.dumps(templates, ensure_ascii=False, indent=2)}")

    # 初始化通信组件
    # 注意：以下API密钥仅为示例，实际使用时应从配置文件或环境变量获取
    gpt_communicator = GptCommunicator(
        api_key="YOUR_GPT_API_KEY", model="gpt-4o")

    claude_communicator = ClaudeCommunicator(
        api_key="YOUR_CLAUDE_API_KEY", model="claude-3-sonnet-20240229"
    )

    # 初始化通信管理器
    comm_manager = CommunicationManager(
        gpt_communicator=gpt_communicator, claude_communicator=claude_communicator
    )

    # 初始化反馈系统
    feedback_collector = FeedbackCollector(storage_path="data/feedback")
    performance_evaluator = PerformanceEvaluator()
    feedback_analyzer = FeedbackAnalyzer(feedback_collector)

    # 示例：从模板创建策略
    try:
        strategy_info = template_manager.create_strategy_from_template(
            template_id="basic_strategy",
            strategy_name="简单MACD策略",
            strategy_params={
                "description": "基于MACD交叉的简单交易策略",
                "timeframe": "1h",
                "risk_level": "medium",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "entry_condition": "macd_cross",
                "exit_condition": "macd_cross_down",
                "profit_target": 0.05,
                "stop_loss": 0.02,
            },
        )

        logger.info(f"成功创建策略: {strategy_info['strategy_id']}")
    except Exception as e:
        logger.error(f"创建策略失败: {str(e)}")

    # 示例：生成GPT提示
    market_data = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "recent_prices": {
            "open": [45000, 45100, 45200, 45300, 45400],
            "high": [45200, 45300, 45400, 45500, 45600],
            "low": [44800, 44900, 45000, 45100, 45200],
            "close": [45100, 45200, 45300, 45400, 45500],
            "volume": [100, 120, 110, 130, 140],
        },
        "market_indicators": {
            "volatility": "medium",
            "trend": "upward",
            "market_type": "trending",
        },
    }

    config = {
        "available_strategies": ["MACD交叉", "RSI反转", "趋势跟踪"],
        "risk_profile": "medium",
        "time_horizon": "medium",
        "constraints": {"max_strategies": 2, "max_allocation_per_strategy": 0.5},
        "gpt_temperature": 0.2,
        "claude_temperature": 0.2,
        "claude_max_tokens": 4000,
    }

    prompt = template_manager.create_prompt_for_gpt(
        task_type="strategy_generation", market_data=market_data, config=config
    )

    logger.info(f"GPT提示示例:\n{prompt}")

    # 注意：以下代码在实际环境中需要API密钥才能运行
    # 这里仅为演示，不执行实际的API调用

    logger.info("模拟执行交易工作流...")
    logger.info("注意：由于没有提供实际API密钥，以下操作仅为演示逻辑流程")

    # 模拟执行结果
    mock_execution_result = {
        "execution_id": f"exec-{int(time.time())}",
        "strategies_executed": [{"id": "strategy-123", "name": "MACD交叉策略"}],
        "execution_details": {
            "operations": [
                {
                    "type": "buy",
                    "status": "success",
                    "timestamp": time.time(),
                    "volume": 0.1,
                },
                {
                    "type": "sell",
                    "status": "success",
                    "timestamp": time.time() + 3600,
                    "volume": 0.1,
                },
            ]
        },
        "performance_metrics": {"profit_loss": 0.03, "execution_time": 0.5},
        "validation_results": "passed",
        "warnings": [],
        "execution_time": 0.5,
    }

    # 演示性能评估
    performance_result = performance_evaluator.evaluate_execution(
        mock_execution_result, market_data
    )

    logger.info(
        f"性能评估结果: {json.dumps(performance_result, ensure_ascii=False, indent=2)}"
    )

    # 演示反馈收集
    feedback_id = feedback_collector.add_execution_feedback(
        mock_execution_result, market_data
    )

    feedback_collector.add_performance_feedback(
        feedback_id, performance_result)

    logger.info(f"已添加反馈，ID: {feedback_id}")

    # 演示反馈分析
    strategy_id = "strategy-123"
    learning_feedback = feedback_analyzer.generate_learning_feedback(
        strategy_id)

    logger.info(
        f"学习反馈: {json.dumps(learning_feedback, ensure_ascii=False, indent=2)}"
    )

    logger.info("GPT-Claude通信系统示例完成")


if __name__ == "__main__":
    main()