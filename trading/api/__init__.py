# -*- coding: utf-8 -*-
"""
交易API模块
"""


class TradingAPI:
    """
    交易API封装
    """

    def __init__(self, api_key="test_key", api_secret="test_secret"):
        """初始化交易API"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_authenticated = False

    def authenticate(self):
        """API认证"""
        self.is_authenticated = True
        return True

    def place_order(self, symbol, side, quantity, price):
        """下单"""
        return {
            "order_id": "test_order_123",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "status": "filled",
        }

    def cancel_order(self, order_id):
        """取消订单"""
        return {"order_id": order_id, "status": "cancelled"}

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认API实例
default_api = TradingAPI()