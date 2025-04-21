# -*- coding: utf-8 -*-
"""
交易执行模块
"""


class OrderExecutor:
    """
    订单执行器
    """

    def __init__(self, api=None):
        """初始化订单执行器"""
        self.api = api or "default_api"
        self.orders = []

    def execute_order(self, order):
        """执行订单"""
        self.orders.append(order)
        return {"order_id": "exec_" + order["order_id"], "status": "executed"}

    def get_order_status(self, order_id):
        """获取订单状态"""
        return {"order_id": order_id, "status": "filled"}

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认执行器实例
default_executor = OrderExecutor()