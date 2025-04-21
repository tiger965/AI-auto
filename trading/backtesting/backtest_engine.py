""" "
模块名称：trading.backtesting.backtest_engine
功能描述：回测引擎，负责执行策略回测、生成交易信号和计算回测结果
版本：1.0
创建日期：2025-04-20
作者：窗口9.3开发者
"""

import os
import json
import logging
import modules.nlp as np
import config.paths as pd
from typing import Dict, List, Union, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import importlib
import inspect
import copy

from trading.backtesting.data_manager import DataManager
from trading.backtesting.performance_analyzer import PerformanceAnalyzer

# 设置日志记录器
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎类，用于执行策略回测、生成交易信号和计算回测结果

    属性:
        data_manager (DataManager): 数据管理器实例
        performance_analyzer (PerformanceAnalyzer): 性能分析器实例
        config (Dict): 回测配置
        strategy (Any): 策略实例
        trades (pd.DataFrame): 交易记录
        equity_curve (pd.DataFrame): 权益曲线
        signals (Dict[str, pd.DataFrame]): 交易信号
        current_results (Dict): 当前回测结果
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        data_manager: Optional[DataManager] = None,
        performance_analyzer: Optional[PerformanceAnalyzer] = None,
    ):
        """
        初始化回测引擎

        参数:
            config (Dict, 可选): 回测配置字典
            data_manager (DataManager, 可选): 数据管理器实例
            performance_analyzer (PerformanceAnalyzer, 可选): 性能分析器实例

        返回:
            无

        异常:
            ValueError: 当参数无效时抛出异常
        """
        # 初始化组件
        self.data_manager = data_manager or DataManager()
        self.performance_analyzer = performance_analyzer or PerformanceAnalyzer()

        # 设置默认配置
        self.config = {
            "pairs": [],  # 交易对列表
            "timeframes": ["1h"],  # 时间周期列表
            "start_date": None,  # 回测开始日期
            "end_date": None,  # 回测结束日期
            "initial_capital": 10000,  # 初始资金
            "stake_amount": 1000,  # 单笔交易金额
            "fee": 0.001,  # 交易费率 (0.1%)
            "slippage": 0.0005,  # 滑点 (0.05%)
            "strategy": None,  # 策略名称或实例
            "leverage": 1,  # 杠杆倍数
            # 仓位大小策略 ('fixed', 'risk_percentage', 'risk_amount')
            "position_sizing": "fixed",
            # 风险百分比 (仅当 position_sizing='risk_percentage' 时使用)
            "risk_percentage": 0.01,
            "max_open_positions": 5,  # 最大持仓数量
            "ohlcv_columns": {  # OHLCV 列名映射
                "date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            },
            "execution_mode": "live",  # 执行模式 ('live', 'open', 'close')
        }

        # 更新自定义配置
        if config:
            self.config.update(config)

        # 初始化变量
        self.strategy = None
        self.trades = None
        self.equity_curve = None
        self.signals = {}
        self.current_results = None

        logger.info("初始化回测引擎")

    def load_strategy(self, strategy: Union[str, Any]) -> None:
        """
        加载策略

        参数:
            strategy (Union[str, Any]): 策略名称（字符串）或策略实例

        返回:
            无

        异常:
            ValueError: 当策略无效或无法加载时抛出异常
            ImportError: 当无法导入策略模块时抛出异常
        """
        # 如果已提供策略实例，直接使用
        if not isinstance(strategy, str):
            self.strategy = strategy
            self.config["strategy"] = strategy.__class__.__name__
            logger.info(f"加载策略实例: {self.config['strategy']}")
            return

        try:
            # 尝试从策略模块导入
            module_path, class_name = strategy.rsplit(".", 1)
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, class_name)

            # 检查策略类是否有必要的方法
            required_methods = [
                "populate_indicators",
                "populate_entry_trend",
                "populate_exit_trend",
            ]
            for method in required_methods:
                if not hasattr(strategy_class, method) or not callable(
                    getattr(strategy_class, method)
                ):
                    raise ValueError(f"策略类 {class_name} 缺少必要的方法: {method}")

            # 创建策略实例
            self.strategy = strategy_class()
            self.config["strategy"] = class_name

            logger.info(f"加载策略: {self.config['strategy']}")

        except (ImportError, AttributeError) as e:
            logger.error(f"无法加载策略 {strategy}: {str(e)}")
            raise ValueError(f"无法加载策略 {strategy}: {str(e)}")

    def prepare_data(
        self,
        pairs: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        准备回测数据

        参数:
            pairs (List[str], 可选): 交易对列表
            timeframes (List[str], 可选): 时间周期列表
            start_date (Union[str, datetime], 可选): 开始日期
            end_date (Union[str, datetime], 可选): 结束日期

        返回:
            Dict[str, Dict[str, pd.DataFrame]]: 按交易对和时间周期组织的数据字典

        异常:
            ValueError: 当参数无效时抛出异常
        """
        # 使用配置中的值（如果未指定参数）
        pairs = pairs or self.config.get("pairs")
        timeframes = timeframes or self.config.get("timeframes")
        start_date = start_date or self.config.get("start_date")
        end_date = end_date or self.config.get("end_date")

        # 确保至少有一个交易对和时间周期
        if not pairs:
            raise ValueError("未指定交易对")

        if not timeframes:
            raise ValueError("未指定时间周期")

        # 准备数据
        data_dict = self.data_manager.prepare_data_for_backtesting(
            pairs=pairs, timeframes=timeframes, start_date=start_date, end_date=end_date
        )

        return data_dict

    def run_backtest(
        self,
        strategy: Optional[Union[str, Any]] = None,
        pairs: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        initial_capital: Optional[float] = None,
        stake_amount: Optional[float] = None,
        fee: Optional[float] = None,
        **kwargs,
    ) -> Dict:
        """
        运行回测

        参数:
            strategy (Union[str, Any], 可选): 策略名称或实例
            pairs (List[str], 可选): 交易对列表
            timeframes (List[str], 可选): 时间周期列表
            start_date (Union[str, datetime], 可选): 开始日期
            end_date (Union[str, datetime], 可选): 结束日期
            initial_capital (float, 可选): 初始资金
            stake_amount (float, 可选): 单笔交易金额
            fee (float, 可选): 交易费率
            **kwargs: 其他配置参数

        返回:
            Dict: 回测结果字典

        异常:
            ValueError: 当参数无效或回测失败时抛出异常
        """
        # 更新配置
        if strategy:
            self.load_strategy(strategy)
        elif self.strategy is None:
            strategy = self.config.get("strategy")
            if strategy:
                self.load_strategy(strategy)
            else:
                raise ValueError("未指定策略")

        # 更新其他配置参数
        if pairs:
            self.config["pairs"] = pairs
        if timeframes:
            self.config["timeframes"] = timeframes
        if start_date:
            self.config["start_date"] = start_date
        if end_date:
            self.config["end_date"] = end_date
        if initial_capital:
            self.config["initial_capital"] = initial_capital
        if stake_amount:
            self.config["stake_amount"] = stake_amount
        if fee:
            self.config["fee"] = fee

        # 更新其他关键字参数
        self.config.update(kwargs)

        try:
            # 准备数据
            data_dict = self.prepare_data(
                pairs=self.config["pairs"],
                timeframes=self.config["timeframes"],
                start_date=self.config["start_date"],
                end_date=self.config["end_date"],
            )

            # 生成交易信号
            self.signals = self._generate_signals(data_dict)

            # 执行模拟交易
            self.trades, self.equity_curve = self._execute_trades(self.signals)

            # 分析性能
            self.performance_analyzer.set_trades(self.trades)
            self.performance_analyzer.set_equity_curve(self.equity_curve)
            performance_metrics = self.performance_analyzer.calculate_metrics()

            # 编译结果
            self.current_results = {
                "config": self.config.copy(),
                "performance": performance_metrics,
                "trades_count": len(self.trades),
                "start_date": self.config["start_date"],
                "end_date": self.config["end_date"],
                "pairs": self.config["pairs"],
                "timeframes": self.config["timeframes"],
                "strategy": self.config["strategy"],
                "initial_capital": self.config["initial_capital"],
                "final_capital": float(self.equity_curve["equity"].iloc[-1]),
                "profit_abs": float(performance_metrics["total_profit_abs"]),
                "profit_pct": float(performance_metrics["total_profit_pct"]),
                "backtest_completed": True,
            }

            logger.info(
                f"完成回测: {self.config['strategy']}, 交易对: {self.config['pairs']}, "
                f"总收益: {performance_metrics['total_profit_pct']:.2f}%"
            )

            return self.current_results

        except Exception as e:
            logger.error(f"回测失败: {str(e)}")
            raise ValueError(f"回测失败: {str(e)}")

    def _generate_signals(
        self, data_dict: Dict[str, Dict[str, pd.DataFrame]]
    ) -> Dict[str, pd.DataFrame]:
        """
        生成交易信号

        参数:
            data_dict (Dict[str, Dict[str, pd.DataFrame]]): 按交易对和时间周期组织的数据字典

        返回:
            Dict[str, pd.DataFrame]: 按交易对组织的信号DataFrame

        异常:
            ValueError: 当策略无效或生成信号失败时抛出异常
        """
        if self.strategy is None:
            raise ValueError("未加载策略，无法生成信号")

        signals = {}

        for pair, timeframe_dict in data_dict.items():
            # 默认使用配置中的第一个时间周期
            timeframe = self.config["timeframes"][0]
            if timeframe not in timeframe_dict:
                available_timeframes = list(timeframe_dict.keys())
                if not available_timeframes:
                    logger.warning(f"交易对 {pair} 没有可用的数据，跳过")
                    continue
                timeframe = available_timeframes[0]
                logger.warning(
                    f"交易对 {pair} 没有时间周期 {timeframe} 的数据，使用 {timeframe} 代替"
                )

            # 获取数据
            df = timeframe_dict[timeframe].copy()

            try:
                # 确保列名符合策略要求
                df = self._rename_columns(df)

                # 应用策略指标
                df = self.strategy.populate_indicators(df, {"pair": pair})

                # 生成入场信号
                df = self.strategy.populate_entry_trend(df, {"pair": pair})

                # 生成出场信号
                df = self.strategy.populate_exit_trend(df, {"pair": pair})

                # 确保信号列存在
                if "enter_long" not in df.columns:
                    df["enter_long"] = False

                if "exit_long" not in df.columns:
                    df["exit_long"] = False

                if "enter_short" not in df.columns:
                    df["enter_short"] = False

                if "exit_short" not in df.columns:
                    df["exit_short"] = False

                # 存储信号
                signals[pair] = df

                logger.info(
                    f"生成信号: {pair}, 数据点: {len(df)}, "
                    f"做多信号: {df['enter_long'].sum()}, 做空信号: {df['enter_short'].sum()}"
                )

            except Exception as e:
                logger.error(f"为交易对 {pair} 生成信号时出错: {str(e)}")
                raise ValueError(f"为交易对 {pair} 生成信号时出错: {str(e)}")

        return signals

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重命名OHLCV列以符合策略要求

        参数:
            df (pd.DataFrame): 原始数据DataFrame

        返回:
            pd.DataFrame: 重命名列后的DataFrame
        """
        # 获取列名映射
        column_map = self.config["ohlcv_columns"]

        # 创建反向映射
        reverse_map = {v: k for k, v in column_map.items()}

        # 重命名列
        rename_dict = {}
        for col in df.columns:
            if col in reverse_map:
                rename_dict[col] = reverse_map[col]

        if rename_dict:
            df = df.rename(columns=rename_dict)

        return df

    def _execute_trades(
        self, signals: Dict[str, pd.DataFrame]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        执行模拟交易

        参数:
            signals (Dict[str, pd.DataFrame]): 按交易对组织的信号DataFrame

        返回:
            Tuple[pd.DataFrame, pd.DataFrame]: 交易记录和权益曲线

        异常:
            ValueError: 当执行交易失败时抛出异常
        """
        # 初始化变量
        initial_capital = self.config["initial_capital"]
        stake_amount = self.config["stake_amount"]
        fee = self.config["fee"]
        slippage = self.config["slippage"]
        leverage = self.config["leverage"]
        max_open_positions = self.config["max_open_positions"]
        position_sizing = self.config["position_sizing"]
        risk_percentage = self.config.get("risk_percentage", 0.01)

        # 创建交易列表和权益曲线的基础
        trades_list = []
        equity_history = []

        # 合并所有信号的日期
        all_dates = set()
        for pair, df in signals.items():
            all_dates.update(df["date"].tolist())

        all_dates = sorted(all_dates)

        # 初始化模拟交易状态
        available_capital = initial_capital
        open_positions = (
            {}
            # 格式: {pair: {'entry_date': date, 'entry_price': price, 'amount': amount, ...}}
        )
        current_capital = initial_capital

        # 按时间顺序遍历每个日期点
        for current_date in all_dates:
            # 检查是否需要平仓现有头寸
            pairs_to_close = []
            for pair, position in open_positions.items():
                if pair in signals and current_date in signals[pair]["date"].values:
                    # 获取当前K线
                    signal_df = signals[pair]
                    current_index = signal_df[signal_df["date"] == current_date].index[
                        0
                    ]
                    current_row = signal_df.loc[current_index]

                    # 检查是否有出场信号
                    if current_row["exit_long"] and position["type"] == "long":
                        pairs_to_close.append(pair)
                    elif current_row["exit_short"] and position["type"] == "short":
                        pairs_to_close.append(pair)

            # 平仓头寸
            for pair in pairs_to_close:
                position = open_positions[pair]
                signal_df = signals[pair]
                current_index = signal_df[signal_df["date"]
                                          == current_date].index[0]
                current_row = signal_df.loc[current_index]

                # 获取出场价格（根据执行模式）
                exit_price = self._get_execution_price(current_row, "exit")

                # 计算滑点
                if position["type"] == "long":
                    exit_price = exit_price * (1 - slippage)
                else:  # short
                    exit_price = exit_price * (1 + slippage)

                # 计算收益
                if position["type"] == "long":
                    profit_pct = (
                        (exit_price /
                         position["entry_price"] - 1) * 100 * leverage
                    )
                    profit_abs = (
                        position["cost"]
                        * (exit_price / position["entry_price"] - 1)
                        * leverage
                    )
                else:  # short
                    profit_pct = (
                        (position["entry_price"] /
                         exit_price - 1) * 100 * leverage
                    )
                    profit_abs = (
                        position["cost"]
                        * (position["entry_price"] / exit_price - 1)
                        * leverage
                    )

                # 应用交易费用
                fee_amount = position["cost"] * fee
                profit_abs -= fee_amount

                # 更新资金
                available_capital += position["cost"] + profit_abs
                current_capital += profit_abs

                # 记录交易
                trade = {
                    "pair": pair,
                    "entry_date": position["entry_date"],
                    "exit_date": current_date,
                    "type": position["type"],
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "amount": position["amount"],
                    "cost": position["cost"],
                    "fee": fee_amount,
                    "profit_abs": profit_abs,
                    "profit_pct": profit_pct,
                    "leverage": leverage,
                }
                trades_list.append(trade)

                # 从开仓列表中移除
                del open_positions[pair]

                logger.info(
                    f"平仓: {pair}, 类型: {position['type']}, 收益: {profit_pct:.2f}%, "
                    f"{profit_abs:.2f}"
                )

            # 检查是否可以开仓新头寸
            for pair, signal_df in signals.items():
                # 如果已经持有该交易对，跳过
                if pair in open_positions:
                    continue

                # 如果当前日期不在信号DataFrame中，跳过
                if current_date not in signal_df["date"].values:
                    continue

                # 获取当前K线
                current_index = signal_df[signal_df["date"]
                                          == current_date].index[0]
                current_row = signal_df.loc[current_index]

                # 检查是否有入场信号
                if current_row["enter_long"] or current_row["enter_short"]:
                    # 检查是否达到最大持仓数量
                    if len(open_positions) >= max_open_positions:
                        continue

                    position_type = "long" if current_row["enter_long"] else "short"

                    # 获取入场价格（根据执行模式）
                    entry_price = self._get_execution_price(
                        current_row, "entry")

                    # 计算滑点
                    if position_type == "long":
                        entry_price = entry_price * (1 + slippage)
                    else:  # short
                        entry_price = entry_price * (1 - slippage)

                    # 计算仓位大小
                    cost, amount = self._calculate_position_size(
                        available_capital=available_capital,
                        entry_price=entry_price,
                        position_type=position_type,
                        position_sizing=position_sizing,
                        risk_percentage=risk_percentage,
                        stake_amount=stake_amount,
                        pair=pair,
                        signal_df=signal_df,
                        current_index=current_index,
                    )

                    # 如果可用资金不足，跳过
                    if cost > available_capital:
                        continue

                    # 应用交易费用
                    fee_amount = cost * fee
                    cost_with_fee = cost + fee_amount

                    # 确保有足够的资金支付费用
                    if cost_with_fee > available_capital:
                        continue

                    # 更新资金
                    available_capital -= cost_with_fee

                    # 记录开仓
                    open_positions[pair] = {
                        "entry_date": current_date,
                        "entry_price": entry_price,
                        "amount": amount,
                        "cost": cost,
                        "fee": fee_amount,
                        "type": position_type,
                    }

                    logger.info(
                        f"开仓: {pair}, 类型: {position_type}, 价格: {entry_price}, "
                        f"金额: {cost:.2f}, 数量: {amount:.6f}"
                    )

            # 计算当前权益（可用资金 + 持仓市值）
            portfolio_value = available_capital
            for pair, position in open_positions.items():
                signal_df = signals[pair]
                if current_date in signal_df["date"].values:
                    current_index = signal_df[signal_df["date"] == current_date].index[
                        0
                    ]
                    current_row = signal_df.loc[current_index]
                    current_price = current_row["close"]

                    if position["type"] == "long":
                        position_value = position["amount"] * current_price
                        unrealized_profit = position["amount"] * (
                            current_price - position["entry_price"]
                        )
                    else:  # short
                        position_value = position["cost"]
                        unrealized_profit = position["amount"] * (
                            position["entry_price"] - current_price
                        )

                    portfolio_value += position_value + unrealized_profit * leverage

            # 记录权益
            equity_history.append(
                {
                    "date": current_date,
                    "equity": portfolio_value,
                    "available_capital": available_capital,
                    "open_positions": len(open_positions),
                }
            )

        # 平仓所有剩余头寸（使用最后的价格）
        for pair, position in list(open_positions.items()):
            signal_df = signals[pair]
            last_row = signal_df.iloc[-1]
            last_date = last_row["date"]

            # 获取出场价格
            exit_price = last_row["close"]

            # 计算滑点
            if position["type"] == "long":
                exit_price = exit_price * (1 - slippage)
            else:  # short
                exit_price = exit_price * (1 + slippage)

            # 计算收益
            if position["type"] == "long":
                profit_pct = (
                    exit_price / position["entry_price"] - 1) * 100 * leverage
                profit_abs = (
                    position["cost"]
                    * (exit_price / position["entry_price"] - 1)
                    * leverage
                )
            else:  # short
                profit_pct = (position["entry_price"] /
                              exit_price - 1) * 100 * leverage
                profit_abs = (
                    position["cost"]
                    * (position["entry_price"] / exit_price - 1)
                    * leverage
                )

            # 应用交易费用
            fee_amount = position["cost"] * fee
            profit_abs -= fee_amount

            # 记录交易
            trade = {
                "pair": pair,
                "entry_date": position["entry_date"],
                "exit_date": last_date,
                "type": position["type"],
                "entry_price": position["entry_price"],
                "exit_price": exit_price,
                "amount": position["amount"],
                "cost": position["cost"],
                "fee": fee_amount,
                "profit_abs": profit_abs,
                "profit_pct": profit_pct,
                "leverage": leverage,
            }
            trades_list.append(trade)

            logger.info(
                f"回测结束平仓: {pair}, 类型: {position['type']}, 收益: {profit_pct:.2f}%, "
                f"{profit_abs:.2f}"
            )

        # 转换为DataFrame
        trades_df = pd.DataFrame(trades_list)
        equity_df = pd.DataFrame(equity_history)

        # 确保日期列是datetime类型
        if not trades_df.empty:
            if not pd.api.types.is_datetime64_dtype(trades_df["entry_date"]):
                trades_df["entry_date"] = pd.to_datetime(
                    trades_df["entry_date"])

            if not pd.api.types.is_datetime64_dtype(trades_df["exit_date"]):
                trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"])

        if not equity_df.empty:
            if not pd.api.types.is_datetime64_dtype(equity_df["date"]):
                equity_df["date"] = pd.to_datetime(equity_df["date"])

        # 计算回撤
        if not equity_df.empty:
            equity_df["equity_peak"] = equity_df["equity"].cummax()
            equity_df["drawdown_abs"] = equity_df["equity_peak"] - \
                equity_df["equity"]
            equity_df["drawdown_pct"] = (
                equity_df["drawdown_abs"] / equity_df["equity_peak"]
            ) * 100

        return trades_df, equity_df

    def _get_execution_price(self, row: pd.Series, action: str) -> float:
        """
        获取执行价格

        参数:
            row (pd.Series): 当前K线数据
            action (str): 操作类型 ('entry' 或 'exit')

        返回:
            float: 执行价格
        """
        execution_mode = self.config["execution_mode"]

        if execution_mode == "live":
            # 使用开盘价（假设是在信号产生后的下一个K线开盘时执行）
            return row["open"]

        elif execution_mode == "close":
            # 使用收盘价（假设是在当前K线收盘时执行）
            return row["close"]

        elif execution_mode == "open":
            # 使用开盘价（假设是在当前K线开盘时执行）
            return row["open"]

        else:
            # 默认使用收盘价
            return row["close"]

    def _calculate_position_size(
        self,
        available_capital: float,
        entry_price: float,
        position_type: str,
        position_sizing: str,
        risk_percentage: float,
        stake_amount: float,
        pair: str,
        signal_df: pd.DataFrame,
        current_index: int,
    ) -> Tuple[float, float]:
        """
        计算仓位大小

        参数:
            available_capital (float): 可用资金
            entry_price (float): 入场价格
            position_type (str): 仓位类型 ('long' 或 'short')
            position_sizing (str): 仓位大小策略
            risk_percentage (float): 风险百分比
            stake_amount (float): 单笔交易金额
            pair (str): 交易对
            signal_df (pd.DataFrame): 信号DataFrame
            current_index (int): 当前行索引

        返回:
            Tuple[float, float]: 交易成本和交易数量
        """
        if position_sizing == "fixed":
            # 固定金额
            cost = min(stake_amount, available_capital)
            amount = cost / entry_price

        elif position_sizing == "risk_percentage":
            # 基于风险百分比
            stop_loss = None

            # 尝试从策略获取止损价格
            if hasattr(self.strategy, "get_stop_loss"):
                stop_loss = self.strategy.get_stop_loss(
                    pair=pair,
                    trade_type=position_type,
                    current_rate=entry_price,
                    current_time=signal_df.loc[current_index, "date"],
                    data=signal_df,
                    current_index=current_index,
                )

            # 如果策略没有提供止损价格，使用默认值
            if stop_loss is None:
                if position_type == "long":
                    # 默认将止损设置为入场价格的95%
                    stop_loss = entry_price * 0.95
                else:  # short
                    # 默认将止损设置为入场价格的105%
                    stop_loss = entry_price * 1.05

            # 计算止损距离
            if position_type == "long":
                stop_distance = entry_price - stop_loss
            else:  # short
                stop_distance = stop_loss - entry_price

            # 防止除以零
            if stop_distance <= 0:
                stop_distance = entry_price * 0.01  # 默认1%

            # 计算风险金额
            risk_amount = available_capital * risk_percentage

            # 计算仓位大小
            cost = risk_amount * entry_price / stop_distance
            cost = min(cost, available_capital)
            amount = cost / entry_price

        elif position_sizing == "risk_amount":
            # 风险固定金额
            risk_amount = self.config.get("risk_amount", stake_amount * 0.01)

            # 尝试从策略获取止损价格
            stop_loss = None
            if hasattr(self.strategy, "get_stop_loss"):
                stop_loss = self.strategy.get_stop_loss(
                    pair=pair,
                    trade_type=position_type,
                    current_rate=entry_price,
                    current_time=signal_df.loc[current_index, "date"],
                    data=signal_df,
                    current_index=current_index,
                )

            # 如果策略没有提供止损价格，使用默认值
            if stop_loss is None:
                if position_type == "long":
                    stop_loss = entry_price * 0.95
                else:  # short
                    stop_loss = entry_price * 1.05

            # 计算止损距离
            if position_type == "long":
                stop_distance = entry_price - stop_loss
            else:  # short
                stop_distance = stop_loss - entry_price

            # 防止除以零
            if stop_distance <= 0:
                stop_distance = entry_price * 0.01

            # 计算仓位大小
            cost = risk_amount * entry_price / stop_distance
            cost = min(cost, available_capital)
            amount = cost / entry_price

        else:
            # 默认使用固定金额
            cost = min(stake_amount, available_capital)
            amount = cost / entry_price

        return cost, amount

    def optimize_hyperparameters(
        self,
        strategy: Union[str, Any],
        param_space: Dict[str, List[Any]],
        pairs: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        initial_capital: Optional[float] = None,
        metric: str = "profit_pct",
        max_evals: int = 10,
        random_state: Optional[int] = None,
    ) -> Dict:
        """
        优化策略超参数

        参数:
            strategy (Union[str, Any]): 策略名称或实例
            param_space (Dict[str, List[Any]]): 参数空间
            pairs (List[str], 可选): 交易对列表
            timeframes (List[str], 可选): 时间周期列表
            start_date (Union[str, datetime], 可选): 开始日期
            end_date (Union[str, datetime], 可选): 结束日期
            initial_capital (float, 可选): 初始资金
            metric (str): 优化目标指标
            max_evals (int): 最大评估次数
            random_state (int, 可选): 随机种子

        返回:
            Dict: 优化结果字典

        异常:
            ValueError: 当参数无效或优化失败时抛出异常
        """
        # 加载策略
        self.load_strategy(strategy)

        # 更新配置
        if pairs:
            self.config["pairs"] = pairs
        if timeframes:
            self.config["timeframes"] = timeframes
        if start_date:
            self.config["start_date"] = start_date
        if end_date:
            self.config["end_date"] = end_date
        if initial_capital:
            self.config["initial_capital"] = initial_capital

        logger.info(
            f"开始超参数优化: {self.config['strategy']}, 参数空间: {param_space}, "
            f"最大评估次数: {max_evals}"
        )

        # 设置随机种子
        np.random.seed(random_state)

        # 准备数据（只需要准备一次）
        data_dict = self.prepare_data(
            pairs=self.config["pairs"],
            timeframes=self.config["timeframes"],
            start_date=self.config["start_date"],
            end_date=self.config["end_date"],
        )

        # 生成参数组合
        param_combinations = self._generate_param_combinations(
            param_space, max_evals)

        # 评估每个参数组合
        results = []
        best_result = None
        best_score = float(
            "-inf") if metric != "max_drawdown_pct" else float("inf")

        for i, params in enumerate(param_combinations):
            try:
                # 更新策略参数
                for param, value in params.items():
                    setattr(self.strategy, param, value)

                # 运行回测
                result = self.run_backtest()

                # 获取评估指标
                score = result["performance"].get(metric)
                if score is None:
                    if metric == "profit_pct":
                        score = result["profit_pct"]
                    elif metric == "sharpe_ratio":
                        score = result["performance"].get("sharpe_ratio")
                    else:
                        logger.warning(
                            f"找不到评估指标: {metric}，使用 'profit_pct' 代替"
                        )
                        score = result["profit_pct"]

                # 保存结果
                result_entry = {
                    "params": params,
                    "score": score,
                    "metrics": {
                        "profit_pct": result["profit_pct"],
                        "profit_abs": result["profit_abs"],
                        "max_drawdown_pct": result["performance"].get(
                            "max_drawdown_pct"
                        ),
                        "sharpe_ratio": result["performance"].get("sharpe_ratio"),
                        "trades_count": result["trades_count"],
                    },
                }
                results.append(result_entry)

                # 更新最佳结果
                is_better = False
                if metric == "max_drawdown_pct":
                    # 对于回撤，越小越好
                    is_better = score < best_score
                else:
                    # 对于其他指标，越大越好
                    is_better = score > best_score

                if is_better:
                    best_result = result_entry
                    best_score = score

                logger.info(
                    f"评估参数 [{i+1}/{len(param_combinations)}]: {params}, "
                    f"得分 ({metric}): {score}"
                )

            except Exception as e:
                logger.error(f"评估参数时出错: {str(e)}")
                continue

        # 编译优化结果
        optimization_result = {
            "best_params": best_result["params"] if best_result else None,
            "best_score": best_score,
            "metric": metric,
            "all_results": results,
            "strategy": self.config["strategy"],
            "pairs": self.config["pairs"],
            "timeframes": self.config["timeframes"],
            "start_date": self.config["start_date"],
            "end_date": self.config["end_date"],
            "evaluations": len(results),
        }

        logger.info(
            f"完成超参数优化: 最佳参数: {optimization_result['best_params']}, "
            f"最佳得分 ({metric}): {best_score}"
        )

        return optimization_result

    def _generate_param_combinations(
        self, param_space: Dict[str, List[Any]], max_evals: int
    ) -> List[Dict]:
        """
        生成参数组合

        参数:
            param_space (Dict[str, List[Any]]): 参数空间
            max_evals (int): 最大评估次数

        返回:
            List[Dict]: 参数组合列表
        """
        # 计算所有可能的组合数量
        total_combinations = 1
        for values in param_space.values():
            total_combinations *= len(values)

        # 如果组合数量小于最大评估次数，返回所有组合
        if total_combinations <= max_evals:
            import itertools

            param_names = list(param_space.keys())
            param_values = list(param_space.values())
            combinations = list(itertools.product(*param_values))

            return [dict(zip(param_names, combination)) for combination in combinations]

        # 否则，随机采样
        combinations = []
        for _ in range(max_evals):
            params = {}
            for name, values in param_space.items():
                params[name] = np.random.choice(values)
            combinations.append(params)

        return combinations

    def save_results(
        self, output_dir: str = "results", filename_prefix: str = None
    ) -> Dict[str, str]:
        """
        保存回测结果

        参数:
            output_dir (str): 输出目录
            filename_prefix (str, 可选): 文件名前缀

        返回:
            Dict[str, str]: 保存的文件路径字典

        异常:
            ValueError: 当保存失败时抛出异常
        """
        if self.current_results is None:
            raise ValueError("没有可保存的回测结果")

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名前缀
        if filename_prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            strategy_name = self.config["strategy"]
            filename_prefix = f"{strategy_name}_{timestamp}"

        saved_files = {}

        try:
            # 保存配置
            config_file = os.path.join(
                output_dir, f"{filename_prefix}_config.json")
            with open(config_file, "w") as f:
                # 需要处理不可序列化的对象
                config_copy = self.config.copy()
                if "strategy" in config_copy and not isinstance(
                    config_copy["strategy"], str
                ):
                    config_copy["strategy"] = config_copy["strategy"].__class__.__name__
                json.dump(config_copy, f, indent=4, default=str)
            saved_files["config"] = config_file

            # 保存性能指标
            metrics_file = os.path.join(
                output_dir, f"{filename_prefix}_metrics.json")
            with open(metrics_file, "w") as f:
                json.dump(
                    self.current_results["performance"], f, indent=4, default=str)
            saved_files["metrics"] = metrics_file

            # 保存交易记录
            if self.trades is not None and not self.trades.empty:
                trades_file = os.path.join(
                    output_dir, f"{filename_prefix}_trades.csv")
                self.trades.to_csv(trades_file, index=False)
                saved_files["trades"] = trades_file

            # 保存权益曲线
            if self.equity_curve is not None and not self.equity_curve.empty:
                equity_file = os.path.join(
                    output_dir, f"{filename_prefix}_equity.csv")
                self.equity_curve.to_csv(equity_file, index=False)
                saved_files["equity"] = equity_file

            # 使用性能分析器导出结果
            if hasattr(self.performance_analyzer, "export_results"):
                export_dir = os.path.join(output_dir, filename_prefix)
                exported_files = self.performance_analyzer.export_results(
                    export_dir)
                saved_files.update(exported_files)

            logger.info(f"保存回测结果: {saved_files}")

            return saved_files

        except Exception as e:
            logger.error(f"保存回测结果时出错: {str(e)}")
            raise ValueError(f"保存回测结果时出错: {str(e)}")

    def export_report(self, output_file: str, include_trades: bool = True) -> str:
        """
        导出回测报告

        参数:
            output_file (str): 输出文件路径
            include_trades (bool): 是否包含交易记录

        返回:
            str: 报告文件路径

        异常:
            ValueError: 当导出失败时抛出异常
        """
        if self.current_results is None:
            raise ValueError("没有可导出的回测结果")

        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # 获取性能指标摘要
            summary = self.performance_analyzer.get_summary(
                include_trade_list=include_trades
            )

            # 构建报告内容
            report = []

            # 标题
            strategy_name = self.config["strategy"]
            pairs_str = ", ".join(self.config["pairs"])
            report.append(f"# 回测报告: {strategy_name}")
            report.append(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")

            # 基本信息
            report.append("## 基本信息")
            report.append(f"- 策略: {strategy_name}")
            report.append(f"- 交易对: {pairs_str}")
            report.append(f"- 时间周期: {', '.join(self.config['timeframes'])}")
            report.append(
                f"- 回测期间: {summary['trading_period']['start_date']} 至 {summary['trading_period']['end_date']} ({summary['trading_period']['total_days']} 天)"
            )
            report.append(f"- 初始资金: {self.config['initial_capital']}")
            report.append(f"- 单笔交易金额: {self.config['stake_amount']}")
            report.append(f"- 交易费率: {self.config['fee'] * 100}%")
            report.append(f"- 杠杆倍数: {self.config['leverage']}")
            report.append("")

            # 性能指标
            report.append("## 性能指标")
            report.append("### 收益")
            report.append(
                f"- 总收益: {summary['performance']['total_profit_pct']}")
            report.append(
                f"- 年化收益率: {summary['performance']['annualized_return']}"
            )
            report.append(f"- 利润因子: {summary['performance']['profit_factor']}")
            report.append("")

            report.append("### 风险")
            report.append(f"- 最大回撤: {summary['risk']['max_drawdown_pct']}")
            report.append(
                f"- 最大回撤持续时间: {summary['risk']['max_drawdown_duration']}"
            )
            report.append(f"- 波动率: {summary['risk']['volatility']}")
            report.append("")

            report.append("### 风险调整收益")
            report.append(f"- 夏普比率: {summary['performance']['sharpe_ratio']}")
            report.append(
                f"- 索提诺比率: {summary['performance']['sortino_ratio']}")
            report.append(f"- 卡玛比率: {summary['performance']['calmar_ratio']}")
            report.append("")

            report.append("### 交易统计")
            report.append(f"- 总交易次数: {summary['trades']['total_trades']}")
            report.append(f"- 胜率: {summary['trades']['win_rate']}")
            report.append(f"- 盈利交易: {summary['trades']['win_count']}")
            report.append(f"- 亏损交易: {summary['trades']['loss_count']}")
            report.append(f"- 平均交易收益: {summary['trades']['avg_trade_profit']}")
            report.append(
                f"- 平均盈利交易: {summary['trades']['avg_winning_trade']}")
            report.append(f"- 平均亏损交易: {summary['trades']['avg_losing_trade']}")
            report.append(
                f"- 最大盈利交易: {summary['trades']['largest_winning_trade']}"
            )
            report.append(
                f"- 最大亏损交易: {summary['trades']['largest_losing_trade']}"
            )
            report.append(f"- 期望值: {summary['trades']['expectancy']}")
            report.append("")

            # 添加交易记录
            if include_trades and "trade_list" in summary:
                report.append("## 交易记录")
                report.append(
                    "| 交易对 | 类型 | 入场时间 | 出场时间 | 入场价格 | 出场价格 | 数量 | 收益 |"
                )
                report.append(
                    "|--------|------|----------|----------|----------|----------|------|------|"
                )

                for trade in summary["trade_list"]:
                    report.append(
                        f"| {trade['pair']} | {trade['type']} | {trade['entry_date']} | {trade['exit_date']} | "
                        f"{trade['entry_price']} | {trade['exit_price']} | {trade['amount']} | {trade['profit_pct']} |"
                    )

                report.append("")

            # 写入文件
            with open(output_file, "w") as f:
                f.write("\n".join(report))

            logger.info(f"导出回测报告: {output_file}")

            return output_file

        except Exception as e:
            logger.error(f"导出回测报告时出错: {str(e)}")
            raise ValueError(f"导出回测报告时出错: {str(e)}")

    def compare_strategies(
        self,
        strategies: List[Union[str, Any]],
        pairs: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        initial_capital: Optional[float] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict:
        """
        比较多个策略的性能

        参数:
            strategies (List[Union[str, Any]]): 策略名称或实例列表
            pairs (List[str], 可选): 交易对列表
            timeframes (List[str], 可选): 时间周期列表
            start_date (Union[str, datetime], 可选): 开始日期
            end_date (Union[str, datetime], 可选): 结束日期
            initial_capital (float, 可选): 初始资金
            metrics (List[str], 可选): 要比较的指标列表

        返回:
            Dict: 比较结果字典

        异常:
            ValueError: 当比较失败时抛出异常
        """
        if not strategies:
            raise ValueError("未指定策略")

        # 默认比较指标
        if metrics is None:
            metrics = [
                "profit_pct",
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown_pct",
                "win_rate",
                "profit_factor",
                "expectancy",
            ]

        # 更新配置
        if pairs:
            self.config["pairs"] = pairs
        if timeframes:
            self.config["timeframes"] = timeframes
        if start_date:
            self.config["start_date"] = start_date
        if end_date:
            self.config["end_date"] = end_date
        if initial_capital:
            self.config["initial_capital"] = initial_capital

        # 保存原始配置
        original_config = self.config.copy()

        # 运行每个策略的回测
        results = []

        for strategy in strategies:
            try:
                # 恢复原始配置
                self.config = original_config.copy()

                # 运行回测
                result = self.run_backtest(strategy=strategy)

                # 提取要比较的指标
                strategy_name = self.config["strategy"]
                metrics_values = {}

                for metric in metrics:
                    if metric in result:
                        metrics_values[metric] = result[metric]
                    elif "performance" in result and metric in result["performance"]:
                        metrics_values[metric] = result["performance"][metric]
                    else:
                        metrics_values[metric] = None

                # 添加策略名称
                metrics_values["strategy"] = strategy_name

                results.append(metrics_values)

                logger.info(f"完成策略回测: {strategy_name}")

            except Exception as e:
                logger.error(f"回测策略 {strategy} 时出错: {str(e)}")
                continue

        # 创建比较表格
        comparison = pd.DataFrame(results)

        # 如果没有结果，抛出异常
        if comparison.empty:
            raise ValueError("没有可比较的结果")

        # 设置策略名称为索引
        comparison.set_index("strategy", inplace=True)

        # 构建比较结果
        comparison_result = {
            "comparison_table": comparison.to_dict(),
            "metrics": metrics,
            "strategies": [r["strategy"] for r in results],
            "pairs": self.config["pairs"],
            "timeframes": self.config["timeframes"],
            "start_date": self.config["start_date"],
            "end_date": self.config["end_date"],
            "initial_capital": self.config["initial_capital"],
        }

        logger.info(f"完成策略比较: {comparison_result['strategies']}")

        return comparison_result