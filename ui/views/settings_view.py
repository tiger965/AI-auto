import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os
from typing import Dict, Any, Callable

from core.models.user import User
from core.services.settings_service import SettingsService
from core.utils.theme_manager import ThemeManager
from core.utils.sound_manager import SoundManager
from core.utils.animation_manager import AnimationManager
from core.utils.accessibility_manager import AccessibilityManager

class SettingsView(ttk.Frame):
    """
    设置视图，管理系统和用户配置
    
    负责处理系统主题切换、动画效果、音效管理和无障碍性设置，
    为用户提供流畅自然的交互体验和个性化的界面体验。
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.settings_service = SettingsService()
        self.user = User.get_current()
        
        # 初始化管理器
        self.theme_manager = ThemeManager()
        self.sound_manager = SoundManager()
        self.animation_manager = AnimationManager()
        self.accessibility_manager = AccessibilityManager()
        
        # 存储原始设置用于取消操作
        self.original_settings = {}
        
        self._create_widgets()
        self._layout_widgets()
        self._load_settings()
        
        # 播放页面加载音效
        self.sound_manager.play("page_load")
    
    def _create_widgets(self):
        """创建设置控件"""
        # 标题
        self.title_frame = ttk.Frame(self)
        self.title_label = ttk.Label(
            self.title_frame,
            text="系统设置",
            font=("Arial", 16, "bold")
        )
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self)
        
        # 主题设置选项卡
        self.theme_frame = ttk.Frame(self.notebook)
        
        # 交互设置选项卡
        self.interaction_frame = ttk.Frame(self.notebook)
        
        # 无障碍选项卡
        self.accessibility_frame = ttk.Frame(self.notebook)
        
        # API设置选项卡
        self.api_frame = ttk.Frame(self.notebook)
        
        # 通知设置选项卡
        self.notification_frame = ttk.Frame(self.notebook)
        
        # 添加选项卡到notebook
        self.notebook.add(self.theme_frame, text="主题设置")
        self.notebook.add(self.interaction_frame, text="交互体验")
        self.notebook.add(self.accessibility_frame, text="无障碍选项")
        self.notebook.add(self.api_frame, text="API配置")
        self.notebook.add(self.notification_frame, text="通知设置")
        
        # ===== 主题设置控件 =====
        self.theme_settings = [
            {"name": "theme", "label": "界面主题", "type": "combobox", 
             "values": ["默认", "暗黑", "浅色", "自定义"], "default": "默认"},
            {"name": "accent_color", "label": "强调色", "type": "color", 
             "default": "#3498db"},
            {"name": "font_family", "label": "字体", "type": "combobox", 
             "values": ["默认", "微软雅黑", "宋体", "黑体", "楷体"], "default": "默认"},
            {"name": "font_size", "label": "字体大小", "type": "scale", 
             "from": 8, "to": 18, "default": 10},
            {"name": "enable_animations", "label": "启用界面动画", "type": "checkbox", 
             "default": True},
            {"name": "custom_css", "label": "自定义CSS", "type": "text", 
             "default": "/* 在此处添加自定义CSS样式 */"}
        ]
        
        self.theme_widgets = {}
        
        # 主题设置标题
        self.theme_title = ttk.Label(
            self.theme_frame, 
            text="界面主题设置", 
            font=("Arial", 12, "bold")
        )
        self.theme_title.pack(pady=10)
        
        # 主题预览区域
        self.preview_frame = ttk.LabelFrame(self.theme_frame, text="主题预览")
        self.preview_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 创建简单的预览控件
        self.preview_content = ttk.Frame(self.preview_frame)
        preview_label = ttk.Label(self.preview_content, text="主题预览")
        preview_entry = ttk.Entry(self.preview_content, width=20)
        preview_entry.insert(0, "示例文本")
        preview_button = ttk.Button(self.preview_content, text="示例按钮")
        preview_check = ttk.Checkbutton(self.preview_content, text="示例复选框")
        
        preview_label.pack(pady=5)
        preview_entry.pack(pady=5)
        preview_button.pack(pady=5)
        preview_check.pack(pady=5)
        self.preview_content.pack(pady=10)
        
        # 主题设置控件
        for setting in self.theme_settings:
            frame = ttk.Frame(self.theme_frame)
            label = ttk.Label(frame, text=setting["label"])
            
            if setting["type"] == "combobox":
                widget = ttk.Combobox(frame, values=setting["values"], state="readonly", width=20)
                widget.set(setting["default"])
                widget.bind("<<ComboboxSelected>>", lambda e, name=setting["name"]: self._on_theme_change(name))
            
            elif setting["type"] == "color":
                color_frame = ttk.Frame(frame)
                color_preview = tk.Canvas(color_frame, width=20, height=20, bg=setting["default"])
                color_button = ttk.Button(
                    color_frame, 
                    text="选择...", 
                    command=lambda preview=color_preview, name=setting["name"]: self._choose_color(preview, name)
                )
                
                color_preview.pack(side=tk.LEFT, padx=5)
                color_button.pack(side=tk.LEFT)
                
                widget = color_frame
                widget.preview = color_preview
            
            elif setting["type"] == "scale":
                var = tk.IntVar(value=setting["default"])
                widget = ttk.Scale(
                    frame, 
                    from_=setting["from"], 
                    to=setting["to"], 
                    variable=var,
                    orient=tk.HORIZONTAL,
                    length=200
                )
                widget.var = var
                # 添加刻度值标签
                value_label = ttk.Label(frame, text=str(var.get()))
                widget.bind("<Motion>", lambda e, l=value_label, v=var: l.config(text=str(v.get())))
                value_label.pack(side=tk.RIGHT, padx=5)
            
            elif setting["type"] == "checkbox":
                var = tk.BooleanVar(value=setting["default"])
                widget = ttk.Checkbutton(frame, variable=var)
                widget.var = var
            
            elif setting["type"] == "text":
                text_frame = ttk.Frame(frame)
                widget = tk.Text(text_frame, width=40, height=5)
                widget.insert(tk.END, setting["default"])
                
                scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=widget.yview)
                widget.configure(yscrollcommand=scrollbar.set)
                
                widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                widget = text_frame
                widget.text_widget = widget.winfo_children()[0]  # 获取文本组件
            
            self.theme_widgets[setting["name"]] = widget
            
            label.pack(side=tk.LEFT, padx=10)
            widget.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
            frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 主题导入/导出按钮
        self.theme_buttons_frame = ttk.Frame(self.theme_frame)
        
        self.export_theme_button = ttk.Button(
            self.theme_buttons_frame,
            text="导出主题",
            command=self._export_theme
        )
        
        self.import_theme_button = ttk.Button(
            self.theme_buttons_frame,
            text="导入主题",
            command=self._import_theme
        )
        
        self.reset_theme_button = ttk.Button(
            self.theme_buttons_frame,
            text="重置主题",
            command=self._reset_theme
        )
        
        self.export_theme_button.pack(side=tk.LEFT, padx=5)
        self.import_theme_button.pack(side=tk.LEFT, padx=5)
        self.reset_theme_button.pack(side=tk.LEFT, padx=5)
        self.theme_buttons_frame.pack(pady=10)
        
        # ===== 交互设置控件 =====
        self.interaction_settings = [
            {"name": "animation_speed", "label": "动画速度", "type": "scale", 
             "from": 0, "to": 100, "default": 50},
            {"name": "enable_sound", "label": "启用音效反馈", "type": "checkbox", 
             "default": True},
            {"name": "sound_volume", "label": "音效音量", "type": "scale", 
             "from": 0, "to": 100, "default": 70},
            {"name": "hover_effect", "label": "悬停效果", "type": "combobox", 
             "values": ["无", "轻微", "明显"], "default": "轻微"},
            {"name": "click_effect", "label": "点击效果", "type": "combobox", 
             "values": ["无", "轻微", "明显"], "default": "轻微"}
        ]
        
        self.interaction_widgets = {}
        
        # 交互设置标题
        self.interaction_title = ttk.Label(
            self.interaction_frame, 
            text="交互体验设置", 
            font=("Arial", 12, "bold")
        )
        self.interaction_title.pack(pady=10)
        
        # 交互效果预览区
        self.interaction_preview = ttk.LabelFrame(self.interaction_frame, text="效果预览")
        
        self.animation_demo_button = ttk.Button(
            self.interaction_preview, 
            text="动画效果演示",
            command=self._show_animation_demo
        )
        
        self.sound_demo_button = ttk.Button(
            self.interaction_preview, 
            text="音效演示",
            command=self._play_sound_demo
        )
        
        self.animation_demo_button.pack(padx=20, pady=10)
        self.sound_demo_button.pack(padx=20, pady=10)
        self.interaction_preview.pack(fill=tk.X, padx=20, pady=10)
        
        # 交互设置控件
        for setting in self.interaction_settings:
            frame = ttk.Frame(self.interaction_frame)
            label = ttk.Label(frame, text=setting["label"])
            
            if setting["type"] == "combobox":
                widget = ttk.Combobox(frame, values=setting["values"], state="readonly", width=20)
                widget.set(setting["default"])
            
            elif setting["type"] == "scale":
                var = tk.IntVar(value=setting["default"])
                widget = ttk.Scale(
                    frame, 
                    from_=setting["from"], 
                    to=setting["to"], 
                    variable=var,
                    orient=tk.HORIZONTAL,
                    length=200
                )
                widget.var = var
                # 添加数值显示
                value_label = ttk.Label(frame, text=str(var.get()))
                widget.bind("<Motion>", lambda e, l=value_label, v=var: l.config(text=str(v.get())))
                value_label.pack(side=tk.RIGHT, padx=5)
                
                # 为音量添加实时预览
                if setting["name"] == "sound_volume":
                    widget.bind("<ButtonRelease-1>", lambda e: self.sound_manager.set_volume(widget.var.get() / 100))
            
            elif setting["type"] == "checkbox":
                var = tk.BooleanVar(value=setting["default"])
                widget = ttk.Checkbutton(frame, variable=var)
                widget.var = var
                
                # 为音效启用添加事件
                if setting["name"] == "enable_sound":
                    widget.config(command=lambda: self.sound_manager.set_enabled(widget.var.get()))
            
            self.interaction_widgets[setting["name"]] = widget
            
            label.pack(side=tk.LEFT, padx=10)
            widget.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
            frame.pack(fill=tk.X, padx=20, pady=10)
        
        # ===== 无障碍选项控件 =====
        self.accessibility_settings = [
            {"name": "high_contrast", "label": "高对比度模式", "type": "checkbox", 
             "default": False},
            {"name": "screen_reader", "label": "屏幕阅读器支持", "type": "checkbox", 
             "default": False},
            {"name": "keyboard_navigation", "label": "键盘导航增强", "type": "checkbox", 
             "default": True},
            {"name": "text_to_speech", "label": "文本转语音", "type": "checkbox", 
             "default": False},
            {"name": "reduce_motion", "label": "减少动态效果", "type": "checkbox", 
             "default": False},
            {"name": "large_text", "label": "大字体模式", "type": "checkbox", 
             "default": False}
        ]
        
        self.accessibility_widgets = {}
        
        # 无障碍设置标题
        self.accessibility_title = ttk.Label(
            self.accessibility_frame, 
            text="无障碍选项设置", 
            font=("Arial", 12, "bold")
        )
        self.accessibility_title.pack(pady=10)
        
        # 无障碍说明
        self.accessibility_desc = ttk.Label(
            self.accessibility_frame,
            text="这些设置帮助改善系统的可访问性，使其更易于使用。",
            wraplength=400
        )
        self.accessibility_desc.pack(pady=5)
        
        # 无障碍设置控件
        for setting in self.accessibility_settings:
            frame = ttk.Frame(self.accessibility_frame)
            label = ttk.Label(frame, text=setting["label"])
            
            if setting["type"] == "checkbox":
                var = tk.BooleanVar(value=setting["default"])
                widget = ttk.Checkbutton(frame, variable=var)
                widget.var = var
                
                # 为某些选项添加即时效果预览
                if setting["name"] == "high_contrast":
                    widget.config(command=lambda: self._preview_accessibility("high_contrast"))
                elif setting["name"] == "large_text":
                    widget.config(command=lambda: self._preview_accessibility("large_text"))
            
            self.accessibility_widgets[setting["name"]] = widget
            
            label.pack(side=tk.LEFT, padx=10)
            widget.pack(side=tk.RIGHT, padx=10)
            frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 快捷键设置区域
        self.shortcut_frame = ttk.LabelFrame(self.accessibility_frame, text="快捷键设置")
        
        # 添加一些快捷键设置
        shortcuts = [
            {"key": "Ctrl+Plus", "action": "放大界面"},
            {"key": "Ctrl+Minus", "action": "缩小界面"},
            {"key": "Ctrl+0", "action": "重置界面大小"},
            {"key": "Alt+A", "action": "切换高对比度模式"}
        ]
        
        for shortcut in shortcuts:
            shortcut_entry = ttk.Frame(self.shortcut_frame)
            action_label = ttk.Label(shortcut_entry, text=shortcut["action"], width=15)
            key_label = ttk.Label(shortcut_entry, text=shortcut["key"], width=15)
            change_button = ttk.Button(shortcut_entry, text="修改", width=10)
            
            action_label.pack(side=tk.LEFT, padx=5)
            key_label.pack(side=tk.LEFT, padx=5)
            change_button.pack(side=tk.LEFT, padx=5)
            shortcut_entry.pack(fill=tk.X, padx=10, pady=5)
        
        self.shortcut_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # ===== API设置控件 =====
        self.api_settings = [
            {"name": "api_key", "label": "API密钥", "type": "entry", "default": ""},
            {"name": "api_secret", "label": "API密钥", "type": "password", "default": ""},
            {"name": "api_endpoint", "label": "API服务端点", "type": "entry", 
             "default": "https://api.example.com"},
            {"name": "timeout", "label": "请求超时(秒)", "type": "spinbox", 
             "from": 1, "to": 60, "default": 10}
        ]
        
        self.api_widgets = {}
        
        # API设置标题
        self.api_title = ttk.Label(
            self.api_frame, 
            text="API配置设置", 
            font=("Arial", 12, "bold")
        )
        self.api_title.pack(pady=10)
        
        for setting in self.api_settings:
            frame = ttk.Frame(self.api_frame)
            label = ttk.Label(frame, text=setting["label"])
            
            if setting["type"] == "entry":
                widget = ttk.Entry(frame, width=30)
                widget.insert(0, setting["default"])
            elif setting["type"] == "password":
                widget = ttk.Entry(frame, width=30, show="*")
                widget.insert(0, setting["default"])
            elif setting["type"] == "spinbox":
                widget = ttk.Spinbox(
                    frame, 
                    from_=setting["from"],
                    to=setting["to"],
                    width=5
                )
                widget.set(setting["default"])
            
            self.api_widgets[setting["name"]] = widget
            
            label.pack(side=tk.LEFT, padx=10)
            widget.pack(side=tk.RIGHT, padx=10)
            frame.pack(fill=tk.X, padx=20, pady=10)
        
        # API状态指示器
        self.api_status_frame = ttk.Frame(self.api_frame)
        self.api_status_label = ttk.Label(self.api_status_frame, text="API状态:")
        self.api_status_indicator = ttk.Label(
            self.api_status_frame, 
            text="未连接", 
            foreground="red"
        )
        
        # 测试API连接按钮
        self.test_api_button = ttk.Button(
            self.api_frame,
            text="测试API连接",
            command=self._test_api_connection
        )
        
        self.api_status_label.pack(side=tk.LEFT, padx=10)
        self.api_status_indicator.pack(side=tk.LEFT, padx=5)
        self.api_status_frame.pack(fill=tk.X, padx=20, pady=10)
        self.test_api_button.pack(padx=20, pady=10)
        
        # ===== 通知设置控件 =====
        self.notification_settings = [
            {"name": "enable_email", "label": "启用邮件通知", "type": "checkbox", 
             "default": False},
            {"name": "email_address", "label": "邮箱地址", "type": "entry", 
             "default": ""},
            {"name": "enable_app", "label": "启用应用内通知", "type": "checkbox", 
             "default": True},
            {"name": "notify_on_trade", "label": "交易完成时通知", "type": "checkbox", 
             "default": True},
            {"name": "notify_on_news", "label": "重要新闻时通知", "type": "checkbox", 
             "default": True},
            {"name": "notification_sound", "label": "通知音效", "type": "combobox", 
             "values": ["默认", "清脆", "柔和", "无"], "default": "默认"}
        ]
        
        self.notification_widgets = {}
        
        # 通知设置标题
        self.notification_title = ttk.Label(
            self.notification_frame, 
            text="通知设置", 
            font=("Arial", 12, "bold")
        )
        self.notification_title.pack(pady=10)
        
        for setting in self.notification_settings:
            frame = ttk.Frame(self.notification_frame)
            label = ttk.Label(frame, text=setting["label"])
            
            if setting["type"] == "checkbox":
                var = tk.BooleanVar(value=setting["default"])
                widget = ttk.Checkbutton(frame, variable=var)
                widget.var = var
                
                # 添加邮件通知的依赖关系
                if setting["name"] == "enable_email":
                    widget.config(command=self._toggle_email_notification)
            elif setting["type"] == "entry":
                widget = ttk.Entry(frame, width=30)
                widget.insert(0, setting["default"])
            elif setting["type"] == "combobox":
                widget = ttk.Combobox(frame, values=setting["values"], state="readonly")
                widget.set(setting["default"])
                
                # 为通知音效添加预览功能
                if setting["name"] == "notification_sound":
                    widget.bind("<<ComboboxSelected>>", self._preview_notification_sound)
            
            self.notification_widgets[setting["name"]] = widget
            
            label.pack(side=tk.LEFT, padx=10)
            widget.pack(side=tk.RIGHT, padx=10)
            frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 通知预览按钮
        self.preview_notification_button = ttk.Button(
            self.notification_frame,
            text="预览通知效果",
            command=self._preview_notification
        )
        self.preview_notification_button.pack(pady=10)
        
        # ===== 底部按钮区域 =====
        self.buttons_frame = ttk.Frame(self)
        
        self.save_button = ttk.Button(
            self.buttons_frame,
            text="保存设置",
            command=self._save_settings
        )
        
        self.apply_button = ttk.Button(
            self.buttons_frame,
            text="应用",
            command=self._apply_settings
        )
        
        self.cancel_button = ttk.Button(
            self.buttons_frame,
            text="取消",
            command=self._cancel_changes
        )
    
    def _layout_widgets(self):
        """布局控件"""
        # 标题布局
        self.title_label.pack(pady=10)
        self.title_frame.pack(fill=tk.X)
        
        # 选项卡布局
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 按钮布局
        self.save_button.pack(side=tk.RIGHT, padx=10)
        self.apply_button.pack(side=tk.RIGHT, padx=10)
        self.cancel_button.pack(side=tk.RIGHT, padx=10)
        self.buttons_frame.pack(fill=tk.X, padx=20, pady=20)
    
    def _load_settings(self):
        """加载当前设置"""
        try:
            # 获取用户设置
            settings = self.settings_service.get_user_settings(self.user.id)
            self.original_settings = settings.copy()  # 保存原始设置
            
            # 更新主题设置控件
            for name, widget in self.theme_widgets.items():
                if name in settings:
                    if name == "theme" or name == "font_family":
                        widget.set(settings[name])
                    elif name == "font_size":
                        widget.var.set(settings[name])
                    elif name == "accent_color":
                        widget.preview.config(bg=settings[name])
                    elif name == "enable_animations":
                        widget.var.set(settings[name])
                    elif name == "custom_css":
                        widget.text_widget.delete(1.0, tk.END)
                        widget.text_widget.insert(tk.END, settings[name])
            
            # 更新交互设置控件
            for name, widget in self.interaction_widgets.items():
                if name in settings:
                    if isinstance(widget, ttk.Combobox):
                        widget.set(settings[name])
                    elif hasattr(widget, "var"):
                        widget.var.set(settings[name])
            
            # 更新无障碍设置控件
            for name, widget in self.accessibility_widgets.items():
                if name in settings:
                    if hasattr(widget, "var"):
                        widget.var.set(settings[name])
            
            # 更新API设置控件
            for name, widget in self.api_widgets.items():
                if name in settings:
                    if isinstance(widget, ttk.Spinbox):
                        widget.set(settings[name])
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, settings[name])
            
            # 更新通知设置控件
            for name, widget in self.notification_widgets.items():
                if name in settings:
                    if isinstance(widget, ttk.Combobox):
                        widget.set(settings[name])
                    elif hasattr(widget, "var"):
                        widget.var.set(settings[name])
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, settings[name])
            
            # 更新邮件设置的依赖关系
            self._toggle_email_notification()
            
            # 应用当前主题预览
            self._update_theme_preview()
                        
        except Exception as e:
            messagebox.showerror("加载设置错误", f"无法加载设置: {e}")
    
    def _save_settings(self):
        """保存设置"""
        settings = self._collect_all_settings()
        
        try:
            # 保存到服务
            self.settings_service.save_user_settings(self.user.id, settings)
            
            # 更新原始设置
            self.original_settings = settings.copy()
            
            # 应用设置
            self._apply_settings_internally(settings)
            
            # 提示用户
            messagebox.showinfo("设置已保存", "您的设置已成功保存")
            
            # 播放成功音效
            self.sound_manager.play("success")
            
        except Exception as e:
            messagebox.showerror("保存设置错误", f"无法保存设置: {e}")
            # 播放错误音效
            self.sound_manager.play("error")
    
    def _apply_settings(self):
        """应用当前设置但不保存"""
        settings = self._collect_all_settings()
        self._apply_settings_internally(settings)
        
        # 播放提示音效
        self.sound_manager.play("notification")
        messagebox.showinfo("设置已应用", "设置已临时应用，但尚未保存")
    
    def _collect_all_settings(self) -> Dict[str, Any]:
        """收集所有设置"""
        settings = {}
        
        # 收集主题设置
        for name, widget in self.theme_widgets.items():
            if name == "theme" or name == "font_family":
                settings[name] = widget.get()
            elif name == "font_size":
                settings[name] = widget.var.get()
            elif name == "accent_color":
                settings[name] = widget.preview.cget("bg")
            elif name == "enable_animations":
                settings[name] = widget.var.get()
            elif name == "custom_css":
                settings[name] = widget.text_widget.get(1.0, tk.END).strip()
        
        # 收集交互设置
        for name, widget in self.interaction_widgets.items():
            if isinstance(widget, ttk.Combobox):
                settings[name] = widget.get()
            elif hasattr(widget, "var"):
                settings[name] = widget.var.get()
        
        # 收集无障碍设置
        for name, widget in self.accessibility_widgets.items():
            if hasattr(widget, "var"):
                settings[name] = widget.var.get()
        
        # 收集API设置
        for name, widget in self.api_widgets.items():
            if isinstance(widget, ttk.Spinbox):
                settings[name] = widget.get()
            else:
                settings[name] = widget.get()
        
        # 收集通知设置
        for name, widget in self.notification_widgets.items():
            if isinstance(widget, ttk.Combobox):
                settings[name] = widget.get()
            elif hasattr(widget, "var"):
                settings[name] = widget.var.get()
            else:
                settings[name] = widget.get()
        
        return settings
    
    def _apply_settings_internally(self, settings: Dict[str, Any]):
        """内部应用设置"""
        # 应用主题
        theme_settings = {k: settings[k] for k in [
            "theme", "accent_color", "font_family", "font_size", 
            "enable_animations", "custom_css"
        ] if k in settings}
        
        self.theme_manager.apply_theme(theme_settings)
        
        # 应用交互设置
        interaction_settings = {k: settings[k] for k in [
            "animation_speed", "enable_sound", "sound_volume", 
            "hover_effect", "click_effect"
        ] if k in settings}
        
        self.animation_manager.set_settings(interaction_settings)
        self.sound_manager.set_settings(interaction_settings)
        
        # 应用无障碍设置
        accessibility_settings = {k: settings[k] for k in [
            "high_contrast", "screen_reader", "keyboard_navigation", 
            "text_to_speech", "reduce_motion", "large_text"
        ] if k in settings}
        
        self.accessibility_manager.apply_settings(accessibility_settings)
        
        # 应用控制器设置
        self.controller.apply_settings(settings)
    
    def _cancel_changes(self):
        """取消更改，重新加载设置"""
        self._load_settings()
        messagebox.showinfo("已取消", "已恢复原始设置")
        
        # 播放取消音效
        self.sound_manager.play("cancel")
    
    def _on_theme_change(self, name):
        """主题选项改变时更新预览"""
        self._update_theme_preview()
        
        # 播放交互反馈音效
        self.sound_manager.play("click")
    
    def _update_theme_preview(self):
        """更新主题预览"""
        # 获取当前主题设置
        theme = self.theme_widgets["theme"].get()
        accent_color = self.theme_widgets["accent_color"].preview.cget("bg")
        
        # 更新预览区域
        if theme == "暗黑":
            self.preview_frame.config(background="#333333")
            self.preview_content.config(background="#333333")
            for widget in self.preview_content.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.config(foreground="white", background="#333333")
        elif theme == "浅色":
            self.preview_frame.config(background="#f0f0f0")
            self.preview_content.config(background="#f0f0f0")
            for widget in self.preview_content.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.config(foreground="black", background="#f0f0f0")
        else:  # 默认或自定义
            self.preview_frame.config(background="")
            self.preview_content.config(background="")
            for widget in self.preview_content.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.config(foreground="", background="")
        
        # 应用强调色
        for widget in self.preview_content.winfo_children():
            if isinstance(widget, ttk.Button):
                # 注意：这不是直接支持的，在实际应用中需要更复杂的样式管理
                # 此处仅为演示目的
                try:
                    widget.configure(style="Accent.TButton")
                except:
                    pass
    
    def _choose_color(self, preview_widget, setting_name):
        """选择颜色"""
        current_color = preview_widget.cget("bg")
        color = colorchooser.askcolor(initialcolor=current_color, title="选择颜色")
        
        if color[1]:  # 用户选择了颜色而不是取消
            preview_widget.config(bg=color[1])
            self._update_theme_preview()
            
            # 播放交互反馈音效
            self.sound_manager.play("click")
    
    def _export_theme(self):
        """导出主题设置到文件"""
        from tkinter import filedialog
        
        # 收集主题设置
        theme_settings = {}
        for name, widget in self.theme_widgets.items():
            if name == "theme" or name == "font_family":
                theme_settings[name] = widget.get()
            elif name == "font_size":
                theme_settings[name] = widget.var.get()
            elif name == "accent_color":
                theme_settings[name] = widget.preview.cget("bg")
            elif name == "enable_animations":
                theme_settings[name] = widget.var.get()
            elif name == "custom_css":
                theme_settings[name] = widget.text_widget.get(1.0, tk.END).strip()
        
        # 选择保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导出主题"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(theme_settings, f, ensure_ascii=False, indent=4)
                
                messagebox.showinfo("导出成功", f"主题设置已导出至：\n{file_path}")
                
                # 播放成功音效
                self.sound_manager.play("success")
            except Exception as e:
                messagebox.showerror("导出失败", f"无法导出主题设置：{e}")
                
                # 播放错误音效
                self.sound_manager.play("error")
    
    def _import_theme(self):
        """从文件导入主题设置"""
        from tkinter import filedialog
        
        # 选择文件
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导入主题"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    theme_settings = json.load(f)
                
                # 应用导入的设置到控件
                for name, value in theme_settings.items():
                    if name in self.theme_widgets:
                        widget = self.theme_widgets[name]
                        
                        if name == "theme" or name == "font_family":
                            widget.set(value)
                        elif name == "font_size":
                            widget.var.set(value)
                        elif name == "accent_color":
                            widget.preview.config(bg=value)
                        elif name == "enable_animations":
                            widget.var.set(value)
                        elif name == "custom_css":
                            widget.text_widget.delete(1.0, tk.END)
                            widget.text_widget.insert(tk.END, value)
                
                # 更新预览
                self._update_theme_preview()
                
                messagebox.showinfo("导入成功", "主题设置已成功导入")
                
                # 播放成功音效
                self.sound_manager.play("success")
            except Exception as e:
                messagebox.showerror("导入失败", f"无法导入主题设置：{e}")
                
                # 播放错误音效
                self.sound_manager.play("error")
    
    def _reset_theme(self):
        """重置主题设置为默认值"""
        if messagebox.askyesno("重置主题", "确定要将主题设置重置为默认值吗？"):
            # 重置主题设置控件
            for setting in self.theme_settings:
                widget = self.theme_widgets[setting["name"]]
                
                if setting["type"] == "combobox":
                    widget.set(setting["default"])
                elif setting["type"] == "scale":
                    widget.var.set(setting["default"])
                elif setting["type"] == "checkbox":
                    widget.var.set(setting["default"])
                elif setting["type"] == "color":
                    widget.preview.config(bg=setting["default"])
                elif setting["type"] == "text":
                    widget.text_widget.delete(1.0, tk.END)
                    widget.text_widget.insert(tk.END, setting["default"])
            
            # 更新预览
            self._update_theme_preview()
            
            # 播放提示音效
            self.sound_manager.play("notification")
    
    def _show_animation_demo(self):
        """显示动画效果演示"""
        # 创建演示窗口
        demo_window = tk.Toplevel(self)
        demo_window.title("动画效果演示")
        demo_window.geometry("400x300")
        
        # 获取动画速度设置
        speed = self.interaction_widgets["animation_speed"].var.get()
        
        # 创建动画管理器
        demo_animation = self.animation_manager.create_animation(
            demo_window, speed=speed/100
        )
        
        # 添加一些演示控件
        frame = ttk.Frame(demo_window, padding=20)
        
        label = ttk.Label(
            frame, 
            text="动画效果演示", 
            font=("Arial", 14, "bold")
        )
        
        fade_button = ttk.Button(
            frame, 
            text="淡入淡出效果",
            command=lambda: demo_animation.fade_in_out(label)
        )
        
        slide_button = ttk.Button(
            frame, 
            text="滑动效果",
            command=lambda: demo_animation.slide_in(label)
        )
        
        pulse_button = ttk.Button(
            frame, 
            text="脉冲效果",
            command=lambda: demo_animation.pulse(label)
        )
        
        label.pack(pady=20)
        fade_button.pack(pady=10)
        slide_button.pack(pady=10)
        pulse_button.pack(pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 播放交互反馈音效
        self.sound_manager.play("click")
    
    def _play_sound_demo(self):
        """播放音效演示"""
        # 获取音量设置
        volume = self.interaction_widgets["sound_volume"].var.get() / 100
        
        # 临时设置音量
        original_volume = self.sound_manager.get_volume()
        self.sound_manager.set_volume(volume)
        
        # 播放一系列音效示例
        sounds = ["click", "success", "error", "notification", "hover"]
        
        def play_sequence(index=0):
            if index < len(sounds):
                # 创建临时标签显示当前音效
                temp_label = ttk.Label(
                    self.interaction_preview,
                    text=f"正在播放: {sounds[index]}",
                    font=("Arial", 10, "italic")
                )
                temp_label.pack(pady=5)
                
                # 播放音效
                self.sound_manager.play(sounds[index])
                
                # 安排下一个音效和清理标签
                self.after(1000, lambda: temp_label.destroy())
                self.after(1200, lambda: play_sequence(index + 1))
            else:
                # 恢复原始音量
                self.sound_manager.set_volume(original_volume)
        
        play_sequence()
    
    def _toggle_email_notification(self):
        """切换邮件通知设置"""
        enabled = self.notification_widgets["enable_email"].var.get()
        email_widget = self.notification_widgets["email_address"]
        
        if enabled:
            email_widget.config(state="normal")
        else:
            email_widget.config(state="disabled")
    
    def _preview_notification_sound(self, event):
        """预览通知音效"""
        sound_type = self.notification_widgets["notification_sound"].get()
        
        if sound_type == "默认":
            self.sound_manager.play("notification")
        elif sound_type == "清脆":
            self.sound_manager.play("notification_crisp")
        elif sound_type == "柔和":
            self.sound_manager.play("notification_soft")
        # 无音效选项不播放任何声音
    
    def _preview_notification(self):
        """预览通知效果"""
        # 获取当前通知设置
        sound = self.notification_widgets["notification_sound"].get()
        
        # 获取动画效果设置
        animation_enabled = self.theme_widgets["enable_animations"].var.get()
        
        # 创建通知预览窗口
        preview_window = tk.Toplevel(self)
        preview_window.title("通知预览")
        preview_window.geometry("300x100+{}+{}".format(
            self.winfo_rootx() + 50,
            self.winfo_rooty() + 50
        ))
        preview_window.attributes("-topmost", True)
        preview_window.overrideredirect(True)  # 移除窗口边框
        
        # 通知内容
        frame = ttk.Frame(preview_window, padding=10)
        
        title = ttk.Label(
            frame, 
            text="交易提醒", 
            font=("Arial", 11, "bold")
        )
        
        message = ttk.Label(
            frame, 
            text="您的交易订单已成功执行。点击查看详情。",
            wraplength=250
        )
        
        close_button = ttk.Button(
            frame, 
            text="关闭",
            width=10,
            command=preview_window.destroy
        )
        
        title.pack(anchor=tk.W)
        message.pack(anchor=tk.W, pady=5)
        close_button.pack(anchor=tk.E, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加阴影和边框效果
        preview_window.configure(bg="#222222")
        frame.configure(relief=tk.RAISED, borderwidth=1)
        
        # 播放通知音效
        if sound == "默认":
            self.sound_manager.play("notification")
        elif sound == "清脆":
            self.sound_manager.play("notification_crisp")
        elif sound == "柔和":
            self.sound_manager.play("notification_soft")
        
        # 如果启用了动画，添加淡入效果
        if animation_enabled:
            # 初始设置透明度为0
            preview_window.attributes("-alpha", 0.0)
            
            # 逐渐增加透明度
            def fade_in(alpha=0.0):
                alpha += 0.1
                preview_window.attributes("-alpha", alpha)
                if alpha < 1.0:
                    preview_window.after(50, lambda: fade_in(alpha))
            
            fade_in()
            
            # 5秒后自动关闭
            preview_window.after(5000, lambda: self._close_with_animation(preview_window))
        else:
            # 如果没有动画，5秒后直接关闭
            preview_window.after(5000, preview_window.destroy)
    
    def _close_with_animation(self, window):
        """带动画效果关闭窗口"""
        # 逐渐降低透明度
        def fade_out(alpha=1.0):
            alpha -= 0.1
            window.attributes("-alpha", alpha)
            if alpha > 0:
                window.after(50, lambda: fade_out(alpha))
            else:
                window.destroy()
        
        fade_out()
    
    def _preview_accessibility(self, feature):
        """预览无障碍功能"""
        if feature == "high_contrast":
            enabled = self.accessibility_widgets["high_contrast"].var.get()
            self._apply_high_contrast(enabled)
        elif feature == "large_text":
            enabled = self.accessibility_widgets["large_text"].var.get()
            self._apply_large_text(enabled)
    
    def _apply_high_contrast(self, enabled):
        """应用高对比度模式"""
        if enabled:
            # 更改预览区域样式
            for frame in [self.theme_frame, self.interaction_frame, 
                          self.accessibility_frame, self.api_frame, 
                          self.notification_frame]:
                frame.config(background="#000000")
                for widget in frame.winfo_children():
                    if isinstance(widget, ttk.Label):
                        widget.config(foreground="#FFFFFF", background="#000000")
        else:
            # 恢复默认样式
            for frame in [self.theme_frame, self.interaction_frame, 
                          self.accessibility_frame, self.api_frame, 
                          self.notification_frame]:
                frame.config(background="")
                for widget in frame.winfo_children():
                    if isinstance(widget, ttk.Label):
                        widget.config(foreground="", background="")
    
    def _apply_large_text(self, enabled):
        """应用大字体模式"""
        if enabled:
            # 临时应用大字体
            font_size = 14
            for frame in [self.theme_frame, self.interaction_frame, 
                          self.accessibility_frame, self.api_frame, 
                          self.notification_frame]:
                for widget in frame.winfo_children():
                    if isinstance(widget, ttk.Label) and not "bold" in widget.cget("font"):
                        widget.config(font=("Arial", font_size))
        else:
            # 恢复默认字体
            for frame in [self.theme_frame, self.interaction_frame, 
                          self.accessibility_frame, self.api_frame, 
                          self.notification_frame]:
                for widget in frame.winfo_children():
                    if isinstance(widget, ttk.Label) and not "bold" in widget.cget("font"):
                        widget.config(font=("Arial", 10))
    
    def _test_api_connection(self):
        """测试API连接"""
        api_key = self.api_widgets["api_key"].get()
        api_secret = self.api_widgets["api_secret"].get()
        api_endpoint = self.api_widgets["api_endpoint"].get()
        timeout = int(self.api_widgets["timeout"].get())
        
        if not api_key or not api_secret or not api_endpoint:
            messagebox.showwarning("输入不完整", "请填写所有API信息")
            self.sound_manager.play("warning")
            return
        
        # 更新状态为测试中
        self.api_status_indicator.config(text="测试中...", foreground="blue")
        self.update()  # 刷新界面
        
        try:
            # 测试API连接
            result = self.settings_service.test_api_connection(
                api_key, api_secret, api_endpoint, timeout
            )
            
            if result:
                self.api_status_indicator.config(text="连接成功", foreground="green")
                messagebox.showinfo("连接成功", "API连接测试成功！")
                self.sound_manager.play("success")
            else:
                self.api_status_indicator.config(text="连接失败", foreground="red")
                messagebox.showerror("连接失败", "API连接测试失败，请检查您的凭据")
                self.sound_manager.play("error")
                
        except Exception as e:
            self.api_status_indicator.config(text="连接错误", foreground="red")
            messagebox.showerror("连接错误", f"API连接测试出错: {e}")
            self.sound_manager.play("error")# 设置视图
