"""
模块名称: strategies.generated.ge_strategy
功能描述: 通用电气(GE)股票交易策略
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


class GEStrategy(BasicStrategy):
    """
    通用电气(GE)股票交易策略

    使用EMA和RSI指标针对通用电气股票的特点进行交易

    属性:
        name (str): 策略名称
        minimal_roi (Dict[str, float]): 最小ROI配置
        stoploss (float): 止损配置
        timeframe (str): 时间周期
    """

    # 策略名称
    name = "GEStrategy"

    # ROI表 - 不同时间段的期望利润
    minimal_roi = {
        "0": 0.05,  # 0分钟后需要5%的利润
        "60": 0.03,  # 60分钟后需要3%的利润
        "120": 0.02,  # 120分钟后需要2%的利润
        "240": 0,  # 240分钟后任何盈利都可以退出
    }

    # 止损设置
    stoploss = -0.07  # 7%止损

    # 时间周期
    timeframe = "4h"

    # 策略参数
    ema_short = 9
    ema_long = 21
    rsi_period = 14
    rsi_oversold = 35
    rsi_overbought = 70

    def __init__(self):
        """
        初始化通用电气股票交易策略
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
        # 添加EMA指标
        dataframe["ema_short"] = ta.EMA(dataframe, timeperiod=self.ema_short)
        dataframe["ema_long"] = ta.EMA(dataframe, timeperiod=self.ema_long)

        # 添加RSI指标
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=self.rsi_period)

        # 添加ATR指标（平均真实范围）
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # 添加交易量相关指标
        dataframe["volume_mean"] = dataframe["volume"].rolling(
            window=20).mean()
        dataframe["volume_ratio"] = dataframe["volume"] / \
            dataframe["volume_mean"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        基于指标生成买入信号

        参数:
            dataframe (DataFrame): 带有指标的dataframe
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了买入信号的dataframe
        """
        # 基本买入条件
        dataframe.loc[
            (
                # EMA短线上穿长线
                (dataframe["ema_short"] > dataframe["ema_long"])
                & (dataframe["ema_short"].shift() <= dataframe["ema_long"].shift())
                &
                # RSI处于合理水平
                (dataframe["rsi"] > self.rsi_oversold)
                & (dataframe["rsi"] < 60)
                &
                # 确保有足够的交易量
                (dataframe["volume_ratio"] > 1.2)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: Dict) -> DataFrame:
        """
        基于指标生成卖出信号

        参数:
            dataframe (DataFrame): 带有指标的dataframe
            metadata (Dict): 额外的元数据

        返回:
            DataFrame: 添加了卖出信号的dataframe
        """
        # 基本卖出条件
        dataframe.loc[
            (
                # EMA短线下穿长线
                (dataframe["ema_short"] < dataframe["ema_long"])
                & (dataframe["ema_short"].shift() >= dataframe["ema_long"].shift())
                |
                # RSI超买
                (dataframe["rsi"] > self.rsi_overbought)
            ),
            "exit_long",
        ] = 1

        return dataframe