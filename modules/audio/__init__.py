# -*- coding: utf-8 -*-
"""
音频模块: 音频处理子包初始化
功能描述: 提供语音转文本和文本转语音功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

# 版本信息
__version__ = "1.0.0"

# 导出子模块类和函数
from .speech_to_text import SpeechToText, SpeechRecognitionConfig
from .text_to_speech import TextToSpeech, SpeechSynthesisConfig

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"音频处理模块初始化完成，版本 {__version__}")

# 从配置加载器加载音频模块特定配置
try:
    from ...config.config_loader import ConfigLoader
    # 初始化配置加载器
    config_loader = ConfigLoader()
    AUDIO_CONFIG = config_loader.load("modules.audio")
except ImportError:
    import warnings
    warnings.warn("配置加载器未找到，使用默认音频模块配置")
    AUDIO_CONFIG = {
        "speech_to_text": {
            "default_language": "en-US",
            "default_model": "default",
            "timeout": 30
        },
        "text_to_speech": {
            "default_voice": "default",
            "default_language": "en-US",
            "audio_format": "wav"
        }
    }

# 导出的模块、类和函数
__all__ = [
    "SpeechToText",
    "SpeechRecognitionConfig",
    "TextToSpeech",
    "SpeechSynthesisConfig",
    "get_audio_config"
]

def get_audio_config():
    """
    获取音频模块配置
    
    返回:
        dict: 音频模块的配置字典
    """
    return AUDIO_CONFIG