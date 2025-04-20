# -*- coding: utf-8 -*-
"""
视觉模块: 图像处理器
功能描述: 提供图像加载、预处理、变换和增强功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

import os
import io
import logging
import base64
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
import numpy as np

# 尝试导入可选依赖
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 从配置加载器获取配置
try:
    from ...config.config_loader import ConfigLoader
    config_loader = ConfigLoader()
    IMAGE_CONFIG = config_loader.load("modules.vision.image_processor")
except ImportError:
    IMAGE_CONFIG = {
        "default_format": "RGB",
        "max_size": 1024,
        "cache_enabled": True,
        "cache_size": 100
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)

@dataclass
class ImageConfig:
    """图像处理配置类"""
    
    format: str = "RGB"  # 图像格式: RGB, BGR, GRAY
    resize_width: Optional[int] = None  # 调整宽度
    resize_height: Optional[int] = None  # 调整高度
    max_size: int = 1024  # 最大尺寸限制
    normalize: bool = False  # 是否标准化像素值到[0,1]
    grayscale: bool = False  # 是否转换为灰度图
    cache_enabled: bool = True  # 是否启用缓存
    cache_size: int = 100  # 缓存大小
    
    def __post_init__(self):
        """数据校验和默认值设置"""
        valid_formats = ["RGB", "BGR", "GRAY"]
        if self.format not in valid_formats:
            logger.warning(f"无效的图像格式: {self.format}，使用默认格式: RGB")
            self.format = "RGB"
        
        # 确保max_size为正整数
        if self.max_size <= 0:
            logger.warning(f"无效的最大尺寸: {self.max_size}，使用默认值: 1024")
            self.max_size = 1024
        
        # 如果启用了灰度，修改格式为GRAY
        if self.grayscale:
            self.format = "GRAY"


class ImageProcessor:
    """图像处理器类"""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], ImageConfig]] = None):
        """
        初始化图像处理器
        
        参数:
            config: 图像处理配置，可以是ImageConfig实例或字典
        """
        if config is None:
            self.config = ImageConfig(**IMAGE_CONFIG)
        elif isinstance(config, dict):
            self.config = ImageConfig(**config)
        else:
            self.config = config
        
        # 检查依赖可用性
        if not PIL_AVAILABLE and not CV2_AVAILABLE:
            logger.warning("PIL和OpenCV都不可用，图像处理功能将受限")
        
        # 初始化图像缓存
        self.cache = OrderedDict()
        self.temp_dir = None
        
        logger.info(f"图像处理器初始化，格式: {self.config.format}, 最大尺寸: {self.config.max_size}")
    
    def _ensure_temp_dir(self):
        """确保临时目录存在"""
        if self.temp_dir is None:
            from tempfile import mkdtemp
            self.temp_dir = mkdtemp(prefix="image_processor_")
            logger.info(f"创建图像处理临时目录: {self.temp_dir}")
    
    def _add_to_cache(self, key: str, image: np.ndarray):
        """
        将图像添加到缓存
        
        参数:
            key: 缓存键
            image: 图像数据
        """
        if not self.config.cache_enabled:
            return
        
        # 限制缓存大小
        if len(self.cache) >= self.config.cache_size:
            self.cache.popitem(last=False)  # 移除最早添加的项
        
        self.cache[key] = image
    
    def _get_from_cache(self, key: str) -> Optional[np.ndarray]:
        """
        从缓存获取图像
        
        参数:
            key: 缓存键
            
        返回:
            缓存的图像数据，如果不存在则返回None
        """
        if not self.config.cache_enabled or key not in self.cache:
            return None
        
        # 移动到末尾（最近使用）
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def load_image(self, image_source: Union[str, Path, bytes, np.ndarray], 
                   cache_key: Optional[str] = None) -> np.ndarray:
        """
        加载图像
        
        参数:
            image_source: 图像源，可以是文件路径、URL、二进制数据或NumPy数组
            cache_key: 可选的缓存键，如果为None则自动生成
            
        返回:
            加载的图像数据，格式为NumPy数组
        """
        # 处理缓存键
        if cache_key is None:
            if isinstance(image_source, (str, Path)):
                cache_key = str(image_source)
            else:
                cache_key = str(uuid.uuid4())
        
        # 检查缓存
        cached_image = self._get_from_cache(cache_key)
        if cached_image is not None:
            return cached_image
        
        # 加载图像
        if isinstance(image_source, np.ndarray):
            # 已经是NumPy数组
            image = image_source
        
        elif isinstance(image_source, (str, Path)):
            path = str(image_source)
            
            if path.startswith(('http://', 'https://')):
                # 处理URL
                try:
                    import requests
                    response = requests.get(path, stream=True, timeout=10)
                    response.raise_for_status()
                    
                    if PIL_AVAILABLE:
                        img = Image.open(io.BytesIO(response.content))
                        image = np.array(img)
                    elif CV2_AVAILABLE:
                        arr = np.asarray(bytearray(response.content), dtype=np.uint8)
                        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    else:
                        raise RuntimeError("无法加载图像：PIL和OpenCV都不可用")
                except Exception as e:
                    logger.error(f"从URL加载图像失败: {str(e)}")
                    # 返回黑色图像
                    image = np.zeros((100, 100, 3), dtype=np.uint8)
            
            elif os.path.exists(path):
                # 处理本地文件
                try:
                    if PIL_AVAILABLE:
                        img = Image.open(path)
                        image = np.array(img)
                    elif CV2_AVAILABLE:
                        image = cv2.imread(path)
                    else:
                        raise RuntimeError("无法加载图像：PIL和OpenCV都不可用")
                except Exception as e:
                    logger.error(f"从文件加载图像失败: {str(e)}")
                    # 返回黑色图像
                    image = np.zeros((100, 100, 3), dtype=np.uint8)
            
            else:
                logger.error(f"图像路径不存在: {path}")
                # 返回黑色图像
                image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        elif isinstance(image_source, bytes):
            # 处理二进制数据
            try:
                if PIL_AVAILABLE:
                    img = Image.open(io.BytesIO(image_source))
                    image = np.array(img)
                elif CV2_AVAILABLE:
                    arr = np.asarray(bytearray(image_source), dtype=np.uint8)
                    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                else:
                    raise RuntimeError("无法加载图像：PIL和OpenCV都不可用")
            except Exception as e:
                logger.error(f"从二进制数据加载图像失败: {str(e)}")
                # 返回黑色图像
                image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        else:
            logger.error(f"不支持的图像源类型: {type(image_source)}")
            # 返回黑色图像
            image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 预处理图像
        image = self.preprocess_image(image)
        
        # 添加到缓存
        self._add_to_cache(cache_key, image)
        
        return image
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像，应用配置中的转换
        
        参数:
            image: 输入图像
            
        返回:
            预处理后的图像
        """
        # 检查图像是否为空
        if image is None or image.size == 0:
            logger.warning("预处理空图像")
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 调整大小
        if (self.config.resize_width is not None and self.config.resize_height is not None) or self.config.max_size:
            image = resize_image(
                image, 
                width=self.config.resize_width,
                height=self.config.resize_height,
                max_size=self.config.max_size
            )
        
        # 转换为灰度图
        if self.config.grayscale and len(image.shape) > 2 and image.shape[2] > 1:
            if CV2_AVAILABLE:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                # 简单的灰度转换
                image = np.mean(image, axis=2).astype(image.dtype)
            
            # 保持3D形状以便统一处理
            if len(image.shape) == 2:
                image = np.expand_dims(image, axis=2)
        
        # 转换颜色格式
        elif len(image.shape) > 2 and image.shape[2] >= 3:
            if self.config.format == "RGB" and CV2_AVAILABLE and image.shape[2] >= 3:
                # 假设输入是BGR（OpenCV默认）
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif self.config.format == "BGR" and PIL_AVAILABLE and image.shape[2] >= 3:
                # 假设输入是RGB（PIL默认）
                image = image[..., ::-1]  # 简单地反转通道顺序
        
        # 标准化
        if self.config.normalize:
            image = normalize_image(image)
        
        return image
    
    def save_image(self, image: np.ndarray, 
                   path: Union[str, Path],
                   format: Optional[str] = None) -> bool:
        """
        保存图像到文件
        
        参数:
            image: 图像数据
            path: 保存路径
            format: 保存格式，如 'png', 'jpg'等，如果为None则从路径推断
            
        返回:
            是否成功保存
        """
        if image is None or image.size == 0:
            logger.error("无法保存空图像")
            return False
        
        try:
            path = str(path)
            
            # 确保目录存在
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # 处理格式
            if format is None:
                format = os.path.splitext(path)[1].lstrip('.')
                if not format:
                    format = 'png'
            
            # 保存图像
            if PIL_AVAILABLE:
                # 转换为PIL图像
                if len(image.shape) > 2 and image.shape[2] == 3 and self.config.format == "BGR":
                    # 如果当前是BGR格式，转换为RGB（PIL需要）
                    image_rgb = image[..., ::-1]
                else:
                    image_rgb = image
                
                pil_image = Image.fromarray(
                    image_rgb if len(image.shape) > 2 else np.squeeze(image)
                )
                pil_image.save(path, format=format.upper())
            
            elif CV2_AVAILABLE:
                # 直接使用OpenCV保存
                cv2.imwrite(path, image)
            
            else:
                logger.error("无法保存图像：PIL和OpenCV都不可用")
                return False
            
            logger.info(f"图像已保存到: {path}")
            return True
        
        except Exception as e:
            logger.error(f"保存图像失败: {str(e)}")
            return False
    
    def to_base64(self, image: np.ndarray, format: str = 'png') -> str:
        """
        将图像转换为Base64编码字符串
        
        参数:
            image: 图像数据
            format: 图像格式，如 'png', 'jpg'
            
        返回:
            Base64编码的图像字符串
        """
        if image is None or image.size == 0:
            logger.error("无法编码空图像")
            return ""
        
        try:
            # 创建内存文件对象
            buffer = io.BytesIO()
            
            if PIL_AVAILABLE:
                # 转换为PIL图像
                if len(image.shape) > 2 and image.shape[2] == 3 and self.config.format == "BGR":
                    # 如果当前是BGR格式，转换为RGB（PIL需要）
                    image_rgb = image[..., ::-1]
                else:
                    image_rgb = image
                
                pil_image = Image.fromarray(
                    image_rgb if len(image.shape) > 2 else np.squeeze(image)
                )
                pil_image.save(buffer, format=format.upper())
            
            elif CV2_AVAILABLE:
                # 使用OpenCV编码
                success, encoded = cv2.imencode(f'.{format}', image)
                if success:
                    buffer.write(encoded.tobytes())
                else:
                    raise RuntimeError("OpenCV编码图像失败")
            
            else:
                logger.error("无法编码图像：PIL和OpenCV都不可用")
                return ""
            
            # 获取Base64编码
            encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/{format};base64,{encoded_string}"
        
        except Exception as e:
            logger.error(f"转换图像到Base64失败: {str(e)}")
            return ""
    
    def apply_filter(self, image: np.ndarray, filter_type: str, **kwargs) -> np.ndarray:
        """
        应用图像滤镜
        
        参数:
            image: 输入图像
            filter_type: 滤镜类型，如 'blur', 'sharpen', 'edge'等
            **kwargs: 滤镜参数
            
        返回:
            应用滤镜后的图像
        """
        if image is None or image.size == 0:
            logger.error("无法对空图像应用滤镜")
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        try:
            filter_type = filter_type.lower()
            
            if PIL_AVAILABLE:
                # 使用PIL应用滤镜
                if len(image.shape) > 2 and image.shape[2] == 3 and self.config.format == "BGR":
                    # 如果当前是BGR格式，转换为RGB（PIL需要）
                    image_rgb = image[..., ::-1]
                else:
                    image_rgb = image
                
                pil_image = Image.fromarray(
                    image_rgb if len(image.shape) > 2 else np.squeeze(image)
                )
                
                if filter_type == 'blur':
                    radius = kwargs.get('radius', 2)
                    filtered = pil_image.filter(ImageFilter.GaussianBlur(radius=radius))
                
                elif filter_type == 'sharpen':
                    factor = kwargs.get('factor', 2.0)
                    filtered = ImageEnhance.Sharpness(pil_image).enhance(factor)
                
                elif filter_type == 'edge':
                    filtered = pil_image.filter(ImageFilter.FIND_EDGES)
                
                elif filter_type == 'emboss':
                    filtered = pil_image.filter(ImageFilter.EMBOSS)
                
                elif filter_type == 'contour':
                    filtered = pil_image.filter(ImageFilter.CONTOUR)
                
                elif filter_type == 'brightness':
                    factor = kwargs.get('factor', 1.5)
                    filtered = ImageEnhance.Brightness(pil_image).enhance(factor)
                
                elif filter_type == 'contrast':
                    factor = kwargs.get('factor', 1.5)
                    filtered = ImageEnhance.Contrast(pil_image).enhance(factor)
                
                elif filter_type == 'color':
                    factor = kwargs.get('factor', 1.5)
                    filtered = ImageEnhance.Color(pil_image).enhance(factor)
                
                else:
                    logger.warning(f"未知的滤镜类型: {filter_type}，返回原始图像")
                    return image
                
                # 转换回NumPy数组
                result = np.array(filtered)
                
                # 如果需要转换回BGR
                if len(result.shape) > 2 and result.shape[2] == 3 and self.config.format == "BGR":
                    result = result[..., ::-1]
                
                return result
            
            elif CV2_AVAILABLE:
                # 使用OpenCV应用滤镜
                if filter_type == 'blur':
                    kernel_size = kwargs.get('kernel_size', 5)
                    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
                
                elif filter_type == 'sharpen':
                    kernel = np.array([[-1, -1, -1],
                                       [-1, 9, -1],
                                       [-1, -1, -1]])
                    return cv2.filter2D(image, -1, kernel)
                
                elif filter_type == 'edge':
                    return cv2.Canny(image, 100, 200)
                
                elif filter_type == 'brightness':
                    factor = kwargs.get('factor', 1.5)
                    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                    hsv[..., 2] = np.clip(hsv[..., 2] * factor, 0, 255).astype(np.uint8)
                    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                
                elif filter_type == 'contrast':
                    factor = kwargs.get('factor', 1.5)
                    return np.clip((image.astype(np.float32) - 128) * factor + 128, 0, 255).astype(np.uint8)
                
                else:
                    logger.warning(f"未知的或不支持的OpenCV滤镜类型: {filter_type}，返回原始图像")
                    return image
            
            else:
                logger.error("无法应用滤镜：PIL和OpenCV都不可用")
                return image
        
        except Exception as e:
            logger.error(f"应用滤镜失败: {str(e)}")
            return image
    
    def crop_image(self, image: np.ndarray, 
                   x: int, y: int, 
                   width: int, height: int) -> np.ndarray:
        """
        裁剪图像
        
        参数:
            image: 输入图像
            x, y: 裁剪区域左上角坐标
            width, height: 裁剪区域宽度和高度
            
        返回:
            裁剪后的图像
        """
        if image is None or image.size == 0:
            logger.error("无法裁剪空图像")
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        try:
            # 获取图像尺寸
            if len(image.shape) == 3:
                img_height, img_width = image.shape[:2]
            else:
                img_height, img_width = image.shape
            
            # 验证裁剪参数
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            width = max(1, min(width, img_width - x))
            height = max(1, min(height, img_height - y))
            
            # 裁剪图像
            return image[y:y+height, x:x+width]
        
        except Exception as e:
            logger.error(f"裁剪图像失败: {str(e)}")
            return image
    
    def rotate_image(self, image: np.ndarray, 
                     angle: float,
                     keep_size: bool = True) -> np.ndarray:
        """
        旋转图像
        
        参数:
            image: 输入图像
            angle: 旋转角度（度）
            keep_size: 是否保持原始尺寸
            
        返回:
            旋转后的图像
        """
        if image is None or image.size == 0:
            logger.error("无法旋转空图像")
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        try:
            if PIL_AVAILABLE:
                # 使用PIL旋转
                if len(image.shape) > 2 and image.shape[2] == 3 and self.config.format == "BGR":
                    # 如果当前是BGR格式，转换为RGB（PIL需要）
                    image_rgb = image[..., ::-1]
                else:
                    image_rgb = image
                
                pil_image = Image.fromarray(
                    image_rgb if len(image.shape) > 2 else np.squeeze(image)
                )
                
                # 处理扩展模式
                if keep_size:
                    expand = False
                    fill_color = (0, 0, 0)  # 黑色填充
                else:
                    expand = True
                    fill_color = None
                
                rotated = pil_image.rotate(angle, expand=expand, fillcolor=fill_color)
                
                # 转换回NumPy数组
                result = np.array(rotated)
                
                # 如果需要转换回BGR
                if len(result.shape) > 2 and result.shape[2] == 3 and self.config.format == "BGR":
                    result = result[..., ::-1]
                
                return result
            
            elif CV2_AVAILABLE:
                # 使用OpenCV旋转
                height, width = image.shape[:2]
                center = (width // 2, height // 2)
                
                # 计算旋转矩阵
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                if keep_size:
                    # 直接应用旋转矩阵
                    result = cv2.warpAffine(image, rotation_matrix, (width, height))
                else:
                    # 计算新尺寸
                    angle_rad = np.radians(angle)
                    new_width = int(np.abs(width * np.cos(angle_rad)) + np.abs(height * np.sin(angle_rad)))
                    new_height = int(np.abs(height * np.cos(angle_rad)) + np.abs(width * np.sin(angle_rad)))
                    
                    # 调整旋转矩阵
                    rotation_matrix[0, 2] += (new_width - width) / 2
                    rotation_matrix[1, 2] += (new_height - height) / 2
                    
                    # 应用旋转矩阵
                    result = cv2.warpAffine(image, rotation_matrix, (new_width, new_height))
                
                return result
            
            else:
                logger.error("无法旋转图像：PIL和OpenCV都不可用")
                return image
        
        except Exception as e:
            logger.error(f"旋转图像失败: {str(e)}")
            return image
    
    def clear_cache(self):
        """清除图像缓存"""
        self.cache.clear()
        logger.info("图像缓存已清除")


# 工具函数

def resize_image(image: np.ndarray, 
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 max_size: Optional[int] = None) -> np.ndarray:
    """
    调整图像大小
    
    参数:
        image: 输入图像
        width: 目标宽度，如果为None则按比例计算
        height: 目标高度，如果为None则按比例计算
        max_size: 最大尺寸限制
        
    返回:
        调整大小后的图像
    """
    if image is None or image.size == 0:
        return image
    
    try:
        # 获取原始尺寸
        if len(image.shape) > 2:
            h, w = image.shape[:2]
        else:
            h, w = image.shape
        
        # 如果明确指定了宽度和高度
        if width is not None and height is not None:
            new_w, new_h = width, height
        
        # 如果只指定了宽度，按比例计算高度
        elif width is not None:
            new_w = width
            new_h = int(h * (width / w))
        
        # 如果只指定了高度，按比例计算宽度
        elif height is not None:
            new_h = height
            new_w = int(w * (height / h))
        
        # 如果设置了最大尺寸限制
        elif max_size is not None and (w > max_size or h > max_size):
            if w > h:
                new_w = max_size
                new_h = int(h * (max_size / w))
            else:
                new_h = max_size
                new_w = int(w * (max_size / h))
        
        # 如果没有任何调整参数，返回原图
        else:
            return image
        
        # 确保尺寸至少为1
        new_w = max(1, new_w)
        new_h = max(1, new_h)
        
        # 调整图像大小
        if CV2_AVAILABLE:
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        elif PIL_AVAILABLE:
            # 转换为PIL图像
            if len(image.shape) > 2 and image.shape[2] == 3:
                # 假设是BGR格式（OpenCV），转换为RGB（PIL需要）
                image_rgb = image[..., ::-1]
            else:
                image_rgb = image
            
            pil_image = Image.fromarray(
                image_rgb if len(image.shape) > 2 else np.squeeze(image)
            )
            resized = pil_image.resize((new_w, new_h), Image.LANCZOS)
            
            # 转换回NumPy数组
            result = np.array(resized)
            
            # 如果是3通道图像，转换回BGR格式
            if len(result.shape) > 2 and result.shape[2] == 3 and len(image.shape) > 2 and image.shape[2] == 3:
                result = result[..., ::-1]
            
            return result
        
        else:
            # 简单的调整大小实现
            from scipy.ndimage import zoom
            
            # 计算缩放比例
            zoom_factors = [new_h / h, new_w / w]
            
            # 如果是彩色图像，为所有通道应用相同的缩放比例
            if len(image.shape) > 2:
                zoom_factors.extend([1] * (len(image.shape) - 2))
            
            return zoom(image, zoom_factors, order=1)
    
    except Exception as e:
        logger.error(f"调整图像大小失败: {str(e)}")
        return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    标准化图像像素值到范围[0,1]
    
    参数:
        image: 输入图像
        
    返回:
        标准化后的图像
    """
    if image is None or image.size == 0:
        return image
    
    try:
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        elif image.dtype == np.uint16:
            return image.astype(np.float32) / 65535.0
        else:
            # 已经是浮点类型，确保在[0,1]范围内
            min_val = np.min(image)
            max_val = np.max(image)
            
            if min_val >= 0 and max_val <= 1:
                # 已经标准化
                return image
            
            if max_val > min_val:
                # 线性缩放到[0,1]
                return (image - min_val) / (max_val - min_val)
            else:
                # 避免除以零
                return np.zeros_like(image, dtype=np.float32)
    
    except Exception as e:
        logger.error(f"标准化图像失败: {str(e)}")
        return image


def denormalize_image(image: np.ndarray, dtype: np.dtype = np.uint8) -> np.ndarray:
    """
    将标准化的图像转换回原始范围
    
    参数:
        image: 标准化的图像，范围[0,1]
        dtype: 目标数据类型
        
    返回:
        反标准化后的图像
    """
    if image is None or image.size == 0:
        return image
    
    try:
        if dtype == np.uint8:
            return np.clip(image * 255.0, 0, 255).astype(np.uint8)
        elif dtype == np.uint16:
            return np.clip(image * 65535.0, 0, 65535).astype(np.uint16)
        else:
            return image
    
    except Exception as e:
        logger.error(f"反标准化图像失败: {str(e)}")
        return image