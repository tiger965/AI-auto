# -*- coding: utf-8 -*-
"""
策略辅助模块: 策略构建工具
功能描述: 提供策略构建相关的辅助功能，包括技术指标生成和信号生成器
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-18
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable

# 初始化日志记录器
logger = logging.getLogger(__name__)

class IndicatorLibrary:
    """
    技术指标代码库
    提供常用技术指标的代码模板生成
    """
    
    @staticmethod
    def ema_cross(dataframe, short_period=10, long_period=20):
        """
        创建EMA交叉指标代码片段
        
        参数:
            dataframe: 数据框架名称
            short_period: 短期EMA周期
            long_period: 长期EMA周期
            
        返回:
            代码字符串
        """
        return f"""
        # EMA交叉策略指标
        dataframe['ema_short'] = ta.EMA(dataframe, timeperiod={short_period})
        dataframe['ema_long'] = ta.EMA(dataframe, timeperiod={long_period})
        dataframe['ema_cross'] = qtpylib.crossed_above(
            dataframe['ema_short'], dataframe['ema_long']
        )
        """
    
    @staticmethod
    def volume_spike(dataframe, volume_factor=2):
        """
        创建成交量突增指标代码片段
        
        参数:
            dataframe: 数据框架名称
            volume_factor: 成交量突增系数
            
        返回:
            代码字符串
        """
        return f"""
        # 成交量突增指标
        dataframe['volume_mean'] = dataframe['volume'].rolling(10).mean()
        dataframe['volume_spike'] = dataframe['volume'] > dataframe['volume_mean'] * {volume_factor}
        """
    
    @staticmethod
    def macd(dataframe, fast_period=12, slow_period=26, signal_period=9):
        """
        创建MACD指标代码片段
        
        参数:
            dataframe: 数据框架名称
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        返回:
            代码字符串
        """
        return f"""
        # MACD指标
        macd = ta.MACD(dataframe, 
                        fastperiod={fast_period}, 
                        slowperiod={slow_period}, 
                        signalperiod={signal_period})
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        dataframe['macd_cross'] = qtpylib.crossed_above(
            dataframe['macd'], dataframe['macdsignal']
        )
        """
    
    @staticmethod
    def rsi(dataframe, period=14, overbought=70, oversold=30):
        """
        创建RSI指标代码片段
        
        参数:
            dataframe: 数据框架名称
            period: RSI周期
            overbought: 超买水平
            oversold: 超卖水平
            
        返回:
            代码字符串
        """
        return f"""
        # RSI指标
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod={period})
        dataframe['rsi_overbought'] = dataframe['rsi'] > {overbought}
        dataframe['rsi_oversold'] = dataframe['rsi'] < {oversold}
        dataframe['rsi_cross_up'] = qtpylib.crossed_above(
            dataframe['rsi'], {oversold}
        )
        dataframe['rsi_cross_down'] = qtpylib.crossed_below(
            dataframe['rsi'], {overbought}
        )
        """
    
    @staticmethod
    def bollinger_bands(dataframe, period=20, std_dev=2.0):
        """
        创建布林带指标代码片段
        
        参数:
            dataframe: 数据框架名称
            period: 布林带周期
            std_dev: 标准差倍数
            
        返回:
            代码字符串
        """
        return f"""
        # 布林带指标
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), 
            window={period}, 
            stds={std_dev}
        )
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_width'] = (
            dataframe['bb_upperband'] - dataframe['bb_lowerband']
        ) / dataframe['bb_middleband']
        dataframe['bb_break_up'] = qtpylib.crossed_above(
            dataframe['close'], dataframe['bb_upperband']
        )
        dataframe['bb_break_down'] = qtpylib.crossed_below(
            dataframe['close'], dataframe['bb_lowerband']
        )
        """
    
    @staticmethod
    def stochastic(dataframe, k_period=14, d_period=3, smooth_k=3):
        """
        创建随机指标代码片段
        
        参数:
            dataframe: 数据框架名称
            k_period: K线周期
            d_period: D线周期
            smooth_k: K线平滑系数
            
        返回:
            代码字符串
        """
        return f"""
        # 随机指标
        stoch = ta.STOCH(
            dataframe,
            fastk_period={k_period},
            slowk_period={smooth_k},
            slowk_matype=0,
            slowd_period={d_period},
            slowd_matype=0
        )
        dataframe['slowk'] = stoch['slowk']
        dataframe['slowd'] = stoch['slowd']
        dataframe['stoch_cross'] = qtpylib.crossed_above(
            dataframe['slowk'], dataframe['slowd']
        )
        """
    
    @staticmethod
    def ichimoku(dataframe, tenkan_period=9, kijun_period=26, senkou_period=52):
        """
        创建一目均衡表指标代码片段
        
        参数:
            dataframe: 数据框架名称
            tenkan_period: 转换线周期
            kijun_period: 基准线周期
            senkou_period: 先行带周期
            
        返回:
            代码字符串
        """
        return f"""
        # 一目均衡表指标
        dataframe['tenkan_sen'] = (
            dataframe['high'].rolling({tenkan_period}).max() + 
            dataframe['low'].rolling({tenkan_period}).min()
        ) / 2
        dataframe['kijun_sen'] = (
            dataframe['high'].rolling({kijun_period}).max() + 
            dataframe['low'].rolling({kijun_period}).min()
        ) / 2
        dataframe['senkou_span_a'] = (
            (dataframe['tenkan_sen'] + dataframe['kijun_sen']) / 2
        ).shift({kijun_period})
        dataframe['senkou_span_b'] = (
            (dataframe['high'].rolling({senkou_period}).max() + 
             dataframe['low'].rolling({senkou_period}).min()) / 2
        ).shift({kijun_period})
        dataframe['chikou_span'] = dataframe['close'].shift(-{kijun_period})
        dataframe['tk_cross'] = qtpylib.crossed_above(
            dataframe['tenkan_sen'], dataframe['kijun_sen']
        )
        """
    
    @staticmethod
    def atr(dataframe, period=14, multiplier=2.0):
        """
        创建ATR指标代码片段
        
        参数:
            dataframe: 数据框架名称
            period: ATR周期
            multiplier: ATR倍数（用于计算止损）
            
        返回:
            代码字符串
        """
        return f"""
        # ATR指标
        dataframe['atr'] = ta.ATR(dataframe, timeperiod={period})
        dataframe['atr_stop_long'] = dataframe['close'] - dataframe['atr'] * {multiplier}
        dataframe['atr_stop_short'] = dataframe['close'] + dataframe['atr'] * {multiplier}
        """
    
    @staticmethod
    def sma_cross(dataframe, short_period=5, long_period=10):
        """
        创建SMA交叉指标代码片段
        
        参数:
            dataframe: 数据框架名称
            short_period: 短期SMA周期
            long_period: 长期SMA周期
            
        返回:
            代码字符串
        """
        return f"""
        # SMA交叉指标
        dataframe['sma_short'] = ta.SMA(dataframe, timeperiod={short_period})
        dataframe['sma_long'] = ta.SMA(dataframe, timeperiod={long_period})
        dataframe['sma_cross'] = qtpylib.crossed_above(
            dataframe['sma_short'], dataframe['sma_long']
        )
        """
    
    @staticmethod
    def adx(dataframe, period=14, threshold=25):
        """
        创建ADX指标代码片段
        
        参数:
            dataframe: 数据框架名称
            period: ADX周期
            threshold: ADX阈值
            
        返回:
            代码字符串
        """
        return f"""
        # ADX指标
        dataframe['adx'] = ta.ADX(dataframe, timeperiod={period})
        dataframe['adx_trend'] = dataframe['adx'] > {threshold}
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod={period})
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod={period})
        dataframe['di_cross'] = qtpylib.crossed_above(
            dataframe['plus_di'], dataframe['minus_di']
        )
        """


class SignalGenerator:
    """
    信号生成器
    提供入场和出场信号生成功能
    """
    
    @staticmethod
    def combine_signals(signals, operator='and'):
        """
        组合多个信号
        
        参数:
            signals: 信号列表
            operator: 操作符，可选 'and', 'or'
            
        返回:
            组合后的信号代码字符串
        """
        if not signals:
            return "True"
        
        if operator.lower() == 'and':
            return f"""({" & ".join(signals)})"""
        elif operator.lower() == 'or':
            return f"""({" | ".join(signals)})"""
        else:
            logger.warning(f"不支持的操作符: {operator}，使用'and'代替")
            return f"""({" & ".join(signals)})"""
    
    @staticmethod
    def entry_condition(name, conditions, operator='and'):
        """
        创建入场条件
        
        参数:
            name: 条件名称
            conditions: 条件列表
            operator: 操作符，可选 'and', 'or'
            
        返回:
            入场条件代码字符串
        """
        combined = SignalGenerator.combine_signals(conditions, operator)
        return f"""
        # {name}入场条件
        dataframe['enter_{name.lower()}'] = {combined}
        """
    
    @staticmethod
    def exit_condition(name, conditions, operator='and'):
        """
        创建出场条件
        
        参数:
            name: 条件名称
            conditions: 条件列表
            operator: 操作符，可选 'and', 'or'
            
        返回:
            出场条件代码字符串
        """
        combined = SignalGenerator.combine_signals(conditions, operator)
        return f"""
        # {name}出场条件
        dataframe['exit_{name.lower()}'] = {combined}
        """
    
    @staticmethod
    def trailing_stop(dataframe, atr_period=14, multiplier=2.0, direction='long'):
        """
        创建跟踪止损代码片段
        
        参数:
            dataframe: 数据框架名称
            atr_period: ATR周期
            multiplier: ATR倍数
            direction: 方向，可选 'long', 'short'
            
        返回:
            跟踪止损代码片段
        """
        if direction.lower() == 'long':
            return f"""
            # 多头跟踪止损
            dataframe['atr'] = ta.ATR(dataframe, timeperiod={atr_period})
            dataframe['trailing_stop'] = dataframe['close'].rolling(window=1, min_periods=1).max() - dataframe['atr'] * {multiplier}
            dataframe['exit_trailing_stop'] = dataframe['close'] < dataframe['trailing_stop']
            """
        elif direction.lower() == 'short':
            return f"""
            # 空头跟踪止损
            dataframe['atr'] = ta.ATR(dataframe, timeperiod={atr_period})
            dataframe['trailing_stop'] = dataframe['close'].rolling(window=1, min_periods=1).min() + dataframe['atr'] * {multiplier}
            dataframe['exit_trailing_stop'] = dataframe['close'] > dataframe['trailing_stop']
            """
        else:
            logger.warning(f"不支持的方向: {direction}，使用'long'代替")
            return SignalGenerator.trailing_stop(dataframe, atr_period, multiplier, 'long')
    
    @staticmethod
    def profit_target(dataframe, target_percentage=1.0, direction='long'):
        """
        创建止盈目标代码片段
        
        参数:
            dataframe: 数据框架名称
            target_percentage: 目标百分比
            direction: 方向，可选 'long', 'short'
            
        返回:
            止盈目标代码片段
        """
        target_ratio = 1.0 + target_percentage / 100.0
        loss_ratio = 1.0 - target_percentage / 100.0
        
        if direction.lower() == 'long':
            return f"""
            # 多头止盈
            dataframe['profit_target'] = dataframe['entry_price'] * {target_ratio}
            dataframe['exit_profit_target'] = dataframe['close'] >= dataframe['profit_target']
            """
        elif direction.lower() == 'short':
            return f"""
            # 空头止盈
            dataframe['profit_target'] = dataframe['entry_price'] * {loss_ratio}
            dataframe['exit_profit_target'] = dataframe['close'] <= dataframe['profit_target']
            """
        else:
            logger.warning(f"不支持的方向: {direction}，使用'long'代替")
            return SignalGenerator.profit_target(dataframe, target_percentage, 'long')
    
    @staticmethod
    def stop_loss(dataframe, stop_percentage=2.0, direction='long'):
        """
        创建止损代码片段
        
        参数:
            dataframe: 数据框架名称
            stop_percentage: 止损百分比
            direction: 方向，可选 'long', 'short'
            
        返回:
            止损代码片段
        """
        loss_ratio = 1.0 - stop_percentage / 100.0
        gain_ratio = 1.0 + stop_percentage / 100.0
        
        if direction.lower() == 'long':
            return f"""
            # 多头止损
            dataframe['stop_loss'] = dataframe['entry_price'] * {loss_ratio}
            dataframe['exit_stop_loss'] = dataframe['close'] <= dataframe['stop_loss']
            """
        elif direction.lower() == 'short':
            return f"""
            # 空头止损
            dataframe['stop_loss'] = dataframe['entry_price'] * {gain_ratio}
            dataframe['exit_stop_loss'] = dataframe['close'] >= dataframe['stop_loss']
            """
        else:
            logger.warning(f"不支持的方向: {direction}，使用'long'代替")
            return SignalGenerator.stop_loss(dataframe, stop_percentage, 'long')
    
    @staticmethod
    def time_based_exit(dataframe, bars=10):
        """
        创建基于时间的出场代码片段
        
        参数:
            dataframe: 数据框架名称
            bars: 持有的K线数量
            
        返回:
            基于时间的出场代码片段
        """
        return f"""
        # 基于时间的出场
        dataframe['bar_count'] = dataframe['in_position'].rolling(window=1000, min_periods=1).sum()
        dataframe['exit_time'] = dataframe['bar_count'] >= {bars}
        """


class StrategyTemplateGenerator:
    """
    策略模板生成器
    可以生成完整的策略代码模板
    """
    
    @staticmethod
    def generate_strategy_template(
        strategy_name,
        indicators,
        entry_conditions,
        exit_conditions,
        timeframe="4h",
        stake_currency="USDT",
        stake_amount=100
    ):
        """
        生成完整的策略代码模板
        
        参数:
            strategy_name: 策略名称
            indicators: 指标列表
            entry_conditions: 入场条件列表
            exit_conditions: 出场条件列表
            timeframe: 时间框架
            stake_currency: 交易货币
            stake_amount: 交易金额
            
        返回:
            完整的策略代码模板
        """
        # 格式化策略名称（驼峰命名法）
        formatted_name = ''.join(word.capitalize() for word in strategy_name.split())
        
        # 生成指标代码
        indicators_code = '\n        '.join(indicators)
        
        # 生成入场条件
        entry_code = '\n        '.join(entry_conditions)
        
        # 生成出场条件
        exit_code = '\n        '.join(exit_conditions)
        
        # 生成完整模板
        template = f"""
# 策略名称: {strategy_name}
# 作者: 自动生成
# 时间框架: {timeframe}

import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter


class {formatted_name}Strategy(IStrategy):
    \"\"\"
    {strategy_name} 策略
    
    这是一个自动生成的策略模板。
    \"\"\"
    
    # 策略配置
    timeframe = "{timeframe}"
    stake_currency = "{stake_currency}"
    stake_amount = {stake_amount}
    
    # 最小ROI表
    minimal_roi = {{
        "0": 0.10,
        "30": 0.05,
        "60": 0.03,
        "120": 0.01
    }}
    
    # 止损设置
    stoploss = -0.05
    
    # 跟踪止损设置
    trailing_stop = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = False
    
    # 定义参数（可选）
    # buy_ema_short = IntParameter(3, 50, default=10)
    # buy_ema_long = IntParameter(15, 200, default=50)
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        \"\"\"
        计算指标
        \"\"\"
        # 计算技术指标
        {indicators_code}
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        \"\"\"
        入场信号
        \"\"\"
        # 入场条件
        {entry_code}
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        \"\"\"
        出场信号
        \"\"\"
        # 出场条件
        {exit_code}
        
        return dataframe
        """
        
        return template


class BacktestReportAnalyzer:
    """
    回测报告分析器
    分析回测结果并提供优化建议
    """
    
    @staticmethod
    def analyze_backtest_report(report):
        """
        分析回测报告
        
        参数:
            report: 回测报告数据
            
        返回:
            分析结果和建议
        """
        analysis = {
            "summary": {},
            "recommendations": []
        }
        
        # 分析总体表现
        if "total_trades" in report:
            total_trades = report["total_trades"]
            profit_factor = report.get("profit_factor", 0)
            win_rate = report.get("win_rate", 0)
            
            analysis["summary"]["total_trades"] = total_trades
            analysis["summary"]["profit_factor"] = profit_factor
            analysis["summary"]["win_rate"] = win_rate
            
            # 添加建议
            if total_trades < 10:
                analysis["recommendations"].append(
                    "交易次数过少，建议扩大回测时间范围或优化入场条件以增加交易次数"
                )
            
            if profit_factor < 1.0:
                analysis["recommendations"].append(
                    "盈亏比小于1，建议优化止损或止盈设置以提高盈亏比"
                )
            
            if win_rate < 0.3:
                analysis["recommendations"].append(
                    "胜率过低，建议优化入场条件以提高胜率"
                )
        
        # 分析回撤
        if "max_drawdown_abs" in report:
            max_drawdown = report["max_drawdown_abs"]
            max_drawdown_pct = report.get("max_drawdown_pct", 0)
            
            analysis["summary"]["max_drawdown"] = max_drawdown
            analysis["summary"]["max_drawdown_pct"] = max_drawdown_pct
            
            if max_drawdown_pct > 30:
                analysis["recommendations"].append(
                    "最大回撤过大，建议优化止损策略以控制风险"
                )
        
        # 分析持仓时间
        if "avg_trade_duration" in report:
            avg_duration = report["avg_trade_duration"]
            
            analysis["summary"]["avg_trade_duration"] = avg_duration
            
            # 解析持仓时间（假设格式为 "X days HH:MM:SS"）
            import re
            duration_match = re.search(r"(\d+) days (\d+):(\d+):(\d+)", avg_duration)
            
            if duration_match:
                days = int(duration_match.group(1))
                hours = int(duration_match.group(2))
                
                if days > 7:
                    analysis["recommendations"].append(
                        "平均持仓时间过长，建议考虑添加基于时间的出场条件"
                    )
        
        return analysis


# 辅助函数

def generate_complete_strategy(strategy_name, indicator_settings, entry_settings, exit_settings):
    """
    生成完整的策略代码
    
    参数:
        strategy_name: 策略名称
        indicator_settings: 指标设置列表
        entry_settings: 入场设置
        exit_settings: 出场设置
        
    返回:
        完整的策略代码
    """
    indicators = []
    
    # 生成指标代码
    for indicator in indicator_settings:
        indicator_type = indicator.get("type")
        if hasattr(IndicatorLibrary, indicator_type):
            indicator_method = getattr(IndicatorLibrary, indicator_type)
            indicators.append(indicator_method("dataframe", **indicator.get("params", {})))
    
    # 生成入场条件
    entry_conditions = []
    if entry_settings:
        for entry in entry_settings:
            conditions = entry.get("conditions", [])
            operator = entry.get("operator", "and")
            entry_conditions.append(
                SignalGenerator.entry_condition(entry.get("name", "default"), conditions, operator)
            )
    
    # 生成出场条件
    exit_conditions = []
    if exit_settings:
        for exit in exit_settings:
            conditions = exit.get("conditions", [])
            operator = exit.get("operator", "and")
            exit_conditions.append(
                SignalGenerator.exit_condition(exit.get("name", "default"), conditions, operator)
            )
    
    # 生成策略模板
    return StrategyTemplateGenerator.generate_strategy_template(
        strategy_name,
        indicators,
        entry_conditions,
        exit_conditions
    )