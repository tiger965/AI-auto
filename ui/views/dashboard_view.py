"""
仪表盘视图模块
提供系统主要功能的概览和快速访问
"""

import tkinter as tk
from tkinter import ttk
import datetime
from . import BaseView


class DashboardView(BaseView):
    """仪表盘视图，显示系统概览和关键指标"""

    def __init__(self, parent, controller):
        self.widgets = {}  # 存储所有创建的小部件，便于主题应用
        super().__init__(parent, controller)

    def _create_widgets(self):
        """创建仪表盘所有组件"""
        theme = self.theme_manager.get_current_theme()

        # 创建头部欢迎区域
        self.widgets["header_frame"] = tk.Frame(self, bg=theme["background"])
        self.widgets["welcome_label"] = tk.Label(
            self.widgets["header_frame"],
            text=f"欢迎回来，{self.controller.current_user.username}",
            font=("Arial", 18, "bold"),
            bg=theme["background"],
            fg=theme["text_primary"],
        )

        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
        self.widgets["time_label"] = tk.Label(
            self.widgets["header_frame"],
            text=current_time,
            font=("Arial", 10),
            bg=theme["background"],
            fg=theme["text_secondary"],
        )

        # 创建快速统计区域
        self.widgets["stats_frame"] = tk.Frame(self, bg=theme["background"])

        # 创建各个统计卡片
        self._create_stat_card("今日交易", "15", "↑5%", theme, is_positive=True)
        self._create_stat_card("总资产", "¥125,750", "↑2.3%",
                               theme, is_positive=True)
        self._create_stat_card("本月收益", "¥3,240", "↓0.8%",
                               theme, is_positive=False)
        self._create_stat_card("系统通知", "3", "新消息", theme)

        # 创建快速操作区域
        self.widgets["actions_frame"] = tk.Frame(self, bg=theme["background"])
        self.widgets["actions_label"] = tk.Label(
            self.widgets["actions_frame"],
            text="快速操作",
            font=("Arial", 14, "bold"),
            bg=theme["background"],
            fg=theme["text_primary"],
        )

        actions = [
            {"text": "新建交易", "icon": "🔄", "command": self._new_trade},
            {"text": "查看分析", "icon": "📊", "command": self._view_analytics},
            {"text": "账户设置", "icon": "⚙️", "command": self._open_settings},
            {"text": "获取帮助", "icon": "❓", "command": self._open_help},
        ]

        self.widgets["action_buttons"] = []
        for i, action in enumerate(actions):
            btn = tk.Button(
                self.widgets["actions_frame"],
                text=f"{action['icon']} {action['text']}",
                font=("Arial", 12),
                bg=theme["button_background"],
                fg=theme["button_text"],
                relief=tk.FLAT,
                padx=15,
                pady=8,
                cursor="hand2",
                command=action["command"],
            )
            self.widgets["action_buttons"].append(btn)

        # 创建最近活动区域
        self.widgets["activity_frame"] = tk.Frame(self, bg=theme["background"])
        self.widgets["activity_label"] = tk.Label(
            self.widgets["activity_frame"],
            text="最近活动",
            font=("Arial", 14, "bold"),
            bg=theme["background"],
            fg=theme["text_primary"],
        )

        # 创建活动列表
        self.widgets["activity_list"] = tk.Frame(
            self.widgets["activity_frame"], bg=theme["card_background"]
        )

        activities = [
            {"time": "今天 10:23", "text": "完成交易 #1082", "type": "交易"},
            {"time": "今天 09:15", "text": "更新个人资料", "type": "账户"},
            {"time": "昨天 16:42", "text": "查看行情分析", "type": "分析"},
            {"time": "昨天 12:30", "text": "完成交易 #1081", "type": "交易"},
        ]

        self.widgets["activity_items"] = []
        for activity in activities:
            item_frame = tk.Frame(
                self.widgets["activity_list"],
                bg=theme["card_background"],
                padx=10,
                pady=8,
            )

            activity_type = tk.Label(
                item_frame,
                text=activity["type"],
                font=("Arial", 9),
                bg=theme["tag_background"],
                fg=theme["tag_text"],
                padx=5,
                pady=2,
            )

            activity_text = tk.Label(
                item_frame,
                text=activity["text"],
                font=("Arial", 11),
                bg=theme["card_background"],
                fg=theme["text_primary"],
                anchor="w",
            )

            activity_time = tk.Label(
                item_frame,
                text=activity["time"],
                font=("Arial", 9),
                bg=theme["card_background"],
                fg=theme["text_secondary"],
            )

            activity_type.pack(side=tk.LEFT, padx=(0, 10))
            activity_text.pack(side=tk.LEFT, fill="x", expand=True)
            activity_time.pack(side=tk.RIGHT)

            self.widgets["activity_items"].append(
                (item_frame, activity_type, activity_text, activity_time)
            )

    def _layout_widgets(self):
        """布局所有控件"""
        # 布局头部区域
        self.widgets["header_frame"].pack(fill="x", padx=20, pady=(20, 10))
        self.widgets["welcome_label"].pack(side=tk.LEFT)
        self.widgets["time_label"].pack(side=tk.RIGHT)

        # 布局统计区域
        self.widgets["stats_frame"].pack(fill="x", padx=20, pady=10)
        # 统计卡片在创建时已经布局

        # 布局快速操作区域
        self.widgets["actions_frame"].pack(fill="x", padx=20, pady=10)
        self.widgets["actions_label"].pack(anchor="w", pady=(0, 10))

        for i, btn in enumerate(self.widgets["action_buttons"]):
            btn.pack(side=tk.LEFT, padx=(0 if i == 0 else 10, 0))

        # 布局最近活动区域
        self.widgets["activity_frame"].pack(
            fill="both", expand=True, padx=20, pady=10)
        self.widgets["activity_label"].pack(anchor="w", pady=(0, 10))
        self.widgets["activity_list"].pack(fill="both", expand=True, pady=5)

        for item_frame, _, _, _ in self.widgets["activity_items"]:
            item_frame.pack(fill="x", pady=2)

    def _apply_theme(self):
        """应用当前主题到所有控件"""
        theme = self.theme_manager.get_current_theme()
        self.configure(bg=theme["background"])

        # 更新所有控件的颜色
        for widget_name, widget in self.widgets.items():
            if isinstance(widget, tk.Widget):
                if isinstance(widget, tk.Frame):
                    widget.configure(bg=theme["background"])
                elif isinstance(widget, tk.Label):
                    widget.configure(
                        bg=theme["background"], fg=theme["text_primary"])
                elif isinstance(widget, tk.Button):
                    widget.configure(
                        bg=theme["button_background"], fg=theme["button_text"]
                    )

        # 更新活动项的颜色
        for item_frame, type_label, text_label, time_label in self.widgets[
            "activity_items"
        ]:
            item_frame.configure(bg=theme["card_background"])
            type_label.configure(
                bg=theme["tag_background"], fg=theme["tag_text"])
            text_label.configure(
                bg=theme["card_background"], fg=theme["text_primary"])
            time_label.configure(
                bg=theme["card_background"], fg=theme["text_secondary"]
            )

    def _create_stat_card(self, title, value, change, theme, is_positive=None):
        """创建统计卡片"""
        card = tk.Frame(
            self.widgets["stats_frame"],
            bg=theme["card_background"],
            padx=15,
            pady=12,
        )

        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", 12),
            bg=theme["card_background"],
            fg=theme["text_secondary"],
        )

        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 18, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        change_color = (
            theme["success_text"]
            if is_positive
            else (
                theme["error_text"] if is_positive is False else theme["text_secondary"]
            )
        )

        change_label = tk.Label(
            card,
            text=change,
            font=("Arial", 10),
            bg=theme["card_background"],
            fg=change_color,
        )

        title_label.pack(anchor="w")
        value_label.pack(anchor="w", pady=5)
        change_label.pack(anchor="w")

        # 将卡片添加到widgets字典中
        self.widgets[f"card_{title}"] = card
        self.widgets[f"title_{title}"] = title_label
        self.widgets[f"value_{title}"] = value_label
        self.widgets[f"change_{title}"] = change_label

        # 将卡片放入统计框架中
        card.pack(side=tk.LEFT, padx=(0, 15), fill="y")

        # 添加悬停效果
        card.bind("<Enter>", lambda e: self._on_card_hover(card, True))
        card.bind("<Leave>", lambda e: self._on_card_hover(card, False))

        return card

    def _on_card_hover(self, card, is_hover):
        """卡片悬停效果"""
        theme = self.theme_manager.get_current_theme()
        if is_hover:
            card.configure(bg=theme["card_hover_background"])
            for widget in card.winfo_children():
                widget.configure(bg=theme["card_hover_background"])
            self.sound_manager.play("hover")
        else:
            card.configure(bg=theme["card_background"])
            for widget in card.winfo_children():
                widget.configure(bg=theme["card_background"])

    # 快速操作按钮的回调函数
    def _new_trade(self):
        """打开交易视图"""
        self.sound_manager.play("button_click")
        self.controller.show_frame("TradingView")

    def _view_analytics(self):
        """打开分析视图"""
        self.sound_manager.play("button_click")
        self.controller.show_frame("AnalyticsView")

    def _open_settings(self):
        """打开设置视图"""
        self.sound_manager.play("button_click")
        self.controller.show_frame("SettingsView")

    def _open_help(self):
        """打开帮助视图"""
        self.sound_manager.play("button_click")
        self.controller.show_frame("HelpView")