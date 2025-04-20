"""
帮助视图模块
提供用户帮助和教程功能
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from . import BaseView


class HelpView(BaseView):
    """帮助视图，提供系统帮助和教程"""
    
    def __init__(self, parent, controller):
        self.widgets = {}  # 存储所有创建的小部件，便于主题应用
        self.current_topic = None  # 当前选中的主题
        super().__init__(parent, controller)
        
    def _create_widgets(self):
        """创建帮助视图所有组件"""
        theme = self.theme_manager.get_current_theme()
        
        # 创建头部
        self.widgets['header_frame'] = tk.Frame(self, bg=theme['background'])
        self.widgets['title_label'] = tk.Label(
            self.widgets['header_frame'],
            text="帮助与教程",
            font=("Arial", 18, "bold"),
            bg=theme['background'],
            fg=theme['text_primary']
        )
        
        # 搜索框
        self.widgets['search_frame'] = tk.Frame(
            self.widgets['header_frame'],
            bg=theme['background']
        )
        
        self.widgets['search_entry'] = tk.Entry(
            self.widgets['search_frame'],
            font=("Arial", 12),
            bg=theme['input_background'],
            fg=theme['text_primary'],
            insertbackground=theme['text_primary'],
            relief=tk.FLAT,
            width=25
        )
        
        self.widgets['search_button'] = tk.Button(
            self.widgets['search_frame'],
            text="搜索",
            font=("Arial", 12),
            bg=theme['button_background'],
            fg=theme['button_text'],
            relief=tk.FLAT,
            padx=10,
            command=self._search_help
        )
        
        # 创建主内容区，分为左右两栏
        self.widgets['content_frame'] = tk.Frame(self, bg=theme['background'])
        
        # 左侧 - 帮助主题列表
        self.widgets['topics_frame'] = tk.Frame(
            self.widgets['content_frame'],
            bg=theme['card_background'],
            padx=15,
            pady=15
        )
        
        self.widgets['topics_label'] = tk.Label(
            self.widgets['topics_frame'],
            text="帮助主题",
            font=("Arial", 14, "bold"),
            bg=theme['card_background'],
            fg=theme['text_primary']
        )
        
        # 创建主题列表
        self.widgets['topics_list_frame'] = tk.Frame(
            self.widgets['topics_frame'],
            bg=theme['card_background']
        )
        
        # 帮助主题数据
        self.help_topics = [
            {"id": "getting_started", "title": "入门指南", "icon": "🚀"},
            {"id": "account", "title": "账户管理", "icon": "👤"},
            {"id": "trading", "title": "交易指南", "icon": "💹"},
            {"id": "security", "title": "安全设置", "icon": "🔒"},
            {"id": "analytics", "title": "数据分析", "icon": "📊"},
            {"id": "api", "title": "API接口", "icon": "🔌"},
            {"id": "faq", "title": "常见问题", "icon": "❓"},
            {"id": "contact", "title": "联系我们", "icon": "✉️"}
        ]
        
        self.widgets['topic_items'] = []
        for topic in self.help_topics:
            self._create_topic_item(topic, theme)
        
        # 右侧 - 帮助内容
        self.widgets['content_container'] = tk.Frame(
            self.widgets['content_frame'],
            bg=theme['card_background'],
            padx=20,
            pady=20
        )
        
        # 内容区域标题
        self.widgets['content_title'] = tk.Label(
            self.widgets['content_container'],
            text="请选择一个帮助主题",
            font=("Arial", 16, "bold"),
            bg=theme['card_background'],
            fg=theme['text_primary']
        )
        
        # 内容区域分隔线
        self.widgets['content_separator'] = ttk.Separator(
            self.widgets['content_container'],
            orient='horizontal'
        )
        
        # 内容滚动区域
        self.widgets['content_canvas'] = tk.Canvas(
            self.widgets['content_container'],
            bg=theme['card_background'],
            highlightthickness=0
        )
        
        self.widgets['content_scrollbar'] = ttk.Scrollbar(
            self.widgets['content_container'],
            orient="vertical",
            command=self.widgets['content_canvas'].yview
        )
        
        self.widgets['content_canvas'].configure(
            yscrollcommand=self.widgets['content_scrollbar'].set
        )
        
        self.widgets['content_frame_inner'] = tk.Frame(
            self.widgets['content_canvas'],
            bg=theme['card_background']
        )
        
        # 创建帮助内容
        self.help_contents = {
            "getting_started": self._create_getting_started_content,
            "account": self._create_account_content,
            "trading": self._create_trading_content,
            "security": self._create_security_content,
            "analytics": self._create_analytics_content,
            "api": self._create_api_content,
            "faq": self._create_faq_content,
            "contact": self._create_contact_content
        }
        
        # 创建视频教程区域
        self.widgets['tutorial_frame'] = tk.Frame(
            self,
            bg=theme['card_background'],
            padx=20,
            pady=20
        )
        
        self.widgets['tutorial_label'] = tk.Label(
            self.widgets['tutorial_frame'],
            text="视频教程",
            font=("Arial", 14, "bold"),
            bg=theme['card_background'],
            fg=theme['text_primary']
        )
        
        # 创建视频卡片
        self.widgets['videos_frame'] = tk.Frame(
            self.widgets['tutorial_frame'],
            bg=theme['card_background']
        )
        
        tutorial_videos = [
            {"title": "快速入门指南", "duration": "5:24", "thumbnail": "thumbnail_1.jpg"},
            {"title": "如何进行交易", "duration": "8:12", "thumbnail": "thumbnail_2.jpg"},
            {"title": "数据分析功能介绍", "duration": "6:45", "thumbnail": "thumbnail_3.jpg"},
            {"title": "账户安全设置", "duration": "4:30", "thumbnail": "thumbnail_4.jpg"}
        ]
        
        self.widgets['video_items'] = []
        for video in tutorial_videos:
            video_card = self._create_video_card(video, theme)
            self.widgets['video_items'].append(video_card)
    
    def _layout_widgets(self):
        """布局所有控件"""
        # 布局头部
        self.widgets['header_frame'].pack(fill='x', padx=20, pady=(20, 10))
        self.widgets['title_label'].pack(side=tk.LEFT)
        self.widgets['search_frame'].pack(side=tk.RIGHT)
        self.widgets['search_entry'].pack(side=tk.LEFT, padx=(0, 5))
        self.widgets['search_button'].pack(side=tk.RIGHT)
        
        # 布局主内容区
        self.widgets['content_frame'].pack(fill='both', expand=True, padx=20, pady=10)
        
        # 左侧主题列表
        self.widgets['topics_frame'].pack(side=tk.LEFT, fill='y', padx=(0, 10))
        self.widgets['topics_label'].pack(anchor='w', pady=(0, 10))
        self.widgets['topics_list_frame'].pack(fill='both', expand=True)
        
        for item_frame in self.widgets['topic_items']:
            item_frame.pack(fill='x', pady=2)
        
        # 右侧内容区域
        self.widgets['content_container'].pack(side=tk.RIGHT, fill='both', expand=True)
        self.widgets['content_title'].pack(anchor='w')
        self.widgets['content_separator'].pack(fill='x', pady=10)
        
        self.widgets['content_scrollbar'].pack(side=tk.RIGHT, fill='y')
        self.widgets['content_canvas'].pack(side=tk.LEFT, fill='both', expand=True)
        
        self.widgets['content_canvas'].create_window(
            (0, 0),
            window=self.widgets['content_frame_inner'],
            anchor='nw',
            tags='content_frame_inner'
        )
        
        self.widgets['content_frame_inner'].bind(
            "<Configure>",
            lambda e: self.widgets['content_canvas'].configure(
                scrollregion=self.widgets['content_canvas'].bbox("all"),
                width=e.width
            )
        )
        
        # 绑定鼠标滚轮事件
        self.widgets['content_canvas'].bind_all(
            "<MouseWheel>",
            lambda e: self.widgets['content_canvas'].yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            )
        )
        
        # 创建视频教程区域
        self.widgets['tutorial_frame'].pack(fill='x', padx=20, pady=10)
        self.widgets['tutorial_label'].pack(anchor='w', pady=(0, 10))
        self.widgets['videos_frame'].pack(fill='x')
        
        # 布局视频卡片
        for i, video_frame in enumerate(self.widgets['video_items']):
            video_frame.pack(side=tk.LEFT, padx=(0 if i == 0 else 10, 0))
        
        # 默认选择第一个主题
        if self.help_topics:
            self._select_topic(self.help_topics[0])
    
    def _create_topic_item(self, topic, theme):
        """创建主题列表项"""
        item_frame = tk.Frame(
            self.widgets['topics_list_frame'],
            bg=theme['row_background'],
            padx=10,
            pady=8,
            cursor="hand2"
        )
        
        topic_icon = tk.Label(
            item_frame,
            text=topic['icon'],
            font=("Arial", 14),
            bg=theme['row_background'],
            fg=theme['text_primary']
        )
        
        topic_title = tk.Label(
            item_frame,
            text=topic['title'],
            font=("Arial", 12),
            bg=theme['row_background'],
            fg=theme['text_primary'],
            anchor='w'
        )
        
        topic_icon.pack(side=tk.LEFT, padx=(0, 10))
        topic_title.pack(side=tk.LEFT, fill='x', expand=True)
        
        # 绑定点击事件
        item_frame.bind("<Button-1>", lambda e, t=topic: self._select_topic(t))
        topic_icon.bind("<Button-1>", lambda e, t=topic: self._select_topic(t))
        topic_title.bind("<Button-1>", lambda e, t=topic: self._select_topic(t))
        
        # 添加悬停效果
        item_frame.bind("<Enter>", lambda e, f=item_frame: self._on_item_hover(f, True, theme))
        item_frame.bind("<Leave>", lambda e, f=item_frame: self._on_item_hover(f, False, theme))
        
        # 保存引用
        topic['frame'] = item_frame
        topic['icon_label'] = topic_icon
        topic['title_label'] = topic_title
        
        self.widgets['topic_items'].append(item_frame)
        
        return item_frame
    
    def _on_item_hover(self, frame, is_hover, theme):
        """列表项悬停效果"""
        if is_hover:
            frame.configure(bg=theme['row_hover_background'])
            for widget in frame.winfo_children():
                widget.configure(bg=theme['row_hover_background'])
            self.sound_manager.play('hover')
        else:
            frame.configure(bg=theme['row_background'])
            for widget in frame.winfo_children():
                widget.configure(bg=theme['row_background'])
    
    def _create_video_card(self, video, theme):
        """创建视频教程卡片"""
        card_frame = tk.Frame(
            self.widgets['videos_frame'],
            bg=theme['card_background'],
            width=150,
            height=120,
            pady=10,
            padx=10
        )
        
        # 视频缩略图（使用Canvas代替实际图片）
        thumbnail = tk.Canvas(
            card_frame,
            width=130,
            height=80,
            bg=theme['primary_background'],
            highlightthickness=0
        )
        
        # 播放按钮
        thumbnail.create_oval(55, 30, 75, 50, fill=theme['button_background'], outline="")
        thumbnail.create_polygon(60, 35, 60, 45, 70, 40, fill=theme['button_text'])
        
        # 视频时长
        duration_label = tk.Label(
            thumbnail,
            text=video['duration'],
            font=("Arial", 8),
            bg=theme['button_background'],
            fg=theme['button_text'],
            padx=3,
            pady=1
        )
        duration_label.place(relx=1.0, rely=1.0, x=-5, y=-5, anchor='se')
        
        # 视频标题
        title_label = tk.Label(
            card_frame,
            text=video['title'],
            font=("Arial", 10),
            bg=theme['card_background'],
            fg=theme['text_primary'],
            wraplength=130,
            justify='left'
        )
        
        # 布局
        thumbnail.pack(pady=(0, 5))
        title_label.pack(anchor='w')
        
        # 添加点击事件
        thumbnail.bind("<Button-1>", lambda e, v=video: self._play_video(v))
        thumbnail.bind("<Enter>", lambda e: thumbnail.configure(cursor="hand2"))
        
        return card_frame
    
    def _select_topic(self, topic):
        """选择主题并显示内容"""
        self.sound_manager.play('button_click')
        
        # 更新当前主题
        self.current_topic = topic
        
        # 更新标题
        self.widgets['content_title'].configure(text=f"{topic['icon']} {topic['title']}")
        
        # 清除现有内容
        for widget in self.widgets['content_frame_inner'].winfo_children():
            widget.destroy()
        
        # 创建新内容
        content_creator = self.help_contents.get(topic['id'])
        if content_creator:
            content_creator()
        
        # 更新主题列表样式
        theme = self.theme_manager.get_current_theme()
        for t in self.help_topics:
            if t['id'] == topic['id']:
                t['frame'].configure(bg=theme['primary_background'])
                t['icon_label'].configure(bg=theme['primary_background'], fg=theme['primary_text'])
                t['title_label'].configure(bg=theme['primary_background'], fg=theme['primary_text'])
            else:
                t['frame'].configure(bg=theme['row_background'])
                t['icon_label'].configure(bg=theme['row_background'], fg=theme['text_primary'])
                t['title_label'].configure(bg=theme['row_background'], fg=theme['text_primary'])
    
    def _search_help(self):
        """搜索帮助内容"""
        search_text = self.widgets['search_entry'].get().strip()
        if not search_text:
            return
        
        self.sound_manager.play('button_click')
        
        # 在实际应用中，这里会执行搜索逻辑
        # 这里我们简单模拟一下，找到第一个匹配的主题
        for topic in self.help_topics:
            if search_text.lower() in topic['title'].lower():
                self._select_topic(topic)
                return
        
        # 如果没有找到匹配的主题，显示搜索结果
        self.widgets['content_title'].configure(text=f"搜索: {search_text}")
        
        # 清除现有内容
        for widget in self.widgets['content_frame_inner'].winfo_children():
            widget.destroy()
        
        # 创建搜索结果内容
        theme = self.theme_manager.get_current_theme()
        
        no_results = tk.Label(
            self.widgets['content_frame_inner'],
            text=f"没有找到与 \"{search_text}\" 相关的帮助内容",
            font=("Arial", 12),
            bg=theme['card_background'],
            fg=theme['text_primary'],
            pady=20
        )
        no_results.pack(anchor='w')
        
        suggestion = tk.Label(
            self.widgets['content_frame_inner'],
            text="您可以尝试以下操作:",
            font=("Arial", 12),
            bg=theme['card_background'],
            fg=theme['text_primary'],
            pady=5
        )
        suggestion.pack(anchor='w')
        
        suggestions = [
            "检查拼写是否正确",
            "使用更通用的关键词",
            "浏览左侧的帮助主题",
            "联系客服获取帮助"
        ]
        
        for s in suggestions:
            item = tk.Label(
                self.widgets['content_frame_inner'],
                text=f"• {s}",
                font=("Arial", 12),
                bg=theme['card_background'],
                fg=theme['text_primary'],
                pady=2
            )
            item.pack(anchor='w', padx=20)
    
    def _play_video(self, video):
        """播放视频（模拟）"""
        self.sound_manager.play('button_click')
        
        # 在实际应用中，这里会播放视频
        # 这里简单弹出消息框
        tk.messagebox.showinfo("视频播放", f"正在播放: {video['title']}")
    
    def _add_section(self, title, content, theme=None):
        """添加内容区域的章节"""
        if theme is None:
            theme = self.theme_manager.get_current_theme()
        
        section_frame = tk.Frame(
            self.widgets['content_frame_inner'],
            bg=theme['card_background'],
            pady=10
        )
        
        if title:
            section_title = tk.Label(
                section_frame,
                text=title,
                font=("Arial", 14, "bold"),
                bg=theme['card_background'],
                fg=theme['text_primary']
            )
            section_title.pack(anchor='w', pady=(0, 5))
        
        section_content = tk.Label(
            section_frame,
            text=content,
            font=("Arial", 12),
            bg=theme['card_background'],
            fg=theme['text_primary'],
            justify='left',
            wraplength=500
        )
        section_content.pack(anchor='w')
        
        section_frame.pack(fill='x', pady=5)
        return section_frame
    
    def _add_step_list(self, steps, theme=None):
        """添加步骤列表"""
        if theme is None:
            theme = self.theme_manager.get_current_theme()
        
        steps_frame = tk.Frame(
            self.widgets['content_frame_inner'],
            bg=theme['card_background'],
            pady=5
        )
        
        for i, step in enumerate(steps):
            step_item = tk.Frame(
                steps_frame,
                bg=theme['card_background'],
                pady=5
            )
            
            step_number = tk.Label(
                step_item,
                text=f"{i+1}.",
                font=("Arial", 12, "bold"),
                bg=theme['card_background'],
                fg=theme['primary_background'],
                width=2,
                anchor='e'
            )
            
            step_text = tk.Label(
                step_item,
                text=step,
                font=("Arial", 12),
                bg=theme['card_background'],
                fg=theme['text_primary'],
                justify='left',
                wraplength=480
            )
            
            step_number.pack(side=tk.LEFT, padx=(0, 10))
            step_text.pack(side=tk.LEFT, fill='x', expand=True, anchor='w')
            
            step_item.pack(fill='x')
        
        steps_frame.pack(fill='x', pady=5, padx=20)
        return steps_frame
    
    def _add_button(self, text, command, theme=None):
        """添加按钮"""
        if theme is None:
            theme = self.theme_manager.get_current_theme()
        
        button = tk.Button(
            self.widgets['content_frame_inner'],
            text=text,
            font=("Arial", 12),
            bg=theme['primary_background'],
            fg=theme['primary_text'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=command
        )
        
        button.pack(anchor='w', pady=10)
        return button
    
    def _create_getting_started_content(self):
        """创建入门指南内容"""
        theme = self.theme_manager.get_current_theme()
        
        welcome_text = """
欢迎使用我们的应用！本指南将帮助您快速上手，了解系统的基本功能和操作方法。
跟随以下步骤，您将能够在短时间内掌握系统的核心功能。
        """
        
        self._add_section("欢迎", welcome_text, theme)
        
        steps = [
            "创建并验证您的账户。填写个人资料并设置安全选项。",
            "浏览仪表盘，熟悉界面布局和各个功能模块。",
            "了解交易中心的基本操作，包括买入和卖出资产。",
            "学习如何使用数据分析工具来跟踪和分析您的交易数据。",
            "探索更多高级功能，如API接口和自动化交易策略。"
        ]
        
        self._add_section("快速入门步骤", "", theme)
        self._add_step_list(steps, theme)
        
        tips_text = """
• 定期查看仪表盘获取系统概览和重要通知
• 使用搜索功能快速找到您需要的信息
• 设置通知选项以保持信息更新
• 经常查看帮助中心了解新功能和使用技巧
        """
        
        self._add_section("使用技巧", tips_text, theme)
        
        self._add_button("查看视频教程", self._scroll_to_videos, theme)
    
    def _create_account_content(self):
        """创建账户管理内容"""
        theme = self.theme_manager.get_current_theme()
        
        intro_text = """
账户管理模块允许您管理个人信息、安全设置和通知偏好。保持您的账户信息更新对于系统的安全和正常使用至关重要。
        """
        
        self._add_section("账户管理概述", intro_text, theme)
        
        profile_text = """
在"个人资料"页面，您可以更新以下信息：
• 个人基本信息（用户名、真实姓名等）
• 联系方式（电子邮箱、手机号码）
• 账户头像
• 身份验证文件
        """
        
        self._add_section("个人资料管理", profile_text, theme)
        
        security_text = """
安全是我们的首要考虑因素。我们建议您：
• 使用强密码并定期更换
• 启用两因素认证
• 定期检查账户活动日志
• 不要在公共场所登录账户
• 不要将账户信息分享给他人
        """
        
        self._add_section("安全建议", security_text, theme)
        
        notification_text = """
您可以在"通知设置"中自定义接收的通知类型：
• 交易确认通知
• 安全警报
• 市场动态通知
• 促销信息
        """
        
        self._add_section("通知管理", notification_text, theme)
        
        self._add_button("前往账户设置", lambda: self.controller.show_frame("ProfileView"), theme)
    
    def _create_trading_content(self):
        """创建交易指南内容"""
        theme = self.theme_manager.get_current_theme()
        
        intro_text = """
交易中心是系统的核心功能，允许您买卖各种资产。本指南将帮助您了解如何进行交易、管理订单和监控市场。
        """
        
        self._add_section("交易中心概述", intro_text, theme)
        
        steps = [
            "在交易中心页面，浏览可用资产列表。",
            "选择您想要交易的资产。",
            "选择交易类型：买入或卖出。",
            "输入您想要交易的数量。",
            "确认交易详情，包括总金额。",
            "点击"确认交易"按钮提交您的订单。",
            "查看交易确认信息和收据。"
        ]
        
        self._add_section("如何进行交易", "", theme)
        self._add_step_list(steps, theme)
        
        tips_text = """
• 交易前请务必了解市场状况和资产价格走势
• 使用限价单来控制买入或卖出价格
• 设置止损单来限制潜在损失
• 不要将所有资金投入单一资产
• 定期查看您的交易历史和表现
        """
        
        self._add_section("交易技巧", tips_text, theme)
        
        self._add_button("前往交易中心", lambda: self.controller.show_frame("TradingView"), theme)
    
    def _create_security_content(self):
        """创建安全设置内容"""
        theme = self.theme_manager.get_current_theme()
        
        intro_text = """
保护您的账户安全是我们的首要任务。本指南将介绍系统提供的安全功能以及如何配置这些功能以最大限度地保护您的账户。
        """
        
        self._add_section("安全概述", intro_text, theme)
        
        password_text = """
强密码是保护账户的第一道防线。一个强密码应该：
• 至少8个字符长度
• 包含大小写字母、数字和特殊字符
• 避免使用常见词汇和个人信息
• 对不同网站使用不同密码
• 定期更换密码（建议每3个月）
        """
        
        self._add_section("密码安全", password_text, theme)
        
        two_factor_text = """
两因素认证(2FA)为您的账户增添了额外的安全层。启用2FA后，登录时除了密码，您还需要提供第二个验证因素，通常是手机验证码或认证应用生成的代码。
        """
        
        self._add_section("两因素认证", two_factor_text, theme)
        
        steps = [
            "进入"账户设置"页面。",
            "选择"安全设置"选项卡。",
            "找到"两因素认证"选项并点击"启用"。",
            "选择您偏好的认证方式（短信或认证应用）。",
            "按照屏幕提示完成设置。",
            "保存备用恢复码以防丢失访问方式。"
        ]
        
        self._add_step_list(steps, theme)
        
        activity_text = """
定期检查您的账户活动日志，查找任何可疑活动。如果发现未经授权的登录或活动，请立即联系客服并更改密码。
        """
        
        self._add_section("活动监控", activity_text, theme)
        
        self._add_button("前往安全设置", lambda: self.controller.show_frame("ProfileView"), theme)