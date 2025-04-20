# -*- coding: utf-8 -*-
"""
UI Module: 用户界面模块
功能描述: 提供用户交互界面，包括Web界面和命令行界面
版本: 1.0
创建日期: 2025-04-17
"""

from . import web
from . import cli

# 版本信息
__version__ = '1.0.0'

class UIManager:
    """
    用户界面管理器，负责初始化和协调各类界面
    
    该类是UI模块的核心，负责管理和协调不同类型的用户界面，
    包括Web界面和命令行界面，确保它们能够协同工作。
    
    属性:
        active_interfaces (list): 当前激活的界面列表
        theme_manager (ThemeManager): 主题管理器，控制界面样式和主题
    """
    
    def __init__(self, config=None):
        """
        初始化UI管理器
        
        Args:
            config (dict, optional): 界面配置参数
        """
        self.active_interfaces = []
        self.config = config or {}
        self.theme_manager = ThemeManager()
        
    def initialize(self):
        """
        初始化所有界面组件
        
        根据配置初始化不同类型的界面，并设置默认主题
        
        Returns:
            bool: 初始化是否成功
        """
        # 设置默认主题 - 实现灵动、有温度的设计
        self.theme_manager.set_theme('harmony')
        
        return True
        
    def launch_interface(self, interface_type='web'):
        """
        启动指定类型的界面
        
        Args:
            interface_type (str): 界面类型，可选值: 'web', 'cli'
            
        Returns:
            object: 启动的界面实例
            
        Raises:
            ValueError: 当指定的界面类型不支持时
        """
        if interface_type == 'web':
            interface = web.WebInterface(self.config.get('web', {}))
            interface.set_theme(self.theme_manager.current_theme)
            self.active_interfaces.append(interface)
            return interface
        elif interface_type == 'cli':
            interface = cli.CLIInterface(self.config.get('cli', {}))
            self.active_interfaces.append(interface)
            return interface
        else:
            raise ValueError(f"不支持的界面类型: {interface_type}")
    
    def shutdown(self):
        """
        关闭所有活动界面并清理资源
        
        Returns:
            bool: 关闭操作是否成功
        """
        for interface in self.active_interfaces:
            interface.close()
        self.active_interfaces = []
        return True


class ThemeManager:
    """
    主题管理器，负责管理和应用用户界面主题
    
    提供主题切换、自定义和应用功能，确保界面视觉一致性
    
    属性:
        available_themes (dict): 可用主题字典
        current_theme (dict): 当前应用的主题
    """
    
    def __init__(self):
        """初始化主题管理器"""
        self.available_themes = {
            'harmony': {
                'font_family': '"Inter", "HarmonyOS Sans", "苹方", sans-serif',
                'text_color': '#333333',
                'primary_color': '#3a7bd5',
                'secondary_color': '#6d5dfc',
                'background_color': '#f9f9fb',
                'accent_color': '#d4e2f9',
                'success_color': '#38b48b',
                'warning_color': '#f0ba3a',
                'error_color': '#eb6771',
                'border_radius': '12px',
                'animation_speed': '0.3s',
                'font_smoothing': 'antialiased',
                'text_rendering': 'optimizeLegibility',
                'shadow_style': '0 8px 16px rgba(58, 123, 213, 0.12)',
                'sound_feedback': True,
                'breathing_animation': True
            },
            'night': {
                'font_family': '"Inter", "HarmonyOS Sans", "苹方", sans-serif',
                'text_color': '#e0e0e0',
                'primary_color': '#6d5dfc',
                'secondary_color': '#3a7bd5',
                'background_color': '#1a1a2e',
                'accent_color': '#292946',
                'success_color': '#38b48b',
                'warning_color': '#f0ba3a',
                'error_color': '#eb6771',
                'border_radius': '12px',
                'animation_speed': '0.3s',
                'font_smoothing': 'antialiased',
                'text_rendering': 'optimizeLegibility',
                'shadow_style': '0 8px 16px rgba(0, 0, 0, 0.25)',
                'sound_feedback': True,
                'breathing_animation': True
            }
        }
        self.current_theme = self.available_themes['harmony']
    
    def set_theme(self, theme_name):
        """
        设置当前主题
        
        Args:
            theme_name (str): 主题名称
            
        Returns:
            bool: 设置是否成功
            
        Raises:
            ValueError: 当指定的主题不存在时
        """
        if theme_name in self.available_themes:
            self.current_theme = self.available_themes[theme_name]
            return True
        raise ValueError(f"主题不存在: {theme_name}")
    
    def customize_theme(self, theme_name, **properties):
        """
        自定义现有主题或创建新主题
        
        Args:
            theme_name (str): 主题名称
            **properties: 主题属性键值对
            
        Returns:
            dict: 更新后的主题
        """
        if theme_name in self.available_themes:
            # 更新现有主题
            self.available_themes[theme_name].update(properties)
        else:
            # 创建新主题
            self.available_themes[theme_name] = properties
        
        return self.available_themes[theme_name]


# 默认UI管理器实例，提供全局访问点
default_manager = UIManager()# UI模块入口，定义UIManager和ThemeManager
