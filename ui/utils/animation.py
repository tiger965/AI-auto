"""
动画效果工具模块 - Animation Utilities

这个模块提供了应用程序的动画效果系统，用于创建流畅、自然的界面过渡和交互反馈。
设计理念是使界面动画带有一种"呼吸感"，让用户感受到界面是有生命的，而不是机械的。
动画效果应当优雅且有意义，既能引导用户注意力，又不会造成视觉疲劳。

主要功能:
    - 动画类型定义（淡入淡出、滑动、缩放等）
    - 动画时间曲线控制
    - 元素状态过渡效果
    - 加载和进度指示动画
    - 动画序列和组合控制

作者: AI助手
日期: 2025-04-19
"""

import time
import math
import threading
from enum import Enum
from typing import Callable, Dict, List, Tuple, Optional, Union, Any
import logging
from dataclasses import dataclass


# 配置日志
logger = logging.getLogger(__name__)


class AnimationType(Enum):
    """动画类型枚举"""
    FADE = "fade"               # 淡入淡出
    SLIDE = "slide"             # 滑动
    SCALE = "scale"             # 缩放
    ROTATE = "rotate"           # 旋转
    BOUNCE = "bounce"           # 弹跳
    PULSE = "pulse"             # 脉冲
    WAVE = "wave"               # 波浪
    TYPEWRITER = "typewriter"   # 打字机
    SHIMMER = "shimmer"         # 闪烁
    BREATHE = "breathe"         # 呼吸


class EasingType(Enum):
    """缓动函数类型枚举"""
    LINEAR = "linear"                   # 线性
    EASE_IN = "ease_in"                 # 渐入
    EASE_OUT = "ease_out"               # 渐出
    EASE_IN_OUT = "ease_in_out"         # 渐入渐出
    ELASTIC_IN = "elastic_in"           # 弹性渐入
    ELASTIC_OUT = "elastic_out"         # 弹性渐出
    ELASTIC_IN_OUT = "elastic_in_out"   # 弹性渐入渐出
    BOUNCE_IN = "bounce_in"             # 弹跳渐入
    BOUNCE_OUT = "bounce_out"           # 弹跳渐出
    BOUNCE_IN_OUT = "bounce_in_out"     # 弹跳渐入渐出
    SPRING = "spring"                   # 弹簧效果


class AnimationDirection(Enum):
    """动画方向枚举"""
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    CENTER = "center"


@dataclass
class AnimationConfig:
    """动画配置数据类"""
    type: AnimationType                          # 动画类型
    duration: float = 0.3                        # 动画持续时间（秒）
    easing: EasingType = EasingType.EASE_IN_OUT  # 缓动类型
    delay: float = 0.0                           # 动画延迟时间（秒）
    direction: Optional[AnimationDirection] = None  # 动画方向
    repeat: int = 0                              # 重复次数，0表示不重复，-1表示无限重复
    auto_reverse: bool = False                   # 是否自动反向播放
    intensity: float = 1.0                       # 动画强度（0.0-2.0）
    
    # 可选的自定义参数
    custom_params: Dict[str, Any] = None


class AnimationState(Enum):
    """动画状态枚举"""
    IDLE = "idle"           # 空闲
    RUNNING = "running"     # 运行中
    PAUSED = "paused"       # 暂停
    COMPLETED = "completed" # 已完成
    CANCELLED = "cancelled" # 已取消


class Animation:
    """
    动画基类
    
    提供动画的基本属性和方法，包括开始、暂停、恢复和停止等控制功能。
    """
    
    def __init__(self, config: AnimationConfig):
        """
        初始化动画实例
        
        参数:
            config: 动画配置
        """
        self.config = config
        self.state = AnimationState.IDLE
        self.progress = 0.0  # 0.0 - 1.0
        self.start_time = 0
        self.pause_time = 0
        self.pause_duration = 0
        self.current_iteration = 0
        self.on_update_callbacks = []
        self.on_complete_callbacks = []
        self.animation_thread = None
        self.should_stop = False
    
    def start(self) -> None:
        """开始动画"""
        if self.state == AnimationState.RUNNING:
            return
        
        if self.state == AnimationState.PAUSED:
            return self.resume()
        
        self.state = AnimationState.RUNNING
        self.start_time = time.time() + self.config.delay
        self.current_iteration = 0
        self.should_stop = False
        
        # 在新线程中运行动画
        self.animation_thread = threading.Thread(target=self._run_animation)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
        logger.debug(f"动画开始: {self.config.type.value}, 持续时间: {self.config.duration}秒")
    
    def _run_animation(self) -> None:
        """在线程中运行动画逻辑"""
        # 等待延迟时间
        if self.config.delay > 0:
            wait_until = self.start_time
            while time.time() < wait_until and not self.should_stop:
                time.sleep(0.01)
        
        while not self.should_stop:
            current_time = time.time()
            elapsed = current_time - self.start_time - self.pause_duration
            
            # 计算当前进度
            raw_progress = min(1.0, elapsed / self.config.duration)
            
            # 处理重复和自动反向
            if self.config.auto_reverse:
                iteration_progress = raw_progress % 2
                if iteration_progress > 1:
                    # 反向阶段
                    self.progress = 2 - iteration_progress
                else:
                    # 正向阶段
                    self.progress = iteration_progress
            else:
                self.progress = raw_progress % 1
            
            # 应用缓动函数
            eased_progress = self._apply_easing(self.progress)
            
            # 触发更新回调
            self._trigger_update(eased_progress)
            
            if raw_progress >= 1.0:
                if self.config.repeat == 0 or (self.config.repeat > 0 and self.current_iteration >= self.config.repeat - 1):
                    # 动画完成
                    self.state = AnimationState.COMPLETED
                    self._trigger_complete()
                    break
                else:
                    # 开始下一次迭代
                    self.current_iteration += 1
                    self.start_time = current_time - self.pause_duration
            
            time.sleep(1/60)  # 约60帧每秒
    
    def pause(self) -> None:
        """暂停动画"""
        if self.state == AnimationState.RUNNING:
            self.state = AnimationState.PAUSED
            self.pause_time = time.time()
            logger.debug(f"动画暂停: {self.config.type.value}, 进度: {self.progress:.2f}")
    
    def resume(self) -> None:
        """恢复动画"""
        if self.state == AnimationState.PAUSED:
            pause_elapsed = time.time() - self.pause_time
            self.pause_duration += pause_elapsed
            self.state = AnimationState.RUNNING
            logger.debug(f"动画恢复: {self.config.type.value}, 进度: {self.progress:.2f}")
    
    def stop(self) -> None:
        """停止动画"""
        if self.state in [AnimationState.RUNNING, AnimationState.PAUSED]:
            self.should_stop = True
            self.state = AnimationState.CANCELLED
            logger.debug(f"动画停止: {self.config.type.value}")
    
    def on_update(self, callback: Callable[[float], None]) -> None:
        """
        添加动画进度更新回调
        
        参数:
            callback: 回调函数，接收一个float参数表示当前进度(0.0-1.0)
        """
        self.on_update_callbacks.append(callback)
    
    def on_complete(self, callback: Callable[[], None]) -> None:
        """
        添加动画完成回调
        
        参数:
            callback: 回调函数，不接收参数
        """
        self.on_complete_callbacks.append(callback)
    
    def _trigger_update(self, progress: float) -> None:
        """触发更新回调"""
        for callback in self.on_update_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"动画更新回调出错: {e}")
    
    def _trigger_complete(self) -> None:
        """触发完成回调"""
        for callback in self.on_complete_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"动画完成回调出错: {e}")
    
    def _apply_easing(self, progress: float) -> float:
        """
        应用缓动函数
        
        参数:
            progress: 原始进度值(0.0-1.0)
        
        返回:
            float: 应用缓动后的进度值
        """
        easing_func = get_easing_function(self.config.easing)
        return easing_func(progress)


class AnimationGroup:
    """
    动画组，用于控制多个动画的组合
    """
    
    def __init__(self, animations: List[Animation], sequence: bool = False):
        """
        初始化动画组
        
        参数:
            animations: 动画列表
            sequence: 是否顺序播放，True表示顺序播放，False表示同时播放
        """
        self.animations = animations
        self.sequence = sequence
        self.current_index = 0
        self.state = AnimationState.IDLE
        self.on_all_complete_callbacks = []
    
    def start(self) -> None:
        """开始播放动画组"""
        if self.state == AnimationState.RUNNING:
            return
        
        self.state = AnimationState.RUNNING
        self.current_index = 0
        
        if self.sequence:
            # 顺序播放
            self._play_next()
        else:
            # 同时播放
            for animation in self.animations:
                animation.start()
                animation.on_complete(self._check_all_complete)
        
        logger.debug(f"动画组开始: 共{len(self.animations)}个动画, {'顺序' if self.sequence else '同时'}播放")
    
    def _play_next(self) -> None:
        """播放下一个动画"""
        if self.current_index < len(self.animations):
            current_animation = self.animations[self.current_index]
            current_animation.on_complete(self._on_animation_complete)
            current_animation.start()
        else:
            self._trigger_all_complete()
    
    def _on_animation_complete(self) -> None:
        """单个动画完成后的回调"""
        self.current_index += 1
        self._play_next()
    
    def _check_all_complete(self) -> None:
        """检查所有动画是否完成"""
        if all(animation.state == AnimationState.COMPLETED for animation in self.animations):
            self._trigger_all_complete()
    
    def _trigger_all_complete(self) -> None:
        """触发所有动画完成回调"""
        self.state = AnimationState.COMPLETED
        for callback in self.on_all_complete_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"动画组完成回调出错: {e}")
        
        logger.debug("动画组完成")
    
    def pause(self) -> None:
        """暂停所有动画"""
        for animation in self.animations:
            animation.pause()
        self.state = AnimationState.PAUSED
    
    def resume(self) -> None:
        """恢复所有动画"""
        for animation in self.animations:
            if animation.state == AnimationState.PAUSED:
                animation.resume()
        self.state = AnimationState.RUNNING
    
    def stop(self) -> None:
        """停止所有动画"""
        for animation in self.animations:
            animation.stop()
        self.state = AnimationState.CANCELLED
    
    def on_all_complete(self, callback: Callable[[], None]) -> None:
        """
        添加所有动画完成后的回调
        
        参数:
            callback: 回调函数，不接收参数
        """
        self.on_all_complete_callbacks.append(callback)


# 各种缓动函数实现

def linear(t: float) -> float:
    """线性缓动"""
    return t

def ease_in(t: float) -> float:
    """渐入缓动"""
    return t * t

def ease_out(t: float) -> float:
    """渐出缓动"""
    return t * (2 - t)

def ease_in_out(t: float) -> float:
    """渐入渐出缓动"""
    return t * t * (3 - 2 * t)

def elastic_in(t: float) -> float:
    """弹性渐入"""
    return sin(13 * (math.pi/2) * t) * pow(2, 10 * (t - 1))

def elastic_out(t: float) -> float:
    """弹性渐出"""
    return sin(-13 * (math.pi/2) * (t + 1)) * pow(2, -10 * t) + 1

def elastic_in_out(t: float) -> float:
    """弹性渐入渐出"""
    if t < 0.5:
        return 0.5 * sin(13 * (math.pi/2) * (2 * t)) * pow(2, 10 * ((2 * t) - 1))
    else:
        return 0.5 * (sin(-13 * (math.pi/2) * ((2 * t - 1) + 1)) * pow(2, -10 * (2 * t - 1)) + 2)

def bounce_in(t: float) -> float:
    """弹跳渐入"""
    return 1 - bounce_out(1 - t)

def bounce_out(t: float) -> float:
    """弹跳渐出"""
    if t < 4/11:
        return (121 * t * t) / 16
    elif t < 8/11:
        return (363 / 40.0 * t * t) - (99 / 10.0 * t) + 17/5.0
    elif t < 9/10:
        return (4356 / 361.0 * t * t) - (35442 / 1805.0 * t) + 16061/1805.0
    else:
        return (54 / 5.0 * t * t) - (513 / 25.0 * t) + 268/25.0

def bounce_in_out(t: float) -> float:
    """弹跳渐入渐出"""
    if t < 0.5:
        return 0.5 * bounce_in(t * 2)
    else:
        return 0.5 * bounce_out(t * 2 - 1) + 0.5

def spring(t: float) -> float:
    """弹簧效果"""
    return 1 - (math.cos(t * 4.5 * math.pi) * math.exp(-t * 6))

def sin(t: float) -> float:
    """正弦函数辅助方法"""
    return math.sin(t)


def get_easing_function(easing_type: EasingType) -> Callable[[float], float]:
    """
    获取缓动函数
    
    参数:
        easing_type: 缓动类型
    
    返回:
        Callable: 缓动函数
    """
    easing_functions = {
        EasingType.LINEAR: linear,
        EasingType.EASE_IN: ease_in,
        EasingType.EASE_OUT: ease_out,
        EasingType.EASE_IN_OUT: ease_in_out,
        EasingType.ELASTIC_IN: elastic_in,
        EasingType.ELASTIC_OUT: elastic_out,
        EasingType.ELASTIC_IN_OUT: elastic_in_out,
        EasingType.BOUNCE_IN: bounce_in,
        EasingType.BOUNCE_OUT: bounce_out,
        EasingType.BOUNCE_IN_OUT: bounce_in_out,
        EasingType.SPRING: spring
    }
    
    return easing_functions.get(easing_type, linear)


# 具体动画实现类

class FadeAnimation(Animation):
    """淡入淡出动画"""
    
    def __init__(self, duration: float = 0.3, fade_in: bool = True, **kwargs):
        """
        初始化淡入淡出动画
        
        参数:
            duration: 动画持续时间（秒）
            fade_in: 是否淡入，False表示淡出
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.FADE,
            duration=duration,
            **kwargs
        )
        super().__init__(config)
        self.fade_in = fade_in
    
    def _apply_animation(self, progress: float) -> float:
        """应用动画效果"""
        if self.fade_in:
            return progress
        else:
            return 1 - progress


class SlideAnimation(Animation):
    """滑动动画"""
    
    def __init__(self, 
                 duration: float = 0.3, 
                 direction: AnimationDirection = AnimationDirection.RIGHT,
                 distance: float = 100.0,
                 **kwargs):
        """
        初始化滑动动画
        
        参数:
            duration: 动画持续时间（秒）
            direction: 滑动方向
            distance: 滑动距离（像素）
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.SLIDE,
            duration=duration,
            direction=direction,
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['distance'] = distance
        
        super().__init__(config)
    
    def get_position(self, progress: float) -> Tuple[float, float]:
        """
        获取当前位置
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            Tuple[float, float]: (x偏移, y偏移)
        """
        distance = self.config.custom_params.get('distance', 100.0)
        
        if self.config.direction == AnimationDirection.LEFT:
            return (-distance * (1 - progress), 0)
        elif self.config.direction == AnimationDirection.RIGHT:
            return (distance * (1 - progress), 0)
        elif self.config.direction == AnimationDirection.UP:
            return (0, -distance * (1 - progress))
        elif self.config.direction == AnimationDirection.DOWN:
            return (0, distance * (1 - progress))
        else:
            return (0, 0)


class ScaleAnimation(Animation):
    """缩放动画"""
    
    def __init__(self, 
                 duration: float = 0.3, 
                 from_scale: float = 0.0,
                 to_scale: float = 1.0,
                 **kwargs):
        """
        初始化缩放动画
        
        参数:
            duration: 动画持续时间（秒）
            from_scale: 起始缩放比例
            to_scale: 结束缩放比例
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.SCALE,
            duration=duration,
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['from_scale'] = from_scale
        config.custom_params['to_scale'] = to_scale
        
        super().__init__(config)
    
    def get_scale(self, progress: float) -> float:
        """
        获取当前缩放值
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            float: 当前缩放比例
        """
        from_scale = self.config.custom_params.get('from_scale', 0.0)
        to_scale = self.config.custom_params.get('to_scale', 1.0)
        
        return from_scale + (to_scale - from_scale) * progress


class RotateAnimation(Animation):
    """旋转动画"""
    
    def __init__(self, 
                 duration: float = 0.3, 
                 from_angle: float = 0.0,
                 to_angle: float = 360.0,
                 **kwargs):
        """
        初始化旋转动画
        
        参数:
            duration: 动画持续时间（秒）
            from_angle: 起始角度（度）
            to_angle: 结束角度（度）
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.ROTATE,
            duration=duration,
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['from_angle'] = from_angle
        config.custom_params['to_angle'] = to_angle
        
        super().__init__(config)
    
    def get_rotation(self, progress: float) -> float:
        """
        获取当前旋转角度
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            float: 当前旋转角度（度）
        """
        from_angle = self.config.custom_params.get('from_angle', 0.0)
        to_angle = self.config.custom_params.get('to_angle', 360.0)
        
        return from_angle + (to_angle - from_angle) * progress


class PulseAnimation(Animation):
    """脉冲动画"""
    
    def __init__(self, 
                 duration: float = 0.5, 
                 min_scale: float = 0.9,
                 max_scale: float = 1.1,
                 **kwargs):
        """
        初始化脉冲动画
        
        参数:
            duration: 动画持续时间（秒）
            min_scale: 最小缩放比例
            max_scale: 最大缩放比例
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.PULSE,
            duration=duration,
            repeat=-1,  # 无限重复
            auto_reverse=True,  # 自动反向
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['min_scale'] = min_scale
        config.custom_params['max_scale'] = max_scale
        
        super().__init__(config)
    
    def get_scale(self, progress: float) -> float:
        """
        获取当前缩放值
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            float: 当前缩放比例
        """
        min_scale = self.config.custom_params.get('min_scale', 0.9)
        max_scale = self.config.custom_params.get('max_scale', 1.1)
        
        return min_scale + (max_scale - min_scale) * progress


class WaveAnimation(Animation):
    """波浪动画"""
    
    def __init__(self, 
                 duration: float = 1.0, 
                 amplitude: float = 10.0,
                 frequency: float = 2.0,
                 **kwargs):
        """
        初始化波浪动画
        
        参数:
            duration: 动画持续时间（秒）
            amplitude: 波浪振幅
            frequency: 波浪频率
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.WAVE,
            duration=duration,
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['amplitude'] = amplitude
        config.custom_params['frequency'] = frequency
        
        super().__init__(config)
    
    def get_offset(self, progress: float) -> float:
        """
        获取当前波浪偏移值
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            float: 当前偏移量
        """
        amplitude = self.config.custom_params.get('amplitude', 10.0)
        frequency = self.config.custom_params.get('frequency', 2.0)
        
        return amplitude * math.sin(progress * math.pi * 2 * frequency)


class TypewriterAnimation(Animation):
    """打字机动画"""
    
    def __init__(self, 
                 text: str,
                 duration: float = None,
                 chars_per_second: float = 20.0,
                 **kwargs):
        """
        初始化打字机动画
        
        参数:
            text: 要显示的文本
            duration: 动画持续时间（秒），如果指定则忽略chars_per_second
            chars_per_second: 每秒显示的字符数
            **kwargs: 其他动画配置参数
        """
        # 如果未指定持续时间，则根据文本长度和打字速度计算
        if duration is None:
            duration = len(text) / chars_per_second
        
        config = AnimationConfig(
            type=AnimationType.TYPEWRITER,
            duration=duration,
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['text'] = text
        
        super().__init__(config)
    
    def get_text(self, progress: float) -> str:
        """
        获取当前应显示的文本
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            str: 当前应显示的文本
        """
        full_text = self.config.custom_params.get('text', '')
        visible_length = int(len(full_text) * progress)
        return full_text[:visible_length]


class ShimmerAnimation(Animation):
    """闪烁动画"""
    
    def __init__(self, 
                 duration: float = 1.5, 
                 color_from: str = "#FFFFFF00",
                 color_to: str = "#FFFFFF80",
                 **kwargs):
        """
        初始化闪烁动画
        
        参数:
            duration: 动画持续时间（秒）
            color_from: 起始颜色（RGBA十六进制）
            color_to: 结束颜色（RGBA十六进制）
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.SHIMMER,
            duration=duration,
            repeat=-1,  # 无限重复
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['color_from'] = color_from
        config.custom_params['color_to'] = color_to
        
        super().__init__(config)
    
    def get_color(self, progress: float) -> str:
        """
        获取当前闪烁颜色
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            str: 当前颜色（RGBA十六进制）
        """
        # 这里实现一个简单的移动渐变效果
        # 实际使用时可能需要更复杂的效果
        adjusted_progress = (math.sin(progress * math.pi * 2) + 1) / 2
        return self._blend_colors(
            self.config.custom_params.get('color_from', "#FFFFFF00"),
            self.config.custom_params.get('color_to', "#FFFFFF80"),
            adjusted_progress
        )
    
    def _blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        """
        混合两种颜色
        
        参数:
            color1: 第一种颜色，RGBA十六进制格式
            color2: 第二种颜色，RGBA十六进制格式
            ratio: 混合比例，0表示完全使用color1，1表示完全使用color2
        
        返回:
            str: 混合后的颜色，RGBA十六进制格式
        """
        # 提取RGBA值
        r1 = int(color1[1:3], 16)
        g1 = int(color1[3:5], 16)
        b1 = int(color1[5:7], 16)
        a1 = int(color1[7:9], 16) if len(color1) > 7 else 255
        
        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)
        a2 = int(color2[7:9], 16) if len(color2) > 7 else 255
        
        # 线性混合
        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)
        a = int(a1 * (1 - ratio) + a2 * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


class BreatheAnimation(Animation):
    """呼吸动画"""
    
    def __init__(self, 
                 duration: float = 4.0, 
                 min_opacity: float = 0.4,
                 max_opacity: float = 1.0,
                 **kwargs):
        """
        初始化呼吸动画
        
        参数:
            duration: 动画持续时间（秒）
            min_opacity: 最小透明度
            max_opacity: 最大透明度
            **kwargs: 其他动画配置参数
        """
        config = AnimationConfig(
            type=AnimationType.BREATHE,
            duration=duration,
            repeat=-1,  # 无限重复
            easing=EasingType.EASE_IN_OUT,
            **kwargs
        )
        if config.custom_params is None:
            config.custom_params = {}
        config.custom_params['min_opacity'] = min_opacity
        config.custom_params['max_opacity'] = max_opacity
        
        super().__init__(config)
    
    def get_opacity(self, progress: float) -> float:
        """
        获取当前透明度
        
        参数:
            progress: 动画进度(0.0-1.0)
        
        返回:
            float: 当前透明度(0.0-1.0)
        """
        min_opacity = self.config.custom_params.get('min_opacity', 0.4)
        max_opacity = self.config.custom_params.get('max_opacity', 1.0)
        
        # 创建一个类似呼吸的效果：缓慢吸气（增加透明度），然后缓慢呼气（降低透明度）
        breathe_progress = (math.sin(progress * math.pi * 2 - math.pi/2) + 1) / 2
        return min_opacity + breathe_progress * (max_opacity - min_opacity)


# 预设动画配置

class AnimationPresets:
    """
    动画预设配置类
    提供常用的动画预设，便于快速应用
    """
    
    @staticmethod
    def fade_in(duration: float = 0.3, delay: float = 0.0) -> FadeAnimation:
        """淡入动画预设"""
        return FadeAnimation(
            duration=duration,
            fade_in=True,
            delay=delay,
            easing=EasingType.EASE_OUT
        )
    
    @staticmethod
    def fade_out(duration: float = 0.3, delay: float = 0.0) -> FadeAnimation:
        """淡出动画预设"""
        return FadeAnimation(
            duration=duration,
            fade_in=False,
            delay=delay,
            easing=EasingType.EASE_IN
        )
    
    @staticmethod
    def slide_in_left(duration: float = 0.4, distance: float = 100.0, delay: float = 0.0) -> SlideAnimation:
        """从左侧滑入动画预设"""
        return SlideAnimation(
            duration=duration,
            direction=AnimationDirection.LEFT,
            distance=distance,
            delay=delay,
            easing=EasingType.EASE_OUT
        )
    
    @staticmethod
    def slide_in_right(duration: float = 0.4, distance: float = 100.0, delay: float = 0.0) -> SlideAnimation:
        """从右侧滑入动画预设"""
        return SlideAnimation(
            duration=duration,
            direction=AnimationDirection.RIGHT,
            distance=distance,
            delay=delay,
            easing=EasingType.EASE_OUT
        )
    
    @staticmethod
    def slide_in_up(duration: float = 0.4, distance: float = 100.0, delay: float = 0.0) -> SlideAnimation:
        """从下方滑入动画预设"""
        return SlideAnimation(
            duration=duration,
            direction=AnimationDirection.UP,
            distance=distance,
            delay=delay,
            easing=EasingType.EASE_OUT
        )
    
    @staticmethod
    def slide_in_down(duration: float = 0.4, distance: float = 100.0, delay: float = 0.0) -> SlideAnimation:
        """从上方滑入动画预设"""
        return SlideAnimation(
            duration=duration,
            direction=AnimationDirection.DOWN,
            distance=distance,
            delay=delay,
            easing=EasingType.EASE_OUT
        )
    
    @staticmethod
    def scale_in(duration: float = 0.3, delay: float = 0.0) -> ScaleAnimation:
        """缩放显示动画预设"""
        return ScaleAnimation(
            duration=duration,
            from_scale=0.5,
            to_scale=1.0,
            delay=delay,
            easing=EasingType.ELASTIC_OUT
        )
    
    @staticmethod
    def scale_out(duration: float = 0.3, delay: float = 0.0) -> ScaleAnimation:
        """缩放隐藏动画预设"""
        return ScaleAnimation(
            duration=duration,
            from_scale=1.0,
            to_scale=0.5,
            delay=delay,
            easing=EasingType.EASE_IN
        )
    
    @staticmethod
    def rotate_in(duration: float = 0.5, delay: float = 0.0) -> RotateAnimation:
        """旋转显示动画预设"""
        return RotateAnimation(
            duration=duration,
            from_angle=-30.0,
            to_angle=0.0,
            delay=delay,
            easing=EasingType.EASE_OUT
        )
    
    @staticmethod
    def rotate_out(duration: float = 0.5, delay: float = 0.0) -> RotateAnimation:
        """旋转隐藏动画预设"""
        return RotateAnimation(
            duration=duration,
            from_angle=0.0,
            to_angle=30.0,
            delay=delay,
            easing=EasingType.EASE_IN
        )
    
    @staticmethod
    def gentle_pulse() -> PulseAnimation:
        """温和脉冲动画预设"""
        return PulseAnimation(
            duration=1.2,
            min_scale=0.95,
            max_scale=1.05,
            easing=EasingType.EASE_IN_OUT
        )
    
    @staticmethod
    def attention_pulse() -> PulseAnimation:
        """注意力脉冲动画预设"""
        return PulseAnimation(
            duration=0.5,
            min_scale=0.9,
            max_scale=1.1,
            easing=EasingType.BOUNCE_IN_OUT,
            repeat=3
        )
    
    @staticmethod
    def wave_effect(duration: float = 1.0, amplitude: float = 10.0) -> WaveAnimation:
        """波浪效果动画预设"""
        return WaveAnimation(
            duration=duration,
            amplitude=amplitude,
            frequency=1.5,
            easing=EasingType.LINEAR
        )
    
    @staticmethod
    def typewriter(text: str, chars_per_second: float = 10.0) -> TypewriterAnimation:
        """打字机动画预设"""
        return TypewriterAnimation(
            text=text,
            chars_per_second=chars_per_second,
            easing=EasingType.LINEAR
        )
    
    @staticmethod
    def shimmer_effect() -> ShimmerAnimation:
        """闪烁效果动画预设"""
        return ShimmerAnimation(
            duration=2.0,
            color_from="#FFFFFF00",
            color_to="#FFFFFF80",
            easing=EasingType.LINEAR
        )
    
    @staticmethod
    def calm_breathing() -> BreatheAnimation:
        """平静呼吸动画预设"""
        return BreatheAnimation(
            duration=5.0,
            min_opacity=0.7,
            max_opacity=1.0,
            easing=EasingType.EASE_IN_OUT
        )
    
    @staticmethod
    def deep_breathing() -> BreatheAnimation:
        """深呼吸动画预设"""
        return BreatheAnimation(
            duration=8.0,
            min_opacity=0.4,
            max_opacity=1.0,
            easing=EasingType.EASE_IN_OUT
        )
    
    @staticmethod
    def bouncy_entrance() -> AnimationGroup:
        """弹跳入场动画组预设"""
        fade = FadeAnimation(
            duration=0.3,
            fade_in=True,
            easing=EasingType.EASE_OUT
        )
        
        scale = ScaleAnimation(
            duration=0.5,
            from_scale=0.3,
            to_scale=1.0,
            easing=EasingType.BOUNCE_OUT
        )
        
        return AnimationGroup([fade, scale], sequence=False)
    
    @staticmethod
    def smooth_entrance() -> AnimationGroup:
        """平滑入场动画组预设"""
        fade = FadeAnimation(
            duration=0.4,
            fade_in=True,
            easing=EasingType.EASE_OUT
        )
        
        slide = SlideAnimation(
            duration=0.4,
            direction=AnimationDirection.UP,
            distance=30.0,
            easing=EasingType.EASE_OUT
        )
        
        return AnimationGroup([fade, slide], sequence=False)
    
    @staticmethod
    def elegant_exit() -> AnimationGroup:
        """优雅退场动画组预设"""
        fade = FadeAnimation(
            duration=0.4,
            fade_in=False,
            easing=EasingType.EASE_IN
        )
        
        scale = ScaleAnimation(
            duration=0.4,
            from_scale=1.0,
            to_scale=0.95,
            easing=EasingType.EASE_IN
        )
        
        return AnimationGroup([fade, scale], sequence=False)


# 功能类：加载动画

class LoadingAnimation:
    """
    加载动画类
    提供各种类型的加载动画
    """
    
    class Type(Enum):
        """加载动画类型枚举"""
        SPINNER = "spinner"             # 旋转加载
        DOTS = "dots"                   # 点动画
        PROGRESS = "progress"           # 进度条
        RIPPLE = "ripple"               # 波纹
        GRADIENT = "gradient"           # 渐变
        SKELETON = "skeleton"           # 骨架屏
    
    def __init__(self, animation_type: Type = Type.SPINNER, config: Dict[str, Any] = None):
        """
        初始化加载动画
        
        参数:
            animation_type: 动画类型
            config: 动画配置
        """
        self.animation_type = animation_type
        self.config = config or {}
        self.animation = self._create_animation()
        self.is_running = False
    
    def _create_animation(self) -> Animation:
        """创建具体的动画实例"""
        if self.animation_type == self.Type.SPINNER:
            return RotateAnimation(
                duration=self.config.get('duration', 1.0),
                from_angle=0.0,
                to_angle=360.0,
                repeat=-1,  # 无限重复
                easing=EasingType.LINEAR
            )
        
        elif self.animation_type == self.Type.DOTS:
            # 创建一组点的动画
            animations = []
            for i in range(3):  # 假设有3个点
                pulse = PulseAnimation(
                    duration=self.config.get('duration', 0.6),
                    min_scale=0.5,
                    max_scale=1.0,
                    delay=i * 0.2,  # 错开开始时间
                    repeat=-1,
                    easing=EasingType.EASE_IN_OUT
                )
                animations.append(pulse)
            
            return AnimationGroup(animations, sequence=False)
        
        elif self.animation_type == self.Type.PROGRESS:
            # 进度条动画
            return Animation(AnimationConfig(
                type=AnimationType.SLIDE,
                duration=self.config.get('duration', 2.0),
                repeat=-1,
                easing=EasingType.LINEAR
            ))
        
        elif self.animation_type == self.Type.RIPPLE:
            # 波纹动画
            animations = []
            for i in range(3):  # 三个波纹
                scale = ScaleAnimation(
                    duration=self.config.get('duration', 1.5),
                    from_scale=0.0,
                    to_scale=1.0,
                    delay=i * 0.5,  # 错开开始时间
                    repeat=-1,
                    easing=EasingType.EASE_OUT
                )
                
                fade = FadeAnimation(
                    duration=self.config.get('duration', 1.5),
                    fade_in=False,
                    delay=i * 0.5,  # 与缩放同步
                    repeat=-1,
                    easing=EasingType.EASE_OUT
                )
                
                animations.extend([scale, fade])
            
            return AnimationGroup(animations, sequence=False)
        
        elif self.animation_type == self.Type.GRADIENT:
            # 渐变动画
            return ShimmerAnimation(
                duration=self.config.get('duration', 1.5),
                color_from=self.config.get('color_from', "#FFFFFF00"),
                color_to=self.config.get('color_to', "#FFFFFF80"),
                repeat=-1,
                easing=EasingType.LINEAR
            )
        
        elif self.animation_type == self.Type.SKELETON:
            # 骨架屏动画
            return ShimmerAnimation(
                duration=self.config.get('duration', 1.8),
                color_from="#EEEEEE",
                color_to="#F8F8F8",
                repeat=-1,
                easing=EasingType.LINEAR
            )
        
        else:
            # 默认返回旋转动画
            return RotateAnimation(
                duration=1.0,
                from_angle=0.0,
                to_angle=360.0,
                repeat=-1,
                easing=EasingType.LINEAR
            )
    
    def start(self) -> None:
        """开始加载动画"""
        if not self.is_running:
            self.animation.start()
            self.is_running = True
    
    def stop(self) -> None:
        """停止加载动画"""
        if self.is_running:
            self.animation.stop()
            self.is_running = False
    
    def on_update(self, callback: Callable[[float], None]) -> None:
        """
        添加更新回调
        
        参数:
            callback: 动画更新回调函数
        """
        self.animation.on_update(callback)


# 工具函数

def chain_animations(animations: List[Animation], delay: float = 0.0) -> AnimationGroup:
    """
    创建顺序播放的动画链
    
    参数:
        animations: 要链接的动画列表
        delay: 每个动画之间的延迟时间
    
    返回:
        AnimationGroup: 动画组
    """
    if delay > 0:
        # 为每个动画添加延迟
        for i in range(1, len(animations)):
            animations[i].config.delay += delay * i
    
    return AnimationGroup(animations, sequence=True)


def stagger_animations(animation_factory: Callable[[], Animation], 
                       count: int, 
                       stagger_delay: float = 0.1) -> AnimationGroup:
    """
    创建错开开始时间的多个相似动画
    
    参数:
        animation_factory: 创建动画的工厂函数
        count: 动画数量
        stagger_delay: 每个动画之间的延迟时间
    
    返回:
        AnimationGroup: 动画组
    """
    animations = []
    
    for i in range(count):
        animation = animation_factory()
        animation.config.delay += stagger_delay * i
        animations.append(animation)
    
    return AnimationGroup(animations, sequence=False)


def animate_property(target_obj: Any, 
                     property_name: str, 
                     end_value: Any, 
                     duration: float = 0.3,
                     easing: EasingType = EasingType.EASE_IN_OUT) -> Animation:
    """
    动画更改对象属性值
    
    参数:
        target_obj: 目标对象
        property_name: 属性名称
        end_value: 目标值
        duration: 动画持续时间
        easing: 缓动类型
    
    返回:
        Animation: 动画对象
    """
    # 获取起始值
    start_value = getattr(target_obj, property_name)
    
    # 确定值类型并创建合适的动画
    if isinstance(start_value, (int, float)) and isinstance(end_value, (int, float)):
        # 数值类型
        config = AnimationConfig(
            type=AnimationType.FADE,  # 使用FADE类型作为基础
            duration=duration,
            easing=easing
        )
        
        animation = Animation(config)
        
        def update_property(progress):
            current = start_value + (end_value - start_value) * progress
            setattr(target_obj, property_name, current)
        
        animation.on_update(update_property)
        return animation
        
    elif isinstance(start_value, str) and start_value.startswith("#") and isinstance(end_value, str) and end_value.startswith("#"):
        # 颜色类型
        config = AnimationConfig(
            type=AnimationType.FADE,
            duration=duration,
            easing=easing
        )
        
        animation = Animation(config)
        
        def blend_color(progress):
            from_color = start_value.lstrip("#")
            to_color = end_value.lstrip("#")
            
            r1, g1, b1 = tuple(int(from_color[i:i+2], 16) for i in (0, 2, 4))
            r2, g2, b2 = tuple(int(to_color[i:i+2], 16) for i in (0, 2, 4))
            
            r = int(r1 * (1 - progress) + r2 * progress)
            g = int(g1 * (1 - progress) + g2 * progress)
            b = int(b1 * (1 - progress) + b2 * progress)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            setattr(target_obj, property_name, color)
        
        animation.on_update(blend_color)
        return animation
    
    else:
        # 不支持的类型，立即设置值
        setattr(target_obj, property_name, end_value)
        
        # 返回一个空动画
        config = AnimationConfig(
            type=AnimationType.FADE,
            duration=0.01
        )
        return Animation(config)


def create_transitions(transitions_config: Dict[str, Dict]) -> Dict[str, Animation]:
    """
    根据配置创建过渡动画字典
    
    参数:
        transitions_config: 过渡动画配置
        
    返回:
        Dict[str, Animation]: 过渡动画字典
    """
    transitions = {}
    
    for key, config in transitions_config.items():
        animation_type = config.get('type', 'fade')
        duration = config.get('duration', 0.3)
        easing_type = config.get('easing', 'ease_in_out')
        
        # 将字符串转换为枚举类型
        anim_type = AnimationType(animation_type)
        easing = EasingType(easing_type)
        
        # 创建动画配置
        anim_config = AnimationConfig(
            type=anim_type,
            duration=duration,
            easing=easing,
            delay=config.get('delay', 0.0),
            direction=AnimationDirection(config.get('direction', 'right')) if 'direction' in config else None,
            repeat=config.get('repeat', 0),
            auto_reverse=config.get('auto_reverse', False)
        )
        
        # 根据动画类型创建具体的动画实例
        if anim_type == AnimationType.FADE:
            transitions[key] = FadeAnimation(
                duration=duration,
                fade_in=config.get('fade_in', True),
                delay=config.get('delay', 0.0),
                easing=easing
            )
        
        elif anim_type == AnimationType.SLIDE:
            transitions[key] = SlideAnimation(
                duration=duration,
                direction=AnimationDirection(config.get('direction', 'right')),
                distance=config.get('distance', 100.0),
                delay=config.get('delay', 0.0),
                easing=easing
            )
        
        elif anim_type == AnimationType.SCALE:
            transitions[key] = ScaleAnimation(
                duration=duration,
                from_scale=config.get('from_scale', 0.0),
                to_scale=config.get('to_scale', 1.0),
                delay=config.get('delay', 0.0),
                easing=easing
            )
        
        elif anim_type == AnimationType.ROTATE:
            transitions[key] = RotateAnimation(
                duration=duration,
                from_angle=config.get('from_angle', 0.0),
                to_angle=config.get('to_angle', 360.0),
                delay=config.get('delay', 0.0),
                easing=easing
            )
        
        else:
            # 默认使用基础动画
            transitions[key] = Animation(anim_config)
    
    return transitions


# 示例用法（供参考）
def example_usage():
    """动画模块使用示例"""
    
    # 创建淡入动画
    fade_in = AnimationPresets.fade_in(duration=0.5)
    
    # 添加动画更新回调
    def on_fade_update(progress):
        # 在实际应用中，这里可能会更新UI元素的opacity属性
        print(f"淡入进度: {progress:.2f}")
    
    fade_in.on_update(on_fade_update)
    
    # 添加动画完成回调
    def on_fade_complete():
        print("淡入动画完成!")
    
    fade_in.on_complete(on_fade_complete)
    
    # 开始动画
    fade_in.start()
    
    # 在实际应用中，这里不需要使用sleep
    time.sleep(0.6)  # 等待动画完成
    
    # 创建动画组
    slide_in = AnimationPresets.slide_in_right()
    scale_in = AnimationPresets.scale_in()
    
    # 组合动画（同时播放）
    entrance_animation = AnimationGroup([slide_in, scale_in], sequence=False)
    
    def on_entrance_complete():
        print("入场动画完成!")
    
    entrance_animation.on_all_complete(on_entrance_complete)
    entrance_animation.start()
    
    # 在实际应用中，这里不需要使用sleep
    time.sleep(0.5)  # 等待动画完成
    
    # 使用加载动画
    loading = LoadingAnimation(LoadingAnimation.Type.SPINNER)
    
    def on_loading_update(progress):
        # 在实际应用中，这里可能会更新UI元素的rotation属性
        print(f"加载动画进度: {progress:.2f}")
    
    loading.on_update(on_loading_update)
    loading.start()
    
    # 在实际应用中，这里表示一个异步操作
    time.sleep(2.0)
    
    # 停止加载动画
    loading.stop()
    print("加载动画已停止")


if __name__ == "__main__":
    # 如果直接运行该模块，展示使用示例
    example_usage()