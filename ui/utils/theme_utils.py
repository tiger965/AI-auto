"""
主题处理工具模块 - Theme Utilities

这个模块提供了应用程序的主题管理功能，包括主题的加载、切换和自定义设置。
设计理念是创造有温度、有灵魂的界面体验，通过柔和的色彩过渡和情感化的视觉元素，
使用户在使用AI自动化工具时感受到温暖而非冰冷的技术感。

主要功能:
    - 主题管理（加载、保存、重置）
    - 主题切换（明亮/暗黑模式）
    - 主题自定义（色彩、字体、边框等）
    - 情境主题（根据时间、用户行为自动调整）
    - 主题导出和分享

作者: AI助手
日期: 2025-04-19
"""

import os
import json
import colorsys
from typing import Dict, Any, Optional, Tuple, List
import logging
from datetime import datetime
from pathlib import Path


# 配置日志
logger = logging.getLogger(__name__)


class ThemeManager:
    """主题管理器类，负责处理应用程序的所有主题相关操作"""
    
    # 默认主题配置
    DEFAULT_LIGHT_THEME = {
        "primary": "#4F6AF5",       # 主色调 - 温暖蓝色
        "secondary": "#7A5AF8",     # 次要色调 - 淡紫色
        "background": "#F8F9FC",    # 背景色 - 柔和白色
        "surface": "#FFFFFF",       # 表面色 - 纯白色
        "text": {
            "primary": "#333344",   # 主要文本 - 近黑色
            "secondary": "#65657A", # 次要文本 - 灰色
            "disabled": "#A5A5B8",  # 禁用文本 - 浅灰色
            "accent": "#4F6AF5"     # 强调文本 - 主色调
        },
        "border": {
            "color": "#E1E2EA",     # 边框颜色
            "radius": "8px"         # 边框圆角
        },
        "shadow": {
            "small": "0 2px 5px rgba(0, 0, 0, 0.05)",
            "medium": "0 4px 10px rgba(0, 0, 0, 0.07)",
            "large": "0 8px 20px rgba(0, 0, 0, 0.1)"
        },
        "animation": {
            "duration": "0.3s",     # 动画持续时间
            "curve": "ease-in-out"  # 动画曲线
        },
        "spacing": {
            "xs": "4px",
            "sm": "8px",
            "md": "16px",
            "lg": "24px",
            "xl": "32px"
        },
        "font": {
            "family": "'Inter', 'Segoe UI', system-ui, sans-serif",
            "size": {
                "xs": "12px",
                "sm": "14px",
                "md": "16px",
                "lg": "18px",
                "xl": "24px",
                "xxl": "32px"
            },
            "weight": {
                "normal": "400",
                "medium": "500",
                "bold": "600",
                "heavy": "700"
            }
        },
        "name": "清新光明",  # 主题名称 - 带有情感化的命名
        "description": "明亮温暖的日间主题，给人以清新舒适的感受",
        "mood": "peaceful", # 情绪标签
        "season": "spring"  # 季节灵感
    }
    
    # 默认暗色主题配置
    DEFAULT_DARK_THEME = {
        "primary": "#6E85FF",       # 主色调 - 亮蓝色
        "secondary": "#9D7CFF",     # 次要色调 - 亮紫色
        "background": "#1A1B23",    # 背景色 - 深灰色
        "surface": "#242530",       # 表面色 - 较深灰色
        "text": {
            "primary": "#F0F0F5",   # 主要文本 - 白色
            "secondary": "#C0C0CF", # 次要文本 - 浅灰色
            "disabled": "#7E7E94",  # 禁用文本 - 中灰色
            "accent": "#6E85FF"     # 强调文本 - 主色调
        },
        "border": {
            "color": "#38394A",     # 边框颜色
            "radius": "8px"         # 边框圆角
        },
        "shadow": {
            "small": "0 2px 5px rgba(0, 0, 0, 0.2)",
            "medium": "0 4px 10px rgba(0, 0, 0, 0.3)",
            "large": "0 8px 20px rgba(0, 0, 0, 0.4)"
        },
        "animation": {
            "duration": "0.3s",     # 动画持续时间
            "curve": "ease-in-out"  # 动画曲线
        },
        "spacing": {
            "xs": "4px",
            "sm": "8px",
            "md": "16px",
            "lg": "24px",
            "xl": "32px"
        },
        "font": {
            "family": "'Inter', 'Segoe UI', system-ui, sans-serif",
            "size": {
                "xs": "12px",
                "sm": "14px",
                "md": "16px",
                "lg": "18px",
                "xl": "24px",
                "xxl": "32px"
            },
            "weight": {
                "normal": "400",
                "medium": "500",
                "bold": "600",
                "heavy": "700"
            }
        },
        "name": "静谧星空",  # 主题名称 - 带有情感化的命名
        "description": "沉稳深邃的夜间主题，如同繁星点缀的夜空",
        "mood": "calm",    # 情绪标签
        "season": "night"  # 季节灵感
    }
    
    # 特殊主题 - 秋季主题示例
    SEASONAL_THEMES = {
        "autumn_breeze": {
            "primary": "#E07A5F",      # 橙红色
            "secondary": "#F2C14E",    # 金黄色
            "background": "#FDFBF7",   # 米色背景
            "surface": "#FFFFFF",
            "text": {
                "primary": "#2C363F",
                "secondary": "#596773",
                "disabled": "#A9B5C0",
                "accent": "#E07A5F"
            },
            "border": {
                "color": "#EDEAE2",
                "radius": "8px"
            },
            "name": "秋日微风",
            "description": "带来秋天温暖色彩的主题，让人想起落叶和金色阳光",
            "mood": "warm",
            "season": "autumn"
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化主题管理器
        
        参数:
            config_dir: 配置文件目录，如果为None则使用默认目录
        """
        if config_dir is None:
            # 默认配置目录是用户主目录下的.app_name目录
            self.config_dir = os.path.join(os.path.expanduser("~"), ".ai_automation")
        else:
            self.config_dir = config_dir
            
        # 确保配置目录存在
        os.makedirs(os.path.join(self.config_dir, "themes"), exist_ok=True)
        
        # 设置主题文件路径
        self.themes_file = os.path.join(self.config_dir, "themes", "user_themes.json")
        self.active_theme_file = os.path.join(self.config_dir, "themes", "active_theme.json")
        
        # 当前活动主题
        self.active_theme = {}
        
        # 用户自定义主题集合
        self.user_themes = {}
        
        # 加载主题
        self._load_themes()
        self._load_active_theme()
        
    def _load_themes(self) -> None:
        """加载用户自定义主题"""
        try:
            if os.path.exists(self.themes_file):
                with open(self.themes_file, 'r', encoding='utf-8') as f:
                    self.user_themes = json.load(f)
                logger.info(f"加载了 {len(self.user_themes)} 个用户自定义主题")
            else:
                logger.info("未找到用户主题文件，将使用默认主题")
                self._save_themes()  # 创建默认文件
        except Exception as e:
            logger.error(f"加载用户主题时出错: {e}")
            self.user_themes = {}
    
    def _save_themes(self) -> None:
        """保存用户自定义主题到文件"""
        try:
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_themes, f, ensure_ascii=False, indent=4)
            logger.info(f"保存了 {len(self.user_themes)} 个用户自定义主题")
        except Exception as e:
            logger.error(f"保存用户主题时出错: {e}")
    
    def _load_active_theme(self) -> None:
        """加载当前活动主题"""
        try:
            if os.path.exists(self.active_theme_file):
                with open(self.active_theme_file, 'r', encoding='utf-8') as f:
                    stored_theme = json.load(f)
                
                # 验证是否是有效的主题数据
                if self._is_valid_theme(stored_theme):
                    self.active_theme = stored_theme
                    logger.info(f"加载活动主题: {self.active_theme.get('name', '未命名主题')}")
                else:
                    logger.warning("存储的活动主题无效，将使用默认亮色主题")
                    self.active_theme = self.DEFAULT_LIGHT_THEME.copy()
                    self._save_active_theme()
            else:
                # 默认使用亮色主题
                self.active_theme = self.DEFAULT_LIGHT_THEME.copy()
                logger.info("未找到活动主题文件，使用默认亮色主题")
                self._save_active_theme()
        except Exception as e:
            logger.error(f"加载活动主题时出错: {e}")
            self.active_theme = self.DEFAULT_LIGHT_THEME.copy()
            self._save_active_theme()
    
    def _save_active_theme(self) -> None:
        """保存当前活动主题到文件"""
        try:
            with open(self.active_theme_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_theme, f, ensure_ascii=False, indent=4)
            logger.info(f"保存活动主题: {self.active_theme.get('name', '未命名主题')}")
        except Exception as e:
            logger.error(f"保存活动主题时出错: {e}")
    
    def _is_valid_theme(self, theme: Dict[str, Any]) -> bool:
        """
        检查主题数据是否有效
        
        参数:
            theme: 要检查的主题数据
        
        返回:
            bool: 是否是有效的主题数据
        """
        # 必须包含的基本键
        required_keys = ["primary", "background", "text"]
        return all(key in theme for key in required_keys)
    
    def get_theme(self, theme_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定ID的主题，如果未指定则返回当前活动主题
        
        参数:
            theme_id: 主题ID，如果为None则返回当前活动主题
        
        返回:
            Dict: 主题数据
        """
        if theme_id is None:
            return self.active_theme.copy()
        
        # 首先在用户自定义主题中查找
        if theme_id in self.user_themes:
            return self.user_themes[theme_id].copy()
        
        # 然后检查默认主题
        if theme_id == "light":
            return self.DEFAULT_LIGHT_THEME.copy()
        elif theme_id == "dark":
            return self.DEFAULT_DARK_THEME.copy()
        
        # 最后查找季节性主题
        if theme_id in self.SEASONAL_THEMES:
            return self.SEASONAL_THEMES[theme_id].copy()
        
        # 如果未找到，返回活动主题
        logger.warning(f"未找到主题 ID: {theme_id}，返回当前活动主题")
        return self.active_theme.copy()
    
    def set_active_theme(self, theme_id: str) -> Dict[str, Any]:
        """
        设置活动主题
        
        参数:
            theme_id: 主题ID
        
        返回:
            Dict: 设置的主题数据
        """
        theme = self.get_theme(theme_id)
        self.active_theme = theme
        self._save_active_theme()
        logger.info(f"设置活动主题: {theme.get('name', theme_id)}")
        return theme
    
    def toggle_dark_mode(self) -> Dict[str, Any]:
        """
        切换明暗模式
        
        返回:
            Dict: 切换后的主题数据
        """
        # 判断当前是否是深色模式
        is_dark = self._is_dark_theme(self.active_theme)
        
        if is_dark:
            # 如果当前是深色，切换到亮色
            new_theme = self.DEFAULT_LIGHT_THEME.copy()
        else:
            # 如果当前是亮色，切换到深色
            new_theme = self.DEFAULT_DARK_THEME.copy()
        
        self.active_theme = new_theme
        self._save_active_theme()
        logger.info(f"切换到{'亮色' if not is_dark else '深色'}模式: {new_theme.get('name')}")
        return new_theme
    
    def _is_dark_theme(self, theme: Dict[str, Any]) -> bool:
        """
        判断主题是否是深色模式
        
        参数:
            theme: 主题数据
        
        返回:
            bool: 是否是深色模式
        """
        # 提取背景色的RGB值
        bg_color = theme.get("background", "#FFFFFF")
        # 移除#前缀并转换为RGB
        bg_color = bg_color.lstrip("#")
        r, g, b = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
        
        # 计算亮度 (使用感知亮度公式: 0.299*R + 0.587*G + 0.114*B)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # 亮度低于0.5视为深色主题
        return luminance < 0.5
    
    def create_theme(self, theme_data: Dict[str, Any], theme_id: Optional[str] = None) -> str:
        """
        创建新的自定义主题
        
        参数:
            theme_data: 主题数据
            theme_id: 可选的主题ID，如果未提供则自动生成
        
        返回:
            str: 创建的主题ID
        """
        # 验证主题数据
        if not self._is_valid_theme(theme_data):
            raise ValueError("无效的主题数据，必须包含所有必需的主题属性")
        
        # 如果未提供ID，则使用主题名称和时间戳生成
        if theme_id is None:
            theme_name = theme_data.get("name", "自定义主题")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            theme_id = f"{theme_name.lower().replace(' ', '_')}_{timestamp}"
        
        # 保存主题
        self.user_themes[theme_id] = theme_data
        self._save_themes()
        logger.info(f"创建新主题: {theme_id} - {theme_data.get('name', '未命名主题')}")
        return theme_id
    
    def update_theme(self, theme_id: str, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新现有主题
        
        参数:
            theme_id: 主题ID
            theme_data: 新的主题数据
        
        返回:
            Dict: 更新后的主题数据
        """
        # 验证主题数据
        if not self._is_valid_theme(theme_data):
            raise ValueError("无效的主题数据，必须包含所有必需的主题属性")
        
        # 检查主题是否存在
        if theme_id not in self.user_themes:
            raise ValueError(f"主题 {theme_id} 不存在，无法更新")
        
        # 更新主题
        self.user_themes[theme_id] = theme_data
        
        # 如果更新的是当前活动主题，同时更新活动主题
        if theme_id == self.get_active_theme_id():
            self.active_theme = theme_data.copy()
            self._save_active_theme()
        
        self._save_themes()
        logger.info(f"更新主题: {theme_id} - {theme_data.get('name', '未命名主题')}")
        return theme_data
    
    def delete_theme(self, theme_id: str) -> bool:
        """
        删除自定义主题
        
        参数:
            theme_id: 主题ID
        
        返回:
            bool: 是否删除成功
        """
        # 检查是否是系统默认主题，不允许删除
        if theme_id in ["light", "dark"] or theme_id in self.SEASONAL_THEMES:
            logger.warning(f"尝试删除系统主题 {theme_id}，操作被拒绝")
            return False
        
        # 检查主题是否存在
        if theme_id not in self.user_themes:
            logger.warning(f"主题 {theme_id} 不存在，无法删除")
            return False
        
        # 如果删除的是当前活动主题，切换为默认亮色主题
        if theme_id == self.get_active_theme_id():
            self.active_theme = self.DEFAULT_LIGHT_THEME.copy()
            self._save_active_theme()
            logger.info(f"删除了活动主题，已切换到默认亮色主题")
        
        # 删除主题
        del self.user_themes[theme_id]
        self._save_themes()
        logger.info(f"删除主题: {theme_id}")
        return True
    
    def get_active_theme_id(self) -> str:
        """
        获取当前活动主题的ID
        
        返回:
            str: 活动主题ID，如果是默认主题则返回"light"或"dark"
        """
        # 比较活动主题与默认主题
        if self.active_theme == self.DEFAULT_LIGHT_THEME:
            return "light"
        elif self.active_theme == self.DEFAULT_DARK_THEME:
            return "dark"
        
        # 查找用户自定义主题
        for theme_id, theme_data in self.user_themes.items():
            if theme_data == self.active_theme:
                return theme_id
        
        # 查找季节性主题
        for theme_id, theme_data in self.SEASONAL_THEMES.items():
            if theme_data == self.active_theme:
                return theme_id
        
        # 如果无法确定，返回"unknown"
        return "unknown"
    
    def get_all_themes(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用主题
        
        返回:
            Dict: 所有主题的字典，键为主题ID，值为主题数据
        """
        all_themes = {
            "light": self.DEFAULT_LIGHT_THEME,
            "dark": self.DEFAULT_DARK_THEME,
            **self.SEASONAL_THEMES,
            **self.user_themes
        }
        return all_themes
    
    def export_theme(self, theme_id: str, file_path: str) -> bool:
        """
        导出主题到文件
        
        参数:
            theme_id: 主题ID
            file_path: 导出文件路径
        
        返回:
            bool: 是否导出成功
        """
        try:
            theme = self.get_theme(theme_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(theme, f, ensure_ascii=False, indent=4)
            logger.info(f"主题 {theme_id} 已导出到 {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出主题 {theme_id} 时出错: {e}")
            return False
    
    def import_theme(self, file_path: str, new_theme_id: Optional[str] = None) -> Optional[str]:
        """
        从文件导入主题
        
        参数:
            file_path: 导入文件路径
            new_theme_id: 可选的新主题ID
        
        返回:
            Optional[str]: 导入的主题ID，如果导入失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            # 验证主题数据
            if not self._is_valid_theme(theme_data):
                logger.error(f"文件 {file_path} 中的主题数据无效")
                return None
            
            # 创建主题
            return self.create_theme(theme_data, new_theme_id)
        except Exception as e:
            logger.error(f"从 {file_path} 导入主题时出错: {e}")
            return None
    
    def generate_theme_from_color(self, primary_color: str, is_dark: bool = False) -> Dict[str, Any]:
        """
        从主色调生成完整主题
        
        参数:
            primary_color: 主色调，十六进制格式，如"#4F6AF5"
            is_dark: 是否生成深色主题
        
        返回:
            Dict: 生成的主题数据
        """
        # 移除#前缀并转换为RGB
        color = primary_color.lstrip("#")
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        # 转换为HSL色彩空间
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        # 生成辅助色 - 调整色相
        secondary_h = (h + 0.1) % 1.0  # 在色相环上偏移
        secondary_rgb = colorsys.hls_to_rgb(secondary_h, l, s)
        secondary_color = "#{:02x}{:02x}{:02x}".format(
            int(secondary_rgb[0] * 255),
            int(secondary_rgb[1] * 255),
            int(secondary_rgb[2] * 255)
        )
        
        if is_dark:
            # 深色主题 - 基于DEFAULT_DARK_THEME修改颜色
            theme_template = self.DEFAULT_DARK_THEME.copy()
            theme_template["primary"] = primary_color
            theme_template["secondary"] = secondary_color
            theme_template["text"]["accent"] = primary_color
            
            # 自动生成名称
            color_name = self._get_color_name(h)
            theme_template["name"] = f"深邃{color_name}"
            theme_template["description"] = f"以{color_name}为主调的深色主题，给人沉稳而神秘的体验"
        else:
            # 亮色主题 - 基于DEFAULT_LIGHT_THEME修改颜色
            theme_template = self.DEFAULT_LIGHT_THEME.copy()
            theme_template["primary"] = primary_color
            theme_template["secondary"] = secondary_color
            theme_template["text"]["accent"] = primary_color
            
            # 自动生成名称
            color_name = self._get_color_name(h)
            theme_template["name"] = f"明亮{color_name}"
            theme_template["description"] = f"以{color_name}为主调的亮色主题，给人清新愉悦的感受"
        
        return theme_template
    
    def _get_color_name(self, hue: float) -> str:
        """
        根据色相值获取中文颜色名称
        
        参数:
            hue: 色相值，范围0-1
        
        返回:
            str: 颜色的中文名称
        """
        # 色相环分段，对应中文颜色名称
        color_names = [
            "红色", "橙红色", "橙色", "黄橙色", "黄色", "黄绿色",
            "绿色", "青绿色", "青色", "青蓝色", "蓝色", "蓝紫色",
            "紫色", "紫红色"
        ]
        
        # 将色相值(0-1)映射到颜色名称索引
        index = int(hue * len(color_names)) % len(color_names)
        return color_names[index]
    
    def get_css_variables(self, theme_id: Optional[str] = None) -> str:
        """
        将主题转换为CSS变量字符串，可直接用于样式设置
        
        参数:
            theme_id: 主题ID，如果为None则使用当前活动主题
        
        返回:
            str: CSS变量定义字符串
        """
        theme = self.get_theme(theme_id)
        css_vars = [":root {"]
        
        # 处理基本颜色
        for key in ["primary", "secondary", "background", "surface"]:
            if key in theme:
                css_vars.append(f"  --{key}: {theme[key]};")
        
        # 处理文本颜色
        if "text" in theme:
            for text_key, text_value in theme["text"].items():
                css_vars.append(f"  --text-{text_key}: {text_value};")
        
        # 处理边框
        if "border" in theme:
            for border_key, border_value in theme["border"].items():
                css_vars.append(f"  --border-{border_key}: {border_value};")
        
        # 处理阴影
        if "shadow" in theme:
            for shadow_key, shadow_value in theme["shadow"].items():
                css_vars.append(f"  --shadow-{shadow_key}: {shadow_value};")
        
        # 处理动画
        if "animation" in theme:
            for anim_key, anim_value in theme["animation"].items():
                css_vars.append(f"  --animation-{anim_key}: {anim_value};")
        
        # 处理间距
        if "spacing" in theme:
            for space_key, space_value in theme["spacing"].items():
                css_vars.append(f"  --spacing-{space_key}: {space_value};")
        
        # 处理字体
        if "font" in theme:
            css_vars.append(f"  --font-family: {theme['font'].get('family', 'sans-serif')};")
            
            # 字体大小
            if "size" in theme["font"]:
                for size_key, size_value in theme["font"]["size"].items():
                    css_vars.append(f"  --font-size-{size_key}: {size_value};")
            
            # 字体粗细
            if "weight" in theme["font"]:
                for weight_key, weight_value in theme["font"]["weight"].items():
                    css_vars.append(f"  --font-weight-{weight_key}: {weight_value};")
        
        css_vars.append("}")
        return "\n".join(css_vars)
    
    def apply_seasonal_theme(self) -> Dict[str, Any]:
        """
        根据当前季节自动应用季节性主题
        
        返回:
            Dict: 应用的主题数据
        """
        # 获取当前月份
        current_month = datetime.now().month
        
        # 根据月份判断季节
        if 3 <= current_month <= 5:  # 春季
            season = "spring"
        elif 6 <= current_month <= 8:  # 夏季
            season = "summer"
        elif 9 <= current_month <= 11:  # 秋季
            season = "autumn"
        else:  # 冬季
            season = "winter"
        
        # 查找对应季节的主题
        for theme_id, theme_data in {**self.SEASONAL_THEMES, **self.user_themes}.items():
            if theme_data.get("season") == season:
                # 找到符合当前季节的主题
                self.active_theme = theme_data
                self._save_active_theme()
                logger.info(f"应用季节性主题: {theme_id} - {theme_data.get('name')}")
                return theme_data
        
        # 如果未找到季节性主题，使用默认主题
        if self._is_dark_theme(self.active_theme):
            return self.DEFAULT_DARK_THEME
        else:
            return self.DEFAULT_LIGHT_THEME
    
    def auto_switch_by_time(self) -> Dict[str, Any]:
        """
        根据时间自动切换明暗主题
        
        返回:
            Dict: 切换后的主题数据
        """
        # 获取当前小时
        current_hour = datetime.now().hour
        
        # 早上6点到晚上8点使用亮色主题，其他时间使用暗色主题
        if 6 <= current_hour < 20:
            # 白天使用亮色主题
            if self._is_dark_theme(self.active_theme):
                self.active_theme = self.DEFAULT_LIGHT_THEME.copy()
                self._save_active_theme()
                logger.info("根据时间自动切换到亮色主题")
        else:
            # 晚上使用暗色主题
            if not self._is_dark_theme(self.active_theme):
                self.active_theme = self.DEFAULT_DARK_THEME.copy()
                self._save_active_theme()
                logger.info("根据时间自动切换到暗色主题")
        
        return self.active_theme

# 工具函数部分

def create_color_palette(base_color: str, count: int = 5, variation: str = "monochromatic") -> List[str]:
    """
    基于基础颜色创建调色板
    
    参数:
        base_color: 基础颜色，十六进制格式
        count: 要生成的颜色数量
        variation: 变化类型，支持"monochromatic"（单色）、"analogous"（类似色）、
                  "complementary"（互补色）、"triadic"（三等分色）
    
    返回:
        List[str]: 生成的颜色列表，十六进制格式
    """
    # 移除#前缀并转换为RGB
    color = base_color.lstrip("#")
    r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    # 转换为HSL色彩空间
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    
    # 根据变化类型生成调色板
    colors = []
    
    if variation == "monochromatic":
        # 单色变化 - 调整亮度和饱和度
        for i in range(count):
            # 在0.1到0.9之间调整亮度
            new_l = 0.1 + (0.8 * i / (count - 1)) if count > 1 else l
            # 保持色相不变，调整亮度
            rgb = colorsys.hls_to_rgb(h, new_l, s)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)
    
    elif variation == "analogous":
        # 类似色 - 在色相环上创建相邻的颜色
        for i in range(count):
            # 在色相环上偏移，范围约为30度（0.083在色相环上）
            offset = -0.083 + (0.166 * i / (count - 1)) if count > 1 else 0
            new_h = (h + offset) % 1.0
            rgb = colorsys.hls_to_rgb(new_h, l, s)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)
    
    elif variation == "complementary":
        # 互补色 - 在色相环上相对的颜色
        for i in range(count):
            # 在色相环的相对位置上偏移
            factor = i / (count - 1) if count > 1 else 0
            new_h = (h + 0.5 * factor) % 1.0
            rgb = colorsys.hls_to_rgb(new_h, l, s)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)
    
    elif variation == "triadic":
        # 三等分色 - 在色相环上均匀分布三个颜色
        for i in range(count):
            # 在色相环上选择0°，120°，240°三个位置
            factor = i / (count - 1) if count > 1 else 0
            new_h = (h + 0.33 * factor * 2) % 1.0
            rgb = colorsys.hls_to_rgb(new_h, l, s)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)
    
    else:
        # 默认返回单色变化
        return create_color_palette(base_color, count, "monochromatic")
    
    return colors

def blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """
    混合两种颜色
    
    参数:
        color1: 第一种颜色，十六进制格式
        color2: 第二种颜色，十六进制格式
        ratio: 混合比例，0表示完全使用color1，1表示完全使用color2
    
    返回:
        str: 混合后的颜色，十六进制格式
    """
    # 确保比例在0-1之间
    ratio = max(0, min(1, ratio))
    
    # 移除#前缀并转换为RGB
    c1 = color1.lstrip("#")
    c2 = color2.lstrip("#")
    
    r1, g1, b1 = tuple(int(c1[i:i+2], 16) for i in (0, 2, 4))
    r2, g2, b2 = tuple(int(c2[i:i+2], 16) for i in (0, 2, 4))
    
    # 线性混合
    r = int(r1 * (1 - ratio) + r2 * ratio)
    g = int(g1 * (1 - ratio) + g2 * ratio)
    b = int(b1 * (1 - ratio) + g2 * ratio)
    
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

def get_contrast_color(color: str) -> str:
    """
    获取与给定颜色形成良好对比的颜色（黑色或白色）
    
    参数:
        color: 基础颜色，十六进制格式
    
    返回:
        str: 对比色，要么是"#FFFFFF"（白色）要么是"#000000"（黑色）
    """
    # 移除#前缀并转换为RGB
    color = color.lstrip("#")
    r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    # 计算亮度 (使用感知亮度公式: 0.299*R + 0.587*G + 0.114*B)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    # 亮度低于0.5使用白色，否则使用黑色
    return "#FFFFFF" if luminance < 0.5 else "#000000"

def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    计算两种颜色之间的对比度比率
    
    参数:
        color1: 第一种颜色，十六进制格式
        color2: 第二种颜色，十六进制格式
    
    返回:
        float: 对比度比率，符合WCAG标准，范围为1到21
    """
    def get_luminance(color):
        # 移除#前缀并转换为RGB
        color = color.lstrip("#")
        r, g, b = tuple(int(color[i:i+2], 16) / 255 for i in (0, 2, 4))
        
        # 应用sRGB伽马校正
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        # 计算相对亮度
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    # 计算两种颜色的亮度
    l1 = get_luminance(color1)
    l2 = get_luminance(color2)
    
    # 计算对比度比率
    if l1 > l2:
        return (l1 + 0.05) / (l2 + 0.05)
    else:
        return (l2 + 0.05) / (l1 + 0.05)

def is_accessible(color1: str, color2: str, level: str = "AA") -> bool:
    """
    检查两种颜色的组合是否符合WCAG可访问性标准
    
    参数:
        color1: 第一种颜色，十六进制格式
        color2: 第二种颜色，十六进制格式
        level: 可访问性级别，"AA"或"AAA"
    
    返回:
        bool: 是否符合指定的可访问性级别
    """
    # 计算对比度比率
    ratio = calculate_contrast_ratio(color1, color2)
    
    # 对比度标准 (WCAG 2.0)
    # AA级：普通文本最小4.5:1，大文本最小3:1
    # AAA级：普通文本最小7:1，大文本最小4.5:1
    if level == "AA":
        return ratio >= 4.5  # 使用普通文本的标准
    elif level == "AAA":
        return ratio >= 7  # 使用普通文本的标准
    else:
        return False