# ui/components/animation_system.py
"""
动画效果系统

这个组件负责管理应用程序中的动画效果，提供统一的接口和工具。
它实现了以下功能：
1. 提供常用动画效果（淡入淡出、缩放、移动等）
2. 支持自定义动画曲线（缓动函数）
3. 支持链式动画和并行动画
4. 集成主题系统的动画配置

设计理念:
- 所有交互应流畅自然，有轻柔的过渡和反馈
- 动画应当强化用户体验，而非干扰用户
- 统一的动画语言，使界面感觉连贯且有生命力
"""

import tkinter as tk
import time
import threading
import math

class Animation:
    """基础动画类，提供动画核心功能"""
    
    def __init__(self, duration=300, easing="ease_out", on_update=None, on_complete=None):
        """
        初始化动画
        
        Args:
            duration: 动画持续时间（毫秒）
            easing: 缓动函数名称
            on_update: 更新回调函数，接收参数 (progress, value)
            on_complete: 完成回调函数
        """
        self.duration = duration  # 毫秒
        self.easing = easing
        self.on_update = on_update
        self.on_complete = on_complete
        
        self.running = False
        self.start_time = 0
        self.start_value = 0
        self.end_value = 1
        self.current_value = 0
        
        # 缓动函数映射
        self.easing_functions = {
            "linear": self._linear,
            "ease_in": self._ease_in,
            "ease_out": self._ease_out,
            "ease_in_out": self._ease_in_out,
            "bounce": self._bounce,
            "elastic": self._elastic,
            "back": self._back
        }
    
    def start(self, start_value=0, end_value=1):
        """
        开始动画
        
        Args:
            start_value: 起始值
            end_value: 结束值
        """
        if self.running:
            return
        
        self.running = True
        self.start_time = time.time() * 1000  # 转换为毫秒
        self.start_value = start_value
        self.end_value = end_value
        self.current_value = start_value
        
        # 在新线程中运行动画循环
        threading.Thread(target=self._animation_loop, daemon=True).start()
    
    def stop(self):
        """停止动画"""
        self.running = False
    
    def _animation_loop(self):
        """动画主循环"""
        while self.running:
            # 计算经过的时间
            current_time = time.time() * 1000
            elapsed = current_time - self.start_time
            
            # 计算进度
            if elapsed >= self.duration:
                # 动画完成
                self.current_value = self.end_value
                progress = 1.0
                self.running = False
            else:
                # 动画进行中
                progress = elapsed / self.duration
                # 应用缓动函数
                eased_progress = self._apply_easing(progress)
                # 计算当前值
                self.current_value = self.start_value + (self.end_value - self.start_value) * eased_progress
            
            # 调用更新回调
            if self.on_update:
                try:
                    self.on_update(progress, self.current_value)
                except Exception as e:
                    print(f"动画更新回调出错: {e}")
            
            # 检查是否完成
            if not self.running:
                # 调用完成回调
                if self.on_complete:
                    try:
                        self.on_complete()
                    except Exception as e:
                        print(f"动画完成回调出错: {e}")
                break
            
            # 等待下一帧
            time.sleep(1/60)  # 约60fps
    
    def _apply_easing(self, progress):
        """
        应用缓动函数
        
        Args:
            progress: 线性进度 (0.0 到 1.0)
            
        Returns:
            float: 缓动后的进度值
        """
        easing_func = self.easing_functions.get(self.easing, self._ease_out)
        return easing_func(progress)
    
    # 缓动函数
    def _linear(self, t):
        """线性缓动"""
        return t
    
    def _ease_in(self, t):
        """缓入"""
        return t * t
    
    def _ease_out(self, t):
        """缓出"""
        return t * (2 - t)
    
    def _ease_in_out(self, t):
        """缓入缓出"""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    def _bounce(self, t):
        """弹跳"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    def _elastic(self, t):
        """弹性"""
        if t == 0 or t == 1:
            return t
        
        t = t - 1
        return -(pow(2, 10 * t) * math.sin((t - 0.1) * (2 * math.pi) / 0.4))
    
    def _back(self, t):
        """回弹"""
        s = 1.70158
        return t * t * ((s + 1) * t - s)


class SequentialAnimation:
    """顺序动画，按顺序执行多个动画"""
    
    def __init__(self, animations=None, on_complete=None):
        """
        初始化顺序动画
        
        Args:
            animations: 动画列表
            on_complete: 完成回调函数
        """
        self.animations = animations or []
        self.on_complete = on_complete
        self.current_index = 0
        self.running = False
    
    def add_animation(self, animation):
        """
        添加动画
        
        Args:
            animation: 要添加的动画对象
        """
        self.animations.append(animation)
    
    def start(self):
        """开始执行动画序列"""
        if self.running or not self.animations:
            return
        
        self.running = True
        self.current_index = 0
        self._start_current_animation()
    
    def stop(self):
        """停止动画序列"""
        if not self.running:
            return
        
        self.running = False
        if self.current_index < len(self.animations):
            self.animations[self.current_index].stop()
    
    def _start_current_animation(self):
        """开始当前动画"""
        if not self.running or self.current_index >= len(self.animations):
            # 所有动画完成
            self.running = False
            if self.on_complete:
                try:
                    self.on_complete()
                except Exception as e:
                    print(f"顺序动画完成回调出错: {e}")
            return
        
        # 获取当前动画
        current_animation = self.animations[self.current_index]
        
        # 设置完成回调
        original_on_complete = current_animation.on_complete
        
        def on_animation_complete():
            # 调用原始回调
            if original_on_complete:
                try:
                    original_on_complete()
                except Exception as e:
                    print(f"动画完成回调出错: {e}")
            
            # 移到下一个动画
            self.current_index += 1
            self._start_current_animation()
        
        # 设置新的完成回调
        current_animation.on_complete = on_animation_complete
        
        # 开始动画
        current_animation.start()


class ParallelAnimation:
    """并行动画，同时执行多个动画"""
    
    def __init__(self, animations=None, on_complete=None):
        """
        初始化并行动画
        
        Args:
            animations: 动画列表
            on_complete: 完成回调函数
        """
        self.animations = animations or []
        self.on_complete = on_complete
        self.running = False
        self.completed_count = 0
    
    def add_animation(self, animation):
        """
        添加动画
        
        Args:
            animation: 要添加的动画对象
        """
        self.animations.append(animation)
    
    def start(self):
        """同时开始所有动画"""
        if self.running or not self.animations:
            return
        
        self.running = True
        self.completed_count = 0
        
        # 为每个动画设置完成回调
        for animation in self.animations:
            original_on_complete = animation.on_complete
            
            def make_on_complete(orig_callback):
                def on_animation_complete():
                    # 调用原始回调
                    if orig_callback:
                        try:
                            orig_callback()
                        except Exception as e:
                            print(f"动画完成回调出错: {e}")
                    
                    # 增加完成计数
                    self.completed_count += 1
                    
                    # 检查是否所有动画都完成
                    if self.completed_count >= len(self.animations):
                        self.running = False
                        if self.on_complete:
                            try:
                                self.on_complete()
                            except Exception as e:
                                print(f"并行动画完成回调出错: {e}")
                
                return on_animation_complete
            
            animation.on_complete = make_on_complete(original_on_complete)
        
        # 启动所有动画
        for animation in self.animations:
            animation.start()
    
    def stop(self):
        """停止所有动画"""
        if not self.running:
            return
        
        self.running = False
        for animation in self.animations:
            animation.stop()


class AnimationManager:
    """动画管理器，提供高级动画和预设效果"""
    
    def __init__(self, theme_manager=None):
        """
        初始化动画管理器
        
        Args:
            theme_manager: 主题管理器实例
        """
        self.theme_manager = theme_manager
        
        # 设置默认配置
        self.default_config = {
            "duration": {
                "fast": 150,
                "normal": 300,
                "slow": 500
            },
            "easing": "ease_out"
        }
    
    def get_duration(self, speed="normal"):
        """
        获取动画持续时间
        
        Args:
            speed: 速度级别，'fast', 'normal' 或 'slow'
            
        Returns:
            int: 持续时间（毫秒）
        """
        if self.theme_manager:
            duration = self.theme_manager.get_animation_duration(speed)
            if duration:
                return duration
        
        return self.default_config["duration"].get(speed, 300)
    
    def get_easing(self, easing_type="ease_out"):
        """
        获取缓动类型
        
        Args:
            easing_type: 缓动类型名称
            
        Returns:
            str: 缓动函数名称
        """
        if self.theme_manager:
            easing = self.theme_manager.get_animation_easing(easing_type)
            if easing:
                return easing.replace("-", "_")
        
        return easing_type
    
    def fade_in(self, widget, duration=None, easing=None, on_complete=None):
        """
        淡入动画
        
        Args:
            widget: 要动画的窗口部件
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("ease_out")
        
        # 确保窗口部件支持alpha通道
        self._ensure_transparency(widget)
        
        # 设置初始透明度
        widget.attributes("-alpha", 0.0)
        widget.deiconify()  # 确保窗口可见
        
        def update_alpha(progress, value):
            widget.attributes("-alpha", value)
        
        # 创建动画
        animation = Animation(duration, easing, update_alpha, on_complete)
        animation.start(0.0, 1.0)
        
        return animation
    
    def fade_out(self, widget, duration=None, easing=None, on_complete=None):
        """
        淡出动画
        
        Args:
            widget: 要动画的窗口部件
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("ease_in")
        
        # 确保窗口部件支持alpha通道
        self._ensure_transparency(widget)
        
        # 获取当前透明度
        try:
            current_alpha = float(widget.attributes("-alpha"))
        except:
            current_alpha = 1.0
        
        def update_alpha(progress, value):
            widget.attributes("-alpha", value)
        
        def complete():
            if on_complete:
                on_complete()
            widget.withdraw()  # 隐藏窗口
        
        # 创建动画
        animation = Animation(duration, easing, update_alpha, complete)
        animation.start(current_alpha, 0.0)
        
        return animation
    
    def slide_in(self, widget, direction="right", distance=None, duration=None, easing=None, on_complete=None):
        """
        滑入动画
        
        Args:
            widget: 要动画的窗口部件
            direction: 方向 ('left', 'right', 'up', 'down')
            distance: 滑动距离（像素）
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("ease_out")
        
        # 获取窗口尺寸和位置
        width = widget.winfo_width()
        height = widget.winfo_height()
        x = widget.winfo_x()
        y = widget.winfo_y()
        
        # 如果尺寸为0，请求更新
        if width == 0 or height == 0:
            widget.update_idletasks()
            width = widget.winfo_width()
            height = widget.winfo_height()
            x = widget.winfo_x()
            y = widget.winfo_y()
        
        # 确定滑动距离
        if distance is None:
            if direction in ["left", "right"]:
                distance = width
            else:
                distance = height
        
        # 设置初始位置
        if direction == "left":
            start_x = x - distance
            start_y = y
            end_x = x
            end_y = y
        elif direction == "right":
            start_x = x + distance
            start_y = y
            end_x = x
            end_y = y
        elif direction == "up":
            start_x = x
            start_y = y - distance
            end_x = x
            end_y = y
        else:  # down
            start_x = x
            start_y = y + distance
            end_x = x
            end_y = y
        
        # 设置初始位置
        widget.place(x=start_x, y=start_y)
        widget.update_idletasks()
        
        def update_position(progress, value):
            current_x = start_x + (end_x - start_x) * value
            current_y = start_y + (end_y - start_y) * value
            widget.place(x=current_x, y=current_y)
        
        # 创建动画
        animation = Animation(duration, easing, update_position, on_complete)
        animation.start(0.0, 1.0)
        
        return animation
    
    def slide_out(self, widget, direction="right", distance=None, duration=None, easing=None, on_complete=None):
        """
        滑出动画
        
        Args:
            widget: 要动画的窗口部件
            direction: 方向 ('left', 'right', 'up', 'down')
            distance: 滑动距离（像素）
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("ease_in")
        
        # 获取窗口尺寸和位置
        width = widget.winfo_width()
        height = widget.winfo_height()
        x = widget.winfo_x()
        y = widget.winfo_y()
        
        # 如果尺寸为0，请求更新
        if width == 0 or height == 0:
            widget.update_idletasks()
            width = widget.winfo_width()
            height = widget.winfo_height()
            x = widget.winfo_x()
            y = widget.winfo_y()
        
        # 确定滑动距离
        if distance is None:
            if direction in ["left", "right"]:
                distance = width
            else:
                distance = height
        
        # 设置结束位置
        if direction == "left":
            end_x = x - distance
            end_y = y
        elif direction == "right":
            end_x = x + distance
            end_y = y
        elif direction == "up":
            end_x = x
            end_y = y - distance
        else:  # down
            end_x = x
            end_y = y + distance
        
        def update_position(progress, value):
            current_x = x + (end_x - x) * value
            current_y = y + (end_y - y) * value
            widget.place(x=current_x, y=current_y)
        
        def complete():
            if on_complete:
                on_complete()
            widget.place_forget()  # 移除布局
        
        # 创建动画
        animation = Animation(duration, easing, update_position, complete)
        animation.start(0.0, 1.0)
        
        return animation
    
    def scale(self, widget, start_scale=0.5, end_scale=1.0, origin="center", duration=None, easing=None, on_complete=None):
        """
        缩放动画
        
        Args:
            widget: 要动画的窗口部件
            start_scale: 起始缩放比例
            end_scale: 结束缩放比例
            origin: 缩放原点 ('center', 'top', 'bottom', 'left', 'right', 'top_left', 'top_right', 'bottom_left', 'bottom_right')
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("ease_out")
        
        # 获取窗口尺寸和位置
        width = widget.winfo_width()
        height = widget.winfo_height()
        x = widget.winfo_x()
        y = widget.winfo_y()
        
        # 如果尺寸为0，请求更新
        if width == 0 or height == 0:
            widget.update_idletasks()
            width = widget.winfo_width()
            height = widget.winfo_height()
            x = widget.winfo_x()
            y = widget.winfo_y()
        
        # 确定缩放原点
        if origin == "center":
            origin_x = x + width / 2
            origin_y = y + height / 2
        elif origin == "top":
            origin_x = x + width / 2
            origin_y = y
        elif origin == "bottom":
            origin_x = x + width / 2
            origin_y = y + height
        elif origin == "left":
            origin_x = x
            origin_y = y + height / 2
        elif origin == "right":
            origin_x = x + width
            origin_y = y + height / 2
        elif origin == "top_left":
            origin_x = x
            origin_y = y
        elif origin == "top_right":
            origin_x = x + width
            origin_y = y
        elif origin == "bottom_left":
            origin_x = x
            origin_y = y + height
        else:  # bottom_right
            origin_x = x + width
            origin_y = y + height
        
        # 计算起始位置
        start_width = width * start_scale
        start_height = height * start_scale
        
        # 根据原点计算起始左上角位置
        if origin == "center":
            start_x = origin_x - start_width / 2
            start_y = origin_y - start_height / 2
        elif origin == "top":
            start_x = origin_x - start_width / 2
            start_y = origin_y
        elif origin == "bottom":
            start_x = origin_x - start_width / 2
            start_y = origin_y - start_height
        elif origin == "left":
            start_x = origin_x
            start_y = origin_y - start_height / 2
        elif origin == "right":
            start_x = origin_x - start_width
            start_y = origin_y - start_height / 2
        elif origin == "top_left":
            start_x = origin_x
            start_y = origin_y
        elif origin == "top_right":
            start_x = origin_x - start_width
            start_y = origin_y
        elif origin == "bottom_left":
            start_x = origin_x
            start_y = origin_y - start_height
        else:  # bottom_right
            start_x = origin_x - start_width
            start_y = origin_y - start_height
        
        def update_scale(progress, value):
            # 计算当前缩放比例
            current_scale = start_scale + (end_scale - start_scale) * value
            
            # 计算当前尺寸
            current_width = width * current_scale
            current_height = height * current_scale
            
            # 计算当前位置
            if origin == "center":
                current_x = origin_x - current_width / 2
                current_y = origin_y - current_height / 2
            elif origin == "top":
                current_x = origin_x - current_width / 2
                current_y = origin_y
            elif origin == "bottom":
                current_x = origin_x - current_width / 2
                current_y = origin_y - current_height
            elif origin == "left":
                current_x = origin_x
                current_y = origin_y - current_height / 2
            elif origin == "right":
                current_x = origin_x - current_width
                current_y = origin_y - current_height / 2
            elif origin == "top_left":
                current_x = origin_x
                current_y = origin_y
            elif origin == "top_right":
                current_x = origin_x - current_width
                current_y = origin_y
            elif origin == "bottom_left":
                current_x = origin_x
                current_y = origin_y - current_height
            else:  # bottom_right
                current_x = origin_x - current_width
                current_y = origin_y - current_height
            
            # 更新位置和尺寸
            widget.place(x=current_x, y=current_y, width=current_width, height=current_height)
        
        # 创建动画
        animation = Animation(duration, easing, update_scale, on_complete)
        animation.start(0.0, 1.0)
        
        return animation
    
    def rotate(self, canvas_widget, start_angle=0, end_angle=360, duration=None, easing=None, on_complete=None):
        """
        旋转动画（只适用于Canvas上的项目）
        
        Args:
            canvas_widget: 包含对象ID的Canvas元组 (canvas, object_id)
            start_angle: 起始角度（度）
            end_angle: 结束角度（度）
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("ease_in_out")
        
        # 解包Canvas和对象ID
        canvas, object_id = canvas_widget
        
        # 获取对象的边界框
        bbox = canvas.bbox(object_id)
        if not bbox:
            print("无法获取对象边界框")
            return None
        
        # 计算旋转中心
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        def update_rotation(progress, value):
            # 计算当前角度
            current_angle = start_angle + (end_angle - start_angle) * value
            
            # 重置变换
            canvas.coords(object_id, *canvas.coords(object_id))
            
            # 应用旋转变换
            canvas.rotate(object_id, center_x, center_y, current_angle)
        
        # 创建动画
        animation = Animation(duration, easing, update_rotation, on_complete)
        animation.start(0.0, 1.0)
        
        return animation
    
    def color_transition(self, widget, start_color, end_color, property_name="background", duration=None, easing=None, on_complete=None):
        """
        颜色过渡动画
        
        Args:
            widget: 要动画的窗口部件
            start_color: 起始颜色（十六进制）
            end_color: 结束颜色（十六进制）
            property_name: 要动画的属性名称
            duration: 持续时间（毫秒）
            easing: 缓动类型
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or self.get_duration("normal")
        easing = easing or self.get_easing("linear")
        
        # 解析颜色
        start_color = start_color.lstrip('#')
        end_color = end_color.lstrip('#')
        
        # 如果提供的不是十六进制颜色，使用默认颜色
        if not all(c in "0123456789ABCDEFabcdef" for c in start_color) or len(start_color) != 6:
            start_color = "000000"
        if not all(c in "0123456789ABCDEFabcdef" for c in end_color) or len(end_color) != 6:
            end_color = "FFFFFF"
        
        # 转换为RGB
        start_rgb = tuple(int(start_color[i:i+2], 16) for i in (0, 2, 4))
        end_rgb = tuple(int(end_color[i:i+2], 16) for i in (0, 2, 4))
        
        def update_color(progress, value):
            # 计算当前颜色
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * value)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * value)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * value)
            
            # 转换为十六进制
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # 更新属性
            if property_name == "background":
                widget.config(bg=color)
            elif property_name == "foreground":
                widget.config(fg=color)
            elif property_name == "activebackground":
                widget.config(activebackground=color)
            elif property_name == "activeforeground":
                widget.config(activeforeground=color)
            elif hasattr(widget, "itemconfig") and isinstance(property_name, int):
                # 如果是Canvas项目
                widget.itemconfig(property_name, fill=color)
        
        # 创建动画
        animation = Animation(duration, easing, update_color, on_complete)
        animation.start(0.0, 1.0)
        
        return animation
    
    def shake(self, widget, intensity=5, count=5, duration=None, on_complete=None):
        """
        抖动动画
        
        Args:
            widget: 要动画的窗口部件
            intensity: 抖动强度（像素）
            count: 抖动次数
            duration: 持续时间（毫秒）
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or min(count * 100, self.get_duration("normal"))
        
        # 获取原始位置
        original_x = widget.winfo_x()
        original_y = widget.winfo_y()
        
        # 创建抖动坐标序列
        shake_points = []
        for i in range(count):
            if i % 2 == 0:
                shake_points.append((original_x + intensity, original_y))
                shake_points.append((original_x, original_y + intensity))
            else:
                shake_points.append((original_x - intensity, original_y))
                shake_points.append((original_x, original_y - intensity))
        
        # 最后回到原始位置
        shake_points.append((original_x, original_y))
        
        # 创建序列动画
        animations = []
        point_duration = duration / (len(shake_points) * 2)
        
        for i, point in enumerate(shake_points):
            # 创建移动动画
            def create_update_func(target_x, target_y):
                def update_position(progress, value):
                    current_x = original_x + (target_x - original_x) * value
                    current_y = original_y + (target_y - original_y) * value
                    widget.place(x=current_x, y=current_y)
                return update_position
            
            animation = Animation(
                point_duration, 
                "linear", 
                create_update_func(point[0], point[1])
            )
            animations.append(animation)
            
            # 如果不是最后一个点，添加返回原点的动画
            if i < len(shake_points) - 1:
                animation = Animation(
                    point_duration, 
                    "linear", 
                    create_update_func(original_x, original_y)
                )
                animations.append(animation)
        
        # 创建顺序动画
        seq_animation = SequentialAnimation(animations, on_complete)
        seq_animation.start()
        
        return seq_animation
    
    def pulse(self, widget, scale_factor=1.2, count=3, duration=None, on_complete=None):
        """
        脉冲动画
        
        Args:
            widget: 要动画的窗口部件
            scale_factor: 最大缩放比例
            count: 脉冲次数
            duration: 持续时间（毫秒）
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or min(count * 300, self.get_duration("slow"))
        
        # 创建脉冲动画序列
        animations = []
        pulse_duration = duration / (count * 2)
        
        for i in range(count):
            # 放大动画
            scale_up = Animation(
                pulse_duration,
                "ease_out",
                lambda p, v, w=widget, sf=scale_factor: self._update_pulse(w, 1.0, sf, v)
            )
            animations.append(scale_up)
            
            # 缩小动画
            scale_down = Animation(
                pulse_duration,
                "ease_in",
                lambda p, v, w=widget, sf=scale_factor: self._update_pulse(w, sf, 1.0, v)
            )
            animations.append(scale_down)
        
        # 创建顺序动画
        seq_animation = SequentialAnimation(animations, on_complete)
        seq_animation.start()
        
        return seq_animation
    
    def _update_pulse(self, widget, start_scale, end_scale, progress):
        """脉冲动画的更新函数"""
        # 计算当前缩放
        current_scale = start_scale + (end_scale - start_scale) * progress
        
        # 获取窗口尺寸和位置
        width = widget.winfo_reqwidth()
        height = widget.winfo_reqheight()
        x = widget.winfo_x()
        y = widget.winfo_y()
        
        # 计算中心点
        center_x = x + width / 2
        center_y = y + height / 2
        
        # 计算新尺寸
        new_width = width * current_scale
        new_height = height * current_scale
        
        # 计算新位置（保持中心不变）
        new_x = center_x - new_width / 2
        new_y = center_y - new_height / 2
        
        # 应用变换
        widget.place(x=new_x, y=new_y, width=new_width, height=new_height)
    
    def highlight_attention(self, widget, highlight_color=None, flash_count=3, duration=None, on_complete=None):
        """
        高亮注意动画
        
        Args:
            widget: 要动画的窗口部件
            highlight_color: 高亮颜色
            flash_count: 闪烁次数
            duration: 持续时间（毫秒）
            on_complete: 完成回调函数
            
        Returns:
            Animation: 动画对象
        """
        duration = duration or min(flash_count * 200, self.get_duration("normal"))
        
        # 获取当前背景色
        try:
            current_bg = widget.cget("background")
        except:
            current_bg = "#ffffff"
        
        # 确定高亮颜色
        if highlight_color is None:
            if self.theme_manager:
                highlight_color = self.theme_manager.get_color("primary")
            else:
                highlight_color = "#3355ff"
        
        # 创建闪烁动画序列
        animations = []
        flash_duration = duration / (flash_count * 2)
        
        for i in range(flash_count):
            # 切换到高亮色
            to_highlight = Animation(
                flash_duration,
                "ease_out",
                lambda p, v, w=widget, c1=current_bg, c2=highlight_color: self._update_color(w, c1, c2, v)
            )
            animations.append(to_highlight)
            
            # 切换回正常色
            to_normal = Animation(
                flash_duration,
                "ease_in",
                lambda p, v, w=widget, c1=highlight_color, c2=current_bg: self._update_color(w, c1, c2, v)
            )
            animations.append(to_normal)
        
        # 创建顺序动画
        seq_animation = SequentialAnimation(animations, on_complete)
        seq_animation.start()
        
        return seq_animation
    
    def _update_color(self, widget, start_color, end_color, progress):
        """颜色更新函数"""
        # 解析颜色
        try:
            start_color = start_color.lstrip('#')
            end_color = end_color.lstrip('#')
            
            # 转换为RGB
            start_rgb = tuple(int(start_color[i:i+2], 16) for i in (0, 2, 4))
            end_rgb = tuple(int(end_color[i:i+2], 16) for i in (0, 2, 4))
            
            # 计算当前颜色
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
            
            # 转换为十六进制
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # 应用颜色
            widget.config(bg=color)
        except Exception as e:
            print(f"更新颜色时出错: {e}")
    
    def _ensure_transparency(self, widget):
        """确保窗口支持透明度"""
        try:
            # 检查是否为顶层窗口
            if isinstance(widget, (tk.Toplevel, tk.Tk)):
                # 确保窗口支持alpha通道
                widget.attributes("-alpha", 1.0)
        except Exception as e:
            print(f"设置透明度时出错: {e}")


# 示例用法
if __name__ == "__main__":
    root = tk.Tk()
    root.title("动画系统演示")
    root.geometry("800x600")
    
    # 创建动画管理器
    animation_manager = AnimationManager()
    
    # 示例容器
    main_frame = tk.Frame(root, bg="#f5f5f7")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 标题
    title = tk.Label(main_frame, text="动画效果演示", font=("Helvetica", 18, "bold"), bg="#f5f5f7")
    title.pack(pady=(0, 20))
    
    # 创建演示区域
    demo_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief=tk.SOLID)
    demo_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 创建演示对象
    demo_widget = tk.Label(
        demo_frame, 
        text="动画测试对象",
        font=("Helvetica", 14),
        bg="#3355ff",
        fg="#ffffff",
        width=15,
        height=5
    )
    demo_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    # 创建按钮框架
    buttons_frame = tk.Frame(main_frame, bg="#f5f5f7")
    buttons_frame.pack(fill=tk.X, pady=20)
    
    # 创建按钮
    def create_animation_button(frame, text, command):
        return tk.Button(frame, text=text, command=command, width=12)
    
    # 动画函数
    def fade_in_demo():
        demo_widget.place_forget()
        animation_manager.fade_in(demo_widget)
        demo_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    def fade_out_demo():
        animation_manager.fade_out(demo_widget)
    
    def slide_in_demo():
        demo_widget.place_forget()
        animation_manager.slide_in(demo_widget, "right")
        demo_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    def slide_out_demo():
        animation_manager.slide_out(demo_widget, "right")
    
    def scale_demo():
        animation_manager.scale(demo_widget, 0.5, 1.5, "center", duration=1000)
    
    def color_demo():
        animation_manager.color_transition(
            demo_widget, 
            "#3355ff", 
            "#ff3355", 
            "background", 
            duration=1000
        )
    
    def shake_demo():
        animation_manager.shake(demo_widget, intensity=10, count=5)
    
    def pulse_demo():
        animation_manager.pulse(demo_widget, scale_factor=1.2, count=3)
    
    def highlight_demo():
        animation_manager.highlight_attention(demo_widget, "#ffcc00", flash_count=3)
    
    def reset_demo():
        demo_widget.place_forget()
        demo_widget.config(bg="#3355ff")
        demo_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    # 添加按钮
    fade_in_btn = create_animation_button(buttons_frame, "淡入", fade_in_demo)
    fade_in_btn.pack(side=tk.LEFT, padx=5)
    
    fade_out_btn = create_animation_button(buttons_frame, "淡出", fade_out_demo)
    fade_out_btn.pack(side=tk.LEFT, padx=5)
    
    slide_in_btn = create_animation_button(buttons_frame, "滑入", slide_in_demo)
    slide_in_btn.pack(side=tk.LEFT, padx=5)
    
    slide_out_btn = create_animation_button(buttons_frame, "滑出", slide_out_demo)
    slide_out_btn.pack(side=tk.LEFT, padx=5)
    
    scale_btn = create_animation_button(buttons_frame, "缩放", scale_demo)
    scale_btn.pack(side=tk.LEFT, padx=5)
    
    color_btn = create_animation_button(buttons_frame, "颜色变换", color_demo)
    color_btn.pack(side=tk.LEFT, padx=5)
    
    shake_btn = create_animation_button(buttons_frame, "抖动", shake_demo)
    shake_btn.pack(side=tk.LEFT, padx=5)
    
    pulse_btn = create_animation_button(buttons_frame, "脉冲", pulse_demo)
    pulse_btn.pack(side=tk.LEFT, padx=5)
    
    highlight_btn = create_animation_button(buttons_frame, "高亮", highlight_demo)
    highlight_btn.pack(side=tk.LEFT, padx=5)
    
    reset_btn = create_animation_button(buttons_frame, "重置", reset_demo)
    reset_btn.pack(side=tk.LEFT, padx=5)
    
    root.mainloop()