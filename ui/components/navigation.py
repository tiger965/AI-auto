# navigation.py
import tkinter as tk
from tkinter import ttk
import time
import threading


class SidebarNavigation:
    """
    侧边栏导航组件，支持流畅的动画效果和主题切换

    提供优雅的导航体验，包括滑动动画和反馈效果
    """

    def __init__(self, parent, items=None, width=250, theme="light"):
        """
        初始化侧边栏导航

        Args:
            parent: 父级窗口部件
            items: 导航项列表，每项为 {"id": "item_id", "label": "显示名称", "icon": "图标unicode"}
            width: 侧边栏宽度
            theme: 主题 ("light" 或 "dark")
        """
        self.parent = parent
        self.items = items or []
        self.width = width
        self.current_theme = theme
        self.selected_item = None
        self.on_select_callbacks = []

        # 主题配置
        self.themes = {
            "light": {
                "bg": "#f5f5f7",
                "item_bg": "#ffffff",
                "item_bg_hover": "#f0f0f5",
                "item_bg_selected": "#e8e8ff",
                "item_fg": "#333333",
                "item_fg_selected": "#3355ff",
                "border": "#e0e0e0",
                "icon_color": "#666666",
                "icon_color_selected": "#3355ff",
            },
            "dark": {
                "bg": "#1e1e2d",
                "item_bg": "#252536",
                "item_bg_hover": "#2a2a3d",
                "item_bg_selected": "#2c2c45",
                "item_fg": "#e0e0e0",
                "item_fg_selected": "#7f9eff",
                "border": "#2c2c45",
                "icon_color": "#a0a0a0",
                "icon_color_selected": "#7f9eff",
            },
        }

        # 创建主框架
        self.frame = ttk.Frame(parent, width=width)
        self.frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        # 创建画布和滚动条
        self.canvas = tk.Canvas(
            self.frame, width=width, highlightthickness=0, bg=self.themes[theme]["bg"]
        )
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.canvas.yview
        )

        # 配置画布
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建内容框架
        self.content_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.content_frame, anchor=tk.NW, width=width
        )

        # 绑定事件
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 应用主题
        self._apply_theme(theme)

        # 渲染导航项
        self._render_items()

    def _apply_theme(self, theme):
        """应用主题样式"""
        self.current_theme = theme
        theme_config = self.themes[theme]

        # 应用到画布
        self.canvas.configure(bg=theme_config["bg"])

        # 应用到内容框架
        self.content_frame.configure(style=f"Sidebar.TFrame")

        # 创建自定义样式
        style = ttk.Style()

        # 侧边栏框架样式
        style.configure("Sidebar.TFrame", background=theme_config["bg"])

        # 侧边栏项目样式
        style.configure("SidebarItem.TFrame",
                        background=theme_config["item_bg"])

        # 侧边栏项目选中样式
        style.configure(
            "SidebarItemSelected.TFrame", background=theme_config["item_bg_selected"]
        )

        # 重新渲染项目以应用新主题
        self._render_items()

    def _render_items(self):
        """渲染所有导航项"""
        # 清除现有项目
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 逐个创建导航项
        for i, item in enumerate(self.items):
            self._create_nav_item(item, i)

    def _create_nav_item(self, item, index):
        """创建单个导航项"""
        item_id = item.get("id", f"item_{index}")
        label = item.get("label", f"Item {index}")
        icon = item.get("icon", "")

        # 确定样式
        theme_config = self.themes[self.current_theme]
        is_selected = self.selected_item == item_id

        frame_style = (
            "SidebarItemSelected.TFrame" if is_selected else "SidebarItem.TFrame"
        )
        fg_color = (
            theme_config["item_fg_selected"] if is_selected else theme_config["item_fg"]
        )
        icon_color = (
            theme_config["icon_color_selected"]
            if is_selected
            else theme_config["icon_color"]
        )

        # 创建项目框架
        item_frame = ttk.Frame(
            self.content_frame, style=frame_style, height=50)
        item_frame.pack(fill=tk.X, padx=5, pady=3)
        item_frame.pack_propagate(False)

        # 创建左侧指示器
        if is_selected:
            indicator = tk.Frame(
                item_frame, width=4, background=theme_config["item_fg_selected"]
            )
            indicator.pack(side=tk.LEFT, fill=tk.Y)
        else:
            # 占位框架，保持对齐
            spacer = tk.Frame(item_frame, width=4,
                              background=theme_config["item_bg"])
            spacer.pack(side=tk.LEFT, fill=tk.Y)

        # 创建图标标签
        if icon:
            icon_label = tk.Label(
                item_frame,
                text=icon,
                font=("Segoe UI Symbol", 16),
                foreground=icon_color,
                background=(
                    theme_config["item_bg_selected"]
                    if is_selected
                    else theme_config["item_bg"]
                ),
            )
            icon_label.pack(side=tk.LEFT, padx=(15, 10), pady=12)

        # 创建文本标签
        text_label = tk.Label(
            item_frame,
            text=label,
            font=("Helvetica", 11),
            foreground=fg_color,
            background=(
                theme_config["item_bg_selected"]
                if is_selected
                else theme_config["item_bg"]
            ),
            anchor=tk.W,
        )
        text_label.pack(side=tk.LEFT, fill=tk.X,
                        expand=True, padx=(5, 15), pady=12)

        # 存储项目ID
        item_frame._item_id = item_id

        # 绑定事件
        item_frame.bind("<Button-1>", lambda e,
                        id=item_id: self._on_item_click(id))
        text_label.bind("<Button-1>", lambda e,
                        id=item_id: self._on_item_click(id))
        if icon:
            icon_label.bind("<Button-1>", lambda e,
                            id=item_id: self._on_item_click(id))

        # 绑定鼠标悬停事件
        for widget in [item_frame, text_label]:
            widget.bind("<Enter>", lambda e,
                        f=item_frame: self._on_item_enter(f))
            widget.bind("<Leave>", lambda e,
                        f=item_frame: self._on_item_leave(f))

        if icon:
            icon_label.bind("<Enter>", lambda e,
                            f=item_frame: self._on_item_enter(f))
            icon_label.bind("<Leave>", lambda e,
                            f=item_frame: self._on_item_leave(f))

    def _on_item_enter(self, item_frame):
        """处理鼠标进入事件"""
        # 如果已经选中，不改变样式
        if (
            hasattr(item_frame, "_item_id")
            and item_frame._item_id == self.selected_item
        ):
            return

        # 应用悬停样式
        theme_config = self.themes[self.current_theme]

        for widget in item_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(background=theme_config["item_bg_hover"])

        # 特殊处理第一个子部件（左侧指示器或占位符）
        if item_frame.winfo_children():
            item_frame.winfo_children()[0].configure(
                background=theme_config["item_bg_hover"]
            )

    def _on_item_leave(self, item_frame):
        """处理鼠标离开事件"""
        # 如果已经选中，保持选中样式
        if (
            hasattr(item_frame, "_item_id")
            and item_frame._item_id == self.selected_item
        ):
            theme_config = self.themes[self.current_theme]

            for widget in item_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(
                        background=theme_config["item_bg_selected"])

            # 特殊处理第一个子部件（左侧指示器）
            if item_frame.winfo_children():
                first_child = item_frame.winfo_children()[0]
                if isinstance(first_child, tk.Frame) and first_child.winfo_width() == 4:
                    # 这是指示器
                    first_child.configure(
                        background=theme_config["item_fg_selected"])
            return

        # 恢复正常样式
        theme_config = self.themes[self.current_theme]

        for widget in item_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(background=theme_config["item_bg"])

        # 特殊处理第一个子部件（占位符）
        if item_frame.winfo_children():
            item_frame.winfo_children()[0].configure(
                background=theme_config["item_bg"])

    def _on_item_click(self, item_id):
        """处理项目点击事件"""
        # 如果点击当前选中项，不执行任何操作
        if item_id == self.selected_item:
            return

        # 更新选中项
        old_selected = self.selected_item
        self.selected_item = item_id

        # 重新渲染以更新样式
        self._render_items()

        # 执行动画
        self._animate_selection_change(old_selected, item_id)

        # 调用回调函数
        for callback in self.on_select_callbacks:
            callback(item_id)

    def _animate_selection_change(self, old_id, new_id):
        """执行选择变化动画"""
        # 查找旧项目和新项目的 Y 坐标
        old_y = None
        new_y = None

        for widget in self.content_frame.winfo_children():
            if hasattr(widget, "_item_id"):
                if widget._item_id == old_id:
                    old_y = widget.winfo_y()
                elif widget._item_id == new_id:
                    new_y = widget.winfo_y()

        if old_y is not None and new_y is not None:
            # 计算需要滚动的距离
            canvas_height = self.canvas.winfo_height()

            # 如果新项目在可视区域外，滚动到它
            if new_y < 0 or new_y + 50 > canvas_height:
                # 计算目标滚动位置
                target_scroll = new_y / self.content_frame.winfo_height()

                # 当前滚动位置
                current_scroll = self.canvas.yview()[0]

                # 执行平滑滚动动画
                self._animate_scroll(current_scroll, target_scroll)

    def _animate_scroll(self, start, end):
        """平滑滚动动画"""
        steps = 15
        step_time = 0.02

        for i in range(steps + 1):
            progress = i / steps
            # 使用缓动函数使动画更自然
            t = self._ease_out_quad(progress)
            current = start + (end - start) * t

            # 设置滚动位置
            self.canvas.yview_moveto(current)
            self.canvas.update_idletasks()
            time.sleep(step_time)

    def _ease_out_quad(self, t):
        """二次缓出函数"""
        return t * (2 - t)

    def _on_frame_configure(self, event):
        """内容框架大小改变时调整画布滚动区域"""
        # 更新画布的滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """画布大小改变时调整内容框架宽度"""
        # 更新画布窗口的宽度以匹配画布
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def add_item(self, item):
        """添加新的导航项"""
        self.items.append(item)
        self._render_items()

    def remove_item(self, item_id):
        """移除导航项"""
        self.items = [item for item in self.items if item.get("id") != item_id]
        if self.selected_item == item_id:
            self.selected_item = None
        self._render_items()

    def select_item(self, item_id):
        """选择指定的导航项"""
        if item_id not in [item.get("id") for item in self.items]:
            return

        old_selected = self.selected_item
        self.selected_item = item_id
        self._render_items()
        self._animate_selection_change(old_selected, item_id)

    def on_select(self, callback):
        """注册选择事件回调函数"""
        self.on_select_callbacks.append(callback)

    def set_theme(self, theme):
        """设置主题"""
        if theme in self.themes:
            # 执行主题切换动画
            self._animate_theme_change(self.current_theme, theme)

    def _animate_theme_change(self, old_theme, new_theme):
        """执行主题切换动画"""
        # 平滑过渡背景色
        old_bg = self.themes[old_theme]["bg"]
        new_bg = self.themes[new_theme]["bg"]

        # 解析颜色为 RGB
        old_rgb = self._hex_to_rgb(old_bg)
        new_rgb = self._hex_to_rgb(new_bg)

        # 执行动画
        steps = 20
        step_time = 0.02

        for i in range(steps + 1):
            progress = i / steps
            # 使用缓动函数
            t = self._ease_in_out_quad(progress)

            # 计算当前颜色
            r = int(old_rgb[0] + (new_rgb[0] - old_rgb[0]) * t)
            g = int(old_rgb[1] + (new_rgb[1] - old_rgb[1]) * t)
            b = int(old_rgb[2] + (new_rgb[2] - old_rgb[2]) * t)

            current_color = f"#{r:02x}{g:02x}{b:02x}"

            # 应用当前颜色
            self.canvas.configure(bg=current_color)
            self.canvas.update_idletasks()
            time.sleep(step_time)

        # 应用完整的新主题
        self._apply_theme(new_theme)

    def _ease_in_out_quad(self, t):
        """二次缓入缓出函数"""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB元组"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))


class TopNavigation:
    """
    顶部导航栏组件，支持动画效果和主题切换
    """

    def __init__(self, parent, title="应用", menu_items=None, theme="light"):
        """
        初始化顶部导航栏

        Args:
            parent: 父级窗口部件
            title: 应用标题
            menu_items: 菜单项列表，例如 [{"label": "文件", "menu": [...子菜单项...]}]
            theme: 主题 ("light" 或 "dark")
        """
        self.parent = parent
        self.title = title
        self.menu_items = menu_items or []
        self.current_theme = theme

        # 主题配置
        self.themes = {
            "light": {
                "bg": "#ffffff",
                "fg": "#333333",
                "title_fg": "#222222",
                "border": "#e0e0e0",
                "highlight": "#f0f0f5",
                "action_bg": "#f5f5f7",
                "action_fg": "#3355ff",
            },
            "dark": {
                "bg": "#252536",
                "fg": "#e0e0e0",
                "title_fg": "#ffffff",
                "border": "#2c2c45",
                "highlight": "#2a2a3d",
                "action_bg": "#2c2c45",
                "action_fg": "#7f9eff",
            },
        }

        # 创建导航栏框架
        self.frame = tk.Frame(
            parent,
            height=60,
            bg=self.themes[theme]["bg"],
            bd=1,
            relief=tk.SOLID,
            borderwidth=0,
        )
        self.frame.pack(side=tk.TOP, fill=tk.X)
        self.frame.pack_propagate(False)

        # 应用标题
        self.title_label = tk.Label(
            self.frame,
            text=title,
            font=("Helvetica", 16, "bold"),
            fg=self.themes[theme]["title_fg"],
            bg=self.themes[theme]["bg"],
        )
        self.title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # 右侧操作区
        self.actions_frame = tk.Frame(self.frame, bg=self.themes[theme]["bg"])
        self.actions_frame.pack(side=tk.RIGHT, padx=20)

        # 设置默认操作按钮（可自定义）
        self._create_default_actions()

        # 创建菜单项
        self.menus = []
        for item in self.menu_items:
            self._create_menu_item(item)

        # 底部分隔线
        self.separator = tk.Frame(
            self.frame, height=1, bg=self.themes[theme]["border"])
        self.separator.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_default_actions(self):
        """创建默认操作按钮"""
        # 主题切换按钮
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"

        self.theme_button = tk.Label(
            self.actions_frame,
            text=theme_icon,
            font=("Segoe UI Symbol", 16),
            fg=self.themes[self.current_theme]["fg"],
            bg=self.themes[self.current_theme]["bg"],
            cursor="hand2",
        )
        self.theme_button.pack(side=tk.RIGHT, padx=10, pady=15)

        # 绑定事件
        self.theme_button.bind("<Button-1>", self._toggle_theme)

        # 绑定鼠标悬停效果
        self.theme_button.bind("<Enter>", self._on_action_enter)
        self.theme_button.bind("<Leave>", self._on_action_leave)

    def _create_menu_item(self, item):
        """创建菜单项"""
        label = item.get("label", "")

        menu_button = tk.Label(
            self.frame,
            text=label,
            font=("Helvetica", 11),
            fg=self.themes[self.current_theme]["fg"],
            bg=self.themes[self.current_theme]["bg"],
            cursor="hand2",
        )
        menu_button.pack(side=tk.LEFT, padx=10, pady=20)

        # 存储菜单项
        self.menus.append({"button": menu_button, "config": item})

        # 创建下拉菜单
        if "menu" in item and isinstance(item["menu"], list):
            menu = tk.Menu(
                self.parent,
                tearoff=0,
                bg=self.themes[self.current_theme]["bg"],
                fg=self.themes[self.current_theme]["fg"],
                activebackground=self.themes[self.current_theme]["highlight"],
                activeforeground=self.themes[self.current_theme]["fg"],
                bd=0,
            )

            for submenu in item["menu"]:
                if submenu == "-":
                    menu.add_separator()
                else:
                    label = submenu.get("label", "")
                    command = submenu.get("command")
                    menu.add_command(label=label, command=command)

            # 绑定事件
            menu_button.bind("<Button-1>", lambda e,
                             m=menu: self._show_menu(e, m))

        # 绑定鼠标悬停效果
        menu_button.bind("<Enter>", self._on_menu_enter)
        menu_button.bind("<Leave>", self._on_menu_leave)

    def _show_menu(self, event, menu):
        """显示下拉菜单"""
        # 获取按钮位置
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty() + event.widget.winfo_height()

        # 显示菜单
        menu.post(x, y)

    def _on_menu_enter(self, event):
        """处理菜单项鼠标进入事件"""
        event.widget.configure(fg=self.themes[self.current_theme]["action_fg"])

    def _on_menu_leave(self, event):
        """处理菜单项鼠标离开事件"""
        event.widget.configure(fg=self.themes[self.current_theme]["fg"])

    def _on_action_enter(self, event):
        """处理操作按钮鼠标进入事件"""
        event.widget.configure(fg=self.themes[self.current_theme]["action_fg"])

    def _on_action_leave(self, event):
        """处理操作按钮鼠标离开事件"""
        event.widget.configure(fg=self.themes[self.current_theme]["fg"])

    def _toggle_theme(self, event):
        """切换主题"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)

    def set_theme(self, theme):
        """设置主题"""
        if theme in self.themes and theme != self.current_theme:
            # 执行主题切换动画
            self._animate_theme_change(self.current_theme, theme)

    def _animate_theme_change(self, old_theme, new_theme):
        """执行主题切换动画"""
        # 解析颜色
        old_bg = self.themes[old_theme]["bg"]
        new_bg = self.themes[new_theme]["bg"]

        old_fg = self.themes[old_theme]["fg"]
        new_fg = self.themes[new_theme]["fg"]

        old_title_fg = self.themes[old_theme]["title_fg"]
        new_title_fg = self.themes[new_theme]["title_fg"]

        old_border = self.themes[old_theme]["border"]
        new_border = self.themes[new_theme]["border"]

        # 转换为RGB
        old_bg_rgb = self._hex_to_rgb(old_bg)
        new_bg_rgb = self._hex_to_rgb(new_bg)

        old_fg_rgb = self._hex_to_rgb(old_fg)
        new_fg_rgb = self._hex_to_rgb(new_fg)

        old_title_fg_rgb = self._hex_to_rgb(old_title_fg)
        new_title_fg_rgb = self._hex_to_rgb(new_title_fg)

        old_border_rgb = self._hex_to_rgb(old_border)
        new_border_rgb = self._hex_to_rgb(new_border)

        # 执行动画
        steps = 20
        step_time = 0.02

        for i in range(steps + 1):
            progress = i / steps
            t = self._ease_in_out_quad(progress)

            # 计算当前颜色 - 背景
            r = int(old_bg_rgb[0] + (new_bg_rgb[0] - old_bg_rgb[0]) * t)
            g = int(old_bg_rgb[1] + (new_bg_rgb[1] - old_bg_rgb[1]) * t)
            b = int(old_bg_rgb[2] + (new_bg_rgb[2] - old_bg_rgb[2]) * t)
            current_bg = f"#{r:02x}{g:02x}{b:02x}"

            # 计算当前颜色 - 前景
            r = int(old_fg_rgb[0] + (new_fg_rgb[0] - old_fg_rgb[0]) * t)
            g = int(old_fg_rgb[1] + (new_fg_rgb[1] - old_fg_rgb[1]) * t)
            b = int(old_fg_rgb[2] + (new_fg_rgb[2] - old_fg_rgb[2]) * t)
            current_fg = f"#{r:02x}{g:02x}{b:02x}"

            # 计算当前颜色 - 标题前景
            r = int(
                old_title_fg_rgb[0] +
                (new_title_fg_rgb[0] - old_title_fg_rgb[0]) * t
            )
            g = int(
                old_title_fg_rgb[1] +
                (new_title_fg_rgb[1] - old_title_fg_rgb[1]) * t
            )
            b = int(
                old_title_fg_rgb[2] +
                (new_title_fg_rgb[2] - old_title_fg_rgb[2]) * t
            )
            current_title_fg = f"#{r:02x}{g:02x}{b:02x}"

            # 计算当前颜色 - 边框
            r = int(old_border_rgb[0] +
                    (new_border_rgb[0] - old_border_rgb[0]) * t)
            g = int(old_border_rgb[1] +
                    (new_border_rgb[1] - old_border_rgb[1]) * t)
            b = int(old_border_rgb[2] +
                    (new_border_rgb[2] - old_border_rgb[2]) * t)
            current_border = f"#{r:02x}{g:02x}{b:02x}"

            # 应用颜色
            self.frame.configure(bg=current_bg)
            self.title_label.configure(bg=current_bg, fg=current_title_fg)
            self.actions_frame.configure(bg=current_bg)
            self.separator.configure(bg=current_border)

            # 应用到菜单按钮
            for menu_item in self.menus:
                menu_item["button"].configure(bg=current_bg, fg=current_fg)

            # 应用到操作按钮
            for widget in self.actions_frame.winfo_children():
                widget.configure(bg=current_bg, fg=current_fg)

            # 更新主题图标
            theme_icon = "🌙" if new_theme == "light" else "☀️"
            self.theme_button.configure(text=theme_icon)

            # 更新界面
            self.frame.update_idletasks()
            time.sleep(step_time)

        # 更新当前主题
        self.current_theme = new_theme

    def _ease_in_out_quad(self, t):
        """二次缓入缓出函数"""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB元组"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))

    def add_action(self, icon, tooltip, command):
        """添加自定义操作按钮"""
        button = tk.Label(
            self.actions_frame,
            text=icon,
            font=("Segoe UI Symbol", 16),
            fg=self.themes[self.current_theme]["fg"],
            bg=self.themes[self.current_theme]["bg"],
            cursor="hand2",
        )
        button.pack(side=tk.RIGHT, padx=10, pady=15)

        # 添加工具提示
        self._create_tooltip(button, tooltip)

        # 绑定事件
        button.bind("<Button-1>", lambda e: command())

        # 绑定鼠标悬停效果
        button.bind("<Enter>", self._on_action_enter)
        button.bind("<Leave>", self._on_action_leave)

        return button

    def _create_tooltip(self, widget, text):
        """为部件创建工具提示"""

        def enter(event):
            # 创建工具提示窗口
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25

            # 创建顶层窗口
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")

            # 创建工具提示标签
            label = tk.Label(
                self.tooltip,
                text=text,
                background=self.themes[self.current_theme]["highlight"],
                foreground=self.themes[self.current_theme]["fg"],
                relief=tk.SOLID,
                borderwidth=1,
                font=("Helvetica", 10),
            )
            label.pack(padx=5, pady=5)

            # 淡入动画
            self.tooltip.attributes("-alpha", 0.0)
            self._animate_tooltip_fade_in()

        def leave(event):
            if hasattr(self, "tooltip"):
                # 淡出动画
                self._animate_tooltip_fade_out()

        # 绑定事件
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def _animate_tooltip_fade_in(self):
        """工具提示淡入动画"""
        if not hasattr(self, "tooltip"):
            return

        steps = 10
        step_time = 0.02

        for i in range(steps + 1):
            alpha = i / steps
            self.tooltip.attributes("-alpha", alpha)
            self.tooltip.update_idletasks()
            time.sleep(step_time)

    def _animate_tooltip_fade_out(self):
        """工具提示淡出动画"""
        if not hasattr(self, "tooltip"):
            return

        steps = 10
        step_time = 0.01

        for i in range(steps + 1):
            alpha = 1.0 - (i / steps)
            self.tooltip.attributes("-alpha", alpha)
            self.tooltip.update_idletasks()
            time.sleep(step_time)

        # 销毁工具提示
        self.tooltip.destroy()
        del self.tooltip


class BreadcrumbNavigation:
    """
    面包屑导航组件，支持动画效果和主题切换
    """

    def __init__(self, parent, items=None, theme="light"):
        """
        初始化面包屑导航

        Args:
            parent: 父级窗口部件
            items: 导航路径项列表，例如 [{"id": "home", "label": "首页"}, ...]
            theme: 主题 ("light" 或 "dark")
        """
        self.parent = parent
        self.items = items or []
        self.current_theme = theme
        self.on_click_callbacks = []

        # 主题配置
        self.themes = {
            "light": {
                "bg": "#f8f8f8",
                "fg": "#333333",
                "separator": "#cccccc",
                "hover_fg": "#3355ff",
                "active_fg": "#3355ff",
            },
            "dark": {
                "bg": "#1e1e2d",
                "fg": "#e0e0e0",
                "separator": "#555555",
                "hover_fg": "#7f9eff",
                "active_fg": "#7f9eff",
            },
        }

        # 创建面包屑框架
        self.frame = tk.Frame(parent, bg=self.themes[theme]["bg"], height=40)
        self.frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # 渲染面包屑
        self._render_breadcrumbs()

    def _render_breadcrumbs(self):
        """渲染面包屑项"""
        # 清除现有项
        for widget in self.frame.winfo_children():
            widget.destroy()

        # 渲染新项
        for i, item in enumerate(self.items):
            # 创建项标签
            label = tk.Label(
                self.frame,
                text=item.get("label", ""),
                font=("Helvetica", 11),
                fg=self.themes[self.current_theme]["fg"],
                bg=self.themes[self.current_theme]["bg"],
                cursor="hand2",
            )
            label.pack(side=tk.LEFT, padx=(0, 5), pady=10)

            # 存储项ID
            label._item_id = item.get("id")

            # 如果不是最后一项，添加分隔符
            if i < len(self.items) - 1:
                separator = tk.Label(
                    self.frame,
                    text=">",
                    font=("Helvetica", 11),
                    fg=self.themes[self.current_theme]["separator"],
                    bg=self.themes[self.current_theme]["bg"],
                )
                separator.pack(side=tk.LEFT, padx=(0, 5), pady=10)
            else:
                # 最后一项使用活动颜色
                label.configure(
                    fg=self.themes[self.current_theme]["active_fg"])

            # 绑定事件
            label.bind(
                "<Button-1>", lambda e, id=item.get(
                    "id"): self._on_item_click(id)
            )

            # 绑定鼠标悬停效果
            label.bind("<Enter>", self._on_item_enter)
            label.bind("<Leave>", self._on_item_leave)

    def _on_item_enter(self, event):
        """处理鼠标进入事件"""
        # 获取项目ID
        if hasattr(event.widget, "_item_id"):
            # 如果是最后一项，不改变颜色
            if event.widget._item_id == self.items[-1].get("id"):
                return

            # 应用悬停颜色
            event.widget.configure(
                fg=self.themes[self.current_theme]["hover_fg"])

    def _on_item_leave(self, event):
        """处理鼠标离开事件"""
        # 获取项目ID
        if hasattr(event.widget, "_item_id"):
            # 如果是最后一项，保持活动颜色
            if event.widget._item_id == self.items[-1].get("id"):
                return

            # 恢复正常颜色
            event.widget.configure(fg=self.themes[self.current_theme]["fg"])

    def _on_item_click(self, item_id):
        """处理项目点击事件"""
        # 查找项目索引
        index = -1
        for i, item in enumerate(self.items):
            if item.get("id") == item_id:
                index = i
                break

        if index >= 0:
            # 移除点击项之后的所有项
            self.items = self.items[: index + 1]

            # 重新渲染
            self._render_breadcrumbs()

            # 调用回调函数
            for callback in self.on_click_callbacks:
                callback(item_id)

    def set_items(self, items):
        """设置新的面包屑项列表"""
        # 存储旧项以用于动画
        old_items = self.items

        # 更新项
        self.items = items

        # 如果是添加新项，使用动画
        if len(items) > len(old_items) and len(old_items) > 0:
            if items[:-1] == old_items:
                # 添加了一个新项
                self._animate_add_item(items[-1])
                return

        # 否则直接渲染
        self._render_breadcrumbs()

    def _animate_add_item(self, new_item):
        """动画添加新项"""
        # 先渲染不包含新项的面包屑
        self._render_breadcrumbs()

        # 添加分隔符
        separator = tk.Label(
            self.frame,
            text=">",
            font=("Helvetica", 11),
            fg=self.themes[self.current_theme]["separator"],
            bg=self.themes[self.current_theme]["bg"],
        )
        separator.pack(side=tk.LEFT, padx=(0, 5), pady=10)

        # 创建新项标签，初始状态为透明
        label = tk.Label(
            self.frame,
            text=new_item.get("label", ""),
            font=("Helvetica", 11),
            fg=self.themes[self.current_theme]["active_fg"],
            bg=self.themes[self.current_theme]["bg"],
            cursor="hand2",
        )

        # 存储项ID
        label._item_id = new_item.get("id")

        # 开始淡入动画
        label.pack(side=tk.LEFT, padx=(0, 5), pady=10)
        label.update_idletasks()

        # 计算初始和最终位置
        width = label.winfo_width()
        x = label.winfo_x()
        final_x = x
        initial_x = x + width

        # 将标签移到初始位置
        label.place(x=initial_x, y=label.winfo_y())
        label.pack_forget()

        # 设置透明度
        alpha = 0.0

        # 执行平滑淡入动画
        steps = 15
        step_time = 0.02

        for i in range(steps + 1):
            progress = i / steps
            t = self._ease_out_quad(progress)

            # 计算当前位置和透明度
            current_x = initial_x - (initial_x - final_x) * t
            current_alpha = t

            # 应用位置
            label.place(x=current_x, y=label.winfo_y())

            # 更新界面
            label.update_idletasks()
            time.sleep(step_time)

        # 使用pack重新管理布局
        label.place_forget()
        label.pack(side=tk.LEFT, padx=(0, 5), pady=10)

        # 绑定事件
        label.bind(
            "<Button-1>", lambda e, id=new_item.get(
                "id"): self._on_item_click(id)
        )

        # 绑定鼠标悬停效果
        label.bind("<Enter>", self._on_item_enter)
        label.bind("<Leave>", self._on_item_leave)

    def _ease_out_quad(self, t):
        """二次缓出函数"""
        return t * (2 - t)

    def add_item(self, item):
        """添加单个面包屑项"""
        self.items.append(item)
        self._animate_add_item(item)

    def on_click(self, callback):
        """注册点击事件回调函数"""
        self.on_click_callbacks.append(callback)

    def set_theme(self, theme):
        """设置主题"""
        if theme in self.themes:
            self.current_theme = theme

            # 应用主题
            self.frame.configure(bg=self.themes[theme]["bg"])

            # 更新所有项
            self._render_breadcrumbs()


# 示例用法
if __name__ == "__main__":
    root = tk.Tk()
    root.title("导航组件演示")
    root.geometry("1000x600")

    # 创建顶部导航
    menu_items = [
        {
            "label": "文件",
            "menu": [
                {"label": "新建", "command": lambda: print("新建")},
                {"label": "打开", "command": lambda: print("打开")},
                "-",
                {"label": "保存", "command": lambda: print("保存")},
                {"label": "另存为", "command": lambda: print("另存为")},
            ],
        },
        {
            "label": "编辑",
            "menu": [
                {"label": "撤销", "command": lambda: print("撤销")},
                {"label": "重做", "command": lambda: print("重做")},
                "-",
                {"label": "剪切", "command": lambda: print("剪切")},
                {"label": "复制", "command": lambda: print("复制")},
                {"label": "粘贴", "command": lambda: print("粘贴")},
            ],
        },
        {
            "label": "视图",
            "menu": [
                {"label": "缩放", "command": lambda: print("缩放")},
                {"label": "全屏", "command": lambda: print("全屏")},
            ],
        },
    ]

    top_nav = TopNavigation(root, "AI智能助手", menu_items)

    # 添加自定义操作按钮
    top_nav.add_action("📊", "查看统计", lambda: print("查看统计"))
    top_nav.add_action("⚙️", "设置", lambda: print("设置"))

    # 创建内容框架
    content_frame = tk.Frame(root)
    content_frame.pack(fill=tk.BOTH, expand=True)

    # 创建侧边栏导航
    sidebar_items = [
        {"id": "dashboard", "label": "仪表盘", "icon": "📊"},
        {"id": "projects", "label": "项目管理", "icon": "📁"},
        {"id": "analytics", "label": "数据分析", "icon": "📈"},
        {"id": "automation", "label": "自动化", "icon": "⚙️"},
        {"id": "settings", "label": "设置", "icon": "🔧"},
    ]

    sidebar = SidebarNavigation(content_frame, sidebar_items)

    # 创建面包屑导航
    breadcrumb_items = [
        {"id": "home", "label": "首页"},
        {"id": "projects", "label": "项目管理"},
        {"id": "project1", "label": "AI助手项目"},
    ]

    breadcrumb = BreadcrumbNavigation(content_frame, breadcrumb_items)

    # 创建主内容区域
    main_content = tk.Frame(content_frame, bg="#f5f5f7")
    main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # 添加一些内容
    header = tk.Label(
        main_content, text="导航组件演示", font=("Helvetica", 18, "bold"), bg="#f5f5f7"
    )
    header.pack(pady=20)

    description = tk.Label(
        main_content,
        text="这个演示展示了顶部导航栏、侧边栏导航和面包屑导航组件。\n尝试点击导航项和菜单，以及悬停在各个元素上查看效果。",
        font=("Helvetica", 12),
        bg="#f5f5f7",
        justify=tk.LEFT,
    )
    description.pack(pady=10)

    # 注册侧边栏点击事件
    def on_sidebar_select(item_id):
        print(f"选择了侧边栏项: {item_id}")
        # 更新面包屑
        if item_id == "dashboard":
            breadcrumb.set_items(
                [
                    {"id": "home", "label": "首页"},
                    {"id": "dashboard", "label": "仪表盘"},
                ]
            )
        elif item_id == "projects":
            breadcrumb.set_items(
                [
                    {"id": "home", "label": "首页"},
                    {"id": "projects", "label": "项目管理"},
                ]
            )
        elif item_id == "analytics":
            breadcrumb.set_items(
                [
                    {"id": "home", "label": "首页"},
                    {"id": "analytics", "label": "数据分析"},
                ]
            )
        elif item_id == "automation":
            breadcrumb.set_items(
                [
                    {"id": "home", "label": "首页"},
                    {"id": "automation", "label": "自动化"},
                ]
            )
        elif item_id == "settings":
            breadcrumb.set_items(
                [{"id": "home", "label": "首页"}, {"id": "settings", "label": "设置"}]
            )

    sidebar.on_select(on_sidebar_select)

    # 注册面包屑点击事件
    def on_breadcrumb_click(item_id):
        print(f"点击了面包屑项: {item_id}")

        # 如果点击首页，更新面包屑
        if item_id == "home":
            breadcrumb.set_items([{"id": "home", "label": "首页"}])
            sidebar.select_item("dashboard")

    breadcrumb.on_click(on_breadcrumb_click)

    # 主题切换按钮
    def toggle_theme():
        # 获取当前主题
        current_theme = "dark" if top_nav.current_theme == "light" else "light"

        # 应用到所有导航组件
        top_nav.set_theme(current_theme)
        sidebar.set_theme(current_theme)
        breadcrumb.set_theme(current_theme)

        # 更新主内容区域背景
        if current_theme == "light":
            main_content.configure(bg="#f5f5f7")
            header.configure(bg="#f5f5f7", fg="#333333")
            description.configure(bg="#f5f5f7", fg="#333333")
        else:
            main_content.configure(bg="#1e1e2d")
            header.configure(bg="#1e1e2d", fg="#e0e0e0")
            description.configure(bg="#1e1e2d", fg="#e0e0e0")

    theme_button = tk.Button(main_content, text="切换主题", command=toggle_theme)
    theme_button.pack(pady=20)

    root.mainloop()