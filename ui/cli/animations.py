# ui/cli/animations.py
import sys
import time
import threading
import random
from contextlib import contextmanager
from .themes import get_current_theme, colorize

class Animation:
    """动画基类"""
    def __init__(self, fps=10):
        self.fps = fps
        self.running = False
        self._thread = None
        self._lock = threading.Lock()
    
    def start(self):
        """开始动画"""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run)
            self._thread.daemon = True
            self._thread.start()
    
    def stop(self):
        """停止动画"""
        if self.running:
            self.running = False
            if self._thread:
                self._thread.join(timeout=0.5)
            self._clear()
            sys.stdout.write("\n")
            sys.stdout.flush()
    
    def _run(self):
        """运行动画循环"""
        frame_time = 1.0 / self.fps
        while self.running:
            start_time = time.time()
            
            with self._lock:
                self._clear()
                self._draw_frame()
                sys.stdout.flush()
            
            # 计算下一帧需要等待的时间
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)
    
    def _clear(self):
        """清除当前行"""
        sys.stdout.write("\r")
        sys.stdout.write(" " * 80)  # 覆盖一整行
        sys.stdout.write("\r")
    
    def _draw_frame(self):
        """绘制一帧 (由子类实现)"""
        pass

class SpinnerAnimation(Animation):
    """旋转加载动画"""
    
    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "arrow": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "pulse": ["█", "▓", "▒", "░", "▒", "▓"],
        "bounce": ["⠁", "⠂", "⠄", "⠠", "⠐", "⠈"],
        "bars": ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"],
        "clock": ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
    }
    
    def __init__(self, text="加载中", style="dots", fps=10):
        super().__init__(fps)
        self.text = text
        self.frames = self.SPINNERS[style] if style in self.SPINNERS else self.SPINNERS["dots"]
        self.current_frame = 0
    
    def _draw_frame(self):
        """绘制一帧旋转动画"""
        theme = get_current_theme()
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        
        spinner = colorize(frame, theme["info"])
        text = colorize(self.text, theme["normal"])
        
        sys.stdout.write(f"{spinner} {text}")
    
    def update_text(self, text):
        """更新动画的文本"""
        with self._lock:
            self.text = text

class ProgressBarAnimation(Animation):
    """进度条动画"""
    
    def __init__(self, total, text="进度", width=40, fps=5):
        super().__init__(fps)
        self.total = total
        self.current = 0
        self.text = text
        self.width = width
        self.start_time = None
    
    def _draw_frame(self):
        """绘制一帧进度条动画"""
        theme = get_current_theme()
        
        if self.start_time is None:
            self.start_time = time.time()
        
        # 计算进度百分比
        percent = min(1.0, self.current / self.total if self.total else 1.0)
        filled_width = int(self.width * percent)
        
        # 计算已用时间
        elapsed = time.time() - self.start_time
        minutes, seconds = divmod(int(elapsed), 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # 构建进度条
        bar = "█" * filled_width + "░" * (self.width - filled_width)
        percent_str = f"{percent * 100:.1f}%"
        
        # 应用颜色
        text = colorize(self.text, theme["normal"])
        bar = colorize(bar, theme["progress_bar"])
        percent_text = colorize(percent_str, theme["value"])
        time_text = colorize(f"用时: {time_str}", theme["time"])
        
        # 输出
        sys.stdout.write(f"{text} |{bar}| {percent_text} {time_text}")
    
    def update(self, current, text=None):
        """更新进度条的当前值和文本"""
        with self._lock:
            self.current = current
            if text is not None:
                self.text = text

class TypewriterAnimation(Animation):
    """打字机效果动画"""
    
    def __init__(self, text, speed=0.05, end_pause=1.0):
        super().__init__(fps=30)
        self.text = text
        self.speed = speed
        self.end_pause = end_pause
        self.cursor_pos = 0
        self.finished = False
        self.finish_time = None
    
    def _draw_frame(self):
        """绘制一帧打字机动画"""
        theme = get_current_theme()
        
        if not self.finished:
            # 增加光标位置
            if self.cursor_pos < len(self.text):
                display_text = self.text[:self.cursor_pos] + colorize("▌", theme["prompt"])
                sys.stdout.write(display_text)
                time.sleep(self.speed)
                self.cursor_pos += 1
            else:
                self.finished = True
                self.finish_time = time.time()
                display_text = self.text + colorize("▌", theme["prompt"])
                sys.stdout.write(display_text)
        else:
            # 显示完成的文本和闪烁的光标
            if time.time() - self.finish_time > self.end_pause:
                self.running = False
                sys.stdout.write(self.text)
            else:
                if int(time.time() * 2) % 2:  # 闪烁效果
                    display_text = self.text + colorize("▌", theme["prompt"])
                else:
                    display_text = self.text + " "
                sys.stdout.write(display_text)

class RainAnimation(Animation):
    """数字雨动画 (Matrix风格)"""
    
    def __init__(self, width=80, height=5, density=0.2, speed=0.1, duration=5.0):
        super().__init__(fps=15)
        self.width = width
        self.height = height
        self.density = density  # 每一列出现字符的概率
        self.speed = speed      # 字符下落的速度
        self.duration = duration  # 动画持续时间
        self.start_time = None
        self.chars = "01"  # 可以使用更多字符: "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        self.columns = []
        self._init_columns()
    
    def _init_columns(self):
        """初始化雨滴列"""
        self.columns = []
        for x in range(self.width):
            if random.random() < self.density:
                # (x位置, y位置, 速度)
                self.columns.append([x, -random.randint(0, self.height), self.speed * random.uniform(0.5, 1.5)])
    
    def _draw_frame(self):
        """绘制一帧数字雨动画"""
        if self.start_time is None:
            self.start_time = time.time()
        
        # 检查动画是否结束
        if time.time() - self.start_time > self.duration:
            self.running = False
            return
        
        theme = get_current_theme()
        
        # 创建空屏幕
        screen = [[" " for _ in range(self.width)] for _ in range(self.height)]
        
        # 更新每一列的雨滴
        for i, (x, y, speed) in enumerate(self.columns):
            if 0 <= int(y) < self.height:
                # 为雨滴选择一个随机字符
                char = random.choice(self.chars)
                screen[int(y)][x] = colorize(char, theme["value"])
            
            # 更新雨滴位置
            self.columns[i][1] += speed
            
            # 如果雨滴离开屏幕，创建一个新的
            if y >= self.height:
                if random.random() < self.density:
                    self.columns[i] = [x, -random.randint(1, 3), speed]
                else:
                    self.columns[i] = [x, -999, speed]  # 暂时隐藏这一列
        
        # 绘制屏幕
        for row in screen:
            sys.stdout.write("\r" + "".join(row))
            sys.stdout.write("\n")
        
        # 将光标移回开始位置
        sys.stdout.write(f"\033[{self.height}A")

@contextmanager
def spinner(text="加载中", style="dots", fps=10):
    """显示加载动画的上下文管理器"""
    animation = SpinnerAnimation(text, style, fps)
    try:
        animation.start()
        yield animation
    finally:
        animation.stop()

@contextmanager
def progress_bar(total, text="进度", width=40, fps=5):
    """显示进度条的上下文管理器"""
    bar = ProgressBarAnimation(total, text, width, fps)
    try:
        bar.start()
        yield bar
    finally:
        bar.stop()

def typewriter(text, speed=0.05):
    """显示打字机效果"""
    animation = TypewriterAnimation(text, speed)
    animation.start()
    while animation.running:
        time.sleep(0.1)
    return text

def matrix_effect(width=80, height=5, duration=3.0):
    """显示Matrix风格的数字雨效果"""
    animation = RainAnimation(width, height, duration=duration)
    animation.start()
    while animation.running:
        time.sleep(0.1)