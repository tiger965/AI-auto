"""
分词器测试模块
测试NLP分词功能在多种语言和场景下的正确性
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock

# 假设我们的主模块中有一个nlp包，包含tokenizer模块
from app.nlp.tokenizer import Tokenizer

class TestTokenizer(unittest.TestCase):
    """测试分词器的各项功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.tokenizer = Tokenizer()
        
        # 创建多语言测试数据集
        self.test_texts = {
            'chinese': '自然语言处理是人工智能的重要分支',
            'english': 'Natural language processing is a crucial branch of artificial intelligence',
            'mixed': 'AI技术development正在迅速evolving',
            'special_chars': 'Test with special characters: !@#$%^&*()',
            'numbers': 'NLP在2025年将有20%的增长率',
            'empty': ''
        }
        
        # 保存测试数据到文件
        test_data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'tokenizer_test_data.json')
        os.makedirs(os.path.dirname(test_data_path), exist_ok=True)
        with open(test_data_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_texts, f, ensure_ascii=False, indent=2)
    
    def test_tokenize_chinese(self):
        """测试中文分词功能"""
        tokens = self.tokenizer.tokenize(self.test_texts['chinese'])
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        self.assertIn('自然语言处理', tokens)
        
    def test_tokenize_english(self):
        """测试英文分词功能"""
        tokens = self.tokenizer.tokenize(self.test_texts['english'])
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        self.assertIn('natural', tokens)
        self.assertIn('language', tokens)
        self.assertIn('processing', tokens)
        
    def test_tokenize_mixed(self):
        """测试混合语言分词功能"""
        tokens = self.tokenizer.tokenize(self.test_texts['mixed'])
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        self.assertIn('AI', tokens)
        self.assertIn('技术', tokens)
        self.assertIn('development', tokens)
        
    def test_tokenize_special_chars(self):
        """测试带有特殊字符的文本分词"""
        tokens = self.tokenizer.tokenize(self.test_texts['special_chars'])
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        
    def test_tokenize_empty(self):
        """测试空字符串分词"""
        tokens = self.tokenizer.tokenize(self.test_texts['empty'])
        self.assertIsInstance(tokens, list)
        self.assertEqual(len(tokens), 0)
        
    def test_tokenize_with_custom_config(self):
        """测试使用自定义配置的分词"""
        config = {'lowercase': True, 'remove_punctuation': True}
        tokens = self.tokenizer.tokenize(self.test_texts['english'], config=config)
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        # 检查是否小写化
        for token in tokens:
            self.assertEqual(token, token.lower())
    
    @patch('app.nlp.tokenizer.Tokenizer._load_model')
    def test_model_loading(self, mock_load):
        """测试模型加载功能"""
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        
        tokenizer = Tokenizer(model_name='custom_model')
        mock_load.assert_called_once_with('custom_model')
        self.assertEqual(tokenizer.model, mock_model)
        
    def test_tokenize_benchmark(self):
        """基准测试分词性能"""
        import time
        
        start_time = time.time()
        for _ in range(100):
            self.tokenizer.tokenize(self.test_texts['chinese'])
        chinese_time = time.time() - start_time
        
        start_time = time.time()
        for _ in range(100):
            self.tokenizer.tokenize(self.test_texts['english'])
        english_time = time.time() - start_time
        
        # 记录性能指标
        print(f"分词性能基准测试: 中文: {chinese_time:.4f}秒, 英文: {english_time:.4f}秒")
        
        # 确保性能在可接受范围内
        self.assertLess(chinese_time, 5.0, "中文分词性能测试超时")
        self.assertLess(english_time, 5.0, "英文分词性能测试超时")
        
if __name__ == '__main__':
    unittest.main()