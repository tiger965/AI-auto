"""
模块名称：gpt_claude
功能描述：GPT-Claude通信系统，实现GPT和Claude之间的通信协议和反馈机制
版本：1.0
创建日期：2025-04-20
作者：开发窗口9.6
"""

from .communication import GptCommunicator, ClaudeCommunicator, CommunicationManager
from .feedback_system import FeedbackAnalyzer, FeedbackCollector, PerformanceEvaluator
from .templates.strategy_templates import StrategyTemplate, StrategyTemplateManager

__all__ = [
    "GptCommunicator",
    "ClaudeCommunicator",
    "CommunicationManager",
    "FeedbackAnalyzer",
    "FeedbackCollector",
    "PerformanceEvaluator",
    "StrategyTemplate",
    "StrategyTemplateManager",
]