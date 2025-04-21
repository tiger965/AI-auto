import unittest
import os
import modules.nlp as np
import ui.cli
from pathlib import Path
from unittest.mock import patch, MagicMock

# 假设这是你的图像处理模块
# 如果实际导入路径不同，请相应调整
from modules.vision.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    """图像处理模块测试类"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建测试数据目录
        self.test_dir = Path("test_data")
        self.test_dir.mkdir(exist_ok=True)

        # 创建各种格式和尺寸的测试图像
        self.create_test_images()

        # 初始化图像处理器
        self.image_processor = ImageProcessor()

    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试数据
        for file in self.test_dir.glob("*"):
            file.unlink()
        self.test_dir.rmdir()

    def create_test_images(self):
        """创建用于测试的各种图像"""
        # 创建不同尺寸和格式的测试图像
        sizes = [(640, 480), (1280, 720), (1920, 1080), (320, 240)]
        formats = ["jpg", "png", "bmp"]

        for size in sizes:
            for fmt in formats:
                # 创建一个随机颜色的测试图像
                img = np.random.randint(
                    0, 255, (size[1], size[0], 3), dtype=np.uint8)
                filename = f"test_{size[0]}x{size[1]}.{fmt}"
                filepath = self.test_dir / filename
                cv2.imwrite(str(filepath), img)

    def test_load_image(self):
        """测试加载不同格式的图像"""
        formats = ["jpg", "png", "bmp"]
        for fmt in formats:
            test_file = str(self.test_dir / f"test_640x480.{fmt}")
            img = self.image_processor.load_image(test_file)

            # 验证图像是否正确加载
            self.assertIsNotNone(img)
            self.assertEqual(img.shape[:2], (480, 640))

    def test_resize_image(self):
        """测试图像大小调整功能"""
        test_file = str(self.test_dir / "test_1280x720.jpg")
        img = self.image_processor.load_image(test_file)

        # 测试不同的目标尺寸
        target_sizes = [(640, 360), (320, 180), (1920, 1080)]
        for target_size in target_sizes:
            resized = self.image_processor.resize(img, target_size)
            # 验证调整后的图像尺寸是否正确
            self.assertEqual(resized.shape[1::-1], target_size)

    def test_convert_color(self):
        """测试颜色空间转换"""
        test_file = str(self.test_dir / "test_640x480.jpg")
        img = self.image_processor.load_image(test_file)

        # 测试RGB到灰度转换
        gray = self.image_processor.convert_to_grayscale(img)
        self.assertEqual(len(gray.shape), 2)  # 灰度图是二维的

        # 测试灰度到RGB转换
        rgb = self.image_processor.convert_to_rgb(gray)
        self.assertEqual(len(rgb.shape), 3)  # RGB是三维的

    def test_apply_filter(self):
        """测试图像滤波功能"""
        test_file = str(self.test_dir / "test_640x480.jpg")
        img = self.image_processor.load_image(test_file)

        # 测试高斯模糊
        blurred = self.image_processor.apply_gaussian_blur(
            img, kernel_size=(5, 5))
        self.assertEqual(blurred.shape, img.shape)

        # 测试中值滤波
        median_filtered = self.image_processor.apply_median_filter(
            img, kernel_size=5)
        self.assertEqual(median_filtered.shape, img.shape)

    def test_edge_detection(self):
        """测试边缘检测功能"""
        test_file = str(self.test_dir / "test_640x480.jpg")
        img = self.image_processor.load_image(test_file)

        # 转换为灰度图像
        gray = self.image_processor.convert_to_grayscale(img)

        # 测试Canny边缘检测
        edges = self.image_processor.detect_edges(
            gray, low_threshold=50, high_threshold=150
        )
        self.assertEqual(edges.shape, gray.shape)

    def test_image_enhancement(self):
        """测试图像增强功能"""
        test_file = str(self.test_dir / "test_640x480.jpg")
        img = self.image_processor.load_image(test_file)

        # 测试直方图均衡化
        enhanced = self.image_processor.enhance_contrast(img)
        self.assertEqual(enhanced.shape, img.shape)

    def test_save_image(self):
        """测试图像保存功能"""
        test_file = str(self.test_dir / "test_640x480.jpg")
        img = self.image_processor.load_image(test_file)

        # 测试不同格式的保存
        formats = ["jpg", "png", "bmp"]
        for fmt in formats:
            output_file = str(self.test_dir / f"output.{fmt}")
            self.image_processor.save_image(img, output_file)

            # 验证文件是否存在
            self.assertTrue(os.path.exists(output_file))

            # 验证保存后的图像是否可以正确加载
            saved_img = self.image_processor.load_image(output_file)
            self.assertIsNotNone(saved_img)
            self.assertEqual(saved_img.shape, img.shape)

    def test_performance(self):
        """测试处理性能"""
        import time

        # 使用大图像进行性能测试
        test_file = str(self.test_dir / "test_1920x1080.jpg")

        # 测量加载时间
        start_time = time.time()
        img = self.image_processor.load_image(test_file)
        load_time = time.time() - start_time

        # 测量调整大小的时间
        start_time = time.time()
        self.image_processor.resize(img, (640, 360))
        resize_time = time.time() - start_time

        # 输出性能信息
        print(
            f"Performance - Load: {load_time:.4f}s, Resize: {resize_time:.4f}s")

        # 这里不做具体断言，只是记录性能信息
        # 在实际项目中，可以根据性能要求设置具体的断言


if __name__ == "__main__":
    unittest.main()  # 图像处理测试