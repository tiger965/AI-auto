"""
交易视图模块
提供交易功能和市场信息
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from . import BaseView


class TradingView(BaseView):
    """交易视图，提供交易功能界面"""

    def __init__(self, parent, controller):
        self.widgets = {}  # 存储所有创建的小部件，便于主题应用
        self.selected_asset = None
        super().__init__(parent, controller)

    def _create_widgets(self):
        """创建交易视图所有组件"""
        theme = self.theme_manager.get_current_theme()

        # 创建头部区域
        self.widgets["header_frame"] = tk.Frame(self, bg=theme["background"])
        self.widgets["title_label"] = tk.Label(
            self.widgets["header_frame"],
            text="交易中心",
            font=("Arial", 18, "bold"),
            bg=theme["background"],
            fg=theme["text_primary"],
        )

        # 创建市场时间和状态信息
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.widgets["market_info"] = tk.Label(
            self.widgets["header_frame"],
            text=f"市场状态: 开放 | 更新时间: {current_time}",
            font=("Arial", 10),
            bg=theme["background"],
            fg=theme["text_secondary"],
        )

        # 创建主内容区，分为左右两栏
        self.widgets["content_frame"] = tk.Frame(self, bg=theme["background"])

        # 左侧 - 市场列表区域
        self.widgets["market_frame"] = tk.Frame(
            self.widgets["content_frame"],
            bg=theme["card_background"],
            padx=15,
            pady=15,
        )

        self.widgets["market_label"] = tk.Label(
            self.widgets["market_frame"],
            text="市场列表",
            font=("Arial", 14, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 创建搜索框
        self.widgets["search_frame"] = tk.Frame(
            self.widgets["market_frame"], bg=theme["card_background"]
        )

        self.widgets["search_entry"] = tk.Entry(
            self.widgets["search_frame"],
            font=("Arial", 12),
            bg=theme["input_background"],
            fg=theme["text_primary"],
            insertbackground=theme["text_primary"],  # 光标颜色
            relief=tk.FLAT,
            width=20,
        )

        self.widgets["search_button"] = tk.Button(
            self.widgets["search_frame"],
            text="🔍",
            font=("Arial", 12),
            bg=theme["button_background"],
            fg=theme["button_text"],
            relief=tk.FLAT,
            padx=10,
            command=self._search_market,
        )

        # 创建资产列表
        self.widgets["asset_list_frame"] = tk.Frame(
            self.widgets["market_frame"], bg=theme["card_background"]
        )

        # 创建列表标题
        self.widgets["list_header"] = tk.Frame(
            self.widgets["asset_list_frame"], bg=theme["card_background"]
        )

        headers = [("资产", 0.4), ("价格", 0.2), ("变动", 0.2), ("操作", 0.2)]

        for text, width in headers:
            header_label = tk.Label(
                self.widgets["list_header"],
                text=text,
                font=("Arial", 12, "bold"),
                bg=theme["card_background"],
                fg=theme["text_primary"],
            )
            header_label.pack(side=tk.LEFT, fill="x", expand=True, anchor="w")
            self.widgets[f"header_{text}"] = header_label

        # 创建资产列表（示例数据）
        assets = [
            {
                "name": "比特币 (BTC)",
                "price": "¥282,450",
                "change": "↑2.1%",
                "is_positive": True,
            },
            {
                "name": "以太坊 (ETH)",
                "price": "¥15,890",
                "change": "↑0.5%",
                "is_positive": True,
            },
            {
                "name": "莱特币 (LTC)",
                "price": "¥950",
                "change": "↓1.2%",
                "is_positive": False,
            },
            {
                "name": "瑞波币 (XRP)",
                "price": "¥3.21",
                "change": "↑0.8%",
                "is_positive": True,
            },
            {
                "name": "卡尔达诺 (ADA)",
                "price": "¥2.85",
                "change": "↓0.3%",
                "is_positive": False,
            },
        ]

        self.widgets["asset_items"] = []
        for asset in assets:
            self._create_asset_item(asset, theme)

        # 右侧 - 交易操作区域
        self.widgets["trade_frame"] = tk.Frame(
            self.widgets["content_frame"], bg=theme["card_background"], padx=15, pady=15
        )

        self.widgets["trade_label"] = tk.Label(
            self.widgets["trade_frame"],
            text="交易操作",
            font=("Arial", 14, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 选择的资产信息
        self.widgets["selected_asset_frame"] = tk.Frame(
            self.widgets["trade_frame"], bg=theme["card_background"]
        )

        self.widgets["selected_asset_label"] = tk.Label(
            self.widgets["selected_asset_frame"],
            text="请先选择资产",
            font=("Arial", 16, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        self.widgets["selected_asset_price"] = tk.Label(
            self.widgets["selected_asset_frame"],
            text="",
            font=("Arial", 14),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 交易类型选择
        self.widgets["trade_type_frame"] = tk.Frame(
            self.widgets["trade_frame"], bg=theme["card_background"]
        )

        self.widgets["buy_button"] = tk.Button(
            self.widgets["trade_type_frame"],
            text="买入",
            font=("Arial", 12, "bold"),
            bg=theme["success_background"],
            fg=theme["success_text"],
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=lambda: self._set_trade_type("buy"),
        )

        self.widgets["sell_button"] = tk.Button(
            self.widgets["trade_type_frame"],
            text="卖出",
            font=("Arial", 12, "bold"),
            bg=theme["button_background"],
            fg=theme["button_text"],
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=lambda: self._set_trade_type("sell"),
        )

        # 创建数量和金额输入区域
        self.widgets["input_frame"] = tk.Frame(
            self.widgets["trade_frame"], bg=theme["card_background"]
        )

        # 数量输入
        self.widgets["amount_label"] = tk.Label(
            self.widgets["input_frame"],
            text="数量:",
            font=("Arial", 12),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        self.widgets["amount_entry"] = tk.Entry(
            self.widgets["input_frame"],
            font=("Arial", 12),
            bg=theme["input_background"],
            fg=theme["text_primary"],
            insertbackground=theme["text_primary"],
            relief=tk.FLAT,
            width=15,
        )

        # 总金额显示
        self.widgets["total_label"] = tk.Label(
            self.widgets["input_frame"],
            text="总金额:",
            font=("Arial", 12),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        self.widgets["total_value"] = tk.Label(
            self.widgets["input_frame"],
            text="¥0.00",
            font=("Arial", 12, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 提交按钮
        self.widgets["submit_button"] = tk.Button(
            self.widgets["trade_frame"],
            text="确认交易",
            font=("Arial", 14, "bold"),
            bg=theme["primary_background"],
            fg=theme["primary_text"],
            relief=tk.FLAT,
            padx=20,
            pady=10,
            state=tk.DISABLED,
            command=self._submit_trade,
        )

        # 绑定数量变化事件
        self.widgets["amount_entry"].bind("<KeyRelease>", self._update_total)

        # 创建最近交易历史区域
        self.widgets["history_frame"] = tk.Frame(
            self.widgets["trade_frame"], bg=theme["card_background"]
        )

        self.widgets["history_label"] = tk.Label(
            self.widgets["history_frame"],
            text="最近交易",
            font=("Arial", 12, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 示例历史记录
        history_data = [
            {
                "time": "今天 10:23",
                "asset": "BTC",
                "type": "买入",
                "amount": "0.01",
                "price": "¥282,000",
            },
            {
                "time": "昨天 15:45",
                "asset": "ETH",
                "type": "卖出",
                "amount": "0.5",
                "price": "¥15,800",
            },
            {
                "time": "昨天 09:12",
                "asset": "LTC",
                "type": "买入",
                "amount": "2.0",
                "price": "¥960",
            },
        ]

        self.widgets["history_items"] = []
        for history in history_data:
            self._create_history_item(history, theme)

    def _layout_widgets(self):
        """布局所有控件"""
        # 布局头部区域
        self.widgets["header_frame"].pack(fill="x", padx=20, pady=(20, 10))
        self.widgets["title_label"].pack(side=tk.LEFT)
        self.widgets["market_info"].pack(side=tk.RIGHT)

        # 布局主内容区
        self.widgets["content_frame"].pack(
            fill="both", expand=True, padx=20, pady=10)

        # 左侧市场列表
        self.widgets["market_frame"].pack(
            side=tk.LEFT, fill="both", expand=True, padx=(0, 10)
        )
        self.widgets["market_label"].pack(anchor="w", pady=(0, 10))

        # 搜索框
        self.widgets["search_frame"].pack(fill="x", pady=(0, 10))
        self.widgets["search_entry"].pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        self.widgets["search_button"].pack(side=tk.RIGHT)

        # 资产列表
        self.widgets["asset_list_frame"].pack(fill="both", expand=True)
        self.widgets["list_header"].pack(fill="x", pady=(0, 5))

        for item_frame, _, _, _, _ in self.widgets["asset_items"]:
            item_frame.pack(fill="x", pady=2)

        # 右侧交易操作
        self.widgets["trade_frame"].pack(
            side=tk.RIGHT, fill="both", expand=True, padx=(10, 0)
        )
        self.widgets["trade_label"].pack(anchor="w", pady=(0, 10))

        # 选择的资产信息
        self.widgets["selected_asset_frame"].pack(fill="x", pady=(5, 15))
        self.widgets["selected_asset_label"].pack(anchor="w")
        self.widgets["selected_asset_price"].pack(anchor="w", pady=(5, 0))

        # 交易类型选择
        self.widgets["trade_type_frame"].pack(fill="x", pady=(0, 15))
        self.widgets["buy_button"].pack(side=tk.LEFT, padx=(0, 10))
        self.widgets["sell_button"].pack(side=tk.LEFT)

        # 数量和金额输入
        self.widgets["input_frame"].pack(fill="x", pady=(0, 15))
        self.widgets["amount_label"].pack(side=tk.LEFT)
        self.widgets["amount_entry"].pack(side=tk.LEFT, padx=(5, 15))
        self.widgets["total_label"].pack(side=tk.LEFT)
        self.widgets["total_value"].pack(side=tk.LEFT, padx=(5, 0))

        # 提交按钮
        self.widgets["submit_button"].pack(fill="x", pady=(0, 20))

        # 交易历史
        self.widgets["history_frame"].pack(fill="both", expand=True)
        self.widgets["history_label"].pack(anchor="w", pady=(0, 10))

        for item in self.widgets["history_items"]:
            item.pack(fill="x", pady=2)

    def _create_asset_item(self, asset, theme):
        """创建资产列表项"""
        item_frame = tk.Frame(
            self.widgets["asset_list_frame"],
            bg=theme["row_background"],
            padx=10,
            pady=8,
        )

        asset_name = tk.Label(
            item_frame,
            text=asset["name"],
            font=("Arial", 12),
            bg=theme["row_background"],
            fg=theme["text_primary"],
            anchor="w",
        )

        asset_price = tk.Label(
            item_frame,
            text=asset["price"],
            font=("Arial", 12),
            bg=theme["row_background"],
            fg=theme["text_primary"],
        )

        change_color = (
            theme["success_text"] if asset["is_positive"] else theme["error_text"]
        )
        asset_change = tk.Label(
            item_frame,
            text=asset["change"],
            font=("Arial", 12),
            bg=theme["row_background"],
            fg=change_color,
        )

        trade_button = tk.Button(
            item_frame,
            text="交易",
            font=("Arial", 10),
            bg=theme["primary_background"],
            fg=theme["primary_text"],
            relief=tk.FLAT,
            padx=8,
            pady=2,
            command=lambda a=asset: self._select_asset(a),
        )

        # 布局列表项
        asset_name.pack(side=tk.LEFT, fill="x", expand=True, anchor="w")
        asset_price.pack(side=tk.LEFT, fill="x", expand=True, anchor="w")
        asset_change.pack(side=tk.LEFT, fill="x", expand=True, anchor="w")
        trade_button.pack(side=tk.LEFT, fill="x", expand=True, anchor="w")

        # 添加悬停效果
        item_frame.bind(
            "<Enter>", lambda e, f=item_frame: self._on_item_hover(
                f, True, theme)
        )
        item_frame.bind(
            "<Leave>", lambda e, f=item_frame: self._on_item_hover(
                f, False, theme)
        )

        # 将项添加到列表中
        self.widgets["asset_items"].append(
            (item_frame, asset_name, asset_price, asset_change, trade_button)
        )

        return item_frame

    def _create_history_item(self, history, theme):
        """创建交易历史项"""
        is_buy = history["type"] == "买入"
        type_color = theme["success_text"] if is_buy else theme["error_text"]

        item_frame = tk.Frame(
            self.widgets["history_frame"], bg=theme["row_background"], padx=10, pady=8
        )

        history_text = tk.Label(
            item_frame,
            text=f"{history['time']} - {history['type']} {history['asset']} {history['amount']}",
            font=("Arial", 11),
            bg=theme["row_background"],
            fg=theme["text_primary"],
            anchor="w",
        )

        history_price = tk.Label(
            item_frame,
            text=history["price"],
            font=("Arial", 11),
            bg=theme["row_background"],
            fg=type_color,
            anchor="e",
        )

        history_text.pack(side=tk.LEFT, fill="x", expand=True, anchor="w")
        history_price.pack(side=tk.RIGHT, anchor="e")

        # 添加悬停效果
        item_frame.bind(
            "<Enter>", lambda e, f=item_frame: self._on_item_hover(
                f, True, theme)
        )
        item_frame.bind(
            "<Leave>", lambda e, f=item_frame: self._on_item_hover(
                f, False, theme)
        )

        # 将项添加到历史列表中
        self.widgets["history_items"].append(item_frame)

        return item_frame

    def _on_item_hover(self, frame, is_hover, theme):
        """列表项悬停效果"""
        if is_hover:
            frame.configure(bg=theme["row_hover_background"])
            for widget in frame.winfo_children():
                widget.configure(bg=theme["row_hover_background"])
            self.sound_manager.play("hover")
        else:
            frame.configure(bg=theme["row_background"])
            for widget in frame.winfo_children():
                widget.configure(bg=theme["row_background"])

    def _search_market(self):
        """搜索市场"""
        search_text = self.widgets["search_entry"].get().strip()
        if search_text:
            self.sound_manager.play("button_click")
            # 在实际应用中，这里会执行搜索逻辑
            messagebox.showinfo("搜索", f"搜索: {search_text}")

    def _select_asset(self, asset):
        """选择资产进行交易"""
        self.sound_manager.play("button_click")
        self.selected_asset = asset

        # 更新显示信息
        self.widgets["selected_asset_label"].configure(text=asset["name"])
        self.widgets["selected_asset_price"].configure(
            text=f"当前价格: {asset['price']}"
        )

        # 启用交易按钮
        self.widgets["submit_button"].configure(state=tk.NORMAL)

        # 初始化为买入状态
        self._set_trade_type("buy")

    def _set_trade_type(self, trade_type):
        """设置交易类型（买入/卖出）"""
        self.sound_manager.play("button_click")
        theme = self.theme_manager.get_current_theme()

        if trade_type == "buy":
            self.widgets["buy_button"].configure(
                bg=theme["success_background"], fg=theme["success_text"]
            )
            self.widgets["sell_button"].configure(
                bg=theme["button_background"], fg=theme["button_text"]
            )
        else:
            self.widgets["buy_button"].configure(
                bg=theme["button_background"], fg=theme["button_text"]
            )
            self.widgets["sell_button"].configure(
                bg=theme["error_background"], fg=theme["error_text"]
            )

        # 保存当前交易类型
        self.current_trade_type = trade_type

        # 更新总金额
        self._update_total(None)

    def _update_total(self, event):
        """更新总金额"""
        if self.selected_asset:
            amount_text = self.widgets["amount_entry"].get().strip()

            try:
                amount = float(amount_text) if amount_text else 0
                price_text = (
                    self.selected_asset["price"].replace(
                        "¥", "").replace(",", "")
                )
                price = float(price_text)

                total = amount * price
                self.widgets["total_value"].configure(text=f"¥{total:,.2f}")

                # 检查输入是否有效，决定提交按钮是否可用
                if amount > 0:
                    self.widgets["submit_button"].configure(state=tk.NORMAL)
                else:
                    self.widgets["submit_button"].configure(state=tk.DISABLED)

            except ValueError:
                self.widgets["total_value"].configure(text="¥0.00")
                self.widgets["submit_button"].configure(state=tk.DISABLED)

    def _submit_trade(self):
        """提交交易"""
        self.sound_manager.play("confirm")

        amount_text = self.widgets["amount_entry"].get().strip()
        trade_type = "买入" if self.current_trade_type == "buy" else "卖出"

        try:
            amount = float(amount_text)
            asset_name = self.selected_asset["name"]

            # 显示确认消息
            messagebox.showinfo(
                "交易确认",
                f"已{trade_type} {asset_name} {amount} 个\n"
                f"总金额: {self.widgets['total_value']['text']}",
            )

            # 重置表单
            self.widgets["amount_entry"].delete(0, tk.END)
            self.widgets["total_value"].configure(text="¥0.00")
            self.widgets["submit_button"].configure(state=tk.DISABLED)

            # 在实际应用中，这里会执行交易逻辑和更新交易历史

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数量")  # 交易视图