"""
trading/optimization/strategy_learner.py
功能描述: 实现策略自学习和进化系统，分析策略性能并生成改进建议
版本: 1.0.0
创建日期: 2025-04-20
"""

import json
import logging
import time
import modules.nlp as np
import config.paths as pd
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import random
import os
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("strategy_learner")

# 全局常量
DEFAULT_STORAGE_PATH = os.path.join(
    os.path.dirname(__file__), "../data/learner")
MAX_HISTORY_VERSIONS = 10
DEFAULT_EVOLUTION_PARAMS = {
    "population_size": 20,
    "generations": 5,
    "mutation_rate": 0.2,
    "crossover_rate": 0.7,
}
DEFAULT_METRICS = [
    "total_return",
    "sharpe_ratio",
    "max_drawdown",
    "win_rate",
    "profit_factor",
    "avg_trade_duration",
]

# 学习器状态
LEARNER_STATUS = {
    "initialized": False,
    "config": None,
    "models": {},
    "strategy_history": {},
    "performance_cache": {},
    "last_error": None,
}


class LearnerInitError(Exception):
    """学习器初始化异常"""

    pass


class StrategyEvolutionError(Exception):
    """策略进化异常"""

    pass


def initialize_learner(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    初始化学习系统

    Args:
        config (Optional[Dict[str, Any]], optional): 配置参数. Defaults to None.

    Returns:
        bool: 初始化是否成功
    """
    global LEARNER_STATUS

    if config is None:
        # 使用默认配置
        config = {
            "storage_path": DEFAULT_STORAGE_PATH,
            "max_history_versions": MAX_HISTORY_VERSIONS,
            "metrics": DEFAULT_METRICS,
            "primary_metric": "sharpe_ratio",
            "evolution_params": DEFAULT_EVOLUTION_PARAMS,
            "use_ml_models": True,
            "backtest_lookback_days": 365,
        }

    try:
        # 创建存储目录
        os.makedirs(config["storage_path"], exist_ok=True)

        # 加载现有模型和历史数据（如果存在）
        models_path = os.path.join(config["storage_path"], "models.pkl")
        history_path = os.path.join(
            config["storage_path"], "strategy_history.json")
        performance_path = os.path.join(
            config["storage_path"], "performance_cache.json"
        )

        if os.path.exists(models_path):
            with open(models_path, "rb") as f:
                LEARNER_STATUS["models"] = pickle.load(f)

        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                LEARNER_STATUS["strategy_history"] = json.load(f)

        if os.path.exists(performance_path):
            with open(performance_path, "r") as f:
                LEARNER_STATUS["performance_cache"] = json.load(f)

        # 更新状态
        LEARNER_STATUS["initialized"] = True
        LEARNER_STATUS["config"] = config
        LEARNER_STATUS["last_error"] = None

        logger.info("Strategy learner initialized successfully")
        return True

    except Exception as e:
        LEARNER_STATUS["initialized"] = False
        LEARNER_STATUS["last_error"] = str(e)
        logger.error(f"Failed to initialize learner: {str(e)}")
        return False


def _save_learner_state() -> bool:
    """
    保存学习器状态到磁盘

    Returns:
        bool: 是否成功保存
    """
    if not LEARNER_STATUS["initialized"]:
        return False

    try:
        config = LEARNER_STATUS["config"]

        # 保存模型
        models_path = os.path.join(config["storage_path"], "models.pkl")
        with open(models_path, "wb") as f:
            pickle.dump(LEARNER_STATUS["models"], f)

        # 保存策略历史
        history_path = os.path.join(
            config["storage_path"], "strategy_history.json")
        with open(history_path, "w") as f:
            json.dump(LEARNER_STATUS["strategy_history"], f, indent=2)

        # 保存性能缓存
        performance_path = os.path.join(
            config["storage_path"], "performance_cache.json"
        )
        with open(performance_path, "w") as f:
            json.dump(LEARNER_STATUS["performance_cache"], f, indent=2)

        return True

    except Exception as e:
        logger.error(f"Failed to save learner state: {str(e)}")
        return False


def _calculate_performance_metrics(
    performance_data: Dict[str, Any],
) -> Dict[str, float]:
    """
    计算策略性能指标

    Args:
        performance_data (Dict[str, Any]): 性能数据

    Returns:
        Dict[str, float]: 计算的性能指标
    """
    metrics = {}

    # 提取交易数据
    trades = performance_data.get("trades", [])
    equity_curve = performance_data.get("equity_curve", [])

    if not trades or not equity_curve:
        logger.warning("Insufficient performance data for calculating metrics")
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_trade_duration": 0.0,
        }

    # 计算总回报率
    initial_equity = equity_curve[0]["equity"] if equity_curve else 1000.0
    final_equity = equity_curve[-1]["equity"] if equity_curve else 1000.0
    metrics["total_return"] = (final_equity - initial_equity) / initial_equity

    # 计算夏普比率
    if len(equity_curve) > 1:
        daily_returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i - 1]["equity"]
            curr_equity = equity_curve[i]["equity"]
            daily_return = (curr_equity - prev_equity) / prev_equity
            daily_returns.append(daily_return)

        avg_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)

        # 年化夏普比率 (假设日数据)
        risk_free_rate = 0.02 / 252  # 假设无风险利率2%
        metrics["sharpe_ratio"] = (
            (avg_return - risk_free_rate) / std_return * np.sqrt(252)
            if std_return > 0
            else 0
        )
    else:
        metrics["sharpe_ratio"] = 0.0

    # 计算最大回撤
    max_equity = initial_equity
    max_drawdown = 0.0

    for point in equity_curve:
        current_equity = point["equity"]
        max_equity = max(max_equity, current_equity)
        drawdown = (max_equity - current_equity) / max_equity
        max_drawdown = max(max_drawdown, drawdown)

    metrics["max_drawdown"] = max_drawdown

    # 计算胜率
    if trades:
        winning_trades = sum(
            1 for trade in trades if trade.get("profit", 0) > 0)
        metrics["win_rate"] = winning_trades / len(trades)
    else:
        metrics["win_rate"] = 0.0

    # 计算盈亏比
    total_profit = sum(
        trade.get("profit", 0) for trade in trades if trade.get("profit", 0) > 0
    )
    total_loss = abs(
        sum(trade.get("profit", 0)
            for trade in trades if trade.get("profit", 0) < 0)
    )
    metrics["profit_factor"] = total_profit / \
        total_loss if total_loss > 0 else 0.0

    # 计算平均交易持续时间
    if trades:
        durations = []
        for trade in trades:
            if "entry_time" in trade and "exit_time" in trade:
                entry_time = datetime.fromisoformat(trade["entry_time"])
                exit_time = datetime.fromisoformat(trade["exit_time"])
                duration = (
                    exit_time - entry_time).total_seconds() / 3600  # 小时
                durations.append(duration)

        metrics["avg_trade_duration"] = np.mean(
            durations) if durations else 0.0
    else:
        metrics["avg_trade_duration"] = 0.0

    return metrics


def _extract_strategy_features(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    从策略定义中提取用于学习的特征

    Args:
        strategy (Dict[str, Any]): 策略定义

    Returns:
        Dict[str, Any]: 提取的特征
    """
    features = {}

    # 基本特征
    features["market"] = strategy.get("market", "unknown")
    features["timeframe"] = strategy.get("timeframe", "unknown")

    # 参数特征
    for name, value in strategy.get("parameters", {}).items():
        if isinstance(value, (int, float)):
            features[f"param_{name}"] = value

    # 条件特征 - 统计不同类型的条件数量
    entry_conditions = strategy.get("entry_conditions", [])
    exit_conditions = strategy.get("exit_conditions", [])

    # 计算不同类型指标的使用频率
    indicator_types = {
        "moving_average": 0,
        "oscillator": 0,
        "volatility": 0,
        "volume": 0,
        "price_action": 0,
        "support_resistance": 0,
        "other": 0,
    }

    # 分类不同指标
    def categorize_indicator(condition):
        indicator = condition.get("indicator", "").lower()

        if any(x in indicator for x in ["ma", "ema", "sma", "wma", "moving average"]):
            return "moving_average"
        elif any(x in indicator for x in ["rsi", "macd", "stoch", "cci", "oscillator"]):
            return "oscillator"
        elif any(x in indicator for x in ["atr", "bollinger", "keltner", "volatility"]):
            return "volatility"
        elif any(x in indicator for x in ["volume", "obv", "money flow"]):
            return "volume"
        elif any(x in indicator for x in ["candle", "pattern", "engulfing", "doji"]):
            return "price_action"
        elif any(
            x in indicator for x in ["support", "resistance", "pivot", "fibonacci"]
        ):
            return "support_resistance"
        else:
            return "other"

    # 统计入场条件
    for condition in entry_conditions:
        category = categorize_indicator(condition)
        indicator_types[category] += 1

    # 统计出场条件
    for condition in exit_conditions:
        category = categorize_indicator(condition)
        indicator_types[category] += 1

    # 添加到特征
    for category, count in indicator_types.items():
        features[f"indicator_{category}"] = count

    # 策略复杂度特征
    features["entry_condition_count"] = len(entry_conditions)
    features["exit_condition_count"] = len(exit_conditions)
    features["total_condition_count"] = len(
        entry_conditions) + len(exit_conditions)
    features["parameter_count"] = len(strategy.get("parameters", {}))

    return features


def _prepare_training_data(
    strategy_id: str = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    准备用于训练的数据

    Args:
        strategy_id (str, optional): 可选的策略ID过滤器. Defaults to None.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (特征DataFrame, 指标DataFrame)
    """
    if not LEARNER_STATUS["initialized"]:
        raise LearnerInitError("Learner not initialized")

    # 收集所有策略数据
    all_features = []
    all_metrics = []

    for s_id, history in LEARNER_STATUS["strategy_history"].items():
        if strategy_id and s_id != strategy_id:
            continue

        for version_data in history["versions"]:
            # 确保有性能数据
            if not version_data.get("performance"):
                continue

            strategy = version_data["strategy"]
            performance = version_data["performance"]

            # 提取特征和指标
            features = _extract_strategy_features(strategy)
            metrics = _calculate_performance_metrics(performance)

            # 添加标识信息
            features["strategy_id"] = s_id
            features["version"] = version_data["version"]

            all_features.append(features)
            all_metrics.append(metrics)

    # 转换为DataFrame
    features_df = pd.DataFrame(all_features)
    metrics_df = pd.DataFrame(all_metrics)

    return features_df, metrics_df


def _train_prediction_model(
    strategy_id: Optional[str] = None, target_metric: Optional[str] = None
) -> Union[Dict[str, Any], None]:
    """
    训练预测模型

    Args:
        strategy_id (Optional[str], optional): 特定策略ID或所有策略. Defaults to None.
        target_metric (Optional[str], optional): 目标指标. Defaults to None.

    Returns:
        Union[Dict[str, Any], None]: 训练好的模型信息或None
    """
    if (
        not LEARNER_STATUS["initialized"]
        or not LEARNER_STATUS["config"]["use_ml_models"]
    ):
        return None

    # 使用默认指标
    if target_metric is None:
        target_metric = LEARNER_STATUS["config"]["primary_metric"]

    try:
        # 准备训练数据
        features_df, metrics_df = _prepare_training_data(strategy_id)

        if len(features_df) < 5:  # 数据太少
            logger.warning(
                f"Insufficient data to train model for {strategy_id or 'all strategies'}"
            )
            return None

        # 移除非数值列和标识列
        feature_cols = [
            col
            for col in features_df.columns
            if col not in ["strategy_id", "version", "market", "timeframe"]
            and pd.api.types.is_numeric_dtype(features_df[col])
        ]

        X = features_df[feature_cols].fillna(0)
        y = metrics_df[target_metric]

        # 分割训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 训练模型
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # 评估模型
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # 特征重要性
        feature_importance = {
            feature: importance
            for feature, importance in zip(feature_cols, model.feature_importances_)
        }

        model_info = {
            "model": model,
            "feature_columns": feature_cols,
            "target_metric": target_metric,
            "train_date": datetime.now().isoformat(),
            "performance": {"mse": mse, "mae": mae, "r2": r2},
            "feature_importance": feature_importance,
        }

        # 更新模型存储
        if strategy_id:
            model_key = f"{strategy_id}_{target_metric}"
        else:
            model_key = f"global_{target_metric}"

        LEARNER_STATUS["models"][model_key] = model_info

        # 保存状态
        _save_learner_state()

        return model_info

    except Exception as e:
        logger.error(f"Error training prediction model: {str(e)}")
        return None


def analyze_strategy_performance(
    strategy_id: str, performance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    分析策略性能并识别优势和劣势

    Args:
        strategy_id (str): 策略ID
        performance_data (Dict[str, Any]): 性能数据

    Returns:
        Dict[str, Any]: 分析结果
    """
    if not LEARNER_STATUS["initialized"]:
        raise LearnerInitError("Learner not initialized")

    # 计算性能指标
    metrics = _calculate_performance_metrics(performance_data)

    # 获取策略信息
    strategy_info = None
    if strategy_id in LEARNER_STATUS["strategy_history"]:
        history = LEARNER_STATUS["strategy_history"][strategy_id]
        if history["versions"]:
            latest_version = max(
                history["versions"], key=lambda x: x["version"])
            strategy_info = latest_version["strategy"]

    # 如果找不到策略信息，返回基本分析
    if not strategy_info:
        return {
            "strategy_id": strategy_id,
            "metrics": metrics,
            "strengths": [],
            "weaknesses": [],
            "timestamp": datetime.now().isoformat(),
        }

    # 分析优势和劣势
    strengths = []
    weaknesses = []

    # 查看历史性能对比
    if strategy_id in LEARNER_STATUS["strategy_history"]:
        history = LEARNER_STATUS["strategy_history"][strategy_id]
        if len(history["versions"]) > 1:
            previous_versions = sorted(
                history["versions"], key=lambda x: x["version"], reverse=True
            )

            if len(previous_versions) > 1:
                prev_version = previous_versions[1]  # 次新版本
                prev_metrics = _calculate_performance_metrics(
                    prev_version.get("performance", {})
                )

                # 比较与上一版本的差异
                if (
                    metrics["total_return"] > prev_metrics["total_return"] * 1.1
                ):  # 提高了10%以上
                    strengths.append("总回报率显著提高")
                elif (
                    metrics["total_return"] < prev_metrics["total_return"] * 0.9
                ):  # 下降了10%以上
                    weaknesses.append("总回报率显著下降")

                if metrics["sharpe_ratio"] > prev_metrics["sharpe_ratio"] * 1.1:
                    strengths.append("风险调整后收益显著提高")
                elif metrics["sharpe_ratio"] < prev_metrics["sharpe_ratio"] * 0.9:
                    weaknesses.append("风险调整后收益显著下降")

                if metrics["max_drawdown"] < prev_metrics["max_drawdown"] * 0.9:
                    strengths.append("最大回撤显著减少")
                elif metrics["max_drawdown"] > prev_metrics["max_drawdown"] * 1.1:
                    weaknesses.append("最大回撤显著增加")

    # 基于绝对指标的分析
    if metrics["sharpe_ratio"] > 1.5:
        strengths.append("优秀的风险调整后收益")
    elif metrics["sharpe_ratio"] < 0.5:
        weaknesses.append("较低的风险调整后收益")

    if metrics["win_rate"] > 0.6:
        strengths.append("较高的胜率")
    elif metrics["win_rate"] < 0.4:
        weaknesses.append("较低的胜率")

    if metrics["profit_factor"] > 2.0:
        strengths.append("优秀的盈亏比")
    elif metrics["profit_factor"] < 1.2:
        weaknesses.append("较低的盈亏比")

    if metrics["max_drawdown"] < 0.1:
        strengths.append("较小的最大回撤")
    elif metrics["max_drawdown"] > 0.25:
        weaknesses.append("较大的最大回撤")

    # 通过ML模型分析特征对性能的影响
    try:
        # 使用全局模型
        model_key = f"global_{LEARNER_STATUS['config']['primary_metric']}"
        if model_key in LEARNER_STATUS["models"]:
            model_info = LEARNER_STATUS["models"][model_key]

            # 提取策略特征
            features = _extract_strategy_features(strategy_info)

            # 转换为模型输入格式
            feature_cols = model_info["feature_columns"]
            feature_vector = {col: features.get(
                col, 0) for col in feature_cols}
            feature_df = pd.DataFrame([feature_vector])

            # 获取特征重要性
            importance = model_info["feature_importance"]
            sorted_features = sorted(
                importance.items(), key=lambda x: x[1], reverse=True
            )

            # 分析最重要的特征
            for feature, imp in sorted_features[:3]:
                if feature in features and imp > 0.05:  # 只关注重要特征
                    feature_value = features[feature]
                    feature_name = feature.replace("param_", "参数: ").replace(
                        "indicator_", "指标类型: "
                    )

                    # 尝试识别是否是强或弱点
                    if imp > 0.1:  # 非常重要的特征
                        if feature.startswith("param_"):
                            param_name = feature.replace("param_", "")
                            high_value = feature_value > np.mean(
                                [v.get(feature, 0) for v in all_features]
                            )

                            if high_value and imp > 0.15:
                                strengths.append(f"参数 {param_name} 设置得当")
                            elif not high_value and imp > 0.15:
                                weaknesses.append(f"参数 {param_name} 可能需要调整")
    except Exception as e:
        logger.warning(f"Error in ML-based analysis: {str(e)}")

    # 保存到性能缓存
    LEARNER_STATUS["performance_cache"][strategy_id] = {
        "metrics": metrics,
        "analysis_date": datetime.now().isoformat(),
    }

    # 更新策略历史
    if strategy_id in LEARNER_STATUS["strategy_history"]:
        history = LEARNER_STATUS["strategy_history"][strategy_id]
        if history["versions"]:
            latest_version = max(
                history["versions"], key=lambda x: x["version"])
            latest_version["performance"] = performance_data
            latest_version["analysis"] = {
                "metrics": metrics,
                "strengths": strengths,
                "weaknesses": weaknesses,
            }

    # 保存状态
    _save_learner_state()

    return {
        "strategy_id": strategy_id,
        "metrics": metrics,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "timestamp": datetime.now().isoformat(),
    }


def generate_improvement_suggestions(
    strategy_id: str, analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    生成策略改进建议

    Args:
        strategy_id (str): 策略ID
        analysis_results (Dict[str, Any]): 分析结果

    Returns:
        Dict[str, Any]: 改进建议
    """
    if not LEARNER_STATUS["initialized"]:
        raise LearnerInitError("Learner not initialized")

    # 获取策略信息
    strategy_info = None
    if strategy_id in LEARNER_STATUS["strategy_history"]:
        history = LEARNER_STATUS["strategy_history"][strategy_id]
        if history["versions"]:
            latest_version = max(
                history["versions"], key=lambda x: x["version"])
            strategy_info = latest_version["strategy"]

    # 如果找不到策略信息，返回基本建议
    if not strategy_info:
        return {
            "strategy_id": strategy_id,
            "suggestions": ["无法获取策略详细信息，请确保策略已注册到学习系统"],
            "parameter_adjustments": {},
            "timestamp": datetime.now().isoformat(),
        }

    weaknesses = analysis_results.get("weaknesses", [])
    metrics = analysis_results.get("metrics", {})

    suggestions = []
    parameter_adjustments = {}

    # 基于弱点的建议
    for weakness in weaknesses:
        if "最大回撤" in weakness:
            suggestions.append("考虑添加更严格的止损条件，减少单笔交易风险")
            suggestions.append("考虑增加市场波动性过滤器，避免在高波动期间入场")

        if "胜率" in weakness:
            suggestions.append("优化入场信号精度，可能需要增加确认指标")
            suggestions.append("考虑延迟入场，等待趋势更加确定")

        if "盈亏比" in weakness:
            suggestions.append("延长获利交易持续时间，使用追踪止损而非固定止盈")
            suggestions.append("调整止盈水平，允许利润继续增长")

    # 从策略模版中学习改进
    feature_vector = _extract_strategy_features(strategy_info)

    # 尝试使用ML模型提供建议
    try:
        # 训练策略特定模型或使用全局模型
        model_key = f"global_{LEARNER_STATUS['config']['primary_metric']}"
        if model_key not in LEARNER_STATUS["models"]:
            _train_prediction_model(
                target_metric=LEARNER_STATUS["config"]["primary_metric"]
            )

        if model_key in LEARNER_STATUS["models"]:
            model_info = LEARNER_STATUS["models"][model_key]

            # 提取参数特征
            param_features = {
                k: v for k, v in feature_vector.items() if k.startswith("param_")
            }

            # 参数敏感性分析
            for param_name, current_value in param_features.items():
                clean_name = param_name.replace("param_", "")

                # 创建测试变化
                test_changes = []
                # 尝试增加和减少参数
                test_values = [
                    current_value * 0.5,
                    current_value * 0.8,
                    current_value * 1.2,
                    current_value * 1.5,
                ]

                for test_value in test_values:
                    # 创建参数变更的特征向量副本
                    test_features = feature_vector.copy()
                    test_features[param_name] = test_value

                    # 转换为DataFrame
                    feature_df = pd.DataFrame(
                        [
                            {
                                col: test_features.get(col, 0)
                                for col in model_info["feature_columns"]
                            }
                        ]
                    )

                    # 预测性能
                    model = model_info["model"]
                    predicted_performance = model.predict(feature_df)[0]

                    test_changes.append((test_value, predicted_performance))

                # 找到预测性能最佳的值
                best_value, best_performance = max(
                    test_changes, key=lambda x: x[1])

                # 如果预测有显著改进，添加建议
                current_performance = metrics.get(
                    model_info["target_metric"], 0)
                if best_performance > current_performance * 1.1:  # 10%的改进
                    direction = "增加" if best_value > current_value else "减少"
                    change_pct = abs(
                        best_value - current_value) / current_value * 100

                    suggestion = (
                        f"建议{direction}参数 {clean_name} 的值约 {change_pct:.0f}%"
                    )
                    suggestions.append(suggestion)

                    parameter_adjustments[clean_name] = best_value
    except Exception as e:
        logger.warning(f"Error generating ML-based suggestions: {str(e)}")

    # 如果改进建议太少，添加通用建议
    if len(suggestions) < 2:
        if metrics.get("win_rate", 0) < 0.5:
            suggestions.append("考虑使用附加过滤器来提高信号质量")

        if metrics.get("sharpe_ratio", 0) < 1.0:
            suggestions.append("优化仓位管理，根据信号强度调整头寸大小")

    # 增加指标多样性建议
    indicator_counts = {
        k.replace("indicator_", ""): v
        for k, v in feature_vector.items()
        if k.startswith("indicator_")
    }

    # 检查是否缺少某类指标
    if indicator_counts.get("volume", 0) == 0:
        suggestions.append("考虑添加成交量指标来确认价格走势")

    if indicator_counts.get("volatility", 0) == 0:
        suggestions.append("考虑添加波动性指标来动态调整止损水平")

    # 记录建议
    if strategy_id in LEARNER_STATUS["strategy_history"]:
        history = LEARNER_STATUS["strategy_history"][strategy_id]
        if history["versions"]:
            latest_version = max(
                history["versions"], key=lambda x: x["version"])
            if "analysis" not in latest_version:
                latest_version["analysis"] = {}

            latest_version["analysis"]["suggestions"] = suggestions
            latest_version["analysis"]["parameter_adjustments"] = parameter_adjustments

    # 保存状态
    _save_learner_state()

    return {
        "strategy_id": strategy_id,
        "suggestions": suggestions,
        "parameter_adjustments": parameter_adjustments,
        "timestamp": datetime.now().isoformat(),
    }


def _get_parameter_bounds(strategy: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    """
    获取参数的上下限

    Args:
        strategy (Dict[str, Any]): 策略定义

    Returns:
        Dict[str, Tuple[float, float]]: 参数边界 {参数名: (下限, 上限)}
    """
    bounds = {}

    for name, value in strategy.get("parameters", {}).items():
        if isinstance(value, (int, float)):
            # 根据参数类型设置合理的上下限范围
            if name.lower().find("period") >= 0:
                # 周期类参数
                bounds[name] = (max(2, int(value * 0.5)), int(value * 2))
            elif name.lower().find("threshold") >= 0 or name.lower().find("level") >= 0:
                # 阈值类参数
                bounds[name] = (value * 0.5, value * 1.5)
            else:
                # 一般参数，设置较宽松的边界
                bounds[name] = (value * 0.2, value * 3.0)

    return bounds


def _crossover(
    parent1: Dict[str, Any],
    parent2: Dict[str, Any],
    params_bounds: Dict[str, Tuple[float, float]],
) -> Dict[str, Any]:
    """
    执行策略参数交叉操作

    Args:
        parent1 (Dict[str, Any]): 父策略1
        parent2 (Dict[str, Any]): 父策略2
        params_bounds (Dict[str, Tuple[float, float]]): 参数边界

    Returns:
        Dict[str, Any]: 子策略
    """
    child = parent1.copy()

    # 创建参数的深拷贝
    child["parameters"] = parent1["parameters"].copy()

    # 随机选择交叉点
    crossover_point = random.randint(0, len(params_bounds))

    # 执行参数交叉
    params = list(params_bounds.keys())

    for i, param_name in enumerate(params):
        if i >= crossover_point:
            if param_name in parent2["parameters"]:
                child["parameters"][param_name] = parent2["parameters"][param_name]

    return child


def _mutate(
    strategy: Dict[str, Any],
    params_bounds: Dict[str, Tuple[float, float]],
    mutation_rate: float,
) -> Dict[str, Any]:
    """
    执行策略参数变异操作

    Args:
        strategy (Dict[str, Any]): 策略定义
        params_bounds (Dict[str, Tuple[float, float]]): 参数边界
        mutation_rate (float): 变异率

    Returns:
        Dict[str, Any]: 变异后的策略
    """
    mutated = strategy.copy()

    # 创建参数的深拷贝
    mutated["parameters"] = strategy["parameters"].copy()

    # 遍历每个参数
    for param_name, (lower_bound, upper_bound) in params_bounds.items():
        # 按变异率决定是否变异此参数
        if random.random() < mutation_rate:
            current_value = mutated["parameters"].get(param_name, 0)

            # 确定是整数还是浮点数
            is_int = isinstance(current_value, int)

            # 生成变异值
            if is_int:
                # 整数参数，在边界内随机选择一个整数值
                mutated_value = random.randint(
                    int(lower_bound), int(upper_bound))
            else:
                # 浮点数参数，在边界内随机选择一个浮点数值
                mutated_value = random.uniform(lower_bound, upper_bound)

            # 更新参数值
            mutated["parameters"][param_name] = mutated_value

    return mutated


def evolve_strategy(
    strategy_id: str, evolution_parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    基于历史表现演化策略

    Args:
        strategy_id (str): 策略ID
        evolution_parameters (Optional[Dict[str, Any]], optional): 进化参数. Defaults to None.

    Returns:
        Dict[str, Any]: 演化结果
    """
    if not LEARNER_STATUS["initialized"]:
        raise LearnerInitError("Learner not initialized")

    # 获取策略历史
    if strategy_id not in LEARNER_STATUS["strategy_history"]:
        raise StrategyEvolutionError(
            f"Strategy with ID {strategy_id} not found")

    history = LEARNER_STATUS["strategy_history"][strategy_id]

    if not history["versions"]:
        raise StrategyEvolutionError(
            f"Strategy with ID {strategy_id} has no versions")

    # 获取最新版本
    latest_version = max(history["versions"], key=lambda x: x["version"])
    base_strategy = latest_version["strategy"]

    # 使用默认或传入的进化参数
    if evolution_parameters is None:
        evolution_parameters = LEARNER_STATUS["config"]["evolution_params"]

    population_size = evolution_parameters.get(
        "population_size", DEFAULT_EVOLUTION_PARAMS["population_size"]
    )
    generations = evolution_parameters.get(
        "generations", DEFAULT_EVOLUTION_PARAMS["generations"]
    )
    mutation_rate = evolution_parameters.get(
        "mutation_rate", DEFAULT_EVOLUTION_PARAMS["mutation_rate"]
    )
    crossover_rate = evolution_parameters.get(
        "crossover_rate", DEFAULT_EVOLUTION_PARAMS["crossover_rate"]
    )

    # 获取参数边界
    params_bounds = _get_parameter_bounds(base_strategy)

    if not params_bounds:
        logger.warning(
            f"No numerical parameters found for strategy {strategy_id}")
        return {
            "strategy_id": strategy_id,
            "status": "failed",
            "message": "No numerical parameters found for evolution",
            "timestamp": datetime.now().isoformat(),
        }

    # 初始化种群
    population = [base_strategy]

    # 添加历史版本以增加多样性
    for version_data in history["versions"]:
        if version_data["version"] != latest_version["version"]:
            population.append(version_data["strategy"])

    # 如果历史版本不足，通过参数变异生成新个体
    while len(population) < population_size:
        # 选择一个随机的现有策略
        parent = random.choice(population)
        # 生成一个变异
        new_strategy = _mutate(
            parent, params_bounds, mutation_rate * 2
        )  # 初始化时使用更高变异率
        population.append(new_strategy)

    # 记录最佳策略
    best_strategy = None
    best_score = float("-inf")

    # 训练模型用于评估
    model_info = _train_prediction_model(
        strategy_id=strategy_id,
        target_metric=LEARNER_STATUS["config"]["primary_metric"],
    )

    # 如果模型训练失败，使用全局模型
    if not model_info:
        model_key = f"global_{LEARNER_STATUS['config']['primary_metric']}"
        if model_key in LEARNER_STATUS["models"]:
            model_info = LEARNER_STATUS["models"][model_key]

    # 进化循环
    for generation in range(generations):
        logger.info(
            f"Evolving strategy {strategy_id}: Generation {generation+1}/{generations}"
        )

        # 评估当前种群
        scored_population = []

        for individual in population:
            # 获取性能评分
            if model_info:
                # 使用机器学习模型评估
                features = _extract_strategy_features(individual)
                feature_cols = model_info["feature_columns"]

                feature_vector = {col: features.get(
                    col, 0) for col in feature_cols}
                feature_df = pd.DataFrame([feature_vector])

                model = model_info["model"]
                score = model.predict(feature_df)[0]
            else:
                # 如果没有模型，使用简单启发式评分
                # 尝试找到个体的历史性能
                score = 0
                for version_data in history["versions"]:
                    if version_data["strategy"].get("parameters") == individual.get(
                        "parameters"
                    ):
                        if "performance" in version_data:
                            metrics = _calculate_performance_metrics(
                                version_data["performance"]
                            )
                            score = metrics.get(
                                LEARNER_STATUS["config"]["primary_metric"], 0
                            )
                            break

            scored_population.append((individual, score))

            # 更新最佳策略
            if score > best_score:
                best_score = score
                best_strategy = individual

        # 按评分排序
        scored_population.sort(key=lambda x: x[1], reverse=True)

        # 记录当前最佳
        logger.info(
            f"Generation {generation+1}: Best score = {scored_population[0][1]}"
        )

        # 如果是最终一代，结束循环
        if generation == generations - 1:
            break

        # 选择精英（保留最佳个体）
        elite_count = max(1, int(population_size * 0.1))
        new_population = [item[0] for item in scored_population[:elite_count]]

        # 生成下一代
        while len(new_population) < population_size:
            # 锦标赛选择
            tournament_size = 3
            tournament = random.sample(scored_population, tournament_size)
            tournament.sort(key=lambda x: x[1], reverse=True)

            parent1 = tournament[0][0]

            # 决定是执行交叉还是变异
            if random.random() < crossover_rate and len(scored_population) > 1:
                # 交叉操作
                tournament2 = random.sample(scored_population, tournament_size)
                tournament2.sort(key=lambda x: x[1], reverse=True)
                parent2 = tournament2[0][0]

                child = _crossover(parent1, parent2, params_bounds)
                # 然后对子代进行可能的变异
                if random.random() < mutation_rate:
                    child = _mutate(child, params_bounds, mutation_rate)
            else:
                # 变异操作
                child = _mutate(parent1, params_bounds, mutation_rate)

            new_population.append(child)

        # 更新种群
        population = new_population

    # 确认最佳策略不为空
    if not best_strategy:
        best_strategy = scored_population[0][0] if scored_population else base_strategy

    # 创建新版本
    new_version_number = latest_version["version"] + 1
    new_version = {
        "version": new_version_number,
        "strategy": best_strategy,
        "created_date": datetime.now().isoformat(),
        "source": "evolution",
        "parent_version": latest_version["version"],
    }

    # 添加到历史
    history["versions"].append(new_version)

    # 修剪历史版本，保留最新的MAX_HISTORY_VERSIONS个版本
    if len(history["versions"]) > MAX_HISTORY_VERSIONS:
        history["versions"].sort(key=lambda x: x["version"], reverse=True)
        history["versions"] = history["versions"][:MAX_HISTORY_VERSIONS]

    # 保存状态
    _save_learner_state()

    return {
        "strategy_id": strategy_id,
        "status": "success",
        "new_version": new_version_number,
        "improvements": {
            "estimated_score": best_score,
            "parameter_changes": {
                k: v
                for k, v in best_strategy["parameters"].items()
                if k in base_strategy["parameters"]
                and v != base_strategy["parameters"][k]
            },
        },
        "timestamp": datetime.now().isoformat(),
    }