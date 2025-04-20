# ui/cli/sounds.py
import os
import threading
import time
import platform

# 检测系统类型
SYSTEM = platform.system()

# 尝试导入声音库
sound_available = False
beep_function = None

try:
    if SYSTEM == "Windows":
        import winsound
        def _win_beep(frequency, duration):
            winsound.Beep(frequency, duration)
        beep_function = _win_beep
        sound_available = True
    elif SYSTEM == "Darwin":  # macOS
        def _mac_beep(frequency, duration):
            os.system(f"afplay /System/Library/Sounds/Tink.aiff")
        beep_function = _mac_beep
        sound_available = True
    else:  # Linux 和其他系统
        # 尝试使用 'beep' 命令
        if os.system("which beep > /dev/null 2>&1") == 0:
            def _linux_beep(frequency, duration):
                os.system(f"beep -f {frequency} -l {duration}")
            beep_function = _linux_beep
            sound_available = True
        # 如果没有 'beep' 命令，尝试使用 'espeak'
        elif os.system("which espeak > /dev/null 2>&1") == 0:
            def _espeak_beep(frequency, duration):
                # 使用语音合成器发出不同音调的声音
                pitch = int(frequency / 20)  # 将频率转换为 espeak 的音调
                os.system(f"espeak -a 10 -p {pitch} 'beep' --stdout > /dev/null 2>&1")
            beep_function = _espeak_beep
            sound_available = True
        # 最后的后备方案
        else:
            def _print_beep(frequency, duration):
                print("\a", end="", flush=True)  # 尝试使用终端铃声
            beep_function = _print_beep
            sound_available = True
except Exception as e:
    print(f"声音系统初始化失败: {str(e)}")
    sound_available = False

# 音效定义
SOUND_EFFECTS = {
    "startup": [(440, 100), (880, 100), (1760, 100)],
    "shutdown": [(1760, 100), (880, 100), (440, 100)],
    "success": [(880, 100), (1320, 200)],
    "error": [(220, 300)],
    "warning": [(440, 100), (440, 100)],
    "notification": [(880, 50), (0, 30), (880, 50)],
    "typing": [(440, 10)],
    "command": [(660, 30)],
    "progress": [(550, 20)]
}

# 音效设置
_sound_enabled = True
_typing_sound_enabled = False
_volume = 1.0  # 0.0-1.0

def enable_sound(enabled=True):
    """启用或禁用声音"""
    global _sound_enabled
    old_setting = _sound_enabled
    _sound_enabled = enabled and sound_available
    return old_setting

def enable_typing_sound(enabled=True):
    """启用或禁用打字音效"""
    global _typing_sound_enabled
    old_setting = _typing_sound_enabled
    _typing_sound_enabled = enabled and sound_available
    return old_setting

def set_volume(volume):
    """设置音量 (0.0-1.0)"""
    global _volume
    _volume = max(0.0, min(1.0, volume))
    return _volume

def beep(frequency, duration):
    """发出蜂鸣声"""
    if not _sound_enabled or not sound_available:
        return
    
    # 应用音量设置
    effective_duration = int(duration * _volume)
    if effective_duration <= 0:
        return
    
    try:
        beep_function(frequency, effective_duration)
    except Exception as e:
        print(f"声音播放失败: {str(e)}")

def play_effect(effect_name):
    """播放预定义音效"""
    if not _sound_enabled or not sound_available:
        return
    
    if effect_name not in SOUND_EFFECTS:
        return
    
    def _play_sequence():
        for freq, dur in SOUND_EFFECTS[effect_name]:
            if freq > 0:
                beep(freq, dur)
            else:
                time.sleep(dur / 1000.0)  # 转换为秒
    
    # 在后台线程播放音效
    threading.Thread(target=_play_sequence, daemon=True).start()

def play_typing_sound():
    """播放打字音效"""
    if _typing_sound_enabled and _sound_enabled and sound_available:
        # 使用非常短的音效，不打断用户体验
        threading.Thread(target=lambda: beep(440, 5), daemon=True).start()

# 自定义音效
def create_custom_effect(name, sequence):
    """创建自定义音效
    
    参数:
        name (str): 音效名称
        sequence (list): 音效序列，格式为 [(频率, 持续时间), ...]
    """
    SOUND_EFFECTS[name] = sequence
    return True

# 示例自定义音效
create_custom_effect("sci_fi", [(1760, 50), (0, 30), (880, 100), (1320, 200)])
create_custom_effect("retro", [(110, 50), (220, 50), (330, 50), (440, 50)])