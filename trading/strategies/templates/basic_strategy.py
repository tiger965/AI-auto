""" "
模块名称: strategies.templates.basic_strategy
功能描述: 基础策略模板，兼容Freqtrade框架的IStrategy接口
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import logging
import modules.nlp as np
import config.paths as pd
from typing import Dict, List, Optional, Tuple, Union
from config.paths import DataFrame

# 设置日志
logger = logging.getLogger(__name__)


class BasicStrategy:
    """
    基础策略模板类，实现与Freqtrade兼容的基本接口

    策略开发者可以继承此类创建自己的策略

    属性:
        name (str): 策略名称
        minimal_roi (Dict[str, float]): 最小ROI配置
        stoploss (float): 止损配置
        trailing_stop (bool): 是否启用追踪止损
        timeframe (str): 时间周期
        process_only_new_candles (bool): 是否只处理新K线
    """

    # 策略名称
    name = "BasicStrategy"

    # 经典的Freqtrade策略变量
    minimal_roi = {
        "0": 0.1,  # 0分钟后需要10%的利润
        "30": 0.05,  # 30分钟后需要5%的利润
        "60": 0.02,  # 60分钟后需要2%的利润
        "120": 0,  # 120分钟后任何盈利都可以退出
    }

    stoploss = -0.1  # 10%止损
    trailing_stop = False  # 不启用追踪止损
    timeframe = "1h"  # 1小时时间周期
    process_only_new_candles = True  # 只处理新K线

    # 交易控制选项
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def __init__(self):
        """
        初始化策略实例
        """
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
        # 添加一些基础指标
        # SMA - 简单移动平均线
        dataframe["sma7"] = dataframe["close"].rolling(window=7).mean()
        dataframe["sma25"] = dataframe["close"].rolling(window=25).mean()
        dataframe["sma99"] = dataframe["close"].rolling(window=99).mean()

        # RSI - 相对强弱指标
        dataframe["rsi"] = self._calculate_rsi(dataframe)

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
        dataframe.loc[
            (
                # SMA趋势过滤
                (dataframe["sma7"] > dataframe["sma25"])
                &
                # RSI超卖恢复
                (dataframe["rsi"] > 30)
                &
                # 确保有足够的交易量
                (dataframe["volume"] > 0)
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
        dataframe.loc[
            (
                # SMA趋势过滤
                (dataframe["sma7"] < dataframe["sma25"])
                |
                # RSI超买
                (dataframe["rsi"] > 70)
            ),
            "exit_long",
        ] = 1

        return dataframe

    def _calculate_rsi(self, dataframe: DataFrame, period: int = 14) -> pd.Series:
        """
        计算RSI指标

        参数:
            dataframe (DataFrame): 价格数据
            period (int): RSI周期

        返回:
            Series: RSI值序列
        """
        delta = dataframe["close"].diff()

        # 获取涨跌幅
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        down = down.abs()

        # 计算相对强度
        avg_gain = up.rolling(window=period).mean()
        avg_loss = down.rolling(window=period).mean()

        # 计算相对强度指标
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi