"""
模块名称: strategies.generated.macd_crossover_strategy
功能描述: MACD交叉策略，使用MACD指标进行趋势跟踪
版本: 1.0
创建日期: 2025-04-20
作者: GPT生成
"""

import logging
import modules.nlp as np
import config.paths as pd
import talib.abstract as ta
from typing import Dict, List, Optional
from config.paths import DataFrame

# 导入基础策略类
from trading.strategies.templates.basic_strategy import BasicStrategy

# 设置日志
logger = logging.getLogger(__name__)


class MacdCrossoverStrategy(BasicStrategy):
    """
    MACD交叉策略

    使用MACD指标进行趋势跟踪，利用MACD与信号线的交叉进行交易

    属性:
        name (str): 策略名称
        minimal_roi (Dict[str, float]): 最小ROI配置
        stoploss (float): 止损配置
        timeframe (str): 时间周期
        macd_fast (int): MACD快线周期
        macd_slow (int): MACD慢线周期
        macd_signal (int): MACD信号线周期
        rsi_period (int): RSI周期
        rsi_oversold (int): RSI超卖阈值
        rsi_overbought (int): RSI超买阈值
    """

    # 策略名称
    name = "MacdCrossoverStrategy"

    # ROI表 - 不同时间段的期望利润
    minimal_roi = {
        "0": 0.05,  # 0分钟后需要5%的利润
        "60": 0.03,  # 60分钟后需要3%的利润
        "120": 0.01,  # 120分钟后需要1%的利润
        "240": 0,  # 240分钟后任何盈利都可以退出
    }

    # 止损设置
    stoploss = -0.08  # 8%止损

    # 时间周期
    timeframe = "1h"

    # 策略参数
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70

    # 订单类型设置
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def __init__(self):
        """
        初始化MACD交叉策略
        """
        super().__init__()
        logger.info(f"初始化 {self.name} 策略")

    def populate_indicators(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        计算并添加策略所需指标

        参数:
            dataframe (DataFrame): 价格和数量数据
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了指标的dataframe
        """
        # 调用父类的populate_indicators方法
        dataframe = super().populate_indicators(dataframe, metadata)

        # 添加MACD指标
        macd = ta.MACD(
            dataframe,
            fastperiod=self.macd_fast,
            slowperiod=self.macd_slow,
            signalperiod=self.macd_signal,
        )
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # 计算MACD趋势
        dataframe["macd_trend"] = 0
        dataframe.loc[dataframe["macd"] >
                      dataframe["macdsignal"], "macd_trend"] = 1
        dataframe.loc[dataframe["macd"] <
                      dataframe["macdsignal"], "macd_trend"] = -1

        # 计算MACD金叉和死叉
        dataframe["macd_cross_up"] = (
            (dataframe["macd"] > dataframe["macdsignal"])
            & (dataframe["macd"].shift() <= dataframe["macdsignal"].shift())
        ).astype(int)
        dataframe["macd_cross_down"] = (
            (dataframe["macd"] < dataframe["macdsignal"])
            & (dataframe["macd"].shift() >= dataframe["macdsignal"].shift())
        ).astype(int)

        # 添加RSI指标（如果父类未添加）
        if "rsi" not in dataframe.columns:
            dataframe["rsi"] = ta.RSI(dataframe, timeperiod=self.rsi_period)

        # 添加交易量指标
        dataframe["volume_mean"] = dataframe["volume"].rolling(
            window=20).mean()
        dataframe["volume_ratio"] = dataframe["volume"] / \
            dataframe["volume_mean"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        基于MACD指标生成买入信号

        参数:
            dataframe (DataFrame): 带有指标的dataframe
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了买入信号的dataframe
        """
        # MACD金叉信号
        macd_cross_condition = dataframe["macd_cross_up"] > 0  # MACD金叉

        # RSI过滤条件
        rsi_condition = (dataframe["rsi"] > self.rsi_oversold) & (  # RSI高于超卖区域
            dataframe["rsi"] < 50
        )  # RSI仍在相对低位

        # 趋势过滤条件
        trend_condition = (
            dataframe["sma7"] > dataframe["sma25"]
        ) & (  # 短期均线高于中期均线
            dataframe["close"] > dataframe["sma25"]
        )  # 价格高于中期均线

        # 交易量确认
        volume_condition = dataframe["volume_ratio"] > 1.0  # 交易量高于平均水平

        # 组合买入信号
        dataframe.loc[
            macd_cross_condition
            & rsi_condition
            & trend_condition
            & volume_condition
            & (dataframe["volume"] > 0),  # 确保有交易量
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        基于MACD指标生成卖出信号

        参数:
            dataframe (DataFrame): 带有指标的dataframe
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了卖出信号的dataframe
        """
        # MACD死叉信号
        macd_cross_condition = dataframe["macd_cross_down"] > 0  # MACD死叉

        # RSI过滤条件
        rsi_condition = dataframe["rsi"] > self.rsi_overbought  # RSI高于超买区域

        # 趋势反转条件
        trend_condition = (
            dataframe["sma7"] < dataframe["sma25"]
        ) | (  # 短期均线低于中期均线
            dataframe["close"] < dataframe["sma7"]
        )  # 价格低于短期均线

        # 组合卖出信号
        dataframe.loc[
            macd_cross_condition | rsi_condition | trend_condition, "exit_long"
        ] = 1

        return dataframe