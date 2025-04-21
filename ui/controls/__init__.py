# -*- coding: utf-8 -*-
"""
控件UI模块
"""


class Control:
    """
    控件基类
    """

    def __init__(self, control_type="button", label="操作"):
        """初始化控件"""
        self.control_type = control_type
        self.label = label
        self.is_enabled = True

    def enable(self):
        """启用控件"""
        self.is_enabled = True
        return True

    def disable(self):
        """禁用控件"""
        self.is_enabled = False
        return True

    def render(self):
        """渲染控件"""
        return {
            "type": self.control_type,
            "label": self.label,
            "enabled": self.is_enabled,
            "status": "rendered",
        }

    def method1(self):
        """测试方法1"""
        return "method1 result"


# 创建默认控件实例
default_control = Control()