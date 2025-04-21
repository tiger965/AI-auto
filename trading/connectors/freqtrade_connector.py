""""
模块名称：freqtrade_connector
功能描述：Freqtrade交易所连接器，用于与Freqtrade框架集成
版本：1.0
创建日期：2025-04-20
作者：Claude
""""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from datetime import datetime, timedelta
import time

from trading.connectors.base_connector import (
    BaseConnector,
    ConnectionError,
    AuthenticationError,
    OrderError,
    DataError
)


class FreqtradeConnector(BaseConnector):
    """"
    Freqtrade连接器类
    
    与Freqtrade框架集成的交易所连接器，通过Freqtrade的交易引擎进行交易操作。
    
    属性:
        name (str): 交易所名称
        is_connected (bool): 是否已连接到交易所
        supported_order_types (List[str]): 支持的订单类型列表
        logger (logging.Logger): 日志记录器
    """"
    
def __init__(self, name: str = "FreqtradeConnector", api_key: Optional[str] = None,:
                 api_secret: Optional[str] = None, additional_params: Optional[Dict[str, Any]] = None):
        """"
        初始化Freqtrade连接器
        
        参数:
            name (str, optional): 连接器名称，默认为"FreqtradeConnector"
            api_key (str, optional): API密钥，对于Freqtrade连接器非必须
            api_secret (str, optional): API密钥的密钥，对于Freqtrade连接器非必须
            additional_params (Dict[str, Any], optional): 额外的连接参数，包括：
                - config_path (str): Freqtrade配置文件路径
                - db_url (str): 数据库URL
                - strategy_name (str): 策略名称
        """"
        super().__init__(name, api_key, api_secret, additional_params)
        
        # 设置默认支持的订单类型
        self.supported_order_types = ["market", "limit", "stop_loss", "stop_loss_limit"]
        
        # Freqtrade配置
        self.config_path = self._additional_params.get("config_path")
        self.db_url = self._additional_params.get("db_url")
        self.strategy_name = self._additional_params.get("strategy_name")
        
        # Freqtrade实例
        self._freqtrade_instance = None
        self._exchange = None
        
        self.logger.info(f"Freqtrade连接器 {name} 初始化完成")
    
    async def connect(self) -> bool:
        """"
        连接到Freqtrade
        
        返回:
            bool: 连接是否成功
            
        异常:
            ConnectionError: 连接失败时抛出
        """"
        if self.is_connected:
            return True
        
        self.logger.info(f"正在连接到Freqtrade")
        
        try:
            # 检查FreqtradeBot实例
            if self._freqtrade_instance:
                # 使用FreqtradeBot获取未完成订单
                open_orders = self._freqtrade_instance.exchange.fetch_open_orders(symbol)
            else:
                # 直接使用交易所获取未完成订单
                open_orders = await self._exchange.fetch_open_orders(symbol)
            
            # 转换为标准格式
            result = []
            
            for order in open_orders:
                # 构建标准格式的订单信息
                standard_order = {
                    "id": order.get('id'),
                    "symbol": order.get('symbol'),
                    "type": order.get('type'),
                    "side": order.get('side'),
                    "price": order.get('price'),
                    "amount": order.get('amount'),
                    "cost": order.get('cost'),
                    "filled": order.get('filled', 0),
                    "remaining": order.get('remaining', order.get('amount', 0)),
                    "status": order.get('status'),
                    "timestamp": order.get('timestamp'),
                    "datetime": order.get('datetime'),
                    "info": order.get('info', {})
                }
                
                result.append(standard_order)
            
            return result
        
        except Exception as e:
            self.logger.error(f"获取未完成订单失败: {e}")
            
            if "auth" in str(e).lower() or "apikey" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(f"获取未完成订单认证失败: {e}")
            else:
                raise DataError(f"获取未完成订单失败: {e}")
    
    async def create_order(self, symbol: str, order_type: str, side: str, 
                          amount: float, price: Optional[float] = None,
                          params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """"
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
            ConnectionError: 未连接到Freqtrade时抛出
            AuthenticationError: 认证失败时抛出
            OrderError: 创建订单失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.info(f"在Freqtrade创建 {symbol} {side} {order_type} 订单")
        
        # 检查订单类型是否支持
        if order_type not in self.supported_order_types:
            raise OrderError(f"不支持的订单类型 {order_type}")
        
        # 检查订单方向是否有效
        if side not in ["buy", "sell"]:
            raise OrderError(f"无效的订单方向 {side}")
        
        # 对于限价单，检查价格是否有效
        if order_type == "limit" and (price is None or price <= 0):
            raise OrderError("限价单必须指定有效价格")
        
        try:
            # 准备参数
            order_params = params or {}
            
            # 检查FreqtradeBot实例
            if self._freqtrade_instance and hasattr(self._freqtrade_instance, 'create_order'):
                # 使用FreqtradeBot创建订单
                order = await self._freqtrade_instance.create_order(
                    symbol=symbol,
                    type=order_type,
                    side=side,
                    amount=amount,
                    price=price,
                    params=order_params
                )
            else:
                # 直接使用交易所创建订单
                order = await self._exchange.create_order(
                    symbol=symbol,
                    type=order_type,
                    side=side,
                    amount=amount,
                    price=price,
                    params=order_params
                )
            
            # 转换为标准格式
            standard_order = {
                "id": order.get('id'),
                "symbol": order.get('symbol'),
                "type": order.get('type'),
                "side": order.get('side'),
                "price": order.get('price'),
                "amount": order.get('amount'),
                "cost": order.get('cost'),
                "filled": order.get('filled', 0),
                "remaining": order.get('remaining', order.get('amount', 0)),
                "status": order.get('status'),
                "timestamp": order.get('timestamp'),
                "datetime": order.get('datetime'),
                "info": order.get('info', {})
            }
            
            return standard_order
        
        except Exception as e:
            self.logger.error(f"创建订单失败: {e}")
            
            if "auth" in str(e).lower() or "apikey" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(f"创建订单认证失败: {e}")
            else:
                raise OrderError(f"创建订单失败: {e}")
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """"
        取消订单
        
        参数:
            order_id (str): 订单ID
            symbol (str, optional): 交易对符号。某些交易所需要提供此参数。
            
        返回:
            Dict[str, Any]: 取消的订单信息
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            AuthenticationError: 认证失败时抛出
            OrderError: 取消订单失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.info(f"在Freqtrade取消订单 {order_id}")
        
        try:
            # 检查FreqtradeBot实例
            if self._freqtrade_instance and hasattr(self._freqtrade_instance, 'cancel_order'):
                # 使用FreqtradeBot取消订单
                order = await self._freqtrade_instance.cancel_order(order_id, symbol)
            else:
                # 直接使用交易所取消订单
                order = await self._exchange.cancel_order(order_id, symbol)
            
            # 转换为标准格式
            standard_order = {
                "id": order.get('id'),
                "symbol": order.get('symbol'),
                "type": order.get('type'),
                "side": order.get('side'),
                "price": order.get('price'),
                "amount": order.get('amount'),
                "cost": order.get('cost'),
                "filled": order.get('filled', 0),
                "remaining": order.get('remaining', order.get('amount', 0)),
                "status": order.get('status'),
                "timestamp": order.get('timestamp'),
                "datetime": order.get('datetime'),
                "info": order.get('info', {})
            }
            
            return standard_order
        
        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
            
            if "auth" in str(e).lower() or "apikey" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(f"取消订单认证失败: {e}")
            else:
                raise OrderError(f"取消订单失败: {e}")
    
    async def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """"
        获取订单状态
        
        参数:
            order_id (str): 订单ID
            symbol (str, optional): 交易对符号。某些交易所需要提供此参数。
            
        返回:
            Dict[str, Any]: 订单状态信息
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的订单 {order_id} 状态")
        
        try:
            # 检查FreqtradeBot实例
            if self._freqtrade_instance and hasattr(self._freqtrade_instance, 'fetch_order'):
                # 使用FreqtradeBot获取订单状态
                order = await self._freqtrade_instance.fetch_order(order_id, symbol)
            else:
                # 直接使用交易所获取订单状态
                order = await self._exchange.fetch_order(order_id, symbol)
            
            # 转换为标准格式
            standard_order = {
                "id": order.get('id'),
                "symbol": order.get('symbol'),
                "type": order.get('type'),
                "side": order.get('side'),
                "price": order.get('price'),
                "amount": order.get('amount'),
                "cost": order.get('cost'),
                "filled": order.get('filled', 0),
                "remaining": order.get('remaining', order.get('amount', 0)),
                "status": order.get('status'),
                "timestamp": order.get('timestamp'),
                "datetime": order.get('datetime'),
                "info": order.get('info', {})
            }
            
            return standard_order
        
        except Exception as e:
            self.logger.error(f"获取订单状态失败: {e}")
            
            if "auth" in str(e).lower() or "apikey" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(f"获取订单状态认证失败: {e}")
            else:
                raise DataError(f"获取订单状态失败: {e}")
    
    async def get_trade_history(self, symbol: Optional[str] = None, 
                               since: Optional[datetime] = None,
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """"
        获取交易历史
        
        参数:
            symbol (str, optional): 交易对符号。如果为None，则获取所有交易对的交易历史。
            since (datetime, optional): 开始时间
            limit (int, optional): 返回的交易数量限制
            
        返回:
            List[Dict[str, Any]]: 交易历史列表
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的交易历史")
        
        try:
            # 设置参数
            params = {}
            
            if since:
                # 转换为时间戳（毫秒）
                since_ms = int(since.timestamp() * 1000)
                params['since'] = since_ms
            
            if limit:
                params['limit'] = limit
            
            # 检查FreqtradeBot实例
            if self._freqtrade_instance and hasattr(self._freqtrade_instance, 'fetch_my_trades'):
                # 使用FreqtradeBot获取交易历史
                trades = await self._freqtrade_instance.fetch_my_trades(symbol, params=params)
            else:
                # 直接使用交易所获取交易历史
                trades = await self._exchange.fetch_my_trades(symbol, params=params)
            
            # 转换为标准格式
            result = []
            
            for trade in trades:
                # 构建标准格式的交易信息
                standard_trade = {
                    "id": trade.get('id'),
                    "order": trade.get('order'),
                    "symbol": trade.get('symbol'),
                    "side": trade.get('side'),
                    "price": trade.get('price'),
                    "amount": trade.get('amount'),
                    "cost": trade.get('cost'),
                    "fee": trade.get('fee'),
                    "timestamp": trade.get('timestamp'),
                    "datetime": trade.get('datetime'),
                    "info": trade.get('info', {})
                }
                
                result.append(standard_trade)
            
            return result
        
        except Exception as e:
            self.logger.error(f"获取交易历史失败: {e}")
            
            if "auth" in str(e).lower() or "apikey" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(f"获取交易历史认证失败: {e}")
            else:
                raise DataError(f"获取交易历史失败: {e}")
    
    # 额外的Freqtrade特定方法
    
    async def run_strategy(self, timeframe: str = "5m", limit: int = 500) -> Dict[str, Any]:
        """"
        运行Freqtrade策略，生成交易信号
        
        参数:
            timeframe (str, optional): 时间周期，默认为"5m"
            limit (int, optional): 历史数据数量限制，默认为500
            
        返回:
            Dict[str, Any]: 策略运行结果
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 运行策略失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        if not self._freqtrade_instance:
            raise DataError(f"Freqtrade实例未初始化，无法运行策略")
        
        self.logger.info(f"运行Freqtrade策略")
        
        try:
            # 运行策略
            result = await self._freqtrade_instance.strategy.analyze_pair_list(
                self._freqtrade_instance.active_pair_whitelist, 
                timeframe, 
                limit
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"运行策略失败: {e}")
            raise DataError(f"运行策略失败: {e}")
    
    async def get_strategy_performance(self) -> Dict[str, Any]:
        """"
        获取策略性能统计
        
        返回:
            Dict[str, Any]: 策略性能统计
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 获取性能统计失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        if not self._freqtrade_instance:
            raise DataError(f"Freqtrade实例未初始化，无法获取策略性能")
        
        self.logger.info(f"获取Freqtrade策略性能")
        
        try:
            # 获取策略性能
            performance = await self._freqtrade_instance.rpc.rpc_performance()
            
            return performance
        
        except Exception as e:
            self.logger.error(f"获取策略性能失败: {e}")
            raise DataError(f"获取策略性能失败: {e}")
    
    async def start_trading(self) -> bool:
        """"
        启动交易
        
        返回:
            bool: 启动是否成功
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 启动交易失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        if not self._freqtrade_instance:
            raise DataError(f"Freqtrade实例未初始化，无法启动交易")
        
        self.logger.info(f"启动Freqtrade交易")
        
        try:
            # 启动交易
            await self._freqtrade_instance.start()
            
            return True
        
        except Exception as e:
            self.logger.error(f"启动交易失败: {e}")
            raise DataError(f"启动交易失败: {e}")
    
    async def stop_trading(self) -> bool:
        """"
        停止交易
        
        返回:
            bool: 停止是否成功
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 停止交易失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        if not self._freqtrade_instance:
            raise DataError(f"Freqtrade实例未初始化，无法停止交易")
        
        self.logger.info(f"停止Freqtrade交易")
        
        try:
            # 停止交易
            await self._freqtrade_instance.cleanup()
            
            return True
        
        except Exception as e:
            self.logger.error(f"停止交易失败: {e}")
            raise DataError(f"停止交易失败: {e}")
    
    async def get_backtest_results(self, strategy_name: str = None, 
                                  timeframe: str = "5m", 
                                  timerange: str = None) -> Dict[str, Any]:
        """"
        获取回测结果
        
        参数:
            strategy_name (str, optional): 策略名称，默认使用当前策略
            timeframe (str, optional): 时间周期，默认为"5m"
            timerange (str, optional): 时间范围，例如"20210101-20210201"
            
        返回:
            Dict[str, Any]: 回测结果
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 获取回测结果失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        # 使用导入的Freqtrade模块
        try:
            from freqtrade.optimize.backtesting import Backtesting
            from freqtrade.resolvers import StrategyResolver
            from freqtrade.data.history import load_pair_history
            from freqtrade.configuration import Configuration
        except ImportError as e:
            self.logger.error(f"无法导入Freqtrade回测模块: {e}")
            raise DataError(f"无法导入Freqtrade回测模块: {e}")
        
        self.logger.info(f"获取Freqtrade回测结果")
        
        try:
            # 加载配置
            config = Configuration.from_files([self.config_path])
            config = config.get_config()
            
            # 设置回测参数
            config['timeframe'] = timeframe
            
            if timerange:
                config['timerange'] = timerange
            
            # 加载策略
            if not strategy_name:
                strategy_name = self.strategy_name or config.get('strategy')
            
            if not strategy_name:
                raise DataError(f"未指定策略名称")
            
            strategy = StrategyResolver.load_strategy(strategy_name)
            strategy_instance = strategy(config)
            
            # 初始化回测
            backtest = Backtesting(config)
            
            # 加载历史数据
            data = load_pair_history(
                datadir=config['datadir'],
                pairs=config['exchange']['pair_whitelist'],
                timeframe=timeframe,
                timerange=timerange,
                startup_candles=strategy_instance.startup_candle_count,
                data_format=config.get('dataformat_ohlcv', 'json'),
                candle_type=config.get('candle_type_def', 'spot')
            )
            
            # 运行回测
            results = backtest.backtest(
                strategy=strategy_instance,
                processed=data,
                start_date=None,
                end_date=None
            )
            
            return results
        
        except Exception as e:
            self.logger.error(f"获取回测结果失败: {e}")
            raise DataError(f"获取回测结果失败: {e}")
 导入Freqtrade模块
            # 注意：这里采用延迟导入的方式，避免在导入连接器模块时就必须安装Freqtrade
            try:
                from freqtrade.configuration import Configuration
                from freqtrade.freqtradebot import FreqtradeBot
                from freqtrade.resolvers import ExchangeResolver
            except ImportError as e:
                self.logger.error(f"无法导入Freqtrade模块: {e}")
                raise ConnectionError(f"请确保已安装Freqtrade: {e}")
            
            # 检查配置路径是否有效
            if not self.config_path or not os.path.exists(self.config_path):
                self.logger.error(f"Freqtrade配置文件不存在: {self.config_path}")
                raise ConnectionError(f"Freqtrade配置文件不存在: {self.config_path}")
            
            # 加载Freqtrade配置
            config = Configuration.from_files([self.config_path])
            config = config.get_config()
            
            # 如果提供了数据库URL，更新配置
            if self.db_url:
                config['db_url'] = self.db_url
            
            # 如果提供了API密钥，更新配置
            if self._api_key and self._api_secret:
                exchange_name = config.get('exchange', {}).get('name', 'binance')
                
                if 'exchange' not in config:
                    config['exchange'] = {}
                
                if 'key' not in config['exchange']:
                    config['exchange']['key'] = self._api_key
                
                if 'secret' not in config['exchange']:
                    config['exchange']['secret'] = self._api_secret
            
            # 初始化交易所
            exchange_name = config.get('exchange', {}).get('name', 'binance')
            self._exchange = ExchangeResolver.load_exchange(exchange_name, config)
            
            # 检查交易所连接
            if not await self._exchange.is_alive():
                self.logger.error(f"无法连接到交易所: {exchange_name}")
                raise ConnectionError(f"无法连接到交易所: {exchange_name}")
            
            # 如果提供了策略名称，初始化FreqtradeBot
            if self.strategy_name:
                from freqtrade.resolvers import StrategyResolver
                
                strategy = StrategyResolver.load_strategy(self.strategy_name)
                strategy_instance = strategy(config)
                
                self._freqtrade_instance = FreqtradeBot(config, strategy_instance)
            
            self.is_connected = True
            self.logger.info(f"已成功连接到Freqtrade")
            
            return True
        
        except Exception as e:
            self.logger.error(f"连接到Freqtrade失败: {e}")
            raise ConnectionError(f"连接到Freqtrade失败: {e}")
    
    async def disconnect(self) -> bool:
        """"
        断开与Freqtrade的连接
        
        返回:
            bool: 断开连接是否成功
        """"
        if not self.is_connected:
            return True
        
        self.logger.info(f"正在断开与Freqtrade的连接")
        
        # 释放资源
        self._exchange = None
        
        if self._freqtrade_instance:
            # 关闭FreqtradeBot
            try:
                await self._freqtrade_instance.cleanup()
            except Exception as e:
                self.logger.warning(f"关闭FreqtradeBot时发生警告: {e}")
            
            self._freqtrade_instance = None
        
        self.is_connected = False
        self.logger.info(f"已成功断开与Freqtrade的连接")
        
        return True
    
    async def get_markets(self) -> List[Dict[str, Any]]:
        """"
        获取所有可交易市场信息
        
        返回:
            List[Dict[str, Any]]: 市场信息列表
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 获取数据失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的市场信息")
        
        try:
            # 获取交易所市场
            markets = self._exchange.markets
            
            # 转换为标准格式
            result = []
            
            for symbol, market in markets.items():
                # 跳过非活跃市场
                if not market.get('active', False):
                    continue
                
                # 构建标准格式的市场信息
                standard_market = {
                    "symbol": symbol,
                    "base": market.get('base'),
                    "quote": market.get('quote'),
                    "active": market.get('active', False),
                    "precision": market.get('precision', {}),
                    "limits": market.get('limits', {}),
                    "info": market.get('info', {})
                }
                
                result.append(standard_market)
            
            return result
        
        except Exception as e:
            self.logger.error(f"获取市场信息失败: {e}")
            raise DataError(f"获取市场信息失败: {e}")
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """"
        获取指定交易对的当前行情
        
        参数:
            symbol (str): 交易对符号
            
        返回:
            Dict[str, Any]: 当前行情数据
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 获取数据失败或交易对不存在时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的 {symbol} 行情")
        
        try:
            # 获取交易对行情
            ticker = await self._exchange.fetch_ticker(symbol)
            
            # 转换为标准格式
            standard_ticker = {
                "symbol": ticker.get('symbol'),
                "last": ticker.get('last'),
                "bid": ticker.get('bid'),
                "ask": ticker.get('ask'),
                "high": ticker.get('high'),
                "low": ticker.get('low'),
                "volume": ticker.get('volume'),
                "timestamp": ticker.get('timestamp'),
                "datetime": ticker.get('datetime'),
                "info": ticker.get('info', {})
            }
            
            return standard_ticker
        
        except Exception as e:
            self.logger.error(f"获取 {symbol} 行情失败: {e}")
            raise DataError(f"获取 {symbol} 行情失败: {e}")
    
    async def get_order_book(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """"
        获取指定交易对的订单簿
        
        参数:
            symbol (str): 交易对符号
            depth (int, optional): 订单簿深度。默认为100。
            
        返回:
            Dict[str, Any]: 订单簿数据
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 获取数据失败或交易对不存在时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的 {symbol} 订单簿")
        
        try:
            # 获取交易对订单簿
            order_book = await self._exchange.fetch_order_book(symbol, depth)
            
            # 转换为标准格式
            standard_order_book = {
                "symbol": symbol,
                "bids": order_book.get('bids', []),
                "asks": order_book.get('asks', []),
                "timestamp": order_book.get('timestamp'),
                "datetime": order_book.get('datetime'),
                "nonce": order_book.get('nonce')
            }
            
            return standard_order_book
        
        except Exception as e:
            self.logger.error(f"获取 {symbol} 订单簿失败: {e}")
            raise DataError(f"获取 {symbol} 订单簿失败: {e}")
    
    async def get_historical_data(self, symbol: str, timeframe: str, 
                                 since: Optional[datetime] = None, 
                                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """"
        获取历史K线数据
        
        参数:
            symbol (str): 交易对符号
            timeframe (str): 时间周期 (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            since (datetime, optional): 开始时间
            limit (int, optional): 返回的K线数量限制
            
        返回:
            List[Dict[str, Any]]: 历史K线数据列表
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            DataError: 获取数据失败或交易对不存在时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的 {symbol} {timeframe} 历史数据")
        
        try:
            # 设置参数
            params = {}
            
            if since:
                # 转换为时间戳（毫秒）
                since_ms = int(since.timestamp() * 1000)
                params['since'] = since_ms
            
            if limit:
                params['limit'] = limit
            
            # 获取历史K线数据
            ohlcv = await self._exchange.fetch_ohlcv(symbol, timeframe, params=params)
            
            # 转换为标准格式
            result = []
            
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                
                # 转换时间戳为datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                
                standard_candle = {
                    "timestamp": timestamp,
                    "datetime": dt.isoformat(),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                }
                
                result.append(standard_candle)
            
            return result
        
        except Exception as e:
            self.logger.error(f"获取 {symbol} {timeframe} 历史数据失败: {e}")
            raise DataError(f"获取 {symbol} {timeframe} 历史数据失败: {e}")
    
    async def get_account_balance(self) -> Dict[str, float]:
        """"
        获取账户余额
        
        返回:
            Dict[str, float]: 账户各资产余额
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的账户余额")
        
        try:
            # 检查FreqtradeBot实例
            if self._freqtrade_instance:
                # 使用FreqtradeBot获取余额
                wallets = self._freqtrade_instance.wallets
                balances = wallets.get_all_balances()
                
                # 转换为标准格式
                standard_balances = {}
                
                for currency, balance in balances.items():
                    standard_balances[currency] = balance.get('total', 0.0)
                
                return standard_balances
            else:
                # 直接使用交易所获取余额
                balance = await self._exchange.fetch_balance()
                
                # 转换为标准格式
                standard_balances = {}
                
                for currency, amount in balance.get('total', {}).items():
                    if amount and amount > 0:
                        standard_balances[currency] = amount
                
                return standard_balances
        
        except Exception as e:
            self.logger.error(f"获取账户余额失败: {e}")
            
            if "auth" in str(e).lower() or "apikey" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(f"获取账户余额认证失败: {e}")
            else:
                raise DataError(f"获取账户余额失败: {e}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """"
        获取未完成订单
        
        参数:
            symbol (str, optional): 交易对符号。如果为None，则获取所有交易对的未完成订单。
            
        返回:
            List[Dict[str, Any]]: 未完成订单列表
            
        异常:
            ConnectionError: 未连接到Freqtrade时抛出
            AuthenticationError: 认证失败时抛出
            DataError: 获取数据失败时抛出
        """"
        if not self.is_connected:
            raise ConnectionError(f"未连接到Freqtrade")
        
        self.logger.debug(f"获取Freqtrade的未完成订单")
        
        try:
            #

        
        except Exception as e:
            
        
            print(f"错误: {str(e)}")