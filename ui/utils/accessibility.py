"""
无障碍功能支持模块 - Accessibility Utilities

这个模块提供了应用程序的无障碍功能支持，确保界面对所有用户可用，包括残障人士。
设计理念是创造"包容性的界面体验"，让每个人都能平等地访问和使用应用程序，
消除不必要的障碍，遵循"通用设计"原则，从而使界面不仅易用，而且对每个人都是友好的。

主要功能:
    - 屏幕阅读器兼容性支持
    - 键盘导航增强
    - 高对比度模式
    - 文本大小调整
    - 动画控制
    - 焦点管理
    - ARIA属性辅助

作者: AI助手
日期: 2025-04-19
"""

import logging
import re
import math
import json
from enum import Enum
from typing import Dict, List, Optional, Union, Any, Callable, Tuple
from dataclasses import dataclass

# 导入其他相关模块
try:
    from .color import Color, RGB, HSL
except ImportError:
    # 如果无法导入，则跳过
    pass


# 配置日志
logger = logging.getLogger(__name__)


class AccessibilityLevel(Enum):
    """无障碍级别枚举"""
    A = "A"                   # WCAG 2.1 A级
    AA = "AA"                 # WCAG 2.1 AA级
    AAA = "AAA"               # WCAG 2.1 AAA级


class AccessibilityFeature(Enum):
    """无障碍特性枚举"""
    SCREEN_READER = "screen_reader"          # 屏幕阅读器支持
    KEYBOARD_NAVIGATION = "keyboard_nav"     # 键盘导航
    HIGH_CONTRAST = "high_contrast"          # 高对比度
    LARGE_TEXT = "large_text"                # 大字体
    REDUCED_MOTION = "reduced_motion"        # 减少动画
    FOCUS_VISIBLE = "focus_visible"          # 可见焦点
    COLOR_BLIND = "color_blind"              # 色盲模式
    VOICE_CONTROL = "voice_control"          # 语音控制


class ColorBlindType(Enum):
    """色盲类型枚举"""
    PROTANOPIA = "protanopia"        # 红色盲
    DEUTERANOPIA = "deuteranopia"    # 绿色盲
    TRITANOPIA = "tritanopia"        # 蓝色盲
    ACHROMATOPSIA = "achromatopsia"  # 全色盲


class FocusDirection(Enum):
    """焦点移动方向枚举"""
    NEXT = "next"           # 下一个元素
    PREVIOUS = "previous"   # 上一个元素
    UP = "up"               # 上方元素
    DOWN = "down"           # 下方元素
    LEFT = "left"           # 左侧元素
    RIGHT = "right"         # 右侧元素
    FIRST = "first"         # 第一个元素
    LAST = "last"           # 最后一个元素


@dataclass
class AccessibilitySettings:
    """无障碍设置数据类"""
    screen_reader_support: bool = True         # 屏幕阅读器支持
    keyboard_navigation: bool = True           # 键盘导航
    high_contrast_mode: bool = False           # 高对比度模式
    large_text: bool = False                   # 大字体
    reduced_motion: bool = False               # 减少动画
    focus_visible: bool = True                 # 可见焦点
    color_blind_mode: Optional[ColorBlindType] = None  # 色盲模式
    voice_control: bool = False                # 语音控制


class AccessibilityManager:
    """
    无障碍管理器类
    
    负责管理应用程序的无障碍特性和设置
    """
    
    def __init__(self, settings: Optional[AccessibilitySettings] = None):
        """
        初始化无障碍管理器
        
        参数:
            settings: 无障碍设置，如果为None则使用默认设置
        """
        self.settings = settings or AccessibilitySettings()
        
        # 特性状态缓存
        self._feature_status = {}
        
        # 焦点管理
        self.focus_elements = []
        self.current_focus_index = -1
        
        # ARIA属性管理
        self.aria_attributes = {}
        
        # 热键映射
        self.keyboard_shortcuts = {}
        
        # 回调函数
        self.settings_change_callbacks = []
        self.focus_change_callbacks = []
        
        # 初始化特性状态
        self._update_feature_status()
    
    def _update_feature_status(self) -> None:
        """更新特性状态缓存"""
        self._feature_status = {
            AccessibilityFeature.SCREEN_READER: self.settings.screen_reader_support,
            AccessibilityFeature.KEYBOARD_NAVIGATION: self.settings.keyboard_navigation,
            AccessibilityFeature.HIGH_CONTRAST: self.settings.high_contrast_mode,
            AccessibilityFeature.LARGE_TEXT: self.settings.large_text,
            AccessibilityFeature.REDUCED_MOTION: self.settings.reduced_motion,
            AccessibilityFeature.FOCUS_VISIBLE: self.settings.focus_visible,
            AccessibilityFeature.COLOR_BLIND: self.settings.color_blind_mode is not None,
            AccessibilityFeature.VOICE_CONTROL: self.settings.voice_control
        }
    
    def get_settings(self) -> AccessibilitySettings:
        """
        获取当前无障碍设置
        
        返回:
            AccessibilitySettings: 无障碍设置对象
        """
        return self.settings
    
    def update_settings(self, new_settings: AccessibilitySettings) -> None:
        """
        更新无障碍设置
        
        参数:
            new_settings: 新的无障碍设置
        """
        old_settings = self.settings
        self.settings = new_settings
        
        # 更新特性状态
        self._update_feature_status()
        
        # 触发回调
        for callback in self.settings_change_callbacks:
            try:
                callback(old_settings, new_settings)
            except Exception as e:
                logger.error(f"执行设置变更回调时出错: {e}")
    
    def toggle_feature(self, feature: AccessibilityFeature) -> bool:
        """
        切换无障碍特性
        
        参数:
            feature: 要切换的特性
        
        返回:
            bool: 切换后的状态
        """
        old_settings = AccessibilitySettings(**vars(self.settings))
        
        if feature == AccessibilityFeature.SCREEN_READER:
            self.settings.screen_reader_support = not self.settings.screen_reader_support
        elif feature == AccessibilityFeature.KEYBOARD_NAVIGATION:
            self.settings.keyboard_navigation = not self.settings.keyboard_navigation
        elif feature == AccessibilityFeature.HIGH_CONTRAST:
            self.settings.high_contrast_mode = not self.settings.high_contrast_mode
        elif feature == AccessibilityFeature.LARGE_TEXT:
            self.settings.large_text = not self.settings.large_text
        elif feature == AccessibilityFeature.REDUCED_MOTION:
            self.settings.reduced_motion = not self.settings.reduced_motion
        elif feature == AccessibilityFeature.FOCUS_VISIBLE:
            self.settings.focus_visible = not self.settings.focus_visible
        elif feature == AccessibilityFeature.COLOR_BLIND:
            if self.settings.color_blind_mode is None:
                self.settings.color_blind_mode = ColorBlindType.DEUTERANOPIA
            else:
                self.settings.color_blind_mode = None
        elif feature == AccessibilityFeature.VOICE_CONTROL:
            self.settings.voice_control = not self.settings.voice_control
        
        # 更新特性状态
        self._update_feature_status()
        
        # 触发回调
        for callback in self.settings_change_callbacks:
            try:
                callback(old_settings, self.settings)
            except Exception as e:
                logger.error(f"执行设置变更回调时出错: {e}")
        
        # 返回新状态
        return self._feature_status[feature]
    
    def is_feature_enabled(self, feature: AccessibilityFeature) -> bool:
        """
        检查无障碍特性是否启用
        
        参数:
            feature: 要检查的特性
        
        返回:
            bool: 是否启用
        """
        return self._feature_status.get(feature, False)
    
    def get_color_blind_type(self) -> Optional[ColorBlindType]:
        """
        获取当前色盲模式类型
        
        返回:
            Optional[ColorBlindType]: 色盲类型，如果未启用则为None
        """
        return self.settings.color_blind_mode
    
    def add_settings_change_callback(self, callback: Callable[[AccessibilitySettings, AccessibilitySettings], None]) -> None:
        """
        添加设置变更回调
        
        参数:
            callback: 回调函数，接收两个参数：old_settings和new_settings
        """
        self.settings_change_callbacks.append(callback)
    
    def simulate_color_blindness(self, hex_color: str) -> str:
        """
        模拟色盲视觉下的颜色
        
        参数:
            hex_color: 十六进制颜色
        
        返回:
            str: 模拟后的十六进制颜色
        """
        if self.settings.color_blind_mode is None:
            return hex_color
        
        try:
            # 转换为RGB
            if 'Color' in globals():
                rgb = Color.hex_to_rgb(hex_color)
                r, g, b = rgb.r, rgb.g, rgb.b
            else:
                # 如果未导入Color模块，手动解析颜色
                hex_color = hex_color.lstrip('#')
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # 根据色盲类型应用不同的变换矩阵
            if self.settings.color_blind_mode == ColorBlindType.PROTANOPIA:
                # 红色盲
                r_new = 0.567 * r + 0.433 * g + 0.0 * b
                g_new = 0.558 * r + 0.442 * g + 0.0 * b
                b_new = 0.0 * r + 0.242 * g + 0.758 * b
            elif self.settings.color_blind_mode == ColorBlindType.DEUTERANOPIA:
                # 绿色盲
                r_new = 0.625 * r + 0.375 * g + 0.0 * b
                g_new = 0.7 * r + 0.3 * g + 0.0 * b
                b_new = 0.0 * r + 0.3 * g + 0.7 * b
            elif self.settings.color_blind_mode == ColorBlindType.TRITANOPIA:
                # 蓝色盲
                r_new = 0.95 * r + 0.05 * g + 0.0 * b
                g_new = 0.0 * r + 0.433 * g + 0.567 * b
                b_new = 0.0 * r + 0.475 * g + 0.525 * b
            elif self.settings.color_blind_mode == ColorBlindType.ACHROMATOPSIA:
                # 全色盲（灰度）
                intensity = 0.299 * r + 0.587 * g + 0.114 * b
                r_new = g_new = b_new = intensity
            else:
                return hex_color
            
            # 确保值在0-255范围内
            r_new = max(0, min(255, int(r_new)))
            g_new = max(0, min(255, int(g_new)))
            b_new = max(0, min(255, int(b_new)))
            
            # 转换回十六进制
            return f"#{r_new:02x}{g_new:02x}{b_new:02x}"
            
        except Exception as e:
            logger.error(f"模拟色盲视觉时出错: {e}")
            return hex_color
    
    def register_focusable_element(self, element_id: str, tab_index: int = 0, 
                                   group: Optional[str] = None, 
                                   accessible_name: Optional[str] = None) -> None:
        """
        注册可聚焦元素
        
        参数:
            element_id: 元素ID
            tab_index: 选项卡索引，控制焦点顺序
            group: 元素组，用于按组导航
            accessible_name: 无障碍名称，用于屏幕阅读器
        """
        # 检查元素是否已存在
        for i, elem in enumerate(self.focus_elements):
            if elem["id"] == element_id:
                # 更新现有元素
                self.focus_elements[i] = {
                    "id": element_id,
                    "tab_index": tab_index,
                    "group": group,
                    "accessible_name": accessible_name
                }
                return
        
        # 添加新元素
        self.focus_elements.append({
            "id": element_id,
            "tab_index": tab_index,
            "group": group,
            "accessible_name": accessible_name
        })
        
        # 排序元素，按tab_index升序
        self.focus_elements.sort(key=lambda x: x["tab_index"])
    
    def unregister_focusable_element(self, element_id: str) -> bool:
        """
        取消注册可聚焦元素
        
        参数:
            element_id: 元素ID
        
        返回:
            bool: 是否成功取消注册
        """
        for i, elem in enumerate(self.focus_elements):
            if elem["id"] == element_id:
                # 如果当前焦点在该元素上，重置焦点
                if self.current_focus_index == i:
                    self.current_focus_index = -1
                
                # 移除元素
                self.focus_elements.pop(i)
                return True
        
        return False
    
    def move_focus(self, direction: FocusDirection) -> Optional[Dict[str, Any]]:
        """
        移动焦点
        
        参数:
            direction: 移动方向
        
        返回:
            Optional[Dict[str, Any]]: 新的焦点元素，如果没有可聚焦元素则返回None
        """
        if not self.focus_elements:
            return None
        
        old_focus_index = self.current_focus_index
        old_focus_element = self.focus_elements[old_focus_index] if 0 <= old_focus_index < len(self.focus_elements) else None
        
        # 根据方向移动焦点
        if direction == FocusDirection.NEXT:
            self.current_focus_index = (self.current_focus_index + 1) % len(self.focus_elements)
        elif direction == FocusDirection.PREVIOUS:
            self.current_focus_index = (self.current_focus_index - 1) % len(self.focus_elements)
        elif direction == FocusDirection.FIRST:
            self.current_focus_index = 0
        elif direction == FocusDirection.LAST:
            self.current_focus_index = len(self.focus_elements) - 1
        elif direction in [FocusDirection.UP, FocusDirection.DOWN, FocusDirection.LEFT, FocusDirection.RIGHT]:
            # 这些方向需要额外的空间信息来确定下一个焦点元素
            # 这里简化处理，使用NEXT方向
            self.current_focus_index = (self.current_focus_index + 1) % len(self.focus_elements)
        
        # 获取新的焦点元素
        new_focus_element = self.focus_elements[self.current_focus_index]
        
        # 触发焦点变化回调
        for callback in self.focus_change_callbacks:
            try:
                callback(old_focus_element, new_focus_element)
            except Exception as e:
                logger.error(f"执行焦点变化回调时出错: {e}")
        
        return new_focus_element
    
    def set_focus(self, element_id: str) -> bool:
        """
        设置焦点到指定元素
        
        参数:
            element_id: 元素ID
        
        返回:
            bool: 是否成功设置焦点
        """
        for i, elem in enumerate(self.focus_elements):
            if elem["id"] == element_id:
                old_focus_index = self.current_focus_index
                old_focus_element = self.focus_elements[old_focus_index] if 0 <= old_focus_index < len(self.focus_elements) else None
                
                self.current_focus_index = i
                new_focus_element = elem
                
                # 触发焦点变化回调
                for callback in self.focus_change_callbacks:
                    try:
                        callback(old_focus_element, new_focus_element)
                    except Exception as e:
                        logger.error(f"执行焦点变化回调时出错: {e}")
                
                return True
        
        return False
    
    def add_focus_change_callback(self, callback: Callable[[Optional[Dict[str, Any]], Dict[str, Any]], None]) -> None:
        """
        添加焦点变化回调
        
        参数:
            callback: 回调函数，接收两个参数：old_focus_element和new_focus_element
        """
        self.focus_change_callbacks.append(callback)
    
    def get_current_focus(self) -> Optional[Dict[str, Any]]:
        """
        获取当前焦点元素
        
        返回:
            Optional[Dict[str, Any]]: 当前焦点元素，如果没有则返回None
        """
        if 0 <= self.current_focus_index < len(self.focus_elements):
            return self.focus_elements[self.current_focus_index]
        return None
    
    def register_keyboard_shortcut(self, key_combination: str, action: Callable[[], None], 
                                  description: str) -> None:
        """
        注册键盘快捷键
        
        参数:
            key_combination: 按键组合，例如"Alt+S"
            action: 要执行的操作
            description: 快捷键描述
        """
        self.keyboard_shortcuts[key_combination] = {
            "action": action,
            "description": description
        }
    
    def execute_keyboard_shortcut(self, key_combination: str) -> bool:
        """
        执行键盘快捷键
        
        参数:
            key_combination: 按键组合
        
        返回:
            bool: 是否成功执行
        """
        if key_combination in self.keyboard_shortcuts:
            try:
                self.keyboard_shortcuts[key_combination]["action"]()
                return True
            except Exception as e:
                logger.error(f"执行键盘快捷键时出错: {e}")
        
        return False
    
    def get_keyboard_shortcuts(self) -> Dict[str, str]:
        """
        获取键盘快捷键列表
        
        返回:
            Dict[str, str]: 键盘快捷键字典，键为按键组合，值为描述
        """
        return {key: value["description"] for key, value in self.keyboard_shortcuts.items()}
    
    def get_accessibility_css(self) -> str:
        """
        获取无障碍CSS样式
        
        返回:
            str: CSS样式字符串
        """
        css = []
        
        # 基础CSS
        css.append(":root {")
        
        # 添加高对比度模式
        if self.settings.high_contrast_mode:
            css.append("  --background-color: #000000;")
            css.append("  --text-color: #FFFFFF;")
            css.append("  --link-color: #FFFF00;")
            css.append("  --primary-color: #00FFFF;")
            css.append("  --secondary-color: #FFFFFF;")
            css.append("  --border-color: #FFFFFF;")
            css.append("  --focus-outline-color: #FFFF00;")
        else:
            css.append("  --background-color: #FFFFFF;")
            css.append("  --text-color: #333333;")
            css.append("  --link-color: #0066CC;")
            css.append("  --primary-color: #4F6AF5;")
            css.append("  --secondary-color: #7A5AF8;")
            css.append("  --border-color: #E1E2EA;")
            css.append("  --focus-outline-color: #4F6AF5;")
        
        # 添加大字体模式
        if self.settings.large_text:
            css.append("  --font-size-factor: 1.5;")
            css.append("  --font-size-base: calc(16px * var(--font-size-factor));")
            css.append("  --font-size-sm: calc(14px * var(--font-size-factor));")
            css.append("  --font-size-lg: calc(18px * var(--font-size-factor));")
            css.append("  --font-size-xl: calc(24px * var(--font-size-factor));")
            css.append("  --line-height-factor: 1.3;")
        else:
            css.append("  --font-size-factor: 1;")
            css.append("  --font-size-base: 16px;")
            css.append("  --font-size-sm: 14px;")
            css.append("  --font-size-lg: 18px;")
            css.append("  --font-size-xl: 24px;")
            css.append("  --line-height-factor: 1;")
        
        # 添加减少动画模式
        if self.settings.reduced_motion:
            css.append("  --transition-duration: 0.01s;")
            css.append("  --animation-duration: 0.01s;")
        else:
            css.append("  --transition-duration: 0.3s;")
            css.append("  --animation-duration: 0.5s;")
        
        css.append("}")
        
        # 添加全局样式
        css.append("body {")
        css.append("  background-color: var(--background-color);")
        css.append("  color: var(--text-color);")
        css.append("  font-size: var(--font-size-base);")
        css.append("  line-height: calc(1.5 * var(--line-height-factor));")
        css.append("}")
        
        # 添加链接样式
        css.append("a {")
        css.append("  color: var(--link-color);")
        css.append("  text-decoration: underline;")
        css.append("}")
        
        # 添加可见焦点样式
        if self.settings.focus_visible:
            css.append(":focus {")
            css.append("  outline: 3px solid var(--focus-outline-color);")
            css.append("  outline-offset: 2px;")
            css.append("}")
            
            css.append(":focus:not(:focus-visible) {")
            css.append("  outline: none;")
            css.append("}")
            
            css.append(":focus-visible {")
            css.append("  outline: 3px solid var(--focus-outline-color);")
            css.append("  outline-offset: 2px;")
            css.append("}")
        
        # 添加减少动画样式
        if self.settings.reduced_motion:
            css.append("@media (prefers-reduced-motion: reduce) {")
            css.append("  *, ::before, ::after {")
            css.append("    animation-duration: 0.01s !important;")
            css.append("    animation-iteration-count: 1 !important;")
            css.append("    transition-duration: 0.01s !important;")
            css.append("    scroll-behavior: auto !important;")
            css.append("  }")
            css.append("}")
        
        return "\n".join(css)
    
    def set_aria_attribute(self, element_id: str, attribute: str, value: str) -> None:
        """
        设置ARIA属性
        
        参数:
            element_id: 元素ID
            attribute: 属性名
            value: 属性值
        """
        if element_id not in self.aria_attributes:
            self.aria_attributes[element_id] = {}
        
        self.aria_attributes[element_id][attribute] = value
    
    def get_aria_attributes(self, element_id: str) -> Dict[str, str]:
        """
        获取元素的ARIA属性
        
        参数:
            element_id: 元素ID
        
        返回:
            Dict[str, str]: ARIA属性字典
        """
        return self.aria_attributes.get(element_id, {})
    
    def generate_aria_markup(self, element_id: str) -> str:
        """
        生成ARIA标记
        
        参数:
            element_id: 元素ID
        
        返回:
            str: ARIA属性标记
        """
        attributes = self.get_aria_attributes(element_id)
        if not attributes:
            return ""
        
        aria_markup = []
        for attr, value in attributes.items():
            aria_markup.append(f'aria-{attr}="{value}"')
        
        return " ".join(aria_markup)
    
    def save_settings(self, file_path: str) -> bool:
        """
        保存设置到文件
        
        参数:
            file_path: 文件路径
        
        返回:
            bool: 是否成功保存
        """
        try:
            # 转换设置为字典
            settings_dict = vars(self.settings)
            
            # 特殊处理枚举
            if settings_dict["color_blind_mode"] is not None:
                settings_dict["color_blind_mode"] = settings_dict["color_blind_mode"].value
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2)
            
            logger.info(f"无障碍设置已保存到: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"保存无障碍设置时出错: {e}")
            return False
    
    def load_settings(self, file_path: str) -> bool:
        """
        从文件加载设置
        
        参数:
            file_path: 文件路径
        
        返回:
            bool: 是否成功加载
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
            
            # 特殊处理枚举
            if settings_dict.get("color_blind_mode"):
                settings_dict["color_blind_mode"] = ColorBlindType(settings_dict["color_blind_mode"])
            
            # 创建设置对象
            new_settings = AccessibilitySettings(**settings_dict)
            
            # 更新设置
            self.update_settings(new_settings)
            
            logger.info(f"无障碍设置已从 {file_path} 加载")
            return True
        
        except Exception as e:
            logger.error(f"加载无障碍设置时出错: {e}")
            return False


class AccessibilityChecker:
    """
    无障碍检查器类
    
    用于检查界面元素的无障碍性
    """
    
    @staticmethod
    def check_text_contrast(text_color: str, background_color: str, 
                           level: AccessibilityLevel = AccessibilityLevel.AA) -> Tuple[bool, float]:
        """
        检查文本对比度
        
        参数:
            text_color: 文本颜色（十六进制）
            background_color: 背景颜色（十六进制）
            level: 无障碍级别
        
        返回:
            Tuple[bool, float]: (是否通过检查, 对比度值)
        """
        try:
            # 计算对比度
            if 'Color' in globals():
                contrast_ratio = Color.calculate_contrast_ratio(text_color, background_color)
            else:
                # 手动计算对比度
                def get_luminance(hex_color):
                    hex_color = hex_color.lstrip('#')
                    r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                    
                    # sRGB伽马校正
                    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
                    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
                    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
                    
                    # 相对亮度
                    return 0.2126 * r + 0.7152 * g + 0.0722 * b
                
                l1 = get_luminance(text_color)
                l2 = get_luminance(background_color)
                
                # 确保l1是较大的值
                if l1 < l2:
                    l1, l2 = l2, l1
                
                contrast_ratio = (l1 + 0.05) / (l2 + 0.05)
            
            # 检查是否满足要求
            if level == AccessibilityLevel.A or level == AccessibilityLevel.AA:
                # AA级：普通文本4.5:1，大文本3:1
                return (contrast_ratio >= 4.5, contrast_ratio)
            elif level == AccessibilityLevel.AAA:
                # AAA级：普通文本7:1，大文本4.5:1
                return (contrast_ratio >= 7.0, contrast_ratio)
            else:
                return (False, contrast_ratio)
            
        except Exception as e:
            logger.error(f"检查文本对比度时出错: {e}")
            return (False, 0.0)
    
    @staticmethod
    def check_element_labels(element_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查元素标签的无障碍性
        
        参数:
            element_data: 元素数据
        
        返回:
            List[Dict[str, Any]]: 问题列表
        """
        issues = []
        
        # 检查是否有可访问名称
        if "accessible_name" not in element_data or not element_data["accessible_name"]:
            issues.append({
                "type": "missing_label",
                "severity": "high",
                "message": "元素缺少可访问名称（aria-label或类似标签）"
            })
        
        # 检查交互元素是否有必要的ARIA角色
        if element_data.get("type") in ["button", "link", "input", "select"]:
            if "role" not in element_data or not element_data["role"]:
                issues.append({
                    "type": "missing_role",
                    "severity": "medium",
                    "message": f"交互元素缺少ARIA角色，建议使用 role=\"{element_data.get('type')}\""
                })
        
        # 检查表单元素是否有适当的标签
        if element_data.get("type") in ["input", "select", "textarea"]:
            if "label_for" not in element_data or not element_data["label_for"]:
                issues.append({
                    "type": "missing_form_label",
                    "severity": "high",
                    "message": "表单元素缺少关联的label元素"
                })
        
        # 检查图像是否有替代文本
        if element_data.get("type") == "image":
            if "alt" not in element_data or not element_data["alt"]:
                issues.append({
                    "type": "missing_alt",
                    "severity": "high",
                    "message": "图像缺少替代文本（alt属性）"
                })
        
        return issues
    
    @staticmethod
    def check_keyboard_navigation(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查键盘导航的无障碍性
        
        参数:
            elements: 元素列表
        
        返回:
            List[Dict[str, Any]]: 问题列表
        """
        issues = []
        
        # 检查是否有可聚焦元素
        if not elements:
            issues.append({
                "type": "no_focusable_elements",
                "severity": "high",
                "message": "页面没有可聚焦元素，无法通过键盘导航"
            })
            return issues
        
        # 检查tab顺序
        tab_indices = [elem.get("tab_index", 0) for elem in elements]
        
        # 检查tab索引是否连续
        for i in range(1, len(tab_indices)):
            if tab_indices[i] > 0 and tab_indices[i] - tab_indices[i-1] > 1:
                issues.append({
                    "type": "tab_order_gap",
                    "severity": "medium",
                    "message": f"元素之间的tab顺序不连续: {tab_indices[i-1]} -> {tab_indices[i]}"
                })
        
        # 检查交互元素是否可聚焦
        for elem in elements:
            if elem.get("type") in ["button", "link", "input", "select", "textarea"]:
                if "tab_index" not in elem or elem["tab_index"] < 0:
                    issues.append({
                        "type": "not_focusable",
                        "severity": "high",
                        "message": f"交互元素 {elem.get('id')} 无法通过键盘聚焦"
                    })
        
        return issues
    
    @staticmethod
    def check_aria_attributes(aria_attributes: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        检查ARIA属性的无障碍性
        
        参数:
            aria_attributes: ARIA属性字典
        
        返回:
            List[Dict[str, Any]]: 问题列表
        """
        issues = []
        
        # 有效的ARIA属性列表
        valid_aria_attributes = {
            "label", "labelledby", "describedby", "hidden", "checked", "expanded",
            "haspopup", "level", "orientation", "pressed", "selected", "valuenow",
            "valuemin", "valuemax", "valuetext", "live", "relevant", "busy",
            "atomic", "disabled", "invalid", "required", "multiline", "multiselectable",
            "readonly", "sort", "placeholder", "current", "controls", "owns",
            "flowto", "errormessage", "keyshortcuts", "roledescription"
        }
        
        for element_id, attributes in aria_attributes.items():
            for attr, value in attributes.items():
                # 检查属性是否有效
                if attr not in valid_aria_attributes:
                    issues.append({
                        "type": "invalid_aria_attribute",
                        "severity": "medium",
                        "message": f"元素 {element_id} 使用了无效的ARIA属性: aria-{attr}"
                    })
                
                # 检查必需的属性值
                if attr in ["hidden", "checked", "expanded", "pressed", "selected", "disabled", "required", "readonly", "multiline", "multiselectable", "atomic", "busy"]:
                    if value.lower() not in ["true", "false"]:
                        issues.append({
                            "type": "invalid_aria_value",
                            "severity": "medium",
                            "message": f"元素 {element_id} 的ARIA属性 aria-{attr} 值必须是 true 或 false"
                        })
                
                # 检查数值属性
                if attr in ["valuenow", "valuemin", "valuemax", "level"]:
                    try:
                        float(value)
                    except ValueError:
                        issues.append({
                            "type": "invalid_aria_value",
                            "severity": "medium",
                            "message": f"元素 {element_id} 的ARIA属性 aria-{attr} 值必须是数字"
                        })
        
        return issues
    
    @staticmethod
    def check_color_usage(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查颜色使用的无障碍性
        
        参数:
            elements: 元素列表
        
        返回:
            List[Dict[str, Any]]: 问题列表
        """
        issues = []
        
        for elem in elements:
            # 检查是否仅使用颜色传达信息
            if "has_color_only_info" in elem and elem["has_color_only_info"]:
                issues.append({
                    "type": "color_only_info",
                    "severity": "high",
                    "message": f"元素 {elem.get('id')} 仅使用颜色传达信息，应添加额外的视觉提示"
                })
            
            # 检查文本和背景的对比度
            if "text_color" in elem and "background_color" in elem:
                is_accessible, contrast_ratio = AccessibilityChecker.check_text_contrast(
                    elem["text_color"], elem["background_color"]
                )
                
                if not is_accessible:
                    issues.append({
                        "type": "low_contrast",
                        "severity": "high",
                        "message": f"元素 {elem.get('id')} 的文本对比度不足: {contrast_ratio:.2f}，最小要求为4.5"
                    })
        
        return issues
    
    @staticmethod
    def check_html_structure(html_content: str) -> List[Dict[str, Any]]:
        """
        检查HTML结构的无障碍性
        
        参数:
            html_content: HTML内容
        
        返回:
            List[Dict[str, Any]]: 问题列表
        """
        issues = []
        
        # 检查HTML语言设置
        if 'lang="' not in html_content.lower():
            issues.append({
                "type": "missing_lang",
                "severity": "medium",
                "message": "HTML缺少lang属性，应指定页面的主要语言"
            })
        
        # 检查标题层级
        heading_pattern = r'<h(\d)[^>]*>'
        headings = re.findall(heading_pattern, html_content)
        
        if not headings:
            issues.append({
                "type": "no_headings",
                "severity": "medium",
                "message": "页面没有标题元素，应使用适当的标题结构"
            })
        else:
            # 检查标题是否从h1开始
            if int(headings[0]) != 1:
                issues.append({
                    "type": "wrong_heading_hierarchy",
                    "severity": "medium",
                    "message": f"页面标题层级不从h1开始，而是从h{headings[0]}开始"
                })
            
            # 检查标题层级是否有跳跃
            current_level = 0
            for level in headings:
                level = int(level)
                if level > current_level + 1:
                    issues.append({
                        "type": "skipped_heading_level",
                        "severity": "medium",
                        "message": f"标题层级从h{current_level}跳到h{level}，跳过了中间层级"
                    })
                current_level = level
        
        # 检查图像是否有alt属性
        img_pattern = r'<img[^>]*>'
        imgs = re.findall(img_pattern, html_content)
        
        for img in imgs:
            if 'alt="' not in img.lower() and 'alt=' not in img.lower():
                issues.append({
                    "type": "missing_alt",
                    "severity": "high",
                    "message": "图像缺少alt属性，屏幕阅读器无法识别图像内容"
                })
        
        return issues
    
    @staticmethod
    def get_accessibility_report(elements: List[Dict[str, Any]], 
                                html_content: Optional[str] = None,
                                aria_attributes: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        生成无障碍报告
        
        参数:
            elements: 元素列表
            html_content: HTML内容
            aria_attributes: ARIA属性字典
        
        返回:
            Dict[str, Any]: 无障碍报告
        """
        report = {
            "timestamp": None,  # 在Python中获取当前时间
            "issues": [],
            "passed_checks": [],
            "summary": {
                "total_issues": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0
            }
        }
        
        # 检查键盘导航
        keyboard_issues = AccessibilityChecker.check_keyboard_navigation(elements)
        report["issues"].extend(keyboard_issues)
        
        if not keyboard_issues:
            report["passed_checks"].append({
                "type": "keyboard_navigation",
                "message": "键盘导航检查通过"
            })
        
        # 检查元素标签
        label_issues = []
        for elem in elements:
            elem_issues = AccessibilityChecker.check_element_labels(elem)
            label_issues.extend(elem_issues)
        
        report["issues"].extend(label_issues)
        
        if not label_issues:
            report["passed_checks"].append({
                "type": "element_labels",
                "message": "元素标签检查通过"
            })
        
        # 检查颜色使用
        color_issues = AccessibilityChecker.check_color_usage(elements)
        report["issues"].extend(color_issues)
        
        if not color_issues:
            report["passed_checks"].append({
                "type": "color_usage",
                "message": "颜色使用检查通过"
            })
        
        # 检查ARIA属性
        if aria_attributes:
            aria_issues = AccessibilityChecker.check_aria_attributes(aria_attributes)
            report["issues"].extend(aria_issues)
            
            if not aria_issues:
                report["passed_checks"].append({
                    "type": "aria_attributes",
                    "message": "ARIA属性检查通过"
                })
        
        # 检查HTML结构
        if html_content:
            html_issues = AccessibilityChecker.check_html_structure(html_content)
            report["issues"].extend(html_issues)
            
            if not html_issues:
                report["passed_checks"].append({
                    "type": "html_structure",
                    "message": "HTML结构检查通过"
                })
        
        # 更新摘要统计
        report["summary"]["total_issues"] = len(report["issues"])
        report["summary"]["high_severity"] = sum(1 for issue in report["issues"] if issue["severity"] == "high")
        report["summary"]["medium_severity"] = sum(1 for issue in report["issues"] if issue["severity"] == "medium")
        report["summary"]["low_severity"] = sum(1 for issue in report["issues"] if issue["severity"] == "low")
        
        import datetime
        report["timestamp"] = datetime.datetime.now().isoformat()
        
        return report


# 适配器和帮助类

class ColorBlindSimulator:
    """
    色盲模拟器类
    
    用于模拟不同类型色盲下的视觉效果
    """
    
    @staticmethod
    def apply_color_blind_filter(hex_color: str, color_blind_type: ColorBlindType) -> str:
        """
        应用色盲滤镜到颜色
        
        参数:
            hex_color: 十六进制颜色
            color_blind_type: 色盲类型
        
        返回:
            str: 模拟后的十六进制颜色
        """
        # 解析颜色
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # 根据色盲类型应用不同的变换矩阵
        if color_blind_type == ColorBlindType.PROTANOPIA:
            # 红色盲
            r_new = 0.567 * r + 0.433 * g + 0.0 * b
            g_new = 0.558 * r + 0.442 * g + 0.0 * b
            b_new = 0.0 * r + 0.242 * g + 0.758 * b
        elif color_blind_type == ColorBlindType.DEUTERANOPIA:
            # 绿色盲
            r_new = 0.625 * r + 0.375 * g + 0.0 * b
            g_new = 0.7 * r + 0.3 * g + 0.0 * b
            b_new = 0.0 * r + 0.3 * g + 0.7 * b
        elif color_blind_type == ColorBlindType.TRITANOPIA:
            # 蓝色盲
            r_new = 0.95 * r + 0.05 * g + 0.0 * b
            g_new = 0.0 * r + 0.433 * g + 0.567 * b
            b_new = 0.0 * r + 0.475 * g + 0.525 * b
        elif color_blind_type == ColorBlindType.ACHROMATOPSIA:
            # 全色盲（灰度）
            intensity = 0.299 * r + 0.587 * g + 0.114 * b
            r_new = g_new = b_new = intensity
        else:
            return f"#{hex_color}"
        
        # 确保值在0-255范围内
        r_new = max(0, min(255, int(r_new)))
        g_new = max(0, min(255, int(g_new)))
        b_new = max(0, min(255, int(b_new)))
        
        # 转换回十六进制
        return f"#{r_new:02x}{g_new:02x}{b_new:02x}"
    
    @staticmethod
    def generate_colorblind_palette(colors: List[str], color_blind_type: ColorBlindType) -> Dict[str, str]:
        """
        为色盲用户生成调色板
        
        参数:
            colors: 原始颜色列表
            color_blind_type: 色盲类型
        
        返回:
            Dict[str, str]: 原始颜色到色盲适配颜色的映射
        """
        palette = {}
        
        for color in colors:
            simulated = ColorBlindSimulator.apply_color_blind_filter(color, color_blind_type)
            palette[color] = simulated
        
        return palette
    
    @staticmethod
    def get_colorblind_safe_colors(count: int = 5) -> List[str]:
        """
        获取色盲安全的颜色列表
        
        参数:
            count: 颜色数量
        
        返回:
            List[str]: 颜色列表
        """
        # 预定义的对比度高、色盲友好的颜色
        safe_colors = [
            "#000000",  # 黑色
            "#E69F00",  # 橙色
            "#56B4E9",  # 天蓝色
            "#009E73",  # 绿色
            "#F0E442",  # 黄色
            "#0072B2",  # 蓝色
            "#D55E00",  # 红橙色
            "#CC79A7",  # 粉色
            "#999999",  # 灰色
            "#FFFFFF",  # 白色
        ]
        
        # 返回请求的数量（最多返回预定义的所有颜色）
        return safe_colors[:min(count, len(safe_colors))]


class ScreenReaderHelper:
    """
    屏幕阅读器助手类
    
    提供生成屏幕阅读器友好内容的工具
    """
    
    @staticmethod
    def generate_sr_text(content: Dict[str, Any]) -> str:
        """
        生成屏幕阅读器友好的文本
        
        参数:
            content: 内容数据
        
        返回:
            str: 屏幕阅读器文本
        """
        sr_text = []
        
        # 提取标题
        if "title" in content:
            sr_text.append(f"标题: {content['title']}")
        
        # 提取描述
        if "description" in content:
            sr_text.append(f"描述: {content['description']}")
        
        # 提取结构信息
        if "structure" in content:
            structure = content["structure"]
            
            if "sections" in structure:
                sections = structure["sections"]
                sr_text.append(f"本内容包含 {len(sections)} 个部分:")
                
                for i, section in enumerate(sections):
                    sr_text.append(f"第 {i+1} 部分: {section.get('title', '无标题')}")
                    
                    if "items" in section:
                        items = section["items"]
                        sr_text.append(f"  包含 {len(items)} 个项目")
        
        # 提取交互元素
        if "interactive_elements" in content:
            elements = content["interactive_elements"]
            sr_text.append(f"交互元素数量: {len(elements)}")
            
            for elem in elements:
                elem_type = elem.get("type", "元素")
                elem_name = elem.get("name", "未命名")
                sr_text.append(f"  {elem_type}: {elem_name}")
                
                if "description" in elem:
                    sr_text.append(f"    描述: {elem['description']}")
        
        return "\n".join(sr_text)
    
    @staticmethod
    def get_aria_description(element: Dict[str, Any]) -> str:
        """
        获取元素的ARIA描述
        
        参数:
            element: 元素数据
        
        返回:
            str: ARIA描述
        """
        descriptions = []
        
        # 添加基本信息
        if "role" in element:
            descriptions.append(f"{element['role']}")
        
        if "accessible_name" in element:
            descriptions.append(element["accessible_name"])
        
        # 添加状态信息
        states = []
        
        if "disabled" in element and element["disabled"]:
            states.append("已禁用")
        
        if "required" in element and element["required"]:
            states.append("必填")
        
        if "checked" in element:
            states.append("已选中" if element["checked"] else "未选中")
        
        if "expanded" in element:
            states.append("已展开" if element["expanded"] else "已折叠")
        
        # 添加描述信息
        if "description" in element:
            descriptions.append(element["description"])
        
        # 组合所有信息
        if states:
            descriptions.append(f"({', '.join(states)})")
        
        return ", ".join(descriptions)
    
    @staticmethod
    def get_element_instructions(element: Dict[str, Any]) -> str:
        """
        获取元素的使用说明
        
        参数:
            element: 元素数据
        
        返回:
            str: 使用说明
        """
        element_type = element.get("type", "").lower()
        
        if element_type == "button":
            return "按空格键或回车键激活"
        elif element_type == "link":
            return "按回车键跟随链接"
        elif element_type == "checkbox":
            return "按空格键切换选中状态"
        elif element_type == "radio":
            return "按空格键选择"
        elif element_type == "select":
            return "按空格键打开下拉菜单，使用箭头键导航选项，按回车键选择"
        elif element_type == "slider":
            return "使用左右箭头键调整值"
        elif element_type == "textbox":
            return "输入文本"
        elif element_type == "menu":
            return "按空格键或回车键打开菜单，使用箭头键导航，按回车键选择"
        elif element_type == "tab":
            return "使用左右箭头键切换标签页"
        else:
            return ""


class KeyboardNavigationHelper:
    """
    键盘导航助手类
    
    提供键盘导航的辅助工具
    """
    
    @staticmethod
    def get_keyboard_shortcut_help() -> str:
        """
        获取键盘快捷键帮助文本
        
        返回:
            str: 帮助文本
        """
        shortcuts = [
            ("Tab", "移动到下一个可聚焦元素"),
            ("Shift+Tab", "移动到上一个可聚焦元素"),
            ("Enter/空格", "激活当前元素（按钮、链接等）"),
            ("Esc", "关闭弹出元素或取消操作"),
            ("箭头键", "在相关元素之间导航（菜单项、列表项等）"),
            ("Home/End", "移动到列表或页面的开始/结束"),
            ("Page Up/Down", "上下翻页"),
            ("Alt+F", "打开文件菜单"),
            ("Alt+E", "打开编辑菜单"),
            ("Alt+V", "打开视图菜单"),
            ("Alt+H", "打开帮助菜单"),
            ("Ctrl+F", "搜索"),
            ("Ctrl+S", "保存"),
            ("Ctrl+P", "打印"),
            ("Ctrl+Z", "撤销"),
            ("Ctrl+Y", "重做"),
            ("F1", "帮助"),
            ("F5", "刷新"),
        ]
        
        # 格式化为表格
        help_text = ["键盘快捷键:\n"]
        
        for key, desc in shortcuts:
            help_text.append(f"{key}: {desc}")
        
        return "\n".join(help_text)
    
    @staticmethod
    def create_keyboard_trap_warning(element_type: str) -> str:
        """
        创建键盘陷阱警告
        
        参数:
            element_type: 元素类型
        
        返回:
            str: 警告文本
        """
        return f"警告: {element_type}元素可能会创建键盘陷阱，请确保用户可以使用Tab键或Esc键离开该元素。"
    
    @staticmethod
    def generate_focus_order(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成焦点顺序列表
        
        参数:
            elements: 元素列表
        
        返回:
            List[Dict[str, Any]]: 排序后的元素列表
        """
        # 根据tabIndex排序
        # tabIndex为0或未设置的元素按DOM顺序排列
        # tabIndex大于0的元素按tabIndex值排序
        # tabIndex小于0的元素不参与键盘导航
        
        # 分离不同tabIndex的元素
        positive_tab_index = []
        zero_tab_index = []
        
        for elem in elements:
            tab_index = elem.get("tab_index", 0)
            
            if tab_index > 0:
                positive_tab_index.append(elem)
            elif tab_index == 0:
                zero_tab_index.append(elem)
        
        # 按tabIndex排序正值元素
        positive_tab_index.sort(key=lambda x: x.get("tab_index", 0))
        
        # 组合排序后的列表
        return positive_tab_index + zero_tab_index


# 示例用法（供参考）
def example_usage():
    """无障碍功能模块使用示例"""
    
    # 初始化无障碍管理器
    accessibility_mgr = AccessibilityManager()
    
    # 获取当前设置
    settings = accessibility_mgr.get_settings()
    print(f"屏幕阅读器支持: {settings.screen_reader_support}")
    print(f"键盘导航: {settings.keyboard_navigation}")
    print(f"高对比度模式: {settings.high_contrast_mode}")
    
    # 切换高对比度模式
    accessibility_mgr.toggle_feature(AccessibilityFeature.HIGH_CONTRAST)
    print(f"高对比度模式已切换为: {accessibility_mgr.is_feature_enabled(AccessibilityFeature.HIGH_CONTRAST)}")
    
    # 获取无障碍CSS样式
    css = accessibility_mgr.get_accessibility_css()
    print("\n生成的CSS样式片段:")
    print(css.split("\n")[:5])  # 只显示前5行
    
    # 注册可聚焦元素
    accessibility_mgr.register_focusable_element(
        "btn_submit", tab_index=1, accessible_name="提交按钮"
    )
    accessibility_mgr.register_focusable_element(
        "btn_cancel", tab_index=2, accessible_name="取消按钮"
    )
    
    # 移动焦点
    focused_elem = accessibility_mgr.move_focus(FocusDirection.NEXT)
    print(f"\n焦点已移动到: {focused_elem['accessible_name']}")
    
    # 设置ARIA属性
    accessibility_mgr.set_aria_attribute("btn_submit", "label", "提交表单")
    aria_markup = accessibility_mgr.generate_aria_markup("btn_submit")
    print(f"\n生成的ARIA标记: {aria_markup}")
    
    # 检查文本对比度
    is_accessible, ratio = AccessibilityChecker.check_text_contrast("#333333", "#FFFFFF")
    print(f"\n文本对比度: {ratio:.2f}, 是否可访问: {is_accessible}")
    
    # 获取色盲安全颜色
    safe_colors = ColorBlindSimulator.get_colorblind_safe_colors(3)
    print(f"\n色盲安全颜色: {safe_colors}")
    
    # 模拟色盲视觉
    original_color = "#FF0000"  # 红色
    deuteranopia_color = ColorBlindSimulator.apply_color_blind_filter(
        original_color, ColorBlindType.DEUTERANOPIA
    )
    print(f"\n原始颜色: {original_color}, 绿色盲视觉下: {deuteranopia_color}")
    
    # 获取键盘导航帮助
    keyboard_help = KeyboardNavigationHelper.get_keyboard_shortcut_help()
    print("\n键盘导航帮助部分内容:")
    print("\n".join(keyboard_help.split("\n")[:3]))  # 只显示前3行


if __name__ == "__main__":
    # 如果直接运行该模块，展示使用示例
    example_usage()
                if