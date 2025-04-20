# -*- coding: utf-8 -*-
"""
视频模块: 视频处理器
功能描述: 提供视频加载、帧提取和视频分析功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-18
"""

import os
import io
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, BinaryIO, Generator, Callable
from collections import OrderedDict

# 尝试导入可选依赖
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# 从配置加载器获取配置
try:
    from ...config.config_loader import ConfigLoader
    config_loader = ConfigLoader()
    VIDEO_CONFIG = config_loader.load("modules.video.video_processor")
except ImportError:
    VIDEO_CONFIG = {
        "default_fps": 1,
        "cache_enabled": True,
        "cache_size": 50,
        "temp_dir": None,
        "default_format": "mp4"
    }

# 引入图像处理器和对象检测器
try:
    from ..vision.image_processor import ImageProcessor
    from ..vision.object_detection import ObjectDetector
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

# 初始化日志记录器
logger = logging.getLogger(__name__)

class VideoProcessor:
    """视频处理器类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化视频处理器
        
        参数:
            config: 处理器配置
        """
        # 合并配置
        self.config = VIDEO_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # 检查依赖可用性
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未安装，视频处理功能将受限")
        
        # 初始化缓存
        self.cache = OrderedDict() if self.config.get("cache_enabled", True) else None
        self.cache_size = self.config.get("cache_size", 50)
        
        # 创建临时目录
        self.temp_dir = self.config.get("temp_dir")
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="video_processor_")
            logger.info(f"创建视频处理临时目录: {self.temp_dir}")
        
        # 初始化图像处理器和对象检测器（如果可用）
        self.image_processor = None
        self.object_detector = None
        if VISION_AVAILABLE:
            try:
                self.image_processor = ImageProcessor()
                self.object_detector = ObjectDetector()
                logger.info("成功初始化图像处理器和对象检测器")
            except Exception as e:
                logger.error(f"初始化视觉处理模块失败: {str(e)}")
        
        logger.info(f"视频处理器初始化完成")
    
    def _add_to_cache(self, key: str, data: Any):
        """
        将数据添加到缓存
        
        参数:
            key: 缓存键
            data: 数据
        """
        if self.cache is None:
            return
        
        # 限制缓存大小
        if len(self.cache) >= self.cache_size:
            self.cache.popitem(last=False)  # 移除最早添加的项
        
        self.cache[key] = data
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        参数:
            key: 缓存键
            
        返回:
            缓存的数据，如果不存在则返回None
        """
        if self.cache is None or key not in self.cache:
            return None
        
        # 移动到末尾（最近使用）
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def load_video(self, video_source: Union[str, Path, BinaryIO]) -> Optional[Any]:
        """
        加载视频
        
        参数:
            video_source: 视频源，可以是文件路径、URL或文件对象
            
        返回:
            OpenCV VideoCapture对象或None（如果加载失败）
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法加载视频")
            return None
        
        try:
            # 处理不同类型的输入
            if isinstance(video_source, (str, Path)):
                # 文件路径或URL
                path = str(video_source)
                
                # 生成缓存键
                cache_key = f"video_{path}"
                
                # 检查缓存
                cached_video = self._get_from_cache(cache_key)
                if cached_video is not None:
                    return cached_video
                
                # 加载视频
                video = cv2.VideoCapture(path)
                if not video.isOpened():
                    logger.error(f"无法打开视频: {path}")
                    return None
                
                # 添加到缓存
                self._add_to_cache(cache_key, video)
                return video
            
            elif hasattr(video_source, 'read') and callable(video_source.read):
                # 文件对象，保存到临时文件
                temp_path = os.path.join(self.temp_dir, f"temp_video_{uuid.uuid4()}.mp4")
                
                with open(temp_path, 'wb') as f:
                    f.write(video_source.read())
                
                # 加载临时文件
                video = cv2.VideoCapture(temp_path)
                if not video.isOpened():
                    logger.error(f"无法打开临时视频文件: {temp_path}")
                    os.unlink(temp_path)
                    return None
                
                return video
            
            else:
                logger.error(f"不支持的视频源类型: {type(video_source)}")
                return None
        
        except Exception as e:
            logger.error(f"加载视频失败: {str(e)}")
            return None
    
    def get_video_info(self, video: Any) -> Dict[str, Any]:
        """
        获取视频信息
        
        参数:
            video: OpenCV VideoCapture对象
            
        返回:
            包含视频信息的字典
        """
        if not CV2_AVAILABLE or video is None:
            logger.error("无法获取视频信息")
            return {}
        
        try:
            # 获取基本信息
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = video.get(cv2.CAP_PROP_FPS)
            width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 计算持续时间（秒）
            duration = frame_count / fps if fps > 0 else 0
            
            # 返回信息字典
            return {
                "frame_count": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration": duration,
                "format": self.config.get("default_format", "mp4")
            }
        
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {}
    
    def extract_frames(self, 
                      video_source: Union[str, Path, BinaryIO, Any],
                      output_dir: Optional[str] = None,
                      fps: Optional[float] = None,
                      frame_interval: Optional[int] = None,
                      max_frames: Optional[int] = None,
                      output_format: str = "jpg",
                      frame_prefix: str = "frame",
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None,
                      process_frame: Optional[Callable] = None) -> List[str]:
        """
        从视频中提取帧
        
        参数:
            video_source: 视频源，可以是文件路径、URL、文件对象或OpenCV VideoCapture对象
            output_dir: 输出目录，如果为None则使用临时目录
            fps: 每秒提取的帧数，如果为None则使用默认值(1)
            frame_interval: 帧间隔，如果指定则优先使用，否则根据fps计算
            max_frames: 最大提取帧数，如果为None则不限制
            output_format: 输出图像格式，如 'jpg', 'png'
            frame_prefix: 输出文件名前缀
            start_time: 开始时间（秒），如果为None则从头开始
            end_time: 结束时间（秒），如果为None则到结尾
            process_frame: 处理帧的函数，接收帧图像作为参数并返回处理后的图像
            
        返回:
            提取的帧文件路径列表
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法提取视频帧")
            return []
        
        try:
            # 加载视频（如果需要）
            video = video_source
            if not isinstance(video_source, cv2.VideoCapture):
                video = self.load_video(video_source)
            
            if video is None or not video.isOpened():
                logger.error("无法打开视频")
                return []
            
            # 获取视频信息
            video_fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = frame_count / video_fps if video_fps > 0 else 0
            
            # 设置输出目录
            if output_dir is None:
                output_dir = self.temp_dir
            elif not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 设置帧提取参数
            target_fps = fps if fps is not None else self.config.get("default_fps", 1)
            
            if frame_interval is not None:
                # 使用指定的帧间隔
                interval = frame_interval
            else:
                # 根据目标fps计算帧间隔
                interval = max(1, int(video_fps / target_fps))
            
            # 设置时间范围
            start_frame = 0
            end_frame = frame_count
            
            if start_time is not None:
                start_frame = max(0, int(start_time * video_fps))
            
            if end_time is not None:
                end_frame = min(frame_count, int(end_time * video_fps))
            
            # 设置当前帧位置
            if start_frame > 0:
                video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # 提取帧
            frame_paths = []
            frame_number = start_frame
            extracted_count = 0
            
            while frame_number < end_frame:
                # 读取一帧
                success, frame = video.read()
                
                if not success:
                    break
                
                # 检查是否应提取此帧
                if (frame_number - start_frame) % interval == 0:
                    # 处理帧（如果提供了处理函数）
                    if process_frame is not None:
                        try:
                            frame = process_frame(frame)
                        except Exception as e:
                            logger.error(f"处理帧 {frame_number} 失败: {str(e)}")
                    
                    # 生成帧文件名
                    timestamp = frame_number / video_fps
                    frame_filename = f"{frame_prefix}_{extracted_count:06d}_{timestamp:.2f}.{output_format}"
                    frame_path = os.path.join(output_dir, frame_filename)
                    
                    # 保存帧
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    
                    extracted_count += 1
                    
                    # 检查是否达到最大帧数
                    if max_frames is not None and extracted_count >= max_frames:
                        break
                
                frame_number += 1
            
            logger.info(f"成功提取 {len(frame_paths)} 帧图像")
            return frame_paths
        
        except Exception as e:
            logger.error(f"提取视频帧失败: {str(e)}")
            return []
        
        finally:
            # 关闭视频（如果我们创建了它）
            if video is not None and video != video_source:
                video.release()
    
    def extract_frames_generator(self, 
                               video_source: Union[str, Path, BinaryIO, Any],
                               fps: Optional[float] = None,
                               frame_interval: Optional[int] = None,
                               max_frames: Optional[int] = None,
                               start_time: Optional[float] = None,
                               end_time: Optional[float] = None,
                               process_frame: Optional[Callable] = None) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """
        从视频中提取帧并以生成器形式返回
        
        参数:
            video_source: 视频源，可以是文件路径、URL、文件对象或OpenCV VideoCapture对象
            fps: 每秒提取的帧数，如果为None则使用默认值(1)
            frame_interval: 帧间隔，如果指定则优先使用，否则根据fps计算
            max_frames: 最大提取帧数，如果为None则不限制
            start_time: 开始时间（秒），如果为None则从头开始
            end_time: 结束时间（秒），如果为None则到结尾
            process_frame: 处理帧的函数，接收帧图像作为参数并返回处理后的图像
            
        返回:
            生成器，每次返回(帧索引, 时间戳, 帧图像)元组
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法提取视频帧")
            return
        
        try:
            # 加载视频（如果需要）
            video = video_source
            if not isinstance(video_source, cv2.VideoCapture):
                video = self.load_video(video_source)
            
            if video is None or not video.isOpened():
                logger.error("无法打开视频")
                return
            
            # 获取视频信息
            video_fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 设置帧提取参数
            target_fps = fps if fps is not None else self.config.get("default_fps", 1)
            
            if frame_interval is not None:
                # 使用指定的帧间隔
                interval = frame_interval
            else:
                # 根据目标fps计算帧间隔
                interval = max(1, int(video_fps / target_fps))
            
            # 设置时间范围
            start_frame = 0
            end_frame = frame_count
            
            if start_time is not None:
                start_frame = max(0, int(start_time * video_fps))
            
            if end_time is not None:
                end_frame = min(frame_count, int(end_time * video_fps))
            
            # 设置当前帧位置
            if start_frame > 0:
                video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # 提取帧
            frame_number = start_frame
            extracted_count = 0
            
            while frame_number < end_frame:
                # 读取一帧
                success, frame = video.read()
                
                if not success:
                    break
                
                # 检查是否应提取此帧
                if (frame_number - start_frame) % interval == 0:
                    # 计算时间戳
                    timestamp = frame_number / video_fps
                    
                    # 处理帧（如果提供了处理函数）
                    if process_frame is not None:
                        try:
                            frame = process_frame(frame)
                        except Exception as e:
                            logger.error(f"处理帧 {frame_number} 失败: {str(e)}")
                    
                    # 生成并返回帧
                    yield (extracted_count, timestamp, frame)
                    
                    extracted_count += 1
                    
                    # 检查是否达到最大帧数
                    if max_frames is not None and extracted_count >= max_frames:
                        break
                
                frame_number += 1
        
        except Exception as e:
            logger.error(f"提取视频帧失败: {str(e)}")
        
        finally:
            # 关闭视频（如果我们创建了它）
            if video is not None and video != video_source:
                video.release()
    
    def analyze_video_frames(self, 
                           video_source: Union[str, Path, BinaryIO, Any],
                           analyzer: Callable[[np.ndarray], Any],
                           fps: Optional[float] = None,
                           batch_size: int = 10,
                           start_time: Optional[float] = None,
                           end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        分析视频帧
        
        参数:
            video_source: 视频源
            analyzer: 分析函数，接收帧图像作为输入并返回分析结果
            fps: 每秒分析的帧数，如果为None则使用默认值(1)
            batch_size: 批处理大小，控制内存使用
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            
        返回:
            分析结果列表，每个元素是包含帧索引、时间戳和分析结果的字典
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法分析视频帧")
            return []
        
        try:
            results = []
            batch = []
            batch_timestamps = []
            batch_indices = []
            
            # 使用生成器提取帧
            for idx, timestamp, frame in self.extract_frames_generator(
                video_source=video_source,
                fps=fps,
                start_time=start_time,
                end_time=end_time
            ):
                # 添加到批处理
                batch.append(frame)
                batch_timestamps.append(timestamp)
                batch_indices.append(idx)
                
                # 达到批处理大小或处理最后一批
                if len(batch) >= batch_size:
                    # 处理当前批次
                    for i, (frame_idx, ts, img) in enumerate(zip(batch_indices, batch_timestamps, batch)):
                        try:
                            # 分析帧
                            analysis_result = analyzer(img)
                            
                            # 添加结果
                            results.append({
                                "frame_index": frame_idx,
                                "timestamp": ts,
                                "result": analysis_result
                            })
                        except Exception as e:
                            logger.error(f"分析帧 {frame_idx} 失败: {str(e)}")
                    
                    # 清空批处理
                    batch = []
                    batch_timestamps = []
                    batch_indices = []
            
            # 处理剩余的帧
            if batch:
                for i, (frame_idx, ts, img) in enumerate(zip(batch_indices, batch_timestamps, batch)):
                    try:
                        # 分析帧
                        analysis_result = analyzer(img)
                        
                        # 添加结果
                        results.append({
                            "frame_index": frame_idx,
                            "timestamp": ts,
                            "result": analysis_result
                        })
                    except Exception as e:
                        logger.error(f"分析帧 {frame_idx} 失败: {str(e)}")
            
            logger.info(f"成功分析 {len(results)} 帧")
            return results
        
        except Exception as e:
            logger.error(f"分析视频帧失败: {str(e)}")
            return []
    
    def detect_objects_in_video(self, 
                              video_source: Union[str, Path, BinaryIO, Any],
                              confidence_threshold: float = 0.5,
                              fps: Optional[float] = None,
                              batch_size: int = 10,
                              start_time: Optional[float] = None,
                              end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        在视频中检测对象
        
        参数:
            video_source: 视频源
            confidence_threshold: 置信度阈值
            fps: 每秒分析的帧数
            batch_size: 批处理大小
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            
        返回:
            检测结果列表
        """
        if not VISION_AVAILABLE or self.object_detector is None:
            logger.error("对象检测器未初始化，无法执行视频对象检测")
            return []
        
        # 定义分析函数
        def analyze_frame(frame):
            # 检测对象
            detections = self.object_detector.detect(frame)
            
            # 过滤低置信度检测
            detections = [d for d in detections if d.confidence >= confidence_threshold]
            
            # 转换为可序列化格式
            return [d.to_dict() for d in detections]
        
        # 分析视频帧
        return self.analyze_video_frames(
            video_source=video_source,
            analyzer=analyze_frame,
            fps=fps,
            batch_size=batch_size,
            start_time=start_time,
            end_time=end_time
        )
    
    def create_timelapse(self, 
                        video_source: Union[str, Path, BinaryIO, Any],
                        output_path: str,
                        speedup_factor: int = 10,
                        fps: Optional[float] = None,
                        resolution: Optional[Tuple[int, int]] = None) -> bool:
        """
        创建延时摄影视频
        
        参数:
            video_source: 视频源
            output_path: 输出文件路径
            speedup_factor: 加速因子
            fps: 输出视频帧率，如果为None则使用原始帧率
            resolution: 输出分辨率(宽, 高)，如果为None则使用原始分辨率
            
        返回:
            是否成功创建
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法创建延时摄影视频")
            return False
        
        try:
            # 加载视频
            video = None
            if not isinstance(video_source, cv2.VideoCapture):
                video = self.load_video(video_source)
            else:
                video = video_source
            
            if video is None or not video.isOpened():
                logger.error("无法打开视频")
                return False
            
            # 获取视频信息
            orig_fps = video.get(cv2.CAP_PROP_FPS)
            orig_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 设置输出参数
            out_fps = fps if fps is not None else orig_fps
            out_width, out_height = resolution if resolution is not None else (orig_width, orig_height)
            
            # 计算帧间隔（加速）
            frame_interval = speedup_factor
            
            # 创建视频编写器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用MP4编码
            out = cv2.VideoWriter(output_path, fourcc, out_fps, (out_width, out_height))
            
            if not out.isOpened():
                logger.error(f"无法创建输出视频: {output_path}")
                return False
            
            # 处理帧
            frame_count = 0
            success = True
            
            while success:
                # 读取一帧
                success, frame = video.read()
                
                if success:
                    # 每n帧处理一次
                    if frame_count % frame_interval == 0:
                        # 调整分辨率（如果需要）
                        if out_width != orig_width or out_height != orig_height:
                            frame = cv2.resize(frame, (out_width, out_height))
                        
                        # 写入输出视频
                        out.write(frame)
                
                frame_count += 1
            
            # 释放资源
            out.release()
            
            logger.info(f"成功创建延时摄影视频: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"创建延时摄影视频失败: {str(e)}")
            return False
        
        finally:
            # 关闭视频（如果我们创建了它）
            if video is not None and video != video_source:
                video.release()
    
    def extract_key_frames(self, 
                          video_source: Union[str, Path, BinaryIO, Any],
                          threshold: float = 0.5,
                          max_frames: Optional[int] = None,
                          output_dir: Optional[str] = None) -> List[str]:
        """
        提取视频中的关键帧（基于场景变化）
        
        参数:
            video_source: 视频源
            threshold: 场景变化阈值 (0-1)，值越大意味着需要更大的变化
            max_frames: 最大提取帧数
            output_dir: 输出目录
            
        返回:
            关键帧文件路径列表
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法提取关键帧")
            return []
        
        try:
            # 加载视频
            video = None
            if not isinstance(video_source, cv2.VideoCapture):
                video = self.load_video(video_source)
            else:
                video = video_source
            
            if video is None or not video.isOpened():
                logger.error("无法打开视频")
                return []
            
            # 设置输出目录
            if output_dir is None:
                output_dir = self.temp_dir
            elif not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 读取第一帧
            success, prev_frame = video.read()
            if not success:
                logger.error("无法读取视频帧")
                return []
            
            # 转换为灰度图
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            
            # 保存第一帧
            first_frame_path = os.path.join(output_dir, f"keyframe_0000.jpg")
            cv2.imwrite(first_frame_path, prev_frame)
            key_frame_paths = [first_frame_path]
            
            frame_count = 1
            key_frame_count = 1
            
            while True:
                # 读取下一帧
                success, curr_frame = video.read()
                if not success:
                    break
                
                # 转换为灰度图
                curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
                
                # 计算帧差异
                diff = cv2.absdiff(curr_gray, prev_gray)
                mean_diff = cv2.mean(diff)[0] / 255.0  # 归一化到0-1
                
                # 检查是否达到阈值
                if mean_diff > threshold:
                    # 保存关键帧
                    key_frame_path = os.path.join(output_dir, f"keyframe_{key_frame_count:04d}.jpg")
                    cv2.imwrite(key_frame_path, curr_frame)
                    key_frame_paths.append(key_frame_path)
                    
                    key_frame_count += 1
                    
                    # 检查是否达到最大帧数
                    if max_frames is not None and key_frame_count >= max_frames:
                        break
                    
                    # 更新参考帧
                    prev_gray = curr_gray
                
                frame_count += 1
            
            logger.info(f"成功提取 {len(key_frame_paths)} 个关键帧")
            return key_frame_paths
        
        except Exception as e:
            logger.error(f"提取关键帧失败: {str(e)}")
            return []
        
        finally:
            # 关闭视频（如果我们创建了它）
            if video is not None and video != video_source:
                video.release()
    
    def process_video(self, 
                     video_source: Union[str, Path, BinaryIO, Any],
                     output_path: str,
                     process_frame: Callable[[np.ndarray], np.ndarray],
                     fps: Optional[float] = None,
                     resolution: Optional[Tuple[int, int]] = None) -> bool:
        """
        处理视频（应用帧处理函数）
        
        参数:
            video_source: 视频源
            output_path: 输出文件路径
            process_frame: 处理函数，接收帧图像并返回处理后的图像
            fps: 输出视频帧率，如果为None则使用原始帧率
            resolution: 输出分辨率(宽, 高)，如果为None则使用原始分辨率
            
        返回:
            是否成功处理
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法处理视频")
            return False
        
        try:
            # 加载视频
            video = None
            if not isinstance(video_source, cv2.VideoCapture):
                video = self.load_video(video_source)
            else:
                video = video_source
            
            if video is None or not video.isOpened():
                logger.error("无法打开视频")
                return False
            
            # 获取视频信息
            orig_fps = video.get(cv2.CAP_PROP_FPS)
            orig_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 设置输出参数
            out_fps = fps if fps is not None else orig_fps
            out_width, out_height = resolution if resolution is not None else (orig_width, orig_height)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 创建视频编写器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用MP4编码
            out = cv2.VideoWriter(output_path, fourcc, out_fps, (out_width, out_height))
            
            if not out.isOpened():
                logger.error(f"无法创建输出视频: {output_path}")
                return False
            
            # 处理帧
            frame_count = 0
            success = True
            
            while success:
                # 读取一帧
                success, frame = video.read()
                
                if success:
                    try:
                        # 处理帧
                        processed_frame = process_frame(frame)
                        
                        # 调整分辨率（如果需要）
                        if processed_frame.shape[1] != out_width or processed_frame.shape[0] != out_height:
                            processed_frame = cv2.resize(processed_frame, (out_width, out_height))
                        
                        # 写入输出视频
                        out.write(processed_frame)
                        
                        frame_count += 1
                    except Exception as e:
                        logger.error(f"处理帧 {frame_count} 失败: {str(e)}")
            
            # 释放资源
            out.release()
            
            logger.info(f"成功处理视频，处理了 {frame_count} 帧，输出到: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"处理视频失败: {str(e)}")
            return False
        
        finally:
            # 关闭视频（如果我们创建了它）
            if video is not None and video != video_source:
                video.release()
    
    def clean_temp_files(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                logger.info("已清理临时文件")
            except Exception as e:
                logger.error(f"清理临时文件失败: {str(e)}")
    
    def __del__(self):
        """析构函数，清理资源"""
        self.clean_temp_files()


# 辅助函数

def create_video_from_frames(frame_paths: List[str], 
                           output_path: str,
                           fps: float = 30.0,
                           resolution: Optional[Tuple[int, int]] = None) -> bool:
    """
    从图像帧创建视频
    
    参数:
        frame_paths: 帧图像文件路径列表
        output_path: 输出视频文件路径
        fps: 帧率
        resolution: 分辨率 (宽, 高)，如果为None则使用第一帧的分辨率
        
    返回:
        是否成功创建
    """
    if not CV2_AVAILABLE:
        logger.error("OpenCV未安装，无法创建视频")
        return False
    
    if not frame_paths:
        logger.error("帧列表为空，无法创建视频")
        return False
    
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 获取第一帧确定分辨率
        first_frame = cv2.imread(frame_paths[0])
        if first_frame is None:
            logger.error(f"无法读取第一帧: {frame_paths[0]}")
            return False
        
        frame_height, frame_width = first_frame.shape[:2]
        
        # 设置分辨率
        if resolution is not None:
            out_width, out_height = resolution
        else:
            out_width, out_height = frame_width, frame_height
        
        # 创建视频编写器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用MP4编码
        out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))
        
        if not out.isOpened():
            logger.error(f"无法创建输出视频: {output_path}")
            return False
        
        # 添加帧
        for frame_path in frame_paths:
            frame = cv2.imread(frame_path)
            if frame is None:
                logger.warning(f"无法读取帧: {frame_path}")
                continue
            
            # 调整分辨率（如果需要）
            if frame.shape[1] != out_width or frame.shape[0] != out_height:
                frame = cv2.resize(frame, (out_width, out_height))
            
            # 写入输出视频
            out.write(frame)
        
        # 释放资源
        out.release()
        
        logger.info(f"成功从 {len(frame_paths)} 帧创建视频: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"创建视频失败: {str(e)}")
        return False


def extract_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    提取视频元数据
    
    参数:
        video_path: 视频文件路径
        
    返回:
        包含元数据的字典
    """
    if not CV2_AVAILABLE:
        logger.error("OpenCV未安装，无法提取视频元数据")
        return {}
    
    try:
        # 打开视频
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return {}
        
        # 获取基本信息
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 计算持续时间（秒）
        duration = frame_count / fps if fps > 0 else 0
        
        # 获取编码器信息
        fourcc_int = int(video.get(cv2.CAP_PROP_FOURCC))
        fourcc = chr(fourcc_int & 0xFF) + chr((fourcc_int >> 8) & 0xFF) + chr((fourcc_int >> 16) & 0xFF) + chr((fourcc_int >> 24) & 0xFF)
        
        # 获取文件大小
        file_size = os.path.getsize(video_path)
        
        # 释放视频
        video.release()
        
        # 返回元数据
        return {
            "frame_count": frame_count,
            "fps": fps,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "duration": duration,
            "duration_formatted": f"{int(duration // 60)}:{int(duration % 60):02d}",
            "codec": fourcc,
            "file_size": file_size,
            "file_size_mb": file_size / (1024 * 1024)
        }
    
    except Exception as e:
        logger.error(f"提取视频元数据失败: {str(e)}")
        return {}