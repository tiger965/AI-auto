""" "
模块名称：base_connector
功能描述：交易所连接器的抽象基类，定义了所有交易所连接器必须实现的接口
版本：1.0
创建日期：2025-04-20
作者：Claude
"""

import abc
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime


class BaseConnectorError(Exception):
    """交易所连接器相关错误的基类"""

    pass


class ConnectionError(BaseConnectorError):
    """连接交易所时发生错误"""

    pass


class AuthenticationError(BaseConnectorError):
    """认证交易所时发生错误"""

    pass


class OrderError(BaseConnectorError):
    """处理订单时发生错误"""

    pass


class DataError(BaseConnectorError):
    """获取市场数据时发生错误"""

    pass


class BaseConnector(abc.ABC):
    """
    交易所连接器的抽象基类

    定义了所有交易所连接器必须实现的接口方法，包括：
    - 市场数据获取（实时和历史）
    - 账户信息获取
    - 订单管理
    - 仓位管理

    属性:
        name (str): 交易所名称
        is_connected (bool): 是否已连接到交易所
        supported_order_types (List[str]): 支持的订单类型列表
        logger (logging.Logger): 日志记录器
    """

    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化交易所连接器

        参数:
            name (str): 交易所名称
            api_key (str, optional): API密钥
            api_secret (str, optional): API密钥的密钥
            additional_params (Dict[str, Any], optional): 额外的连接参数
        """
        self.name = name
        self._api_key = api_key
        self._api_secret = api_secret
        self._additional_params = additional_params or {}
        self.is_connected = False
        self.supported_order_types = []

        # 设置日志
        self.logger = logging.getLogger(f"trading.connectors.{name}")

    @abc.abstractmethod
    async def connect(self) -> bool:
        """
        连接到交易所

        返回:
            bool: 连接是否成功

        异常:
            ConnectionError: 连接失败时抛出
        """
        pass

    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """
        断开与交易所的连接

        返回:
            bool: 断开连接是否成功
        """
        pass

    @abc.abstractmethod
    async def get_markets(self) -> List[Dict[str, Any]]:
        """
        获取所有可交易市场信息

        返回:
            List[Dict[str, Any]]: 市场信息列表

        异常:
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取指定交易对的当前行情

        参数:
            symbol (str): 交易对符号

        返回:
            Dict[str, Any]: 当前行情数据

        异常:
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """
        获取指定交易对的订单簿

        参数:
            symbol (str): 交易对符号
            depth (int, optional): 订单簿深度。默认为100。

        返回:
            Dict[str, Any]: 订单簿数据

        异常:
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取历史K线数据

        参数:
            symbol (str): 交易对符号
            timeframe (str): 时间周期 (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            since (datetime, optional): 开始时间
            limit (int, optional): 返回的K线数量限制

        返回:
            List[Dict[str, Any]]: 历史K线数据列表

        异常:
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额

        返回:
            Dict[str, float]: 账户各资产余额

        异常:
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_open_orders(
        self, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取未完成订单

        参数:
            symbol (str, optional): 交易对符号。如果为None，则获取所有交易对的未完成订单。

        返回:
            List[Dict[str, Any]]: 未完成订单列表

        异常:
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建订单

        参数:
            symbol (str): 交易对符号
            order_type (str): 订单类型 (market, limit, etc.)
            side (str): 订单方向 (buy, sell)
            amount (float): 订单数量
            price (float, optional): 订单价格，对于市价单可以为None
            params (Dict[str, Any], optional): 额外的订单参数

        返回:
            Dict[str, Any]: 创建的订单信息

        异常:
            AuthenticationError: 认证失败时抛出
            OrderError: 创建订单失败时抛出
        """
        pass

    @abc.abstractmethod
    async def cancel_order(
        self, order_id: str, symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        取消订单

        参数:
            order_id (str): 订单ID
            symbol (str, optional): 交易对符号。某些交易所需要提供此参数。

        返回:
            Dict[str, Any]: 取消的订单信息

        异常:
            AuthenticationError: 认证失败时抛出
            OrderError: 取消订单失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_order_status(
        self, order_id: str, symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订单状态

        参数:
            order_id (str): 订单ID
            symbol (str, optional): 交易对符号。某些交易所需要提供此参数。

        返回:
            Dict[str, Any]: 订单状态信息

        异常:
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """
        pass

    @abc.abstractmethod
    async def get_trade_history(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取交易历史

        参数:
            symbol (str, optional): 交易对符号。如果为None，则获取所有交易对的交易历史。
            since (datetime, optional): 开始时间
            limit (int, optional): 返回的交易数量限制

        返回:
            List[Dict[str, Any]]: 交易历史列表

        异常:
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """
        pass