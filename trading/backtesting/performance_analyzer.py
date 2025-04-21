""" "
模块名称：trading.backtesting.performance_analyzer
功能描述：回测性能分析器，负责计算和评估策略回测结果的各项性能指标
版本：1.0
创建日期：2025-04-20
作者：窗口9.3开发者
"""

import modules.nlp as np
import config.paths as pd
import logging
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
from config.secure import Figure

# 设置日志记录器
logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    性能分析器类，用于计算和评估策略回测结果的各项性能指标

    属性:
        trades (pd.DataFrame): 交易记录，包含策略执行的所有交易
        equity_curve (pd.DataFrame): 权益曲线，记录资金变化情况
        starting_balance (float): 初始资金
        trading_fees (float): 交易费率
        risk_free_rate (float): 无风险利率，用于计算夏普比率等指标
    """

    def __init__(
        self,
        trades: Optional[pd.DataFrame] = None,
        equity_curve: Optional[pd.DataFrame] = None,
        starting_balance: float = 10000.0,
        trading_fees: float = 0.001,
        risk_free_rate: float = 0.02,
    ):
        """
        初始化性能分析器

        参数:
            trades (pd.DataFrame, 可选): 交易记录DataFrame
            equity_curve (pd.DataFrame, 可选): 权益曲线DataFrame
            starting_balance (float): 初始资金，默认为10000
            trading_fees (float): 交易费率，默认为0.001 (0.1%)
            risk_free_rate (float): 年化无风险利率，默认为0.02 (2%)

        返回:
            无

        异常:
            ValueError: 当参数无效时抛出异常
        """
        self.trades = trades
        self.equity_curve = equity_curve
        self.starting_balance = starting_balance
        self.trading_fees = trading_fees
        self.risk_free_rate = risk_free_rate

        # 性能指标缓存
        self._performance_metrics = None

        # 验证参数
        self._validate_params()

        logger.info("初始化性能分析器")

    def _validate_params(self) -> None:
        """
        验证初始化参数的有效性

        参数:
            无

        返回:
            无

        异常:
            ValueError: 当参数无效时抛出异常
        """
        if self.starting_balance <= 0:
            raise ValueError("初始资金必须为正数")

        if self.trading_fees < 0 or self.trading_fees > 1:
            raise ValueError("交易费率必须在0到1之间")

    def set_trades(self, trades: pd.DataFrame) -> None:
        """
        设置交易记录

        参数:
            trades (pd.DataFrame): 交易记录DataFrame，应包含以下列：
                - entry_date: 入场日期
                - exit_date: 出场日期
                - pair: 交易对
                - entry_price: 入场价格
                - exit_price: 出场价格
                - amount: 交易数量
                - profit_abs: 绝对收益
                - profit_pct: 百分比收益

        返回:
            无

        异常:
            ValueError: 当交易记录格式无效时抛出异常
        """
        # 验证交易记录格式
        required_columns = [
            "entry_date",
            "exit_date",
            "pair",
            "entry_price",
            "exit_price",
            "amount",
            "profit_abs",
            "profit_pct",
        ]

        for column in required_columns:
            if column not in trades.columns:
                raise ValueError(f"交易记录缺少必要的列: {column}")

        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_dtype(trades["entry_date"]):
            trades["entry_date"] = pd.to_datetime(trades["entry_date"])

        if not pd.api.types.is_datetime64_dtype(trades["exit_date"]):
            trades["exit_date"] = pd.to_datetime(trades["exit_date"])

        self.trades = trades

        # 重置性能指标缓存
        self._performance_metrics = None

        logger.info(f"设置交易记录: {len(trades)} 条交易")

    def set_equity_curve(self, equity_curve: pd.DataFrame) -> None:
        """
        设置权益曲线

        参数:
            equity_curve (pd.DataFrame): 权益曲线DataFrame，应包含以下列：
                - date: 日期
                - equity: 权益值
                - drawdown_pct: 回撤百分比（可选）

        返回:
            无

        异常:
            ValueError: 当权益曲线格式无效时抛出异常
        """
        # 验证权益曲线格式
        required_columns = ["date", "equity"]

        for column in required_columns:
            if column not in equity_curve.columns:
                raise ValueError(f"权益曲线缺少必要的列: {column}")

        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_dtype(equity_curve["date"]):
            equity_curve["date"] = pd.to_datetime(equity_curve["date"])

        # 如果没有回撤列，添加一个
        if "drawdown_pct" not in equity_curve.columns:
            equity_curve = self._calculate_drawdown(equity_curve)

        self.equity_curve = equity_curve

        # 重置性能指标缓存
        self._performance_metrics = None

        logger.info(f"设置权益曲线: {len(equity_curve)} 个数据点")

    def _calculate_drawdown(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        """
        计算权益曲线的回撤

        参数:
            equity_curve (pd.DataFrame): 权益曲线DataFrame

        返回:
            pd.DataFrame: 添加了回撤列的权益曲线DataFrame
        """
        # 计算累计最大值
        equity_curve["equity_peak"] = equity_curve["equity"].cummax()

        # 计算绝对回撤
        equity_curve["drawdown_abs"] = (
            equity_curve["equity_peak"] - equity_curve["equity"]
        )

        # 计算百分比回撤
        equity_curve["drawdown_pct"] = (
            equity_curve["drawdown_abs"] / equity_curve["equity_peak"]
        ) * 100

        return equity_curve

    def calculate_metrics(self, recalculate: bool = False) -> Dict:
        """
        计算所有性能指标

        参数:
            recalculate (bool): 是否强制重新计算，默认为False

        返回:
            Dict: 包含所有性能指标的字典

        异常:
            ValueError: 当缺少必要的交易记录或权益曲线时抛出异常
        """
        # 如果已经计算过且不需要重新计算，直接返回缓存结果
        if self._performance_metrics is not None and not recalculate:
            return self._performance_metrics

        # 验证数据完整性
        if self.trades is None or self.trades.empty:
            raise ValueError("缺少交易记录，无法计算性能指标")

        if self.equity_curve is None or self.equity_curve.empty:
            raise ValueError("缺少权益曲线，无法计算性能指标")

        # 计算各项指标
        total_profit = self._calculate_total_profit()
        profit_factor = self._calculate_profit_factor()
        sharpe_ratio = self._calculate_sharpe_ratio()
        sortino_ratio = self._calculate_sortino_ratio()
        max_drawdown = self._calculate_max_drawdown()
        win_rate = self._calculate_win_rate()
        avg_profit = self._calculate_avg_profit()
        avg_loss = self._calculate_avg_loss()
        profit_to_drawdown = (
            total_profit["profit_pct"] / max_drawdown["max_drawdown_pct"]
            if max_drawdown["max_drawdown_pct"] > 0
            else float("inf")
        )

        # 汇总指标
        metrics = {
            # 收益相关指标
            "total_profit_abs": total_profit["profit_abs"],
            "total_profit_pct": total_profit["profit_pct"],
            "profit_factor": profit_factor,
            "annualized_return": self._calculate_annualized_return(),
            # 风险相关指标
            "max_drawdown_abs": max_drawdown["max_drawdown_abs"],
            "max_drawdown_pct": max_drawdown["max_drawdown_pct"],
            "max_drawdown_duration": max_drawdown["max_drawdown_duration"],
            "volatility": self._calculate_volatility(),
            # 风险调整收益指标
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": self._calculate_calmar_ratio(),
            "profit_to_drawdown_ratio": profit_to_drawdown,
            # 交易统计指标
            "total_trades": len(self.trades),
            "win_rate": win_rate["win_rate"],
            "win_count": win_rate["win_count"],
            "loss_count": win_rate["loss_count"],
            "avg_trade_profit": avg_profit["avg_profit_pct"],
            "avg_winning_trade": avg_profit["avg_win_pct"],
            "avg_losing_trade": avg_loss["avg_loss_pct"],
            "largest_winning_trade": avg_profit["max_win_pct"],
            "largest_losing_trade": avg_loss["max_loss_pct"],
            "avg_duration": self._calculate_avg_duration(),
            # 其他指标
            "expectancy": self._calculate_expectancy(),
            "trading_period": {
                "start_date": self.equity_curve["date"].min(),
                "end_date": self.equity_curve["date"].max(),
                "total_days": (
                    self.equity_curve["date"].max(
                    ) - self.equity_curve["date"].min()
                ).days,
            },
        }

        # 缓存结果
        self._performance_metrics = metrics

        logger.info("计算性能指标完成")
        return metrics

    def _calculate_total_profit(self) -> Dict:
        """
        计算总收益

        参数:
            无

        返回:
            Dict: 包含绝对收益和百分比收益的字典
        """
        # 从交易记录计算
        if self.trades is not None and not self.trades.empty:
            profit_abs = self.trades["profit_abs"].sum()
            profit_pct = (profit_abs / self.starting_balance) * 100
        else:
            # 从权益曲线计算
            profit_abs = (
                self.equity_curve["equity"].iloc[-1]
                - self.equity_curve["equity"].iloc[0]
            )
            profit_pct = (
                profit_abs / self.equity_curve["equity"].iloc[0]) * 100

        return {"profit_abs": profit_abs, "profit_pct": profit_pct}

    def _calculate_profit_factor(self) -> float:
        """
        计算利润因子（总盈利 / 总亏损的绝对值）

        参数:
            无

        返回:
            float: 利润因子
        """
        gross_profits = self.trades[self.trades["profit_abs"]
                                    > 0]["profit_abs"].sum()
        gross_losses = abs(
            self.trades[self.trades["profit_abs"] < 0]["profit_abs"].sum()
        )

        if gross_losses == 0:
            return float("inf") if gross_profits > 0 else 0

        return gross_profits / gross_losses

    def _calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率

        参数:
            无

        返回:
            float: 夏普比率
        """
        # 计算日收益率
        daily_returns = self.equity_curve["equity"].pct_change().dropna()

        # 年化收益率
        annual_return = self._calculate_annualized_return()

        # 日无风险利率
        daily_risk_free = (1 + self.risk_free_rate) ** (1 / 365) - 1

        # 计算超额收益的标准差
        excess_returns = daily_returns - daily_risk_free
        std_excess = excess_returns.std()

        # 计算年化标准差
        annual_std = std_excess * np.sqrt(252)

        if annual_std == 0:
            return 0

        # 夏普比率 = (年化收益率 - 无风险利率) / 年化标准差
        sharpe = (annual_return - self.risk_free_rate) / annual_std

        return sharpe

    def _calculate_sortino_ratio(self) -> float:
        """
        计算索提诺比率

        参数:
            无

        返回:
            float: 索提诺比率
        """
        # 计算日收益率
        daily_returns = self.equity_curve["equity"].pct_change().dropna()

        # 年化收益率
        annual_return = self._calculate_annualized_return()

        # 日无风险利率
        daily_risk_free = (1 + self.risk_free_rate) ** (1 / 365) - 1

        # 计算负收益
        negative_returns = (
            daily_returns[daily_returns < daily_risk_free] - daily_risk_free
        )

        if len(negative_returns) == 0:
            return float("inf") if annual_return > self.risk_free_rate else 0

        # 计算负收益的标准差
        downside_std = negative_returns.std()

        # 计算年化下行标准差
        annual_downside_std = downside_std * np.sqrt(252)

        if annual_downside_std == 0:
            return 0

        # 索提诺比率 = (年化收益率 - 无风险利率) / 年化下行标准差
        sortino = (annual_return - self.risk_free_rate) / annual_downside_std

        return sortino

    def _calculate_max_drawdown(self) -> Dict:
        """
        计算最大回撤

        参数:
            无

        返回:
            Dict: 包含最大回撤相关指标的字典
        """
        # 如果权益曲线不包含回撤列，先计算回撤
        if "drawdown_pct" not in self.equity_curve.columns:
            self.equity_curve = self._calculate_drawdown(self.equity_curve)

        # 找到最大回撤点
        max_dd_idx = self.equity_curve["drawdown_pct"].idxmax()
        max_dd_pct = self.equity_curve.loc[max_dd_idx, "drawdown_pct"]
        max_dd_abs = self.equity_curve.loc[max_dd_idx, "drawdown_abs"]

        # 计算回撤持续时间
        peak_idx = self.equity_curve.loc[:max_dd_idx, "equity"].idxmax()

        # 找到恢复点（如果有）
        recovery_idx = None
        if max_dd_idx < self.equity_curve.index[-1]:
            post_dd = self.equity_curve.loc[max_dd_idx:]
            peak_value = self.equity_curve.loc[peak_idx, "equity"]
            recovery_points = post_dd[post_dd["equity"] >= peak_value]

            if not recovery_points.empty:
                recovery_idx = recovery_points.index[0]

        # 计算持续时间
        if recovery_idx is not None:
            duration = (
                self.equity_curve.loc[recovery_idx, "date"]
                - self.equity_curve.loc[peak_idx, "date"]
            ).days
        else:
            duration = (
                self.equity_curve.loc[self.equity_curve.index[-1], "date"]
                - self.equity_curve.loc[peak_idx, "date"]
            ).days

        return {
            "max_drawdown_abs": max_dd_abs,
            "max_drawdown_pct": max_dd_pct,
            "max_drawdown_duration": duration,
            "peak_date": self.equity_curve.loc[peak_idx, "date"],
            "valley_date": self.equity_curve.loc[max_dd_idx, "date"],
            "recovery_date": (
                self.equity_curve.loc[recovery_idx, "date"]
                if recovery_idx is not None
                else None
            ),
        }

    def _calculate_win_rate(self) -> Dict:
        """
        计算胜率

        参数:
            无

        返回:
            Dict: 包含胜率相关指标的字典
        """
        # 计算盈利和亏损交易数量
        win_count = len(self.trades[self.trades["profit_abs"] > 0])
        loss_count = len(self.trades[self.trades["profit_abs"] < 0])

        # 计算胜率
        total_trades = len(self.trades)
        win_rate = win_count / total_trades if total_trades > 0 else 0

        return {"win_rate": win_rate, "win_count": win_count, "loss_count": loss_count}

    def _calculate_avg_profit(self) -> Dict:
        """
        计算平均收益和最大收益

        参数:
            无

        返回:
            Dict: 包含平均收益和最大收益的字典
        """
        # 所有交易的平均收益
        avg_profit_abs = self.trades["profit_abs"].mean()
        avg_profit_pct = self.trades["profit_pct"].mean()

        # 盈利交易的平均收益
        winning_trades = self.trades[self.trades["profit_abs"] > 0]
        avg_win_abs = (
            winning_trades["profit_abs"].mean(
            ) if not winning_trades.empty else 0
        )
        avg_win_pct = (
            winning_trades["profit_pct"].mean(
            ) if not winning_trades.empty else 0
        )

        # 最大盈利交易
        max_win_abs = (
            winning_trades["profit_abs"].max(
            ) if not winning_trades.empty else 0
        )
        max_win_idx = (
            winning_trades["profit_abs"].idxmax(
            ) if not winning_trades.empty else None
        )
        max_win_pct = (
            winning_trades.loc[max_win_idx, "profit_pct"]
            if max_win_idx is not None
            else 0
        )

        return {
            "avg_profit_abs": avg_profit_abs,
            "avg_profit_pct": avg_profit_pct,
            "avg_win_abs": avg_win_abs,
            "avg_win_pct": avg_win_pct,
            "max_win_abs": max_win_abs,
            "max_win_pct": max_win_pct,
        }

    def _calculate_avg_loss(self) -> Dict:
        """
        计算平均亏损和最大亏损

        参数:
            无

        返回:
            Dict: 包含平均亏损和最大亏损的字典
        """
        # 亏损交易的平均亏损
        losing_trades = self.trades[self.trades["profit_abs"] < 0]
        avg_loss_abs = (
            losing_trades["profit_abs"].mean(
            ) if not losing_trades.empty else 0
        )
        avg_loss_pct = (
            losing_trades["profit_pct"].mean(
            ) if not losing_trades.empty else 0
        )

        # 最大亏损交易
        max_loss_abs = (
            losing_trades["profit_abs"].min() if not losing_trades.empty else 0
        )
        max_loss_idx = (
            losing_trades["profit_abs"].idxmin(
            ) if not losing_trades.empty else None
        )
        max_loss_pct = (
            losing_trades.loc[max_loss_idx, "profit_pct"]
            if max_loss_idx is not None
            else 0
        )

        return {
            "avg_loss_abs": avg_loss_abs,
            "avg_loss_pct": avg_loss_pct,
            "max_loss_abs": max_loss_abs,
            "max_loss_pct": max_loss_pct,
        }

    def _calculate_annualized_return(self) -> float:
        """
        计算年化收益率

        参数:
            无

        返回:
            float: 年化收益率
        """
        # 计算总收益率
        initial_equity = self.equity_curve["equity"].iloc[0]
        final_equity = self.equity_curve["equity"].iloc[-1]
        total_return = (final_equity / initial_equity) - 1

        # 计算交易周期（年）
        start_date = self.equity_curve["date"].min()
        end_date = self.equity_curve["date"].max()
        years = (end_date - start_date).days / 365.25

        if years <= 0:
            return 0

        # 计算年化收益率
        annualized_return = (1 + total_return) ** (1 / years) - 1

        return annualized_return

    def _calculate_volatility(self) -> float:
        """
        计算波动率（年化标准差）

        参数:
            无

        返回:
            float: 年化波动率
        """
        # 计算日收益率
        daily_returns = self.equity_curve["equity"].pct_change().dropna()

        # 计算日收益率的标准差
        daily_std = daily_returns.std()

        # 计算年化标准差
        annual_std = daily_std * np.sqrt(252)

        return annual_std

    def _calculate_calmar_ratio(self) -> float:
        """
        计算卡玛比率（年化收益率 / 最大回撤）

        参数:
            无

        返回:
            float: 卡玛比率
        """
        # 计算年化收益率
        annual_return = self._calculate_annualized_return()

        # 计算最大回撤
        max_dd = self._calculate_max_drawdown()
        max_dd_pct = max_dd["max_drawdown_pct"] / 100  # 转换为小数

        if max_dd_pct == 0:
            return float("inf") if annual_return > 0 else 0

        # 计算卡玛比率
        calmar = annual_return / max_dd_pct

        return calmar

    def _calculate_avg_duration(self) -> Dict:
        """
        计算平均持仓时间

        参数:
            无

        返回:
            Dict: 包含平均持仓时间的字典
        """
        # 计算每笔交易的持仓时间
        self.trades["duration"] = self.trades["exit_date"] - \
            self.trades["entry_date"]

        # 计算平均持仓时间
        avg_duration_timedelta = self.trades["duration"].mean()
        avg_duration_days = avg_duration_timedelta.total_seconds() / (24 * 3600)

        # 计算最长和最短持仓时间
        max_duration_timedelta = self.trades["duration"].max()
        max_duration_days = max_duration_timedelta.total_seconds() / (24 * 3600)

        min_duration_timedelta = self.trades["duration"].min()
        min_duration_days = min_duration_timedelta.total_seconds() / (24 * 3600)

        return {
            "avg_duration_days": avg_duration_days,
            "max_duration_days": max_duration_days,
            "min_duration_days": min_duration_days,
        }

    def _calculate_expectancy(self) -> float:
        """
        计算期望值（Win Rate * Average Win - Loss Rate * Average Loss）

        参数:
            无

        返回:
            float: 期望值
        """
        win_rate = self._calculate_win_rate()["win_rate"]
        loss_rate = 1 - win_rate

        avg_win = self._calculate_avg_profit()["avg_win_pct"]
        avg_loss = abs(self._calculate_avg_loss()["avg_loss_pct"])

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        return expectancy

    def get_summary(self, include_trade_list: bool = False) -> Dict:
        """
        获取性能指标摘要

        参数:
            include_trade_list (bool): 是否包含交易列表，默认为False

        返回:
            Dict: 包含性能指标摘要和可选的交易列表的字典
        """
        # 计算性能指标
        metrics = self.calculate_metrics()

        # 构建摘要
        summary = {
            "trading_period": {
                "start_date": metrics["trading_period"]["start_date"].strftime(
                    "%Y-%m-%d"
                ),
                "end_date": metrics["trading_period"]["end_date"].strftime("%Y-%m-%d"),
                "total_days": metrics["trading_period"]["total_days"],
            },
            "performance": {
                "total_profit_pct": f"{metrics['total_profit_pct']:.2f}%",
                "total_profit_abs": f"{metrics['total_profit_abs']:.2f}",
                "annualized_return": f"{metrics['annualized_return'] * 100:.2f}%",
                "profit_factor": f"{metrics['profit_factor']:.2f}",
                "sharpe_ratio": f"{metrics['sharpe_ratio']:.2f}",
                "sortino_ratio": f"{metrics['sortino_ratio']:.2f}",
                "calmar_ratio": f"{metrics['calmar_ratio']:.2f}",
            },
            "risk": {
                "max_drawdown_pct": f"{metrics['max_drawdown_pct']:.2f}%",
                "max_drawdown_abs": f"{metrics['max_drawdown_abs']:.2f}",
                "max_drawdown_duration": f"{metrics['max_drawdown_duration']} days",
                "volatility": f"{metrics['volatility'] * 100:.2f}%",
            },
            "trades": {
                "total_trades": metrics["total_trades"],
                "win_rate": f"{metrics['win_rate'] * 100:.2f}%",
                "win_count": metrics["win_count"],
                "loss_count": metrics["loss_count"],
                "avg_trade_profit": f"{metrics['avg_trade_profit']:.2f}%",
                "avg_winning_trade": f"{metrics['avg_winning_trade']:.2f}%",
                "avg_losing_trade": f"{metrics['avg_losing_trade']:.2f}%",
                "largest_winning_trade": f"{metrics['largest_winning_trade']:.2f}%",
                "largest_losing_trade": f"{metrics['largest_losing_trade']:.2f}%",
                "expectancy": f"{metrics['expectancy']:.2f}%",
            },
        }

        # 如果需要包含交易列表
        if include_trade_list and self.trades is not None:
            # 选择要包含的列
            trade_cols = [
                "entry_date",
                "exit_date",
                "pair",
                "entry_price",
                "exit_price",
                "amount",
                "profit_abs",
                "profit_pct",
            ]

            # 将日期转换为字符串
            trades_list = self.trades[trade_cols].copy()
            trades_list["entry_date"] = trades_list["entry_date"].dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            trades_list["exit_date"] = trades_list["exit_date"].dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # 格式化数值
            trades_list["profit_abs"] = trades_list["profit_abs"].map(
                lambda x: f"{x:.2f}"
            )
            trades_list["profit_pct"] = trades_list["profit_pct"].map(
                lambda x: f"{x:.2f}%"
            )

            # 转换为字典列表
            summary["trade_list"] = trades_list.to_dict("records")

        return summary

    def plot_equity_curve(self, figsize: Tuple[int, int] = (10, 6)) -> Figure:
        """
        绘制权益曲线图

        参数:
            figsize (Tuple[int, int]): 图表大小，默认为 (10, 6)

        返回:
            Figure: Matplotlib 图表对象

        异常:
            ValueError: 当缺少权益曲线数据时抛出异常
        """
        if self.equity_curve is None or self.equity_curve.empty:
            raise ValueError("缺少权益曲线数据，无法绘制图表")

        # 创建图表
        fig, ax1 = plt.subplots(figsize=figsize)

        # 绘制权益曲线
        ax1.plot(
            self.equity_curve["date"], self.equity_curve["equity"], "b-", label="权益"
        )
        ax1.set_xlabel("日期")
        ax1.set_ylabel("权益", color="b")
        ax1.tick_params(axis="y", labelcolor="b")

        # 创建第二个y轴用于绘制回撤
        ax2 = ax1.twinx()
        ax2.plot(
            self.equity_curve["date"],
            -self.equity_curve["drawdown_pct"],
            "r-",
            label="回撤",
        )
        ax2.set_ylabel("回撤 (%)", color="r")
        ax2.tick_params(axis="y", labelcolor="r")
        ax2.invert_yaxis()  # 反转y轴使回撤向下显示

        # 设置标题
        metrics = self.calculate_metrics()
        title = (
            f"权益曲线 - 总收益: {metrics['total_profit_pct']:.2f}%, "
            f"最大回撤: {metrics['max_drawdown_pct']:.2f}%, "
            f"夏普比率: {metrics['sharpe_ratio']:.2f}"
        )
        plt.title(title)

        # 添加图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        # 自动调整布局
        fig.tight_layout()

        return fig

    def plot_monthly_returns(self, figsize: Tuple[int, int] = (12, 8)) -> Figure:
        """
        绘制月度收益热图

        参数:
            figsize (Tuple[int, int]): 图表大小，默认为 (12, 8)

        返回:
            Figure: Matplotlib 图表对象

        异常:
            ValueError: 当缺少权益曲线数据时抛出异常
        """
        if self.equity_curve is None or self.equity_curve.empty:
            raise ValueError("缺少权益曲线数据，无法绘制图表")

        # 计算日收益率
        equity_data = self.equity_curve.copy()
        equity_data["daily_return"] = equity_data["equity"].pct_change()

        # 提取年份和月份
        equity_data["year"] = equity_data["date"].dt.year
        equity_data["month"] = equity_data["date"].dt.month

        # 计算月度收益率
        monthly_returns = equity_data.groupby(["year", "month"])["daily_return"].apply(
            lambda x: (1 + x).prod() - 1
        )

        # 转换为表格格式
        monthly_returns = monthly_returns.unstack(level=0)

        # 创建图表
        fig, ax = plt.subplots(figsize=figsize)

        # 绘制热图
        cmap = plt.cm.RdYlGn  # 红黄绿色映射
        im = ax.imshow(monthly_returns.values, cmap=cmap)

        # 添加颜色条
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("月度收益率", rotation=-90, va="bottom")

        # 设置轴标签
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        ax.set_yticks(np.arange(len(month_names)))
        ax.set_yticklabels(month_names)

        ax.set_xticks(np.arange(len(monthly_returns.columns)))
        ax.set_xticklabels(monthly_returns.columns)

        # 在单元格中显示数值
        for i in range(len(month_names)):
            for j in range(len(monthly_returns.columns)):
                if not np.isnan(monthly_returns.values[i, j]):
                    text = ax.text(
                        j,
                        i,
                        f"{monthly_returns.values[i, j]:.2%}",
                        ha="center",
                        va="center",
                        color="black",
                    )

        # 设置标题
        ax.set_title("月度收益热图")

        # 自动调整布局
        fig.tight_layout()

        return fig

    def plot_trade_distribution(self, figsize: Tuple[int, int] = (12, 8)) -> Figure:
        """
        绘制交易分布图

        参数:
            figsize (Tuple[int, int]): 图表大小，默认为 (12, 8)

        返回:
            Figure: Matplotlib 图表对象

        异常:
            ValueError: 当缺少交易记录时抛出异常
        """
        if self.trades is None or self.trades.empty:
            raise ValueError("缺少交易记录，无法绘制图表")

        # 创建2x2的子图
        fig, axs = plt.subplots(2, 2, figsize=figsize)

        # 1. 交易对分布
        pair_counts = self.trades["pair"].value_counts()
        axs[0, 0].pie(pair_counts, labels=pair_counts.index, autopct="%1.1f%%")
        axs[0, 0].set_title("交易对分布")

        # 2. 胜负分布
        win_loss = [
            len(self.trades[self.trades["profit_abs"] > 0]),
            len(self.trades[self.trades["profit_abs"] < 0]),
        ]
        axs[0, 1].pie(
            win_loss, labels=["Win", "Loss"], colors=["green", "red"], autopct="%1.1f%%"
        )
        axs[0, 1].set_title("胜负分布")

        # 3. 收益分布直方图
        axs[1, 0].hist(self.trades["profit_pct"], bins=20, alpha=0.7)
        axs[1, 0].axvline(x=0, color="r", linestyle="--")
        axs[1, 0].set_title("收益分布")
        axs[1, 0].set_xlabel("收益百分比 (%)")
        axs[1, 0].set_ylabel("交易次数")

        # 4. 交易持续时间分布
        if "duration" not in self.trades.columns:
            self.trades["duration"] = (
                self.trades["exit_date"] - self.trades["entry_date"]
            )

        duration_hours = self.trades["duration"].dt.total_seconds() / 3600
        axs[1, 1].hist(duration_hours, bins=20, alpha=0.7)
        axs[1, 1].set_title("持仓时间分布")
        axs[1, 1].set_xlabel("持仓时间 (小时)")
        axs[1, 1].set_ylabel("交易次数")

        # 自动调整布局
        fig.tight_layout()

        return fig

    def export_results(self, output_dir: str = "results") -> Dict[str, str]:
        """
        导出回测结果到文件

        参数:
            output_dir (str): 输出目录，默认为 'results'

        返回:
            Dict[str, str]: 导出文件的路径字典

        异常:
            ValueError: 当缺少必要的数据时抛出异常
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        exported_files = {}

        # 导出性能指标摘要
        if self._performance_metrics is not None:
            summary_file = os.path.join(
                output_dir, f"performance_summary_{timestamp}.json"
            )
            with open(summary_file, "w") as f:
                import json

                # 转换 datetime 对象为字符串
                summary = self.get_summary(include_trade_list=True)
                json.dump(summary, f, indent=4)
            exported_files["summary"] = summary_file

        # 导出交易记录
        if self.trades is not None and not self.trades.empty:
            trades_file = os.path.join(output_dir, f"trades_{timestamp}.csv")
            self.trades.to_csv(trades_file, index=False)
            exported_files["trades"] = trades_file

        # 导出权益曲线
        if self.equity_curve is not None and not self.equity_curve.empty:
            equity_file = os.path.join(
                output_dir, f"equity_curve_{timestamp}.csv")
            self.equity_curve.to_csv(equity_file, index=False)
            exported_files["equity_curve"] = equity_file

        # 导出图表
        try:
            # 权益曲线图
            equity_plot_file = os.path.join(
                output_dir, f"equity_plot_{timestamp}.png")
            fig = self.plot_equity_curve()
            fig.savefig(equity_plot_file)
            plt.close(fig)
            exported_files["equity_plot"] = equity_plot_file

            # 月度收益热图
            monthly_plot_file = os.path.join(
                output_dir, f"monthly_returns_{timestamp}.png"
            )
            fig = self.plot_monthly_returns()
            fig.savefig(monthly_plot_file)
            plt.close(fig)
            exported_files["monthly_plot"] = monthly_plot_file

            # 交易分布图
            if self.trades is not None and not self.trades.empty:
                distribution_plot_file = os.path.join(
                    output_dir, f"trade_distribution_{timestamp}.png"
                )
                fig = self.plot_trade_distribution()
                fig.savefig(distribution_plot_file)
                plt.close(fig)
                exported_files["distribution_plot"] = distribution_plot_file

        except Exception as e:
            logger.error(f"导出图表时出错: {str(e)}")

        logger.info(f"导出回测结果到目录: {output_dir}")
        return exported_files