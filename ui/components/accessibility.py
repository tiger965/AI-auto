# ui/components/accessibility.py
"""
无障碍性支持组件

这个组件负责提高应用程序的无障碍性和易用性。
它实现了以下功能：
1. 支持屏幕阅读器兼容性
2. 键盘导航增强
3. 高对比度模式
4. 文本大小调整
5. 专注模式

设计理念:
- 确保应用可以被所有用户使用，无论其能力如何
- 提供足够的灵活性，使界面适应不同用户的需求
- 保持易用性的同时不牺牲功能性
"""

import tkinter as tk
from tkinter import ttk
import os
import json
import platform
import sys

class AccessibilityManager:
    """无障碍性管理器，负责管理应用的无障碍性功能"""
    
    def __init__(self, theme_manager=None, config_dir=None):
        """
        初始化无障碍性管理器
        
        Args:
            theme_manager: 主题管理器实例，用于高对比度模式
            config_dir: 配置文件目录
        """
        self.theme_manager = theme_manager
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".ai_assistant")
        
        # 确保目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 默认设置
        self.settings = {
            'screen_reader_support': False,  # 屏幕阅读器支持
            'high_contrast': False,          # 高对比度模式
            'keyboard_navigation': True,     # 键盘导航
            'text_zoom': 1.0,                # 文本缩放比例 (1.0 = 100%)
            'focus_mode': False,             # 专注模式
            'reduced_motion': False,         # 减少动画
            'auto_read': False,              # 自动朗读
            'cursor_size': 1.0,              # 光标大小倍数
            'hover_time': 0.5                # 鼠标悬停触发时间（秒）
        }
        
        # 初始化辅助功能变量
        self.active_widgets = []          # 追踪活动部件
        self.current_focus_index = -1     # 当前焦点索引
        self.focus_highlight = None       # 焦点高亮元素
        
        # 支持屏幕阅读器相关
        self.screen_reader_available = self._check_screen_reader()
        self.screen_reader_callbacks = []  # 文本变更回调
        
        # 初始化注册的文本到语音引擎
        self.tts_engine = None
        
        # 加载设置
        self._load_settings()
        
        # 如果主题管理器可用，注册主题变化监听器
        if self.theme_manager:
            self.theme_manager.add_listener(self._on_theme_change)
    
    def _check_screen_reader(self):
        """检查系统是否有屏幕阅读器支持"""
        is_available = False
        system = platform.system()
        
        try:
            if system == "Windows":
                # 检查常见的Windows屏幕阅读器
                import ctypes
                # 检查NVDA
                nvda_running = False
                try:
                    import comtypes.client
                    comtypes.client.CreateObject("NvdaControllerClient.NvdaController")
                    nvda_running = True
                except:
                    pass
                
                # 检查JAWS
                jaws_running = False
                try:
                    # 检查JAWS进程
                    import psutil
                    for proc in psutil.process_iter(['name']):
                        if 'jfw' in proc.info['name'].lower():
                            jaws_running = True
                            break
                except:
                    pass
                
                # 检查Narrator
                narrator_running = False
                try:
                    # 简单检查Narrator窗口
                    hwnd = ctypes.windll.user32.FindWindowW(None, "Narrator")
                    if hwnd != 0:
                        narrator_running = True
                except:
                    pass
                
                is_available = nvda_running or jaws_running or narrator_running
                
            elif system == "Darwin":  # macOS
                # 检查VoiceOver
                try:
                    result = os.popen('defaults read com.apple.universalaccess voiceOverOnOffKey').read()
                    is_available = "1" in result
                except:
                    pass
                    
            elif system == "Linux":
                # 检查Orca
                try:
                    result = os.popen('ps -A | grep -i orca').read()
                    is_available = bool(result.strip())
                except:
                    pass
                
        except Exception as e:
            print(f"检查屏幕阅读器时出错: {e}")
        
        return is_available
    
    def _load_settings(self):
        """加载无障碍性设置"""
        settings_path = os.path.join(self.config_dir, "accessibility_settings.json")
        
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # 更新设置，保留默认值
                for key, value in loaded_settings.items():
                    if key in self.settings:
                        self.settings[key] = value
        except Exception as e:
            print(f"加载无障碍性设置时出错: {e}")
    
    def _save_settings(self):
        """保存无障碍性设置"""
        settings_path = os.path.join(self.config_dir, "accessibility_settings.json")
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"保存无障碍性设置时出错: {e}")
    
    def get_setting(self, key):
        """
        获取设置值
        
        Args:
            key: 设置键名
            
        Returns:
            设置值，如果键不存在则返回None
        """
        return self.settings.get(key)
    
    def set_setting(self, key, value):
        """
        设置设置值
        
        Args:
            key: 设置键名
            value: 设置值
            
        Returns:
            bool: 是否成功设置
        """
        if key not in self.settings:
            return False
        
        self.settings[key] = value
        self._save_settings()
        
        # 特殊处理某些设置更改
        if key == 'high_contrast' and self.theme_manager:
            # 切换高对比度主题
            theme = "high_contrast" if value else "light"
            self.theme_manager.set_theme(theme)
        
        elif key == 'keyboard_navigation':
            # 切换键盘导航
            if value:
                self._setup_keyboard_navigation()
            else:
                self._remove_keyboard_navigation()
        
        elif key == 'text_zoom':
            # 更新文本缩放
            self._apply_text_zoom()
        
        return True
    
    def register_for_accessibility(self, widget, role=None, description=None):
        """
        注册部件以支持无障碍性
        
        Args:
            widget: Tkinter窗口部件
            role: 部件角色（如'button', 'text', 'heading'等）
            description: 部件描述，用于屏幕阅读器
            
        Returns:
            widget: 注册的窗口部件
        """
        if widget in self.active_widgets:
            # 已注册，更新信息
            index = self.active_widgets.index(widget)
            self.active_widgets[index] = widget
        else:
            # 新注册
            self.active_widgets.append(widget)
        
        # 设置部件属性
        widget._a11y_role = role
        widget._a11y_description = description
        
        # 应用可访问性增强
        self._enhance_widget_accessibility(widget)
        
        return widget
    
    def _enhance_widget_accessibility(self, widget):
        """为部件添加无障碍性增强"""
        # 添加焦点处理
        if self.settings['keyboard_navigation']:
            # 确保部件可以接收焦点
            try:
                if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton, ttk.Radiobutton)):
                    # 这些部件默认可以接收焦点
                    pass
                elif isinstance(widget, tk.Label) and hasattr(widget, '_a11y_role') and widget._a11y_role == 'button':
                    # 作为按钮的标签
                    widget.configure(takefocus=1)
                else:
                    # 其他部件默认不接收焦点
                    current = str(widget.cget('takefocus')).lower()
                    if current not in ['1', 'true']:
                        widget.configure(takefocus=1)
            except:
                # 某些部件可能不支持takefocus
                pass
        
        # 为部件添加鼠标悬停效果
        def on_enter(event, w=widget):
            if hasattr(w, '_a11y_description') and w._a11y_description:
                self._show_tooltip(w, w._a11y_description)
                
                # 如果启用了自动朗读
                if self.settings['auto_read'] and self.tts_engine:
                    self._speak_text(w._a11y_description)
        
        def on_leave(event):
            self._hide_tooltip()
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
        # 应用文本缩放
        self._apply_text_zoom_to_widget(widget)
        
        # 屏幕阅读器支持
        if self.settings['screen_reader_support']:
            # 添加额外属性以支持屏幕阅读器
            if hasattr(widget, '_a11y_role') and widget._a11y_role:
                widget.winfo_class = lambda role=widget._a11y_role: role
            
            # 对于文本变更，添加通知
            if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
                # 绑定文本变更事件
                if isinstance(widget, (tk.Entry, ttk.Entry)):
                    vcmd = (widget.register(self._on_text_change), '%P', '%W')
                    widget.configure(validate="all", validatecommand=vcmd)
                elif isinstance(widget, tk.Text):
                    widget.bind("<<TextModified>>", lambda e, w=widget: self._on_text_widget_change(w))
    
    def _on_text_change(self, text, widget_id):
        """处理文本变更事件"""
        if self.settings['screen_reader_support'] and self.tts_engine:
            # 通知屏幕阅读器文本变更
            widget = self._nametowidget(widget_id)
            if widget and hasattr(widget, '_a11y_description'):
                description = widget._a11y_description or "文本框"
                self._speak_text(f"{description}: {text}")
        
        # 调用注册的回调
        for callback in self.screen_reader_callbacks:
            try:
                callback(text)
            except Exception as e:
                print(f"调用屏幕阅读器回调时出错: {e}")
        
        return True  # 验证总是通过
    
    def _on_text_widget_change(self, text_widget):
        """处理文本部件变更事件"""
        if self.settings['screen_reader_support'] and self.tts_engine:
            # 获取当前插入点所在行
            try:
                insert_index = text_widget.index(tk.INSERT)
                line, column = map(int, insert_index.split('.'))
                current_line = text_widget.get(f"{line}.0", f"{line}.end")
                
                if current_line:
                    # 只朗读当前行
                    description = text_widget._a11y_description if hasattr(text_widget, '_a11y_description') else "文本区域"
                    self._speak_text(f"{description}, 第{line}行: {current_line}")
            except Exception as e:
                print(f"处理文本部件变更时出错: {e}")
    
    def _nametowidget(self, widget_id):
        """将部件ID转换为部件对象"""
        for widget in self.active_widgets:
            if str(widget) == widget_id:
                return widget
        return None
    
    def register_screen_reader_callback(self, callback):
        """
        注册屏幕阅读器回调函数
        
        Args:
            callback: 回调函数，接收文本参数
            
        Returns:
            bool: 是否成功注册
        """
        if callable(callback) and callback not in self.screen_reader_callbacks:
            self.screen_reader_callbacks.append(callback)
            return True
        return False
    
    def unregister_screen_reader_callback(self, callback):
        """
        取消注册屏幕阅读器回调函数
        
        Args:
            callback: 要取消的回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        if callback in self.screen_reader_callbacks:
            self.screen_reader_callbacks.remove(callback)
            return True
        return False
    
    def register_tts_engine(self, engine):
        """
        注册文本到语音引擎
        
        Args:
            engine: 文本到语音引擎，必须有speak方法
            
        Returns:
            bool: 是否成功注册
        """
        if hasattr(engine, 'speak') and callable(engine.speak):
            self.tts_engine = engine
            return True
        return False
    
    def _speak_text(self, text):
        """使用TTS引擎朗读文本"""
        if self.tts_engine and hasattr(self.tts_engine, 'speak'):
            try:
                self.tts_engine.speak(text)
                return True
            except Exception as e:
                print(f"使用TTS引擎朗读文本时出错: {e}")
        return False
    
    def announce(self, text):
        """
        朗读文本给屏幕阅读器
        
        Args:
            text: 要朗读的文本
            
        Returns:
            bool: 是否成功朗读
        """
        if self.settings['screen_reader_support']:
            return self._speak_text(text)
        return False
    
    def _setup_keyboard_navigation(self):
        """设置键盘导航"""
        # 将在根窗口上实现，当根窗口可用时
        pass
    
    def _remove_keyboard_navigation(self):
        """移除键盘导航"""
        # 将在根窗口上实现，当根窗口可用时
        pass
    
    def setup_keyboard_navigation(self, root):
        """
        为根窗口设置键盘导航
        
        Args:
            root: Tkinter根窗口
            
        Returns:
            bool: 是否成功设置
        """
        if not self.settings['keyboard_navigation']:
            return False
        
        try:
            # 绑定Tab和Shift+Tab用于导航
            root.bind("<Tab>", lambda event: self._next_focus(event, root))
            root.bind("<Shift-Tab>", lambda event: self._prev_focus(event, root))
            
            # 绑定箭头键用于导航
            root.bind("<Down>", lambda event: self._next_focus(event, root))
            root.bind("<Up>", lambda event: self._prev_focus(event, root))
            
            # 绑定Home和End键
            root.bind("<Home>", lambda event: self._first_focus(event, root))
            root.bind("<End>", lambda event: self._last_focus(event, root))
            
            # 创建焦点高亮
            self._create_focus_highlight(root)
            
            return True
        except Exception as e:
            print(f"设置键盘导航时出错: {e}")
            return False
    
    def _create_focus_highlight(self, root):
        """创建焦点高亮元素"""
        try:
            # 创建顶层窗口作为高亮
            self.focus_highlight = tk.Toplevel(root)
            self.focus_highlight.overrideredirect(True)  # 无边框
            self.focus_highlight.attributes("-topmost", True)  # 置顶
            self.focus_highlight.withdraw()  # 初始隐藏
            
            # 创建高亮框架
            highlight_frame = tk.Frame(
                self.focus_highlight,
                bg="#3355ff",  # 蓝色边框
                bd=2
            )
            highlight_frame.pack(fill=tk.BOTH, expand=True)
            
            # 使其半透明
            self.focus_highlight.attributes("-alpha", 0.3)
            
            # 绑定失去焦点事件
            root.bind("<FocusOut>", lambda event: self.focus_highlight.withdraw())
        except Exception as e:
            print(f"创建焦点高亮时出错: {e}")
            self.focus_highlight = None
    
    def _update_focus_highlight(self, widget):
        """更新焦点高亮位置"""
        if not self.focus_highlight:
            return
        
        try:
            # 获取部件在屏幕上的位置和大小
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            width = widget.winfo_width()
            height = widget.winfo_height()
            
            # 设置高亮位置和大小
            self.focus_highlight.geometry(f"{width+4}x{height+4}+{x-2}+{y-2}")
            self.focus_highlight.deiconify()
        except Exception as e:
            print(f"更新焦点高亮时出错: {e}")
            self.focus_highlight.withdraw()
    
    def _next_focus(self, event, root):
        """移动到下一个可获得焦点的部件"""
        focusable = self._get_all_focusable(root)
        if not focusable:
            return
        
        # 查找当前焦点部件
        current = root.focus_get()
        
        if current in focusable:
            index = focusable.index(current)
            next_index = (index + 1) % len(focusable)
        else:
            next_index = 0
        
        # 设置下一个部件的焦点
        next_widget = focusable[next_index]
        next_widget.focus_set()
        
        # 更新焦点高亮
        self._update_focus_highlight(next_widget)
        
        # 朗读部件描述
        if self.settings['screen_reader_support'] and hasattr(next_widget, '_a11y_description'):
            self._speak_text(next_widget._a11y_description)
        
        return "break"  # 阻止默认行为
    
    def _prev_focus(self, event, root):
        """移动到上一个可获得焦点的部件"""
        focusable = self._get_all_focusable(root)
        if not focusable:
            return
        
        # 查找当前焦点部件
        current = root.focus_get()
        
        if current in focusable:
            index = focusable.index(current)
            prev_index = (index - 1) % len(focusable)
        else:
            prev_index = 0
        
        # 设置上一个部件的焦点
        prev_widget = focusable[prev_index]
        prev_widget.focus_set()
        
        # 更新焦点高亮
        self._update_focus_highlight(prev_widget)
        
        # 朗读部件描述
        if self.settings['screen_reader_support'] and hasattr(prev_widget, '_a11y_description'):
            self._speak_text(prev_widget._a11y_description)
        
        return "break"  # 阻止默认行为
    
    def _first_focus(self, event, root):
        """移动到第一个可获得焦点的部件"""
        focusable = self._get_all_focusable(root)
        if not focusable:
            return
        
        # 设置第一个部件的焦点
        first_widget = focusable[0]
        first_widget.focus_set()
        
        # 更新焦点高亮
        self._update_focus_highlight(first_widget)
        
        # 朗读部件描述
        if self.settings['screen_reader_support'] and hasattr(first_widget, '_a11y_description'):
            self._speak_text(first_widget._a11y_description)
        
        return "break"  # 阻止默认行为
    
    def _last_focus(self, event, root):
        """移动到最后一个可获得焦点的部件"""
        focusable = self._get_all_focusable(root)
        if not focusable:
            return
        
        # 设置最后一个部件的焦点
        last_widget = focusable[-1]
        last_widget.focus_set()
        
        # 更新焦点高亮
        self._update_focus_highlight(last_widget)
        
        # 朗读部件描述
        if self.settings['screen_reader_support'] and hasattr(last_widget, '_a11y_description'):
            self._speak_text(last_widget._a11y_description)
        
        return "break"  # 阻止默认行为
    
    def _get_all_focusable(self, widget):
        """获取所有可获得焦点的部件"""
        result = []
        
        def collect_focusable(w):
            # 检查是否可以获得焦点
            try:
                if 'takefocus' in w.configure() and str(w.cget('takefocus')).lower() in ['1', 'true']:
                    if w.winfo_viewable():  # 确保部件可见
                        result.append(w)
            except:
                pass
            
            # 遍历子部件
            try:
                for child in w.winfo_children():
                    collect_focusable(child)
            except:
                pass
        
        collect_focusable(widget)
        return result
    
    def _show_tooltip(self, widget, text):
        """显示工具提示"""
        if not hasattr(self, 'tooltip'):
            # 创建工具提示窗口
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)  # 无边框
            self.tooltip.wm_attributes("-topmost", True)  # 置顶
            
            # 创建标签
            self.tip_label = tk.Label(
                self.tooltip,
                text="",
                justify=tk.LEFT,
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                font=("TkDefaultFont", int(10 * self.settings['text_zoom']))
            )
            self.tip_label.pack()
            
            # 初始隐藏
            self.tooltip.withdraw()
        
        # 更新文本
        self.tip_label.configure(text=text)
        self.tooltip.update_idletasks()
        
        # 计算位置
        x = widget.winfo_rootx() + widget.winfo_width() + 5
        y = widget.winfo_rooty() + 5
        
        # 如果提示会超出屏幕，调整位置
        screen_width = widget.winfo_screenwidth()
        tip_width = self.tooltip.winfo_reqwidth()
        
        if x + tip_width > screen_width:
            x = screen_width - tip_width - 5
        
        # 设置位置
        self.tooltip.geometry(f"+{x}+{y}")
        
        # 显示提示
        self.tooltip.deiconify()
    
    def _hide_tooltip(self):
        """隐藏工具提示"""
        if hasattr(self, 'tooltip'):
            self.tooltip.withdraw()
    
    def _apply_text_zoom(self):
        """应用文本缩放到所有注册的部件"""
        for widget in self.active_widgets:
            self._apply_text_zoom_to_widget(widget)
    
    def _apply_text_zoom_to_widget(self, widget):
        """应用文本缩放到单个部件"""
        try:
            # 获取缩放比例
            zoom = self.settings['text_zoom']
            
            # 根据部件类型应用缩放
            if isinstance(widget, (tk.Label, ttk.Label)):
                # 获取当前字体
                font = widget.cget('font')
                if isinstance(font, str):
                    # 默认字体
                    family = font
                    size = 10  # 默认大小
                else:
                    # 自定义字体
                    family = font[0]
                    size = font[1]
                
                # 应用缩放
                new_size = int(size * zoom)
                widget.configure(font=(family, new_size))
            
            elif isinstance(widget, (tk.Button, ttk.Button)):
                # 获取当前字体
                try:
                    font = widget.cget('font')
                    if font:
                        if isinstance(font, str):
                            # 默认字体
                            family = font
                            size = 10  # 默认大小
                        else:
                            # 自定义字体
                            family = font[0]
                            size = font[1]
                        
                        # 应用缩放
                        new_size = int(size * zoom)
                        widget.configure(font=(family, new_size))
                except:
                    pass
            
            elif isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
                # 获取当前字体
                try:
                    font = widget.cget('font')
                    if font:
                        if isinstance(font, str):
                            # 默认字体
                            family = font
                            size = 10  # 默认大小
                        else:
                            # 自定义字体
                            family = font[0]
                            size = font[1]
                        
                        # 应用缩放
                        new_size = int(size * zoom)
                        widget.configure(font=(family, new_size))
                except:
                    pass
        except Exception as e:
            print(f"应用文本缩放到部件时出错: {e}")
    
    def _on_theme_change(self, old_theme, new_theme, progress):
        """处理主题变化事件"""
        # 如果是高对比度模式
        if new_theme == 'high_contrast' and progress >= 1.0:
            self.settings['high_contrast'] = True
        elif old_theme == 'high_contrast' and progress >= 1.0:
            self.settings['high_contrast'] = False
    
    def create_accessibility_settings_panel(self, parent):
        """
        创建无障碍性设置面板
        
        Args:
            parent: 父级窗口部件
            
        Returns:
            ttk.Frame: 设置面板框架
        """
        # 创建主框架
        frame = ttk.LabelFrame(parent, text="无障碍性设置")
        
        # 创建设置控件
        # 屏幕阅读器支持
        screen_reader_var = tk.BooleanVar(value=self.settings['screen_reader_support'])
        screen_reader_check = ttk.Checkbutton(
            frame,
            text="屏幕阅读器支持",
            variable=screen_reader_var,
            command=lambda: self.set_setting('screen_reader_support', screen_reader_var.get())
        )
        screen_reader_check.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        # 高对比度模式
        high_contrast_var = tk.BooleanVar(value=self.settings['high_contrast'])
        high_contrast_check = ttk.Checkbutton(
            frame,
            text="高对比度模式",
            variable=high_contrast_var,
            command=lambda: self.set_setting('high_contrast', high_contrast_var.get())
        )
        high_contrast_check.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        # 键盘导航
        keyboard_nav_var = tk.BooleanVar(value=self.settings['keyboard_navigation'])
        keyboard_nav_check = ttk.Checkbutton(
            frame,
            text="增强键盘导航",
            variable=keyboard_nav_var,
            command=lambda: self.set_setting('keyboard_navigation', keyboard_nav_var.get())
        )
        keyboard_nav_check.grid(row=2, column=0, sticky='w', padx=10, pady=5)
        
        # 文本缩放
        text_zoom_frame = ttk.Frame(frame)
        text_zoom_frame.grid(row=3, column=0, sticky='we', padx=10, pady=5)
        
        ttk.Label(text_zoom_frame, text="文本大小:").pack(side=tk.LEFT)
        
        text_zoom_var = tk.DoubleVar(value=self.settings['text_zoom'])
        text_zoom_scale = ttk.Scale(
            text_zoom_frame,
            from_=0.8,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=text_zoom_var,
            length=150
        )
        text_zoom_scale.pack(side=tk.LEFT, padx=5)
        
        def update_text_zoom(*args):
            value = text_zoom_var.get()
            self.set_setting('text_zoom', value)
            text_zoom_label.configure(text=f"{int(value * 100)}%")
        
        text_zoom_scale.configure(command=update_text_zoom)
        
        text_zoom_label = ttk.Label(text_zoom_frame, text=f"{int(text_zoom_var.get() * 100)}%")
        text_zoom_label.pack(side=tk.LEFT, padx=5)
        
        # 专注模式
        focus_mode_var = tk.BooleanVar(value=self.settings['focus_mode'])
        focus_mode_check = ttk.Checkbutton(
            frame,
            text="专注模式",
            variable=focus_mode_var,
            command=lambda: self.set_setting('focus_mode', focus_mode_var.get())
        )
        focus_mode_check.grid(row=4, column=0, sticky='w', padx=10, pady=5)
        
        # 减少动画
        reduced_motion_var = tk.BooleanVar(value=self.settings['reduced_motion'])
        reduced_motion_check = ttk.Checkbutton(
            frame,
            text="减少动画",
            variable=reduced_motion_var,
            command=lambda: self.set_setting('reduced_motion', reduced_motion_var.get())
        )
        reduced_motion_check.grid(row=5, column=0, sticky='w', padx=10, pady=5)
        
        # 自动朗读
        auto_read_var = tk.BooleanVar(value=self.settings['auto_read'])
        auto_read_check = ttk.Checkbutton(
            frame,
            text="鼠标悬停朗读",
            variable=auto_read_var,
            command=lambda: self.set_setting('auto_read', auto_read_var.get())
        )
        auto_read_check.grid(row=6, column=0, sticky='w', padx=10, pady=5)
        
        # 光标大小
        cursor_size_frame = ttk.Frame(frame)
        cursor_size_frame.grid(row=7, column=0, sticky='we', padx=10, pady=5)
        
        ttk.Label(cursor_size_frame, text="光标大小:").pack(side=tk.LEFT)
        
        cursor_size_var = tk.DoubleVar(value=self.settings['cursor_size'])
        cursor_size_scale = ttk.Scale(
            cursor_size_frame,
            from_=1.0,
            to=3.0,
            orient=tk.HORIZONTAL,
            variable=cursor_size_var,
            length=150
        )
        cursor_size_scale.pack(side=tk.LEFT, padx=5)
        
        def update_cursor_size(*args):
            value = cursor_size_var.get()
            self.set_setting('cursor_size', value)
            cursor_size_label.configure(text=f"{int(value * 100)}%")
        
        cursor_size_scale.configure(command=update_cursor_size)
        
        cursor_size_label = ttk.Label(cursor_size_frame, text=f"{int(cursor_size_var.get() * 100)}%")
        cursor_size_label.pack(side=tk.LEFT, padx=5)
        
        # 鼠标悬停时间
        hover_time_frame = ttk.Frame(frame)
        hover_time_frame.grid(row=8, column=0, sticky='we', padx=10, pady=5)
        
        ttk.Label(hover_time_frame, text="悬停触发时间:").pack(side=tk.LEFT)
        
        hover_time_var = tk.DoubleVar(value=self.settings['hover_time'])
        hover_time_scale = ttk.Scale(
            hover_time_frame,
            from_=0.2,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=hover_time_var,
            length=150
        )
        hover_time_scale.pack(side=tk.LEFT, padx=5)
        
        def update_hover_time(*args):
            value = hover_time_var.get()
            self.set_setting('hover_time', value)
            hover_time_label.configure(text=f"{value:.1f}秒")
        
        hover_time_scale.configure(command=update_hover_time)
        
        hover_time_label = ttk.Label(hover_time_frame, text=f"{hover_time_var.get():.1f}秒")
        hover_time_label.pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        def reset_settings():
            # 恢复默认设置
            self.settings = {
                'screen_reader_support': False,
                'high_contrast': False,
                'keyboard_navigation': True,
                'text_zoom': 1.0,
                'focus_mode': False,
                'reduced_motion': False,
                'auto_read': False,
                'cursor_size': 1.0,
                'hover_time': 0.5
            }
            self._save_settings()
            
            # 更新控件
            screen_reader_var.set(False)
            high_contrast_var.set(False)
            keyboard_nav_var.set(True)
            text_zoom_var.set(1.0)
            focus_mode_var.set(False)
            reduced_motion_var.set(False)
            auto_read_var.set(False)
            cursor_size_var.set(1.0)
            hover_time_var.set(0.5)
            
            # 应用设置
            if self.theme_manager:
                self.theme_manager.set_theme("light")
            self._apply_text_zoom()
        
        reset_button = ttk.Button(frame, text="恢复默认设置", command=reset_settings)
        reset_button.grid(row=9, column=0, pady=10)
        
        # 注册部件以支持无障碍性
        self.register_for_accessibility(
            screen_reader_check,
            role="checkbox",
            description="屏幕阅读器支持复选框"
        )
        
        self.register_for_accessibility(
            high_contrast_check,
            role="checkbox",
            description="高对比度模式复选框"
        )
        
        self.register_for_accessibility(
            keyboard_nav_check,
            role="checkbox",
            description="增强键盘导航复选框"
        )
        
        self.register_for_accessibility(
            text_zoom_scale,
            role="slider",
            description="文本大小滑块，从80%到200%"
        )
        
        self.register_for_accessibility(
            focus_mode_check,
            role="checkbox",
            description="专注模式复选框"
        )
        
        self.register_for_accessibility(
            reduced_motion_check,
            role="checkbox",
            description="减少动画复选框"
        )
        
        self.register_for_accessibility(
            auto_read_check,
            role="checkbox",
            description="鼠标悬停朗读复选框"
        )
        
        self.register_for_accessibility(
            cursor_size_scale,
            role="slider",
            description="光标大小滑块，从100%到300%"
        )
        
        self.register_for_accessibility(
            hover_time_scale,
            role="slider",
            description="悬停触发时间滑块，从0.2秒到2秒"
        )
        
        self.register_for_accessibility(
            reset_button,
            role="button",
            description="恢复默认设置按钮"
        )
        
        return frame


# 简单的文本到语音引擎示例
class SimpleTTS:
    """简单的文本到语音引擎示例"""
    
    def __init__(self):
        """初始化TTS引擎"""
        self.tts_available = False
        
        # 尝试初始化不同的TTS后端
        try:
            # 尝试pyttsx3
            import pyttsx3
            self.engine = pyttsx3.init()
            self.backend = "pyttsx3"
            self.tts_available = True
            print("使用 pyttsx3 TTS 后端")
        except ImportError:
            try:
                # 尝试win32com (Windows)
                import win32com.client
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                self.backend = "win32com"
                self.tts_available = True
                print("使用 Windows SAPI TTS 后端")
            except ImportError:
                try:
                    # 尝试使用 GTK (Linux)
                    from gi.repository import Gtk
                    os.system('echo "TTS test" | festival --tts')
                    self.backend = "festival"
                    self.tts_available = True
                    print("使用 Festival TTS 后端")
                except:
                    print("没有可用的TTS后端")
    
    def speak(self, text):
        """
        朗读文本
        
        Args:
            text: 要朗读的文本
            
        Returns:
            bool: 是否成功朗读
        """
        if not self.tts_available:
            return False
        
        try:
            if self.backend == "pyttsx3":
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            elif self.backend == "win32com":
                self.engine.Speak(text)
                return True
            elif self.backend == "festival":
                # 使用festival命令行工具
                text = text.replace('"', r'\"')  # 转义引号
                os.system(f'echo "{text}" | festival --tts')
                return True
        except Exception as e:
            print(f"TTS朗读时出错: {e}")
            return False


# 示例用法
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk
    
    # 创建测试 UI
    root = tk.Tk()
    root.title("无障碍性支持演示")
    root.geometry("800x600")
    root.configure(background="#f5f5f7")
    
    # 创建无障碍性管理器
    a11y_manager = AccessibilityManager()
    
    # 注册TTS引擎
    tts = SimpleTTS()
    if tts.tts_available:
        a11y_manager.register_tts_engine(tts)
    
    # 设置键盘导航
    a11y_manager.setup_keyboard_navigation(root)
    
    # 主框架
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text="无障碍性支持演示", font=("Helvetica", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # 注册标题以支持无障碍性
    a11y_manager.register_for_accessibility(
        title_label,
        role="heading",
        description="无障碍性支持演示"
    )
    
    # 创建示例表单
    form_frame = ttk.LabelFrame(main_frame, text="示例表单")
    form_frame.pack(fill=tk.X, pady=10)
    
    # 用户名
    username_frame = ttk.Frame(form_frame)
    username_frame.pack(fill=tk.X, padx=10, pady=5)
    
    username_label = ttk.Label(username_frame, text="用户名:")
    username_label.pack(side=tk.LEFT)
    
    username_entry = ttk.Entry(username_frame)
    username_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # 密码
    password_frame = ttk.Frame(form_frame)
    password_frame.pack(fill=tk.X, padx=10, pady=5)
    
    password_label = ttk.Label(password_frame, text="密码:")
    password_label.pack(side=tk.LEFT)
    
    password_entry = ttk.Entry(password_frame, show="*")
    password_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # 记住我
    remember_frame = ttk.Frame(form_frame)
    remember_frame.pack(fill=tk.X, padx=10, pady=5)
    
    remember_var = tk.BooleanVar()
    remember_check = ttk.Checkbutton(remember_frame, text="记住我", variable=remember_var)
    remember_check.pack(side=tk.LEFT)
    
    # 提交按钮
    submit_frame = ttk.Frame(form_frame)
    submit_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def on_submit():
        # 创建提示
        if a11y_manager.get_setting('screen_reader_support'):
            a11y_manager.announce("表单已提交")
        
        # 显示操作反馈
        feedback_label.configure(text="表单已提交，感谢您！")
    
    submit_button = ttk.Button(submit_frame, text="提交", command=on_submit)
    submit_button.pack(side=tk.RIGHT)
    
    # 操作反馈
    feedback_frame = ttk.Frame(main_frame)
    feedback_frame.pack(fill=tk.X, pady=10)
    
    feedback_label = ttk.Label(feedback_frame, text="")
    feedback_label.pack()
    
    # 注册表单部件以支持无障碍性
    a11y_manager.register_for_accessibility(
        username_label,
        role="label",
        description="用户名标签"
    )
    
    a11y_manager.register_for_accessibility(
        username_entry,
        role="textbox",
        description="用户名输入框"
    )
    
    a11y_manager.register_for_accessibility(
        password_label,
        role="label",
        description="密码标签"
    )
    
    a11y_manager.register_for_accessibility(
        password_entry,
        role="textbox",
        description="密码输入框，输入时字符会被星号代替"
    )
    
    a11y_manager.register_for_accessibility(
        remember_check,
        role="checkbox",
        description="记住我复选框"
    )
    
    a11y_manager.register_for_accessibility(
        submit_button,
        role="button",
        description="提交按钮，点击提交表单"
    )
    
    a11y_manager.register_for_accessibility(
        feedback_label,
        role="status",
        description="操作反馈信息"
    )
    
    # 添加无障碍性设置面板
    settings_frame = a11y_manager.create_accessibility_settings_panel(main_frame)
    settings_frame.pack(fill=tk.X, pady=20)
    
    # 状态栏
    status_frame = ttk.Frame(root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    status_label = ttk.Label(
        status_frame,
        text="Tab 键用于导航，Enter 键用于激活按钮，空格键用于切换复选框"
    )
    status_label.pack(side=tk.LEFT, padx=10, pady=5)
    
    # 启动主循环
    root.mainloop()