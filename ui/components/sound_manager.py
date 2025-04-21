# ui/components/sound_manager.py
"""
音效管理和播放机制

这个组件负责管理应用程序中的音频效果，提供统一的接口和工具。
它实现了以下功能：
1. 加载和播放不同类型的音效
2. 管理音效音量和静音设置
3. 支持音效分组和分类
4. 提供基于上下文的音效播放

设计理念:
- 音效应当增强用户体验，传递情感和反馈
- 提供适当的声音线索，增强用户操作的满足感
- 所有声音应当优雅且不打扰用户
"""

import os
import time
import threading
import json
from typing import Dict, List, Optional, Callable, Union

try:
    # 尝试导入 pygame 用于音频播放
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    # 尝试导入 playsound 作为备选
    from playsound import playsound

    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

try:
    # 尝试导入 winsound 作为 Windows 平台的备选
    import winsound

    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class SoundManager:
    """声音管理器，负责管理和播放应用中的音效"""

    def __init__(self, sounds_dir=None, config_dir=None):
        """
        初始化声音管理器

        Args:
            sounds_dir: 音效文件目录
            config_dir: 配置文件目录
        """
        # 设置目录
        self.sounds_dir = sounds_dir or os.path.join(
            os.path.dirname(__file__), "../../assets/sounds"
        )
        self.config_dir = config_dir or os.path.join(
            os.path.expanduser("~"), ".ai_assistant"
        )

        # 确保目录存在
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        # 音效和设置
        self.sounds = {}  # 音效缓存
        self.categories = {}  # 音效分类
        self.volume = 1.0  # 主音量 (0.0 - 1.0)
        self.muted = False  # 是否静音
        self.enabled = True  # 是否启用音效

        # 初始化音频后端
        self._init_audio_backend()

        # 加载设置和音效
        self._load_settings()
        self._load_sound_catalog()

    def _init_audio_backend(self):
        """初始化音频后端"""
        self.backend = None

        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.backend = "pygame"
                print("使用 Pygame 音频后端")
            except Exception as e:
                print(f"初始化 Pygame 音频后端失败: {e}")

        if not self.backend and PLAYSOUND_AVAILABLE:
            self.backend = "playsound"
            print("使用 playsound 音频后端")

        if not self.backend and WINSOUND_AVAILABLE:
            self.backend = "winsound"
            print("使用 Windows 音频后端")

        if not self.backend:
            print("警告: 没有可用的音频后端，音效将被禁用")
            self.enabled = False

    def _load_settings(self):
        """加载声音设置"""
        settings_path = os.path.join(self.config_dir, "sound_settings.json")

        try:
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                self.volume = float(settings.get("volume", 1.0))
                self.muted = bool(settings.get("muted", False))
                self.enabled = bool(settings.get("enabled", True))
        except Exception as e:
            print(f"加载声音设置时出错: {e}")

    def _save_settings(self):
        """保存声音设置"""
        settings_path = os.path.join(self.config_dir, "sound_settings.json")

        try:
            settings = {
                "volume": self.volume,
                "muted": self.muted,
                "enabled": self.enabled,
            }

            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"保存声音设置时出错: {e}")

    def _load_sound_catalog(self):
        """加载音效目录"""
        catalog_path = os.path.join(self.sounds_dir, "catalog.json")

        try:
            if os.path.exists(catalog_path):
                with open(catalog_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)

                # 加载分类
                self.categories = catalog.get("categories", {})

                # 预加载音效
                preload_list = catalog.get("preload", [])
                for sound_id in preload_list:
                    self.load_sound(sound_id)
        except Exception as e:
            print(f"加载音效目录时出错: {e}")

        # 如果没有目录文件，尝试扫描音效目录
        if not self.categories:
            self._scan_sounds_directory()

    def _scan_sounds_directory(self):
        """扫描音效目录，创建音效分类"""
        try:
            for root, dirs, files in os.walk(self.sounds_dir):
                # 获取相对路径
                rel_path = os.path.relpath(root, self.sounds_dir)

                # 跳过根目录
                if rel_path == ".":
                    continue

                # 创建分类
                category = rel_path.replace(os.path.sep, "/")
                self.categories[category] = []

                # 添加音效文件
                for file in files:
                    if file.endswith((".wav", ".mp3", ".ogg")):
                        sound_id = f"{category}/{os.path.splitext(file)[0]}"
                        self.categories[category].append(sound_id)
        except Exception as e:
            print(f"扫描音效目录时出错: {e}")

    def load_sound(self, sound_id):
        """
        加载音效

        Args:
            sound_id: 音效ID

        Returns:
            bool: 是否成功加载
        """
        if not self.enabled or sound_id in self.sounds:
            return sound_id in self.sounds

        # 查找音效文件
        sound_path = self._get_sound_path(sound_id)
        if not sound_path or not os.path.exists(sound_path):
            print(f"音效文件不存在: {sound_id}")
            return False

        try:
            if self.backend == "pygame":
                self.sounds[sound_id] = pygame.mixer.Sound(sound_path)
                return True
            else:
                # 对于其他后端，只需记录路径
                self.sounds[sound_id] = sound_path
                return True
        except Exception as e:
            print(f"加载音效 {sound_id} 时出错: {e}")
            return False

    def _get_sound_path(self, sound_id):
        """
        获取音效文件路径

        Args:
            sound_id: 音效ID

        Returns:
            str: 音效文件路径
        """
        # 检查不同的文件扩展名
        for ext in [".wav", ".mp3", ".ogg"]:
            path = os.path.join(self.sounds_dir, sound_id + ext)
            if os.path.exists(path):
                return path

        # 处理包含目录的ID
        if "/" in sound_id:
            category, name = sound_id.rsplit("/", 1)
            for ext in [".wav", ".mp3", ".ogg"]:
                path = os.path.join(self.sounds_dir, category, name + ext)
                if os.path.exists(path):
                    return path

        return None

    def play(self, sound_id, volume=None, loop=False):
        """
        播放音效

        Args:
            sound_id: 音效ID
            volume: 音量 (0.0 - 1.0)，None 表示使用主音量
            loop: 是否循环播放

        Returns:
            bool: 是否成功播放
        """
        if not self.enabled or self.muted:
            return False

        # 获取实际音量
        actual_volume = volume if volume is not None else self.volume
        if actual_volume <= 0:
            return False

        # 加载音效（如果尚未加载）
        if sound_id not in self.sounds and not self.load_sound(sound_id):
            return False

        try:
            if self.backend == "pygame":
                sound = self.sounds[sound_id]
                sound.set_volume(actual_volume)
                loop_count = -1 if loop else 0
                sound.play(loops=loop_count)
                return True
            elif self.backend == "playsound":
                # playsound 不支持音量调节和循环播放
                # 在新线程中播放以避免阻塞
                threading.Thread(
                    target=self._play_with_playsound,
                    args=(self.sounds[sound_id], loop),
                    daemon=True,
                ).start()
                return True
            elif self.backend == "winsound" and sound_id.endswith(".wav"):
                # winsound 只支持 WAV 文件
                # 在新线程中播放以避免阻塞
                threading.Thread(
                    target=self._play_with_winsound,
                    args=(self.sounds[sound_id], loop),
                    daemon=True,
                ).start()
                return True
        except Exception as e:
            print(f"播放音效 {sound_id} 时出错: {e}")

        return False

    def _play_with_playsound(self, sound_path, loop):
        """使用 playsound 播放音效"""
        try:
            if loop:
                while self.enabled and not self.muted:
                    playsound(sound_path)
            else:
                playsound(sound_path)
        except Exception as e:
            print(f"使用 playsound 播放音效时出错: {e}")

    def _play_with_winsound(self, sound_path, loop):
        """使用 winsound 播放音效"""
        try:
            if loop:
                while self.enabled and not self.muted:
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME)
            else:
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
        except Exception as e:
            print(f"使用 winsound 播放音效时出错: {e}")

    def stop(self, sound_id=None):
        """
        停止播放音效

        Args:
            sound_id: 要停止的音效ID，None 表示停止所有音效

        Returns:
            bool: 是否成功停止
        """
        if not self.enabled:
            return False

        try:
            if self.backend == "pygame":
                if sound_id is None:
                    # 停止所有音效
                    pygame.mixer.stop()
                elif sound_id in self.sounds:
                    # 停止特定音效
                    self.sounds[sound_id].stop()
                return True
            else:
                # 其他后端不支持停止播放
                print("当前音频后端不支持停止播放")
                return False
        except Exception as e:
            print(f"停止音效播放时出错: {e}")
            return False

    def set_volume(self, volume):
        """
        设置主音量

        Args:
            volume: 音量 (0.0 - 1.0)

        Returns:
            bool: 是否成功设置
        """
        try:
            # 确保音量在有效范围内
            volume = max(0.0, min(1.0, float(volume)))
            self.volume = volume
            self._save_settings()
            return True
        except Exception as e:
            print(f"设置音量时出错: {e}")
            return False

    def get_volume(self):
        """
        获取当前主音量

        Returns:
            float: 当前音量 (0.0 - 1.0)
        """
        return self.volume

    def set_muted(self, muted):
        """
        设置静音状态

        Args:
            muted: 是否静音

        Returns:
            bool: 是否成功设置
        """
        try:
            self.muted = bool(muted)

            # 如果静音，停止所有声音
            if self.muted and self.backend == "pygame":
                pygame.mixer.stop()

            self._save_settings()
            return True
        except Exception as e:
            print(f"设置静音状态时出错: {e}")
            return False

    def is_muted(self):
        """
        获取当前静音状态

        Returns:
            bool: 是否静音
        """
        return self.muted

    def set_enabled(self, enabled):
        """
        设置音效是否启用

        Args:
            enabled: 是否启用音效

        Returns:
            bool: 是否成功设置
        """
        try:
            prev_enabled = self.enabled
            self.enabled = bool(enabled)

            # 如果禁用，停止所有声音
            if prev_enabled and not self.enabled and self.backend == "pygame":
                pygame.mixer.stop()

            self._save_settings()
            return True
        except Exception as e:
            print(f"设置音效启用状态时出错: {e}")
            return False

    def is_enabled(self):
        """
        获取当前音效启用状态

        Returns:
            bool: 是否启用音效
        """
        return self.enabled

    def get_categories(self):
        """
        获取所有音效分类

        Returns:
            dict: 音效分类字典
        """
        return self.categories

    def get_sounds_in_category(self, category):
        """
        获取指定分类中的所有音效

        Args:
            category: 分类名称

        Returns:
            list: 音效ID列表
        """
        return self.categories.get(category, [])

    def play_random_from_category(self, category, volume=None):
        """
        从指定分类中随机播放一个音效

        Args:
            category: 分类名称
            volume: 音量 (0.0 - 1.0)，None 表示使用主音量

        Returns:
            bool: 是否成功播放
        """
        import random

        sounds = self.get_sounds_in_category(category)
        if not sounds:
            return False

        sound_id = random.choice(sounds)
        return self.play(sound_id, volume)

    def play_ui_sound(self, action, volume=None):
        """
        播放UI交互音效

        Args:
            action: 操作类型，例如 'click', 'hover', 'success', 'error', 'notification'
            volume: 音量 (0.0 - 1.0)，None 表示使用主音量

        Returns:
            bool: 是否成功播放
        """
        # UI音效映射
        ui_sounds = {
            "click": "ui/click",
            "hover": "ui/hover",
            "success": "ui/success",
            "error": "ui/error",
            "notification": "ui/notification",
            "alert": "ui/alert",
            "toggle": "ui/toggle",
            "swipe": "ui/swipe",
            "typing": "ui/typing",
            "complete": "ui/complete",
        }

        sound_id = ui_sounds.get(action.lower())
        if sound_id:
            return self.play(sound_id, volume)

        return False

    def preload_category(self, category):
        """
        预加载指定分类的所有音效

        Args:
            category: 分类名称

        Returns:
            int: 加载的音效数量
        """
        count = 0
        sounds = self.get_sounds_in_category(category)

        for sound_id in sounds:
            if self.load_sound(sound_id):
                count += 1

        return count

    def play_sequence(self, sound_ids, interval=0.5, volume=None):
        """
        按顺序播放一系列音效

        Args:
            sound_ids: 音效ID列表
            interval: 音效之间的间隔（秒）
            volume: 音量 (0.0 - 1.0)，None 表示使用主音量

        Returns:
            bool: 是否成功开始播放序列
        """
        if not self.enabled or self.muted or not sound_ids:
            return False

        # 在新线程中播放序列
        threading.Thread(
            target=self._play_sequence, args=(
                sound_ids, interval, volume), daemon=True
        ).start()

        return True

    def _play_sequence(self, sound_ids, interval, volume):
        """内部方法：按顺序播放音效"""
        for sound_id in sound_ids:
            if not self.enabled or self.muted:
                break

            self.play(sound_id, volume)
            time.sleep(interval)

    def register_sound_event(self, event_name, sound_id, volume=None):
        """
        注册声音事件

        Args:
            event_name: 事件名称
            sound_id: 要播放的音效ID
            volume: 音量 (0.0 - 1.0)，None 表示使用主音量

        Returns:
            bool: 是否成功注册
        """
        try:
            # 确保音效存在
            if not self._get_sound_path(sound_id):
                return False

            event_path = os.path.join(self.config_dir, "sound_events.json")

            # 加载现有事件
            events = {}
            if os.path.exists(event_path):
                with open(event_path, "r", encoding="utf-8") as f:
                    events = json.load(f)

            # 注册事件
            events[event_name] = {"sound_id": sound_id, "volume": volume}

            # 保存事件
            with open(event_path, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)

            return True
        except Exception as e:
            print(f"注册声音事件时出错: {e}")
            return False

    def trigger_event(self, event_name):
        """
        触发声音事件

        Args:
            event_name: 事件名称

        Returns:
            bool: 是否成功触发
        """
        try:
            event_path = os.path.join(self.config_dir, "sound_events.json")

            # 加载事件
            if not os.path.exists(event_path):
                return False

            with open(event_path, "r", encoding="utf-8") as f:
                events = json.load(f)

            # 检查事件是否存在
            if event_name not in events:
                return False

            # 获取事件信息
            event = events[event_name]
            sound_id = event.get("sound_id")
            volume = event.get("volume")

            # 播放音效
            return self.play(sound_id, volume)
        except Exception as e:
            print(f"触发声音事件时出错: {e}")
            return False

    def clear_cache(self):
        """
        清除音效缓存

        Returns:
            bool: 是否成功清除
        """
        try:
            # 停止所有声音
            if self.backend == "pygame":
                pygame.mixer.stop()

            # 清除缓存
            self.sounds = {}
            return True
        except Exception as e:
            print(f"清除音效缓存时出错: {e}")
            return False

    def shutdown(self):
        """
        关闭声音管理器

        Returns:
            bool: 是否成功关闭
        """
        try:
            # 停止所有声音
            if self.backend == "pygame":
                pygame.mixer.stop()
                pygame.mixer.quit()

            # 清除缓存
            self.sounds = {}
            return True
        except Exception as e:
            print(f"关闭声音管理器时出错: {e}")
            return False


# 示例用法
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk

    # 创建测试 UI
    root = tk.Tk()
    root.title("音效系统演示")
    root.geometry("600x400")
    root.configure(background="#f5f5f7")

    # 创建声音管理器
    sound_manager = SoundManager()

    # 主框架
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 标题
    title_label = ttk.Label(
        main_frame, text="音效系统演示", font=("Helvetica", 16, "bold")
    )
    title_label.pack(pady=(0, 20))

    # UI 音效部分
    ui_frame = ttk.LabelFrame(main_frame, text="UI 音效", padding=10)
    ui_frame.pack(fill=tk.X, pady=10)

    ui_buttons_frame = ttk.Frame(ui_frame)
    ui_buttons_frame.pack(fill=tk.X)

    # UI音效按钮
    def play_ui_sound(action):
        sound_manager.play_ui_sound(action)

    ui_actions = ["click", "hover", "success",
                  "error", "notification", "alert"]

    for action in ui_actions:
        btn = ttk.Button(
            ui_buttons_frame,
            text=action.capitalize(),
            command=lambda a=action: play_ui_sound(a),
        )
        btn.pack(side=tk.LEFT, padx=5, pady=5)

    # 音量控制
    volume_frame = ttk.LabelFrame(main_frame, text="音量控制", padding=10)
    volume_frame.pack(fill=tk.X, pady=10)

    volume_value = tk.DoubleVar(value=sound_manager.get_volume())

    def on_volume_change(event=None):
        value = volume_slider.get()
        sound_manager.set_volume(value)
        volume_label.config(text=f"音量: {int(value * 100)}%")

        # 播放音效反馈
        if value > 0:
            sound_manager.play_ui_sound("click")

    volume_slider = ttk.Scale(
        volume_frame,
        from_=0.0,
        to=1.0,
        orient=tk.HORIZONTAL,
        variable=volume_value,
        command=on_volume_change,
    )
    volume_slider.pack(fill=tk.X, padx=10, pady=5)

    volume_label = ttk.Label(
        volume_frame, text=f"音量: {int(volume_value.get() * 100)}%"
    )
    volume_label.pack(pady=5)

    # 静音控制
    mute_var = tk.BooleanVar(value=sound_manager.is_muted())

    def on_mute_toggle():
        muted = mute_var.get()
        sound_manager.set_muted(muted)

        # 如果取消静音，播放确认音效
        if not muted:
            sound_manager.play_ui_sound("toggle")

    mute_check = ttk.Checkbutton(
        volume_frame, text="静音", variable=mute_var, command=on_mute_toggle
    )
    mute_check.pack(pady=5)

    # 序列播放演示
    sequence_frame = ttk.LabelFrame(main_frame, text="音效序列", padding=10)
    sequence_frame.pack(fill=tk.X, pady=10)

    def play_success_sequence():
        sound_manager.play_sequence(
            ["ui/click", "ui/success", "ui/complete"], interval=0.3
        )

    def play_error_sequence():
        sound_manager.play_sequence(
            ["ui/click", "ui/error", "ui/alert"], interval=0.3)

    sequence_buttons_frame = ttk.Frame(sequence_frame)
    sequence_buttons_frame.pack(fill=tk.X)

    success_btn = ttk.Button(
        sequence_buttons_frame, text="成功序列", command=play_success_sequence
    )
    success_btn.pack(side=tk.LEFT, padx=5, pady=5)

    error_btn = ttk.Button(
        sequence_buttons_frame, text="错误序列", command=play_error_sequence
    )
    error_btn.pack(side=tk.LEFT, padx=5, pady=5)

    # 状态栏
    status_frame = ttk.Frame(root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)

    status_label = ttk.Label(
        status_frame, text=f"音频后端: {sound_manager.backend or '无可用后端'}"
    )
    status_label.pack(side=tk.LEFT, padx=10, pady=5)

    root.mainloop()