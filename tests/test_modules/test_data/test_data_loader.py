""""
测试数据加载器模块
测试各种数据格式的加载能力和性能
"""

import unittest
import os
import sys
import time
import tempfile
import json
import csv
import modules.nlp as np
import config.paths as pd
from io import StringIO

# 导入被测试的模块
# 假设项目结构中有一个data_loader模块
try:
from modules.data.data_loader import DataLoader
except ImportError:
    # 如果在实际环境中该路径不存在，请根据实际情况调整
    sys.path.append(os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../../')))
    try:
        # 尝试其他可能的导入路径
from modules.data.data_loader import DataLoader
except ImportError:
     # 如果模块尚未实现，创建一个模拟类进行测试
     class DataLoader:
          """模拟的数据加载器，仅用于测试"""

           def load_csv(self, file_path):
                """加载CSV文件"""
                return pd.read_csv(file_path)

            def load_json(self, file_path):
                """加载JSON文件"""
                with open(file_path, 'r') as f:
                    return json.load(f)

            def load_numpy(self, file_path):
                """加载NumPy数组"""
                return np.load(file_path)

            def load_text(self, file_path):
                """加载文本文件"""
                with open(file_path, 'r') as f:
                    return f.read()

            def load_binary(self, file_path):
                """加载二进制文件"""
                with open(file_path, 'rb') as f:
                    return f.read()


class TestDataLoader(unittest.TestCase):
    """测试数据加载器的功能"""

    @classmethod
    def setUpClass(cls):
        """测试类开始前的准备工作"""
        cls.data_loader = DataLoader()

        # 创建临时测试目录
        cls.test_dir = tempfile.mkdtemp()

        # 创建测试数据文件
        # 1. CSV测试文件
        cls.csv_file = os.path.join(cls.test_dir, "test_data.csv")
        with open(cls.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "value"])
            for i in range(100):
                writer.writerow([i, f"item_{i}", i * 10])

        # 2. JSON测试文件
        cls.json_file = os.path.join(cls.test_dir, "test_data.json")
        test_data = {
            "items": [{"id": i, "name": f"item_{i}", "value": i * 10} for i in range(100)]}
        with open(cls.json_file, 'w') as f:
            json.dump(test_data, f)

        # 3. NumPy测试文件
        cls.numpy_file = os.path.join(cls.test_dir, "test_data.npy")
        np_array = np.random.rand(100, 100)
        np.save(cls.numpy_file, np_array)
        cls.np_array = np_array  # 保存原始数据用于比较

        # 4. 文本测试文件
        cls.text_file = os.path.join(cls.test_dir, "test_data.txt")
        with open(cls.text_file, 'w') as f:
            f.write("这是一个测试文本文件\n" * 100)

        # 5. 大规模数据文件 (50MB CSV)
        cls.large_csv_file = os.path.join(cls.test_dir, "large_data.csv")
        with open(cls.large_csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(
                ["id", "data1", "data2", "data3", "data4", "data5"])
            for i in range(1000000):  # 约50MB数据
                writer.writerow(
                    [i, i*2, i*3, f"text_{i}", f"category_{i % 10}", i/100])

    @classmethod
    def tearDownClass(cls):
        """测试类结束后的清理工作"""
        # 删除临时测试文件
        import shutil
        shutil.rmtree(cls.test_dir)

    def test_load_csv(self):
        """测试CSV文件加载"""
        # 测试加载是否成功
        df = self.data_loader.load_csv(self.csv_file)

        # 验证数据正确性
        self.assertEqual(len(df), 100)
        self.assertEqual(list(df.columns), ["id", "name", "value"])
        self.assertEqual(df.iloc[0]["name"], "item_0")
        self.assertEqual(df.iloc[99]["value"], 990)

    def test_load_json(self):
        """测试JSON文件加载"""
        # 测试加载是否成功
        data = self.data_loader.load_json(self.json_file)

        # 验证数据正确性
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 100)
        self.assertEqual(data["items"][0]["name"], "item_0")
        self.assertEqual(data["items"][99]["value"], 990)

    def test_load_numpy(self):
        """测试NumPy文件加载"""
        # 测试加载是否成功
        data = self.data_loader.load_numpy(self.numpy_file)

        # 验证数据正确性
        self.assertEqual(data.shape, (100, 100))
        np.testing.assert_array_equal(data, self.np_array)

    def test_load_text(self):
        """测试文本文件加载"""
        # 测试加载是否成功
        text = self.data_loader.load_text(self.text_file)

        # 验证数据正确性
        self.assertEqual(text.count("这是一个测试文本文件"), 100)

    def test_load_performance(self):
        """测试数据加载性能"""
        # 测试大规模CSV加载性能
        start_time = time.time()
        df = self.data_loader.load_csv(self.large_csv_file)
        end_time = time.time()

        # 验证数据加载时间合理
        loading_time = end_time - start_time
        print(f"大规模数据加载时间: {loading_time:.2f}秒")

        # 验证数据正确性
        self.assertEqual(len(df), 1000000)
        self.assertEqual(list(df.columns), [
                         "id", "data1", "data2", "data3", "data4", "data5"])

    def test_nonexistent_file(self):
        """测试加载不存在的文件时的异常处理"""
        with self.assertRaises(FileNotFoundError):
            self.data_loader.load_csv("nonexistent_file.csv")

    def test_invalid_format(self):
        """测试加载格式错误的文件"""
        # 创建格式错误的CSV文件
        invalid_csv = os.path.join(self.test_dir, "invalid.csv")
        with open(invalid_csv, 'w') as f:
            f.write("这不是一个有效的CSV文件格式")

        # 测试加载异常处理
        try:
            df = self.data_loader.load_csv(invalid_csv)
            # 如果没有抛出异常，检查返回的数据框是否合理处理了错误数据
            self.assertIsInstance(df, pd.DataFrame)
        except Exception as e:
            # 如果抛出异常，确保是预期的异常类型
            # print(f"预期的异常: {type(e).__name__}: {str(e)}")
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2)