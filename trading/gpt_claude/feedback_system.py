""" "
模块名称：feedback_system
功能描述：实现交易策略的反馈分析和性能评估系统，提供策略改进机制
版本：1.0
创建日期：2025-04-20
作者：开发窗口9.6
"""

import json
import logging
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import config.paths as pd
import modules.nlp as np

# 配置日志
logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    反馈收集器，收集和存储策略执行的反馈数据
    """

    def __init__(self, storage_path: str = None):
        """
        初始化反馈收集器

        参数:
            storage_path (str, optional): 反馈数据存储路径
        """
        self.storage_path = storage_path or "data/feedback"
        self.feedback_data = []

    def add_execution_feedback(
        self, execution_result: Dict[str, Any], market_data: Dict[str, Any]
    ) -> str:
        """
        添加策略执行的反馈

        参数:
            execution_result (Dict[str, Any]): 策略执行结果
            market_data (Dict[str, Any]): 执行时的市场数据

        返回:
            str: 反馈ID
        """
        feedback_id = f"fb-{int(time.time())}-{len(self.feedback_data)}"

        feedback_entry = {
            "feedback_id": feedback_id,
            "timestamp": time.time(),
            "execution_result": execution_result,
            "market_data": market_data,
            "execution_time": execution_result.get("execution_time", 0),
            "strategy_ids": self._extract_strategy_ids(execution_result),
        }

        self.feedback_data.append(feedback_entry)
        self._save_feedback(feedback_entry)

        return feedback_id

    def add_performance_feedback(
        self, feedback_id: str, performance_data: Dict[str, Any]
    ) -> None:
        """
        添加策略执行后的性能反馈

        参数:
            feedback_id (str): 反馈ID
            performance_data (Dict[str, Any]): 性能数据
        """
        for entry in self.feedback_data:
            if entry["feedback_id"] == feedback_id:
                entry["performance_data"] = performance_data
                entry["updated_at"] = time.time()
                self._save_feedback(entry)
                logger.info(f"已添加性能反馈数据到 {feedback_id}")
                break
        else:
            logger.warning(f"无法找到反馈ID: {feedback_id}")

    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定ID的反馈

        参数:
            feedback_id (str): 反馈ID

        返回:
            Optional[Dict[str, Any]]: 反馈数据，如果不存在则返回None
        """
        for entry in self.feedback_data:
            if entry["feedback_id"] == feedback_id:
                return entry

        # 尝试从存储中加载
        try:
            import os
            import json

            file_path = os.path.join(self.storage_path, f"{feedback_id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载反馈数据失败: {str(e)}")

        return None

    def get_strategy_feedback(
        self, strategy_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取指定策略的反馈数据

        参数:
            strategy_id (str): 策略ID
            limit (int): 返回的最大记录数，默认为10

        返回:
            List[Dict[str, Any]]: 反馈数据列表
        """
        results = []

        for entry in sorted(
            self.feedback_data, key=lambda x: x["timestamp"], reverse=True
        ):
            if strategy_id in entry.get("strategy_ids", []):
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def _extract_strategy_ids(self, execution_result: Dict[str, Any]) -> List[str]:
        """
        从执行结果中提取策略ID

        参数:
            execution_result (Dict[str, Any]): 执行结果

        返回:
            List[str]: 策略ID列表
        """
        strategy_ids = []

        # 从执行结果中提取策略ID
        if "strategies_executed" in execution_result:
            strategies = execution_result["strategies_executed"]
            if isinstance(strategies, list):
                for strategy in strategies:
                    if isinstance(strategy, dict) and "id" in strategy:
                        strategy_ids.append(strategy["id"])
                    elif isinstance(strategy, str):
                        strategy_ids.append(strategy)

        return strategy_ids

    def _save_feedback(self, feedback_entry: Dict[str, Any]) -> None:
        """
        保存反馈数据到存储

        参数:
            feedback_entry (Dict[str, Any]): 反馈数据条目
        """
        try:
            import os
            import json

            # 确保存储目录存在
            os.makedirs(self.storage_path, exist_ok=True)

            # 保存反馈数据
            file_path = os.path.join(
                self.storage_path, f"{feedback_entry['feedback_id']}.json"
            )
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(feedback_entry, f, ensure_ascii=False, indent=2)

            logger.info(f"反馈数据已保存到 {file_path}")
        except Exception as e:
            logger.error(f"保存反馈数据失败: {str(e)}")


class PerformanceEvaluator:
    """
    性能评估器，评估策略执行的性能
    """

    def __init__(self):
        """
        初始化性能评估器
        """
        pass

    def evaluate_execution(
        self, execution_result: Dict[str, Any], market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估策略执行的性能

        参数:
            execution_result (Dict[str, Any]): 策略执行结果
            market_data (Dict[str, Any]): 执行时的市场数据

        返回:
            Dict[str, Any]: 性能评估结果
        """
        try:
            # 提取执行细节
            execution_details = execution_result.get("execution_details", {})

            # 计算基本指标
            execution_time = execution_result.get("execution_time", 0)
            success_rate = self._calculate_success_rate(execution_details)

            # 分析交易操作
            trade_analysis = self._analyze_trades(execution_details)

            # 策略执行质量评分
            quality_score = self._calculate_quality_score(
                execution_time, success_rate, trade_analysis
            )

            return {
                "timestamp": time.time(),
                "execution_time": execution_time,
                "success_rate": success_rate,
                "trade_analysis": trade_analysis,
                "quality_score": quality_score,
                "evaluation_summary": self._generate_summary(
                    quality_score, success_rate, trade_analysis
                ),
            }
        except Exception as e:
            logger.error(f"性能评估失败: {str(e)}")
            return {
                "timestamp": time.time(),
                "error": str(e),
                "quality_score": 0,
                "evaluation_summary": "性能评估失败",
            }

    def _calculate_success_rate(self, execution_details: Dict[str, Any]) -> float:
        """
        计算策略执行的成功率

        参数:
            execution_details (Dict[str, Any]): 执行细节

        返回:
            float: 成功率，范围为0-1
        """
        operations = execution_details.get("operations", [])
        if not operations:
            return 0.0

        successful = sum(
            1 for op in operations if op.get("status") == "success")
        return successful / len(operations)

    def _analyze_trades(self, execution_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析交易操作

        参数:
            execution_details (Dict[str, Any]): 执行细节

        返回:
            Dict[str, Any]: 交易分析结果
        """
        operations = execution_details.get("operations", [])
        trades = [op for op in operations if op.get("type") in ["buy", "sell"]]

        if not trades:
            return {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "average_trade_size": 0,
                "trade_interval": 0,
            }

        # 计算买卖操作数量
        buy_trades = sum(1 for trade in trades if trade.get("type") == "buy")
        sell_trades = sum(1 for trade in trades if trade.get("type") == "sell")

        # 计算平均交易大小
        total_volume = sum(trade.get("volume", 0) for trade in trades)
        average_trade_size = total_volume / len(trades)

        # 计算交易间隔
        if len(trades) > 1:
            timestamps = sorted([trade.get("timestamp", 0)
                                for trade in trades])
            intervals = [
                timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)
            ]
            average_interval = sum(intervals) / len(intervals)
        else:
            average_interval = 0

        return {
            "total_trades": len(trades),
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "average_trade_size": average_trade_size,
            "trade_interval": average_interval,
        }

    def _calculate_quality_score(
        self, execution_time: float, success_rate: float, trade_analysis: Dict[str, Any]
    ) -> float:
        """
        计算策略执行质量评分

        参数:
            execution_time (float): 执行时间
            success_rate (float): 成功率
            trade_analysis (Dict[str, Any]): 交易分析结果

        返回:
            float: 质量评分，范围为0-100
        """
        # 分配权重
        weights = {"success_rate": 0.6,
                   "execution_time": 0.2, "trade_balance": 0.2}

        # 计算执行时间得分（越快越好，最长容忍10秒）
        time_score = max(0, 1 - (execution_time / 10))

        # 计算交易平衡得分（买卖平衡更好）
        buy_trades = trade_analysis.get("buy_trades", 0)
        sell_trades = trade_analysis.get("sell_trades", 0)
        if buy_trades + sell_trades > 0:
            trade_balance = (
                min(buy_trades, sell_trades) / max(buy_trades, sell_trades)
                if max(buy_trades, sell_trades) > 0
                else 1
            )
        else:
            trade_balance = 0

        # 计算总分
        total_score = (
            weights["success_rate"] * success_rate
            + weights["execution_time"] * time_score
            + weights["trade_balance"] * trade_balance
        ) * 100

        return round(total_score, 2)

    def _generate_summary(
        self, quality_score: float, success_rate: float, trade_analysis: Dict[str, Any]
    ) -> str:
        """
        生成评估摘要

        参数:
            quality_score (float): 质量评分
            success_rate (float): 成功率
            trade_analysis (Dict[str, Any]): 交易分析结果

        返回:
            str: 评估摘要
        """
        total_trades = trade_analysis.get("total_trades", 0)

        if quality_score >= 90:
            return (
                f"优秀的策略执行，成功率{success_rate:.2%}，共执行{total_trades}笔交易"
            )
        elif quality_score >= 70:
            return (
                f"良好的策略执行，成功率{success_rate:.2%}，共执行{total_trades}笔交易"
            )
        elif quality_score >= 50:
            return (
                f"一般的策略执行，成功率{success_rate:.2%}，共执行{total_trades}笔交易"
            )
        else:
            return f"较差的策略执行，成功率{success_rate:.2%}，共执行{total_trades}笔交易，需要改进"


class FeedbackAnalyzer:
    """
    反馈分析器，分析策略执行反馈并生成改进建议
    """

    def __init__(self, feedback_collector: FeedbackCollector):
        """
        初始化反馈分析器

        参数:
            feedback_collector (FeedbackCollector): 反馈收集器实例
        """
        self.feedback_collector = feedback_collector

    def analyze_strategy_performance(
        self, strategy_id: str, lookback_days: int = 7
    ) -> Dict[str, Any]:
        """
        分析策略的历史表现

        参数:
            strategy_id (str): 策略ID
            lookback_days (int): 回溯天数，默认为7

        返回:
            Dict[str, Any]: 策略表现分析结果
        """
        # 获取策略的历史反馈数据
        feedback_data = self.feedback_collector.get_strategy_feedback(
            strategy_id, limit=100
        )

        # 如果没有反馈数据，返回空结果
        if not feedback_data:
            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "status": "no_data",
                "message": f"没有找到策略 {strategy_id} 的反馈数据",
            }

        # 过滤最近N天的数据
        cutoff_time = time.time() - (lookback_days * 86400)
        recent_feedback = [
            fb
            for fb in feedback_data
            if fb["timestamp"] >= cutoff_time and "performance_data" in fb
        ]

        if not recent_feedback:
            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "status": "no_recent_data",
                "message": f"没有找到策略 {strategy_id} 最近 {lookback_days} 天的性能数据",
            }

        try:
            # 提取性能指标
            quality_scores = [
                fb["performance_data"].get("quality_score", 0) for fb in recent_feedback
            ]
            success_rates = [
                fb["performance_data"].get("success_rate", 0) for fb in recent_feedback
            ]
            execution_times = [
                fb["performance_data"].get("execution_time", 0)
                for fb in recent_feedback
            ]

            # 计算统计数据
            avg_quality = sum(quality_scores) / len(quality_scores)
            avg_success_rate = sum(success_rates) / len(success_rates)
            avg_execution_time = sum(execution_times) / len(execution_times)

            # 评估性能趋势
            trend = self._evaluate_trend(quality_scores)

            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                avg_quality, avg_success_rate, recent_feedback
            )

            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "analysis_period": f"{lookback_days} days",
                "execution_count": len(recent_feedback),
                "performance_stats": {
                    "avg_quality_score": round(avg_quality, 2),
                    "avg_success_rate": round(avg_success_rate, 4),
                    "avg_execution_time": round(avg_execution_time, 4),
                    "min_quality_score": min(quality_scores),
                    "max_quality_score": max(quality_scores),
                },
                "trend": trend,
                "improvement_suggestions": improvement_suggestions,
            }
        except Exception as e:
            logger.error(f"分析策略性能失败: {str(e)}")
            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "status": "error",
                "message": f"分析失败: {str(e)}",
            }

    def generate_learning_feedback(self, strategy_id: str) -> Dict[str, Any]:
        """
        生成学习反馈，用于策略的自我改进

        参数:
            strategy_id (str): 策略ID

        返回:
            Dict[str, Any]: 学习反馈
        """
        # 分析策略性能
        performance_analysis = self.analyze_strategy_performance(strategy_id)

        if performance_analysis.get("status") in ["no_data", "no_recent_data", "error"]:
            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "learning_feedback": "没有足够的数据生成学习反馈",
                "status": performance_analysis.get("status"),
            }

        # 获取最近的反馈数据用于详细分析
        recent_feedback = self.feedback_collector.get_strategy_feedback(
            strategy_id, limit=3
        )
        recent_executions = [
            fb.get("execution_result", {})
            for fb in recent_feedback
            if "execution_result" in fb
        ]

        # 生成学习反馈
        try:
            learning_points = []

            # 从性能统计中获取反馈
            perf_stats = performance_analysis.get("performance_stats", {})
            avg_quality = perf_stats.get("avg_quality_score", 0)

            if avg_quality < 50:
                learning_points.append(
                    {
                        "type": "warning",
                        "aspect": "overall_performance",
                        "message": "策略整体表现较差，需要全面优化",
                    }
                )

            # 从执行细节中提取学习点
            for execution in recent_executions:
                details = execution.get("execution_details", {})
                warnings = execution.get("warnings", [])

                # 分析警告
                for warning in warnings:
                    learning_points.append(
                        {
                            "type": "warning",
                            "aspect": "execution_warning",
                            "message": warning,
                        }
                    )

                # 分析操作
                operations = details.get("operations", [])
                failed_ops = [op for op in operations if op.get(
                    "status") != "success"]

                for op in failed_ops:
                    learning_points.append(
                        {
                            "type": "error",
                            "aspect": "failed_operation",
                            "operation_type": op.get("type"),
                            "message": op.get("error", "操作失败"),
                        }
                    )

            # 提取改进建议
            improvement_suggestions = performance_analysis.get(
                "improvement_suggestions", []
            )
            for suggestion in improvement_suggestions:
                learning_points.append(
                    {
                        "type": "suggestion",
                        "aspect": suggestion.get("aspect"),
                        "message": suggestion.get("suggestion"),
                    }
                )

            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "performance_summary": {
                    "avg_quality_score": perf_stats.get("avg_quality_score", 0),
                    "avg_success_rate": perf_stats.get("avg_success_rate", 0),
                    "trend": performance_analysis.get("trend"),
                },
                "learning_points": learning_points,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"生成学习反馈失败: {str(e)}")
            return {
                "strategy_id": strategy_id,
                "timestamp": time.time(),
                "learning_feedback": f"生成学习反馈失败: {str(e)}",
                "status": "error",
            }

    def _evaluate_trend(self, quality_scores: List[float]) -> str:
        """
        评估性能趋势

        参数:
            quality_scores (List[float]): 质量评分列表

        返回:
            str: 趋势评估结果
        """
        if len(quality_scores) < 2:
            return "insufficient_data"

        # 简单线性趋势
        x = list(range(len(quality_scores)))
        y = quality_scores

        if len(x) == len(y) and len(x) > 1:
            n = len(x)
            xy = sum(x[i] * y[i] for i in range(n))
            x_sum = sum(x)
            y_sum = sum(y)
            x_squared = sum(xi * xi for xi in x)

            slope = (n * xy - x_sum * y_sum) / (n * x_squared - x_sum * x_sum)

            # 评估趋势
            if slope > 0.5:
                return "strongly_improving"
            elif slope > 0.1:
                return "improving"
            elif slope < -0.5:
                return "strongly_declining"
            elif slope < -0.1:
                return "declining"
            else:
                return "stable"
        else:
            return "error"

    def _generate_improvement_suggestions(
        self,
        avg_quality: float,
        avg_success_rate: float,
        feedback_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        生成改进建议

        参数:
            avg_quality (float): 平均质量评分
            avg_success_rate (float): 平均成功率
            feedback_data (List[Dict[str, Any]]): 反馈数据列表

        返回:
            List[Dict[str, Any]]: 改进建议列表
        """
        suggestions = []

        # 基于质量评分的建议
        if avg_quality < 50:
            suggestions.append(
                {
                    "aspect": "overall_quality",
                    "suggestion": "策略质量评分较低，建议全面审查策略逻辑和参数",
                }
            )

        # 基于成功率的建议
        if avg_success_rate < 0.7:
            suggestions.append(
                {
                    "aspect": "success_rate",
                    "suggestion": "策略执行成功率较低，建议检查错误处理和异常情况",
                }
            )

        # 分析常见的执行问题
        error_counts = {}
        for fb in feedback_data:
            execution = fb.get("execution_result", {})
            for warning in execution.get("warnings", []):
                error_counts[warning] = error_counts.get(warning, 0) + 1

            for op in execution.get("execution_details", {}).get("operations", []):
                if op.get("status") != "success" and "error" in op:
                    error_counts[op["error"]] = error_counts.get(
                        op["error"], 0) + 1

        # 找出最常见的错误
        if error_counts:
            common_errors = sorted(
                error_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
            for error, count in common_errors:
                suggestions.append(
                    {
                        "aspect": "common_error",
                        "suggestion": f"频繁出现错误 ({count}次): {error}，建议重点解决此问题",
                    }
                )

        # 如果没有问题，也给出积极反馈
        if not suggestions and avg_quality >= 80:
            suggestions.append(
                {
                    "aspect": "positive_feedback",
                    "suggestion": "策略表现良好，可以考虑增加资金分配或扩大应用范围",
                }
            )

        return suggestions