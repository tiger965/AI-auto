# ui/components/theme_manager.py
"""
主题管理组件

这个组件负责管理应用程序的主题系统，提供主题切换、自定义和动画效果。
它实现了以下功能：
1. 定义基础主题（浅色、深色等）
2. 加载和保存自定义主题
3. 提供动态切换主题的接口
4. 主题切换动画效果
5. 支持主题事件监听器

设计理念:
- 创造有温度、有灵魂的界面体验，通过颜色、字体和动画传递情感
- 所有颜色变化都有平滑的过渡效果
- 支持用户个性化定制，使界面更具个人特色
"""

import tkinter as tk
import json
import os
import time
import threading
import colorsys

class ThemeManager:
    """主题管理器，负责管理应用的视觉主题和风格"""
    
    def __init__(self, config_dir=None):
        """
        初始化主题管理器
        
        Args:
            config_dir: 配置文件目录，默认为用户目录下的 .ai_assistant
        """
        # 设置配置目录
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".ai_assistant")
        self.themes_dir = os.path.join(self.config_dir, "themes")
        
        # 确保目录存在
        os.makedirs(self.themes_dir, exist_ok=True)
        
        # 初始化变量
        self.listeners = []  # 主题变化监听器列表
        self.current_theme_name = "light"  # 默认主题
        self.animation_in_progress = False  # 动画状态标志
        
        # 定义内置主题
        self._define_built_in_themes()
        
        # 加载自定义主题
        self._load_custom_themes()
        
        # 加载用户首选项
        self._load_preferences()
    
    def _define_built_in_themes(self):
        """定义内置主题"""
        self.themes = {
            # 浅色主题 - 清爽明亮的设计
            "light": {
                "meta": {
                    "name": "浅色主题",
                    "description": "清爽明亮的默认浅色主题",
                    "built_in": True,
                    "version": "1.0"
                },
                "colors": {
                    # 品牌颜色
                    "primary": "#3355ff",            # 主色调
                    "primary_light": "#6681ff",      # 主色调亮色版
                    "primary_dark": "#0033cc",       # 主色调暗色版
                    "secondary": "#6c757d",          # 次要颜色
                    
                    # 功能颜色
                    "success": "#4caf50",            # 成功
                    "info": "#2196f3",               # 信息
                    "warning": "#ff9800",            # 警告
                    "danger": "#f44336",             # 危险
                    
                    # 背景颜色
                    "background": "#f5f5f7",         # 应用背景
                    "surface": "#ffffff",            # 卡片/面板背景
                    "surface_variant": "#f0f0f5",    # 次要面板背景
                    
                    # 文本颜色
                    "text": "#333333",               # 主要文本
                    "text_secondary": "#666666",     # 次要文本
                    "text_tertiary": "#888888",      # 第三级文本
                    "text_disabled": "#aaaaaa",      # 禁用文本
                    
                    # 边框和分隔线
                    "border": "#e0e0e0",             # 边框
                    "divider": "#eeeeee",            # 分隔线
                    
                    # 状态颜色
                    "hover": "#f0f0f5",              # 悬停状态
                    "active": "#e8e8ff",             # 活动状态
                    "selected": "#ebefff",           # 选中状态
                    "disabled": "#cccccc",           # 禁用状态
                    
                    # 特殊效果
                    "shadow": "rgba(0, 0, 0, 0.1)",  # 阴影效果
                    "overlay": "rgba(0, 0, 0, 0.5)"  # 覆盖层
                },
                "fonts": {
                    "family": {
                        "primary": "Helvetica, Arial, sans-serif",
                        "secondary": "Georgia, serif",
                        "monospace": "Consolas, 'Courier New', monospace"
                    },
                    "weight": {
                        "light": "300",
                        "regular": "400",
                        "medium": "500",
                        "semibold": "600",
                        "bold": "700"
                    },
                    "size": {
                        "xs": 10,
                        "sm": 12,
                        "md": 14,
                        "lg": 16,
                        "xl": 18,
                        "2xl": 20,
                        "3xl": 24,
                        "4xl": 30,
                        "5xl": 36
                    }
                },
                "spacing": {
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32,
                    "2xl": 48,
                    "3xl": 64
                },
                "radius": {
                    "none": 0,
                    "sm": 4,
                    "md": 8,
                    "lg": 16,
                    "xl": 24,
                    "full": 9999
                },
                "animation": {
                    "duration": {
                        "fast": 150,
                        "normal": 300,
                        "slow": 500
                    },
                    "easing": {
                        "linear": "linear",
                        "ease": "ease",
                        "ease_in": "ease-in",
                        "ease_out": "ease-out",
                        "ease_in_out": "ease-in-out"
                    }
                },
                "effects": {
                    "shadow": {
                        "sm": "0 1px 3px rgba(0,0,0,0.1)",
                        "md": "0 4px 6px rgba(0,0,0,0.1)",
                        "lg": "0 10px 15px rgba(0,0,0,0.1)",
                        "xl": "0 20px 25px rgba(0,0,0,0.1)"
                    },
                    "transition": {
                        "color": "color 0.3s ease",
                        "background": "background-color 0.3s ease",
                        "transform": "transform 0.3s ease",
                        "opacity": "opacity 0.3s ease",
                        "all": "all 0.3s ease"
                    }
                }
            },
            
            # 深色主题 - 适合夜间使用
            "dark": {
                "meta": {
                    "name": "深色主题",
                    "description": "低亮度的暗色主题，减少眼睛疲劳",
                    "built_in": True,
                    "version": "1.0"
                },
                "colors": {
                    # 品牌颜色
                    "primary": "#7f9eff",            # 主色调
                    "primary_light": "#a0b9ff",      # 主色调亮色版
                    "primary_dark": "#5d7ce6",       # 主色调暗色版
                    "secondary": "#adb5bd",          # 次要颜色
                    
                    # 功能颜色
                    "success": "#81c784",            # 成功
                    "info": "#64b5f6",               # 信息
                    "warning": "#ffa726",            # 警告
                    "danger": "#e57373",             # 危险
                    
                    # 背景颜色
                    "background": "#1e1e2d",         # 应用背景
                    "surface": "#252536",            # 卡片/面板背景
                    "surface_variant": "#2a2a3d",    # 次要面板背景
                    
                    # 文本颜色
                    "text": "#e0e0e0",               # 主要文本
                    "text_secondary": "#a0a0a0",     # 次要文本
                    "text_tertiary": "#777777",      # 第三级文本
                    "text_disabled": "#555555",      # 禁用文本
                    
                    # 边框和分隔线
                    "border": "#2c2c45",             # 边框
                    "divider": "#333345",            # 分隔线
                    
                    # 状态颜色
                    "hover": "#2a2a3d",              # 悬停状态
                    "active": "#2c2c45",             # 活动状态
                    "selected": "#303052",           # 选中状态
                    "disabled": "#555555",           # 禁用状态
                    
                    # 特殊效果
                    "shadow": "rgba(0, 0, 0, 0.3)",  # 阴影效果
                    "overlay": "rgba(0, 0, 0, 0.7)"  # 覆盖层
                },
                "fonts": {
                    "family": {
                        "primary": "Helvetica, Arial, sans-serif",
                        "secondary": "Georgia, serif",
                        "monospace": "Consolas, 'Courier New', monospace"
                    },
                    "weight": {
                        "light": "300",
                        "regular": "400",
                        "medium": "500",
                        "semibold": "600",
                        "bold": "700"
                    },
                    "size": {
                        "xs": 10,
                        "sm": 12,
                        "md": 14,
                        "lg": 16,
                        "xl": 18,
                        "2xl": 20,
                        "3xl": 24,
                        "4xl": 30,
                        "5xl": 36
                    }
                },
                "spacing": {
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32,
                    "2xl": 48,
                    "3xl": 64
                },
                "radius": {
                    "none": 0,
                    "sm": 4,
                    "md": 8,
                    "lg": 16,
                    "xl": 24,
                    "full": 9999
                },
                "animation": {
                    "duration": {
                        "fast": 150,
                        "normal": 300,
                        "slow": 500
                    },
                    "easing": {
                        "linear": "linear",
                        "ease": "ease",
                        "ease_in": "ease-in",
                        "ease_out": "ease-out",
                        "ease_in_out": "ease-in-out"
                    }
                },
                "effects": {
                    "shadow": {
                        "sm": "0 1px 3px rgba(0,0,0,0.3)",
                        "md": "0 4px 6px rgba(0,0,0,0.3)",
                        "lg": "0 10px 15px rgba(0,0,0,0.3)",
                        "xl": "0 20px 25px rgba(0,0,0,0.3)"
                    },
                    "transition": {
                        "color": "color 0.3s ease",
                        "background": "background-color 0.3s ease",
                        "transform": "transform 0.3s ease",
                        "opacity": "opacity 0.3s ease",
                        "all": "all 0.3s ease"
                    }
                }
            },
            
            # 柔和蓝色主题 - 舒适的观感
            "soft_blue": {
                "meta": {
                    "name": "柔蓝主题",
                    "description": "舒适、柔和的蓝色调主题",
                    "built_in": True,
                    "version": "1.0"
                },
                "colors": {
                    # 品牌颜色
                    "primary": "#5b9bd5",            # 主色调
                    "primary_light": "#78b0e6",      # 主色调亮色版
                    "primary_dark": "#4080bf",       # 主色调暗色版
                    "secondary": "#8c8c8c",          # 次要颜色
                    
                    # 功能颜色
                    "success": "#70ad47",            # 成功
                    "info": "#4bacc6",               # 信息
                    "warning": "#f9a825",            # 警告
                    "danger": "#c55a11",             # 危险
                    
                    # 背景颜色
                    "background": "#f2f7fb",         # 应用背景
                    "surface": "#ffffff",            # 卡片/面板背景
                    "surface_variant": "#edf5fc",    # 次要面板背景
                    
                    # 文本颜色
                    "text": "#2e2e2e",               # 主要文本
                    "text_secondary": "#4e4e4e",     # 次要文本
                    "text_tertiary": "#767676",      # 第三级文本
                    "text_disabled": "#9e9e9e",      # 禁用文本
                    
                    # 边框和分隔线
                    "border": "#d9e5f1",             # 边框
                    "divider": "#e6eff8",            # 分隔线
                    
                    # 状态颜色
                    "hover": "#e6f0fa",              # 悬停状态
                    "active": "#d4e6f6",             # 活动状态
                    "selected": "#c2dbf2",           # 选中状态
                    "disabled": "#d9d9d9",           # 禁用状态
                    
                    # 特殊效果
                    "shadow": "rgba(91, 155, 213, 0.15)",  # 阴影效果
                    "overlay": "rgba(91, 155, 213, 0.5)"   # 覆盖层
                },
                "fonts": {
                    "family": {
                        "primary": "Helvetica, Arial, sans-serif",
                        "secondary": "Georgia, serif",
                        "monospace": "Consolas, 'Courier New', monospace"
                    },
                    "weight": {
                        "light": "300",
                        "regular": "400",
                        "medium": "500",
                        "semibold": "600",
                        "bold": "700"
                    },
                    "size": {
                        "xs": 10,
                        "sm": 12,
                        "md": 14,
                        "lg": 16,
                        "xl": 18,
                        "2xl": 20,
                        "3xl": 24,
                        "4xl": 30,
                        "5xl": 36
                    }
                },
                "spacing": {
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32,
                    "2xl": 48,
                    "3xl": 64
                },
                "radius": {
                    "none": 0,
                    "sm": 4,
                    "md": 8,
                    "lg": 16,
                    "xl": 24,
                    "full": 9999
                },
                "animation": {
                    "duration": {
                        "fast": 150,
                        "normal": 300,
                        "slow": 500
                    },
                    "easing": {
                        "linear": "linear",
                        "ease": "ease",
                        "ease_in": "ease-in",
                        "ease_out": "ease-out",
                        "ease_in_out": "ease-in-out"
                    }
                },
                "effects": {
                    "shadow": {
                        "sm": "0 2px 5px rgba(91, 155, 213, 0.1)",
                        "md": "0 4px 10px rgba(91, 155, 213, 0.1)",
                        "lg": "0 8px 15px rgba(91, 155, 213, 0.1)",
                        "xl": "0 15px 25px rgba(91, 155, 213, 0.1)"
                    },
                    "transition": {
                        "color": "color 0.3s ease",
                        "background": "background-color 0.3s ease",
                        "transform": "transform 0.3s ease",
                        "opacity": "opacity 0.3s ease",
                        "all": "all 0.3s ease"
                    }
                }
            },
            
            # 自然绿色主题 - 以大自然为灵感
            "nature": {
                "meta": {
                    "name": "自然主题",
                    "description": "以大自然为灵感的绿色主题",
                    "built_in": True,
                    "version": "1.0"
                },
                "colors": {
                    # 品牌颜色
                    "primary": "#4caf50",            # 主色调
                    "primary_light": "#80e27e",      # 主色调亮色版
                    "primary_dark": "#087f23",       # 主色调暗色版
                    "secondary": "#78909c",          # 次要颜色
                    
                    # 功能颜色
                    "success": "#66bb6a",            # 成功
                    "info": "#4fc3f7",               # 信息
                    "warning": "#ffb74d",            # 警告
                    "danger": "#e57373",             # 危险
                    
                    # 背景颜色
                    "background": "#f1f8e9",         # 应用背景
                    "surface": "#ffffff",            # 卡片/面板背景
                    "surface_variant": "#edf7e4",    # 次要面板背景
                    
                    # 文本颜色
                    "text": "#33691e",               # 主要文本
                    "text_secondary": "#558b2f",     # 次要文本
                    "text_tertiary": "#689f38",      # 第三级文本
                    "text_disabled": "#9e9d24",      # 禁用文本
                    
                    # 边框和分隔线
                    "border": "#c5e1a5",             # 边框
                    "divider": "#dcedc8",            # 分隔线
                    
                    # 状态颜色
                    "hover": "#e8f5e9",              # 悬停状态
                    "active": "#c8e6c9",             # 活动状态
                    "selected": "#a5d6a7",           # 选中状态
                    "disabled": "#f1f8e9",           # 禁用状态
                    
                    # 特殊效果
                    "shadow": "rgba(76, 175, 80, 0.15)",  # 阴影效果
                    "overlay": "rgba(76, 175, 80, 0.5)"   # 覆盖层
                },
                "fonts": {
                    "family": {
                        "primary": "Helvetica, Arial, sans-serif",
                        "secondary": "Georgia, serif",
                        "monospace": "Consolas, 'Courier New', monospace"
                    },
                    "weight": {
                        "light": "300",
                        "regular": "400",
                        "medium": "500",
                        "semibold": "600",
                        "bold": "700"
                    },
                    "size": {
                        "xs": 10,
                        "sm": 12,
                        "md": 14,
                        "lg": 16,
                        "xl": 18,
                        "2xl": 20,
                        "3xl": 24,
                        "4xl": 30,
                        "5xl": 36
                    }
                },
                "spacing": {
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32,
                    "2xl": 48,
                    "3xl": 64
                },
                "radius": {
                    "none": 0,
                    "sm": 4,
                    "md": 8,
                    "lg": 16,
                    "xl": 24,
                    "full": 9999
                },
                "animation": {
                    "duration": {
                        "fast": 150,
                        "normal": 300,
                        "slow": 500
                    },
                    "easing": {
                        "linear": "linear",
                        "ease": "ease",
                        "ease_in": "ease-in",
                        "ease_out": "ease-out",
                        "ease_in_out": "ease-in-out"
                    }
                },
                "effects": {
                    "shadow": {
                        "sm": "0 2px 5px rgba(76, 175, 80, 0.1)",
                        "md": "0 4px 10px rgba(76, 175, 80, 0.1)",
                        "lg": "0 8px 15px rgba(76, 175, 80, 0.1)",
                        "xl": "0 15px 25px rgba(76, 175, 80, 0.1)"
                    },
                    "transition": {
                        "color": "color 0.3s ease",
                        "background": "background-color 0.3s ease",
                        "transform": "transform 0.3s ease",
                        "opacity": "opacity 0.3s ease",
                        "all": "all 0.3s ease"
                    }
                }
            }
        }
    
    def _load_custom_themes(self):
        """加载自定义主题"""
        try:
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_path = os.path.join(self.themes_dir, filename)
                    try:
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                        
                        # 验证主题数据结构
                        if self._validate_theme(theme_data):
                            # 获取主题ID（文件名去掉扩展名）
                            theme_id = os.path.splitext(filename)[0]
                            # 确保主题标记为非内置
                            if "meta" not in theme_data:
                                theme_data["meta"] = {}
                            theme_data["meta"]["built_in"] = False
                            # 添加到主题字典
                            self.themes[theme_id] = theme_data
                    except Exception as e:
                        print(f"加载主题文件 {filename} 时出错: {e}")
        except Exception as e:
            print(f"加载自定义主题时出错: {e}")
    
    def _validate_theme(self, theme_data):
        """
        验证主题数据结构是否合法
        
        Args:
            theme_data: 要验证的主题数据
            
        Returns:
            bool: 是否通过验证
        """
        # 基本结构验证
        required_sections = ["colors", "fonts", "spacing", "radius", "animation", "effects"]
        for section in required_sections:
            if section not in theme_data:
                print(f"主题验证失败: 缺少必需部分 '{section}'")
                return False
        
        # 颜色验证
        essential_colors = ["primary", "background", "surface", "text"]
        for color in essential_colors:
            if color not in theme_data["colors"]:
                print(f"主题验证失败: 缺少必需颜色 '{color}'")
                return False
        
        return True
    
    def _load_preferences(self):
        """加载用户主题首选项"""
        prefs_path = os.path.join(self.config_dir, "preferences.json")
        try:
            if os.path.exists(prefs_path):
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    
                # 获取保存的主题设置
                if "theme" in prefs and prefs["theme"] in self.themes:
                    self.current_theme_name = prefs["theme"]
        except Exception as e:
            print(f"加载主题首选项时出错: {e}")
    
    def _save_preferences(self):
        """保存用户主题首选项"""
        prefs_path = os.path.join(self.config_dir, "preferences.json")
        try:
            # 读取现有首选项
            prefs = {}
            if os.path.exists(prefs_path):
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
            
            # 更新主题设置
            prefs["theme"] = self.current_theme_name
            
            # 保存首选项
            with open(prefs_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存主题首选项时出错: {e}")
    
    def get_theme_list(self):
        """
        获取所有可用主题的列表
        
        Returns:
            list: 主题信息列表，每项包含id和name
        """
        theme_list = []
        for theme_id, theme in self.themes.items():
            name = theme.get("meta", {}).get("name", theme_id)
            description = theme.get("meta", {}).get("description", "")
            built_in = theme.get("meta", {}).get("built_in", False)
            
            theme_list.append({
                "id": theme_id,
                "name": name,
                "description": description,
                "built_in": built_in
            })
        
        # 先显示内置主题，再显示自定义主题，按名称排序
        return sorted(theme_list, key=lambda x: (not x["built_in"], x["name"]))
    
    def get_current_theme(self):
        """
        获取当前主题数据
        
        Returns:
            dict: 当前主题的完整数据
        """
        return self.themes.get(self.current_theme_name, self.themes["light"])
    
    def get_current_theme_name(self):
        """
        获取当前主题名称
        
        Returns:
            str: 当前主题的ID
        """
        return self.current_theme_name
    
    def get_color(self, color_key):
        """
        获取指定颜色值
        
        Args:
            color_key: 颜色键名
            
        Returns:
            str: 颜色值
        """
        theme = self.get_current_theme()
        return theme["colors"].get(color_key, "#000000")
    
    def get_font(self, family_key="primary", size_key="md", weight_key="regular"):
        """
        获取字体设置
        
        Args:
            family_key: 字体族键名
            size_key: 字体大小键名
            weight_key: 字体粗细键名
            
        Returns:
            tuple: (字体族, 字体大小, 字体粗细)
        """
        theme = self.get_current_theme()
        family = theme["fonts"]["family"].get(family_key, "Helvetica")
        size = theme["fonts"]["size"].get(size_key, 14)
        weight = theme["fonts"]["weight"].get(weight_key, "400")
        
        return (family, size, weight)
    
    def get_spacing(self, key="md"):
        """
        获取间距值
        
        Args:
            key: 间距键名
            
        Returns:
            int: 间距值
        """
        theme = self.get_current_theme()
        return theme["spacing"].get(key, 16)
    
    def get_radius(self, key="md"):
        """
        获取圆角半径
        
        Args:
            key: 圆角键名
            
        Returns:
            int: 圆角半径值
        """
        theme = self.get_current_theme()
        return theme["radius"].get(key, 8)
    
    def get_animation_duration(self, key="normal"):
        """
        获取动画持续时间
        
        Args:
            key: 持续时间键名
            
        Returns:
            int: 持续时间（毫秒）
        """
        theme = self.get_current_theme()
        return theme["animation"]["duration"].get(key, 300)
    
    def get_animation_easing(self, key="ease_out"):
        """
        获取动画缓动函数
        
        Args:
            key: 缓动函数键名
            
        Returns:
            str: 缓动函数名称
        """
        theme = self.get_current_theme()
        return theme["animation"]["easing"].get(key, "ease-out")
    
    def get_shadow(self, key="md"):
        """
        获取阴影效果
        
        Args:
            key: 阴影键名
            
        Returns:
            str: 阴影效果值
        """
        theme = self.get_current_theme()
        return theme["effects"]["shadow"].get(key, "0 4px 6px rgba(0,0,0,0.1)")
    
    def set_theme(self, theme_name, with_animation=True):
        """
        切换主题
        
        Args:
            theme_name: 主题名称
            with_animation: 是否使用动画效果
            
        Returns:
            bool: 是否成功切换
        """
        # 验证主题是否存在
        if theme_name not in self.themes:
            print(f"主题 '{theme_name}' 不存在")
            return False
        
        # 如果与当前主题相同，则不执行操作
        if theme_name == self.current_theme_name:
            return True
        
        # 获取旧主题和新主题
        old_theme = self.get_current_theme()
        new_theme = self.themes[theme_name]
        
        # 更新当前主题名称
        old_theme_name = self.current_theme_name
        self.current_theme_name = theme_name
        
        # 保存设置
        self._save_preferences()
        
        # 执行主题切换动画和通知监听器
        if with_animation and not self.animation_in_progress:
            self.animation_in_progress = True
            # 创建新线程执行动画，避免阻塞UI
            animation_thread = threading.Thread(
                target=self._animate_theme_change,
                args=(old_theme, new_theme, old_theme_name, theme_name)
            )
            animation_thread.daemon = True
            animation_thread.start()
        else:
            # 直接通知监听器
            self._notify_listeners(old_theme_name, theme_name, 1.0)
        
        return True
    
    def _animate_theme_change(self, old_theme, new_theme, old_theme_name, new_theme_name):
        """
        执行主题切换动画
        
        Args:
            old_theme: 旧主题数据
            new_theme: 新主题数据
            old_theme_name: 旧主题名称
            new_theme_name: 新主题名称
        """
        try:
            # 动画步数和时间
            steps = 20
            duration = self.get_animation_duration("normal") / 1000  # 转换为秒
            step_time = duration / steps
            
            # 执行动画
            for step in range(steps + 1):
                progress = step / steps
                # 使用缓动函数使动画更自然
                t = self._ease_in_out_quad(progress)
                
                # 通知监听器执行插值动画
                self._notify_listeners(old_theme_name, new_theme_name, t)
                
                # 等待下一帧
                time.sleep(step_time)
        
        except Exception as e:
            print(f"主题切换动画出错: {e}")
        finally:
            # 确保最终状态是正确的
            self._notify_listeners(old_theme_name, new_theme_name, 1.0)
            self.animation_in_progress = False
    
    def _ease_in_out_quad(self, t):
        """
        二次缓入缓出函数
        
        Args:
            t: 进度值 (0.0 到 1.0)
            
        Returns:
            float: 缓动后的进度值
        """
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    def interpolate_color(self, color1, color2, t):
        """
        在两个颜色之间插值
        
        Args:
            color1: 起始颜色 (十六进制)
            color2: 结束颜色 (十六进制)
            t: 插值比例 (0.0 到 1.0)
            
        Returns:
            str: 插值后的颜色 (十六进制)
        """
        # 解析颜色
        try:
            # 处理 rgba 格式
            if color1.startswith("rgba(") and color2.startswith("rgba("):
                rgba1 = [float(x.strip()) for x in color1[5:-1].split(",")]
                rgba2 = [float(x.strip()) for x in color2[5:-1].split(",")]
                
                r = int(rgba1[0] + (rgba2[0] - rgba1[0]) * t)
                g = int(rgba1[1] + (rgba2[1] - rgba1[1]) * t)
                b = int(rgba1[2] + (rgba2[2] - rgba1[2]) * t)
                a = rgba1[3] + (rgba2[3] - rgba1[3]) * t
                
                return f"rgba({r}, {g}, {b}, {a})"
            
            # 处理十六进制格式
            color1 = color1.lstrip("#")
            color2 = color2.lstrip("#")
            
            # 转换为RGB
            rgb1 = tuple(int(color1[i:i+2], 16) for i in (0, 2, 4))
            rgb2 = tuple(int(color2[i:i+2], 16) for i in (0, 2, 4))
            
            # 插值
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * t)
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * t)
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * t)
            
            # 转回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
            
        except Exception as e:
            print(f"颜色插值出错: {e}, color1={color1}, color2={color2}")
            return color2
    
    def add_listener(self, listener):
        """
        添加主题变化监听器
        
        Args:
            listener: 监听器函数，接收参数 (old_theme, new_theme, progress)
        """
        if callable(listener) and listener not in self.listeners:
            self.listeners.append(listener)
    
    def remove_listener(self, listener):
        """
        移除主题变化监听器
        
        Args:
            listener: 要移除的监听器函数
        """
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    def _notify_listeners(self, old_theme_name, new_theme_name, progress):
        """
        通知所有监听器
        
        Args:
            old_theme_name: 旧主题名称
            new_theme_name: 新主题名称
            progress: 过渡进度 (0.0 到 1.0)
        """
        for listener in self.listeners:
            try:
                listener(old_theme_name, new_theme_name, progress)
            except Exception as e:
                print(f"通知主题监听器出错: {e}")
    
    def create_custom_theme(self, theme_id, theme_data):
        """
        创建新的自定义主题
        
        Args:
            theme_id: 主题标识符
            theme_data: 主题数据
            
        Returns:
            bool: 是否创建成功
        """
        # 验证主题ID
        if not self._validate_theme_id(theme_id):
            print(f"无效的主题ID: '{theme_id}'")
            return False
        
        # 验证主题数据
        if not self._validate_theme(theme_data):
            return False
        
        # 确保有meta部分
        if "meta" not in theme_data:
            theme_data["meta"] = {}
        
        # 设置为非内置主题
        theme_data["meta"]["built_in"] = False
        
        # 保存主题
        theme_path = os.path.join(self.themes_dir, f"{theme_id}.json")
        try:
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            # 添加到内存中的主题列表
            self.themes[theme_id] = theme_data
            return True
        except Exception as e:
            print(f"保存自定义主题时出错: {e}")
            return False
    
    def update_custom_theme(self, theme_id, theme_data):
        """
        更新现有的自定义主题
        
        Args:
            theme_id: 主题标识符
            theme_data: 新的主题数据
            
        Returns:
            bool: 是否更新成功
        """
        # 检查主题是否存在
        if theme_id not in self.themes:
            print(f"主题 '{theme_id}' 不存在")
            return False
        
        # 检查是否为内置主题
        if self.themes[theme_id].get("meta", {}).get("built_in", False):
            print(f"无法修改内置主题 '{theme_id}'")
            return False
        
        # 验证主题数据
        if not self._validate_theme(theme_data):
            return False
        
        # 确保meta部分
        if "meta" not in theme_data:
            theme_data["meta"] = {}
        
        # 保留非内置标记
        theme_data["meta"]["built_in"] = False
        
        # 保存主题
        theme_path = os.path.join(self.themes_dir, f"{theme_id}.json")
        try:
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            # 更新内存中的主题
            self.themes[theme_id] = theme_data
            
            # 如果正在使用此主题，通知监听器
            if self.current_theme_name == theme_id:
                self._notify_listeners(theme_id, theme_id, 1.0)
            
            return True
        except Exception as e:
            print(f"更新自定义主题时出错: {e}")
            return False
    
    def delete_custom_theme(self, theme_id):
        """
        删除自定义主题
        
        Args:
            theme_id: 主题标识符
            
        Returns:
            bool: 是否删除成功
        """
        # 检查主题是否存在
        if theme_id not in self.themes:
            print(f"主题 '{theme_id}' 不存在")
            return False
        
        # 检查是否为内置主题
        if self.themes[theme_id].get("meta", {}).get("built_in", False):
            print(f"无法删除内置主题 '{theme_id}'")
            return False
        
        # 检查是否为当前主题
        if theme_id == self.current_theme_name:
            # 切换到默认主题
            self.set_theme("light", False)
        
        # 删除主题文件
        theme_path = os.path.join(self.themes_dir, f"{theme_id}.json")
        try:
            if os.path.exists(theme_path):
                os.remove(theme_path)
            
            # 从内存中移除
            del self.themes[theme_id]
            return True
        except Exception as e:
            print(f"删除自定义主题时出错: {e}")
            return False
    
    def _validate_theme_id(self, theme_id):
        """
        验证主题ID是否合法
        
        Args:
            theme_id: 主题标识符
            
        Returns:
            bool: 是否合法
        """
        # 检查是否为有效字符串
        if not isinstance(theme_id, str) or not theme_id:
            return False
        
        # 检查是否只包含字母、数字、下划线和连字符
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+$', theme_id):
            return False
        
        return True
    
    def create_theme_from_color(self, base_color, theme_id, theme_name, is_dark=False):
        """
        基于主色调创建新主题
        
        Args:
            base_color: 基础颜色（十六进制）
            theme_id: 主题标识符
            theme_name: 主题名称
            is_dark: 是否为深色主题
            
        Returns:
            bool: 是否创建成功
        """
        # 验证主题ID
        if not self._validate_theme_id(theme_id):
            print(f"无效的主题ID: '{theme_id}'")
            return False
        
        # 验证颜色格式
        try:
            # 去除#前缀
            base_color = base_color.lstrip('#')
            # 转换为RGB
            r, g, b = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            print(f"无效的颜色格式: '{base_color}'")
            return False
        
        # 创建基础模板
        template_name = "dark" if is_dark else "light"
        template = self.themes[template_name].copy()
        
        # 转换为HSL以便于计算
        h, s, l = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        # 创建衍生颜色
        colors = template["colors"].copy()
        
        # 设置主色调
        colors["primary"] = f"#{r:02x}{g:02x}{b:02x}"
        
        # 创建主色调的亮色和暗色变体
        if is_dark:
            # 深色主题中，亮色变体更亮
            primary_light_l = min(l * 1.3, 0.9)
            primary_dark_l = max(l * 0.7, 0.2)
        else:
            # 浅色主题中，暗色变体更暗
            primary_light_l = min(l * 1.2, 0.8)
            primary_dark_l = max(l * 0.6, 0.3)
        
        # 计算RGB值
        primary_light_rgb = colorsys.hls_to_rgb(h, primary_light_l, s)
        primary_dark_rgb = colorsys.hls_to_rgb(h, primary_dark_l, s)
        
        # 转换回十六进制
        r_light, g_light, b_light = [int(x * 255) for x in primary_light_rgb]
        r_dark, g_dark, b_dark = [int(x * 255) for x in primary_dark_rgb]
        
        colors["primary_light"] = f"#{r_light:02x}{g_light:02x}{b_light:02x}"
        colors["primary_dark"] = f"#{r_dark:02x}{g_dark:02x}{b_dark:02x}"
        
        # 调整活动和选中状态的颜色
        if is_dark:
            # 深色主题
            active_l = min(l * 0.8, 0.5)
            selected_l = min(l * 0.6, 0.4)
            hover_l = min(l * 0.7, 0.45)
        else:
            # 浅色主题
            active_l = max(l * 1.7, 0.9)
            selected_l = max(l * 1.8, 0.92)
            hover_l = max(l * 1.9, 0.95)
        
        # 计算RGB值
        active_rgb = colorsys.hls_to_rgb(h, active_l, min(s * 0.3, 0.3))
        selected_rgb = colorsys.hls_to_rgb(h, selected_l, min(s * 0.2, 0.2))
        hover_rgb = colorsys.hls_to_rgb(h, hover_l, min(s * 0.1, 0.1))
        
        # 转换回十六进制
        r_active, g_active, b_active = [int(x * 255) for x in active_rgb]
        r_selected, g_selected, b_selected = [int(x * 255) for x in selected_rgb]
        r_hover, g_hover, b_hover = [int(x * 255) for x in hover_rgb]
        
        colors["active"] = f"#{r_active:02x}{g_active:02x}{b_active:02x}"
        colors["selected"] = f"#{r_selected:02x}{g_selected:02x}{b_selected:02x}"
        colors["hover"] = f"#{r_hover:02x}{g_hover:02x}{b_hover:02x}"
        
        # 为阴影和覆盖层添加颜色
        if is_dark:
            colors["shadow"] = f"rgba({r_dark}, {g_dark}, {b_dark}, 0.3)"
            colors["overlay"] = f"rgba({r_dark}, {g_dark}, {b_dark}, 0.7)"
        else:
            colors["shadow"] = f"rgba({r}, {g}, {b}, 0.1)"
            colors["overlay"] = f"rgba({r}, {g}, {b}, 0.5)"
        
        # 更新模板
        template["colors"] = colors
        template["meta"] = {
            "name": theme_name,
            "description": f"基于颜色 #{base_color} 自动生成的{'深色' if is_dark else '浅色'}主题",
            "built_in": False,
            "version": "1.0"
        }
        
        # 保存主题
        return self.create_custom_theme(theme_id, template)
    
    def apply_to_widget(self, widget, old_theme_name, new_theme_name, progress=1.0):
        """
        将主题应用到Tkinter窗口部件
        
        Args:
            widget: Tkinter窗口部件
            old_theme_name: 旧主题名称
            new_theme_name: 新主题名称
            progress: 过渡进度 (0.0 到 1.0)
        """
        if not widget:
            return
        
        # 获取主题数据
        old_theme = self.themes.get(old_theme_name, self.themes["light"])
        new_theme = self.themes.get(new_theme_name, self.themes["light"])
        
        # 根据部件类型应用不同的样式
        widget_type = widget.__class__.__name__
        
        # 应用常规配置
        try:
            # 对于所有部件，处理背景色
            if "bg" in widget.config() or "background" in widget.config():
                bg_key = "background"
                # 根据部件类型选择合适的背景色
                if widget_type in ["Frame", "LabelFrame", "Canvas"]:
                    color_key = "background"
                elif widget_type in ["Button", "Entry", "Text", "Listbox"]:
                    color_key = "surface"
                else:
                    color_key = "background"
                
                # 插值颜色
                old_color = old_theme["colors"].get(color_key, "#ffffff")
                new_color = new_theme["colors"].get(color_key, "#ffffff")
                color = self.interpolate_color(old_color, new_color, progress)
                
                widget.config(**{bg_key: color})
            
            # 对于有前景色的部件
            if "fg" in widget.config() or "foreground" in widget.config():
                fg_key = "fg" if "fg" in widget.config() else "foreground"
                # 根据部件类型选择合适的文本色
                if widget_type in ["Label", "Button", "Entry", "Text"]:
                    color_key = "text"
                else:
                    color_key = "text"
                
                # 插值颜色
                old_color = old_theme["colors"].get(color_key, "#000000")
                new_color = new_theme["colors"].get(color_key, "#000000")
                color = self.interpolate_color(old_color, new_color, progress)
                
                widget.config(**{fg_key: color})
            
            # 对于有活动颜色的部件
            if "activebackground" in widget.config():
                old_color = old_theme["colors"].get("active", "#e8e8ff")
                new_color = new_theme["colors"].get("active", "#e8e8ff")
                color = self.interpolate_color(old_color, new_color, progress)
                
                widget.config(activebackground=color)
            
            # 对于有活动前景色的部件
            if "activeforeground" in widget.config():
                old_color = old_theme["colors"].get("text", "#000000")
                new_color = new_theme["colors"].get("text", "#000000")
                color = self.interpolate_color(old_color, new_color, progress)
                
                widget.config(activeforeground=color)
            
            # 对于有高亮颜色的部件
            if "highlightbackground" in widget.config():
                old_color = old_theme["colors"].get("border", "#e0e0e0")
                new_color = new_theme["colors"].get("border", "#e0e0e0")
                color = self.interpolate_color(old_color, new_color, progress)
                
                widget.config(highlightbackground=color)
            
            # 对于有高亮颜色的部件
            if "highlightcolor" in widget.config():
                old_color = old_theme["colors"].get("primary", "#3355ff")
                new_color = new_theme["colors"].get("primary", "#3355ff")
                color = self.interpolate_color(old_color, new_color, progress)
                
                widget.config(highlightcolor=color)
            
            # 对于特定部件的特殊处理
            if widget_type == "Button":
                # 按钮特殊处理
                if progress >= 1.0:  # 完成过渡后设置按钮边框
                    bd_color = new_theme["colors"].get("border", "#e0e0e0")
                    widget.config(bd=1, relief=tk.SOLID)
            
        except Exception as e:
            print(f"应用主题到部件 {widget_type} 时出错: {e}")
        
        # 递归处理子部件
        try:
            for child in widget.winfo_children():
                self.apply_to_widget(child, old_theme_name, new_theme_name, progress)
        except:
            pass

# 主题使用示例
if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    root.title("主题管理器演示")
    root.geometry("800x600")
    
    # 创建主题管理器
    theme_manager = ThemeManager()
    
    # 创建顶部栏
    top_frame = tk.Frame(root, height=60)
    top_frame.pack(fill=tk.X)
    
    # 标题
    title_label = tk.Label(top_frame, text="主题管理器演示", font=("Helvetica", 16, "bold"))
    title_label.pack(side=tk.LEFT, padx=20, pady=15)
    
    # 侧边栏
    sidebar = tk.Frame(root, width=200)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    
    # 主题列表
    themes_label = tk.Label(sidebar, text="可用主题", font=("Helvetica", 12, "bold"))
    themes_label.pack(pady=(20, 10))
    
    # 主内容区
    content = tk.Frame(root)
    content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 创建一些演示部件
    demo_frame = tk.LabelFrame(content, text="主题演示", padx=15, pady=15)
    demo_frame.pack(fill=tk.BOTH, expand=True)
    
    # 按钮区
    buttons_frame = tk.Frame(demo_frame)
    buttons_frame.pack(fill=tk.X, pady=10)
    
    tk.Button(buttons_frame, text="主要按钮", padx=10).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons_frame, text="次要按钮", padx=10).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons_frame, text="警告按钮", padx=10).pack(side=tk.LEFT, padx=5)
    
    # 文本框
    tk.Label(demo_frame, text="输入框:").pack(anchor=tk.W, pady=(10, 5))
    tk.Entry(demo_frame).pack(fill=tk.X, pady=5)
    
    # 列表框
    tk.Label(demo_frame, text="列表:").pack(anchor=tk.W, pady=(10, 5))
    listbox = tk.Listbox(demo_frame, height=5)
    listbox.pack(fill=tk.X, pady=5)
    for i in range(1, 11):
        listbox.insert(tk.END, f"列表项 {i}")
    
    # 文本区域
    tk.Label(demo_frame, text="文本区域:").pack(anchor=tk.W, pady=(10, 5))
    text = tk.Text(demo_frame, height=5)
    text.pack(fill=tk.X, pady=5)
    text.insert(tk.END, "这是一个文本区域示例。\n可以输入多行文本。")
    
    # 添加主题切换函数
    def on_theme_change(old_theme, new_theme, progress):
        # 应用主题到整个应用
        theme_manager.apply_to_widget(root, old_theme, new_theme, progress)
    
    # 注册主题变化监听器
    theme_manager.add_listener(on_theme_change)
    
    # 创建主题切换按钮
    theme_list = theme_manager.get_theme_list()
    
    for theme in theme_list:
        theme_id = theme["id"]
        theme_name = theme["name"]
        
        def make_theme_setter(theme_id):
            return lambda: theme_manager.set_theme(theme_id)
        
        theme_button = tk.Button(
            sidebar,
            text=theme_name,
            command=make_theme_setter(theme_id),
            width=15
        )
        theme_button.pack(pady=5)
    
    # 自动应用默认主题
    current_theme = theme_manager.get_current_theme_name()
    theme_manager.apply_to_widget(root, current_theme, current_theme, 1.0)
    
    # 启动主循环
    root.mainloop()