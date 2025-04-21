# -*- coding: utf-8 -*-
"""
交易辅助工具模块: trading_utils
功能描述: 提供量化交易相关的辅助功能，包括策略ID生成、参数验证等
版本: 1.1
创建日期: 2025-04-17
"""

import os
import time
import uuid
import random
import string
import logging
import json
import datetime
from typing import Dict, Any, Tuple, List, Optional, Union

# 配置日志记录器
logger = logging.getLogger(__name__)


def generate_strategy_id(symbol: str, timeframe: str, prefix: str = "strat") -> str:
    """
    生成唯一策略ID

    Args:
        symbol: 交易对符号（如 'BTC/USDT'）
        timeframe: 时间周期（如 '1h', '4h', '1d'）
        prefix: 前缀标识符

    Returns:
        生成的唯一策略ID

    Examples:
        >>> generate_strategy_id('BTC/USDT', '1h')
        'strat_btc_usdt_1h_1713399245_a7b3c'
    """
    try:
        # 生成时间戳
        timestamp = int(time.time())

        # 生成随机后缀
        random_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=5)
        )

        # 格式化交易对，如BTC/USDT -> btc_usdt
        formatted_symbol = symbol.lower().replace("/", "_")

        # 组合ID
        strategy_id = (
            f"{prefix}_{formatted_symbol}_{timeframe}_{timestamp}_{random_suffix}"
        )

        logger.debug(
            f"生成策略ID: {strategy_id}, 基于符号: {symbol}, 时间周期: {timeframe}"
        )
        return strategy_id

    except Exception as e:
        logger.error(f"生成策略ID时出错: {str(e)}")
        # 出错时使用更简单的后备ID生成方法
        fallback_id = f"{prefix}_{int(time.time())}"
        logger.info(f"使用后备策略ID: {fallback_id}")
        return fallback_id


def validate_strategy_params(params: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证策略参数有效性

    Args:
        params: 策略参数字典

    Returns:
        一个元组，包含(是否有效, 验证消息)

    Examples:
        >>> validate_strategy_params({"symbol": "BTC/USDT", "timeframe": "1h",
        ...                          "entry_logic": ["ema_cross"], "exit_logic": ["stop_loss"],
        ...                          "risk": {"stop_loss_pct": 0.05, "take_profit_pct": 0.15}})
        (True, "参数有效")
    """
    try:
        # 检查必填字段
        required_fields = ["symbol", "timeframe",
                           "entry_logic", "exit_logic", "risk"]
        for field in required_fields:
            if field not in params:
                logger.warning(f"策略参数验证失败: 缺少必填字段 '{field}'")
                return False, f"缺少必填字段: {field}"

        # 检查symbol格式
        if not isinstance(params["symbol"], str) or "/" not in params["symbol"]:
            logger.warning(f"策略参数验证失败: 无效的交易对格式 '{params['symbol']}'")
            return False, "无效的交易对格式，应为 'BTC/USDT' 格式"

        # 检查timeframe格式
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        if params["timeframe"] not in valid_timeframes:
            logger.warning(f"策略参数验证失败: 无效的时间周期 '{params['timeframe']}'")
            return False, f"无效的时间周期，应为 {', '.join(valid_timeframes)} 之一"

        # 检查入场和出场逻辑
        if (
            not isinstance(params["entry_logic"], list)
            or len(params["entry_logic"]) == 0
        ):
            logger.warning("策略参数验证失败: 入场逻辑应为非空列表")
            return False, "入场逻辑应为非空列表"

        if not isinstance(params["exit_logic"], list) or len(params["exit_logic"]) == 0:
            logger.warning("策略参数验证失败: 出场逻辑应为非空列表")
            return False, "出场逻辑应为非空列表"

        # 检查入场逻辑有效性
        supported_entry_logic = get_supported_entry_logic()
        for logic in params["entry_logic"]:
            if logic not in supported_entry_logic and not logic.startswith("custom_"):
                logger.warning(f"策略参数验证失败: 不支持的入场逻辑 '{logic}'")
                return (
                    False,
                    f"不支持的入场逻辑: {logic}, 支持的选项: {', '.join(supported_entry_logic)}",
                )

        # 检查出场逻辑有效性
        supported_exit_logic = get_supported_exit_logic()
        for logic in params["exit_logic"]:
            if logic not in supported_exit_logic and not logic.startswith("custom_"):
                logger.warning(f"策略参数验证失败: 不支持的出场逻辑 '{logic}'")
                return (
                    False,
                    f"不支持的出场逻辑: {logic}, 支持的选项: {', '.join(supported_exit_logic)}",
                )

        # 检查风险参数
        if not isinstance(params["risk"], dict):
            logger.warning("策略参数验证失败: 风险参数应为字典")
            return False, "风险参数应为字典"

        risk_params = params["risk"]
        if "stop_loss_pct" not in risk_params or "take_profit_pct" not in risk_params:
            logger.warning("策略参数验证失败: 风险参数缺少止损或止盈比例")
            return False, "风险参数缺少止损或止盈比例"

        # 检查止损和止盈比例
        try:
            stop_loss = float(risk_params["stop_loss_pct"])
            take_profit = float(risk_params["take_profit_pct"])

            if stop_loss <= 0 or stop_loss > 0.5:
                logger.warning(
                    f"策略参数验证失败: 止损比例 {stop_loss} 应在 0-50% 之间"
                )
                return False, "止损比例应在 0-50% 之间"

            if take_profit <= 0:
                logger.warning(f"策略参数验证失败: 止盈比例 {take_profit} 应大于 0")
                return False, "止盈比例应大于 0"

        except (ValueError, TypeError) as e:
            logger.warning(f"策略参数验证失败: 止损或止盈比例无效 - {str(e)}")
            return False, "止损或止盈比例无效，应为数字"

        # 检查可选参数
        if "position_size" in params:
            if (
                not isinstance(params["position_size"], (int, float))
                or params["position_size"] <= 0
            ):
                logger.warning(
                    f"策略参数验证失败: 仓位大小 {params['position_size']} 应为正数"
                )
                return False, "仓位大小应为正数"

        if "indicators" in params:
            if not isinstance(params["indicators"], dict):
                logger.warning("策略参数验证失败: 指标配置应为字典")
                return False, "指标配置应为字典"

            # 验证所有指标是否支持
            supported_indicators = get_supported_indicators()
            for indicator_name in params["indicators"].keys():
                if indicator_name not in supported_indicators:
                    logger.warning(f"策略参数验证失败: 不支持的指标 '{indicator_name}'")
                    return (
                        False,
                        f"不支持的指标: {indicator_name}, 支持的指标: {', '.join(supported_indicators)}",
                    )

        logger.info(f"策略参数验证通过: {params['symbol']} {params['timeframe']}")
        return True, "参数有效"

    except Exception as e:
        logger.error(f"验证策略参数时出错: {str(e)}")
        return False, f"验证过程中出错: {str(e)}"


def parse_timeframe(timeframe: str) -> int:
    """
    将时间周期字符串解析为分钟数

    Args:
        timeframe: 时间周期字符串，如 '1h', '15m', '1d'

    Returns:
        分钟数

    Raises:
        ValueError: 如果时间周期格式无效

    Examples:
        >>> parse_timeframe("1h")
        60
        >>> parse_timeframe("15m")
        15
        >>> parse_timeframe("1d")
        1440
    """
    try:
        if timeframe.endswith("m"):
            return int(timeframe[:-1])
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith("d"):
            return int(timeframe[:-1]) * 60 * 24
        elif timeframe.endswith("w"):
            return int(timeframe[:-1]) * 60 * 24 * 7
        else:
            logger.error(f"无效的时间周期格式: {timeframe}")
            raise ValueError(f"无效的时间周期格式: {timeframe}")
    except Exception as e:
        logger.error(f"解析时间周期出错: {str(e)}")
        raise ValueError(f"解析时间周期出错: {str(e)}")


def get_supported_indicators() -> List[str]:
    """
    获取支持的技术指标列表

    Returns:
        指标列表

    Examples:
        >>> get_supported_indicators()
        ['sma', 'ema', 'rsi', 'macd', 'bollinger_bands', 'stochastic', 'adx', 'obv', 'atr', 'cci']
    """
    indicators = [
        "sma",
        "ema",
        "rsi",
        "macd",
        "bollinger_bands",
        "stochastic",
        "adx",
        "obv",
        "atr",
        "cci",
    ]
    logger.debug(f"支持的技术指标: {', '.join(indicators)}")
    return indicators


def get_supported_entry_logic() -> List[str]:
    """
    获取支持的入场逻辑列表

    Returns:
        入场逻辑列表

    Examples:
        >>> get_supported_entry_logic()
        ['ema_cross', 'macd_cross', 'rsi_oversold', 'bollinger_breakout', 'volume_spike', 'support_bounce']
    """
    entry_logic = [
        "ema_cross",
        "macd_cross",
        "rsi_oversold",
        "bollinger_breakout",
        "volume_spike",
        "support_bounce",
    ]
    logger.debug(f"支持的入场逻辑: {', '.join(entry_logic)}")
    return entry_logic


def get_supported_exit_logic() -> List[str]:
    """
    获取支持的出场逻辑列表

    Returns:
        出场逻辑列表

    Examples:
        >>> get_supported_exit_logic()
        ['ema_cross', 'macd_cross', 'rsi_overbought', 'trailing_stop', 'take_profit', 'stop_loss']
    """
    exit_logic = [
        "ema_cross",
        "macd_cross",
        "rsi_overbought",
        "trailing_stop",
        "take_profit",
        "stop_loss",
    ]
    logger.debug(f"支持的出场逻辑: {', '.join(exit_logic)}")
    return exit_logic


def calculate_position_size(
    account_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss_price: float,
) -> float:
    """
    计算基于风险的仓位大小

    Args:
        account_balance: 账户余额
        risk_percentage: 愿意损失的账户余额百分比(0-100)
        entry_price: 入场价格
        stop_loss_price: 止损价格

    Returns:
        仓位大小（交易数量）

    Examples:
        >>> calculate_position_size(10000, 2, 50000, 49000)
        0.2
    """
    try:
        # 验证输入
        if account_balance <= 0:
            logger.error("计算仓位大小错误: 账户余额必须为正数")
            return 0

        if risk_percentage <= 0 or risk_percentage > 100:
            logger.error("计算仓位大小错误: 风险百分比必须在0-100之间")
            return 0

        if entry_price <= 0:
            logger.error("计算仓位大小错误: 入场价格必须为正数")
            return 0

        if stop_loss_price <= 0:
            logger.error("计算仓位大小错误: 止损价格必须为正数")
            return 0

        # 转换风险百分比
        risk_decimal = risk_percentage / 100

        # 计算风险金额
        risk_amount = account_balance * risk_decimal

        # 计算每单位的风险
        price_difference = abs(entry_price - stop_loss_price)

        # 防止除以零
        if price_difference == 0:
            logger.error("计算仓位大小错误: 入场价格和止损价格不能相同")
            return 0

        # 计算仓位大小
        position_size = risk_amount / price_difference

        # 根据账户余额和入场价格验证仓位是否合理
        max_possible_position = account_balance / entry_price
        if position_size > max_possible_position:
            logger.warning(
                f"计算的仓位大小({position_size})超过可用余额允许的最大值({max_possible_position})，将使用最大可能值"
            )
            position_size = max_possible_position

        logger.info(
            f"计算仓位大小: {position_size}, 基于账户余额: {account_balance}, 风险百分比: {risk_percentage}%"
        )
        return position_size

    except Exception as e:
        logger.error(f"计算仓位大小时出错: {str(e)}")
        return 0


def save_strategy_config(
    strategy_id: str, config: Dict[str, Any], folder_path: str = "strategies"
) -> Tuple[bool, str]:
    """
    保存策略配置到JSON文件

    Args:
        strategy_id: 策略ID
        config: 策略配置字典
        folder_path: 存储配置文件的文件夹路径

    Returns:
        一个元组，包含(是否成功, 消息)

    Examples:
        >>> save_strategy_config("strat_btc_usdt_1h_12345", {"symbol": "BTC/USDT", "timeframe": "1h"})
        (True, "配置已保存到 strategies/strat_btc_usdt_1h_12345.json")
    """
    try:
        # 确保目录存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logger.info(f"创建策略配置目录: {folder_path}")

        # 添加元数据
        config_with_meta = config.copy()
        config_with_meta["strategy_id"] = strategy_id
        config_with_meta["created_at"] = datetime.datetime.now().isoformat()
        config_with_meta["updated_at"] = datetime.datetime.now().isoformat()

        # 构建文件路径
        file_path = os.path.join(folder_path, f"{strategy_id}.json")

        # 保存到文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config_with_meta, f, indent=4, ensure_ascii=False)

        logger.info(f"策略配置已保存: {file_path}")
        return True, f"配置已保存到 {file_path}"

    except Exception as e:
        logger.error(f"保存策略配置时出错: {str(e)}")
        return False, f"保存配置时出错: {str(e)}"


def load_strategy_config(
    strategy_id: str, folder_path: str = "strategies"
) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    从JSON文件加载策略配置

    Args:
        strategy_id: 策略ID
        folder_path: 存储配置文件的文件夹路径

    Returns:
        一个元组，包含(是否成功, 配置字典或错误消息)

    Examples:
        >>> success, config = load_strategy_config("strat_btc_usdt_1h_12345")
        >>> if success:
        ...     print(config["symbol"])
        ... else:
        ...     print(config)  # 错误消息
        'BTC/USDT'
    """
    try:
        # 构建文件路径
        file_path = os.path.join(folder_path, f"{strategy_id}.json")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"策略配置文件不存在: {file_path}")
            return False, f"策略配置不存在: {strategy_id}"

        # 读取文件
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        logger.info(f"策略配置已加载: {strategy_id}")
        return True, config

    except json.JSONDecodeError as e:
        logger.error(f"解析策略配置时出错: {str(e)}")
        return False, f"策略配置格式无效: {str(e)}"
    except Exception as e:
        logger.error(f"加载策略配置时出错: {str(e)}")
        return False, f"加载配置时出错: {str(e)}"


def get_timeframe_milliseconds(timeframe: str) -> int:
    """
    获取时间周期的毫秒表示

    Args:
        timeframe: 时间周期字符串

    Returns:
        毫秒数

    Examples:
        >>> get_timeframe_milliseconds("1m")
        60000
        >>> get_timeframe_milliseconds("1h")
        3600000
    """
    try:
        # 获取分钟数
        minutes = parse_timeframe(timeframe)
        # 转换为毫秒
        milliseconds = minutes * 60 * 1000
        logger.debug(f"时间周期 {timeframe} 转换为 {milliseconds} 毫秒")
        return milliseconds
    except Exception as e:
        logger.error(f"获取时间周期毫秒数时出错: {str(e)}")
        raise


def validate_exchange_symbol(exchange_name: str, symbol: str) -> bool:
    """
    验证交易所是否支持指定交易对

    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号

    Returns:
        是否支持

    Note:
        此函数需要与交易所API集成
    """
    # 注意：此函数需要实际集成交易所API才能完全实现
    logger.warning(
        f"验证交易所交易对 {exchange_name}/{symbol} - 此功能需要集成具体交易所API"
    )
    return True  # 仅作为示例返回


def calculate_historical_performance(
    strategy_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    计算策略的历史表现

    Args:
        strategy_id: 策略ID
        start_date: 开始日期 (ISO格式，如 '2023-01-01')
        end_date: 结束日期 (ISO格式，如 '2023-12-31')

    Returns:
        表现指标字典

    Note:
        此函数需要与回测系统集成
    """
    # 注意：此函数需要实际集成回测系统才能完全实现
    logger.warning(f"计算策略 {strategy_id} 的历史表现 - 此功能需要集成回测系统")

    # 示例返回
    return {
        "strategy_id": strategy_id,
        "start_date": start_date or "2023-01-01",
        "end_date": end_date or datetime.datetime.now().strftime("%Y-%m-%d"),
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "max_drawdown": 0.0,
        "sharpe_ratio": 0.0,
        "note": "此为示例数据，需要集成实际回测系统",
    }