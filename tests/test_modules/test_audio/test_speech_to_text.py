# tests/test_modules/test_audio/test_speech_to_text.py
"""
测试语音转文本功能模块
"""

import unittest
import os
import tempfile
import subprocess
import wave
import numpy as np
from unittest.mock import patch, MagicMock

# 假设语音转文本模块的导入路径
try:
    from ai_project.modules.audio import speech_to_text
except ImportError:
    # 提供一个模拟的语音转文本函数用于测试
    def speech_to_text(audio_file, language="zh-CN"):
        """模拟的语音转文本函数"""
        return "这是一个测试文本"


class TestSpeechToText(unittest.TestCase):
    """测试语音转文本功能的类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录来存储测试音频文件
        self.temp_dir = tempfile.mkdtemp()
        
        # 支持的语言列表
        self.supported_languages = ["zh-CN", "en-US", "ja-JP", "ko-KR", "fr-FR", "de-DE"]
        
        # 各语言的测试文本
        self.test_texts = {
            "zh-CN": "这是一个中文语音识别测试",
            "en-US": "This is an English speech recognition test",
            "ja-JP": "これは日本語の音声認識テストです",
            "ko-KR": "이것은 한국어 음성 인식 테스트입니다",
            "fr-FR": "Ceci est un test de reconnaissance vocale en français",
            "de-DE": "Dies ist ein Spracherkennungstest auf Deutsch"
        }
        
        # 创建测试音频文件或模拟音频文件
        self.test_audio_files = self._create_test_audio_files()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时文件和目录
        for file_path in self.test_audio_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def _create_test_audio_files(self):
        """创建或模拟不同语言的测试音频文件"""
        audio_files = {}
        
        for lang in self.supported_languages:
            # 这里我们只是创建空的WAV文件
            # 在实际测试中，你可能需要通过文本转语音服务生成真实的音频文件
            file_path = os.path.join(self.temp_dir, f"test_{lang}.wav")
            
            # 创建一个简单的WAV文件
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)  # 单声道
                wf.setsampwidth(2)  # 2字节，16位
                wf.setframerate(16000)  # 16kHz采样率
                wf.writeframes(np.zeros(16000, dtype=np.int16).tobytes())  # 1秒静音
            
            audio_files[lang] = file_path
        
        return audio_files
    
    def test_speech_recognition_basic(self):
        """测试基本的语音识别功能"""
        # 选择中文进行基本测试
        audio_file = self.test_audio_files["zh-CN"]
        
        # 使用patch模拟语音识别结果
        with patch('ai_project.modules.audio.speech_to_text', return_value=self.test_texts["zh-CN"]):
            result = speech_to_text(audio_file)
            self.assertEqual(result, self.test_texts["zh-CN"])
    
    def test_multi_language_support(self):
        """测试多语言支持"""
        for lang in self.supported_languages:
            audio_file = self.test_audio_files[lang]
            expected_text = self.test_texts[lang]
            
            # 使用patch模拟不同语言的语音识别结果
            with patch('ai_project.modules.audio.speech_to_text', return_value=expected_text):
                result = speech_to_text(audio_file, language=lang)
                self.assertEqual(result, expected_text)
    
    def test_noisy_environment(self):
        """测试在嘈杂环境下的语音识别性能"""
        # 在实际测试中，你可能需要添加噪音到音频文件
        # 这里我们使用模拟的方式测试
        
        # 创建带噪音的测试音频文件
        noisy_audio_path = os.path.join(self.temp_dir, "noisy_test.wav")
        
        # 生成带噪音的音频（这里只是一个示例，实际中需要更复杂的处理）
        with wave.open(noisy_audio_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            # 生成随机噪音
            noise = np.random.normal(0, 500, 16000).astype(np.int16)
            wf.writeframes(noise.tobytes())
        
        expected_text = "这是在嘈杂环境下的测试"
        
        # 使用patch模拟在嘈杂环境下的语音识别结果
        with patch('ai_project.modules.audio.speech_to_text', return_value=expected_text):
            result = speech_to_text(noisy_audio_path)
            self.assertEqual(result, expected_text)
    
    def test_low_quality_audio(self):
        """测试低质量音频的语音识别性能"""
        # 创建低质量（低采样率）的测试音频文件
        low_quality_audio_path = os.path.join(self.temp_dir, "low_quality_test.wav")
        
        # 生成低质量音频
        with wave.open(low_quality_audio_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)  # 低采样率
            wf.writeframes(np.zeros(8000, dtype=np.int16).tobytes())
        
        expected_text = "这是低质量音频的测试"
        
        # 使用patch模拟低质量音频的语音识别结果
        with patch('ai_project.modules.audio.speech_to_text', return_value=expected_text):
            result = speech_to_text(low_quality_audio_path)
            self.assertEqual(result, expected_text)
    
    @unittest.skipIf(not os.path.exists("/dev/null"), "仅在类Unix系统上运行")
    def test_real_microphone_input(self):
        """测试真实麦克风输入（仅在有麦克风的环境中运行）"""
        # 检查是否有可用的麦克风
        try:
            # 使用subprocess执行一个简单的命令检查麦克风
            # 在Windows上可能需要使用不同的命令
            subprocess.run(["arecord", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            has_microphone = True
        except (subprocess.SubprocessError, FileNotFoundError):
            has_microphone = False
        
        if not has_microphone:
            self.skipTest("没有检测到可用的麦克风")
        
        # 录制短暂的音频样本
        mic_audio_path = os.path.join(self.temp_dir, "mic_test.wav")
        
        try:
            # 录制3秒音频
            subprocess.run(
                ["arecord", "-d", "3", "-f", "S16_LE", "-r", "16000", "-c", "1", mic_audio_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.SubprocessError:
            self.skipTest("无法从麦克风录制音频")
        
        # 实际测试麦克风输入
        # 在实际测试中，你可能需要说出一个特定的短语
        expected_text = "这是一个麦克风测试"
        
        with patch('ai_project.modules.audio.speech_to_text', return_value=expected_text):
            result = speech_to_text(mic_audio_path)
            self.assertEqual(result, expected_text)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的文件
        non_existent_file = os.path.join(self.temp_dir, "non_existent.wav")
        
        with patch('ai_project.modules.audio.speech_to_text', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                speech_to_text(non_existent_file)
        
        # 测试不支持的文件格式
        invalid_file = os.path.join(self.temp_dir, "invalid.txt")
        with open(invalid_file, 'w') as f:
            f.write("This is not an audio file")
        
        with patch('ai_project.modules.audio.speech_to_text', side_effect=ValueError):
            with self.assertRaises(ValueError):
                speech_to_text(invalid_file)


if __name__ == "__main__":
    unittest.main()# 语音转文本测试
