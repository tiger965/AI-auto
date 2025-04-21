# -*- coding: utf-8 -*-
"""
音频模块: 文本转语音
功能描述: 提供文本转语音功能，支持多种合成引擎
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

from .. config.config_loader import ConfigLoader
import ui.utils.color
import os
import io
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO
from dataclasses import dataclass

# 尝试导入可选依赖
try:
import config.paths
from config.paths import gTTS
GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# 从配置加载器获取配置
try:
config_loader = ConfigLoader()
TTS_CONFIG = config_loader.load("modules.audio.text_to_speech")
except ImportError:
    TTS_CONFIG = {
        "default_voice": "default",
        "default_language": "en-US",
        "audio_format": "wav"
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)


@dataclass
class SpeechSynthesisConfig:
    """语音合成配置类"""

    engine: str = "system"  # 合成引擎: system, gtts, pyttsx3, azure, aws
    voice: str = "default"  # 语音名称
    language: str = "en-US"  # 语言代码
    gender: str = "neutral"  # 性别: male, female, neutral
    rate: float = 1.0  # 语速因子，1.0表示正常速度
    pitch: float = 1.0  # 音高因子，1.0表示正常音高
    volume: float = 1.0  # 音量因子，1.0表示正常音量
    audio_format: str = "wav"  # 音频格式: wav, mp3, ogg
    api_key: Optional[str] = None  # API密钥
    endpoint: Optional[str] = None  # 服务端点

    def __post_init__(self):
        """数据校验和默认值设置"""
        supported_engines = ["system", "gtts", "pyttsx3", "azure", "aws"]
        if self.engine not in supported_engines:
            logger.warning(f"不支持的合成引擎: {self.engine}，使用默认引擎: system")
            self.engine = "system"

        supported_formats = ["wav", "mp3", "ogg"]
        if self.audio_format not in supported_formats:
            logger.warning(f"不支持的音频格式: {self.audio_format}，使用默认格式: wav")
            self.audio_format = "wav"

        # 确保语速、音高和音量为正数
        if self.rate <= 0:
            logger.warning(f"无效的语速: {self.rate}，使用默认值: 1.0")
            self.rate = 1.0

        if self.pitch <= 0:
            logger.warning(f"无效的音高: {self.pitch}，使用默认值: 1.0")
            self.pitch = 1.0

        if self.volume <= 0:
            logger.warning(f"无效的音量: {self.volume}，使用默认值: 1.0")
            self.volume = 1.0

        # 如果使用第三方服务但未提供API密钥，尝试从环境变量获取
        if self.engine in ["azure", "aws"] and not self.api_key:
            env_var = f"{self.engine.upper()}_API_KEY"
            self.api_key = os.environ.get(env_var)
            if not self.api_key:
                logger.warning(f"未提供{self.engine}的API密钥，可能无法正常使用该服务")


class TextToSpeech:
    """文本转语音类"""

    def __init__(self, config: Optional[Union[Dict[str, Any], SpeechSynthesisConfig]] = None):
        """
        初始化语音合成器

        参数:
            config: 合成配置，可以是SpeechSynthesisConfig实例或字典
        """
        if config is None:
            self.config = SpeechSynthesisConfig(**TTS_CONFIG)
        elif isinstance(config, dict):
            self.config = SpeechSynthesisConfig(**config)
        else:
            self.config = config

        # 检查依赖可用性
        if not GTTS_AVAILABLE and not PYTTSX3_AVAILABLE:
            logger.warning("gTTS和pyttsx3库都未安装，文本转语音功能将受限")

        # 初始化合成引擎
        self.engine = None
        self._setup_engine()

        logger.info(
            f"语音合成器初始化，引擎: {self.config.engine}, 语言: {self.config.language}")

    def _setup_engine(self):
        """设置合成引擎"""
        if self.config.engine == "gtts":
            if not GTTS_AVAILABLE:
                logger.warning("gTTS库未安装，回退到系统引擎")
                self.config.engine = "system"
            # gTTS不需要预先初始化

        elif self.config.engine == "pyttsx3":
            if not PYTTSX3_AVAILABLE:
                logger.warning("pyttsx3库未安装，回退到系统引擎")
                self.config.engine = "system"
            else:
                # 初始化pyttsx3引擎
                try:
                    self.engine = pyttsx3.init()

                    # 设置属性
                    self.engine.setProperty('rate', int(
                        self.engine.getProperty('rate') * self.config.rate))

                    # 设置声音
                    voices = self.engine.getProperty('voices')
                    if voices:
                        # 根据性别选择声音
                        if self.config.gender == "male":
                            male_voices = [
                                v for v in voices if "male" in v.gender.lower()]
                            if male_voices:
                                self.engine.setProperty(
                                    'voice', male_voices[0].id)
                        elif self.config.gender == "female":
                            female_voices = [
                                v for v in voices if "female" in v.gender.lower()]
                            if female_voices:
                                self.engine.setProperty(
                                    'voice', female_voices[0].id)

                        # 如果指定了特定的声音
                        if self.config.voice != "default":
                            for voice in voices:
                                if self.config.voice.lower() in voice.name.lower() or self.config.voice == voice.id:
                                    self.engine.setProperty('voice', voice.id)
                                    break
                except Exception as e:
                    logger.error(f"初始化pyttsx3引擎失败: {str(e)}")
                    self.config.engine = "system"
                    self.engine = None

        elif self.config.engine == "azure":
            try:
                import azure.cognitiveservices.speech as speechsdk

                # 检查API密钥和端点
                if not self.config.api_key or not self.config.endpoint:
                    logger.warning("未提供Azure语音服务的API密钥或端点，回退到系统引擎")
                    self.config.engine = "system"
                else:
                    # 初始化Azure语音配置
                    speech_config = speechsdk.SpeechConfig(
                        subscription=self.config.api_key,
                        region=self.config.endpoint
                    )

                    # 设置语音和语言
                    speech_config.speech_synthesis_language = self.config.language

                    if self.config.voice != "default":
                        speech_config.speech_synthesis_voice_name = self.config.voice

                    self.engine = speech_config
            except ImportError:
                logger.warning("Azure语音SDK未安装，回退到系统引擎")
                self.config.engine = "system"

        elif self.config.engine == "aws":
            try:
                
                # 检查API密钥
                if not self.config.api_key:
                    logger.warning("未提供AWS访问密钥，回退到系统引擎")
                    self.config.engine = "system"
                else:
                    # 初始化AWS Polly客户端
                    session = boto3.Session(
                        aws_access_key_id=self.config.api_key,
                        aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                        region_name=self.config.endpoint or "us-east-1"
                    )

                    self.engine = session.client("polly")
            except ImportError:
                logger.warning("boto3库未安装，回退到系统引擎")
                self.config.engine = "system"

        # 如果指定了系统引擎或者其他引擎初始化失败
        if self.config.engine == "system":
            # 根据可用性选择默认引擎
            if PYTTSX3_AVAILABLE:
                self.config.engine = "pyttsx3"
                self._setup_engine()  # 递归调用设置pyttsx3引擎
            elif GTTS_AVAILABLE:
                self.config.engine = "gtts"
                # gTTS不需要预先初始化
            else:
                logger.error("没有可用的文本转语音引擎")

    def synthesize(self,
                   text: str,
                   output_file: Optional[str] = None) -> Optional[bytes]:
        """
        合成语音
        
        参数:
            text: 要合成的文本
            output_file: 输出文件路径，如果为None则返回音频字节数据
            
        返回:
            如果output_file为None，则返回音频字节数据，否则返回None
        """
        if not text:
            logger.warning("无法合成空文本")
            return None

        try:
            # 根据引擎合成语音
            if self.config.engine == "gtts":
                return self._synthesize_gtts(text, output_file)
            elif self.config.engine == "pyttsx3":
                return self._synthesize_pyttsx3(text, output_file)
            elif self.config.engine == "azure":
                return self._synthesize_azure(text, output_file)
            elif self.config.engine == "aws":
                return self._synthesize_aws(text, output_file)
            else:
                logger.error(f"不支持的合成引擎: {self.config.engine}")
                return None

        except Exception as e:
            logger.error(f"合成语音失败: {str(e)}")
            return None

    def _synthesize_gtts(self,
                         text: str,
                         output_file: Optional[str] = None) -> Optional[bytes]:
        """
        使用gTTS引擎合成语音
        
        参数:
            text: 要合成的文本
            output_file: 输出文件路径
            
        返回:
            如果output_file为None，则返回音频字节数据，否则返回None
        """
        if not GTTS_AVAILABLE:
            logger.error("gTTS库未安装，无法合成语音")
            return None

        try:
            # 设置语言代码
            lang = self.config.language.split('-')[0]  # 只取语言部分，如'en-US'变成'en'

            # 创建gTTS对象
            tts = gTTS(text=text, lang=lang, slow=(self.config.rate < 0.8))

            # 输出到文件或内存
            if output_file:
                # 确保目录存在
                directory = os.path.dirname(output_file)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

                # 保存到文件
                tts.save(output_file)
                logger.info(f"语音已保存到: {output_file}")
                return None
            else:
                # 保存到内存
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)

                # 如果需要转换格式
                if self.config.audio_format != "mp3":
                    return self._convert_audio_format(mp3_fp.read(), "mp3", self.config.audio_format)

                return mp3_fp.read()

        except Exception as e:
            logger.error(f"gTTS合成失败: {str(e)}")
            return None

    def _synthesize_pyttsx3(self,
                            text: str,
                            output_file: Optional[str] = None) -> Optional[bytes]:
        """
        使用pyttsx3引擎合成语音
        
        参数:
            text: 要合成的文本
            output_file: 输出文件路径
            
        返回:
            如果output_file为None，则返回音频字节数据，否则返回None
        """
        if not PYTTSX3_AVAILABLE or not self.engine:
            logger.error("pyttsx3引擎未初始化，无法合成语音")
            return None

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

            # 设置属性
            self.engine.setProperty('volume', self.config.volume)

            # 添加文本
            self.engine.save_to_file(text, temp_path)

            # 执行合成
            self.engine.runAndWait()

            # 处理输出
            if output_file:
                # 确保目录存在
                directory = os.path.dirname(output_file)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

                # 如果需要转换格式
                if self.config.audio_format != "wav":
                    self._convert_audio_format_file(
                        temp_path, output_file, "wav", self.config.audio_format)
                else:
                    # 直接移动文件
                    import shutil
                    shutil.move(temp_path, output_file)

                logger.info(f"语音已保存到: {output_file}")
                return None
            else:
                # 读取临时文件
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()

                # 删除临时文件
                os.unlink(temp_path)

                # 如果需要转换格式
                if self.config.audio_format != "wav":
                    return self._convert_audio_format(audio_data, "wav", self.config.audio_format)

                return audio_data

        except Exception as e:
            logger.error(f"pyttsx3合成失败: {str(e)}")
            # 清理临时文件
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            return None

    def _synthesize_azure(self,
                          text: str,
                          output_file: Optional[str] = None) -> Optional[bytes]:
        """
        使用Azure语音服务合成语音
        
        参数:
            text: 要合成的文本
            output_file: 输出文件路径
            
        返回:
            如果output_file为None，则返回音频字节数据，否则返回None
        """
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            logger.error("Azure语音SDK未安装，无法合成语音")
            return None

        if not self.engine:
            logger.error("Azure语音配置未初始化，无法合成语音")
            return None

        try:
            # 创建语音合成器
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.engine)

            # 根据输出类型设置合成参数
            if output_file:
                # 创建音频输出配置
                audio_config = speechsdk.audio.AudioOutputConfig(
                    filename=output_file)
                speech_synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.engine,
                    audio_config=audio_config
                )

                # 合成语音
                result = speech_synthesizer.speak_text_async(text).get()

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    logger.info(f"语音已保存到: {output_file}")
                    return None
                else:
                    logger.error(f"Azure语音合成失败: {result.reason}")
                    return None
            else:
                # 合成内存中的音频
                result = speech_synthesizer.speak_text_async(text).get()

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    # 获取音频数据
                    audio_data = result.audio_data

                    # 如果需要转换格式（Azure默认返回WAV格式）
                    if self.config.audio_format != "wav":
                        return self._convert_audio_format(audio_data, "wav", self.config.audio_format)

                    return audio_data
                else:
                    logger.error(f"Azure语音合成失败: {result.reason}")
                    return None

        except Exception as e:
            logger.error(f"Azure语音合成失败: {str(e)}")
            return None

    def _synthesize_aws(self,
                        text: str,
                        output_file: Optional[str] = None) -> Optional[bytes]:
        """
        使用AWS Polly服务合成语音
        
        参数:
            text: 要合成的文本
            output_file: 输出文件路径
            
        返回:
            如果output_file为None，则返回音频字节数据，否则返回None
        """
        if not self.engine:
            logger.error("AWS Polly客户端未初始化，无法合成语音")
            return None

        try:
            # 设置Polly参数
            params = {
                "Text": text,
                "OutputFormat": "mp3" if self.config.audio_format == "mp3" else "ogg_vorbis" if self.config.audio_format == "ogg" else "pcm",
                "VoiceId": self.config.voice if self.config.voice != "default" else "Joanna",
                "SampleRate": "16000",  # 可根据需要调整
            }

            # 根据性别选择默认声音
            if self.config.voice == "default":
                if self.config.gender == "male":
                    params["VoiceId"] = "Matthew"
                elif self.config.gender == "female":
                    params["VoiceId"] = "Joanna"

            # 设置语言
            if "-" in self.config.language:
                lang_parts = self.config.language.split("-")
                params["LanguageCode"] = f"{lang_parts[0]}-{lang_parts[1].upper()}"

            # 调用Polly API
            response = self.engine.synthesize_speech(**params)

            # 处理结果
            if "AudioStream" in response:
                # 读取音频流
                audio_data = response["AudioStream"].read()

                if output_file:
                    # 确保目录存在
                    directory = os.path.dirname(output_file)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory)

                    # 保存到文件
                    with open(output_file, "wb") as f:
                        f.write(audio_data)

                    logger.info(f"语音已保存到: {output_file}")
                    return None
                else:
                    # 返回音频数据
                    return audio_data
            else:
                logger.error("AWS Polly未返回音频流")
                return None

        except Exception as e:
            logger.error(f"AWS Polly合成失败: {str(e)}")
            return None

    def _convert_audio_format(self,
                              audio_data: bytes,
                              input_format: str,
                              output_format: str) -> Optional[bytes]:
        """
        转换音频格式
        
        参数:
            audio_data: 输入音频数据
            input_format: 输入格式
            output_format: 输出格式
            
        返回:
            转换后的音频数据，如果转换失败则返回None
        """
        try:
            # 检查格式是否相同
            if input_format == output_format:
                return audio_data

            # 创建临时输入文件
            with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as temp_in:
                temp_in.write(audio_data)
                input_file = temp_in.name

            # 创建临时输出文件
            output_file = f"{input_file}.{output_format}"

            # 转换格式
            result = self._convert_audio_format_file(
                input_file, output_file, input_format, output_format)

            # 读取转换后的文件
            if result:
                with open(output_file, 'rb') as f:
                    converted_data = f.read()
            else:
                converted_data = None

            # 删除临时文件
            os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

            return converted_data

        except Exception as e:
            logger.error(f"转换音频格式失败: {str(e)}")
            # 清理临时文件
            if 'input_file' in locals():
                try:
                    os.unlink(input_file)
                except:
                    pass
            if 'output_file' in locals() and os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except:
                    pass
            return None

    def _convert_audio_format_file(self,
                                   input_file: str,
                                   output_file: str,
                                   input_format: str,
                                   output_format: str) -> bool:
        """
        转换音频文件格式
        
        参数:
            input_file: 输入文件路径
            output_file: 输出文件路径
            input_format: 输入格式
            output_format: 输出格式
            
        返回:
            是否成功转换
        """
        try:
            # 尝试使用pydub转换
            from pydub import AudioSegment

            # 加载音频
            audio = AudioSegment.from_file(input_file, format=input_format)

            # 导出为目标格式
            audio.export(output_file, format=output_format)

            return True

        except ImportError:
            logger.warning("pydub库未安装，尝试使用ffmpeg")

            try:
                # 尝试使用ffmpeg
                import subprocess

                # 构建ffmpeg命令
                cmd = ["ffmpeg", "-y", "-i", input_file, output_file]

                # 执行命令
                subprocess.run(cmd, check=True, capture_output=True)

                return True

            except Exception as e:
                logger.error(f"ffmpeg转换失败: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"pydub转换失败: {str(e)}")
            return False

    def list_available_voices(self) -> List[Dict[str, Any]]:
        """
        列出可用的语音
        
        返回:
            语音信息列表
        """
        voices = []

        try:
            if self.config.engine == "pyttsx3" and PYTTSX3_AVAILABLE and self.engine:
                # 获取pyttsx3可用的语音
                pyttsx3_voices = self.engine.getProperty('voices')

                for voice in pyttsx3_voices:
                    voices.append({
                        "id": voice.id,
                        "name": voice.name,
                        "gender": voice.gender,
                        "language": voice.languages[0] if voice.languages else "unknown",
                        "engine": "pyttsx3"
                    })

            elif self.config.engine == "azure" and self.engine:
                # Azure语音需要单独API调用获取，这里只返回一些常用语音
                common_voices = [
                    {"id": "en-US-AriaNeural", "name": "Aria",
                        "gender": "Female", "language": "en-US"},
                    {"id": "en-US-GuyNeural", "name": "Guy",
                        "gender": "Male", "language": "en-US"},
                    {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao",
                        "gender": "Female", "language": "zh-CN"},
                    {"id": "zh-CN-YunxiNeural", "name": "Yunxi",
                        "gender": "Male", "language": "zh-CN"},
                    # 可以添加更多语音
                ]

                for voice in common_voices:
                    voice["engine"] = "azure"
                    voices.append(voice)

            elif self.config.engine == "aws" and self.engine:
                # 获取AWS Polly可用的语音
                try:
                    response = self.engine.describe_voices()

                    if "Voices" in response:
                        for voice in response["Voices"]:
                            voices.append({
                                "id": voice["Id"],
                                "name": voice["Name"],
                                "gender": voice["Gender"],
                                "language": voice["LanguageCode"],
                                "engine": "aws"
                            })
                except Exception as e:
                    logger.error(f"获取AWS Polly语音列表失败: {str(e)}")

            elif self.config.engine == "gtts" and GTTS_AVAILABLE:
                # gTTS没有明确的语音列表，只有语言
                languages = gtts.lang.tts_langs()

                # 为每种语言创建默认语音
                for code, name in languages.items():
                    voices.append({
                        "id": f"gtts-{code}",
                        "name": f"gTTS {name}",
                        "gender": "neutral",
                        "language": code,
                        "engine": "gtts"
                    })

        except Exception as e:
            logger.error(f"获取可用语音列表失败: {str(e)}")

        return voices

    def is_available(self) -> bool:
        """
        检查文本转语音是否可用
        
        返回:
            布尔值，表示是否可用
        """
        if self.config.engine == "pyttsx3":
            return PYTTSX3_AVAILABLE and self.engine is not None
        elif self.config.engine == "gtts":
            return GTTS_AVAILABLE
        elif self.config.engine == "azure":
            return self.engine is not None
        elif self.config.engine == "aws":
            return self.engine is not None
        return False


# 辅助函数

def generate_ssml(text: str,
                  voice: Optional[str] = None,
                  language: Optional[str] = None,
                  rate: Optional[float] = None,
                  pitch: Optional[float] = None,
                  volume: Optional[float] = None,
                  emphasis: Optional[List[Tuple[str, str]]] = None) -> str:
    """
    生成SSML标记语言
    
    参数:
        text: 基础文本
        voice: 语音名称
        language: 语言代码
        rate: 语速因子
        pitch: 音高因子
        volume: 音量因子
        emphasis: 强调列表，每个元素为(文本, 级别)，级别可为 'strong', 'moderate', 'reduced'
        
    返回:
        SSML文本
    """
    # 基础SSML
    ssml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    ssml += '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="{}">\n'.format(
        language or "en-US")

    # 添加声音
    if voice:
        ssml += f'  <voice name="{voice}">\n'

    # 添加Prosody（韵律）
    prosody_attrs = []
    if rate is not None:
        # 将因子转换为百分比
        rate_percent = int((rate - 1.0) * 100)
        if rate_percent > 0:
            prosody_attrs.append(f'rate="+{rate_percent}%"')
        elif rate_percent < 0:
            prosody_attrs.append(f'rate="{rate_percent}%"')

    if pitch is not None:
        # 将因子转换为半音
        pitch_semitones = int((pitch - 1.0) * 12)
        if pitch_semitones > 0:
            prosody_attrs.append(f'pitch="+{pitch_semitones}st"')
        elif pitch_semitones < 0:
            prosody_attrs.append(f'pitch="{pitch_semitones}st"')

    if volume is not None:
        # 将因子转换为分贝
        volume_db = int((volume - 1.0) * 10)
        if volume_db > 0:
            prosody_attrs.append(f'volume="+{volume_db}dB"')
        elif volume_db < 0:
            prosody_attrs.append(f'volume="{volume_db}dB"')

    # 如果有韵律属性，添加韵律标签
    if prosody_attrs:
        prosody_tag = f'  <prosody {" ".join(prosody_attrs)}>\n'
        ssml += prosody_tag
        indent = "    "
    else:
        indent = "  "

    # 处理强调
    if emphasis and isinstance(emphasis, list):
        # 创建替换映射
        replacements = {}

        for emph_text, level in emphasis:
            if emph_text in text:
                replacement = f'<emphasis level="{level}">{emph_text}</emphasis>'
                replacements[emph_text] = replacement

        # 应用替换
        processed_text = text
        for original, replacement in replacements.items():
            processed_text = processed_text.replace(original, replacement)

        text = processed_text

    # 添加文本
    ssml += f'{indent}{text}\n'

    # 闭合标签
    if prosody_attrs:
        ssml += '  </prosody>\n'

    if voice:
        ssml += '</voice>\n'

    ssml += '</speak>'

    return ssml