# -*- coding: utf-8 -*-
"""
音频模块: 语音转文本
功能描述: 提供语音识别和转录功能，支持多种识别引擎
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

import os
import io
import wave
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO
from dataclasses import dataclass

# 尝试导入可选依赖
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# 从配置加载器获取配置
try:
    from ...config.config_loader import ConfigLoader
    config_loader = ConfigLoader()
    STT_CONFIG = config_loader.load("modules.audio.speech_to_text")
except ImportError:
    STT_CONFIG = {
        "default_language": "en-US",
        "default_model": "default",
        "timeout": 30
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)

@dataclass
class SpeechRecognitionConfig:
    """语音识别配置类"""
    
    engine: str = "system"  # 识别引擎: system, google, sphinx, wit, azure, whisper
    language: str = "en-US"  # 语言代码
    model: str = "default"  # 模型名称
    timeout: int = 30  # 超时时间(秒)
    api_key: Optional[str] = None  # API密钥
    endpoint: Optional[str] = None  # 服务端点
    sensitivity: float = 0.5  # 灵敏度
    show_all: bool = False  # 是否返回所有候选结果
    
    def __post_init__(self):
        """数据校验和默认值设置"""
        supported_engines = ["system", "google", "sphinx", "wit", "azure", "whisper"]
        if self.engine not in supported_engines:
            logger.warning(f"不支持的识别引擎: {self.engine}，使用默认引擎: system")
            self.engine = "system"
        
        # 确保超时为正整数
        if self.timeout <= 0:
            logger.warning(f"无效的超时时间: {self.timeout}，使用默认值: 30")
            self.timeout = 30
        
        # 如果使用第三方服务但未提供API密钥，尝试从环境变量获取
        if self.engine in ["google", "wit", "azure"] and not self.api_key:
            env_var = f"{self.engine.upper()}_API_KEY"
            self.api_key = os.environ.get(env_var)
            if not self.api_key:
                logger.warning(f"未提供{self.engine}的API密钥，可能无法正常使用该服务")


class SpeechToText:
    """语音转文本类"""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], SpeechRecognitionConfig]] = None):
        """
        初始化语音识别器
        
        参数:
            config: 识别配置，可以是SpeechRecognitionConfig实例或字典
        """
        if config is None:
            self.config = SpeechRecognitionConfig(**STT_CONFIG)
        elif isinstance(config, dict):
            self.config = SpeechRecognitionConfig(**config)
        else:
            self.config = config
        
        # 检查依赖可用性
        if not SR_AVAILABLE:
            logger.warning("speech_recognition库未安装，语音识别功能将受限")
        
        # 初始化识别器
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        
        # 设置引擎特定参数
        self._setup_engine()
        
        logger.info(f"语音识别器初始化，引擎: {self.config.engine}, 语言: {self.config.language}")
    
    def _setup_engine(self):
        """设置识别引擎特定参数"""
        if not SR_AVAILABLE:
            return
        
        # 根据引擎类型设置参数
        if self.config.engine == "sphinx":
            # 设置CMU Sphinx引擎参数
            self.recognizer.energy_threshold = 300  # 能量阈值
            self.recognizer.dynamic_energy_threshold = True  # 动态能量阈值
            self.recognizer.pause_threshold = 0.8  # 暂停阈值
        
        elif self.config.engine == "google":
            # Google Cloud Speech API不需要额外设置
            pass
        
        elif self.config.engine == "wit":
            # Wit.ai不需要额外设置
            pass
        
        elif self.config.engine == "azure":
            # Microsoft Azure Speech不需要额外设置
            pass
        
        elif self.config.engine == "whisper":
            # OpenAI Whisper不需要额外设置
            pass
        
        else:  # system - 使用系统默认识别器
            # 根据操作系统选择不同的默认识别器
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                self.config.engine = "sphinx"  # 使用CMU Sphinx作为默认
            elif system == "Windows":
                self.config.engine = "google"  # 使用Google Speech Recognition作为默认
            else:  # Linux或其他
                self.config.engine = "sphinx"  # 使用CMU Sphinx作为默认
            
            logger.info(f"使用{self.config.engine}作为系统默认识别引擎")
    
    def recognize_file(self, 
                      audio_file: Union[str, Path, BinaryIO],
                      language: Optional[str] = None) -> Dict[str, Any]:
        """
        识别音频文件中的语音
        
        参数:
            audio_file: 音频文件路径或文件对象
            language: 语言代码，如果为None则使用配置中的默认值
            
        返回:
            包含识别结果的字典，包括文本、置信度等信息
        """
        if not SR_AVAILABLE or self.recognizer is None:
            logger.error("speech_recognition库未安装，无法执行语音识别")
            return {"error": "speech_recognition库未安装", "text": "", "success": False}
        
        try:
            # 处理语言参数
            if language is None:
                language = self.config.language
            
            # 加载音频文件
            audio_data = self._load_audio(audio_file)
            if audio_data is None:
                return {"error": "无法加载音频文件", "text": "", "success": False}
            
            # 执行语音识别
            return self._perform_recognition(audio_data, language)
        
        except Exception as e:
            logger.error(f"识别音频文件失败: {str(e)}")
            return {"error": str(e), "text": "", "success": False}
    
    def recognize_bytes(self, 
                       audio_bytes: bytes,
                       sample_rate: int = 16000,
                       sample_width: int = 2,
                       channels: int = 1,
                       language: Optional[str] = None) -> Dict[str, Any]:
        """
        识别音频字节数据中的语音
        
        参数:
            audio_bytes: 音频字节数据
            sample_rate: 采样率
            sample_width: 样本宽度（字节数）
            channels: 通道数
            language: 语言代码，如果为None则使用配置中的默认值
            
        返回:
            包含识别结果的字典
        """
        if not SR_AVAILABLE or self.recognizer is None:
            logger.error("speech_recognition库未安装，无法执行语音识别")
            return {"error": "speech_recognition库未安装", "text": "", "success": False}
        
        try:
            # 处理语言参数
            if language is None:
                language = self.config.language
            
            # 将原始音频转换为WAV格式
            with io.BytesIO() as wav_io:
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_bytes)
                
                wav_io.seek(0)
                audio_data = sr.AudioData(
                    wav_io.read(),
                    sample_rate=sample_rate,
                    sample_width=sample_width
                )
            
            # 执行语音识别
            return self._perform_recognition(audio_data, language)
        
        except Exception as e:
            logger.error(f"识别音频字节数据失败: {str(e)}")
            return {"error": str(e), "text": "", "success": False}
    
    def recognize_microphone(self, 
                            duration: Optional[int] = None,
                            language: Optional[str] = None,
                            adjust_for_ambient_noise: bool = True) -> Dict[str, Any]:
        """
        通过麦克风识别语音
        
        参数:
            duration: 录音持续时间（秒），如果为None则一直录制直到静音
            language: 语言代码，如果为None则使用配置中的默认值
            adjust_for_ambient_noise: 是否调整环境噪音
            
        返回:
            包含识别结果的字典
        """
        if not SR_AVAILABLE or self.recognizer is None:
            logger.error("speech_recognition库未安装，无法执行语音识别")
            return {"error": "speech_recognition库未安装", "text": "", "success": False}
        
        try:
            # 处理语言参数
            if language is None:
                language = self.config.language
            
            # 初始化麦克风
            microphone = sr.Microphone()
            
            with microphone as source:
                logger.info("正在初始化麦克风...")
                
                # 调整环境噪音
                if adjust_for_ambient_noise:
                    logger.info("调整环境噪音...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("开始录音...")
                if duration is not None:
                    audio_data = self.recognizer.record(source, duration=duration)
                    logger.info(f"录音完成，持续时间: {duration}秒")
                else:
                    audio_data = self.recognizer.listen(source, timeout=self.config.timeout)
                    logger.info("录音完成")
            
            # 执行语音识别
            return self._perform_recognition(audio_data, language)
        
        except Exception as e:
            logger.error(f"麦克风录音或识别失败: {str(e)}")
            return {"error": str(e), "text": "", "success": False}
    
    def _load_audio(self, audio_file: Union[str, Path, BinaryIO]) -> Optional[sr.AudioData]:
        """
        加载音频文件
        
        参数:
            audio_file: 音频文件路径或文件对象
            
        返回:
            AudioData对象，如果加载失败则返回None
        """
        try:
            # 处理不同类型的输入
            if isinstance(audio_file, (str, Path)):
                # 文件路径
                with sr.AudioFile(str(audio_file)) as source:
                    return self.recognizer.record(source)
            
            elif hasattr(audio_file, 'read') and callable(audio_file.read):
                # 文件对象
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_file.write(audio_file.read())
                temp_file.close()
                
                try:
                    with sr.AudioFile(temp_file.name) as source:
                        audio_data = self.recognizer.record(source)
                finally:
                    # 删除临时文件
                    os.unlink(temp_file.name)
                
                return audio_data
            
            else:
                logger.error(f"不支持的音频文件类型: {type(audio_file)}")
                return None
        
        except Exception as e:
            logger.error(f"加载音频文件失败: {str(e)}")
            return None
    
    def _perform_recognition(self, 
                           audio_data: sr.AudioData, 
                           language: str) -> Dict[str, Any]:
        """
        执行语音识别
        
        参数:
            audio_data: 音频数据
            language: 语言代码
            
        返回:
            包含识别结果的字典
        """
        try:
            text = ""
            details = {}
            
            # 根据引擎执行识别
            if self.config.engine == "sphinx":
                # 使用CMU Sphinx引擎
                try:
                    text = self.recognizer.recognize_sphinx(
                        audio_data,
                        language=language,
                        show_all=self.config.show_all
                    )
                    
                    if self.config.show_all and not isinstance(text, str):
                        # 如果 show_all=True，则返回的是包含多个候选结果的对象
                        details = {"alternatives": text}
                        text = text.hypstr if hasattr(text, 'hypstr') else ""
                
                except sr.UnknownValueError:
                    return {"error": "无法识别语音", "text": "", "success": False}
            
            elif self.config.engine == "google":
                # 使用Google Cloud Speech API
                try:
                    text = self.recognizer.recognize_google(
                        audio_data,
                        language=language,
                        key=self.config.api_key,
                        show_all=self.config.show_all
                    )
                    
                    if self.config.show_all and not isinstance(text, str):
                        # 提取所有候选结果
                        if isinstance(text, dict) and 'alternative' in text:
                            details = {"alternatives": text['alternative']}
                            text = text['alternative'][0]['transcript'] if text['alternative'] else ""
                
                except sr.UnknownValueError:
                    return {"error": "无法识别语音", "text": "", "success": False}
            
            elif self.config.engine == "wit":
                # 使用Wit.ai API
                if not self.config.api_key:
                    return {"error": "未提供Wit.ai API密钥", "text": "", "success": False}
                
                try:
                    text = self.recognizer.recognize_wit(
                        audio_data,
                        key=self.config.api_key,
                        show_all=self.config.show_all
                    )
                    
                    if self.config.show_all and not isinstance(text, str):
                        details = {"wit_response": text}
                        # 尝试从Wit.ai响应中提取文本
                        if isinstance(text, dict) and '_text' in text:
                            text = text['_text']
                        elif isinstance(text, dict) and 'text' in text:
                            text = text['text']
                        else:
                            text = ""
                
                except sr.UnknownValueError:
                    return {"error": "无法识别语音", "text": "", "success": False}
            
            elif self.config.engine == "azure":
                # 使用Microsoft Azure Speech
                if not self.config.api_key:
                    return {"error": "未提供Azure API密钥", "text": "", "success": False}
                
                try:
                    # Azure需要服务区域
                    region = self.config.endpoint or "westus"
                    
                    text = self.recognizer.recognize_azure(
                        audio_data,
                        key=self.config.api_key,
                        location=region,
                        language=language,
                        show_all=self.config.show_all
                    )
                    
                    if self.config.show_all and not isinstance(text, str):
                        details = {"azure_response": text}
                        # 尝试从Azure响应中提取文本
                        if isinstance(text, dict) and 'DisplayText' in text:
                            text = text['DisplayText']
                        else:
                            text = ""
                
                except sr.UnknownValueError:
                    return {"error": "无法识别语音", "text": "", "success": False}
            
            elif self.config.engine == "whisper":
                # 使用OpenAI Whisper
                try:
                    import whisper
                except ImportError:
                    return {"error": "Whisper库未安装", "text": "", "success": False}
                
                try:
                    # 将AudioData转换为临时wav文件
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    temp_file.write(audio_data.get_wav_data())
                    temp_file.close()
                    
                    try:
                        # 加载Whisper模型
                        model_name = self.config.model if self.config.model != "default" else "tiny"
                        model = whisper.load_model(model_name)
                        
                        # 执行转录
                        result = model.transcribe(
                            temp_file.name,
                            language=language[:2] if language else None,
                            verbose=False
                        )
                        
                        text = result["text"]
                        details = {"whisper_response": result}
                    
                    finally:
                        # 删除临时文件
                        os.unlink(temp_file.name)
                
                except Exception as e:
                    return {"error": f"Whisper识别失败: {str(e)}", "text": "", "success": False}
            
            else:
                return {"error": f"不支持的识别引擎: {self.config.engine}", "text": "", "success": False}
            
            # 返回识别结果
            result = {
                "text": text,
                "engine": self.config.engine,
                "language": language,
                "success": True
            }
            
            # 如果有其他细节，添加到结果中
            if details:
                result["details"] = details
            
            return result
        
        except Exception as e:
            logger.error(f"执行语音识别失败: {str(e)}")
            return {"error": str(e), "text": "", "success": False}
    
    def is_available(self) -> bool:
        """
        检查语音识别是否可用
        
        返回:
            布尔值，表示是否可用
        """
        return SR_AVAILABLE and self.recognizer is not None


# 辅助函数

def list_available_microphones() -> Dict[int, str]:
    """
    列出可用的麦克风设备
    
    返回:
        麦克风索引到名称的映射字典
    """
    if not SR_AVAILABLE:
        logger.error("speech_recognition库未安装，无法列出麦克风")
        return {}
    
    try:
        import pyaudio
        
        pa = pyaudio.PyAudio()
        devices = {}
        
        for i in range(pa.get_device_count()):
            device_info = pa.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # 输入设备
                devices[i] = device_info['name']
        
        pa.terminate()
        return devices
    
    except ImportError:
        logger.error("pyaudio库未安装，无法列出麦克风")
        return {}
    
    except Exception as e:
        logger.error(f"列出麦克风失败: {str(e)}")
        return {}


def convert_audio_format(input_file: str, 
                        output_file: str,
                        output_format: str = "wav",
                        sample_rate: int = 16000,
                        channels: int = 1,
                        bit_depth: int = 16) -> bool:
    """
    转换音频文件格式
    
    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径
        output_format: 输出格式，如 'wav', 'mp3', 'flac' 等
        sample_rate: 采样率
        channels: 通道数
        bit_depth: 位深度
        
    返回:
        是否成功转换
    """
    try:
        # 尝试使用 pydub
        from pydub import AudioSegment
        
        # 加载音频文件
        audio = AudioSegment.from_file(input_file)
        
        # 设置参数
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_channels(channels)
        audio = audio.set_sample_width(bit_depth // 8)
        
        # 导出文件
        audio.export(output_file, format=output_format)
        
        logger.info(f"成功转换音频文件: {input_file} -> {output_file}")
        return True
    
    except ImportError:
        logger.error("pydub库未安装，无法转换音频格式")
        return False
    
    except Exception as e:
        logger.error(f"转换音频格式失败: {str(e)}")
        return False


def transcribe_long_audio(audio_file: str, 
                         config: Optional[SpeechRecognitionConfig] = None,
                         segment_duration: int = 60,
                         overlap: int = 5) -> Dict[str, Any]:
    """
    转录长音频文件，通过分段处理
    
    参数:
        audio_file: 音频文件路径
        config: 识别配置
        segment_duration: 每段的持续时间（秒）
        overlap: 重叠部分的持续时间（秒）
        
    返回:
        包含转录结果的字典
    """
    try:
        # 尝试使用 pydub 加载音频
        from pydub import AudioSegment
        
        # 加载音频文件
        audio = AudioSegment.from_file(audio_file)
        
        # 创建识别器
        recognizer = SpeechToText(config)
        
        if not recognizer.is_available():
            return {"error": "语音识别不可用", "text": "", "success": False}
        
        # 计算分段
        audio_duration = len(audio) / 1000.0  # 毫秒转秒
        segments = []
        
        # 创建分段
        start_time = 0
        while start_time < audio_duration:
            end_time = min(start_time + segment_duration, audio_duration)
            segments.append((start_time, end_time))
            start_time = end_time - overlap
        
        logger.info(f"将音频分成 {len(segments)} 段处理")
        
        # 处理每一段
        results = []
        
        for i, (start, end) in enumerate(segments):
            logger.info(f"处理音频段 {i+1}/{len(segments)}: {start:.1f}s - {end:.1f}s")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # 提取音频段
                segment = audio[int(start * 1000):int(end * 1000)]
                segment.export(temp_file.name, format='wav')
                
                # 识别
                try:
                    result = recognizer.recognize_file(temp_file.name)
                    if result["success"]:
                        results.append(result["text"])
                finally:
                    # 删除临时文件
                    os.unlink(temp_file.name)
        
        # 合并结果
        full_text = " ".join(results)
        
        return {
            "text": full_text,
            "segments": len(segments),
            "audio_duration": audio_duration,
            "success": True
        }
    
    except ImportError:
        logger.error("pydub库未安装，无法处理长音频")
        return {"error": "pydub库未安装", "text": "", "success": False}
    
    except Exception as e:
        logger.error(f"处理长音频失败: {str(e)}")
        return {"error": str(e), "text": "", "success": False}