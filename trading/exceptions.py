""" "
模块名称：exceptions
功能描述：交易系统的异常类定义
版本：1.0
创建日期：2025-04-20
作者：窗口9.1开发者
"""


# 假设项目中已有的BaseError基类，如果没有，可以创建一个
class BaseError(Exception):
    """项目的基础异常类"""

    def __init__(self, message="An error occurred"):
        self.message = message
        super().__init__(self.message)


class TradingError(BaseError):
    """交易系统的基础异常类"""

    def __init__(self, message="An error occurred in the trading system"):
        super().__init__(message)


class ExchangeConnectionError(TradingError):
    """交易所连接异常"""

    def __init__(
        self, message="Failed to connect to exchange", exchange=None, details=None
    ):
        self.exchange = exchange
        self.details = details
        msg = message
        if exchange:
            msg += f" ({exchange})"
        if details:
            msg += f": {details}"
        super().__init__(msg)


class InsufficientFundsError(TradingError):
    """资金不足异常"""

    def __init__(
        self,
        message="Insufficient funds for trading operation",
        required=None,
        available=None,
        currency=None,
    ):
        self.required = required
        self.available = available
        self.currency = currency

        msg = message
        if required and available and currency:
            msg += f": Required {required} {currency}, but only {available} {currency} available"

        super().__init__(msg)


class InvalidConfigError(TradingError):
    """配置无效异常"""

    def __init__(
        self, message="Invalid trading configuration", parameter=None, details=None
    ):
        self.parameter = parameter
        self.details = details

        msg = message
        if parameter:
            msg += f": Invalid parameter '{parameter}'"
        if details:
            msg += f" - {details}"

        super().__init__(msg)


class StrategyError(TradingError):
    """策略异常"""

    def __init__(
        self, message="Error in trading strategy", strategy_name=None, details=None
    ):
        self.strategy_name = strategy_name
        self.details = details

        msg = message
        if strategy_name:
            msg += f" ({strategy_name})"
        if details:
            msg += f": {details}"

        super().__init__(msg)


class GPTCommunicationError(TradingError):
    """GPT通信异常"""

    def __init__(self, message="Failed to communicate with GPT system", details=None):
        self.details = details

        msg = message
        if details:
            msg += f": {details}"

        super().__init__(msg)


class ClaudeExecutionError(TradingError):
    """Claude执行异常"""

    def __init__(self, message="Failed to execute via Claude system", details=None):
        self.details = details

        msg = message
        if details:
            msg += f": {details}"

        super().__init__(msg)


class BacktestingError(TradingError):
    """回测异常"""

    def __init__(self, message="Error during backtesting", details=None):
        self.details = details

        msg = message
        if details:
            msg += f": {details}"

        super().__init__(msg)


class OptimizationError(TradingError):
    """优化异常"""

    def __init__(self, message="Error during strategy optimization", details=None):
        self.details = details

        msg = message
        if details:
            msg += f": {details}"

        super().__init__(msg)