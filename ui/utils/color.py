"""
颜色处理工具模块 - Color Utilities

这个模块提供了应用程序的颜色处理和管理功能，支持各种颜色空间转换和调色板生成。
设计理念是构建"有感情的色彩系统"，让颜色不仅具有视觉美感，还能传达情感和引导用户体验，
通过精心设计的色彩组合创造令人愉悦和易于使用的界面。

主要功能:
    - 颜色格式转换(HEX, RGB, HSL, HSV等)
    - 颜色混合和变换
    - 调色板和色彩方案生成
    - 颜色对比度计算
    - 无障碍颜色检查
    - 颜色命名和分类

作者: AI助手
日期: 2025-04-19
"""

import math
import re
import random
import logging
from enum import Enum
from typing import Tuple, List, Dict, Optional, Union, Any
from dataclasses import dataclass
import colorsys


# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class RGB:
    """RGB颜色数据类"""
    r: int  # 红色分量 (0-255)
    g: int  # 绿色分量 (0-255)
    b: int  # 蓝色分量 (0-255)
    a: float = 1.0  # 透明度 (0.0-1.0)
    
    def __post_init__(self):
        """验证并限制值范围"""
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))
        self.a = max(0.0, min(1.0, self.a))


@dataclass
class HSL:
    """HSL颜色数据类"""
    h: float  # 色相 (0-360)
    s: float  # 饱和度 (0.0-1.0)
    l: float  # 亮度 (0.0-1.0)
    a: float = 1.0  # 透明度 (0.0-1.0)
    
    def __post_init__(self):
        """验证并限制值范围"""
        self.h = self.h % 360
        self.s = max(0.0, min(1.0, self.s))
        self.l = max(0.0, min(1.0, self.l))
        self.a = max(0.0, min(1.0, self.a))


@dataclass
class HSV:
    """HSV颜色数据类"""
    h: float  # 色相 (0-360)
    s: float  # 饱和度 (0.0-1.0)
    v: float  # 明度 (0.0-1.0)
    a: float = 1.0  # 透明度 (0.0-1.0)
    
    def __post_init__(self):
        """验证并限制值范围"""
        self.h = self.h % 360
        self.s = max(0.0, min(1.0, self.s))
        self.v = max(0.0, min(1.0, self.v))
        self.a = max(0.0, min(1.0, self.a))


@dataclass
class CMYK:
    """CMYK颜色数据类"""
    c: float  # 青色 (0.0-1.0)
    m: float  # 品红 (0.0-1.0)
    y: float  # 黄色 (0.0-1.0)
    k: float  # 黑色 (0.0-1.0)
    
    def __post_init__(self):
        """验证并限制值范围"""
        self.c = max(0.0, min(1.0, self.c))
        self.m = max(0.0, min(1.0, self.m))
        self.y = max(0.0, min(1.0, self.y))
        self.k = max(0.0, min(1.0, self.k))


class ColorHarmony(Enum):
    """色彩和谐模式枚举"""
    MONOCHROMATIC = "monochromatic"      # 单色
    ANALOGOUS = "analogous"              # 类似色
    COMPLEMENTARY = "complementary"      # 互补色
    SPLIT_COMPLEMENTARY = "split"        # 分裂互补色
    TRIADIC = "triadic"                  # 三等分色
    TETRADIC = "tetradic"                # 四等分色
    SQUARE = "square"                    # 方形
    COMPOUND = "compound"                # 复合色


class Mood(Enum):
    """情绪主题枚举"""
    CALM = "calm"                       # 平静
    ENERGETIC = "energetic"             # 充满活力
    CHEERFUL = "cheerful"               # 愉快
    SERIOUS = "serious"                 # 严肃
    PLAYFUL = "playful"                 # 俏皮
    ELEGANT = "elegant"                 # 优雅
    NATURAL = "natural"                 # 自然
    PROFESSIONAL = "professional"       # 专业
    CREATIVE = "creative"               # 创意
    VINTAGE = "vintage"                 # 复古
    FUTURISTIC = "futuristic"           # 未来
    WARM = "warm"                       # 温暖
    COOL = "cool"                       # 冷酷
    BOLD = "bold"                       # 大胆
    SUBTLE = "subtle"                   # 微妙


@dataclass
class ColorInfo:
    """颜色信息数据类"""
    hex: str                           # 十六进制表示
    rgb: RGB                           # RGB数据
    hsl: HSL                           # HSL数据
    hsv: HSV                           # HSV数据
    name: Optional[str] = None         # 颜色名称
    is_dark: bool = False              # 是否是深色
    category: Optional[str] = None     # 颜色类别
    mood: Optional[Mood] = None        # 情绪感受


class Color:
    """
    颜色处理类
    
    提供颜色转换、操作和分析功能
    """
    
    # 常见颜色名称映射
    COLOR_NAMES = {
        "#FF0000": "红色",
        "#00FF00": "绿色",
        "#0000FF": "蓝色",
        "#FFFF00": "黄色",
        "#FF00FF": "品红",
        "#00FFFF": "青色",
        "#800000": "褐红色",
        "#008000": "深绿色",
        "#000080": "海军蓝",
        "#808000": "橄榄色",
        "#800080": "紫色",
        "#008080": "青绿色",
        "#FFFFFF": "白色",
        "#C0C0C0": "银色",
        "#808080": "灰色",
        "#000000": "黑色",
        "#FFA500": "橙色",
        "#A52A2A": "棕色",
        "#FFC0CB": "粉色",
        "#FFD700": "金色",
        "#E6E6FA": "淡紫色",
        "#90EE90": "淡绿色",
        "#ADD8E6": "淡蓝色",
    }
    
    # 颜色类别映射
    COLOR_CATEGORIES = {
        "red": {"min_h": 355, "max_h": 10},
        "orange": {"min_h": 10, "max_h": 45},
        "yellow": {"min_h": 45, "max_h": 70},
        "green": {"min_h": 70, "max_h": 170},
        "cyan": {"min_h": 170, "max_h": 200},
        "blue": {"min_h": 200, "max_h": 260},
        "purple": {"min_h": 260, "max_h": 320},
        "pink": {"min_h": 320, "max_h": 355},
        "brown": {"special": "brown"},
        "white": {"special": "white"},
        "gray": {"special": "gray"},
        "black": {"special": "black"}
    }
    
    # 情绪色彩映射
    MOOD_COLORS = {
        Mood.CALM: {
            "primary": "#4A90E2",
            "palette": ["#C5E0F5", "#93C0E9", "#4A90E2", "#2E6FC1", "#1E4C88"]
        },
        Mood.ENERGETIC: {
            "primary": "#FF5722",
            "palette": ["#FFCCBC", "#FF8A65", "#FF5722", "#E64A19", "#BF360C"]
        },
        Mood.CHEERFUL: {
            "primary": "#FFD54F",
            "palette": ["#FFF9C4", "#FFE082", "#FFD54F", "#FFC107", "#FFA000"]
        },
        Mood.SERIOUS: {
            "primary": "#455A64",
            "palette": ["#CFD8DC", "#90A4AE", "#607D8B", "#455A64", "#263238"]
        },
        Mood.PLAYFUL: {
            "primary": "#9C27B0",
            "palette": ["#E1BEE7", "#CE93D8", "#9C27B0", "#7B1FA2", "#4A148C"]
        },
        Mood.ELEGANT: {
            "primary": "#8D6E63",
            "palette": ["#D7CCC8", "#A1887F", "#8D6E63", "#6D4C41", "#4E342E"]
        },
        Mood.NATURAL: {
            "primary": "#8BC34A",
            "palette": ["#DCEDC8", "#AED581", "#8BC34A", "#689F38", "#33691E"]
        },
        Mood.PROFESSIONAL: {
            "primary": "#3F51B5",
            "palette": ["#C5CAE9", "#7986CB", "#3F51B5", "#303F9F", "#1A237E"]
        },
        Mood.CREATIVE: {
            "primary": "#E91E63",
            "palette": ["#F8BBD0", "#F06292", "#E91E63", "#C2185B", "#880E4F"]
        },
        Mood.VINTAGE: {
            "primary": "#BCAAA4",
            "palette": ["#EFEBE9", "#D7CCC8", "#BCAAA4", "#8D6E63", "#5D4037"]
        },
        Mood.FUTURISTIC: {
            "primary": "#00BCD4",
            "palette": ["#B2EBF2", "#4DD0E1", "#00BCD4", "#0097A7", "#006064"]
        },
        Mood.WARM: {
            "primary": "#FF9800",
            "palette": ["#FFE0B2", "#FFCC80", "#FF9800", "#F57C00", "#E65100"]
        },
        Mood.COOL: {
            "primary": "#448AFF",
            "palette": ["#BBD8FF", "#82B1FF", "#448AFF", "#2979FF", "#2962FF"]
        },
        Mood.BOLD: {
            "primary": "#F44336",
            "palette": ["#FFCDD2", "#EF9A9A", "#F44336", "#D32F2F", "#B71C1C"]
        },
        Mood.SUBTLE: {
            "primary": "#9E9E9E",
            "palette": ["#F5F5F5", "#E0E0E0", "#9E9E9E", "#616161", "#212121"]
        },
    }
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> RGB:
        """
        将十六进制颜色转换为RGB
        
        参数:
            hex_color: 十六进制颜色字符串，格式为"#RRGGBB"或"#RRGGBBAA"
        
        返回:
            RGB: RGB颜色对象
        """
        # 移除#前缀
        hex_color = hex_color.lstrip('#')
        
        # 根据长度不同处理
        if len(hex_color) == 3:
            # 简写形式 #RGB
            r = int(hex_color[0] + hex_color[0], 16)
            g = int(hex_color[1] + hex_color[1], 16)
            b = int(hex_color[2] + hex_color[2], 16)
            return RGB(r, g, b)
        elif len(hex_color) == 4:
            # 简写形式带透明度 #RGBA
            r = int(hex_color[0] + hex_color[0], 16)
            g = int(hex_color[1] + hex_color[1], 16)
            b = int(hex_color[2] + hex_color[2], 16)
            a = int(hex_color[3] + hex_color[3], 16) / 255
            return RGB(r, g, b, a)
        elif len(hex_color) == 6:
            # 标准形式 #RRGGBB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return RGB(r, g, b)
        elif len(hex_color) == 8:
            # 带透明度 #RRGGBBAA
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16) / 255
            return RGB(r, g, b, a)
        else:
            raise ValueError(f"无效的十六进制颜色格式: {hex_color}")
    
    @staticmethod
    def rgb_to_hex(rgb: RGB) -> str:
        """
        将RGB颜色转换为十六进制
        
        参数:
            rgb: RGB颜色对象
        
        返回:
            str: 十六进制颜色字符串
        """
        if rgb.a < 1.0:
            # 带透明度
            return f"#{rgb.r:02x}{rgb.g:02x}{rgb.b:02x}{int(rgb.a * 255):02x}"
        else:
            # 不带透明度
            return f"#{rgb.r:02x}{rgb.g:02x}{rgb.b:02x}"
    
    @staticmethod
    def rgb_to_hsl(rgb: RGB) -> HSL:
        """
        将RGB颜色转换为HSL
        
        参数:
            rgb: RGB颜色对象
        
        返回:
            HSL: HSL颜色对象
        """
        r, g, b = rgb.r / 255.0, rgb.g / 255.0, rgb.b / 255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        
        # colorsys返回的范围是0-1，转换为0-360度
        h = h * 360
        
        return HSL(h, s, l, rgb.a)
    
    @staticmethod
    def hsl_to_rgb(hsl: HSL) -> RGB:
        """
        将HSL颜色转换为RGB
        
        参数:
            hsl: HSL颜色对象
        
        返回:
            RGB: RGB颜色对象
        """
        h, s, l = hsl.h / 360.0, hsl.s, hsl.l
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        
        # 转换为0-255范围
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        return RGB(r, g, b, hsl.a)
    
    @staticmethod
    def rgb_to_hsv(rgb: RGB) -> HSV:
        """
        将RGB颜色转换为HSV
        
        参数:
            rgb: RGB颜色对象
        
        返回:
            HSV: HSV颜色对象
        """
        r, g, b = rgb.r / 255.0, rgb.g / 255.0, rgb.b / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        # 转换为0-360度
        h = h * 360
        
        return HSV(h, s, v, rgb.a)
    
    @staticmethod
    def hsv_to_rgb(hsv: HSV) -> RGB:
        """
        将HSV颜色转换为RGB
        
        参数:
            hsv: HSV颜色对象
        
        返回:
            RGB: RGB颜色对象
        """
        h, s, v = hsv.h / 360.0, hsv.s, hsv.v
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        # 转换为0-255范围
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        return RGB(r, g, b, hsv.a)
    
    @staticmethod
    def rgb_to_cmyk(rgb: RGB) -> CMYK:
        """
        将RGB颜色转换为CMYK
        
        参数:
            rgb: RGB颜色对象
        
        返回:
            CMYK: CMYK颜色对象
        """
        if rgb.r == 0 and rgb.g == 0 and rgb.b == 0:
            # 黑色特殊处理
            return CMYK(0, 0, 0, 1)
        
        # 归一化RGB值
        r, g, b = rgb.r / 255.0, rgb.g / 255.0, rgb.b / 255.0
        
        # 计算K (黑色)
        k = 1 - max(r, g, b)
        
        # 计算C, M, Y
        if k == 1:
            c, m, y = 0, 0, 0
        else:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)
        
        return CMYK(c, m, y, k)
    
    @staticmethod
    def cmyk_to_rgb(cmyk: CMYK) -> RGB:
        """
        将CMYK颜色转换为RGB
        
        参数:
            cmyk: CMYK颜色对象
        
        返回:
            RGB: RGB颜色对象
        """
        c, m, y, k = cmyk.c, cmyk.m, cmyk.y, cmyk.k
        
        # 计算RGB值
        r = int(255 * (1 - c) * (1 - k))
        g = int(255 * (1 - m) * (1 - k))
        b = int(255 * (1 - y) * (1 - k))
        
        return RGB(r, g, b)
    
    @staticmethod
    def hsl_to_hsv(hsl: HSL) -> HSV:
        """
        将HSL颜色转换为HSV
        
        参数:
            hsl: HSL颜色对象
        
        返回:
            HSV: HSV颜色对象
        """
        # 先转换为RGB，再转换为HSV
        rgb = Color.hsl_to_rgb(hsl)
        return Color.rgb_to_hsv(rgb)
    
    @staticmethod
    def hsv_to_hsl(hsv: HSV) -> HSL:
        """
        将HSV颜色转换为HSL
        
        参数:
            hsv: HSV颜色对象
        
        返回:
            HSL: HSL颜色对象
        """
        # 先转换为RGB，再转换为HSL
        rgb = Color.hsv_to_rgb(hsv)
        return Color.rgb_to_hsl(rgb)
    
    @staticmethod
    def parse_color(color_str: str) -> ColorInfo:
        """
        解析颜色字符串
        
        参数:
            color_str: 颜色字符串，支持多种格式
        
        返回:
            ColorInfo: 颜色信息对象
        """
        color_str = color_str.strip().lower()
        
        # 判断颜色格式
        if color_str.startswith('#'):
            # 十六进制格式
            rgb = Color.hex_to_rgb(color_str)
        elif color_str.startswith('rgb'):
            # RGB格式
            match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_str)
            if match:
                r = int(match.group(1))
                g = int(match.group(2))
                b = int(match.group(3))
                a = float(match.group(4)) if match.group(4) else 1.0
                rgb = RGB(r, g, b, a)
            else:
                raise ValueError(f"无效的RGB颜色格式: {color_str}")
        elif color_str.startswith('hsl'):
            # HSL格式
            match = re.match(r'hsla?\((\d+),\s*([\d.]+)%,\s*([\d.]+)%(?:,\s*([\d.]+))?\)', color_str)
            if match:
                h = float(match.group(1))
                s = float(match.group(2)) / 100
                l = float(match.group(3)) / 100
                a = float(match.group(4)) if match.group(4) else 1.0
                hsl = HSL(h, s, l, a)
                rgb = Color.hsl_to_rgb(hsl)
            else:
                raise ValueError(f"无效的HSL颜色格式: {color_str}")
        else:
            # 尝试作为颜色名称处理
            color_map = {name.lower(): code for code, name in Color.COLOR_NAMES.items()}
            if color_str in color_map:
                rgb = Color.hex_to_rgb(color_map[color_str])
            else:
                raise ValueError(f"不支持的颜色格式或未知的颜色名称: {color_str}")
        
        # 转换为各种格式
        hex_code = Color.rgb_to_hex(rgb)
        hsl = Color.rgb_to_hsl(rgb)
        hsv = Color.rgb_to_hsv(rgb)
        
        # 获取颜色名称
        name = Color.COLOR_NAMES.get(hex_code.upper())
        
        # 判断是否深色
        is_dark = Color.is_dark_color(rgb)
        
        # 获取颜色类别
        category = Color.get_color_category(hsl)
        
        # 获取情绪感受
        mood = Color.get_color_mood(hsl)
        
        return ColorInfo(hex_code, rgb, hsl, hsv, name, is_dark, category, mood)
    
    @staticmethod
    def is_dark_color(rgb: RGB) -> bool:
        """
        判断是否是深色
        
        参数:
            rgb: RGB颜色对象
        
        返回:
            bool: 是否是深色
        """
        # 使用相对亮度公式: (0.299*R + 0.587*G + 0.114*B)
        luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255
        
        # 亮度低于0.5认为是深色
        return luminance < 0.5
    
    @staticmethod
    def get_color_category(hsl: HSL) -> str:
        """
        获取颜色类别
        
        参数:
            hsl: HSL颜色对象
        
        返回:
            str: 颜色类别
        """
        h, s, l = hsl.h, hsl.s, hsl.l
        
        # 首先判断特殊情况
        if l <= 0.12:
            return "black"
        
        if l >= 0.95:
            return "white"
        
        if s <= 0.1 and 0.15 <= l <= 0.9:
            return "gray"
        
        if s <= 0.3 and l <= 0.35:
            return "brown"
        
        # 根据色相判断颜色类别
        for category, range_data in Color.COLOR_CATEGORIES.items():
            if "special" in range_data:
                continue
            
            min_h, max_h = range_data["min_h"], range_data["max_h"]
            
            if min_h <= h <= max_h or (min_h > max_h and (h >= min_h or h <= max_h)):
                return category
        
        # 默认返回
        return "unknown"
    
    @staticmethod
    def get_color_mood(hsl: HSL) -> Optional[Mood]:
        """
        获取颜色对应的情绪
        
        参数:
            hsl: HSL颜色对象
        
        返回:
            Optional[Mood]: 情绪枚举
        """
        h, s, l = hsl.h, hsl.s, hsl.l
        
        # 基于色相、饱和度和亮度的情绪映射
        if s < 0.2 and l > 0.8:
            # 低饱和度高亮度 - 淡雅
            return Mood.SUBTLE
        
        if s < 0.2 and l < 0.3:
            # 低饱和度低亮度 - 严肃
            return Mood.SERIOUS
        
        if s < 0.3 and 0.4 < l < 0.7:
            # 低饱和度中亮度 - 专业
            return Mood.PROFESSIONAL
        
        if 0.4 < s < 0.7 and 0.4 < l < 0.7:
            # 中等饱和度中等亮度
            if 0 <= h < 40 or 300 <= h <= 360:
                # 红色系 - 温暖
                return Mood.WARM
            elif 40 <= h < 70:
                # 黄色系 - 欢快
                return Mood.CHEERFUL
            elif 70 <= h < 170:
                # 绿色系 - 自然
                return Mood.NATURAL
            elif 170 <= h < 260:
                # 蓝色系 - 平静
                return Mood.CALM
            elif 260 <= h < 300:
                # 紫色系 - 创意
                return Mood.CREATIVE
        
        if s > 0.7 and l > 0.5:
            # 高饱和度高亮度 - 充满活力
            return Mood.ENERGETIC
        
        if s > 0.7 and l < 0.5:
            # 高饱和度低亮度 - 大胆
            return Mood.BOLD
        
        if 200 <= h <= 240 and s > 0.3:
            # 蓝色 - 冷酷
            return Mood.COOL
        
        # 默认返回None
        return None
    
    @staticmethod
    def lighten(color: Union[str, RGB, HSL], amount: float = 0.1) -> str:
        """
        增亮颜色
        
        参数:
            color: 颜色对象或字符串
            amount: 增亮量 (0.0-1.0)
        
        返回:
            str: 增亮后的十六进制颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 增加亮度
        new_l = min(1.0, hsl.l + amount)
        new_hsl = HSL(hsl.h, hsl.s, new_l, hsl.a)
        
        # 转换回RGB和十六进制
        new_rgb = Color.hsl_to_rgb(new_hsl)
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def darken(color: Union[str, RGB, HSL], amount: float = 0.1) -> str:
        """
        加深颜色
        
        参数:
            color: 颜色对象或字符串
            amount: 加深量 (0.0-1.0)
        
        返回:
            str: 加深后的十六进制颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 减少亮度
        new_l = max(0.0, hsl.l - amount)
        new_hsl = HSL(hsl.h, hsl.s, new_l, hsl.a)
        
        # 转换回RGB和十六进制
        new_rgb = Color.hsl_to_rgb(new_hsl)
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def saturate(color: Union[str, RGB, HSL], amount: float = 0.1) -> str:
        """
        增加颜色饱和度
        
        参数:
            color: 颜色对象或字符串
            amount: 增加量 (0.0-1.0)
        
        返回:
            str: 调整后的十六进制颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 增加饱和度
        new_s = min(1.0, hsl.s + amount)
        new_hsl = HSL(hsl.h, new_s, hsl.l, hsl.a)
        
        # 转换回RGB和十六进制
        new_rgb = Color.hsl_to_rgb(new_hsl)
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def desaturate(color: Union[str, RGB, HSL], amount: float = 0.1) -> str:
        """
        减少颜色饱和度
        
        参数:
            color: 颜色对象或字符串
            amount: 减少量 (0.0-1.0)
        
        返回:
            str: 调整后的十六进制颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 减少饱和度
        new_s = max(0.0, hsl.s - amount)
        new_hsl = HSL(hsl.h, new_s, hsl.l, hsl.a)
        
        # 转换回RGB和十六进制
        new_rgb = Color.hsl_to_rgb(new_hsl)
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def adjust_hue(color: Union[str, RGB, HSL], degrees: float) -> str:
        """
        调整颜色色相
        
        参数:
            color: 颜色对象或字符串
            degrees: 调整角度 (-360到360)
        
        返回:
            str: 调整后的十六进制颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 调整色相
        new_h = (hsl.h + degrees) % 360
        new_hsl = HSL(new_h, hsl.s, hsl.l, hsl.a)
        
        # 转换回RGB和十六进制
        new_rgb = Color.hsl_to_rgb(new_hsl)
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def grayscale(color: Union[str, RGB, HSL]) -> str:
        """
        将颜色转换为灰度
        
        参数:
            color: 颜色对象或字符串
        
        返回:
            str: 灰度化的十六进制颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 设置饱和度为0
        new_hsl = HSL(hsl.h, 0, hsl.l, hsl.a)
        
        # 转换回RGB和十六进制
        new_rgb = Color.hsl_to_rgb(new_hsl)
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def invert(color: Union[str, RGB]) -> str:
        """
        反转颜色
        
        参数:
            color: 颜色对象或字符串
        
        返回:
            str: 反转后的十六进制颜色
        """
        # 转换为RGB
        if isinstance(color, str):
            info = Color.parse_color(color)
            rgb = info.rgb
        elif isinstance(color, RGB):
            rgb = color
        else:
            raise TypeError("颜色必须是字符串或RGB对象")
        
        # 反转RGB值
        new_rgb = RGB(255 - rgb.r, 255 - rgb.g, 255 - rgb.b, rgb.a)
        
        # 转换为十六进制
        return Color.rgb_to_hex(new_rgb)
    
    @staticmethod
    def mix(color1: Union[str, RGB], color2: Union[str, RGB], weight: float = 0.5) -> str:
        """
        混合两种颜色
        
        参数:
            color1: 第一种颜色
            color2: 第二种颜色
            weight: 混合权重 (0.0-1.0)，1.0表示完全使用color1
        
        返回:
            str: 混合后的十六进制颜色
        """
        # 转换为RGB
        if isinstance(color1, str):
            info1 = Color.parse_color(color1)
            rgb1 = info1.rgb
        elif isinstance(color1, RGB):
            rgb1 = color1
        else:
            raise TypeError("颜色必须是字符串或RGB对象")
        
        if isinstance(color2, str):
            info2 = Color.parse_color(color2)
            rgb2 = info2.rgb
        elif isinstance(color2, RGB):
            rgb2 = color2
        else:
            raise TypeError("颜色必须是字符串或RGB对象")
        
        # 限制权重范围
        weight = max(0.0, min(1.0, weight))
        
        # 线性混合
        r = int(rgb1.r * weight + rgb2.r * (1 - weight))
        g = int(rgb1.g * weight + rgb2.g * (1 - weight))
        b = int(rgb1.b * weight + rgb2.b * (1 - weight))
        a = rgb1.a * weight + rgb2.a * (1 - weight)
        
        # 创建新的RGB对象
        mixed_rgb = RGB(r, g, b, a)
        
        # 转换为十六进制
        return Color.rgb_to_hex(mixed_rgb)
    
    @staticmethod
    def get_complementary(color: Union[str, RGB, HSL]) -> str:
        """
        获取互补色
        
        参数:
            color: 颜色对象或字符串
        
        返回:
            str: 互补色的十六进制表示
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 互补色的色相相差180度
        complementary_h = (hsl.h + 180) % 360
        complementary_hsl = HSL(complementary_h, hsl.s, hsl.l, hsl.a)
        
        # 转换为RGB和十六进制
        complementary_rgb = Color.hsl_to_rgb(complementary_hsl)
        return Color.rgb_to_hex(complementary_rgb)
    
    @staticmethod
    def get_analogous(color: Union[str, RGB, HSL], angle: int = 30, count: int = 3) -> List[str]:
        """
        获取类似色
        
        参数:
            color: 颜色对象或字符串
            angle: 色相角度差
            count: 颜色数量
        
        返回:
            List[str]: 类似色列表，包括原始颜色
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 确保count至少为1
        count = max(1, count)
        
        # 生成类似色
        result = []
        
        # 计算起始角度偏移
        start_offset = -angle * (count - 1) / 2
        
        for i in range(count):
            offset = start_offset + i * angle
            new_h = (hsl.h + offset) % 360
            new_hsl = HSL(new_h, hsl.s, hsl.l, hsl.a)
            new_rgb = Color.hsl_to_rgb(new_hsl)
            result.append(Color.rgb_to_hex(new_rgb))
        
        return result
    
    @staticmethod
    def get_triadic(color: Union[str, RGB, HSL]) -> List[str]:
        """
        获取三等分色
        
        参数:
            color: 颜色对象或字符串
        
        返回:
            List[str]: 三等分色列表
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 三等分色相差120度
        colors = []
        for i in range(3):
            new_h = (hsl.h + i * 120) % 360
            new_hsl = HSL(new_h, hsl.s, hsl.l, hsl.a)
            new_rgb = Color.hsl_to_rgb(new_hsl)
            colors.append(Color.rgb_to_hex(new_rgb))
        
        return colors
    
    @staticmethod
    def get_tetradic(color: Union[str, RGB, HSL]) -> List[str]:
        """
        获取四等分色
        
        参数:
            color: 颜色对象或字符串
        
        返回:
            List[str]: 四等分色列表
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 四等分色相差90度
        colors = []
        for i in range(4):
            new_h = (hsl.h + i * 90) % 360
            new_hsl = HSL(new_h, hsl.s, hsl.l, hsl.a)
            new_rgb = Color.hsl_to_rgb(new_hsl)
            colors.append(Color.rgb_to_hex(new_rgb))
        
        return colors
    
    @staticmethod
    def get_split_complementary(color: Union[str, RGB, HSL], angle: int = 30) -> List[str]:
        """
        获取分裂互补色
        
        参数:
            color: 颜色对象或字符串
            angle: 分裂角度
        
        返回:
            List[str]: 分裂互补色列表
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 获取互补色的色相
        comp_h = (hsl.h + 180) % 360
        
        # 计算分裂互补色
        colors = [Color.rgb_to_hex(Color.hsl_to_rgb(hsl))]  # 原色
        
        # 分裂互补色1
        split1_h = (comp_h - angle) % 360
        split1_hsl = HSL(split1_h, hsl.s, hsl.l, hsl.a)
        colors.append(Color.rgb_to_hex(Color.hsl_to_rgb(split1_hsl)))
        
        # 分裂互补色2
        split2_h = (comp_h + angle) % 360
        split2_hsl = HSL(split2_h, hsl.s, hsl.l, hsl.a)
        colors.append(Color.rgb_to_hex(Color.hsl_to_rgb(split2_hsl)))
        
        return colors
    
    @staticmethod
    def get_monochromatic(color: Union[str, RGB, HSL], count: int = 5) -> List[str]:
        """
        获取单色系列
        
        参数:
            color: 颜色对象或字符串
            count: 颜色数量
        
        返回:
            List[str]: 单色系列列表
        """
        # 转换为HSL
        if isinstance(color, str):
            info = Color.parse_color(color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(color)
        elif isinstance(color, HSL):
            hsl = color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 确保count至少为1
        count = max(1, count)
        
        # 生成不同亮度和饱和度的变体
        result = []
        
        for i in range(count):
            # 根据索引调整亮度和饱和度
            factor = i / (count - 1) if count > 1 else 0
            
            # 调整亮度从深到浅
            new_l = 0.1 + factor * 0.7  # 范围从0.1到0.8
            
            # 饱和度随亮度变化
            if factor < 0.5:
                # 深色部分，饱和度稍高
                new_s = min(1.0, hsl.s * (1.0 + 0.3 * (0.5 - factor)))
            else:
                # 浅色部分，饱和度稍低
                new_s = max(0.0, hsl.s * (1.0 - 0.3 * (factor - 0.5)))
            
            new_hsl = HSL(hsl.h, new_s, new_l, hsl.a)
            new_rgb = Color.hsl_to_rgb(new_hsl)
            result.append(Color.rgb_to_hex(new_rgb))
        
        return result
    
    @staticmethod
    def create_palette(base_color: Union[str, RGB, HSL], 
                      harmony: ColorHarmony = ColorHarmony.MONOCHROMATIC,
                      count: int = 5) -> List[str]:
        """
        创建色彩方案
        
        参数:
            base_color: 基础颜色
            harmony: 色彩和谐模式
            count: 颜色数量
        
        返回:
            List[str]: 颜色列表
        """
        if harmony == ColorHarmony.MONOCHROMATIC:
            return Color.get_monochromatic(base_color, count)
        
        elif harmony == ColorHarmony.ANALOGOUS:
            return Color.get_analogous(base_color, angle=30, count=count)
        
        elif harmony == ColorHarmony.COMPLEMENTARY:
            # 补充颜色以达到指定数量
            base_hex = Color.parse_color(base_color).hex if isinstance(base_color, str) else Color.rgb_to_hex(Color.hsl_to_rgb(base_color)) if isinstance(base_color, HSL) else Color.rgb_to_hex(base_color)
            comp_hex = Color.get_complementary(base_color)
            
            # 生成过渡色
            result = [base_hex]
            
            if count > 2:
                # 在这两种颜色之间添加过渡色
                for i in range(1, count - 1):
                    weight = 1.0 - (i / (count - 1))
                    result.append(Color.mix(base_hex, comp_hex, weight))
            
            result.append(comp_hex)
            return result
        
        elif harmony == ColorHarmony.SPLIT_COMPLEMENTARY:
            split_colors = Color.get_split_complementary(base_color)
            
            if count <= 3:
                return split_colors[:count]
            else:
                # 添加额外的过渡色
                result = [split_colors[0]]  # 基础色
                
                # 添加到第一个分裂色的过渡
                steps1 = (count - 3) // 2 + ((count - 3) % 2)  # 第一组过渡色数量
                for i in range(steps1):
                    weight = 1.0 - ((i + 1) / (steps1 + 1))
                    result.append(Color.mix(split_colors[0], split_colors[1], weight))
                
                # 添加第一个分裂色
                result.append(split_colors[1])
                
                # 添加到第二个分裂色的过渡
                steps2 = (count - 3) // 2  # 第二组过渡色数量
                for i in range(steps2):
                    weight = 1.0 - ((i + 1) / (steps2 + 1))
                    result.append(Color.mix(split_colors[1], split_colors[2], weight))
                
                # 添加第二个分裂色
                result.append(split_colors[2])
                
                return result
        
        elif harmony == ColorHarmony.TRIADIC:
            triadic_colors = Color.get_triadic(base_color)
            
            if count <= 3:
                return triadic_colors[:count]
            else:
                # 添加过渡色
                result = []
                
                for i in range(len(triadic_colors)):
                    result.append(triadic_colors[i])
                    
                    if i < len(triadic_colors) - 1:
                        steps = (count - 3) // 2 if i == 0 else (count - 3) - ((count - 3) // 2)
                        
                        for j in range(steps):
                            weight = 1.0 - ((j + 1) / (steps + 1))
                            result.append(Color.mix(triadic_colors[i], triadic_colors[i+1], weight))
                
                return result[:count]
        
        elif harmony == ColorHarmony.TETRADIC:
            tetradic_colors = Color.get_tetradic(base_color)
            
            if count <= 4:
                return tetradic_colors[:count]
            else:
                # 添加过渡色
                result = []
                
                for i in range(len(tetradic_colors)):
                    result.append(tetradic_colors[i])
                    
                    if i < len(tetradic_colors) - 1:
                        steps = (count - 4) // 3
                        if i < (count - 4) % 3:
                            steps += 1
                        
                        for j in range(steps):
                            weight = 1.0 - ((j + 1) / (steps + 1))
                            result.append(Color.mix(tetradic_colors[i], tetradic_colors[i+1], weight))
                
                return result[:count]
        
        elif harmony == ColorHarmony.SQUARE:
            # 正方形配色是特殊的四等分色
            return Color.get_tetradic(base_color)
        
        elif harmony == ColorHarmony.COMPOUND:
            # 复合配色是类似色加互补色的组合
            analogous = Color.get_analogous(base_color, angle=15, count=3)
            complement = Color.get_complementary(base_color)
            
            # 获取互补色的类似色
            comp_analogous = Color.get_analogous(complement, angle=15, count=2)
            
            # 结合所有颜色
            result = analogous + comp_analogous
            
            if count <= len(result):
                return result[:count]
            else:
                # 添加过渡色
                # ... 这里可以添加更复杂的过渡色逻辑
                return result
        
        else:
            # 默认返回单色系列
            return Color.get_monochromatic(base_color, count)
    
    @staticmethod
    def create_color_theme(base_color: Union[str, RGB, HSL], 
                          mood: Optional[Mood] = None) -> Dict[str, str]:
        """
        创建颜色主题
        
        参数:
            base_color: 基础颜色
            mood: 情绪主题
        
        返回:
            Dict[str, str]: 主题颜色字典
        """
        # 解析颜色
        if isinstance(base_color, str):
            info = Color.parse_color(base_color)
            hsl = info.hsl
        elif isinstance(color, RGB):
            hsl = Color.rgb_to_hsl(base_color)
        elif isinstance(color, HSL):
            hsl = base_color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 如果未指定情绪，根据颜色属性来猜测
        if mood is None:
            detected_mood = Color.get_color_mood(hsl)
            mood = detected_mood if detected_mood else Mood.CALM
        
        # 根据情绪选择合适的和谐模式
        harmony_map = {
            Mood.CALM: ColorHarmony.ANALOGOUS,
            Mood.ENERGETIC: ColorHarmony.TRIADIC,
            Mood.CHEERFUL: ColorHarmony.SPLIT_COMPLEMENTARY,
            Mood.SERIOUS: ColorHarmony.MONOCHROMATIC,
            Mood.PLAYFUL: ColorHarmony.TETRADIC,
            Mood.ELEGANT: ColorHarmony.ANALOGOUS,
            Mood.NATURAL: ColorHarmony.MONOCHROMATIC,
            Mood.PROFESSIONAL: ColorHarmony.MONOCHROMATIC,
            Mood.CREATIVE: ColorHarmony.TRIADIC,
            Mood.VINTAGE: ColorHarmony.ANALOGOUS,
            Mood.FUTURISTIC: ColorHarmony.COMPLEMENTARY,
            Mood.WARM: ColorHarmony.ANALOGOUS,
            Mood.COOL: ColorHarmony.ANALOGOUS,
            Mood.BOLD: ColorHarmony.SPLIT_COMPLEMENTARY,
            Mood.SUBTLE: ColorHarmony.MONOCHROMATIC
        }
        
        harmony = harmony_map.get(mood, ColorHarmony.MONOCHROMATIC)
        
        # 创建主色调
        base_hex = Color.rgb_to_hex(Color.hsl_to_rgb(hsl))
        
        # 创建辅助色
        palette = Color.create_palette(base_hex, harmony, count=5)
        
        # 创建主题色
        theme = {
            "primary": base_hex,
            "secondary": palette[-1] if len(palette) > 1 else Color.adjust_hue(base_hex, 30),
            "background": Color.lighten(Color.desaturate(base_hex, 0.7), 0.6),
            "surface": "#FFFFFF",
            "text": Color.get_contrast_color(Color.lighten(Color.desaturate(base_hex, 0.7), 0.6)),
            "accent": palette[1] if len(palette) > 2 else Color.adjust_hue(base_hex, 60)
        }
        
        # 添加调色板
        theme["palette"] = palette
        
        # 添加情绪标签
        theme["mood"] = mood.value
        
        return theme
    
    @staticmethod
    def get_contrast_color(color: Union[str, RGB, HSL]) -> str:
        """
        获取对比色（黑色或白色），以保证在背景色上有良好的可读性
        
        参数:
            color: 背景颜色
        
        返回:
            str: 对比色（黑色或白色）
        """
        # 转换为RGB
        if isinstance(color, str):
            info = Color.parse_color(color)
            rgb = info.rgb
        elif isinstance(color, RGB):
            rgb = color
        elif isinstance(color, HSL):
            rgb = Color.hsl_to_rgb(color)
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 计算相对亮度
        # 使用相对亮度公式: (0.299*R + 0.587*G + 0.114*B)
        luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255
        
        # 阈值为0.5，低于则使用白色，高于则使用黑色
        return "#FFFFFF" if luminance < 0.5 else "#000000"
    
    @staticmethod
    def calculate_contrast_ratio(color1: Union[str, RGB], color2: Union[str, RGB]) -> float:
        """
        计算两种颜色之间的对比度比率
        
        参数:
            color1: 第一种颜色
            color2: 第二种颜色
        
        返回:
            float: 对比度比率
        """
        def get_luminance(rgb):
            """计算相对亮度"""
            r, g, b = rgb.r / 255.0, rgb.g / 255.0, rgb.b / 255.0
            
            # sRGB颜色空间的伽马校正
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            
            # ITU-R BT.709系数的相对亮度
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        # 转换为RGB
        rgb1 = color1 if isinstance(color1, RGB) else Color.parse_color(color1).rgb
        rgb2 = color2 if isinstance(color2, RGB) else Color.parse_color(color2).rgb
        
        # 计算亮度
        l1 = get_luminance(rgb1)
        l2 = get_luminance(rgb2)
        
        # 确保l1是较亮的颜色（较大的值）
        if l1 < l2:
            l1, l2 = l2, l1
        
        # 计算对比度比率
        contrast_ratio = (l1 + 0.05) / (l2 + 0.05)
        
        return contrast_ratio
    
    @staticmethod
    def is_accessible(color1: Union[str, RGB], color2: Union[str, RGB], level: str = "AA") -> bool:
        """
        检查两种颜色的组合是否符合WCAG可访问性标准
        
        参数:
            color1: 第一种颜色
            color2: 第二种颜色
            level: 可访问性级别，"AA"或"AAA"
        
        返回:
            bool: 是否可访问
        """
        # 计算对比度比率
        ratio = Color.calculate_contrast_ratio(color1, color2)
        
        # 检查是否符合要求的级别
        # AA级：普通文本4.5:1，大文本3:1
        # AAA级：普通文本7:1，大文本4.5:1
        if level == "AA":
            return ratio >= 4.5  # 使用普通文本标准
        elif level == "AAA":
            return ratio >= 7.0  # 使用普通文本标准
        else:
            raise ValueError("不支持的可访问性级别，必须是'AA'或'AAA'")
    
    @staticmethod
    def generate_accessible_palette(base_color: Union[str, RGB, HSL], 
                                   background_color: Union[str, RGB, HSL] = "#FFFFFF",
                                   level: str = "AA") -> Dict[str, str]:
        """
        生成符合可访问性标准的调色板
        
        参数:
            base_color: 基础颜色
            background_color: 背景颜色
            level: 可访问性级别，"AA"或"AAA"
        
        返回:
            Dict[str, str]: 可访问调色板
        """
        # 解析颜色
        if isinstance(base_color, str):
            base_info = Color.parse_color(base_color)
            base_hsl = base_info.hsl
        elif isinstance(base_color, RGB):
            base_hsl = Color.rgb_to_hsl(base_color)
        elif isinstance(base_color, HSL):
            base_hsl = base_color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        if isinstance(background_color, str):
            bg_info = Color.parse_color(background_color)
            bg_rgb = bg_info.rgb
        elif isinstance(background_color, RGB):
            bg_rgb = background_color
        elif isinstance(background_color, HSL):
            bg_rgb = Color.hsl_to_rgb(background_color)
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 调整亮度直到符合可访问性标准
        adjusted_hsl = HSL(base_hsl.h, base_hsl.s, base_hsl.l, base_hsl.a)
        adjusted_rgb = Color.hsl_to_rgb(adjusted_hsl)
        
        step = 0.05  # 亮度调整步长
        max_iterations = 20  # 最大迭代次数
        
        for _ in range(max_iterations):
            # 检查当前颜色是否可访问
            if Color.is_accessible(adjusted_rgb, bg_rgb, level):
                break
            
            # 检查是黑色背景还是白色背景
            is_dark_bg = Color.is_dark_color(bg_rgb)
            
            if is_dark_bg:
                # 深色背景，增加颜色亮度
                adjusted_hsl.l = min(1.0, adjusted_hsl.l + step)
            else:
                # 浅色背景，减少颜色亮度
                adjusted_hsl.l = max(0.0, adjusted_hsl.l - step)
            
            # 更新RGB值
            adjusted_rgb = Color.hsl_to_rgb(adjusted_hsl)
        
        # 生成一个包含不同亮度值的调色板
        palette = {}
        
        # 主色调
        palette["primary"] = Color.rgb_to_hex(adjusted_rgb)
        
        # 浅色变体
        light_hsl = HSL(adjusted_hsl.h, adjusted_hsl.s, min(1.0, adjusted_hsl.l + 0.2), adjusted_hsl.a)
        palette["light"] = Color.rgb_to_hex(Color.hsl_to_rgb(light_hsl))
        
        # 深色变体
        dark_hsl = HSL(adjusted_hsl.h, adjusted_hsl.s, max(0.0, adjusted_hsl.l - 0.2), adjusted_hsl.a)
        palette["dark"] = Color.rgb_to_hex(Color.hsl_to_rgb(dark_hsl))
        
        # 次要颜色（色相偏移60度）
        secondary_hsl = HSL((adjusted_hsl.h + 60) % 360, adjusted_hsl.s, adjusted_hsl.l, adjusted_hsl.a)
        secondary_rgb = Color.hsl_to_rgb(secondary_hsl)
        
        # 调整次要颜色的亮度以符合可访问性标准
        for _ in range(max_iterations):
            if Color.is_accessible(secondary_rgb, bg_rgb, level):
                break
            
            if is_dark_bg:
                secondary_hsl.l = min(1.0, secondary_hsl.l + step)
            else:
                secondary_hsl.l = max(0.0, secondary_hsl.l - step)
            
            secondary_rgb = Color.hsl_to_rgb(secondary_hsl)
        
        palette["secondary"] = Color.rgb_to_hex(secondary_rgb)
        
        # 强调色（色相偏移180度）
        accent_hsl = HSL((adjusted_hsl.h + 180) % 360, adjusted_hsl.s, adjusted_hsl.l, adjusted_hsl.a)
        accent_rgb = Color.hsl_to_rgb(accent_hsl)
        
        # 调整强调色的亮度以符合可访问性标准
        for _ in range(max_iterations):
            if Color.is_accessible(accent_rgb, bg_rgb, level):
                break
            
            if is_dark_bg:
                accent_hsl.l = min(1.0, accent_hsl.l + step)
            else:
                accent_hsl.l = max(0.0, accent_hsl.l - step)
            
            accent_rgb = Color.hsl_to_rgb(accent_hsl)
        
        palette["accent"] = Color.rgb_to_hex(accent_rgb)
        
        # 背景色
        palette["background"] = Color.rgb_to_hex(bg_rgb)
        
        # 文本色（确保在背景上可见）
        text_color = Color.get_contrast_color(bg_rgb)
        palette["text"] = text_color
        
        return palette
    
    @staticmethod
    def generate_material_palette(base_color: Union[str, RGB, HSL]) -> Dict[str, str]:
        """
        生成Material Design风格的调色板
        
        参数:
            base_color: 基础颜色
        
        返回:
            Dict[str, str]: Material调色板
        """
        # 解析颜色
        if isinstance(base_color, str):
            base_info = Color.parse_color(base_color)
            base_hsl = base_info.hsl
        elif isinstance(base_color, RGB):
            base_hsl = Color.rgb_to_hsl(base_color)
        elif isinstance(base_color, HSL):
            base_hsl = base_color
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 创建不同亮度的变体
        palette = {}
        
        # 添加主色调（原色）
        base_hex = Color.rgb_to_hex(Color.hsl_to_rgb(base_hsl))
        palette["500"] = base_hex
        
        # 创建更亮的变体 (100, 200, 300, 400)
        lightness_steps = [0.8, 0.65, 0.5, 0.3]
        for i, step in enumerate(lightness_steps):
            level = (i + 1) * 100
            
            # 调整亮度和饱和度
            l_adjust = step
            s_adjust = -0.1 * (i + 1)
            
            variant_hsl = HSL(
                base_hsl.h,
                max(0, min(1, base_hsl.s + s_adjust)),
                max(0, min(1, base_hsl.l + l_adjust)),
                base_hsl.a
            )
            
            palette[str(level)] = Color.rgb_to_hex(Color.hsl_to_rgb(variant_hsl))
        
        # 创建更暗的变体 (600, 700, 800, 900)
        darkness_steps = [0.1, 0.2, 0.3, 0.4]
        for i, step in enumerate(darkness_steps):
            level = 600 + i * 100
            
            # 调整亮度和饱和度
            l_adjust = -step
            s_adjust = 0.05 * (i + 1)
            
            variant_hsl = HSL(
                base_hsl.h,
                max(0, min(1, base_hsl.s + s_adjust)),
                max(0, min(1, base_hsl.l + l_adjust)),
                base_hsl.a
            )
            
            palette[str(level)] = Color.rgb_to_hex(Color.hsl_to_rgb(variant_hsl))
        
        # 添加强调色 (A100, A200, A400, A700)
        # 稍微调整色相，增加饱和度
        accent_hsl = HSL(
            (base_hsl.h + 20) % 360,
            min(1, base_hsl.s + 0.2),
            base_hsl.l,
            base_hsl.a
        )
        
        accent_lightness = [0.7, 0.5, 0.3, 0.1]
        accent_levels = ["A100", "A200", "A400", "A700"]
        
        for i, (level, l_adjust) in enumerate(zip(accent_levels, accent_lightness)):
            variant_hsl = HSL(
                accent_hsl.h,
                accent_hsl.s,
                max(0, min(1, accent_hsl.l + l_adjust)),
                accent_hsl.a
            )
            
            palette[level] = Color.rgb_to_hex(Color.hsl_to_rgb(variant_hsl))
        
        return palette
    
    @staticmethod
    def get_color_name(color: Union[str, RGB, HSL]) -> str:
        """
        获取颜色的命名
        
        参数:
            color: 颜色对象或字符串
        
        返回:
            str: 颜色名称
        """
        # 解析颜色
        if isinstance(color, str):
            info = Color.parse_color(color)
            hex_code = info.hex.upper()
            rgb = info.rgb
            hsl = info.hsl
        elif isinstance(color, RGB):
            rgb = color
            hex_code = Color.rgb_to_hex(rgb).upper()
            hsl = Color.rgb_to_hsl(rgb)
        elif isinstance(color, HSL):
            hsl = color
            rgb = Color.hsl_to_rgb(hsl)
            hex_code = Color.rgb_to_hex(rgb).upper()
        else:
            raise TypeError("颜色必须是字符串、RGB或HSL对象")
        
        # 检查是否匹配预定义名称
        if hex_code in Color.COLOR_NAMES:
            return Color.COLOR_NAMES[hex_code]
        
        # 获取颜色类别
        category = Color.get_color_category(hsl)
        
        # 生成描述性名称
        if category == "white":
            return "白色"
        elif category == "black":
            return "黑色"
        elif category == "gray":
            if hsl.l < 0.3:
                return "深灰色"
            elif hsl.l > 0.7:
                return "浅灰色"
            else:
                return "灰色"
        else:
            # 根据饱和度和亮度添加修饰词
            prefix = ""
            suffix = ""
            
            if hsl.s < 0.3:
                prefix = "灰"
            elif hsl.s > 0.8:
                prefix = "艳"
            
            if hsl.l < 0.3:
                suffix = "深"
            elif hsl.l > 0.7:
                suffix = "浅"
            
            # 基础颜色名称
            base_name = ""
            if category == "red":
                base_name = "红色"
            elif category == "orange":
                base_name = "橙色"
            elif category == "yellow":
                base_name = "黄色"
            elif category == "green":
                base_name = "绿色"
            elif category == "cyan":
                base_name = "青色"
            elif category == "blue":
                base_name = "蓝色"
            elif category == "purple":
                base_name = "紫色"
            elif category == "pink":
                base_name = "粉色"
            elif category == "brown":
                base_name = "棕色"
            
            # 组合名称
            return f"{suffix}{prefix}{base_name}"
    
    @staticmethod
    def generate_random_color(saturation_range: Tuple[float, float] = (0.5, 1.0),
                             lightness_range: Tuple[float, float] = (0.3, 0.7)) -> str:
        """
        生成随机颜色
        
        参数:
            saturation_range: 饱和度范围
            lightness_range: 亮度范围
        
        返回:
            str: 随机颜色的十六进制表示
        """
        # 生成随机HSL值
        h = random.random() * 360
        s = random.uniform(saturation_range[0], saturation_range[1])
        l = random.uniform(lightness_range[0], lightness_range[1])
        
        # 创建HSL对象
        hsl = HSL(h, s, l)
        
        # 转换为十六进制
        rgb = Color.hsl_to_rgb(hsl)
        return Color.rgb_to_hex(rgb)
    
    @staticmethod
    def generate_random_palette(count: int = 5, 
                              harmony: ColorHarmony = ColorHarmony.MONOCHROMATIC) -> List[str]:
        """
        生成随机调色板
        
        参数:
            count: 颜色数量
            harmony: 色彩和谐模式
        
        返回:
            List[str]: 颜色列表
        """
        # 生成基础随机颜色
        base_color = Color.generate_random_color()
        
        # 使用已有方法创建调色板
        return Color.create_palette(base_color, harmony, count)


# 示例用法（供参考）
def example_usage():
    """颜色模块使用示例"""
    
    # 解析颜色
    color_info = Color.parse_color("#3F51B5")
    print(f"颜色解析: {color_info.hex}, RGB: {color_info.rgb}, HSL: {color_info.hsl}")
    
    # 颜色转换
    rgb = RGB(63, 81, 181)
    hex_color = Color.rgb_to_hex(rgb)
    print(f"RGB到HEX: {hex_color}")
    
    hsl = Color.rgb_to_hsl(rgb)
    print(f"RGB到HSL: h={hsl.h:.1f}, s={hsl.s:.2f}, l={hsl.l:.2f}")
    
    # 颜色变换
    print(f"变浅: {Color.lighten(hex_color, 0.2)}")
    print(f"变深: {Color.darken(hex_color, 0.2)}")
    print(f"增加饱和度: {Color.saturate(hex_color, 0.2)}")
    print(f"减少饱和度: {Color.desaturate(hex_color, 0.2)}")
    
    # 调色板生成
    print("\n单色调色板:")
    monochromatic = Color.get_monochromatic(hex_color)
    for color in monochromatic:
        print(color)
    
    print("\n互补色:")
    complement = Color.get_complementary(hex_color)
    print(complement)
    
    print("\n三等分色:")
    triadic = Color.get_triadic(hex_color)
    for color in triadic:
        print(color)
    
    # 主题生成
    theme = Color.create_color_theme(hex_color, Mood.CALM)
    print("\n生成主题:")
    for key, value in theme.items():
        if key != "palette":
            print(f"{key}: {value}")
    
    # 可访问性检查
    background = "#FFFFFF"
    contrast_ratio = Color.calculate_contrast_ratio(hex_color, background)
    print(f"\n对比度比率: {contrast_ratio:.2f}")
    print(f"AA级可访问: {Color.is_accessible(hex_color, background, 'AA')}")
    print(f"AAA级可访问: {Color.is_accessible(hex_color, background, 'AAA')}")
    
    # 生成Material调色板
    material_palette = Color.generate_material_palette(hex_color)
    print("\nMaterial调色板片段:")
    for key in ["500", "700", "A200"]:
        print(f"{key}: {material_palette[key]}")


if __name__ == "__main__":
    # 如果直接运行该模块，展示使用示例
    example_usage()