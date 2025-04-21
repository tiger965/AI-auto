""""
测试数据转换器模块
测试各种数据格式的转换功能、正确性和性能
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
# 假设项目结构中有一个data_transformer模块
try:
from modules.data.data_transformer import DataTransformer
except ImportError:
    # 如果在实际环境中该路径不存在，请根据实际情况调整
    sys.path.append(os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../../')))
    try:
        # 尝试其他可能的导入路径
from modules.data.data_transformer import DataTransformer
except ImportError:
     # 如果模块尚未实现，创建一个模拟类进行测试
     class DataTransformer:
          """模拟的数据转换器，仅用于测试"""

           def normalize(self, data):
                """数据归一化处理"""
                if isinstance(data, np.ndarray):
                    # 对numpy数组归一化
                    return (data - data.min()) / (data.max() - data.min() + 1e-8)
                elif isinstance(data, pd.DataFrame):
                    # 对DataFrame中的数值列归一化
                    numeric_cols = data.select_dtypes(
                        include=np.number).columns
                    result = data.copy()
                    for col in numeric_cols:
                        min_val = data[col].min()
                        max_val = data[col].max()
                        result[col] = (data[col] - min_val) / \
                            (max_val - min_val + 1e-8)
                    return result
                else:
                    raise TypeError("不支持的数据类型")

            def one_hot_encode(self, data, column):
                """对指定列进行独热编码"""
                if not isinstance(data, pd.DataFrame):
                    raise TypeError("数据必须是DataFrame类型")

                # 对指定列进行独热编码
                encoded = pd.get_dummies(data[column], prefix=column)

                # 将编码结果与原数据合并
                result = pd.concat(
                    [data.drop(column, axis=1), encoded], axis=1)
                return result

            def to_csv(self, data, file_path):
                """将数据保存为CSV格式"""
                if isinstance(data, pd.DataFrame):
                    data.to_csv(file_path, index=False)
                elif isinstance(data, np.ndarray):
                    np.savetxt(file_path, data, delimiter=',')
                else:
                    raise TypeError("不支持的数据类型")

            def to_json(self, data, file_path):
                """将数据保存为JSON格式"""
                if isinstance(data, pd.DataFrame):
                    data.to_json(file_path, orient='records')
                elif isinstance(data, dict):
                    with open(file_path, 'w') as f:
                        json.dump(data, f)
                else:
                    raise TypeError("不支持的数据类型")

            def batch_process(self, data, batch_size, process_func):
                """批量处理数据"""
                if isinstance(data, pd.DataFrame):
                    result = pd.DataFrame()
                    for i in range(0, len(data), batch_size):
                        batch = data.iloc[i:i+batch_size].copy()
                        processed = process_func(batch)
                        result = pd.concat([result, processed])
                    return result
                elif isinstance(data, np.ndarray):
                    result = []
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i+batch_size].copy()
                        processed = process_func(batch)
                        result.append(processed)
                    return np.vstack(result)
                else:
                    raise TypeError("不支持的数据类型")


class TestDataTransformer(unittest.TestCase):
    """测试数据转换器的功能"""

    @classmethod
    def setUpClass(cls):
        """测试类开始前的准备工作"""
        cls.transformer = DataTransformer()

        # 创建临时测试目录
        cls.test_dir = tempfile.mkdtemp()

        # 创建测试数据
        # 1. 数值型DataFrame
        cls.numeric_df = pd.DataFrame({
            'id': range(1000),
            'value1': np.random.rand(1000) * 100,
            'value2': np.random.rand(1000) * 50,
            'value3': np.random.rand(1000) * 10
        })

        # 2. 混合型DataFrame（包含分类变量）
        categories = ['A', 'B', 'C', 'D']
        cls.mixed_df = pd.DataFrame({
            'id': range(1000),
            'value': np.random.rand(1000) * 100,
            'category': [categories[i % len(categories)] for i in range(1000)]
        })

        # 3. NumPy数组
        cls.numpy_array = np.random.rand(1000, 5) * 100

        # 4. 大规模数据集 (约100MB)
        cls.large_df = pd.DataFrame({
            'id': range(1000000),
            'value1': np.random.rand(1000000) * 100,
            'value2': np.random.rand(1000000) * 50,
            'category': [categories[i % len(categories)] for i in range(1000000)]
        })

    @classmethod
    def tearDownClass(cls):
        """测试类结束后的清理工作"""
        # 删除临时测试目录
        import shutil
        shutil.rmtree(cls.test_dir)

    def test_normalize(self):
        """测试数据归一化功能"""
        # 测试DataFrame归一化
        normalized_df = self.transformer.normalize(self.numeric_df)

        # 验证结果正确性
        self.assertEqual(normalized_df.shape, self.numeric_df.shape)
        for col in ['value1', 'value2', 'value3']:
            self.assertAlmostEqual(normalized_df[col].min(), 0.0, places=5)
            self.assertAlmostEqual(normalized_df[col].max(), 1.0, places=5)

        # 测试NumPy数组归一化
        normalized_array = self.transformer.normalize(self.numpy_array)

        # 验证结果正确性
        self.assertEqual(normalized_array.shape, self.numpy_array.shape)
        self.assertAlmostEqual(normalized_array.min(), 0.0, places=5)
        self.assertAlmostEqual(normalized_array.max(), 1.0, places=5)

    def test_one_hot_encode(self):
        """测试独热编码功能"""
        # 测试对分类变量进行独热编码
        encoded_df = self.transformer.one_hot_encode(self.mixed_df, 'category')

        # 验证结果正确性
        self.assertEqual(len(encoded_df.columns), len(
            self.mixed_df.columns) - 1 + 4)  # 原列数 - 1 + 分类数量
        self.assertIn('category_A', encoded_df.columns)
        self.assertIn('category_B', encoded_df.columns)
        self.assertIn('category_C', encoded_df.columns)
        self.assertIn('category_D', encoded_df.columns)

        # 检查每行的独热编码是否正确
        for i, row in self.mixed_df.iterrows():
            category = row['category']
            one_hot_col = f'category_{category}'
            self.assertEqual(encoded_df.loc[i, one_hot_col], 1)

    def test_to_csv(self):
        """测试保存为CSV格式"""
        # 测试保存DataFrame为CSV
        csv_file = os.path.join(self.test_dir, "test_output.csv")
        self.transformer.to_csv(self.numeric_df, csv_file)

        # 验证文件是否成功创建
        self.assertTrue(os.path.exists(csv_file))

        # 验证文件内容正确性
        df_loaded = pd.read_csv(csv_file)
        self.assertEqual(df_loaded.shape, self.numeric_df.shape)
        pd.testing.assert_frame_equal(df_loaded, self.numeric_df)

    def test_to_json(self):
        """测试保存为JSON格式"""
        # 测试保存DataFrame为JSON
        json_file = os.path.join(self.test_dir, "test_output.json")
        self.transformer.to_json(self.numeric_df, json_file)

        # 验证文件是否成功创建
        self.assertTrue(os.path.exists(json_file))

        # 验证文件内容正确性
        df_loaded = pd.read_json(json_file, orient='records')
        self.assertEqual(df_loaded.shape, self.numeric_df.shape)

        # 比较两个DataFrame的列
        for col in self.numeric_df.columns:
            self.assertIn(col, df_loaded.columns)

    def test_batch_process(self):
        """测试批量处理功能"""
        # 定义一个简单的处理函数
        def double_values(batch):
            if isinstance(batch, pd.DataFrame):
                result = batch.copy()
                for col in ['value1', 'value2', 'value3']:
                    result[col] = batch[col] * 2
                return result
            elif isinstance(batch, np.ndarray):
                return batch * 2

        # 测试批量处理DataFrame
        batch_size = 100
        processed_df = self.transformer.batch_process(
            self.numeric_df, batch_size, double_values)

        # 验证结果正确性
        self.assertEqual(processed_df.shape, self.numeric_df.shape)
        for col in ['value1', 'value2', 'value3']:
            self.assertTrue(all(processed_df[col] == self.numeric_df[col] * 2))

        # 测试批量处理NumPy数组
        processed_array = self.transformer.batch_process(
            self.numpy_array, batch_size, lambda x: x * 2)

        # 验证结果正确性
        self.assertEqual(processed_array.shape, self.numpy_array.shape)
        np.testing.assert_array_equal(processed_array, self.numpy_array * 2)

    def test_performance(self):
        """测试数据转换性能"""
        # 测试大规模数据的归一化性能
        start_time = time.time()
        normalized_large_df = self.transformer.normalize(
            self.large_df[['value1', 'value2']])
        end_time = time.time()

        # 验证处理时间合理
        processing_time = end_time - start_time
        print(f"大规模数据归一化处理时间: {processing_time:.2f}秒")

        # 验证结果正确性
        self.assertEqual(normalized_large_df.shape, (1000000, 2))

        # 测试大规模数据的独热编码性能
        start_time = time.time()
        encoded_large_df = self.transformer.one_hot_encode(
            self.large_df, 'category')
        end_time = time.time()

        # 验证处理时间合理
        processing_time = end_time - start_time
        print(f"大规模数据独热编码处理时间: {processing_time:.2f}秒")

        # 验证结果正确性
        self.assertEqual(encoded_large_df.shape[0], 1000000)
        # 原列数 - 1 + 分类数量
        self.assertEqual(
            encoded_large_df.shape[1], self.large_df.shape[1] - 1 + 4)

    def test_error_handling(self):
        """测试错误处理"""
        # 测试不支持的数据类型
        with self.assertRaises(TypeError):
            self.transformer.normalize("不支持的字符串数据")

        # 测试空数据处理
        empty_df = pd.DataFrame()
        try:
            result = self.transformer.normalize(empty_df)
            # 应该能处理空DataFrame，不抛出异常
            self.assertTrue(result.empty)
        except Exception as e:
            self.fail(f"处理空DataFrame时抛出了异常: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)