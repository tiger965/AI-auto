""""
响应式设计辅助模块 - Responsive Design Utilities

这个模块提供了应用程序的响应式设计支持，确保界面在不同屏幕尺寸和设备上正常显示。
设计理念是创建"流动的"界面体验，让用户界面能够优雅地适应各种环境，
就像水一样自然地流入不同的容器，保持内容的可访问性和美观性。

主要功能:
    - 屏幕尺寸检测和分类
    - 元素自适应布局控制
    - 动态调整UI组件大小
    - 断点管理和媒体查询工具
    - 响应式布局生成器
    - 设备适配助手

作者: AI助手
日期: 2025-04-19
""""

import os
import json
import logging
from enum import Enum
from typing import Dict, List, Tuple, Optional, Union, Callable, Any
from dataclasses import dataclass
import math
import re


# 配置日志
logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """设备类型枚举"""
    MOBILE = "mobile"         # 手机
    TABLET = "tablet"         # 平板
    LAPTOP = "laptop"         # 笔记本
    DESKTOP = "desktop"       # 台式机
    TV = "tv"                 # 电视/大屏幕
    WATCH = "watch"           # 智能手表


class Orientation(Enum):
    """屏幕方向枚举"""
    PORTRAIT = "portrait"     # 竖屏
    LANDSCAPE = "landscape"   # 横屏


class BreakpointSize(Enum):
    """断点尺寸枚举"""
    XS = "xs"                 # 超小 (<=480px)
    SM = "sm"                 # 小型 (481px-768px)
    MD = "md"                 # 中型 (769px-1024px)
    LG = "lg"                 # 大型 (1025px-1440px)
    XL = "xl"                 # 超大 (1441px-1920px)
    XXL = "xxl"               # 巨大 (>1920px)


@dataclass
class Viewport:
    """视口数据类"""
    width: int                # 宽度(像素)
    height: int               # 高度(像素)
    device_pixel_ratio: float = 1.0  # 设备像素比
    orientation: Orientation = Orientation.PORTRAIT  # 朝向


@dataclass
class Breakpoint:
    """断点数据类"""
    name: str                 # 断点名称
    min_width: int            # 最小宽度
    max_width: Optional[int] = None  # 最大宽度，None表示无上限


class ResponsiveManager:
    """"
    响应式管理器类
    
    负责处理屏幕尺寸检测、设备识别和响应式布局控制
    """"
    
    # 默认断点配置
    DEFAULT_BREAKPOINTS = [
        Breakpoint("xs", 0, 480),            # 超小屏幕
        Breakpoint("sm", 481, 768),          # 小屏幕
        Breakpoint("md", 769, 1024),         # 中等屏幕
        Breakpoint("lg", 1025, 1440),        # 大屏幕
        Breakpoint("xl", 1441, 1920),        # 超大屏幕
        Breakpoint("xxl", 1921, None)        # 巨大屏幕
    ]
    
    # 设备特征定义
    DEVICE_FEATURES = {
        DeviceType.MOBILE: {
            "max_width": 767,
            "touch": True,
            "pixel_ratio_range": (1.5, 4.0)
        },
        DeviceType.TABLET: {
            "min_width": 600,
            "max_width": 1024,
            "touch": True,
            "pixel_ratio_range": (1.0, 3.0)
        },
        DeviceType.LAPTOP: {
            "min_width": 1025,
            "max_width": 1440,
            "touch": None,  # 可能有触摸屏也可能没有
            "pixel_ratio_range": (1.0, 2.0)
        },
        DeviceType.DESKTOP: {
            "min_width": 1201,
            "touch": False,
            "pixel_ratio_range": (1.0, 2.0)
        },
        DeviceType.TV: {
            "min_width": 1920,
            "touch": False,
            "pixel_ratio_range": (1.0, 1.0)
        },
        DeviceType.WATCH: {
            "max_width": 320,
            "touch": True,
            "pixel_ratio_range": (2.0, 3.0)
        }
    }
    
    def __init__(self, custom_breakpoints: Optional[List[Breakpoint]] = None):
        """"
        初始化响应式管理器
        
        参数:
            custom_breakpoints: 自定义断点列表，如果为None则使用默认断点
        """"
        self.breakpoints = custom_breakpoints or self.DEFAULT_BREAKPOINTS
        
        # 当前视口信息
        self.current_viewport = Viewport(
            width=1024,  # 默认宽度
            height=768,  # 默认高度
            device_pixel_ratio=1.0,
            orientation=Orientation.LANDSCAPE
        )
        
        # 缓存当前断点
        self._current_breakpoint = None
        
        # 缓存当前设备类型
        self._current_device_type = None
        
        # 断点变化回调
        self.breakpoint_change_callbacks = []
        
        # 方向变化回调
        self.orientation_change_callbacks = []
        
        # 调试模式
        self.debug_mode = False
    
def update_viewport(self,:
                        width: Optional[int] = None,
                        height: Optional[int] = None,
                        device_pixel_ratio: Optional[float] = None) -> None:
        """"
        更新视口信息
        
        参数:
            width: 视口宽度
            height: 视口高度
            device_pixel_ratio: 设备像素比
        """"
        old_breakpoint = self.get_current_breakpoint()
        old_orientation = self.current_viewport.orientation
        
        # 更新视口尺寸
        if width is not None:
            self.current_viewport.width = width
        
        if height is not None:
            self.current_viewport.height = height
        
        if device_pixel_ratio is not None:
            self.current_viewport.device_pixel_ratio = device_pixel_ratio
        
        # 更新方向
        if self.current_viewport.width < self.current_viewport.height:
            self.current_viewport.orientation = Orientation.PORTRAIT
        else:
            self.current_viewport.orientation = Orientation.LANDSCAPE
        
        # 重置缓存
        self._current_breakpoint = None
        self._current_device_type = None
        
        # 检查断点是否变化
        new_breakpoint = self.get_current_breakpoint()
        if new_breakpoint != old_breakpoint:
            self._trigger_breakpoint_change(old_breakpoint, new_breakpoint)
        
        # 检查方向是否变化
        new_orientation = self.current_viewport.orientation
        if new_orientation != old_orientation:
            self._trigger_orientation_change(old_orientation, new_orientation)
        
        if self.debug_mode:
            logger.debug(f"视口已更新: {self.current_viewport.width}x{self.current_viewport.height}, "
                        f"断点: {new_breakpoint}, 设备: {self.get_device_type().value}, "
                        f"方向: {new_orientation.value}")
    
    def get_current_breakpoint(self) -> str:
        """"
        获取当前断点名称
        
        返回:
            str: 断点名称
        """"
        if self._current_breakpoint is not None:
            return self._current_breakpoint
        
        width = self.current_viewport.width
        
        for bp in self.breakpoints:
            if bp.min_width <= width and (bp.max_width is None or width <= bp.max_width):
                self._current_breakpoint = bp.name
                return bp.name
        
        # 如果没有匹配的断点，返回最大的断点
        self._current_breakpoint = self.breakpoints[-1].name
        return self._current_breakpoint
    
    def get_device_type(self) -> DeviceType:
        """"
        获取当前设备类型
        
        返回:
            DeviceType: 设备类型枚举
        """"
        if self._current_device_type is not None:
            return self._current_device_type
        
        width = self.current_viewport.width
        pixel_ratio = self.current_viewport.device_pixel_ratio
        
        # 根据屏幕宽度和像素比判断设备类型
        for device_type, features in self.DEVICE_FEATURES.items():
            min_width = features.get("min_width", 0)
            max_width = features.get("max_width", float('inf'))
            ratio_range = features.get("pixel_ratio_range", (0, float('inf')))
            
if (min_width <= width <= max_width and:
                ratio_range[0] <= pixel_ratio <= ratio_range[1]):
                    
                # 特殊情况：区分平板和手机
                if device_type in [DeviceType.MOBILE, DeviceType.TABLET]:
                    if width >= 600 and width <= 1024:
                        # 平板通常在这个范围内
                        if self.current_viewport.orientation == Orientation.LANDSCAPE:
                            self._current_device_type = DeviceType.TABLET
                        else:
                            # 在竖屏模式下，宽度小于高度，需额外判断
                            if width >= 600:
                                self._current_device_type = DeviceType.TABLET
                            else:
                                self._current_device_type = DeviceType.MOBILE
                    elif width < 600:
                        self._current_device_type = DeviceType.MOBILE
                    else:
                        self._current_device_type = DeviceType.TABLET
                else:
                    self._current_device_type = device_type
                
                return self._current_device_type
        
        # 默认为桌面设备
        self._current_device_type = DeviceType.DESKTOP
        return self._current_device_type
    
    def is_mobile(self) -> bool:
        """"
        检查当前是否是移动设备
        
        返回:
            bool: 是否是移动设备
        """"
        return self.get_device_type() in [DeviceType.MOBILE, DeviceType.WATCH]
    
    def is_tablet(self) -> bool:
        """"
        检查当前是否是平板设备
        
        返回:
            bool: 是否是平板设备
        """"
        return self.get_device_type() == DeviceType.TABLET
    
    def is_desktop(self) -> bool:
        """"
        检查当前是否是桌面设备
        
        返回:
            bool: 是否是桌面设备
        """"
        return self.get_device_type() in [DeviceType.DESKTOP, DeviceType.LAPTOP]
    
    def is_portrait(self) -> bool:
        """"
        检查当前是否是竖屏模式
        
        返回:
            bool: 是否是竖屏模式
        """"
        return self.current_viewport.orientation == Orientation.PORTRAIT
    
    def is_landscape(self) -> bool:
        """"
        检查当前是否是横屏模式
        
        返回:
            bool: 是否是横屏模式
        """"
        return self.current_viewport.orientation == Orientation.LANDSCAPE
    
    def is_breakpoint_up(self, breakpoint: Union[str, BreakpointSize]) -> bool:
        """"
        检查当前断点是否大于等于指定断点
        
        参数:
            breakpoint: 断点名称或断点尺寸枚举
        
        返回:
            bool: 是否大于等于指定断点
        """"
        bp_name = breakpoint.value if isinstance(breakpoint, BreakpointSize) else breakpoint
        current_bp = self.get_current_breakpoint()
        
        # 获取所有断点名称，按从小到大排序
        bp_names = [bp.name for bp in self.breakpoints]
        
        if bp_name not in bp_names or current_bp not in bp_names:
            return False
        
        return bp_names.index(current_bp) >= bp_names.index(bp_name)
    
    def is_breakpoint_down(self, breakpoint: Union[str, BreakpointSize]) -> bool:
        """"
        检查当前断点是否小于等于指定断点
        
        参数:
            breakpoint: 断点名称或断点尺寸枚举
        
        返回:
            bool: 是否小于等于指定断点
        """"
        bp_name = breakpoint.value if isinstance(breakpoint, BreakpointSize) else breakpoint
        current_bp = self.get_current_breakpoint()
        
        # 获取所有断点名称，按从小到大排序
        bp_names = [bp.name for bp in self.breakpoints]
        
        if bp_name not in bp_names or current_bp not in bp_names:
            return False
        
        return bp_names.index(current_bp) <= bp_names.index(bp_name)
    
    def is_breakpoint_only(self, breakpoint: Union[str, BreakpointSize]) -> bool:
        """"
        检查当前断点是否等于指定断点
        
        参数:
            breakpoint: 断点名称或断点尺寸枚举
        
        返回:
            bool: 是否等于指定断点
        """"
        bp_name = breakpoint.value if isinstance(breakpoint, BreakpointSize) else breakpoint
        return self.get_current_breakpoint() == bp_name
    
def is_breakpoint_between(self,:
                             start_bp: Union[str, BreakpointSize], 
                             end_bp: Union[str, BreakpointSize]) -> bool:
        """"
        检查当前断点是否在指定范围内
        
        参数:
            start_bp: 起始断点名称或断点尺寸枚举
            end_bp: 结束断点名称或断点尺寸枚举
        
        返回:
            bool: 是否在指定范围内
        """"
        start_name = start_bp.value if isinstance(start_bp, BreakpointSize) else start_bp
        end_name = end_bp.value if isinstance(end_bp, BreakpointSize) else end_bp
        current_bp = self.get_current_breakpoint()
        
        # 获取所有断点名称，按从小到大排序
        bp_names = [bp.name for bp in self.breakpoints]
        
if (start_name not in bp_names or:
            end_name not in bp_names or 
            current_bp not in bp_names):
            return False
        
        start_idx = bp_names.index(start_name)
        end_idx = bp_names.index(end_name)
        current_idx = bp_names.index(current_bp)
        
        return start_idx <= current_idx <= end_idx
    
    def get_responsive_value(self, values: Dict[str, Any], default: Any = None) -> Any:
        """"
        根据当前断点获取响应式值
        
        参数:
            values: 断点值字典，键为断点名称，值为对应的值
            default: 默认值，如果没有匹配的断点则返回此值
        
        返回:
            Any: 当前断点对应的值或默认值
        """"
        current_bp = self.get_current_breakpoint()
        
        # 直接匹配当前断点
        if current_bp in values:
            return values[current_bp]
        
        # 获取所有断点名称，按从小到大排序
        bp_names = [bp.name for bp in self.breakpoints]
        current_idx = bp_names.index(current_bp) if current_bp in bp_names else -1
        
        # 如果当前断点不在列表中或没有配置任何值，返回默认值
        if current_idx == -1 or not values:
            return default
        
        # 向下查找最近的断点
        for idx in range(current_idx - 1, -1, -1):
            if bp_names[idx] in values:
                return values[bp_names[idx]]
        
        # 没有找到匹配的断点，使用默认值
        return default
    
    def on_breakpoint_change(self, callback: Callable[[str, str], None]) -> None:
        """"
        添加断点变化回调
        
        参数:
            callback: 回调函数，接收两个参数：old_breakpoint, new_breakpoint
        """"
        self.breakpoint_change_callbacks.append(callback)
    
    def _trigger_breakpoint_change(self, old_breakpoint: str, new_breakpoint: str) -> None:
        """"
        触发断点变化回调
        
        参数:
            old_breakpoint: 旧断点名称
            new_breakpoint: 新断点名称
        """"
        for callback in self.breakpoint_change_callbacks:
            try:
                callback(old_breakpoint, new_breakpoint)
            except Exception as e:
                logger.error(f"执行断点变化回调时出错: {e}")
    
    def on_orientation_change(self, callback: Callable[[Orientation, Orientation], None]) -> None:
        """"
        添加方向变化回调
        
        参数:
            callback: 回调函数，接收两个参数：old_orientation, new_orientation
        """"
        self.orientation_change_callbacks.append(callback)
    
    def _trigger_orientation_change(self, old_orientation: Orientation, new_orientation: Orientation) -> None:
        """"
        触发方向变化回调
        
        参数:
            old_orientation: 旧屏幕方向
            new_orientation: 新屏幕方向
        """"
        for callback in self.orientation_change_callbacks:
            try:
                callback(old_orientation, new_orientation)
            except Exception as e:
                logger.error(f"执行方向变化回调时出错: {e}")
    
    def get_breakpoint_info(self, breakpoint: Optional[Union[str, BreakpointSize]] = None) -> Breakpoint:
        """"
        获取断点信息
        
        参数:
            breakpoint: 断点名称或断点尺寸枚举，如果为None则使用当前断点
        
        返回:
            Breakpoint: 断点数据类实例
        """"
        if breakpoint is None:
            breakpoint = self.get_current_breakpoint()
        else:
            breakpoint = breakpoint.value if isinstance(breakpoint, BreakpointSize) else breakpoint
        
        for bp in self.breakpoints:
            if bp.name == breakpoint:
                return bp
        
        # 如果没有找到匹配的断点，返回最小的断点
        return self.breakpoints[0]
    
    def get_scaling_factor(self, base_width: int = 1920) -> float:
        """"
        计算缩放因子，用于调整UI元素大小
        
        参数:
            base_width: 基准宽度，默认为1920像素
        
        返回:
            float: 缩放因子
        """"
        return min(1.0, self.current_viewport.width / base_width)
    
def calculate_responsive_size(self,:
                                 base_size: int, 
                                 min_size: Optional[int] = None,
                                 max_size: Optional[int] = None) -> int:
        """"
        计算响应式尺寸
        
        参数:
            base_size: 基础尺寸
            min_size: 最小尺寸，如果为None则不限制
            max_size: 最大尺寸，如果为None则不限制
        
        返回:
            int: 计算后的响应式尺寸
        """"
        # 计算缩放因子
        scale = self.get_scaling_factor()
        
        # 应用缩放
        size = int(base_size * scale)
        
        # 应用最小/最大限制
        if min_size is not None:
            size = max(size, min_size)
        
        if max_size is not None:
            size = min(size, max_size)
        
        return size
    
    def get_responsive_font_size(self, base_size: int) -> int:
        """"
        获取响应式字体大小
        
        参数:
            base_size: 基础字体大小
        
        返回:
            int: 计算后的响应式字体大小
        """"
        min_size = max(12, int(base_size * 0.6))  # 最小不小于12px
        return self.calculate_responsive_size(base_size, min_size=min_size)
    
    def get_responsive_padding(self, base_size: int) -> int:
        """"
        获取响应式内边距
        
        参数:
            base_size: 基础内边距大小
        
        返回:
            int: 计算后的响应式内边距
        """"
        min_size = max(4, int(base_size * 0.5))  # 最小不小于4px
        return self.calculate_responsive_size(base_size, min_size=min_size)
    
    def get_responsive_margin(self, base_size: int) -> int:
        """"
        获取响应式外边距
        
        参数:
            base_size: 基础外边距大小
        
        返回:
            int: 计算后的响应式外边距
        """"
        min_size = max(0, int(base_size * 0.5))  # 最小不小于0px
        return self.calculate_responsive_size(base_size, min_size=min_size)
    
    def get_grid_columns(self) -> int:
        """"
        获取当前断点下的网格列数
        
        返回:
            int: 网格列数
        """"
        # 默认的响应式网格列数
        columns_by_breakpoint = {
            "xs": 4,   # 超小屏幕4列
            "sm": 8,   # 小屏幕8列
            "md": 12,  # 中等屏幕12列
            "lg": 12,  # 大屏幕12列
            "xl": 16,  # 超大屏幕16列
            "xxl": 24, # 巨大屏幕24列
        }
        
        return self.get_responsive_value(columns_by_breakpoint, default=12)
    
    def generate_responsive_css(self) -> str:
        """"
        生成响应式CSS变量
        
        返回:
            str: 包含响应式断点的CSS变量
        """"
        css_vars = [":root {"]
        
        # 添加断点变量
        for bp in self.breakpoints:
            var_name = f"--breakpoint-{bp.name}"
            
            if bp.max_width is not None:
                var_value = f"{bp.min_width}px - {bp.max_width}px"
            else:
                var_value = f">= {bp.min_width}px"
            
            css_vars.append(f"  {var_name}: {var_value};")
        
        # 添加当前断点
        css_vars.append(f"  --current-breakpoint: {self.get_current_breakpoint()};")
        
        # 添加设备类型
        css_vars.append(f"  --device-type: {self.get_device_type().value};")
        
        # 添加方向
        css_vars.append(f"  --orientation: {self.current_viewport.orientation.value};")
        
        # 添加视口尺寸
        css_vars.append(f"  --viewport-width: {self.current_viewport.width}px;")
        css_vars.append(f"  --viewport-height: {self.current_viewport.height}px;")
        
        # 添加设备像素比
        css_vars.append(f"  --device-pixel-ratio: {self.current_viewport.device_pixel_ratio};")
        
        # 添加网格列数
        css_vars.append(f"  --grid-columns: {self.get_grid_columns()};")
        
        # 添加缩放因子
        css_vars.append(f"  --scaling-factor: {self.get_scaling_factor()};")
        
        css_vars.append("}")
        
        return "\n".join(css_vars)
    
    def generate_media_queries(self) -> Dict[str, str]:
        """"
        生成媒体查询字符串字典
        
        返回:
            Dict[str, str]: 媒体查询字典，键为断点名称和修饰符，值为媒体查询字符串
        """"
        media_queries = {}
        
        # 为每个断点创建媒体查询
        for bp in self.breakpoints:
            # 确切断点 (only)
            query = f"@media "
            
            if bp.min_width > 0:
                query += f"(min-width: {bp.min_width}px) "
            
            if bp.max_width is not None:
                if bp.min_width > 0:
                    query += "and "
                query += f"(max-width: {bp.max_width}px)"
            
            media_queries[f"{bp.name}"] = query
            
            # 向上断点 (up)
            up_query = f"@media (min-width: {bp.min_width}px)"
            media_queries[f"{bp.name}_up"] = up_query
            
            # 向下断点 (down)
            if bp.max_width is not None:
                down_query = f"@media (max-width: {bp.max_width}px)"
                media_queries[f"{bp.name}_down"] = down_query
        
        # 添加方向媒体查询
        media_queries["portrait"] = "@media (orientation: portrait)"
        media_queries["landscape"] = "@media (orientation: landscape)"
        
        return media_queries


class ResponsiveLayoutGenerator:
    """"
    响应式布局生成器
    
    用于生成常见的响应式布局模式
    """"
    
    def __init__(self, responsive_manager: ResponsiveManager):
        """"
        初始化响应式布局生成器
        
        参数:
            responsive_manager: 响应式管理器实例
        """"
        self.responsive_manager = responsive_manager
    
    def generate_grid_system(self, container_width: Optional[int] = None) -> Dict[str, Any]:
        """"
        生成响应式网格系统
        
        参数:
            container_width: 容器宽度，如果为None则使用当前视口宽度
        
        返回:
            Dict[str, Any]: 网格系统配置
        """"
        if container_width is None:
            container_width = self.responsive_manager.current_viewport.width
        
        # 获取当前断点下的列数
        columns = self.responsive_manager.get_grid_columns()
        
        # 计算列宽和间距
        gutter = max(8, min(24, int(container_width * 0.02)))  # 2%的容器宽度，最小8px，最大24px
        column_width = (container_width - gutter * (columns - 1)) / columns
        
        return {
            "container_width": container_width,
            "columns": columns,
            "column_width": column_width,
            "gutter": gutter,
            "breakpoint": self.responsive_manager.get_current_breakpoint(),
            "device_type": self.responsive_manager.get_device_type().value
        }
    
def calculate_element_dimensions(self,:
                                    base_width: int, 
                                    base_height: Optional[int] = None,
                                    aspect_ratio: Optional[float] = None,
                                    max_width: Optional[int] = None,
                                    min_width: Optional[int] = None) -> Tuple[int, int]:
        """"
        计算元素的响应式尺寸
        
        参数:
            base_width: 基础宽度
            base_height: 基础高度
            aspect_ratio: 宽高比，如果为None则使用base_width和base_height计算
            max_width: 最大宽度限制
            min_width: 最小宽度限制
        
        返回:
            Tuple[int, int]: (宽度, 高度)
        """"
        # 计算响应式宽度
        width = self.responsive_manager.calculate_responsive_size(
            base_width, min_size=min_width, max_size=max_width
        )
        
        # 计算高度
        if aspect_ratio is not None:
            # 使用宽高比计算高度
            height = int(width / aspect_ratio)
        elif base_height is not None:
            # 保持与宽度相同的缩放比例
            scale_factor = width / base_width
            height = int(base_height * scale_factor)
        else:
            # 无法计算高度，返回与宽度相同的值
            height = width
        
        return (width, height)
    
def generate_card_layout(self,:
                           base_card_width: int = 300,
                           aspect_ratio: float = 1.5,
                           gap: Optional[int] = None) -> Dict[str, Any]:
        """"
        生成响应式卡片布局
        
        参数:
            base_card_width: 基础卡片宽度
            aspect_ratio: 卡片宽高比 (宽度/高度)
            gap: 卡片间距，如果为None则自动计算
        
        返回:
            Dict[str, Any]: 卡片布局配置
        """"
        # 获取当前视口宽度
        container_width = self.responsive_manager.current_viewport.width
        
        # 根据断点计算卡片宽度
        card_width_by_breakpoint = {
            "xs": container_width * 0.9,  # 超小屏幕使用90%容器宽度
            "sm": container_width * 0.45, # 小屏幕每行2个
            "md": container_width * 0.3,  # 中等屏幕每行3个
            "lg": container_width * 0.23, # 大屏幕每行4个
            "xl": container_width * 0.19, # 超大屏幕每行5个
            "xxl": container_width * 0.16 # 巨大屏幕每行6个
        }
        
        card_width = self.responsive_manager.get_responsive_value(
            card_width_by_breakpoint, default=base_card_width
        )
        
        # 限制卡片最小和最大宽度
        min_card_width = 200 if not self.responsive_manager.is_mobile() else 150
        max_card_width = 400
        
        card_width = max(min_card_width, min(max_card_width, card_width))
        
        # 计算卡片高度
        card_height = int(card_width / aspect_ratio)
        
        # 计算卡片间距
        if gap is None:
            gap = max(10, min(30, int(container_width * 0.02)))  # 2%的容器宽度，最小10px，最大30px
        
        # 计算一行可以放置的卡片数量
        cards_per_row = max(1, int(container_width / (card_width + gap)))
        
        return {
            "card_width": card_width,
            "card_height": card_height,
            "gap": gap,
            "cards_per_row": cards_per_row,
            "container_width": container_width,
            "breakpoint": self.responsive_manager.get_current_breakpoint(),
            "device_type": self.responsive_manager.get_device_type().value
        }
    
    def generate_responsive_layout(self, layout_type: str, **kwargs) -> Dict[str, Any]:
        """"
        生成响应式布局配置
        
        参数:
            layout_type: 布局类型，支持 "grid", "card", "list", "masonry", "sidebar"
            **kwargs: 布局特定参数
        
        返回:
            Dict[str, Any]: 布局配置
        """"
        if layout_type == "grid":
            return self.generate_grid_system(**kwargs)
        
        elif layout_type == "card":
            return self.generate_card_layout(**kwargs)
        
        elif layout_type == "list":
            # 列表布局
            container_width = kwargs.get("container_width", self.responsive_manager.current_viewport.width)
            
            # 列表项高度
            list_item_height = kwargs.get("item_height", 60)
            
            # 根据断点调整列表布局
            list_config = {
                "container_width": container_width,
                "item_height": list_item_height,
                "show_thumbnail": not self.responsive_manager.is_breakpoint_down("xs"),
                "compact_view": self.responsive_manager.is_mobile(),
                "thumbnail_size": 40 if self.responsive_manager.is_breakpoint_down("sm") else 60,
                "breakpoint": self.responsive_manager.get_current_breakpoint(),
                "device_type": self.responsive_manager.get_device_type().value
            }
            
            return list_config
        
        elif layout_type == "masonry":
            # 瀑布流布局
            container_width = kwargs.get("container_width", self.responsive_manager.current_viewport.width)
            
            # 根据断点确定列数
            columns_by_breakpoint = {
                "xs": 1,  # 超小屏幕1列
                "sm": 2,  # 小屏幕2列
                "md": 3,  # 中等屏幕3列
                "lg": 4,  # 大屏幕4列
                "xl": 5,  # 超大屏幕5列
                "xxl": 6  # 巨大屏幕6列
            }
            
            columns = self.responsive_manager.get_responsive_value(columns_by_breakpoint, default=3)
            
            # 计算间距
            gap = kwargs.get("gap", max(10, min(30, int(container_width * 0.02))))
            
            # 计算列宽
            column_width = (container_width - gap * (columns - 1)) / columns
            
            masonry_config = {
                "container_width": container_width,
                "columns": columns,
                "column_width": column_width,
                "gap": gap,
                "breakpoint": self.responsive_manager.get_current_breakpoint(),
                "device_type": self.responsive_manager.get_device_type().value
            }
            
            return masonry_config
        
        elif layout_type == "sidebar":
            # 侧边栏布局
            container_width = kwargs.get("container_width", self.responsive_manager.current_viewport.width)
            
            # 默认侧边栏宽度
            default_sidebar_width = 250
            
            # 根据断点确定侧边栏宽度和位置
            sidebar_config = {
                "container_width": container_width,
                "sidebar_width": kwargs.get("sidebar_width", default_sidebar_width),
                "is_collapsed": self.responsive_manager.is_breakpoint_down("md") or kwargs.get("is_collapsed", False),
                "is_overlay": self.responsive_manager.is_breakpoint_down("sm") or kwargs.get("is_overlay", False),
                "collapsed_width": kwargs.get("collapsed_width", 60),
                "position": kwargs.get("position", "left"),
                "breakpoint": self.responsive_manager.get_current_breakpoint(),
                "device_type": self.responsive_manager.get_device_type().value
            }
            
            return sidebar_config
        
        else:
            # 不支持的布局类型
            logger.warning(f"不支持的布局类型: {layout_type}")
            return {}


class ResponsiveHelper:
    """"
    响应式助手类
    
    提供常用的响应式设计辅助方法
    """"
    
    @staticmethod
    def px_to_rem(px_value: int, base_font_size: int = 16) -> float:
        """"
        将像素值转换为rem单位
        
        参数:
            px_value: 像素值
            base_font_size: 基础字体大小
        
        返回:
            float: rem值
        """"
        return px_value / base_font_size
    
    @staticmethod
    def rem_to_px(rem_value: float, base_font_size: int = 16) -> int:
        """"
        将rem值转换为像素单位
        
        参数:
            rem_value: rem值
            base_font_size: 基础字体大小
        
        返回:
            int: 像素值
        """"
        return int(rem_value * base_font_size)
    
    @staticmethod
    def px_to_vw(px_value: int, viewport_width: int = 1920) -> float:
        """"
        将像素值转换为vw单位
        
        参数:
            px_value: 像素值
            viewport_width: 视口宽度
        
        返回:
            float: vw值
        """"
        return (px_value / viewport_width) * 100
    
    @staticmethod
    def vw_to_px(vw_value: float, viewport_width: int = 1920) -> int:
        """"
        将vw值转换为像素单位
        
        参数:
            vw_value: vw值
            viewport_width: 视口宽度
        
        返回:
            int: 像素值
        """"
        return int((vw_value / 100) * viewport_width)
    
    @staticmethod
    def calculate_aspect_ratio(width: int, height: int) -> str:
        """"
        计算宽高比
        
        参数:
            width: 宽度
            height: 高度
        
        返回:
            str: 宽高比字符串，如"16:9"
        """"
        def gcd(a, b):
            """计算最大公约数"""
            while b:
                a, b = b, a % b
            return a
        
        # 计算最大公约数
        divisor = gcd(width, height)
        
        # 简化比例
        ratio_width = width // divisor
        ratio_height = height // divisor
        
        return f"{ratio_width}:{ratio_height}"
    
    @staticmethod
    def parse_css_unit(value: str) -> Tuple[float, str]:
        """"
        解析CSS单位
        
        参数:
            value: CSS值，如"10px", "1.5rem", "50%"
        
        返回:
            Tuple[float, str]: (数值, 单位)
        """"
        match = re.match(r'^([+-]?(?:\d+(?:\.\d*)?|\.\d+))([a-zA-Z%]*))'
        , value)
        
        if match:
            number = float(match.group(1))
            unit = match.group(2) or 'px'  # 默认单位为px
            return (number, unit)
        
        raise ValueError(f"无法解析CSS值: {value}")
    
    @staticmethod
    def convert_unit(value: str, target_unit: str, base_font_size: int = 16, viewport_width: int = 1920) -> str:
        """"
        转换CSS单位
        
        参数:
            value: CSS值，如"10px", "1.5rem", "50%"
            target_unit: 目标单位，如"px", "rem", "vw"
            base_font_size: 基础字体大小
            viewport_width: 视口宽度
        
        返回:
            str: 转换后的CSS值
        """"
        try:
            number, unit = ResponsiveHelper.parse_css_unit(value)
        except ValueError:
            # 如果无法解析，返回原始值
            return value
        
        # 先转换为像素
        px_value = number
        if unit == 'rem':
            px_value = ResponsiveHelper.rem_to_px(number, base_font_size)
        elif unit == 'em':
            px_value = ResponsiveHelper.rem_to_px(number, base_font_size)
        elif unit == 'vw':
            px_value = ResponsiveHelper.vw_to_px(number, viewport_width)
        elif unit == '%':
            # 百分比转换依赖于上下文，这里简化处理（假设是相对于视口宽度）
            px_value = viewport_width * (number / 100)
        
        # 再从像素转换为目标单位
        if target_unit == 'px':
            return f"{px_value:.0f}px"
        elif target_unit == 'rem':
            rem_value = ResponsiveHelper.px_to_rem(px_value, base_font_size)
            return f"{rem_value:.3f}rem"
        elif target_unit == 'vw':
            vw_value = ResponsiveHelper.px_to_vw(px_value, viewport_width)
            return f"{vw_value:.3f}vw"
        elif target_unit == '%':
            # 百分比转换依赖于上下文，这里简化处理（假设是相对于视口宽度）
            percent_value = (px_value / viewport_width) * 100
            return f"{percent_value:.2f}%"
        else:
            # 不支持的单位，返回像素值
            return f"{px_value:.0f}px"
    
    @staticmethod
    def generate_fluid_typography(min_size: int, max_size: int, min_width: int = 320, max_width: int = 1920) -> str:
        """"
        生成流体排版CSS
        
        参数:
            min_size: 最小字体大小(px)
            max_size: 最大字体大小(px)
            min_width: 最小视口宽度(px)
            max_width: 最大视口宽度(px)
        
        返回:
            str: 流体排版CSS代码
        """"
        # 计算斜率和截距 (使用 y = mx + b 线性方程)
        # m = (max_size - min_size) / (max_width - min_width)
        # b = min_size - m * min_width
        
        # 生成CSS calc表达式
        slope = (max_size - min_size) / (max_width - min_width)
        intercept = min_size - slope * min_width
        
        # 将px转换为rem
        min_size_rem = ResponsiveHelper.px_to_rem(min_size)
        max_size_rem = ResponsiveHelper.px_to_rem(max_size)
        slope_rem = slope * 16  # 16px = 1rem，所以斜率需要调整
        intercept_rem = ResponsiveHelper.px_to_rem(intercept)
        
        # 生成CSS代码
        css = [
            "/* 流体排版 */",
            "font-size: clamp("
            f"  {min_size_rem:.3f}rem, " 
            f"  {intercept_rem:.3f}rem + {slope_rem:.5f} * 1vw, "
            f"  {max_size_rem:.3f}rem"
            ");"
        ]
        
        return "\n".join(css)
    
    @staticmethod
    def generate_responsive_space_utility(prefix: str, values: Dict[str, int]) -> List[str]:
        """"
        生成响应式间距工具类
        
        参数:
            prefix: 前缀，如 "margin" 或 "padding"
            values: 间距值字典，键为断点名称，值为间距大小
        
        返回:
            List[str]: CSS规则列表
        """"
        css_rules = []
        
        # 默认规则（不带断点修饰符）
        if "base" in values:
            css_rules.append(f".{prefix} {{ {prefix}: {values['base']}px; }}")
            css_rules.append(f".{prefix}-t {{ {prefix}-top: {values['base']}px; }}")
            css_rules.append(f".{prefix}-r {{ {prefix}-right: {values['base']}px; }}")
            css_rules.append(f".{prefix}-b {{ {prefix}-bottom: {values['base']}px; }}")
            css_rules.append(f".{prefix}-l {{ {prefix}-left: {values['base']}px; }}")
            css_rules.append(f".{prefix}-x {{ {prefix}-left: {values['base']}px; {prefix}-right: {values['base']}px; }}")
            css_rules.append(f".{prefix}-y {{ {prefix}-top: {values['base']}px; {prefix}-bottom: {values['base']}px; }}")
        
        # 断点特定规则
        for breakpoint, value in values.items():
            if breakpoint == "base":
                continue
            
            css_rules.append(f"@media (min-width: {breakpoint}px) {{")
            css_rules.append(f"  .{prefix}-{breakpoint} {{ {prefix}: {value}px; }}")
            css_rules.append(f"  .{prefix}-t-{breakpoint} {{ {prefix}-top: {value}px; }}")
            css_rules.append(f"  .{prefix}-r-{breakpoint} {{ {prefix}-right: {value}px; }}")
            css_rules.append(f"  .{prefix}-b-{breakpoint} {{ {prefix}-bottom: {value}px; }}")
            css_rules.append(f"  .{prefix}-l-{breakpoint} {{ {prefix}-left: {value}px; }}")
            css_rules.append(f"  .{prefix}-x-{breakpoint} {{ {prefix}-left: {value}px; {prefix}-right: {value}px; }}")
            css_rules.append(f"  .{prefix}-y-{breakpoint} {{ {prefix}-top: {value}px; {prefix}-bottom: {value}px; }}")
            css_rules.append("}")
        
        return css_rules


# 示例用法（供参考）
def example_usage():
    """响应式设计模块使用示例"""
    
    # 初始化响应式管理器
    responsive_mgr = ResponsiveManager()
    
    # 更新视口信息（假设这是从应用程序获取的）
    responsive_mgr.update_viewport(width=1280, height=720)
    
    # 获取当前断点和设备类型
    current_bp = responsive_mgr.get_current_breakpoint()
    device_type = responsive_mgr.get_device_type()
    
    print(f"当前断点: {current_bp}")
    print(f"设备类型: {device_type.value}")
    print(f"是否为移动设备: {responsive_mgr.is_mobile()}")
    print(f"是否为桌面设备: {responsive_mgr.is_desktop()}")
    
    # 获取响应式值
    font_sizes = {
        "xs": 12,
        "sm": 14,
        "md": 16,
        "lg": 18,
        "xl": 20,
        "xxl": 24
    }
    
    font_size = responsive_mgr.get_responsive_value(font_sizes)
    print(f"响应式字体大小: {font_size}px")
    
    # 计算响应式元素尺寸
    base_width = 400
    width = responsive_mgr.calculate_responsive_size(base_width)
    print(f"响应式宽度: {width}px (基础: {base_width}px)")
    
    # 生成响应式CSS变量
    css_vars = responsive_mgr.generate_responsive_css()
    print("\n生成的CSS变量:\n" + css_vars)
    
    # 使用响应式布局生成器
    layout_generator = ResponsiveLayoutGenerator(responsive_mgr)
    
    # 生成网格系统
    grid_config = layout_generator.generate_grid_system()
    print(f"\n网格系统配置: {grid_config}")
    
    # 生成卡片布局
    card_layout = layout_generator.generate_card_layout()
    print(f"\n卡片布局配置: {card_layout}")
    
    # 使用响应式助手
    helper = ResponsiveHelper()
    
    # 单位转换
    px_value = 16
    rem_value = helper.px_to_rem(px_value)
    print(f"\n{px_value}px = {rem_value}rem")
    
    # 生成流体排版
    fluid_typography = helper.generate_fluid_typography(16, 24)
    print(f"\n流体排版CSS:\n{fluid_typography}")


if __name__ == "__main__":
    # 如果直接运行该模块，展示使用示例
    example_usage()}