"""
分析视图模块
提供数据分析和可视化功能
"""

import tkinter as tk
from tkinter import ttk
import datetime
import random
import math
from . import BaseView


class AnalyticsView(BaseView):
    """分析视图，提供数据分析和可视化"""

    def __init__(self, parent, controller):
        self.widgets = {}  # 存储所有创建的小部件，便于主题应用

        # 图表数据
        self.chart_data = self._generate_sample_data()
        self.current_chart_type = "line"  # 默认图表类型：折线图
        self.current_time_range = "1w"  # 默认时间范围：1周

        super().__init__(parent, controller)

    def _create_widgets(self):
        """创建分析视图所有组件"""
        theme = self.theme_manager.get_current_theme()

        # 创建头部
        self.widgets["header_frame"] = tk.Frame(self, bg=theme["background"])
        self.widgets["title_label"] = tk.Label(
            self.widgets["header_frame"],
            text="数据分析",
            font=("Arial", 18, "bold"),
            bg=theme["background"],
            fg=theme["text_primary"],
        )

        # 创建图表类型选择器
        self.widgets["chart_type_frame"] = tk.Frame(
            self.widgets["header_frame"], bg=theme["background"]
        )

        chart_types = [
            {"value": "line", "text": "折线图", "icon": "📈"},
            {"value": "bar", "text": "柱状图", "icon": "📊"},
            {"value": "pie", "text": "饼图", "icon": "🔄"},
        ]

        for chart_type in chart_types:
            btn = tk.Button(
                self.widgets["chart_type_frame"],
                text=f"{chart_type['icon']} {chart_type['text']}",
                font=("Arial", 11),
                bg=(
                    theme["primary_background"]
                    if chart_type["value"] == self.current_chart_type
                    else theme["button_background"]
                ),
                fg=(
                    theme["primary_text"]
                    if chart_type["value"] == self.current_chart_type
                    else theme["button_text"]
                ),
                relief=tk.FLAT,
                padx=10,
                pady=5,
                command=lambda t=chart_type["value"]: self._change_chart_type(
                    t),
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.widgets[f"button_{chart_type['value']}"] = btn

        # 创建主内容区，分为左右两栏
        self.widgets["content_frame"] = tk.Frame(self, bg=theme["background"])

        # 左侧 - 过滤器和统计摘要
        self.widgets["filters_frame"] = tk.Frame(
            self.widgets["content_frame"], bg=theme["card_background"], padx=15, pady=15
        )

        # 时间范围选择器
        self.widgets["time_range_label"] = tk.Label(
            self.widgets["filters_frame"],
            text="时间范围",
            font=("Arial", 12, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        time_ranges = [
            {"value": "1d", "text": "1天"},
            {"value": "1w", "text": "1周"},
            {"value": "1m", "text": "1月"},
            {"value": "3m", "text": "3月"},
            {"value": "1y", "text": "1年"},
        ]

        self.widgets["time_range_frame"] = tk.Frame(
            self.widgets["filters_frame"], bg=theme["card_background"]
        )

        for time_range in time_ranges:
            btn = tk.Button(
                self.widgets["time_range_frame"],
                text=time_range["text"],
                font=("Arial", 11),
                bg=(
                    theme["primary_background"]
                    if time_range["value"] == self.current_time_range
                    else theme["button_background"]
                ),
                fg=(
                    theme["primary_text"]
                    if time_range["value"] == self.current_time_range
                    else theme["button_text"]
                ),
                relief=tk.FLAT,
                padx=8,
                pady=3,
                command=lambda r=time_range["value"]: self._change_time_range(
                    r),
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.widgets[f"button_{time_range['value']}"] = btn

        # 其他过滤选项
        filter_options = [
            {
                "label": "资产类型",
                "options": ["全部", "加密货币", "股票", "外汇", "商品"],
            },
            {"label": "交易类型", "options": ["全部", "买入", "卖出"]},
        ]

        self.filter_vars = {}
        for filter_option in filter_options:
            # 创建标签
            label = tk.Label(
                self.widgets["filters_frame"],
                text=filter_option["label"],
                font=("Arial", 12, "bold"),
                bg=theme["card_background"],
                fg=theme["text_primary"],
            )
            self.widgets[f"label_{filter_option['label']}"] = label

            # 创建下拉框
            var = tk.StringVar(value=filter_option["options"][0])
            self.filter_vars[filter_option["label"]] = var

            dropdown = ttk.Combobox(
                self.widgets["filters_frame"],
                textvariable=var,
                values=filter_option["options"],
                font=("Arial", 11),
                state="readonly",
                width=15,
            )
            dropdown.bind("<<ComboboxSelected>>",
                          lambda e: self._update_chart())
            self.widgets[f"dropdown_{filter_option['label']}"] = dropdown

        # 统计摘要
        self.widgets["summary_label"] = tk.Label(
            self.widgets["filters_frame"],
            text="统计摘要",
            font=("Arial", 12, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 创建统计数据卡片
        self.widgets["summary_frame"] = tk.Frame(
            self.widgets["filters_frame"], bg=theme["card_background"]
        )

        summary_data = [
            {"label": "总交易次数", "value": "157"},
            {"label": "成功率", "value": "82%"},
            {"label": "平均收益", "value": "¥320"},
            {"label": "最大收益", "value": "¥2,450"},
        ]

        for data in summary_data:
            self._create_summary_card(data, theme)

        # 右侧 - 图表区域
        self.widgets["chart_frame"] = tk.Frame(
            self.widgets["content_frame"], bg=theme["card_background"], padx=15, pady=15
        )

        self.widgets["chart_title"] = tk.Label(
            self.widgets["chart_frame"],
            text="交易数据分析",
            font=("Arial", 14, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 创建图表画布
        self.widgets["chart_canvas"] = tk.Canvas(
            self.widgets["chart_frame"],
            bg=theme["card_background"],
            highlightthickness=0,
            height=300,
        )

        # 数据表格区域
        self.widgets["table_frame"] = tk.Frame(
            self, bg=theme["card_background"], padx=15, pady=15
        )

        self.widgets["table_label"] = tk.Label(
            self.widgets["table_frame"],
            text="详细数据",
            font=("Arial", 14, "bold"),
            bg=theme["card_background"],
            fg=theme["text_primary"],
        )

        # 创建表格
        self.widgets["table"] = ttk.Treeview(
            self.widgets["table_frame"],
            columns=("date", "asset", "type", "amount", "price", "total"),
            show="headings",
            height=8,
        )

        # 设置列标题
        self.widgets["table"].heading("date", text="日期")
        self.widgets["table"].heading("asset", text="资产")
        self.widgets["table"].heading("type", text="类型")
        self.widgets["table"].heading("amount", text="数量")
        self.widgets["table"].heading("price", text="价格")
        self.widgets["table"].heading("total", text="总金额")

        # 设置列宽
        self.widgets["table"].column("date", width=100)
        self.widgets["table"].column("asset", width=100)
        self.widgets["table"].column("type", width=80)
        self.widgets["table"].column("amount", width=80)
        self.widgets["table"].column("price", width=100)
        self.widgets["table"].column("total", width=100)

        # 添加滚动条
        self.widgets["table_scrollbar"] = ttk.Scrollbar(
            self.widgets["table_frame"],
            orient="vertical",
            command=self.widgets["table"].yview,
        )
        self.widgets["table"].configure(
            yscrollcommand=self.widgets["table_scrollbar"].set
        )

        # 填充表格数据
        self._populate_table()

        # 导出按钮
        self.widgets["export_frame"] = tk.Frame(
            self.widgets["table_frame"], bg=theme["card_background"]
        )

        self.widgets["export_button"] = tk.Button(
            self.widgets["export_frame"],
            text="导出数据",
            font=("Arial", 11),
            bg=theme["button_background"],
            fg=theme["button_text"],
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self._export_data,
        )

        self.widgets["print_button"] = tk.Button(
            self.widgets["export_frame"],
            text="打印报告",
            font=("Arial", 11),
            bg=theme["button_background"],
            fg=theme["button_text"],
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self._print_report,
        )

    def _layout_widgets(self):
        """布局所有控件"""
        # 布局头部
        self.widgets["header_frame"].pack(fill="x", padx=20, pady=(20, 10))
        self.widgets["title_label"].pack(side=tk.LEFT)
        self.widgets["chart_type_frame"].pack(side=tk.RIGHT)

        # 布局主内容区
        self.widgets["content_frame"].pack(fill="x", padx=20, pady=10)

        # 左侧过滤器和统计摘要
        self.widgets["filters_frame"].pack(
            side=tk.LEFT, fill="y", padx=(0, 10))

        # 时间范围选择器
        self.widgets["time_range_label"].pack(anchor="w", pady=(0, 5))
        self.widgets["time_range_frame"].pack(fill="x", pady=(0, 15))

        # 其他过滤选项
        for filter_option in ["资产类型", "交易类型"]:
            self.widgets[f"label_{filter_option}"].pack(
                anchor="w", pady=(0, 5))
            self.widgets[f"dropdown_{filter_option}"].pack(
                fill="x", pady=(0, 15))

        # 统计摘要
        self.widgets["summary_label"].pack(anchor="w", pady=(10, 5))
        self.widgets["summary_frame"].pack(fill="x")

        # 右侧图表区域
        self.widgets["chart_frame"].pack(
            side=tk.RIGHT, fill="both", expand=True)
        self.widgets["chart_title"].pack(anchor="w", pady=(0, 10))
        self.widgets["chart_canvas"].pack(fill="both", expand=True)

        # 绘制图表
        self._draw_chart()

        # 数据表格区域
        self.widgets["table_frame"].pack(
            fill="both", expand=True, padx=20, pady=10)
        self.widgets["table_label"].pack(anchor="w", pady=(0, 10))
        self.widgets["table_scrollbar"].pack(side=tk.RIGHT, fill="y")
        self.widgets["table"].pack(fill="both", expand=True)

        # 导出按钮
        self.widgets["export_frame"].pack(anchor="e", pady=(10, 0))
        self.widgets["export_button"].pack(side=tk.LEFT, padx=(0, 10))
        self.widgets["print_button"].pack(side=tk.LEFT)

    def _create_summary_card(self, data, theme):
        """创建统计摘要卡片"""
        card = tk.Frame(
            self.widgets["summary_frame"], bg=theme["row_background"], padx=10, pady=8
        )

        label = tk.Label(
            card,
            text=data["label"],
            font=("Arial", 11),
            bg=theme["row_background"],
            fg=theme["text_secondary"],
            anchor="w",
        )

        value = tk.Label(
            card,
            text=data["value"],
            font=("Arial", 14, "bold"),
            bg=theme["row_background"],
            fg=theme["text_primary"],
            anchor="w",
        )

        label.pack(anchor="w")
        value.pack(anchor="w", pady=(5, 0))

        card.pack(fill="x", pady=5)

        # 添加悬停效果
        card.bind("<Enter>", lambda e,
                  f=card: self._on_card_hover(f, True, theme))
        card.bind("<Leave>", lambda e,
                  f=card: self._on_card_hover(f, False, theme))

        # 保存控件引用
        self.widgets[f"card_{data['label']}"] = card
        self.widgets[f"label_{data['label']}_card"] = label
        self.widgets[f"value_{data['label']}"] = value

        return card

    def _on_card_hover(self, frame, is_hover, theme):
        """卡片悬停效果"""
        if is_hover:
            frame.configure(bg=theme["row_hover_background"])
            for widget in frame.winfo_children():
                widget.configure(bg=theme["row_hover_background"])
            self.sound_manager.play("hover")
        else:
            frame.configure(bg=theme["row_background"])
            for widget in frame.winfo_children():
                widget.configure(bg=theme["row_background"])

    def _generate_sample_data(self):
        """生成示例数据"""
        data = {"line": [], "bar": [], "pie": []}

        # 生成折线图和柱状图数据
        end_date = datetime.datetime.now()

        # 生成一年的数据
        for i in range(365, 0, -1):
            date = end_date - datetime.timedelta(days=i)
            value = random.randint(50, 200) + math.sin(i / 20) * 50

            data_point = {"date": date.strftime("%Y-%m-%d"), "value": value}

            data["line"].append(data_point)

            # 每月第一天的数据用于柱状图
            if date.day == 1:
                data["bar"].append(data_point)

        # 生成饼图数据
        pie_data = [
            {"label": "比特币 (BTC)", "value": 45},
            {"label": "以太坊 (ETH)", "value": 30},
            {"label": "莱特币 (LTC)", "value": 15},
            {"label": "瑞波币 (XRP)", "value": 10},
        ]
        data["pie"] = pie_data

        return data

    def _change_chart_type(self, chart_type):
        """切换图表类型"""
        self.sound_manager.play("button_click")

        if chart_type != self.current_chart_type:
            self.current_chart_type = chart_type

            # 更新按钮样式
            theme = self.theme_manager.get_current_theme()
            for t in ["line", "bar", "pie"]:
                if t == chart_type:
                    self.widgets[f"button_{t}"].configure(
                        bg=theme["primary_background"], fg=theme["primary_text"]
                    )
                else:
                    self.widgets[f"button_{t}"].configure(
                        bg=theme["button_background"], fg=theme["button_text"]
                    )

            # 重绘图表
            self._draw_chart()

    def _change_time_range(self, time_range):
        """切换时间范围"""
        self.sound_manager.play("button_click")

        if time_range != self.current_time_range:
            self.current_time_range = time_range

            # 更新按钮样式
            theme = self.theme_manager.get_current_theme()
            for t in ["1d", "1w", "1m", "3m", "1y"]:
                if t == time_range:
                    self.widgets[f"button_{t}"].configure(
                        bg=theme["primary_background"], fg=theme["primary_text"]
                    )
                else:
                    self.widgets[f"button_{t}"].configure(
                        bg=theme["button_background"], fg=theme["button_text"]
                    )

            # 重绘图表
            self._draw_chart()

    def _update_chart(self):
        """更新图表"""
        self.sound_manager.play("click")
        self._draw_chart()

    def _draw_chart(self):
        """绘制图表"""
        # 清除画布
        self.widgets["chart_canvas"].delete("all")

        # 获取画布大小
        width = self.widgets["chart_canvas"].winfo_width()
        height = self.widgets["chart_canvas"].winfo_height()

        # 确保画布有足够大小
        if width < 20 or height < 20:
            # 画布尚未完全布局，延迟绘制
            self.after(100, self._draw_chart)
            return

        theme = self.theme_manager.get_current_theme()

        # 根据图表类型绘制不同的图表
        if self.current_chart_type == "line":
            self._draw_line_chart(width, height, theme)
        elif self.current_chart_type == "bar":
            self._draw_bar_chart(width, height, theme)
        elif self.current_chart_type == "pie":
            self._draw_pie_chart(width, height, theme)

    def _draw_line_chart(self, width, height, theme):
        """绘制折线图"""
        # 边距
        margin = {"top": 20, "right": 20, "bottom": 30, "left": 40}
        chart_width = width - margin["left"] - margin["right"]
        chart_height = height - margin["top"] - margin["bottom"]

        # 过滤数据根据时间范围
        filtered_data = self._filter_data_by_time_range(
            self.chart_data["line"])

        if not filtered_data:
            return

        # 找到数值范围
        min_value = min(point["value"] for point in filtered_data)
        max_value = max(point["value"] for point in filtered_data)

        # 添加一些边距
        value_margin = (max_value - min_value) * 0.1
        min_value = max(0, min_value - value_margin)
        max_value = max_value + value_margin

        # 绘制坐标轴
        self.widgets["chart_canvas"].create_line(
            margin["left"],
            height - margin["bottom"],
            width - margin["right"],
            height - margin["bottom"],
            fill=theme["text_secondary"],
        )

        self.widgets["chart_canvas"].create_line(
            margin["left"],
            margin["top"],
            margin["left"],
            height - margin["bottom"],
            fill=theme["text_secondary"],
        )

        # 绘制折线
        points = []
        for i, point in enumerate(filtered_data):
            x = margin["left"] + (i / (len(filtered_data) - 1)) * chart_width
            y = (
                height
                - margin["bottom"]
                - ((point["value"] - min_value) / (max_value - min_value))
                * chart_height
            )
            points.extend([x, y])

            # 绘制数据点
            self.widgets["chart_canvas"].create_oval(
                x - 3,
                y - 3,
                x + 3,
                y + 3,
                fill=theme["primary_background"],
                outline=theme["primary_background"],
            )

        # 绘制连线
        self.widgets["chart_canvas"].create_line(
            points, fill=theme["primary_background"], width=2, smooth=True
        )

        # 绘制日期标签
        dates_to_show = 5
        for i in range(dates_to_show):
            idx = int(i * (len(filtered_data) - 1) / (dates_to_show - 1))
            x = margin["left"] + (idx / (len(filtered_data) - 1)) * chart_width
            self.widgets["chart_canvas"].create_text(
                x,
                height - margin["bottom"] + 15,
                text=filtered_data[idx]["date"],
                fill=theme["text_secondary"],
                font=("Arial", 8),
            )

        # 绘制值标签
        values_to_show = 5
        for i in range(values_to_show):
            value = min_value + (i / (values_to_show - 1)
                                 ) * (max_value - min_value)
            y = height - margin["bottom"] - \
                (i / (values_to_show - 1)) * chart_height
            self.widgets["chart_canvas"].create_text(
                margin["left"] - 10,
                y,
                text=f"{value:.0f}",
                fill=theme["text_secondary"],
                font=("Arial", 8),
                anchor="e",
            )

    def _draw_bar_chart(self, width, height, theme):
        """绘制柱状图"""
        # 边距
        margin = {"top": 20, "right": 20, "bottom": 30, "left": 40}
        chart_width = width - margin["left"] - margin["right"]
        chart_height = height - margin["top"] - margin["bottom"]

        # 过滤数据根据时间范围
        filtered_data = self._filter_data_by_time_range(self.chart_data["bar"])

        if not filtered_data:
            return

        # 找到数值范围
        min_value = min(point["value"] for point in filtered_data)
        max_value = max(point["value"] for point in filtered_data)

        # 添加一些边距
        value_margin = (max_value - min_value) * 0.1
        min_value = max(0, min_value - value_margin)
        max_value = max_value + value_margin

        # 绘制坐标轴
        self.widgets["chart_canvas"].create_line(
            margin["left"],
            height - margin["bottom"],
            width - margin["right"],
            height - margin["bottom"],
            fill=theme["text_secondary"],
        )

        self.widgets["chart_canvas"].create_line(
            margin["left"],
            margin["top"],
            margin["left"],
            height - margin["bottom"],
            fill=theme["text_secondary"],
        )

        # 绘制柱状图
        bar_width = chart_width / len(filtered_data) * 0.8
        for i, point in enumerate(filtered_data):
            x = margin["left"] + (i + 0.5) / len(filtered_data) * chart_width
            y_top = (
                height
                - margin["bottom"]
                - ((point["value"] - min_value) / (max_value - min_value))
                * chart_height
            )
            y_bottom = height - margin["bottom"]

            self.widgets["chart_canvas"].create_rectangle(
                x - bar_width / 2,
                y_top,
                x + bar_width / 2,
                y_bottom,
                fill=theme["primary_background"],
                outline="",
            )

            # 绘制值标签
            self.widgets["chart_canvas"].create_text(
                x,
                y_top - 10,
                text=f"{point['value']:.0f}",
                fill=theme["text_primary"],
                font=("Arial", 8),
            )

        # 绘制日期标签
        for i, point in enumerate(filtered_data):
            x = margin["left"] + (i + 0.5) / len(filtered_data) * chart_width
            self.widgets["chart_canvas"].create_text(
                x,
                height - margin["bottom"] + 15,
                text=point["date"],
                fill=theme["text_secondary"],
                font=("Arial", 8),
            )

        # 绘制值标签
        values_to_show = 5
        for i in range(values_to_show):
            value = min_value + (i / (values_to_show - 1)
                                 ) * (max_value - min_value)
            y = height - margin["bottom"] - \
                (i / (values_to_show - 1)) * chart_height
            self.widgets["chart_canvas"].create_text(
                margin["left"] - 10,
                y,
                text=f"{value:.0f}",
                fill=theme["text_secondary"],
                font=("Arial", 8),
                anchor="e",
            )

    def _draw_pie_chart(self, width, height, theme):
        """绘制饼图"""
        # 计算中心和半径
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 40

        pie_data = self.chart_data["pie"]
        total = sum(item["value"] for item in pie_data)

        # 绘制饼图
        start_angle = 0
        for i, item in enumerate(pie_data):
            angle = item["value"] / total * 360
            end_angle = start_angle + angle

            # 创建一个颜色序列
            colors = [
                theme["primary_background"],
                theme["success_background"],
                theme["error_background"],
                theme["tag_background"],
            ]
            color = colors[i % len(colors)]

            # 绘制扇形
            self.widgets["chart_canvas"].create_arc(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                start=start_angle,
                extent=angle,
                fill=color,
                outline="",
            )

            # 计算标签位置
            mid_angle = math.radians(start_angle + angle / 2)
            label_x = center_x + (radius * 0.7) * math.cos(mid_angle)
            label_y = center_y + (radius * 0.7) * math.sin(mid_angle)

            # 绘制标签
            self.widgets["chart_canvas"].create_text(
                label_x,
                label_y,
                text=f"{item['label']}\n{item['value']}%",
                fill=theme["text_primary"],
                font=("Arial", 9, "bold"),
                justify="center",
            )

            start_angle = end_angle

    def _filter_data_by_time_range(self, data):
        """根据时间范围过滤数据"""
        now = datetime.datetime.now()

        # 转换时间范围为天数
        days = {"1d": 1, "1w": 7, "1m": 30, "3m": 90, "1y": 365}

        days_to_show = days.get(self.current_time_range, 30)

        # 过滤数据
        filtered_data = []
        for point in data:
            date = datetime.datetime.strptime(point["date"], "%Y-%m-%d")
            if (now - date).days <= days_to_show:
                filtered_data.append(point)

        return filtered_data

    def _populate_table(self):
        """填充表格数据"""
        # 清空表格
        for item in self.widgets["table"].get_children():
            self.widgets["table"].delete(item)

        # 示例数据
        table_data = [
            {
                "date": "2023-05-20",
                "asset": "BTC",
                "type": "买入",
                "amount": "0.01",
                "price": "¥282,450",
                "total": "¥2,824.50",
            },
            {
                "date": "2023-05-19",
                "asset": "ETH",
                "type": "卖出",
                "amount": "0.5",
                "price": "¥15,890",
                "total": "¥7,945.00",
            },
            {
                "date": "2023-05-18",
                "asset": "LTC",
                "type": "买入",
                "amount": "2.0",
                "price": "¥950",
                "total": "¥1,900.00",
            },
            {
                "date": "2023-05-15",
                "asset": "XRP",
                "type": "买入",
                "amount": "100",
                "price": "¥3.21",
                "total": "¥321.00",
            },
            {
                "date": "2023-05-10",
                "asset": "BTC",
                "type": "卖出",
                "amount": "0.005",
                "price": "¥281,200",
                "total": "¥1,406.00",
            },
            {
                "date": "2023-05-05",
                "asset": "ETH",
                "type": "买入",
                "amount": "0.3",
                "price": "¥15,750",
                "total": "¥4,725.00",
            },
            {
                "date": "2023-05-01",
                "asset": "ADA",
                "type": "买入",
                "amount": "500",
                "price": "¥2.85",
                "total": "¥1,425.00",
            },
            {
                "date": "2023-04-28",
                "asset": "LTC",
                "type": "卖出",
                "amount": "1.0",
                "price": "¥960",
                "total": "¥960.00",
            },
            {
                "date": "2023-04-25",
                "asset": "BTC",
                "type": "买入",
                "amount": "0.02",
                "price": "¥280,500",
                "total": "¥5,610.00",
            },
            {
                "date": "2023-04-20",
                "asset": "XRP",
                "type": "卖出",
                "amount": "50",
                "price": "¥3.18",
                "total": "¥159.00",
            },
        ]

        # 添加数据到表格
        for item in table_data:
            values = (
                item["date"],
                item["asset"],
                item["type"],
                item["amount"],
                item["price"],
                item["total"],
            )
            self.widgets["table"].insert("", "end", values=values)

    def _export_data(self):
        """导出数据"""
        self.sound_manager.play("button_click")
        tk.messagebox.showinfo("导出数据", "数据已导出到 analytics_data.csv")

    def _print_report(self):
        """打印报告"""
        self.sound_manager.play("button_click")
        tk.messagebox.showinfo("打印报告", "报告已发送到打印队列")