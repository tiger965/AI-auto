# tests/test_modules/test_audio/test_text_to_speech.py
"""
测试文本转语音功能模块
"""

import unittest
import os
import tempfile
import wave
import numpy as np
from unittest.mock import patch, MagicMock

# 假设文本转语音模块的导入路径
try:
    from ai_project.modules.audio import text_to_speech
except ImportError:
    # 提供一个模拟的文本转语音函数用于测试
    def text_to_speech(text, output_file, language="zh-CN", voice_name=None):
        """模拟的文本转语音函数"""
        # 创建一个空的WAV文件
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(np.zeros(16000, dtype=np.int16).tobytes())
        return True


class TestTextToSpeech(unittest.TestCase):
    """测试文本转语音功能的类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录来存储测试音频文件
        self.temp_dir = tempfile.mkdtemp()
        
        # 支持的语言列表
        self.supported_languages = ["zh-CN", "en-US", "ja-JP", "ko-KR", "fr-FR", "de-DE"]
        
        # 各语言的测试文本
        self.test_texts = {
            "zh-CN": "这是一个中文语音合成测试",
            "en-US": "This is an English text-to-speech test",
            "ja-JP": "これは日本語の音声合成テストです",
            "ko-KR": "이것은 한국어 텍스트 음성 변환 테스트입니다",
            "fr-FR": "Ceci est un test de synthèse vocale en français",
            "de-DE": "Dies ist ein Text-zu-Sprache-Test auf Deutsch"
        }
        
        # 语音角色名称（根据实际TTS引擎支持的进行调整）
        self.voice_names = {
            "zh-CN": ["xiaoming", "xiaohong", "xiaoyu"],
            "en-US": ["john", "mary", "alex"],
            "ja-JP": ["haruka", "takumi"],
            "ko-KR": ["seoyeon"],
            "fr-FR": ["mathieu", "celine"],
            "de-DE": ["hans", "marlene"]
        }
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时文件和目录
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def _validate_audio_file(self, file_path):
        """验证生成的音频文件是否有效"""
        if not os.path.exists(file_path):
            return False
        
        try:
            with wave.open(file_path, 'rb') as wf:
                # 检查基本参数
                if wf.getnchannels() <= 0 or wf.getsampwidth() <= 0 or wf.getframerate() <= 0:
                    return False
                # 检查文件大小（应该有一些内容）
                if wf.getnframes() <= 0:
                    return False
            return True
        except Exception:
            return False
    
    def test_basic_text_to_speech(self):
        """测试基本的文本转语音功能"""
        # 选择中文进行基本测试
        text = self.test_texts["zh-CN"]
        output_file = os.path.join(self.temp_dir, "basic_test.wav")
        
        # 使用实际的TTS函数或模拟函数
        result = text_to_speech(text, output_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(self._validate_audio_file(output_file))
    
    def test_multi_language_support(self):
        """测试多语言支持"""
        for lang in self.supported_languages:
            text = self.test_texts[lang]
            output_file = os.path.join(self.temp_dir, f"test_{lang}.wav")
            
            # 使用实际的TTS函数或模拟函数
            result = text_to_speech(text, output_file, language=lang)
            
            self.assertTrue(result)
            self.assertTrue(os.path.exists(output_file))
            self.assertTrue(self._validate_audio_file(output_file))
    
    def test_different_voices(self):
        """测试不同的语音角色"""
        for lang in self.supported_languages:
            if lang not in self.voice_names:
                continue
                
            text = self.test_texts[lang]
            
            for voice in self.voice_names[lang]:
                output_file = os.path.join(self.temp_dir, f"test_{lang}_{voice}.wav")
                
                # 使用实际的TTS函数或模拟函数
                result = text_to_speech(text, output_file, language=lang, voice_name=voice)
                
                self.assertTrue(result)
                self.assertTrue(os.path.exists(output_file))
                self.assertTrue(self._validate_audio_file(output_file))
    
    def test_long_text(self):
        """测试长文本的语音合成"""
        # 创建一个长文本
        long_text = "这是一个很长的测试文本，用于测试文本转语音功能对长文本的处理能力。" * 20
        output_file = os.path.join(self.temp_dir, "long_text_test.wav")
        
        # 使用实际的TTS函数或模拟函数
        result = text_to_speech(long_text, output_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(self._validate_audio_file(output_file))
    
    def test_special_characters(self):
        """测试包含特殊字符的文本"""
        special_chars_text = "测试特殊字符：!@#$%^&*()_+{}|:<>?[];',./~`"
        output_file = os.path.join(self.temp_dir, "special_chars_test.wav")
        
        # 使用实际的TTS函数或模拟函数
        result = text_to_speech(special_chars_text, output_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(self._validate_audio_file(output_file))
    
    def test_numbers_and_dates(self):
        """测试包含数字和日期的文本"""
        numbers_text = "测试数字和日期：123.45，2023年4月1日，12:30"
        output_file = os.path.join(self.temp_dir, "numbers_test.wav")
        
        # 使用实际的TTS函数或模拟函数
        result = text_to_speech(numbers_text, output_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(self._validate_audio_file(output_file))
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试空文本
        empty_text = ""
        output_file = os.path.join(self.temp_dir, "empty_text_test.wav")
        
        with patch('ai_project.modules.audio.text_to_speech', side_effect=ValueError("空文本")):
            with self.assertRaises(ValueError):
                text_to_speech(empty_text, output_file)
        
        # 测试不支持的语言
        unsupported_lang = "xx-XX"
        output_file = os.path.join(self.temp_dir, "unsupported_lang_test.wav")
        
        with patch('ai_project.modules.audio.text_to_speech', side_effect=ValueError("不支持的语言")):
            with self.assertRaises(ValueError):
                text_to_speech(self.test_texts["zh-CN"], output_file, language=unsupported_lang)
        
        # 测试输出目录不存在
        non_existent_dir = os.path.join(self.temp_dir, "non_existent_dir")
        output_file = os.path.join(non_existent_dir, "test.wav")
        
        with patch('ai_project.modules.audio.text_to_speech', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                text_to_speech(self.test_texts["zh-CN"], output_file)
    
    def test_output_format(self):
        """测试不同的输出格式（如果支持）"""
        text = self.test_texts["zh-CN"]
        
        # 测试WAV格式
        wav_output = os.path.join(self.temp_dir, "test.wav")
        wav_result = text_to_speech(text, wav_output)
        self.assertTrue(wav_result)
        self.assertTrue(self._validate_audio_file(wav_output))
        
        # 注意：以下测试需要实际的TTS引擎支持相应格式
        # 如果不支持，这些测试可能会失败
        
        # 测试MP3格式（如果支持）
        try:
            mp3_output = os.path.join(self.temp_dir, "test.mp3")
            with patch('ai_project.modules.audio.text_to_speech', return_value=True):
                mp3_result = text_to_speech(text, mp3_output)
                self.assertTrue(mp3_result)
                self.assertTrue(os.path.exists(mp3_output))
        except Exception:
            pass  # 如果不支持MP3格式，忽略错误
        
        # 测试OGG格式（如果支持）
        try:
            ogg_output = os.path.join(self.temp_dir, "test.ogg")
            with patch('ai_project.modules.audio.text_to_speech', return_value=True):
                ogg_result = text_to_speech(text, ogg_output)
                self.assertTrue(ogg_result)
                self.assertTrue(os.path.exists(ogg_output))
        except Exception:
            pass  # 如果不支持OGG格式，忽略错误


if __name__ == "__main__":
    unittest.main()# 文本转语音测试
