"""
音效处理工具模块 - Audio Utilities

这个模块提供了应用程序的音频处理和管理功能，负责界面音效、通知声音和背景音乐。
设计理念是通过精心设计的声音反馈增强用户体验，使界面交互更加立体和人性化。
声音反馈应当是贴心且恰到好处的，既能提供必要信息，又不会造成干扰。

主要功能:
    - 界面音效播放（点击、滑动、提示等）
    - 通知声音管理
    - 背景音乐控制
    - 音频预加载和缓存
    - 音量控制和静音设置
    - 无障碍声音支持

作者: AI助手
日期: 2025-04-19
"""

import os
import time
import threading
import logging
from enum import Enum
from typing import Dict, List, Optional, Callable, Union, Tuple
import json
from dataclasses import dataclass
import tempfile
import wave
import array
import math
import random
import threading


# 尝试导入不同平台的音频库
try:
    import pygame
    AUDIO_BACKEND = "pygame"
except ImportError:
    try:
        import simpleaudio as sa
        AUDIO_BACKEND = "simpleaudio"
    except ImportError:
        try:
            import winsound
            AUDIO_BACKEND = "winsound"
        except ImportError:
            try:
                from Foundation import NSSound
                from AppKit import NSSound
                AUDIO_BACKEND = "nssound"
            except ImportError:
                import subprocess
                AUDIO_BACKEND = "command_line"


# 配置日志
logger = logging.getLogger(__name__)


class AudioCategory(Enum):
    """音频类别枚举"""
    UI_FEEDBACK = "ui_feedback"     # 界面反馈音效
    NOTIFICATION = "notification"   # 通知声音
    BACKGROUND = "background"       # 背景音乐
    ALERT = "alert"                 # 警告音效
    SUCCESS = "success"             # 成功提示音
    ERROR = "error"                 # 错误提示音
    AMBIENT = "ambient"             # 环境声音


class SoundType(Enum):
    """界面交互声音类型枚举"""
    CLICK = "click"                 # 点击音效
    HOVER = "hover"                 # 悬停音效
    TOGGLE = "toggle"               # 开关切换音效
    SCROLL = "scroll"               # 滚动音效
    SWIPE = "swipe"                 # 滑动音效
    TYPING = "typing"               # 打字音效
    POPUP_OPEN = "popup_open"       # 弹窗打开音效
    POPUP_CLOSE = "popup_close"     # 弹窗关闭音效
    SUCCESS = "success"             # 成功音效
    ERROR = "error"                 # 错误音效
    WARNING = "warning"             # 警告音效
    INFO = "info"                   # 信息提示音效
    COMPLETE = "complete"           # 完成音效
    LOADING = "loading"             # 加载音效
    NOTIFICATION = "notification"   # 通知音效
    MESSAGE = "message"             # 消息通知音效
    CUSTOM = "custom"               # 自定义音效


@dataclass
class AudioProperties:
    """音频属性数据类"""
    volume: float = 1.0             # 音量 (0.0-1.0)
    pitch: float = 1.0              # 音高 (0.5-2.0)
    stereo_pan: float = 0.0         # 立体声平衡 (-1.0 左声道到 1.0 右声道)
    loop: bool = False              # 是否循环播放
    loop_count: int = 0             # 循环次数 (0表示无限循环)
    loop_delay: float = 0.0         # 循环间隔时间
    fade_in: float = 0.0            # 淡入时间 (秒)
    fade_out: float = 0.0           # 淡出时间 (秒)
    start_position: float = 0.0     # 开始位置 (秒)
    tempo: float = 1.0              # 速度 (0.5-2.0)


class AudioState(Enum):
    """音频状态枚举"""
    IDLE = "idle"               # 空闲
    LOADING = "loading"         # 加载中
    PLAYING = "playing"         # 播放中
    PAUSED = "paused"           # 暂停
    STOPPED = "stopped"         # 停止
    ERROR = "error"             # 错误


@dataclass
class AudioMetadata:
    """音频元数据"""
    title: str = ""                 # 标题
    artist: str = ""                # 艺术家
    album: str = ""                 # 专辑
    year: str = ""                  # 年份
    duration: float = 0.0           # 时长(秒)
    sample_rate: int = 44100        # 采样率
    channels: int = 2               # 声道数
    bit_depth: int = 16             # 位深度
    file_size: int = 0              # 文件大小(字节)
    file_format: str = ""           # 文件格式


class AudioFile:
    """
    音频文件类
    
    表示一个音频文件及其属性和状态
    """
    
    def __init__(self, 
                 file_path: str,
                 properties: Optional[AudioProperties] = None,
                 category: AudioCategory = AudioCategory.UI_FEEDBACK,
                 metadata: Optional[AudioMetadata] = None):
        """
        初始化音频文件
        
        参数:
            file_path: 音频文件路径
            properties: 音频属性
            category: 音频类别
            metadata: 音频元数据
        """
        self.file_path = file_path
        self.properties = properties or AudioProperties()
        self.category = category
        self.metadata = metadata or AudioMetadata()
        self.state = AudioState.IDLE
        self.loaded_data = None  # 用于存储预加载的音频数据
        self.play_instance = None  # 用于存储当前播放实例
        self.play_thread = None  # 用于存储播放线程
        self.stop_flag = False  # 用于标记是否停止播放
        
        # 回调函数
        self.on_play_callbacks = []
        self.on_pause_callbacks = []
        self.on_stop_callbacks = []
        self.on_complete_callbacks = []
        self.on_loop_callbacks = []
        self.on_error_callbacks = []
    
    def load(self) -> bool:
        """
        加载音频文件
        
        返回:
            bool: 是否加载成功
        """
        try:
            self.state = AudioState.LOADING
            
            if not os.path.exists(self.file_path):
                logger.error(f"音频文件不存在: {self.file_path}")
                self.state = AudioState.ERROR
                self._trigger_error("文件不存在")
                return False
            
            # 根据不同后端进行加载
            if AUDIO_BACKEND == "pygame":
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2)
                try:
                    self.loaded_data = pygame.mixer.Sound(self.file_path)
                    # 设置音量
                    self.loaded_data.set_volume(self.properties.volume)
                    # 尝试加载元数据
                    self._load_metadata_pygame()
                except Exception as e:
                    logger.error(f"无法加载音频文件: {self.file_path}, 错误: {e}")
                    self.state = AudioState.ERROR
                    self._trigger_error(str(e))
                    return False
            
            elif AUDIO_BACKEND == "simpleaudio":
                try:
                    wave_obj = sa.WaveObject.from_wave_file(self.file_path)
                    self.loaded_data = wave_obj
                    # 尝试加载元数据
                    self._load_metadata_wave()
                except Exception as e:
                    logger.error(f"无法加载音频文件: {self.file_path}, 错误: {e}")
                    self.state = AudioState.ERROR
                    self._trigger_error(str(e))
                    return False
            
            elif AUDIO_BACKEND == "winsound":
                # winsound不需要预加载，只需要检查文件是否存在和可读
                try:
                    with open(self.file_path, 'rb') as f:
                        # 只读取一小部分检查文件有效性
                        f.read(1024)
                    # 标记为已加载
                    self.loaded_data = True
                except Exception as e:
                    logger.error(f"无法加载音频文件: {self.file_path}, 错误: {e}")
                    self.state = AudioState.ERROR
                    self._trigger_error(str(e))
                    return False
            
            elif AUDIO_BACKEND == "nssound":
                try:
                    # 在macOS上使用NSSound
                    sound = NSSound.alloc().initWithContentsOfFile_byReference_(
                        self.file_path, True)
                    if sound:
                        self.loaded_data = sound
                    else:
                        raise Exception("无法初始化NSSound对象")
                except Exception as e:
                    logger.error(f"无法加载音频文件: {self.file_path}, 错误: {e}")
                    self.state = AudioState.ERROR
                    self._trigger_error(str(e))
                    return False
            
            else:  # command_line
                # 对于命令行后端，只需检查文件是否存在和可读
                try:
                    with open(self.file_path, 'rb') as f:
                        # 只读取一小部分检查文件有效性
                        f.read(1024)
                    # 标记为已加载
                    self.loaded_data = True
                except Exception as e:
                    logger.error(f"无法加载音频文件: {self.file_path}, 错误: {e}")
                    self.state = AudioState.ERROR
                    self._trigger_error(str(e))
                    return False
            
            self.state = AudioState.IDLE
            return True
        
        except Exception as e:
            logger.error(f"加载音频文件时出错: {self.file_path}, 错误: {e}")
            self.state = AudioState.ERROR
            self._trigger_error(str(e))
            return False
    
    def _load_metadata_pygame(self) -> None:
        """使用pygame加载音频元数据"""
        try:
            # pygame不提供直接访问元数据的方法，但我们可以获取一些基本信息
            if hasattr(self.loaded_data, 'get_length'):
                self.metadata.duration = self.loaded_data.get_length()
            
            if pygame.mixer.get_init():
                freq, size, channels = pygame.mixer.get_init()
                self.metadata.sample_rate = freq
                self.metadata.channels = channels
                self.metadata.bit_depth = abs(size)
            
            # 尝试从文件名提取一些信息
            filename = os.path.basename(self.file_path)
            self.metadata.file_format = os.path.splitext(filename)[1][1:]
            self.metadata.file_size = os.path.getsize(self.file_path)
            
        except Exception as e:
            logger.warning(f"加载音频元数据时出错: {e}")
    
    def _load_metadata_wave(self) -> None:
        """从WAV文件加载元数据"""
        try:
            with wave.open(self.file_path, 'rb') as wav:
                self.metadata.channels = wav.getnchannels()
                self.metadata.sample_rate = wav.getframerate()
                self.metadata.bit_depth = wav.getsampwidth() * 8
                frames = wav.getnframes()
                self.metadata.duration = frames / self.metadata.sample_rate
            
            # 获取文件大小
            self.metadata.file_size = os.path.getsize(self.file_path)
            self.metadata.file_format = 'wav'
            
        except Exception as e:
            logger.warning(f"加载WAV元数据时出错: {e}")
    
    def play(self) -> bool:
        """
        播放音频文件
        
        返回:
            bool: 是否成功开始播放
        """
        if self.state == AudioState.ERROR:
            logger.error(f"无法播放，音频处于错误状态: {self.file_path}")
            return False
        
        if self.state == AudioState.PLAYING:
            logger.debug(f"音频已经在播放中: {self.file_path}")
            return True
        
        # 如果没有预加载，先加载
        if self.loaded_data is None:
            if not self.load():
                return False
        
        self.stop_flag = False
        
        # 创建播放线程
        self.play_thread = threading.Thread(target=self._play_thread_func)
        self.play_thread.daemon = True
        self.play_thread.start()
        
        return True
    
    def _play_thread_func(self) -> None:
        """播放线程函数"""
        try:
            # 设置状态为播放中
            self.state = AudioState.PLAYING
            self._trigger_play()
            
            loop_count = 0
            
            while not self.stop_flag:
                if AUDIO_BACKEND == "pygame":
                    # 设置音量
                    self.loaded_data.set_volume(self.properties.volume)
                    
                    # 播放声音
                    channel = self.loaded_data.play()
                    
                    # 等待播放完成
                    while channel.get_busy() and not self.stop_flag:
                        time.sleep(0.1)
                    
                elif AUDIO_BACKEND == "simpleaudio":
                    # 播放声音
                    self.play_instance = self.loaded_data.play()
                    
                    # 等待播放完成
                    if not self.stop_flag:
                        self.play_instance.wait_done()
                    
                elif AUDIO_BACKEND == "winsound":
                    # 使用winsound播放
                    winsound.PlaySound(self.file_path, winsound.SND_FILENAME)
                    
                elif AUDIO_BACKEND == "nssound":
                    # 使用NSSound播放
                    sound = self.loaded_data
                    sound.setVolume_(self.properties.volume)
                    sound.play()
                    
                    # 等待播放完成
                    while sound.isPlaying() and not self.stop_flag:
                        time.sleep(0.1)
                    
                else:  # command_line
                    # 根据平台选择命令行播放工具
                    if os.name == 'posix':  # macOS或Linux
                        subprocess.run(['afplay', self.file_path], 
                                      check=False, stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL)
                    else:  # 可能是Windows
                        subprocess.run(['powershell', '-c', 
                                      f'(New-Object Media.SoundPlayer "{self.file_path}").PlaySync();'],
                                      check=False, stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL)
                
                # 触发循环回调
                if not self.stop_flag:
                    self._trigger_loop(loop_count)
                
                # 处理循环逻辑
                if self.properties.loop:
                    loop_count += 1
                    
                    # 检查循环次数
                    if self.properties.loop_count > 0 and loop_count >= self.properties.loop_count:
                        break
                    
                    # 循环延迟
                    if self.properties.loop_delay > 0 and not self.stop_flag:
                        time.sleep(self.properties.loop_delay)
                    
                    # 如果被停止则退出循环
                    if self.stop_flag:
                        break
                else:
                    # 不循环则退出循环
                    break
            
            # 如果不是被停止的，则触发完成回调
            if not self.stop_flag:
                self.state = AudioState.STOPPED
                self._trigger_complete()
            
        except Exception as e:
            logger.error(f"播放音频时出错: {e}")
            self.state = AudioState.ERROR
            self._trigger_error(str(e))
    
    def pause(self) -> bool:
        """
        暂停播放
        
        返回:
            bool: 是否成功暂停
        """
        if self.state != AudioState.PLAYING:
            return False
        
        try:
            if AUDIO_BACKEND == "pygame":
                # pygame中没有直接暂停单个声音的方法，这里简化处理
                pygame.mixer.pause()
            
            elif AUDIO_BACKEND == "simpleaudio" and self.play_instance:
                # simpleaudio没有暂停方法，只能停止
                self.play_instance.stop()
            
            # 其他后端不支持暂停
            
            self.state = AudioState.PAUSED
            self._trigger_pause()
            return True
            
        except Exception as e:
            logger.error(f"暂停音频时出错: {e}")
            return False
    
    def resume(self) -> bool:
        """
        恢复播放
        
        返回:
            bool: 是否成功恢复
        """
        if self.state != AudioState.PAUSED:
            return False
        
        try:
            if AUDIO_BACKEND == "pygame":
                pygame.mixer.unpause()
            
            elif AUDIO_BACKEND == "simpleaudio":
                # simpleaudio不支持恢复，需要重新播放
                return self.play()
            
            # 其他后端不支持恢复
            
            self.state = AudioState.PLAYING
            self._trigger_play()
            return True
            
        except Exception as e:
            logger.error(f"恢复音频时出错: {e}")
            return False
    
    def stop(self) -> bool:
        """
        停止播放
        
        返回:
            bool: 是否成功停止
        """
        if self.state not in [AudioState.PLAYING, AudioState.PAUSED]:
            return False
        
        try:
            # 设置停止标志
            self.stop_flag = True
            
            if AUDIO_BACKEND == "pygame":
                # 停止所有声道，这可能会影响其他声音
                pygame.mixer.stop()
            
            elif AUDIO_BACKEND == "simpleaudio" and self.play_instance:
                self.play_instance.stop()
            
            elif AUDIO_BACKEND == "nssound" and self.loaded_data:
                self.loaded_data.stop()
            
            # 其他后端不需要特殊处理，线程会自行结束
            
            self.state = AudioState.STOPPED
            self._trigger_stop()
            return True
            
        except Exception as e:
            logger.error(f"停止音频时出错: {e}")
            return False
    
    def set_volume(self, volume: float) -> None:
        """
        设置音量
        
        参数:
            volume: 音量值 (0.0-1.0)
        """
        # 限制音量范围
        volume = max(0.0, min(1.0, volume))
        
        self.properties.volume = volume
        
        # 如果已加载音频，立即应用新音量
        if self.loaded_data and self.state in [AudioState.PLAYING, AudioState.PAUSED]:
            try:
                if AUDIO_BACKEND == "pygame":
                    self.loaded_data.set_volume(volume)
                
                elif AUDIO_BACKEND == "nssound":
                    self.loaded_data.setVolume_(volume)
                
                # 其他后端不支持实时调整音量
                
            except Exception as e:
                logger.error(f"设置音量时出错: {e}")
    
    def on_play(self, callback: Callable[[], None]) -> None:
        """添加播放开始回调"""
        self.on_play_callbacks.append(callback)
    
    def on_pause(self, callback: Callable[[], None]) -> None:
        """添加暂停回调"""
        self.on_pause_callbacks.append(callback)
    
    def on_stop(self, callback: Callable[[], None]) -> None:
        """添加停止回调"""
        self.on_stop_callbacks.append(callback)
    
    def on_complete(self, callback: Callable[[], None]) -> None:
        """添加播放完成回调"""
        self.on_complete_callbacks.append(callback)
    
    def on_loop(self, callback: Callable[[int], None]) -> None:
        """添加循环回调"""
        self.on_loop_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[str], None]) -> None:
        """添加错误回调"""
        self.on_error_callbacks.append(callback)
    
    def _trigger_play(self) -> None:
        """触发播放回调"""
        for callback in self.on_play_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行播放回调时出错: {e}")
    
    def _trigger_pause(self) -> None:
        """触发暂停回调"""
        for callback in self.on_pause_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行暂停回调时出错: {e}")
    
    def _trigger_stop(self) -> None:
        """触发停止回调"""
        for callback in self.on_stop_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行停止回调时出错: {e}")
    
    def _trigger_complete(self) -> None:
        """触发完成回调"""
        for callback in self.on_complete_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行完成回调时出错: {e}")
    
    def _trigger_loop(self, loop_count: int) -> None:
        """触发循环回调"""
        for callback in self.on_loop_callbacks:
            try:
                callback(loop_count)
            except Exception as e:
                logger.error(f"执行循环回调时出错: {e}")
    
    def _trigger_error(self, error_message: str) -> None:
        """触发错误回调"""
        for callback in self.on_error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                logger.error(f"执行错误回调时出错: {e}")
    
    def __del__(self) -> None:
        """析构函数，确保资源被释放"""
        if self.state == AudioState.PLAYING:
            self.stop()


class AudioManager:
    """
    音频管理器
    
    管理应用程序中的所有音频资源和播放控制
    """
    
    # 默认音效路径
    DEFAULT_SOUNDS = {
        SoundType.CLICK: "sounds/ui/click.wav",
        SoundType.HOVER: "sounds/ui/hover.wav",
        SoundType.TOGGLE: "sounds/ui/toggle.wav",
        SoundType.SCROLL: "sounds/ui/scroll.wav",
        SoundType.SWIPE: "sounds/ui/swipe.wav",
        SoundType.TYPING: "sounds/ui/typing.wav",
        SoundType.POPUP_OPEN: "sounds/ui/popup_open.wav",
        SoundType.POPUP_CLOSE: "sounds/ui/popup_close.wav",
        SoundType.SUCCESS: "sounds/ui/success.wav",
        SoundType.ERROR: "sounds/ui/error.wav",
        SoundType.WARNING: "sounds/ui/warning.wav",
        SoundType.INFO: "sounds/ui/info.wav",
        SoundType.COMPLETE: "sounds/ui/complete.wav",
        SoundType.LOADING: "sounds/ui/loading.wav",
        SoundType.NOTIFICATION: "sounds/notifications/notification.wav",
        SoundType.MESSAGE: "sounds/notifications/message.wav"
    }
    
    def __init__(self, sound_dir: Optional[str] = None):
        """
        初始化音频管理器
        
        参数:
            sound_dir: 音效文件目录，如果为None则使用默认目录
        """
        # 设置音效目录
        if sound_dir is None:
            # 默认使用当前目录下的 assets/sounds
            self.sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        else:
            self.sound_dir = sound_dir
        
        # 创建音效目录（如果不存在）
        os.makedirs(os.path.join(self.sound_dir, "sounds", "ui"), exist_ok=True)
        os.makedirs(os.path.join(self.sound_dir, "sounds", "notifications"), exist_ok=True)
        os.makedirs(os.path.join(self.sound_dir, "sounds", "background"), exist_ok=True)
        
        # 音频缓存
        self.audio_cache: Dict[str, AudioFile] = {}
        
        # 当前播放的背景音乐
        self.current_background: Optional[AudioFile] = None
        
        # 音量设置
        self.master_volume = 1.0
        self.category_volumes = {
            AudioCategory.UI_FEEDBACK: 0.7,
            AudioCategory.NOTIFICATION: 0.8,
            AudioCategory.BACKGROUND: 0.4,
            AudioCategory.ALERT: 0.9,
            AudioCategory.SUCCESS: 0.7,
            AudioCategory.ERROR: 0.7,
            AudioCategory.AMBIENT: 0.5
        }
        
        # 静音状态
        self.muted = False
        
        # 初始化音频系统
        self._init_audio_system()
        
        # 加载默认音效
        self._preload_default_sounds()
    
    def _init_audio_system(self) -> None:
        """初始化音频系统"""
        if AUDIO_BACKEND == "pygame":
            try:
                if not pygame.get_init():
                    pygame.init()
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                logger.info("音频系统初始化成功 (使用 pygame)")
            except Exception as e:
                logger.error(f"初始化pygame音频系统时出错: {e}")
        
        elif AUDIO_BACKEND == "simpleaudio":
            logger.info("音频系统初始化成功 (使用 simpleaudio)")
        
        elif AUDIO_BACKEND == "winsound":
            logger.info("音频系统初始化成功 (使用 winsound)")
        
        elif AUDIO_BACKEND == "nssound":
            logger.info("音频系统初始化成功 (使用 NSSound)")
        
        else:
            logger.info("音频系统初始化成功 (使用命令行工具)")
    
    def _preload_default_sounds(self) -> None:
        """预加载默认音效"""
        for sound_type, rel_path in self.DEFAULT_SOUNDS.items():
            # 构建完整路径
            full_path = os.path.join(self.sound_dir, rel_path)
            
            # 检查文件是否存在
            if os.path.exists(full_path):
                # 创建AudioFile对象
                audio_file = AudioFile(
                    file_path=full_path,
                    properties=AudioProperties(volume=0.7),
                    category=AudioCategory.UI_FEEDBACK
                )
                
                # 预加载并缓存
                if audio_file.load():
                    self.audio_cache[sound_type.value] = audio_file
                    logger.debug(f"预加载音效: {sound_type.value} ({full_path})")
            else:
                # 如果文件不存在，可以生成默认音效（此处简化处理，仅记录日志）
                logger.warning(f"默认音效文件不存在: {full_path}")
                # self._generate_default_sound(sound_type)
    
    def _generate_default_sound(self, sound_type: SoundType) -> None:
        """
        生成默认音效
        
        参数:
            sound_type: 音效类型
        """
        # 音效生成参数
        duration = 0.1  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 根据音效类型设置不同的生成参数
        if sound_type == SoundType.CLICK:
            frequency = 1000
            volume = 0.5
            duration = 0.05
        elif sound_type == SoundType.HOVER:
            frequency = 1200
            volume = 0.3
            duration = 0.03
        elif sound_type == SoundType.TOGGLE:
            frequency = 800
            volume = 0.6
            duration = 0.08
        elif sound_type == SoundType.SUCCESS:
            frequency = 1500
            volume = 0.7
            duration = 0.2
        elif sound_type == SoundType.ERROR:
            frequency = 300
            volume = 0.7
            duration = 0.2
        elif sound_type == SoundType.NOTIFICATION:
            frequency = 1800
            volume = 0.8
            duration = 0.15
        else:
            frequency = 1000
            volume = 0.5
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 生成正弦波
        for i in range(num_samples):
            t = i / sample_rate
            val = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
            buf[i] = val
        
        # 应用衰减
        for i in range(num_samples):
            buf[i] = int(buf[i] * (1 - i / num_samples))
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name
        
        # 写入WAV文件
        with wave.open(temp_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        # 创建目标目录（如果不存在）
        rel_path = self.DEFAULT_SOUNDS[sound_type]
        target_dir = os.path.dirname(os.path.join(self.sound_dir, rel_path))
        os.makedirs(target_dir, exist_ok=True)
        
        # 复制到目标位置
        target_path = os.path.join(self.sound_dir, rel_path)
        try:
            import shutil
            shutil.copy(temp_path, target_path)
            os.remove(temp_path)  # 删除临时文件
            
            logger.info(f"已生成默认音效: {sound_type.value} ({target_path})")
            
            # 加载生成的音效
            audio_file = AudioFile(
                file_path=target_path,
                properties=AudioProperties(volume=0.7),
                category=AudioCategory.UI_FEEDBACK
            )
            
            if audio_file.load():
                self.audio_cache[sound_type.value] = audio_file
            
        except Exception as e:
            logger.error(f"复制生成的音效文件时出错: {e}")
    
    def play_sound(self, 
                   sound_type: Union[SoundType, str],
                   volume: Optional[float] = None,
                   loop: bool = False) -> Optional[AudioFile]:
        """
        播放界面音效
        
        参数:
            sound_type: 音效类型或音频文件路径
            volume: 音量，如果为None则使用默认音量
            loop: 是否循环播放
        
        返回:
            Optional[AudioFile]: 音频文件对象，如果播放失败则返回None
        """
        # 如果静音，则不播放
        if self.muted:
            return None
        
        # 处理传入的音效类型
        sound_key = sound_type.value if isinstance(sound_type, SoundType) else sound_type
        
        # 检查是否已缓存
        audio_file = self.audio_cache.get(sound_key)
        
        # 如果未缓存，尝试创建并加载
        if audio_file is None:
            # 判断是否是文件路径
            if isinstance(sound_type, str) and os.path.exists(sound_type):
                # 直接使用提供的文件路径
                file_path = sound_type
            elif isinstance(sound_type, str) and os.path.exists(os.path.join(self.sound_dir, sound_type)):
                # 相对于音效目录的路径
                file_path = os.path.join(self.sound_dir, sound_type)
            elif isinstance(sound_type, SoundType) and sound_type in SoundType:
                # 使用默认音效
                rel_path = self.DEFAULT_SOUNDS.get(sound_type)
                if rel_path:
                    file_path = os.path.join(self.sound_dir, rel_path)
                else:
                    logger.error(f"未找到音效类型对应的默认音效: {sound_type}")
                    return None
            else:
                logger.error(f"无效的音效类型或文件路径: {sound_type}")
                return None
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"音效文件不存在: {file_path}")
                return None
            
            # 创建音频文件对象
            audio_file = AudioFile(
                file_path=file_path,
                properties=AudioProperties(
                    volume=self.category_volumes[AudioCategory.UI_FEEDBACK] * self.master_volume if volume is None else volume * self.master_volume,
                    loop=loop
                ),
                category=AudioCategory.UI_FEEDBACK
            )
            
            # 加载音频
            if not audio_file.load():
                return None
            
            # 缓存
            self.audio_cache[sound_key] = audio_file
        
        # 更新属性
        if volume is not None:
            audio_file.set_volume(volume * self.master_volume)
        else:
            # 使用类别音量和主音量
            category_volume = self.category_volumes[audio_file.category]
            audio_file.set_volume(category_volume * self.master_volume)
        
        audio_file.properties.loop = loop
        
        # 播放音频
        if audio_file.play():
            return audio_file
        else:
            return None
    
    def play_notification(self, 
                         notification_type: Union[str, SoundType] = SoundType.NOTIFICATION,
                         volume: Optional[float] = None) -> Optional[AudioFile]:
        """
        播放通知音效
        
        参数:
            notification_type: 通知类型或音频文件路径
            volume: 音量，如果为None则使用默认音量
        
        返回:
            Optional[AudioFile]: 音频文件对象，如果播放失败则返回None
        """
        # 如果静音，则不播放
        if self.muted:
            return None
        
        # 处理传入的通知类型
        if isinstance(notification_type, SoundType):
            sound_key = notification_type.value
        else:
            sound_key = notification_type
        
        # 检查是否已缓存
        audio_file = self.audio_cache.get(sound_key)
        
        # 如果未缓存，尝试创建并加载
        if audio_file is None:
            # 判断是否是文件路径
            if isinstance(notification_type, str) and os.path.exists(notification_type):
                # 直接使用提供的文件路径
                file_path = notification_type
            elif isinstance(notification_type, str) and os.path.exists(os.path.join(self.sound_dir, notification_type)):
                # 相对于音效目录的路径
                file_path = os.path.join(self.sound_dir, notification_type)
            elif notification_type == SoundType.NOTIFICATION or notification_type == "notification":
                # 使用默认通知音效
                file_path = os.path.join(self.sound_dir, self.DEFAULT_SOUNDS[SoundType.NOTIFICATION])
            elif notification_type == SoundType.MESSAGE or notification_type == "message":
                # 使用默认消息音效
                file_path = os.path.join(self.sound_dir, self.DEFAULT_SOUNDS[SoundType.MESSAGE])
            else:
                logger.error(f"无效的通知类型或文件路径: {notification_type}")
                return None
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"通知音效文件不存在: {file_path}")
                return None
            
            # 创建音频文件对象
            audio_file = AudioFile(
                file_path=file_path,
                properties=AudioProperties(
                    volume=self.category_volumes[AudioCategory.NOTIFICATION] * self.master_volume if volume is None else volume * self.master_volume
                ),
                category=AudioCategory.NOTIFICATION
            )
            
            # 加载音频
            if not audio_file.load():
                return None
            
            # 缓存
            self.audio_cache[sound_key] = audio_file
        
        # 更新属性
        if volume is not None:
            audio_file.set_volume(volume * self.master_volume)
        else:
            # 使用类别音量和主音量
            audio_file.set_volume(self.category_volumes[AudioCategory.NOTIFICATION] * self.master_volume)
        
        # 播放音频
        if audio_file.play():
            return audio_file
        else:
            return None
    
    def play_background_music(self, 
                             file_path: str,
                             volume: Optional[float] = None,
                             loop: bool = True,
                             fade_in: float = 1.0) -> Optional[AudioFile]:
        """
        播放背景音乐
        
        参数:
            file_path: 音频文件路径
            volume: 音量，如果为None则使用默认音量
            loop: 是否循环播放
            fade_in: 淡入时间（秒）
        
        返回:
            Optional[AudioFile]: 音频文件对象，如果播放失败则返回None
        """
        # 如果静音，则不播放
        if self.muted:
            return None
        
        # 停止当前播放的背景音乐
        if self.current_background is not None:
            self.current_background.stop()
            self.current_background = None
        
        # 检查文件是否存在
        if not os.path.exists(file_path) and not os.path.exists(os.path.join(self.sound_dir, file_path)):
            logger.error(f"背景音乐文件不存在: {file_path}")
            return None
        
        # 使用完整路径
        if os.path.exists(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.sound_dir, file_path)
        
        # 设置音量
        if volume is None:
            volume = self.category_volumes[AudioCategory.BACKGROUND] * self.master_volume
        else:
            volume = volume * self.master_volume
        
        # 创建音频文件对象
        audio_file = AudioFile(
            file_path=full_path,
            properties=AudioProperties(
                volume=volume,
                loop=loop,
                fade_in=fade_in
            ),
            category=AudioCategory.BACKGROUND
        )
        
        # 加载音频
        if not audio_file.load():
            return None
        
        # 播放背景音乐
        if audio_file.play():
            self.current_background = audio_file
            return audio_file
        else:
            return None
    
    def stop_background_music(self, fade_out: float = 1.0) -> bool:
        """
        停止背景音乐
        
        参数:
            fade_out: 淡出时间（秒）
        
        返回:
            bool: 是否成功停止
        """
        if self.current_background is None:
            return False
        
        # 设置淡出时间
        self.current_background.properties.fade_out = fade_out
        
        # 停止播放
        success = self.current_background.stop()
        
        if success:
            self.current_background = None
        
        return success
    
    def pause_background_music(self) -> bool:
        """
        暂停背景音乐
        
        返回:
            bool: 是否成功暂停
        """
        if self.current_background is None:
            return False
        
        return self.current_background.pause()
    
    def resume_background_music(self) -> bool:
        """
        恢复背景音乐
        
        返回:
            bool: 是否成功恢复
        """
        if self.current_background is None:
            return False
        
        return self.current_background.resume()
    
    def set_master_volume(self, volume: float) -> None:
        """
        设置主音量
        
        参数:
            volume: 音量值 (0.0-1.0)
        """
        # 限制音量范围
        volume = max(0.0, min(1.0, volume))
        
        # 如果值相同，不做任何处理
        if self.master_volume == volume:
            return
        
        # 更新主音量
        self.master_volume = volume
        
        # 更新所有正在播放的音频音量
        for audio_file in self.audio_cache.values():
            if audio_file.state == AudioState.PLAYING:
                category_volume = self.category_volumes[audio_file.category]
                audio_file.set_volume(category_volume * self.master_volume)
        
        # 更新背景音乐音量
        if self.current_background is not None:
            category_volume = self.category_volumes[AudioCategory.BACKGROUND]
            self.current_background.set_volume(category_volume * self.master_volume)
        
        logger.debug(f"设置主音量: {volume}")
    
    def set_category_volume(self, category: AudioCategory, volume: float) -> None:
        """
        设置音频类别音量
        
        参数:
            category: 音频类别
            volume: 音量值 (0.0-1.0)
        """
        # 限制音量范围
        volume = max(0.0, min(1.0, volume))
        
        # 如果值相同，不做任何处理
        if self.category_volumes.get(category, 1.0) == volume:
            return
        
        # 更新类别音量
        self.category_volumes[category] = volume
        
        # 更新该类别所有正在播放的音频音量
        for audio_file in self.audio_cache.values():
            if audio_file.category == category and audio_file.state == AudioState.PLAYING:
                audio_file.set_volume(volume * self.master_volume)
        
        # 更新背景音乐音量（如果类别是背景音乐）
        if category == AudioCategory.BACKGROUND and self.current_background is not None:
            self.current_background.set_volume(volume * self.master_volume)
        
        logger.debug(f"设置{category.value}类别音量: {volume}")
    
    def toggle_mute(self) -> bool:
        """
        切换静音状态
        
        返回:
            bool: 当前是否静音
        """
        self.muted = not self.muted
        
        if self.muted:
            # 停止所有正在播放的音频
            for audio_file in self.audio_cache.values():
                if audio_file.state == AudioState.PLAYING:
                    audio_file.pause()
            
            # 暂停背景音乐
            if self.current_background is not None and self.current_background.state == AudioState.PLAYING:
                self.current_background.pause()
            
            logger.debug("静音已开启")
        else:
            # 恢复背景音乐
            if self.current_background is not None and self.current_background.state == AudioState.PAUSED:
                self.current_background.resume()
            
            logger.debug("静音已关闭")
        
        return self.muted
    
    def set_mute(self, mute: bool) -> None:
        """
        设置静音状态
        
        参数:
            mute: 是否静音
        """
        if self.muted == mute:
            return
        
        self.toggle_mute()
    
    def preload_sound(self, 
                     file_path: str, 
                     sound_id: Optional[str] = None,
                     category: AudioCategory = AudioCategory.UI_FEEDBACK) -> bool:
        """
        预加载音效
        
        参数:
            file_path: 音频文件路径
            sound_id: 音效ID，如果为None则使用文件路径
            category: 音频类别
        
        返回:
            bool: 是否成功加载
        """
        # 检查文件是否存在
        if not os.path.exists(file_path) and not os.path.exists(os.path.join(self.sound_dir, file_path)):
            logger.error(f"音频文件不存在: {file_path}")
            return False
        
        # 使用完整路径
        if os.path.exists(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.sound_dir, file_path)
        
        # 设置音效ID
        if sound_id is None:
            sound_id = file_path
        
        # 如果已经加载，直接返回成功
        if sound_id in self.audio_cache:
            return True
        
        # 创建音频文件对象
        audio_file = AudioFile(
            file_path=full_path,
            properties=AudioProperties(
                volume=self.category_volumes[category] * self.master_volume
            ),
            category=category
        )
        
        # 加载音频
        if audio_file.load():
            # 缓存
            self.audio_cache[sound_id] = audio_file
            logger.debug(f"预加载音效: {sound_id} ({full_path})")
            return True
        else:
            return False
    
    def preload_sounds(self, sound_files: Dict[str, str], category: AudioCategory = AudioCategory.UI_FEEDBACK) -> int:
        """
        批量预加载音效
        
        参数:
            sound_files: 音效文件字典，键为音效ID，值为文件路径
            category: 音频类别
        
        返回:
            int: 成功加载的音效数量
        """
        success_count = 0
        
        for sound_id, file_path in sound_files.items():
            if self.preload_sound(file_path, sound_id, category):
                success_count += 1
        
        return success_count
    
    def play_preloaded_sound(self, 
                            sound_id: str, 
                            volume: Optional[float] = None,
                            loop: bool = False) -> Optional[AudioFile]:
        """
        播放预加载的音效
        
        参数:
            sound_id: 音效ID
            volume: 音量，如果为None则使用默认音量
            loop: 是否循环播放
        
        返回:
            Optional[AudioFile]: 音频文件对象，如果播放失败则返回None
        """
        # 如果静音，则不播放
        if self.muted:
            return None
        
        # 检查是否已加载
        if sound_id not in self.audio_cache:
            logger.error(f"未找到预加载的音效: {sound_id}")
            return None
        
        audio_file = self.audio_cache[sound_id]
        
        # 更新属性
        if volume is not None:
            audio_file.set_volume(volume * self.master_volume)
        else:
            # 使用类别音量和主音量
            category_volume = self.category_volumes[audio_file.category]
            audio_file.set_volume(category_volume * self.master_volume)
        
        audio_file.properties.loop = loop
        
        # 播放音频
        if audio_file.play():
            return audio_file
        else:
            return None
    
    def stop_all_sounds(self) -> None:
        """停止所有音效和音乐"""
        # 停止所有缓存的音效
        for audio_file in self.audio_cache.values():
            if audio_file.state in [AudioState.PLAYING, AudioState.PAUSED]:
                audio_file.stop()
        
        # 停止背景音乐
        if self.current_background is not None:
            self.current_background.stop()
            self.current_background = None
        
        logger.debug("已停止所有音效和音乐")
    
    def cleanup(self) -> None:
        """清理资源"""
        # 停止所有音效和音乐
        self.stop_all_sounds()
        
        # 清空缓存
        self.audio_cache.clear()
        
        # 如果使用pygame，退出mixer
        if AUDIO_BACKEND == "pygame" and pygame.mixer.get_init():
            pygame.mixer.quit()
        
        logger.debug("音频管理器资源已清理")
    
    def __del__(self) -> None:
        """析构函数，确保资源被释放"""
        self.cleanup()


# 工具函数：生成简单的音效

def generate_click_sound(file_path: str, volume: float = 0.7, frequency: float = 1000) -> bool:
    """
    生成点击音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
        frequency: 频率 (Hz)
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.05  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 生成正弦波
        for i in range(num_samples):
            t = i / sample_rate
            val = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
            buf[i] = val
        
        # 应用指数衰减
        for i in range(num_samples):
            buf[i] = int(buf[i] * math.exp(-5 * i / num_samples))
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成点击音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成点击音效时出错: {e}")
        return False


def generate_notification_sound(file_path: str, volume: float = 0.8) -> bool:
    """
    生成通知音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.3  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 生成两个频率的正弦波组合
        freq1 = 1800  # 第一个频率
        freq2 = 2200  # 第二个频率
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # 第一部分是上升音调
            if t < duration / 2:
                val = math.sin(2 * math.pi * (freq1 + (freq2 - freq1) * t / (duration / 2)) * t)
            # 第二部分是下降音调
            else:
                val = math.sin(2 * math.pi * (freq2 - (freq2 - freq1) * (t - duration / 2) / (duration / 2)) * t)
            
            buf[i] = int(32767 * volume * val)
        
        # 应用振幅包络
        for i in range(num_samples):
            t = i / num_samples
            # 快速上升，缓慢下降
            if t < 0.1:
                envelope = t / 0.1
            else:
                envelope = 1.0 - (t - 0.1) / 0.9
            
            buf[i] = int(buf[i] * envelope)
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成通知音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成通知音效时出错: {e}")
        return False


def generate_success_sound(file_path: str, volume: float = 0.7) -> bool:
    """
    生成成功提示音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.6  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 生成和弦音效 - 简单的三和弦
        freq_base = 440.0  # A4
        freq_major_third = 554.37  # C#5
        freq_fifth = 659.25  # E5
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # 基音
            wave1 = math.sin(2 * math.pi * freq_base * t)
            # 大三度
            wave2 = math.sin(2 * math.pi * freq_major_third * t)
            # 纯五度
            wave3 = math.sin(2 * math.pi * freq_fifth * t)
            
            # 混合三个波形
            val = (wave1 + wave2 * 0.8 + wave3 * 0.6) / 3.0
            
            buf[i] = int(32767 * volume * val)
        
        # 应用渐变
        for i in range(num_samples):
            t = i / num_samples
            # 快速上升，缓慢下降
            if t < 0.1:
                envelope = t / 0.1
            else:
                envelope = 1.0 * math.exp(-3 * (t - 0.1))
            
            buf[i] = int(buf[i] * envelope)
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成成功音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成成功音效时出错: {e}")
        return False


def generate_error_sound(file_path: str, volume: float = 0.7) -> bool:
    """
    生成错误提示音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.5  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 生成和弦音效 - 不和谐的和弦
        freq1 = 277.18  # C#4
        freq2 = 370.0   # F#4
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # 两个不和谐频率
            wave1 = math.sin(2 * math.pi * freq1 * t)
            wave2 = math.sin(2 * math.pi * freq2 * t)
            
            # 两次短促的声音
            if t < 0.15 or (0.25 < t < 0.4):
                val = (wave1 * 0.7 + wave2 * 0.8) / 2.0
            else:
                val = 0
            
            buf[i] = int(32767 * volume * val)
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成错误音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成错误音效时出错: {e}")
        return False


def generate_button_hover_sound(file_path: str, volume: float = 0.3) -> bool:
    """
    生成按钮悬停音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.08  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 生成扫频音效（从高频到低频）
        freq_start = 2000
        freq_end = 1500
        
        for i in range(num_samples):
            t = i / sample_rate
            # 线性频率变化
            freq = freq_start + (freq_end - freq_start) * (t / duration)
            val = math.sin(2 * math.pi * freq * t)
            
            buf[i] = int(32767 * volume * val)
        
        # 应用淡入淡出
        fade_samples = int(0.02 * sample_rate)  # 20ms淡入淡出
        for i in range(fade_samples):
            # 淡入
            buf[i] = int(buf[i] * (i / fade_samples))
            # 淡出
            if i < fade_samples and (num_samples - i - 1) >= 0:
                buf[num_samples - i - 1] = int(buf[num_samples - i - 1] * (i / fade_samples))
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成按钮悬停音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成按钮悬停音效时出错: {e}")
        return False


def generate_toggle_sound(file_path: str, volume: float = 0.6, is_on: bool = True) -> bool:
    """
    生成开关切换音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
        is_on: 是否是打开状态的音效
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.15  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 根据开关状态调整频率
        if is_on:
            # 打开：从低到高
            freq_start = 700
            freq_end = 1200
        else:
            # 关闭：从高到低
            freq_start = 1200
            freq_end = 700
        
        for i in range(num_samples):
            t = i / sample_rate
            # 非线性频率变化
            progress = math.pow(t / duration, 1.5)
            freq = freq_start + (freq_end - freq_start) * progress
            val = math.sin(2 * math.pi * freq * t)
            
            # 添加轻微噪声模拟机械感
            noise = (random.random() * 2 - 1) * 0.1
            combined = val * 0.9 + noise * 0.1
            
            buf[i] = int(32767 * volume * combined)
        
        # 应用振幅包络
        for i in range(num_samples):
            t = i / num_samples
            # 开启时快速上升，慢速下降
            if is_on:
                if t < 0.2:
                    envelope = t / 0.2
                else:
                    envelope = 1.0 - (t - 0.2) / 0.8
            # 关闭时慢速上升，快速下降
            else:
                if t < 0.6:
                    envelope = t / 0.6
                else:
                    envelope = 1.0 - (t - 0.6) / 0.4
            
            buf[i] = int(buf[i] * envelope)
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成开关{('打开' if is_on else '关闭')}音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成开关音效时出错: {e}")
        return False


def generate_typing_sound(file_path: str, volume: float = 0.4) -> bool:
    """
    生成打字音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.03  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 随机选择基频以增加变化
        base_freq = random.uniform(1200, 1600)
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # 基础音调
            wave = math.sin(2 * math.pi * base_freq * t)
            
            # 添加一些高频噪声模拟按键声
            noise = (random.random() * 2 - 1) * 0.3
            
            # 混合声音
            val = wave * 0.7 + noise * 0.3
            
            buf[i] = int(32767 * volume * val)
        
        # 应用快速衰减
        for i in range(num_samples):
            t = i / num_samples
            envelope = math.exp(-10 * t)
            buf[i] = int(buf[i] * envelope)
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成打字音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成打字音效时出错: {e}")
        return False


def generate_popup_sound(file_path: str, volume: float = 0.6, is_open: bool = True) -> bool:
    """
    生成弹窗打开/关闭音效
    
    参数:
        file_path: 保存路径
        volume: 音量 (0.0-1.0)
        is_open: 是否是打开状态的音效
    
    返回:
        bool: 是否成功生成
    """
    try:
        # 音效参数
        duration = 0.3 if is_open else 0.25  # 秒
        sample_rate = 44100
        channels = 1
        bit_depth = 16
        
        # 生成音频数据
        num_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * num_samples)
        
        # 根据状态调整参数
        if is_open:
            # 打开：较长，从低到高，有弹性
            freq_start = 300
            freq_end = 800
            envelope_peak = 0.3  # 音量峰值位置
        else:
            # 关闭：较短，从高到低，快速衰减
            freq_start = 700
            freq_end = 300
            envelope_peak = 0.1  # 音量峰值位置
        
        for i in range(num_samples):
            t = i / sample_rate
            progress = t / duration
            
            # 非线性频率变化
            if is_open:
                # 开始快速上升，之后慢速上升
                freq_progress = 1 - math.exp(-5 * progress)
            else:
                # 快速下降
                freq_progress = math.exp(-2 * progress) - 0.1 * progress
            
            freq = freq_start + (freq_end - freq_start) * freq_progress
            
            # 基础波形
            val = math.sin(2 * math.pi * freq * t)
            
            # 添加和谐泛音
            if is_open:
                val += 0.3 * math.sin(2 * math.pi * freq * 2 * t)  # 二次泛音
            else:
                val += 0.2 * math.sin(2 * math.pi * freq * 1.5 * t)  # 1.5次泛音
            
            val = val / 1.3  # 归一化
            
            buf[i] = int(32767 * volume * val)
        
        # 应用振幅包络
        for i in range(num_samples):
            t = i / num_samples
            
            if is_open:
                # 打开：先快速上升，达到峰值后有轻微的振荡
                if t < envelope_peak:
                    envelope = t / envelope_peak
                else:
                    # 添加轻微振荡效果
                    decay = (t - envelope_peak) / (1 - envelope_peak)
                    envelope = (1 - decay) * (1 + 0.1 * math.sin(20 * math.pi * decay))
            else:
                # 关闭：快速达到峰值，然后快速衰减
                if t < envelope_peak:
                    envelope = t / envelope_peak
                else:
                    envelope = (1 - t) / (1 - envelope_peak)
            
            buf[i] = int(buf[i] * max(0, min(1, envelope)))
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入WAV文件
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buf.tobytes())
        
        logger.info(f"生成弹窗{('打开' if is_open else '关闭')}音效: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成弹窗音效时出错: {e}")
        return False


def generate_all_default_sounds(output_dir: str) -> int:
    """
    生成所有默认音效
    
    参数:
        output_dir: 输出目录
    
    返回:
        int: 成功生成的音效数量
    """
    success_count = 0
    
    # 创建目录结构
    ui_dir = os.path.join(output_dir, "sounds", "ui")
    notification_dir = os.path.join(output_dir, "sounds", "notifications")
    
    os.makedirs(ui_dir, exist_ok=True)
    os.makedirs(notification_dir, exist_ok=True)
    
    # 生成UI音效
    if generate_click_sound(os.path.join(ui_dir, "click.wav")):
        success_count += 1
    
    if generate_button_hover_sound(os.path.join(ui_dir, "hover.wav")):
        success_count += 1
    
    if generate_toggle_sound(os.path.join(ui_dir, "toggle.wav"), is_on=True):
        success_count += 1
    
    if generate_typing_sound(os.path.join(ui_dir, "typing.wav")):
        success_count += 1
    
    if generate_popup_sound(os.path.join(ui_dir, "popup_open.wav"), is_open=True):
        success_count += 1
    
    if generate_popup_sound(os.path.join(ui_dir, "popup_close.wav"), is_open=False):
        success_count += 1
    
    if generate_success_sound(os.path.join(ui_dir, "success.wav")):
        success_count += 1
    
    if generate_error_sound(os.path.join(ui_dir, "error.wav")):
        success_count += 1
    
    # 生成通知音效
    if generate_notification_sound(os.path.join(notification_dir, "notification.wav")):
        success_count += 1
    
    return success_count


# 示例用法（供参考）
def example_usage():
    """音频模块使用示例"""
    
    # 初始化音频管理器
    audio_mgr = AudioManager()
    
    # 播放点击音效
    audio_mgr.play_sound(SoundType.CLICK)
    
    # 等待一段时间
    time.sleep(0.5)
    
    # 播放成功音效
    audio_mgr.play_sound(SoundType.SUCCESS)
    
    time.sleep(1)
    
    # 播放通知音效
    audio_mgr.play_notification()
    
    time.sleep(1)
    
    # 调整音量
    audio_mgr.set_master_volume(0.5)
    
    # 播放背景音乐
    music_file = os.path.join(audio_mgr.sound_dir, "sounds", "background", "ambient.wav")
    if os.path.exists(music_file):
        bg_music = audio_mgr.play_background_music(music_file, loop=True)
    
    time.sleep(2)
    
    # 停止背景音乐
    audio_mgr.stop_background_music(fade_out=1.0)
    
    # 清理资源
    audio_mgr.cleanup()


if __name__ == "__main__":
    # 如果直接运行该模块，展示使用示例
    example_usage()

            wave1 =