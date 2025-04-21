""" "
模块名称：mock_connector
功能描述：模拟交易所连接器，用于测试和开发环境
版本：1.0
创建日期：2025-04-20
作者：Claude
"""

from typing import Dict, List, Optional, Any
import uuid
import random
import logging
import asyncio
from datetime import datetime, timedelta

from trading.connectors.base_connector import (
    BaseConnector,
    ConnectionError,
    AuthenticationError,
    OrderError,
    DataError,
)


class MockConnector(BaseConnector):
    """
    模拟交易所连接器类

    用于测试和开发环境的模拟交易所连接器，模拟真实交易所的行为但不进行实际交易。

    属性:
        name (str): 交易所名称，默认为"MockExchange"
        is_connected (bool): 是否已连接到交易所
        supported_order_types (List[str]): 支持的订单类型列表
        logger (logging.Logger): 日志记录器
    """

    def __init__(
        self,
        name: str = "MockExchange",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化模拟交易所连接器

        参数:
            name (str, optional): 交易所名称，默认为"MockExchange"
            api_key (str, optional): API密钥，对于模拟交易所非必须
            api_secret (str, optional): API密钥的密钥，对于模拟交易所非必须
            additional_params (Dict[str, Any], optional): 额外的连接参数
        """
        super().__init__(name, api_key, api_secret, additional_params)

        # 设置支持的订单类型
        self.supported_order_types = [
            "market", "limit", "stop_loss", "take_profit"]

        # 模拟数据存储
        self._markets = {}
        self._tickers = {}
        self._order_books = {}
        self._balances = {}
        self._orders = {}
        self._trades = []

        # 设置初始模拟数据
        self._setup_mock_data()

        self.logger.info(f"模拟交易所连接器 {name} 初始化完成")

    def _setup_mock_data(self) -> None:
        """
        设置初始模拟数据

        设置交易对、余额和其他初始数据用于模拟交易
        """
        # 设置模拟交易对
        symbols = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BNB/USDT"]

        for symbol in symbols:
            base, quote = symbol.split("/")

            # 创建市场信息
            self._markets[symbol] = {
                "symbol": symbol,
                "base": base,
                "quote": quote,
                "active": True,
                "precision": {"price": 2, "amount": 6},
                "limits": {
                    "price": {"min": 0.01, "max": 100000},
                    "amount": {"min": 0.0001, "max": 1000},
                },
            }

            # 创建行情数据
            base_price = {
                "BTC/USDT": 35000,
                "ETH/USDT": 2000,
                "XRP/USDT": 0.5,
                "LTC/USDT": 120,
                "BNB/USDT": 300,
            }.get(symbol, 100)

            self._tickers[symbol] = {
                "symbol": symbol,
                "last": base_price,
                "bid": base_price * 0.998,
                "ask": base_price * 1.002,
                "high": base_price * 1.05,
                "low": base_price * 0.95,
                "volume": random.uniform(100, 1000),
                "timestamp": datetime.now().timestamp(),
            }

            # 创建订单簿
            self._order_books[symbol] = {
                "symbol": symbol,
                "bids": [
                    [base_price * (1 - i * 0.001), random.uniform(0.1, 10)]
                    for i in range(20)
                ],
                "asks": [
                    [base_price * (1 + i * 0.001), random.uniform(0.1, 10)]
                    for i in range(20)
                ],
                "timestamp": datetime.now().timestamp(),
            }

        # 设置模拟余额
        self._balances = {
            "USDT": 10000,
            "BTC": 0.5,
            "ETH": 5,
            "XRP": 1000,
            "LTC": 10,
            "BNB": 20,
        }

    async def connect(self) -> bool:
        """
        连接到模拟交易所

        在真实交易所中，这会建立API连接，但在模拟交易所中，只是模拟连接过程

        返回:
            bool: 连接是否成功

        异常:
            ConnectionError: 模拟连接失败时抛出
        """
        if not self.is_connected:
            self.logger.info(f"正在连接到模拟交易所 {self.name}")

            # 模拟连接延迟
            await asyncio.sleep(0.5)

            # 随机模拟连接失败的情况 (5%概率)
            if random.random() < 0.05:
                self.logger.error(f"连接到模拟交易所 {self.name} 失败")
                raise ConnectionError(f"无法连接到模拟交易所 {self.name}")

            self.is_connected = True
            self.logger.info(f"已成功连接到模拟交易所 {self.name}")

        return self.is_connected

    async def disconnect(self) -> bool:
        """
        断开与模拟交易所的连接

        返回:
            bool: 断开连接是否成功
        """
        if self.is_connected:
            self.logger.info(f"正在断开与模拟交易所 {self.name} 的连接")

            # 模拟断开连接延迟
            await asyncio.sleep(0.3)

            self.is_connected = False
            self.logger.info(f"已成功断开与模拟交易所 {self.name} 的连接")

        return not self.is_connected

    async def get_markets(self) -> List[Dict[str, Any]]:
        """
        获取所有可交易市场信息

        返回:
            List[Dict[str, Any]]: 市场信息列表

        异常:
            ConnectionError: 未连接到交易所时抛出
            DataError: 获取数据失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.debug(f"获取模拟交易所 {self.name} 的市场信息")

        # 模拟API延迟
        await asyncio.sleep(0.2)

        return list(self._markets.values())

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取指定交易对的当前行情

        参数:
            symbol (str): 交易对符号

        返回:
            Dict[str, Any]: 当前行情数据

        异常:
            ConnectionError: 未连接到交易所时抛出
            DataError: 获取数据失败或交易对不存在时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.debug(f"获取模拟交易所 {self.name} 的 {symbol} 行情")

        # 检查交易对是否存在
        if symbol not in self._tickers:
            raise DataError(f"交易对 {symbol} 在模拟交易所 {self.name} 中不存在")

        # 模拟API延迟
        await asyncio.sleep(0.1)

        # 更新行情数据
        ticker = self._tickers[symbol].copy()
        last_price = ticker["last"]

        # 模拟价格波动 (±1%)
        price_change = last_price * random.uniform(-0.01, 0.01)
        new_price = last_price + price_change

        ticker.update(
            {
                "last": new_price,
                "bid": new_price * 0.998,
                "ask": new_price * 1.002,
                "high": max(ticker["high"], new_price),
                "low": min(ticker["low"], new_price),
                "timestamp": datetime.now().timestamp(),
            }
        )

        self._tickers[symbol] = ticker

        return ticker

    async def get_order_book(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """
        获取指定交易对的订单簿

        参数:
            symbol (str): 交易对符号
            depth (int, optional): 订单簿深度。默认为100。

        返回:
            Dict[str, Any]: 订单簿数据

        异常:
            ConnectionError: 未连接到交易所时抛出
            DataError: 获取数据失败或交易对不存在时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.debug(f"获取模拟交易所 {self.name} 的 {symbol} 订单簿")

        # 检查交易对是否存在
        if symbol not in self._order_books:
            raise DataError(f"交易对 {symbol} 在模拟交易所 {self.name} 中不存在")

        # 模拟API延迟
        await asyncio.sleep(0.15)

        # 更新订单簿
        order_book = self._order_books[symbol].copy()

        # 获取当前价格
        ticker = await self.get_ticker(symbol)
        current_price = ticker["last"]

        # 重新生成订单簿
        order_book.update(
            {
                "bids": [
                    [current_price * (1 - i * 0.001), random.uniform(0.1, 10)]
                    for i in range(min(20, depth))
                ],
                "asks": [
                    [current_price * (1 + i * 0.001), random.uniform(0.1, 10)]
                    for i in range(min(20, depth))
                ],
                "timestamp": datetime.now().timestamp(),
            }
        )

        self._order_books[symbol] = order_book

        return order_book

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
            ConnectionError: 未连接到交易所时抛出
            DataError: 获取数据失败或交易对不存在时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.debug(
            f"获取模拟交易所 {self.name} 的 {symbol} {timeframe} 历史数据"
        )

        # 检查交易对是否存在
        if symbol not in self._markets:
            raise DataError(f"交易对 {symbol} 在模拟交易所 {self.name} 中不存在")

        # 解析时间周期
        timeframe_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }.get(timeframe)

        if not timeframe_minutes:
            raise DataError(f"不支持的时间周期 {timeframe}")

        # 设置默认值
        if limit is None:
            limit = 100

        if since is None:
            since = datetime.now() - timedelta(minutes=timeframe_minutes * limit)

        # 模拟API延迟
        await asyncio.sleep(0.3)

        # 生成模拟历史数据
        ticker = await self.get_ticker(symbol)
        current_price = ticker["last"]

        # 使用随机游走模拟历史价格
        historical_data = []
        current_time = datetime.now()

        for i in range(limit):
            candle_time = current_time - \
                timedelta(minutes=timeframe_minutes * i)
            if candle_time < since:
                continue

            # 根据时间和交易对生成一个伪随机种子，使每次查询相同参数时返回相似结果
            random.seed(
                f"{symbol}_{timeframe}_{candle_time.strftime('%Y%m%d%H%M')}")

            # 生成历史价格数据（使用简单的随机游走模型）
            price_volatility = current_price * \
                0.002 * (1 + random.uniform(-0.5, 0.5))
            open_price = current_price * (1 + random.uniform(-0.01, 0.01))
            high_price = open_price * (1 + random.uniform(0, 0.02))
            low_price = open_price * (1 - random.uniform(0, 0.02))
            close_price = open_price * (1 + random.uniform(-0.015, 0.015))
            volume = random.uniform(10, 1000) * (current_price / 100)

            historical_data.append(
                {
                    "timestamp": int(candle_time.timestamp() * 1000),
                    "datetime": candle_time.isoformat(),
                    "symbol": symbol,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
            )

            # 重置随机种子
            random.seed()

        # 按时间排序
        historical_data.sort(key=lambda x: x["timestamp"])

        return historical_data

    async def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额

        返回:
            Dict[str, float]: 账户各资产余额

        异常:
            ConnectionError: 未连接到交易所时抛出
            AuthenticationError: 认证失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        # 检查是否提供了API密钥
        if not self._api_key or not self._api_secret:
            self.logger.warning("使用模拟交易所时未提供API密钥，使用默认模拟余额")

        self.logger.debug(f"获取模拟交易所 {self.name} 的账户余额")

        # 模拟API延迟
        await asyncio.sleep(0.2)

        return self._balances.copy()

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
            ConnectionError: 未连接到交易所时抛出
            AuthenticationError: 认证失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        # 检查是否提供了API密钥
        if not self._api_key or not self._api_secret:
            self.logger.warning("使用模拟交易所时未提供API密钥，使用默认模拟订单")

        self.logger.debug(f"获取模拟交易所 {self.name} 的未完成订单")

        # 模拟API延迟
        await asyncio.sleep(0.25)

        # 过滤订单
        open_orders = [
            order
            for order in self._orders.values()
            if order["status"] in ["open", "partially_filled"]
            and (symbol is None or order["symbol"] == symbol)
        ]

        return open_orders

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
            ConnectionError: 未连接到交易所时抛出
            AuthenticationError: 认证失败时抛出
            OrderError: 创建订单失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        # 检查交易对是否存在
        if symbol not in self._markets:
            raise OrderError(f"交易对 {symbol} 在模拟交易所 {self.name} 中不存在")

        # 检查订单类型是否支持
        if order_type not in self.supported_order_types:
            raise OrderError(f"不支持的订单类型 {order_type}")

        # 检查订单方向是否有效
        if side not in ["buy", "sell"]:
            raise OrderError(f"无效的订单方向 {side}")

        # 对于限价单，检查价格是否有效
        if order_type == "limit" and (price is None or price <= 0):
            raise OrderError("限价单必须指定有效价格")

        # 检查订单数量是否有效
        if amount <= 0:
            raise OrderError("订单数量必须大于零")

        self.logger.info(
            f"在模拟交易所 {self.name} 创建 {symbol} {side} {order_type} 订单"
        )

        # 模拟API延迟
        await asyncio.sleep(0.3)

        # 获取当前行情
        ticker = await self.get_ticker(symbol)
        current_price = ticker["last"]

        # 对于市价单，使用当前价格
        if price is None:
            price = current_price

        # 生成订单ID
        order_id = str(uuid.uuid4())

        # 计算订单金额
        cost = amount * price

        # 检查余额是否足够
        base, quote = symbol.split("/")

        if side == "buy" and self._balances.get(quote, 0) < cost:
            raise OrderError(
                f"余额不足，需要 {cost} {quote}，但只有 {self._balances.get(quote, 0)} {quote}"
            )
        elif side == "sell" and self._balances.get(base, 0) < amount:
            raise OrderError(
                f"余额不足，需要 {amount} {base}，但只有 {self._balances.get(base, 0)} {base}"
            )

        # 创建订单
        order = {
            "id": order_id,
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "price": price,
            "amount": amount,
            "cost": cost,
            "filled": 0,
            "remaining": amount,
            "status": "open",
            "timestamp": datetime.now().timestamp(),
            "datetime": datetime.now().isoformat(),
        }

        # 保存订单
        self._orders[order_id] = order

        # 对于市价单，立即部分或全部成交
        if order_type == "market":
            # 模拟市价单成交
            await self._fill_market_order(order_id)

        return order

    async def _fill_market_order(self, order_id: str) -> None:
        """
        模拟市价单成交

        参数:
            order_id (str): 订单ID
        """
        order = self._orders.get(order_id)
        if not order or order["type"] != "market":
            return

        # 随机决定成交比例
        fill_percentage = random.uniform(0.9, 1.0)
        filled_amount = order["amount"] * fill_percentage

        # 更新订单状态
        order["filled"] = filled_amount
        order["remaining"] = order["amount"] - filled_amount

        if filled_amount == order["amount"]:
            order["status"] = "closed"
        else:
            order["status"] = "partially_filled"

        # 更新余额
        base, quote = order["symbol"].split("/")

        if order["side"] == "buy":
            self._balances[base] = self._balances.get(base, 0) + filled_amount
            self._balances[quote] = (
                self._balances.get(quote, 0) - filled_amount * order["price"]
            )
        else:
            self._balances[base] = self._balances.get(base, 0) - filled_amount
            self._balances[quote] = (
                self._balances.get(quote, 0) + filled_amount * order["price"]
            )

        # 添加交易记录
        trade = {
            "id": str(uuid.uuid4()),
            "order": order_id,
            "symbol": order["symbol"],
            "side": order["side"],
            "price": order["price"],
            "amount": filled_amount,
            "cost": filled_amount * order["price"],
            "timestamp": datetime.now().timestamp(),
            "datetime": datetime.now().isoformat(),
        }

        self._trades.append(trade)

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
            ConnectionError: 未连接到交易所时抛出
            AuthenticationError: 认证失败时抛出
            OrderError: 取消订单失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.info(f"在模拟交易所 {self.name} 取消订单 {order_id}")

        # 检查订单是否存在
        if order_id not in self._orders:
            raise OrderError(f"订单 {order_id} 不存在")

        order = self._orders[order_id]

        # 检查订单状态
        if order["status"] in ["closed", "canceled"]:
            raise OrderError(f"订单 {order_id} 已经 {order['status']}")

        # 如果提供了交易对，检查是否匹配
        if symbol and order["symbol"] != symbol:
            raise OrderError(f"订单 {order_id} 不是交易对 {symbol} 的订单")

        # 模拟API延迟
        await asyncio.sleep(0.2)

        # 更新订单状态
        order["status"] = "canceled"

        return order

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
            ConnectionError: 未连接到交易所时抛出
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.debug(f"获取模拟交易所 {self.name} 的订单 {order_id} 状态")

        # 检查订单是否存在
        if order_id not in self._orders:
            raise DataError(f"订单 {order_id} 不存在")

        order = self._orders[order_id]

        # 如果提供了交易对，检查是否匹配
        if symbol and order["symbol"] != symbol:
            raise DataError(f"订单 {order_id} 不是交易对 {symbol} 的订单")

        # 模拟API延迟
        await asyncio.sleep(0.15)

        # 对于未完成的订单，随机模拟成交进度
        if order["status"] in ["open", "partially_filled"]:
            # 随机决定是否更新状态
            if random.random() < 0.3:
                # 随机增加成交量
                additional_fill = min(
                    order["remaining"], order["remaining"] *
                    random.uniform(0.1, 0.5)
                )

                if additional_fill > 0:
                    order["filled"] += additional_fill
                    order["remaining"] -= additional_fill

                    if order["remaining"] == 0:
                        order["status"] = "closed"
                    else:
                        order["status"] = "partially_filled"

                    # 更新余额
                    base, quote = order["symbol"].split("/")

                    if order["side"] == "buy":
                        self._balances[base] = (
                            self._balances.get(base, 0) + additional_fill
                        )
                        self._balances[quote] = (
                            self._balances.get(quote, 0)
                            - additional_fill * order["price"]
                        )
                    else:
                        self._balances[base] = (
                            self._balances.get(base, 0) - additional_fill
                        )
                        self._balances[quote] = (
                            self._balances.get(quote, 0)
                            + additional_fill * order["price"]
                        )

                    # 添加交易记录
                    trade = {
                        "id": str(uuid.uuid4()),
                        "order": order_id,
                        "symbol": order["symbol"],
                        "side": order["side"],
                        "price": order["price"],
                        "amount": additional_fill,
                        "cost": additional_fill * order["price"],
                        "timestamp": datetime.now().timestamp(),
                        "datetime": datetime.now().isoformat(),
                    }

                    self._trades.append(trade)

        return order

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
            ConnectionError: 未连接到交易所时抛出
            AuthenticationError: 认证失败时抛出
        """
        if not self.is_connected:
            raise ConnectionError(f"未连接到模拟交易所 {self.name}")

        self.logger.debug(f"获取模拟交易所 {self.name} 的交易历史")

        # 模拟API延迟
        await asyncio.sleep(0.3)

        # 过滤交易
        trades = self._trades.copy()

        if symbol:
            trades = [trade for trade in trades if trade["symbol"] == symbol]

        if since:
            since_timestamp = since.timestamp()
            trades = [
                trade for trade in trades if trade["timestamp"] >= since_timestamp
            ]

        # 按时间排序（最新的在前）
        trades.sort(key=lambda x: x["timestamp"], reverse=True)

        # 限制返回数量
        if limit:
            trades = trades[:limit]

        return trades