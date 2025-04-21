
# 添加项目根目录到Python路径
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿  # tests/test_modules/test_audio/__init__.py
""""
音频模块测试包
包含语音转文本和文本转语音功能的测试
""""

from .test_speech_to_text import TestSpeechToText
from .test_text_to_speech import TestTextToSpeech

__all__ = ['TestSpeechToText', 'TestTextToSpeech']# 音频测试初始化文件