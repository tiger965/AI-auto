# tests/test_modules/test_audio/__init__.py
"""
音频模块测试包
包含语音转文本和文本转语音功能的测试
"""

from .test_speech_to_text import TestSpeechToText
from .test_text_to_speech import TestTextToSpeech

__all__ = ['TestSpeechToText', 'TestTextToSpeech']# 音频测试初始化文件
