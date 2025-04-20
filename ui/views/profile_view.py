"""
用户资料视图模块
提供用户个人信息管理功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from . import BaseView


class ProfileView(BaseView):
    """用户资料视图，提供用户信息管理"""
    
    def __init__(self, parent, controller):
        self.widgets = {}  # 存储所有创建的小部件，便于主题应用
        super().__init__(parent, controller)
        
    def _create_widgets(self):
        """创建用户资料视图所有组件"""
        theme = self.theme_manager.get_current_theme()
        
        # 创建头部
        self.widgets['header_frame'] = tk.Frame(self, bg=theme['background'])
        self.widgets['title_label'] = tk.Label(
            self.widgets['header_frame'],
            text="个人资料",
            font=("Arial", 18, "bold"),
            bg=theme['background'],
            fg=theme['text_primary']
        )
        
        # 创建保存按钮
        self.widgets['save_button'] = tk.Button(
            self.widgets['header_frame'],
            text="保存更改",
            font=("Arial", 12),
            bg=theme['primary_background'],
            fg=theme['primary_text'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self._save_profile
        )
        
        # 创建主内容区，分为左右两栏
        self.widgets['content_frame'] = tk.Frame(self, bg=theme['background'])
        
        # 左侧 - 用户基本信息
        self.widgets['basic_info_frame'] = tk.Frame(
            self.widgets['content_frame'],
            bg=theme['card_background'],
            padx=20,
            pady=20
        )
        
        # 用户头像
        self.widgets['avatar_frame'] = tk.Frame(
            self.widgets['basic_info_frame'],
            bg=theme['card_background']
        )
        
        # 模拟头像（实际应用中这里会显示图像）
        self.widgets['avatar_placeholder'] = tk.Canvas(
            self.widgets['avatar_frame'],
            width=120,
            height=120,
            bg=theme['primary_background'],
            highlightthickness=0
        )
        
        # 添加用户首字母作为头像占位符
        self.widgets['avatar_placeholder'].create_text(
            60, 60,
            text="U",
            fill=theme['primary_text'],
            font=("Arial", 48, "bold")
        )
        
        # 更换头像按钮
        self.widgets['change_avatar_button'] = tk.Button(
            self.widgets['avatar_frame'],
            text="更换头像",
            font=("Arial", 10),
            bg=theme['button_background'],
            fg=theme['button_text'],
            relief=tk.FLAT,
            padx=10,
            pady=2,
            command=self._change_avatar
        )
        
        # 用户信息表单
        self.widgets['form_frame'] = tk.Frame(
            self.widgets['basic_info_frame'],
            bg=theme['card_background']
        )
        
        # 创建表单字段
        form_fields = [
            {"label": "用户名", "key": "username", "value": "user123"},
            {"label": "电子邮箱", "key": "email", "value": "user@example.com"},
            {"label": "真实姓名", "key": "real_name", "value": "张三"},
            {"label": "手机号码", "key": "phone", "value": "138****1234"},
        ]
        
        self.form_entries = {}
        for field in form_fields:
            field_frame = tk.Frame(
                self.widgets['form_frame'],
                bg=theme['card_background'],
                pady=5
            )
            
            label = tk.Label(
                field_frame,
                text=field['label'],
                font=("Arial", 12),
                width=10,
                anchor='w',
                bg=theme['card_background'],
                fg=theme['text_primary']
            )
            
            entry = tk.Entry(
                field_frame,
                font=("Arial", 12),
                bg=theme['input_background'],
                fg=theme['text_primary'],
                insertbackground=theme['text_primary'],
                relief=tk.FLAT,
                width=25
            )
            entry.insert(0, field['value'])
            
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.LEFT, padx=(10, 0), fill='x', expand=True)
            
            field_frame.pack(fill='x', pady=5)
            
            # 保存控件引用以便后续访问
            self.widgets[f"label_{field['key']}"] = label
            self.widgets[f"entry_{field['key']}"] = entry
            self.form_entries[field['key']] = entry
        
        # 右侧 - 安全与偏好设置
        self.widgets['settings_frame'] = tk.Frame(
            self.widgets['content_frame'],
            bg=theme['card_background'],
            padx=20,
            pady=20
        )
        
        # 安全设置
        self.widgets['security_label'] = tk.Label(
            self.widgets['settings_frame'],
            text="安全设置",
            font=("Arial", 14, "bold"),
            bg=theme['card_background'],
            fg=theme['text_primary']
        )
        
        # 修改密码区域
        self.widgets['password_frame'] = tk.Frame(
            self.widgets['settings_frame'],
            bg=theme['card_background'],
            pady=10
        )
        
        password_fields = [
            {"label": "当前密码", "key": "current_password"},
            {"label": "新密码", "key": "new_password"},
            {"label": "确认新密码", "key": "confirm_password"}
        ]
        
        for field in password_fields:
            field_frame = tk.Frame(
                self.widgets['password_frame'],
                bg=theme['card_background'],
                pady=5
            )
            
            label = tk.Label(
                field_frame,
                text=field['label'],
                font=("Arial", 12),
                width=10,
                anchor='w',
                bg=theme['card_background'],
                fg=theme['text_primary']
            )
            
            entry = tk.Entry(
                field_frame,
                font=("Arial", 12),
                bg=theme['input_background'],
                fg=theme['text_primary'],
                insertbackground=theme['text_primary'],
                relief=tk.FLAT,
                width=25,
                show="*"  # 密码字段显示为星号
            )
            
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.LEFT, padx=(10, 0), fill='x', expand=True)
            
            field_frame.pack(fill='x', pady=5)
            
            # 保存控件引用
            self.widgets[f"label_{field['key']}"] = label
            self.widgets[f"entry_{field['key']}"] = entry
        
        # 更改密码按钮
        self.widgets['change_password_button'] = tk.Button(
            self.widgets['password_frame'],
            text="更改密码",
            font=("Arial", 12),
            bg=theme['primary_background'],
            fg=theme['primary_text'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self._change_password
        )
        
        # 分隔线
        self.widgets['separator'] = ttk.Separator(
            self.widgets['settings_frame'], 
            orient='horizontal'
        )
        
        # 通知设置
        self.widgets['notifications_label'] = tk.Label(
            self.widgets['settings_frame'],
            text="通知设置",
            font=("Arial", 14, "bold"),
            bg=theme['card_background'],
            fg=theme['text_primary'],
            pady=10
        )
        
        notification_options = [
            {"text": "接收交易确认邮件", "var_name": "email_confirmation", "default": True},
            {"text": "接收安全警报", "var_name": "security_alerts", "default": True},
            {"text": "接收市场动态通知", "var_name": "market_updates", "default": False},
            {"text": "接收促销信息", "var_name": "promotions", "default": False}
        ]
        
        self.notification_vars = {}
        for option in notification_options:
            var = tk.BooleanVar(value=option['default'])
            self.notification_vars[option['var_name']] = var
            
            checkbutton = tk.Checkbutton(
                self.widgets['settings_frame'],
                text=option['text'],
                variable=var,
                font=("Arial", 12),
                bg=theme['card_background'],
                fg=theme['text_primary'],
                selectcolor=theme['card_background'],
                activebackground=theme['card_background'],
                padx=10,
                pady=5,
                command=lambda: self.sound_manager.play('click')
            )
            
            checkbutton.pack(anchor='w', pady=5)
            self.widgets[f"check_{option['var_name']}"] = checkbutton
        
        # 创建账户活动日志区域
        self.widgets['activity_frame'] = tk.Frame(
            self,
            bg=theme['card_background'],
            padx=20,
            pady=20
        )
        
        self.widgets['activity_label'] = tk.Label(
            self.widgets['activity_frame'],
            text="账户活动日志",
            font=("Arial", 14, "bold"),
            bg=theme['card_background'],
            fg=theme['text_primary']
        )
        
        # 创建活动日志表格
        self.widgets['logs_frame'] = tk.Frame(
            self.widgets['activity_frame'],
            bg=theme['card_background']
        )
        
        # 表格标题
        columns = ["时间", "活动", "IP地址", "状态"]
        self.widgets['log_header'] = tk.Frame(
            self.widgets['logs_frame'],
            bg=theme['card_background'],
            pady=10
        )
        
        for col in columns:
            header = tk.Label(
                self.widgets['log_header'],
                text=col,
                font=("Arial", 12, "bold"),
                bg=theme['card_background'],
                fg=theme['text_primary']
            )
            header.pack(side=tk.LEFT, fill='x', expand=True)
            self.widgets[f"header_{col}"] = header
        
        # 示例日志数据
        log_data = [
            {"time": "2023-05-20 10:23", "activity": "登录成功", "ip": "192.168.1.1", "status": "成功"},
            {"time": "2023-05-19 15:45", "activity": "修改密码", "ip": "192.168.1.1", "status": "成功"},
            {"time": "2023-05-18 08:30", "activity": "登录尝试", "ip": "203.0.113.0", "status": "失败"},
            {"time": "2023-05-15 14:20", "activity": "更新个人资料", "ip": "192.168.1.1", "status": "成功"},
        ]
        
        self.widgets['log_items'] = []
        for log in log_data:
            log_item = tk.Frame(
                self.widgets['logs_frame'],
                bg=theme['row_background'],
                padx=5,
                pady=8
            )
            
            for i, key in enumerate(["time", "activity", "ip", "status"]):
                text_color = theme['success_text'] if log['status'] == "成功" and key == "status" else \
                             theme['error_text'] if log['status'] == "失败" and key == "status" else \
                             theme['text_primary']
                
                item_label = tk.Label(
                    log_item,
                    text=log[key],
                    font=("Arial", 11),
                    bg=theme['row_background'],
                    fg=text_color
                )
                item_label.pack(side=tk.LEFT, fill='x', expand=True)
            
            self.widgets['log_items'].append(log_item)
            
            # 添加悬停效果
            log_item.bind("<Enter>", lambda e, f=log_item: self._on_item_hover(f, True, theme))
            log_item.bind("<Leave>", lambda e, f=log_item: self._on_item_hover(f, False, theme))
    
    def _layout_widgets(self):
        """布局所有控件"""
        # 布局头部
        self.widgets['header_frame'].pack(fill='x', padx=20, pady=(20, 10))
        self.widgets['title_label'].pack(side=tk.LEFT)
        self.widgets['save_button'].pack(side=tk.RIGHT)
        
        # 布局主内容区
        self.widgets['content_frame'].pack(fill='x', padx=20, pady=10)
        
        # 左侧用户基本信息
        self.widgets['basic_info_frame'].pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10))
        
        # 头像区域
        self.widgets['avatar_frame'].pack(pady=(0, 20))
        self.widgets['avatar_placeholder'].pack()
        self.widgets['change_avatar_button'].pack(pady=(10, 0))
        
        # 表单区域
        self.widgets['form_frame'].pack(fill='x', expand=True)
        
        # 右侧安全与偏好设置
        self.widgets['settings_frame'].pack(side=tk.RIGHT, fill='both', expand=True, padx=(10, 0))
        
        # 安全设置
        self.widgets['security_label'].pack(anchor='w')
        self.widgets['password_frame'].pack(fill='x')
        self.widgets['change_password_button'].pack(anchor='e', pady=(10, 0))
        
        # 分隔线
        self.widgets['separator'].pack(fill='x', pady=15)
        
        # 通知设置
        self.widgets['notifications_label'].pack(anchor='w')
        
        # 账户活动日志
        self.widgets['activity_frame'].pack(fill='both', expand=True, padx=20, pady=10)
        self.widgets['activity_label'].pack(anchor='w', pady=(0, 10))
        self.widgets['logs_frame'].pack(fill='both', expand=True)
        
        # 日志表头
        self.widgets['log_header'].pack(fill='x')
        
        # 日志项
        for log_item in self.widgets['log_items']:
            log_item.pack(fill='x', pady=2)
    
    def _on_item_hover(self, frame, is_hover, theme):
        """日志项悬停效果"""
        if is_hover:
            frame.configure(bg=theme['row_hover_background'])
            for widget in frame.winfo_children():
                widget.configure(bg=theme['row_hover_background'])
            self.sound_manager.play('hover')
        else:
            frame.configure(bg=theme['row_background'])
            for widget in frame.winfo_children():
                widget.configure(bg=theme['row_background'])
    
    def _change_avatar(self):
        """更换头像"""
        self.sound_manager.play('button_click')
        
        # 打开文件对话框
        filename = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg")]
        )
        
        if filename:
            # 在实际应用中，这里会处理头像更新逻辑
            messagebox.showinfo("头像更新", f"已选择图片: {os.path.basename(filename)}")
    
    def _change_password(self):
        """更改密码"""
        self.sound_manager.play('button_click')
        
        current_password = self.widgets['entry_current_password'].get()
        new_password = self.widgets['entry_new_password'].get()
        confirm_password = self.widgets['entry_confirm_password'].get()
        
        # 简单的密码验证
        if not current_password or not new_password or not confirm_password:
            messagebox.showerror("错误", "请填写所有密码字段")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("错误", "新密码和确认密码不匹配")
            return
        
        if len(new_password) < 8:
            messagebox.showerror("错误", "新密码长度必须至少为8个字符")
            return
        
        # 在实际应用中，这里会验证当前密码并更新密码
        messagebox.showinfo("成功", "密码已成功更改")
        
        # 清空密码字段
        self.widgets['entry_current_password'].delete(0, tk.END)
        self.widgets['entry_new_password'].delete(0, tk.END)
        self.widgets['entry_confirm_password'].delete(0, tk.END)
    
    def _save_profile(self):
        """保存用户资料"""
        self.sound_manager.play('confirm')
        
        # 获取表单数据
        profile_data = {}
        for key, entry in self.form_entries.items():
            profile_data[key] = entry.get()
        
        # 获取通知设置
        notification_settings = {}
        for key, var in self.notification_vars.items():
            notification_settings[key] = var.get()
        
        # 在实际应用中，这里会保存用户资料
        messagebox.showinfo("成功", "个人资料已成功更新")# 用户资料视图
