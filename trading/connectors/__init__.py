# -*- coding: utf-8 -*-
"""
交易连接器模块
"""


class ExchangeConnector:
    """
    交易所连接器基类
    """

    def __init__(self, exchange_name="test_exchange"):
        """初始化交易所连接器"""
        self.exchange_name = exchange_name
        self.is_connected = False

    def connect(self):
        """连接到交易所"""
        self.is_connected = True
        return True

    def disconnect(self):
        """断开与交易所的连接"""
        self.is_connected = False
        return True

    def fetch_market_data(self, symbol):
        """获取市场数据"""
        return {"symbol": symbol, "price": 100.0, "volume": 1000.0}

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认连接器实例
default_connector = ExchangeConnector()