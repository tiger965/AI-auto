# -*- coding: utf-8 -*-
"""
视觉模块: 对象检测
功能描述: 提供图像对象检测功能，支持多种检测模型
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
import numpy as np

# 尝试导入可选依赖
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 从配置加载器获取配置
try:
    from ...config.config_loader import ConfigLoader
    config_loader = ConfigLoader()
    DETECTION_CONFIG = config_loader.load("modules.vision.object_detection")
except ImportError:
    DETECTION_CONFIG = {
        "model_path": "models/detection/default",
        "confidence_threshold": 0.5,
        "enable_gpu": False
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """对象检测结果类"""
    
    class_id: int  # 类别ID
    class_name: str  # 类别名称
    confidence: float  # 置信度
    x: int  # 左上角x坐标
    y: int  # 左上角y坐标
    width: int  # 宽度
    height: int  # 高度
    
    @property
    def box(self) -> Tuple[int, int, int, int]:
        """获取检测框坐标 (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def box_xyxy(self) -> Tuple[int, int, int, int]:
        """获取检测框坐标 (x1, y1, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    @property
    def center(self) -> Tuple[int, int]:
        """获取检测框中心点坐标"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        """获取检测框面积"""
        return self.width * self.height
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionResult':
        """从字典创建实例"""
        return cls(
            class_id=data["class_id"],
            class_name=data["class_name"],
            confidence=data["confidence"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"]
        )
    
    @classmethod
    def from_yolo_format(cls, 
                        detection: List[float], 
                        image_width: int, 
                        image_height: int,
                        class_names: List[str]) -> 'DetectionResult':
        """
        从YOLO格式检测结果创建实例
        
        参数:
            detection: YOLO格式检测 [class_id, x_center, y_center, width, height, confidence]
            image_width: 原始图像宽度
            image_height: 原始图像高度
            class_names: 类别名称列表
            
        返回:
            DetectionResult实例
        """
        class_id = int(detection[0])
        x_center = detection[1] * image_width
        y_center = detection[2] * image_height
        width = detection[3] * image_width
        height = detection[4] * image_height
        confidence = detection[5] if len(detection) > 5 else 1.0
        
        # 转换为左上角坐标
        x = int(x_center - width / 2)
        y = int(y_center - height / 2)
        
        # 获取类别名称
        class_name = class_names[class_id] if class_id < len(class_names) else f"class_{class_id}"
        
        return cls(
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
            x=x,
            y=y,
            width=int(width),
            height=int(height)
        )


class ObjectDetector:
    """对象检测器类"""
    
    SUPPORTED_BACKENDS = ["opencv", "yolo", "torch", "custom"]
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 model_type: str = "opencv",
                 confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.4,
                 enable_gpu: bool = False,
                 class_names: Optional[List[str]] = None):
        """
        初始化对象检测器
        
        参数:
            model_path: 模型路径，如果为None则使用配置中的路径
            model_type: 模型类型，支持 "opencv", "yolo", "torch", "custom"
            confidence_threshold: 置信度阈值
            nms_threshold: 非极大值抑制阈值
            enable_gpu: 是否启用GPU
            class_names: 类别名称列表，如果为None则尝试从模型配置加载
        """
        self.model_type = model_type.lower()
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.enable_gpu = enable_gpu
        self.model = None
        self.loaded = False
        
        # 设置模型路径
        if model_path is None:
            self.model_path = DETECTION_CONFIG.get("model_path", "models/detection/default")
        else:
            self.model_path = model_path
        
        # 从环境变量获取模型路径（如果配置了）
        if self.model_path and self.model_path.startswith('$'):
            env_var = self.model_path[1:]
            env_path = os.environ.get(env_var)
            if env_path:
                self.model_path = env_path
        
        # 加载类别名称
        self.class_names = class_names or self._load_class_names()
        
        # 验证模型类型
        if self.model_type not in self.SUPPORTED_BACKENDS:
            logger.warning(f"不支持的检测模型类型: {self.model_type}，使用默认类型: opencv")
            self.model_type = "opencv"
        
        # 初始化模型
        self._initialize_model()
        logger.info(f"对象检测器初始化，类型: {self.model_type}, 置信度阈值: {self.confidence_threshold}")
    
    def _load_class_names(self) -> List[str]:
        """
        加载类别名称
        
        返回:
            类别名称列表
        """
        # 首先尝试从配置加载
        if "class_names" in DETECTION_CONFIG:
            return DETECTION_CONFIG["class_names"]
        
        # 然后尝试从文件加载
        class_file = None
        
        # 根据模型路径找到对应的类别文件
        if self.model_path:
            model_dir = os.path.dirname(self.model_path)
            
            # 尝试多种可能的类别文件名
            possible_names = [
                os.path.join(model_dir, "classes.txt"),
                os.path.join(model_dir, "classes.names"),
                os.path.join(model_dir, "coco.names"),
                os.path.join(model_dir, "labels.txt")
            ]
            
            for path in possible_names:
                if os.path.exists(path):
                    class_file = path
                    break
        
        # 如果找到类别文件，加载它
        if class_file and os.path.exists(class_file):
            try:
                with open(class_file, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            except Exception as e:
                logger.error(f"加载类别文件失败: {str(e)}")
        
        # 默认使用COCO数据集的80个类别
        return [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
            "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
            "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
        ]
    
    def _initialize_model(self):
        """初始化检测模型"""
        if self.model_type == "opencv":
            self._initialize_opencv_model()
        elif self.model_type == "yolo":
            self._initialize_yolo_model()
        elif self.model_type == "torch":
            self._initialize_torch_model()
        elif self.model_type == "custom":
            self._initialize_custom_model()
    
    def _initialize_opencv_model(self):
        """初始化OpenCV DNN模型"""
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法初始化OpenCV检测模型")
            return
        
        try:
            # 确保模型文件存在
            if not self.model_path or not os.path.exists(self.model_path):
                logger.error(f"模型文件不存在: {self.model_path}")
                return
            
            # 获取配置文件路径（假设与模型文件在同一目录）
            model_dir = os.path.dirname(self.model_path)
            model_name = os.path.basename(self.model_path)
            
            # 尝试找到配置文件
            config_path = None
            config_extensions = [".pbtxt", ".prototxt", ".cfg"]
            
            for ext in config_extensions:
                path = os.path.join(model_dir, os.path.splitext(model_name)[0] + ext)
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                logger.warning(f"未找到模型配置文件，尝试直接加载模型: {self.model_path}")
                
                # 尝试根据文件扩展名判断模型类型
                if self.model_path.endswith(".pb"):
                    # TensorFlow模型
                    self.model = cv2.dnn.readNetFromTensorflow(self.model_path)
                elif self.model_path.endswith((".caffemodel", ".prototxt")):
                    # Caffe模型
                    self.model = cv2.dnn.readNetFromCaffe(self.model_path)
                elif self.model_path.endswith((".weights", ".cfg")):
                    # Darknet模型
                    # 查找对应的cfg文件
                    weights_path = self.model_path
                    cfg_path = os.path.splitext(weights_path)[0] + ".cfg"
                    
                    if os.path.exists(cfg_path):
                        self.model = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
                    else:
                        logger.error(f"Darknet配置文件不存在: {cfg_path}")
                        return
                elif self.model_path.endswith((".onnx")):
                    # ONNX模型
                    self.model = cv2.dnn.readNetFromONNX(self.model_path)
                else:
                    logger.error(f"不支持的模型文件扩展名: {self.model_path}")
                    return
            else:
                # 根据配置文件和模型文件扩展名加载模型
                if config_path.endswith(".pbtxt"):
                    # TensorFlow模型
                    self.model = cv2.dnn.readNetFromTensorflow(self.model_path, config_path)
                elif config_path.endswith(".prototxt"):
                    # Caffe模型
                    self.model = cv2.dnn.readNetFromCaffe(config_path, self.model_path)
                elif config_path.endswith(".cfg"):
                    # Darknet模型
                    self.model = cv2.dnn.readNetFromDarknet(config_path, self.model_path)
                else:
                    logger.error(f"不支持的配置文件扩展名: {config_path}")
                    return
            
            # 设置目标设备
            if self.enable_gpu and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                logger.info("已启用GPU加速")
            else:
                self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            self.loaded = True
            logger.info(f"成功加载OpenCV DNN模型: {self.model_path}")
        
        except Exception as e:
            logger.error(f"初始化OpenCV DNN模型失败: {str(e)}")
            self.model = None
            self.loaded = False
    
    def _initialize_yolo_model(self):
        """初始化YOLO模型"""
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装，无法初始化YOLO检测模型")
            return
        
        try:
            # 确保模型文件存在
            if not self.model_path or not os.path.exists(self.model_path):
                logger.error(f"模型文件不存在: {self.model_path}")
                return
            
            # 获取配置文件路径
            model_dir = os.path.dirname(self.model_path)
            weights_path = self.model_path
            
            # 查找配置文件
            cfg_path = os.path.join(model_dir, os.path.splitext(os.path.basename(weights_path))[0] + ".cfg")
            if not os.path.exists(cfg_path):
                # 尝试在同目录下查找任何.cfg文件
                cfg_files = [f for f in os.listdir(model_dir) if f.endswith(".cfg")]
                if cfg_files:
                    cfg_path = os.path.join(model_dir, cfg_files[0])
                else:
                    logger.error(f"未找到YOLO配置文件")
                    return
            
            # 加载模型
            self.model = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
            
            # 获取输出层名称
            layer_names = self.model.getLayerNames()
            try:
                # OpenCV 4.5.4及以上版本
                self.output_layers = [layer_names[i - 1] for i in self.model.getUnconnectedOutLayers()]
            except:
                # OpenCV较低版本
                self.output_layers = [layer_names[i[0] - 1] for i in self.model.getUnconnectedOutLayers()]
            
            # 设置目标设备
            if self.enable_gpu and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                logger.info("已启用GPU加速")
            else:
                self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            self.loaded = True
            logger.info(f"成功加载YOLO模型: {self.model_path}")
        
        except Exception as e:
            logger.error(f"初始化YOLO模型失败: {str(e)}")
            self.model = None
            self.loaded = False
    
    def _initialize_torch_model(self):
        """初始化PyTorch模型"""
        if not TORCH_AVAILABLE:
            logger.error("PyTorch未安装，无法初始化Torch检测模型")
            return
        
        try:
            # 尝试导入相关库
            try:
                import torchvision
                from torchvision.models.detection import fasterrcnn_resnet50_fpn, retinanet_resnet50_fpn
            except ImportError:
                logger.error("torchvision未安装，无法加载预训练检测模型")
                return
            
            # 确定设备
            device = torch.device("cuda" if self.enable_gpu and torch.cuda.is_available() else "cpu")
            
            # 查找预训练模型名称或检查自定义模型路径
            if not self.model_path or self.model_path == "fasterrcnn_resnet50_fpn":
                # 使用预训练的Faster R-CNN
                self.model = fasterrcnn_resnet50_fpn(pretrained=True)
                logger.info("加载预训练的Faster R-CNN模型")
            elif self.model_path == "retinanet_resnet50_fpn":
                # 使用预训练的RetinaNet
                self.model = retinanet_resnet50_fpn(pretrained=True)
                logger.info("加载预训练的RetinaNet模型")
            elif os.path.exists(self.model_path):
                # 加载自定义保存的模型
                self.model = torch.load(self.model_path, map_location=device)
                logger.info(f"加载自定义PyTorch模型: {self.model_path}")
            else:
                logger.error(f"无效的PyTorch模型路径: {self.model_path}")
                return
            
            # 将模型移动到适当的设备并设置为评估模式
            self.model.to(device)
            self.model.eval()
            self.device = device
            
            self.loaded = True
            logger.info(f"成功初始化PyTorch检测模型，使用设备: {device}")
        
        except Exception as e:
            logger.error(f"初始化PyTorch模型失败: {str(e)}")
            self.model = None
            self.loaded = False
    
    def _initialize_custom_model(self):
        """初始化自定义模型"""
        try:
            # 检查模型路径
            if not self.model_path or not os.path.exists(self.model_path):
                logger.error(f"自定义模型文件不存在: {self.model_path}")
                return
            
            # 尝试加载自定义模型
            # 这里只是一个示例，实际实现取决于自定义模型的格式
            if self.model_path.endswith(".json"):
                # 假设这是一个JSON格式的自定义模型定义
                with open(self.model_path, 'r') as f:
                    model_def = json.load(f)
                
                model_type = model_def.get("type", "unknown")
                model_params = model_def.get("parameters", {})
                
                # 这里应该有更多的逻辑来处理不同类型的自定义模型
                logger.info(f"加载自定义模型，类型: {model_type}")
                
                # 作为示例，我们只设置一个标志表示模型已加载
                self.loaded = True
            
            elif self.model_path.endswith((".h5", ".hdf5")):
                # 尝试加载Keras模型
                try:
                    from tensorflow import keras
                    self.model = keras.models.load_model(self.model_path)
                    self.loaded = True
                    logger.info(f"成功加载Keras模型: {self.model_path}")
                except ImportError:
                    logger.error("TensorFlow/Keras未安装，无法加载.h5模型")
                    return
            
            else:
                logger.error(f"不支持的自定义模型格式: {self.model_path}")
                return
        
        except Exception as e:
            logger.error(f"初始化自定义模型失败: {str(e)}")
            self.model = None
            self.loaded = False
    
    def detect(self, image: np.ndarray) -> List[DetectionResult]:
        """
        检测图像中的对象
        
        参数:
            image: 输入图像
            
        返回:
            检测结果列表
        """
        if not self.loaded or self.model is None:
            logger.error("检测模型未加载，无法执行检测")
            return []
        
        if image is None or image.size == 0:
            logger.error("无法检测空图像")
            return []
        
        try:
            if self.model_type == "opencv":
                return self._detect_opencv(image)
            elif self.model_type == "yolo":
                return self._detect_yolo(image)
            elif self.model_type == "torch":
                return self._detect_torch(image)
            elif self.model_type == "custom":
                return self._detect_custom(image)
            else:
                logger.error(f"不支持的检测模型类型: {self.model_type}")
                return []
        
        except Exception as e:
            logger.error(f"执行对象检测失败: {str(e)}")
            return []
    
    def _detect_opencv(self, image: np.ndarray) -> List[DetectionResult]:
        """
        使用OpenCV DNN模型检测对象
        
        参数:
            image: 输入图像
            
        返回:
            检测结果列表
        """
        height, width = image.shape[:2]
        
        # 创建blob，并进行前向传递
        blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.model.setInput(blob)
        
        # 获取模型的输出层
        output_layers = self.model.getUnconnectedOutLayersNames()
        layer_outputs = self.model.forward(output_layers)
        
        # 处理检测结果
        class_ids = []
        confidences = []
        boxes = []
        
        for output in layer_outputs:
            for detection in output:
                # 提取类别ID和置信度
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    # 检测到对象，计算包围框
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # 左上角坐标
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(int(class_id))
        
        # 应用非极大值抑制
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
        
        # 创建结果对象
        results = []
        
        if len(indices) > 0:
            # OpenCV 4.x 和 OpenCV 3.x 返回的indices格式不同
            if isinstance(indices, tuple):
                # OpenCV 4.5.4 及以上版本
                indices = indices[0]
            
            for i in indices:
                # 处理不同版本的OpenCV索引格式
                if isinstance(i, (list, tuple, np.ndarray)):
                    i = i[0]
                
                box = boxes[i]
                x, y, w, h = box
                class_id = class_ids[i]
                confidence = confidences[i]
                
                # 获取类别名称
                class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                
                results.append(DetectionResult(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    x=x,
                    y=y,
                    width=w,
                    height=h
                ))
        
        return results
    
    def _detect_yolo(self, image: np.ndarray) -> List[DetectionResult]:
        """
        使用YOLO模型检测对象
        
        参数:
            image: 输入图像
            
        返回:
            检测结果列表
        """
        height, width = image.shape[:2]
        
        # 创建blob
        blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.model.setInput(blob)
        
        # 前向传递
        detections = self.model.forward(self.output_layers)
        
        # 处理检测结果
        class_ids = []
        confidences = []
        boxes = []
        
        for detection in detections:
            for obj in detection:
                scores = obj[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    # 检测到对象，计算包围框
                    center_x = int(obj[0] * width)
                    center_y = int(obj[1] * height)
                    w = int(obj[2] * width)
                    h = int(obj[3] * height)
                    
                    # 左上角坐标
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(int(class_id))
        
        # 应用非极大值抑制
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
        
        # 创建结果对象
        results = []
        
        if len(indices) > 0:
            # 处理不同版本的OpenCV索引格式
            if isinstance(indices, tuple):
                indices = indices[0]
            
            for i in indices:
                if isinstance(i, (list, tuple, np.ndarray)):
                    i = i[0]
                
                box = boxes[i]
                x, y, w, h = box
                class_id = class_ids[i]
                confidence = confidences[i]
                
                # 获取类别名称
                class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                
                results.append(DetectionResult(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    x=x,
                    y=y,
                    width=w,
                    height=h
                ))
        
        return results
    
    def _detect_torch(self, image: np.ndarray) -> List[DetectionResult]:
        """
        使用PyTorch模型检测对象
        
        参数:
            image: 输入图像
            
        返回:
            检测结果列表
        """
        if not TORCH_AVAILABLE:
            logger.error("PyTorch未安装，无法执行检测")
            return []
        
        try:
            import torch
            import torchvision.transforms as T
            
            # 转换图像为RGB（如果需要）
            if len(image.shape) > 2 and image.shape[2] == 3:
                # 假设输入是BGR（OpenCV默认）
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # 转换为PyTorch张量
            transform = T.Compose([
                T.ToTensor()
            ])
            tensor = transform(image_rgb).to(self.device)
            
            # 执行推理
            with torch.no_grad():
                predictions = self.model([tensor])
            
            # 处理结果
            results = []
            
            for i, pred in enumerate(predictions):
                boxes = pred['boxes'].cpu().numpy()
                scores = pred['scores'].cpu().numpy()
                labels = pred['labels'].cpu().numpy()
                
                for box, score, label in zip(boxes, scores, labels):
                    if score >= self.confidence_threshold:
                        x1, y1, x2, y2 = box.astype(int)
                        width = x2 - x1
                        height = y2 - y1
                        
                        # 获取类别名称
                        class_id = int(label)
                        class_name = self.class_names[class_id - 1] if class_id - 1 < len(self.class_names) else f"class_{class_id}"
                        
                        results.append(DetectionResult(
                            class_id=class_id,
                            class_name=class_name,
                            confidence=float(score),
                            x=int(x1),
                            y=int(y1),
                            width=int(width),
                            height=int(height)
                        ))
            
            return results
        
        except Exception as e:
            logger.error(f"PyTorch检测失败: {str(e)}")
            return []
    
    def _detect_custom(self, image: np.ndarray) -> List[DetectionResult]:
        """
        使用自定义模型检测对象
        
        参数:
            image: 输入图像
            
        返回:
            检测结果列表
        """
        # 这里应该实现自定义模型的推理逻辑
        # 作为示例，我们返回一个空列表
        logger.warning("自定义模型检测未实现")
        return []
    
    def draw_detections(self, image: np.ndarray, 
                        detections: List[DetectionResult],
                        draw_labels: bool = True,
                        color_map: Optional[Dict[int, Tuple[int, int, int]]] = None) -> np.ndarray:
        """
        在图像上绘制检测结果
        
        参数:
            image: 输入图像
            detections: 检测结果列表
            draw_labels: 是否绘制标签
            color_map: 类别ID到颜色的映射
            
        返回:
            绘制了检测结果的图像
        """
        if image is None or image.size == 0:
            logger.error("无法在空图像上绘制检测结果")
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        if not detections:
            return image.copy()
        
        # 创建图像副本
        result = image.copy()
        
        # 默认颜色映射
        if color_map is None:
            color_map = {}
        
        for detection in detections:
            # 获取颜色
            if detection.class_id in color_map:
                color = color_map[detection.class_id]
            else:
                # 为未映射的类别生成随机颜色
                color = (
                    np.random.randint(0, 255),
                    np.random.randint(0, 255),
                    np.random.randint(0, 255)
                )
                color_map[detection.class_id] = color
            
            # 绘制边界框
            x, y, w, h = detection.box
            cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
            
            # 绘制标签
            if draw_labels:
                confidence_text = f"{detection.confidence:.2f}"
                label = f"{detection.class_name}: {confidence_text}"
                
                # 获取文本尺寸
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                
                # 填充标签背景
                cv2.rectangle(
                    result,
                    (x, y - text_size[1] - 4),
                    (x + text_size[0], y),
                    color,
                    -1
                )
                
                # 绘制文本
                cv2.putText(
                    result,
                    label,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )
        
        return result
    
    def filter_detections(self, 
                         detections: List[DetectionResult],
                         class_ids: Optional[List[int]] = None,
                         min_confidence: Optional[float] = None,
                         min_size: Optional[int] = None,
                         max_results: Optional[int] = None) -> List[DetectionResult]:
        """
        过滤检测结果
        
        参数:
            detections: 检测结果列表
            class_ids: 要保留的类别ID列表
            min_confidence: 最小置信度
            min_size: 最小检测框面积
            max_results: 最大结果数量
            
        返回:
            过滤后的检测结果列表
        """
        if not detections:
            return []
        
        filtered = detections
        
        # 按类别ID过滤
        if class_ids is not None:
            filtered = [d for d in filtered if d.class_id in class_ids]
        
        # 按置信度过滤
        if min_confidence is not None:
            filtered = [d for d in filtered if d.confidence >= min_confidence]
        
        # 按尺寸过滤
        if min_size is not None:
            filtered = [d for d in filtered if d.area >= min_size]
        
        # 按置信度排序
        filtered.sort(key=lambda d: d.confidence, reverse=True)
        
        # 限制结果数量
        if max_results is not None and max_results > 0:
            filtered = filtered[:max_results]
        
        return filtered