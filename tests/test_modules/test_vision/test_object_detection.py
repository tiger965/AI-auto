import unittest
import os
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock

# 假设这是你的对象检测模块
# 如果实际导入路径不同，请相应调整
from vision.object_detector import ObjectDetector

class TestObjectDetection(unittest.TestCase):
    """对象检测模块测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试数据目录
        self.test_dir = Path("test_data")
        self.test_dir.mkdir(exist_ok=True)
        
        # 创建测试图像
        self.create_test_images()
        
        # 初始化对象检测器
        self.detector = ObjectDetector()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试数据
        for file in self.test_dir.glob("*"):
            file.unlink()
        self.test_dir.rmdir()
    
    def create_test_images(self):
        """创建用于测试的对象检测测试图像"""
        # 创建一个包含简单形状的测试图像
        # 这里创建一个带有几个矩形和圆形的图像作为测试
        img_size = (640, 480)
        img = np.zeros((img_size[1], img_size[0], 3), dtype=np.uint8)
        
        # 添加一些矩形
        cv2.rectangle(img, (100, 100), (200, 200), (0, 255, 0), -1)  # 绿色矩形
        cv2.rectangle(img, (300, 150), (450, 250), (0, 0, 255), -1)  # 红色矩形
        
        # 添加一些圆形
        cv2.circle(img, (500, 100), 50, (255, 0, 0), -1)  # 蓝色圆形
        cv2.circle(img, (150, 350), 70, (255, 255, 0), -1)  # 黄色圆形
        
        # 保存测试图像
        filepath = self.test_dir / "test_objects.jpg"
        cv2.imwrite(str(filepath), img)
        
        # 创建带有噪声的测试图像
        noisy_img = img.copy()
        noise = np.random.normal(0, 25, img.shape).astype(np.uint8)
        noisy_img = cv2.add(noisy_img, noise)
        filepath = self.test_dir / "test_objects_noisy.jpg"
        cv2.imwrite(str(filepath), noisy_img)
        
        # 创建低光照测试图像
        dark_img = np.clip(img.astype(np.int16) // 3, 0, 255).astype(np.uint8)
        filepath = self.test_dir / "test_objects_dark.jpg"
        cv2.imwrite(str(filepath), dark_img)
        
        # 创建模糊测试图像
        blurry_img = cv2.GaussianBlur(img, (15, 15), 0)
        filepath = self.test_dir / "test_objects_blurry.jpg"
        cv2.imwrite(str(filepath), blurry_img)
    
    def test_object_detection_basic(self):
        """测试基本对象检测功能"""
        test_file = str(self.test_dir / "test_objects.jpg")
        
        # 测试对象检测
        detections = self.detector.detect_objects(test_file)
        
        # 验证是否检测到了至少4个对象（2个矩形和2个圆形）
        self.assertGreaterEqual(len(detections), 4)
        
        # 验证检测结果的格式
        for detection in detections:
            # 每个检测结果应该包含类别、置信度和边界框
            self.assertIn('class', detection)
            self.assertIn('confidence', detection)
            self.assertIn('bbox', detection)
            
            # 验证边界框格式
            self.assertEqual(len(detection['bbox']), 4)
    
    def test_object_detection_with_threshold(self):
        """测试不同置信度阈值下的对象检测"""
        test_file = str(self.test_dir / "test_objects.jpg")
        
        # 使用不同的置信度阈值进行测试
        thresholds = [0.3, 0.5, 0.7, 0.9]
        
        for threshold in thresholds:
            detections = self.detector.detect_objects(test_file, confidence_threshold=threshold)
            
            # 验证所有检测结果的置信度都高于阈值
            for detection in detections:
                self.assertGreaterEqual(detection['confidence'], threshold)
    
    def test_noisy_image_detection(self):
        """测试在带噪声图像上的对象检测"""
        test_file = str(self.test_dir / "test_objects_noisy.jpg")
        
        # 在带噪声的图像上测试对象检测
        detections = self.detector.detect_objects(test_file)
        
        # 虽然噪声可能会影响检测结果，但应该仍能检测到一些对象
        self.assertGreater(len(detections), 0)
    
    def test_low_light_detection(self):
        """测试在低光照图像上的对象检测"""
        test_file = str(self.test_dir / "test_objects_dark.jpg")
        
        # 在低光照图像上测试对象检测
        detections = self.detector.detect_objects(test_file)
        
        # 低光照可能会影响检测结果，但应该仍能检测到一些对象
        self.assertGreater(len(detections), 0)
    
    def test_blurry_image_detection(self):
        """测试在模糊图像上的对象检测"""
        test_file = str(self.test_dir / "test_objects_blurry.jpg")
        
        # 在模糊图像上测试对象检测
        detections = self.detector.detect_objects(test_file)
        
        # 模糊可能会影响检测结果，但应该仍能检测到一些对象
        self.assertGreater(len(detections), 0)
    
    def test_detection_speed(self):
        """测试对象检测的速度"""
        import time
        
        test_file = str(self.test_dir / "test_objects.jpg")
        
        # 测量检测速度
        start_time = time.time()
        self.detector.detect_objects(test_file)
        detection_time = time.time() - start_time
        
        # 输出性能信息
        print(f"Object detection time: {detection_time:.4f}s")
        
        # 这里不做具体断言，只是记录性能信息
        # 在实际项目中，可以根据性能要求设置具体的断言
    
    @patch('vision.object_detector.ObjectDetector.detect_objects')
    def test_mock_detector(self, mock_detect):
        """使用模拟对象测试检测器集成"""
        # 设置模拟返回值
        mock_detect.return_value = [
            {'class': 'rectangle', 'confidence': 0.95, 'bbox': [100, 100, 200, 200]},
            {'class': 'circle', 'confidence': 0.90, 'bbox': [500, 100, 600, 200]}
        ]
        
        # 调用检测方法
        test_file = str(self.test_dir / "test_objects.jpg")
        detections = self.detector.detect_objects(test_file)
        
        # 验证模拟调用
        mock_detect.assert_called_once_with(test_file)
        
        # 验证返回结果
        self.assertEqual(len(detections), 2)
        self.assertEqual(detections[0]['class'], 'rectangle')
        self.assertEqual(detections[1]['class'], 'circle')
    
    def test_batch_detection(self):
        """测试批量对象检测功能"""
        # 获取所有测试图像
        test_files = [str(file) for file in self.test_dir.glob("*.jpg")]
        
        # 批量检测
        batch_results = self.detector.detect_objects_batch(test_files)
        
        # 验证结果
        self.assertEqual(len(batch_results), len(test_files))
        
        # 检查每个结果
        for result in batch_results:
            self.assertIsInstance(result, list)
    
    def test_specific_object_detection(self):
        """测试特定对象类别的检测"""
        test_file = str(self.test_dir / "test_objects.jpg")
        
        # 只检测矩形
        rectangles = self.detector.detect_objects(test_file, classes=['rectangle'])
        
        # 验证所有检测结果都是矩形
        for detection in rectangles:
            self.assertEqual(detection['class'], 'rectangle')
        
        # 只检测圆形
        circles = self.detector.detect_objects(test_file, classes=['circle'])
        
        # 验证所有检测结果都是圆形
        for detection in circles:
            self.assertEqual(detection['class'], 'circle')

if __name__ == "__main__":
    unittest.main()# 物体检测测试
