""" "
模块名称: strategies.templates.advanced_strategy
功能描述: 高级策略模板，提供更多高级功能和指标
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import logging
import modules.nlp as np
import config.paths as pd
import talib.abstract as ta
from typing import Dict, List, Optional, Tuple, Union
from config.paths import DataFrame

# 设置日志
logger = logging.getLogger(__name__)


class AdvancedStrategy:
    """
    高级策略模板类，提供更多高级功能和指标

    包含市场状态检测、多重信号确认和风险管理功能

    属性:
        name (str): 策略名称
        minimal_roi (Dict[str, float]): 最小ROI配置
        stoploss (float): 止损配置
        trailing_stop (bool): 是否启用追踪止损
        trailing_stop_positive (float): 盈利追踪止损激活值
        trailing_stop_positive_offset (float): 盈利追踪止损偏移
        trailing_only_offset_is_reached (bool): 是否仅在达到偏移时启用追踪
        timeframe (str): 时间周期
    """

    # 策略名称
    name = "AdvancedStrategy"

    # ROI表 - 不同时间段的期望利润
    minimal_roi = {
        "0": 0.1,  # 0分钟后需要10%的利润
        "30": 0.05,  # 30分钟后需要5%的利润
        "60": 0.02,  # 60分钟后需要2%的利润
        "120": 0,  # 120分钟后任何盈利都可以退出
    }

    # 止损设置
    stoploss = -0.1  # 10%止损
    trailing_stop = True
    trailing_stop_positive = 0.01  # 1%
    trailing_stop_positive_offset = 0.02  # 2%
    trailing_only_offset_is_reached = True

    # 时间周期
    timeframe = "1h"

    # 交易控制选项
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": True,
    }

    # 订单时间有效期
    order_time_in_force = {
        "entry": "gtc",  # good till cancelled
        "exit": "gtc",  # good till cancelled
    }

    # 交易保护配置
    use_custom_stoploss = True

    def __init__(self):
        """
        初始化高级策略实例
        """
        logger.info(f"初始化 {self.name} 策略")

        # 定义市场状态变量
        self.market_state = None
        self.current_trend = None

    def populate_indicators(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        计算并添加高级策略所需指标

        包括趋势指标、震荡指标和交易量指标

        参数:
            dataframe (DataFrame): 价格和数量数据
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了指标的dataframe
        """
        # 价格和交易量的移动平均线
        for length in [5, 10, 20, 50, 100, 200]:
            dataframe[f"sma_{length}"] = ta.SMA(dataframe, timeperiod=length)
            dataframe[f"ema_{length}"] = ta.EMA(dataframe, timeperiod=length)

        # 交易量指标
        dataframe["volume_mean"] = dataframe["volume"].rolling(
            window=20).mean()
        dataframe["volume_ratio"] = dataframe["volume"] / \
            dataframe["volume_mean"]

        # MACD
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # RSI
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # Bollinger Bands
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2, nbdevdn=2)
        dataframe["bb_upperband"] = bollinger["upperband"]
        dataframe["bb_middleband"] = bollinger["middleband"]
        dataframe["bb_lowerband"] = bollinger["lowerband"]
        dataframe["bb_width"] = (
            dataframe["bb_upperband"] - dataframe["bb_lowerband"]
        ) / dataframe["bb_middleband"]

        # ATR - 平均真实范围
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # 添加市场状态分类
        dataframe = self._classify_market_state(dataframe)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        基于多重确认信号生成买入信号

        参数:
            dataframe (DataFrame): 带有指标的dataframe
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了买入信号的dataframe
        """
        # 趋势跟随信号
        trend_signal = (
            (dataframe["ema_20"] > dataframe["ema_50"])  # 中期上涨趋势
            & (dataframe["ema_50"] > dataframe["ema_100"])  # 长期上涨趋势
            & (dataframe["macd"] > dataframe["macdsignal"])  # MACD信号
        )

        # 价格回调至支撑位信号
        support_signal = (
            (dataframe["close"] <= dataframe["bb_lowerband"])  # 价格触及下轨
            & (dataframe["rsi"] < 30)  # RSI超卖
            & (dataframe["volume_ratio"] > 1.0)  # 交易量确认
        )

        # 震荡市场做多信号
        oscillating_signal = (
            (dataframe["market_state"] == "oscillating")  # 震荡市场
            & (dataframe["close"] < dataframe["bb_middleband"])  # 价格低于中轨
            & (dataframe["rsi"] > 30)
            & (dataframe["rsi"] < 50)  # RSI在合理区间
            & (dataframe["volume_ratio"] > 1.0)  # 交易量确认
        )

        # 合并信号
        dataframe.loc[
            (trend_signal | support_signal | oscillating_signal)
            & (dataframe["volume"] > 0),  # 确保有交易量
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        基于多重确认信号生成卖出信号

        参数:
            dataframe (DataFrame): 带有指标的dataframe
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了卖出信号的dataframe
        """
        # 趋势反转信号
        trend_reversal = (dataframe["ema_20"] < dataframe["ema_50"]) | (  # 中期趋势反转
            dataframe["macd"] < dataframe["macdsignal"]
        )  # MACD死叉

        # 超买信号
        overbought_signal = (
            dataframe["close"] >= dataframe["bb_upperband"]
        ) & (  # 价格触及上轨
            dataframe["rsi"] > 70
        )  # RSI超买

        # 止盈信号
        take_profit = (
            dataframe["close"] > dataframe["ema_20"] * 1.05
        ) & (  # 价格高于20日均线5%
            dataframe["volume_ratio"] > 1.5
        )  # 大交易量确认

        # 合并信号
        dataframe.loc[
            (trend_reversal | overbought_signal | take_profit), "exit_long"
        ] = 1

        return dataframe

    def custom_stoploss(
        self,
        pair: str,
        trade: "Trade",
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> float:
        """
        计算自定义止损

        该方法允许根据当前利润和市场状态动态调整止损

        参数:
            pair (str): 交易对名称
            trade (Trade): 交易对象
            current_time (datetime): 当前时间
            current_rate (float): 当前价格
            current_profit (float): 当前利润

        返回:
            float: 自定义止损值
        """
        # 如果利润大于5%，将止损移动至成本附近
        if current_profit > 0.05:
            return current_profit * 0.5

        # 默认使用策略设置的止损
        return self.stoploss

    def _classify_market_state(self, dataframe: DataFrame) -> DataFrame:
        """
        根据市场指标分类市场状态

        参数:
            dataframe (DataFrame): 带有指标的dataframe

        返回:
            DataFrame: 添加了市场状态的dataframe
        """
        # 利用布林带宽度识别趋势/震荡市场
        dataframe.loc[dataframe["bb_width"] >
                      0.05, "market_state"] = "trending"
        dataframe.loc[dataframe["bb_width"] <=
                      0.05, "market_state"] = "oscillating"

        # 利用均线判断趋势方向
        dataframe.loc[
            (dataframe["market_state"] == "trending")
            & (dataframe["ema_20"] > dataframe["ema_50"]),
            "trend_direction",
        ] = "uptrend"

        dataframe.loc[
            (dataframe["market_state"] == "trending")
            & (dataframe["ema_20"] < dataframe["ema_50"]),
            "trend_direction",
        ] = "downtrend"

        return dataframe