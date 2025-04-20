"""
嵌入测试模块
测试文本向量嵌入功能的准确性和一致性
"""

import unittest
import numpy as np
import os
import json
import pickle
from unittest.mock import patch, MagicMock

# 假设我们的主模块中有一个nlp包，包含embedding模块
from app.nlp.embedding import TextEmbedding

class TestEmbedding(unittest.TestCase):
    """测试文本嵌入功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.embedding_model = TextEmbedding()
        
        # 创建测试数据
        self.test_texts = {
            'simple': '人工智能',
            'sentence': '自然语言处理是人工智能的重要分支',
            'paragraph': '深度学习模型在自然语言处理任务中表现出色。通过Transformer架构，模型能够理解上下文信息并生成流畅的回复。',
            'multi_lang': ['Artificial intelligence', '人工智能', 'Intelligence artificielle'],
            'similar_pairs': [
                ('自然语言处理', '计算语言学'),
                ('深度学习', '机器学习'),
                ('图像识别', '计算机视觉')
            ]
        }
        
        # 保存测试数据
        test_data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'embedding_test_data.json')
        os.makedirs(os.path.dirname(test_data_path), exist_ok=True)
        
        # 将不可JSON序列化的数据转为可序列化格式
        serializable_data = {k: v for k, v in self.test_texts.items() if k != 'similar_pairs'}
        serializable_data['similar_pairs'] = [list(pair) for pair in self.test_texts['similar_pairs']]
        
        with open(test_data_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        # 预计算并缓存一些嵌入结果用于一致性测试
        self.cached_embeddings = {}
        for key in ['simple', 'sentence']:
            self.cached_embeddings[key] = self.embedding_model.get_embedding(self.test_texts[key])
        
        cached_emb_path = os.path.join(os.path.dirname(__file__), 'test_data', 'cached_embeddings.pkl')
        with open(cached_emb_path, 'wb') as f:
            pickle.dump(self.cached_embeddings, f)
    
    def test_embedding_output_shape(self):
        """测试嵌入输出维度"""
        embedding = self.embedding_model.get_embedding(self.test_texts['simple'])
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (self.embedding_model.dimension,))
        
        # 测试批量嵌入
        embeddings = self.embedding_model.get_embeddings(self.test_texts['multi_lang'])
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape, (len(self.test_texts['multi_lang']), self.embedding_model.dimension))
    
    def test_embedding_consistency(self):
        """测试嵌入结果的一致性"""
        # 同一段文本多次嵌入应该得到相同的结果
        emb1 = self.embedding_model.get_embedding(self.test_texts['simple'])
        emb2 = self.embedding_model.get_embedding(self.test_texts['simple'])
        np.testing.assert_allclose(emb1, emb2, rtol=1e-5)
        
        # 与缓存的嵌入结果对比
        for key in self.cached_embeddings:
            current_emb = self.embedding_model.get_embedding(self.test_texts[key])
            np.testing.assert_allclose(current_emb, self.cached_embeddings[key], rtol=1e-5)
    
    def test_embedding_similarity(self):
        """测试嵌入相似度计算"""
        for text1, text2 in self.test_texts['similar_pairs']:
            emb1 = self.embedding_model.get_embedding(text1)
            emb2 = self.embedding_model.get_embedding(text2)
            
            # 计算余弦相似度
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            # 相似文本的嵌入应该有较高相似度
            self.assertGreater(similarity, 0.5, f"'{text1}'和'{text2}'的嵌入相似度太低: {similarity}")
    
    def test_multilingual_embeddings(self):
        """测试多语言嵌入空间一致性"""
        # 获取同一个概念的不同语言表示的嵌入
        embeddings = self.embedding_model.get_embeddings(self.test_texts['multi_lang'])
        
        # 计算它们之间的相似度矩阵
        n = len(embeddings)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                similarity_matrix[i][j] = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
        
        # 确认所有语言表示的相似度都较高（不低于0.6）
        for i in range(n):
            for j in range(n):
                if i != j:
                    self.assertGreater(
                        similarity_matrix[i][j], 
                        0.6, 
                        f"'{self.test_texts['multi_lang'][i]}'和'{self.test_texts['multi_lang'][j]}'的跨语言嵌入相似度太低"
                    )
    
    def test_embedding_normalization(self):
        """测试嵌入向量归一化"""
        emb = self.embedding_model.get_embedding(self.test_texts['simple'], normalize=True)
        # 归一化后的向量范数应约等于1
        self.assertAlmostEqual(np.linalg.norm(emb), 1.0, places=6)
    
    @patch('app.nlp.embedding.TextEmbedding._load_model')
    def test_model_loading(self, mock_load):
        """测试模型加载功能"""
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        
        embedding_model = TextEmbedding(model_name='custom_model')
        mock_load.assert_called_once_with('custom_model')
        self.assertEqual(embedding_model.model, mock_model)
    
    def test_embedding_benchmark(self):
        """基准测试嵌入性能"""
        import time
        
        # 单个短文本
        start_time = time.time()
        for _ in range(20):
            self.embedding_model.get_embedding(self.test_texts['simple'])
        simple_time = time.time() - start_time
        
        # 长段落
        start_time = time.time()
        for _ in range(20):
            self.embedding_model.get_embedding(self.test_texts['paragraph'])
        paragraph_time = time.time() - start_time
        
        # 批量嵌入
        start_time = time.time()
        for _ in range(20):
            self.embedding_model.get_embeddings(self.test_texts['multi_lang'])
        batch_time = time.time() - start_time
        
        # 记录性能指标
        print(f"嵌入性能基准测试: 短文本: {simple_time:.4f}秒, 长段落: {paragraph_time:.4f}秒, 批量: {batch_time:.4f}秒")
        
        # 确保性能在可接受范围内
        self.assertLess(simple_time, 3.0, "短文本嵌入性能测试超时")
        self.assertLess(paragraph_time, 5.0, "段落嵌入性能测试超时")
        self.assertLess(batch_time, 8.0, "批量嵌入性能测试超时")
        
if __name__ == '__main__':
    unittest.main()