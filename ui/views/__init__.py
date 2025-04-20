"""
视图模块初始化文件
定义视图系统的基础类和管理器
"""

from tkinter import Frame, ttk
import tkinter as tk


class BaseView(Frame):
    """所有视图的基类，提供通用功能和结构"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        
        # 加载管理器
        self.theme_manager = controller.theme_manager
        self.animation_manager = controller.animation_manager
        self.sound_manager = controller.sound_manager
        
        # 初始化视图
        self._create_widgets()
        self._layout_widgets()
        self._apply_theme()
        
    def _create_widgets(self):
        """创建所有UI控件，子类必须实现此方法"""
        raise NotImplementedError("子类必须实现_create_widgets方法")
    
    def _layout_widgets(self):
        """布局所有控件，子类必须实现此方法"""
        raise NotImplementedError("子类必须实现_layout_widgets方法")
        
    def _apply_theme(self):
        """应用当前主题到视图"""
        theme = self.theme_manager.get_current_theme()
        self.configure(bg=theme['background'])
        
    def show(self):
        """显示视图，包含动画效果"""
        self.animation_manager.fade_in(self)
        self.sound_manager.play('view_transition')
        self.lift()
        
    def hide(self):
        """隐藏视图，包含动画效果"""
        self.animation_manager.fade_out(self)
        self.sound_manager.play('view_transition')


# 导出所有视图类，方便导入
from .dashboard_view import DashboardView
from .trading_view import TradingView
from .profile_view import ProfileView
from .analytics_view import AnalyticsView
from .help_view import HelpView

__all__ = [
    'BaseView',
    'DashboardView',
    'TradingView',
    'ProfileView',
    'AnalyticsView',
    'HelpView'
]# 视图模块初始化
