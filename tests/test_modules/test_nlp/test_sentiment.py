"""
情感分析测试模块
测试NLP情感分析功能在多种语言和场景下的准确性
"""

import unittest
import os
import json
import numpy as np
from unittest.mock import patch, MagicMock

# 假设我们的主模块中有一个nlp包，包含sentiment模块
from app.nlp.sentiment import SentimentAnalyzer

class TestSentimentAnalysis(unittest.TestCase):
    """测试情感分析功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # 创建多语言情感测试数据集
        self.test_data = {
            'chinese': {
                'positive': [
                    '这个产品非常好用，我很满意',
                    '服务态度很好，体验极佳',
                    '新功能让使用体验提升了很多'
                ],
                'neutral': [
                    '这个产品有优点也有缺点',
                    '使用起来一般般，没什么特别的',
                    '产品功能基本符合预期'
                ],
                'negative': [
                    '质量太差了，很失望',
                    '客服态度恶劣，不会再购买',
                    '操作太复杂，体验很糟糕'
                ]
            },
            'english': {
                'positive': [
                    'This product is excellent and I am very satisfied',
                    'The service was outstanding and the experience was great',
                    'The new features have greatly improved the user experience'
                ],
                'neutral': [
                    'This product has both pros and cons',
                    'It works okay, nothing special',
                    'The functionality meets basic expectations'
                ],
                'negative': [
                    'The quality is terrible, very disappointing',
                    'Customer service was awful, will not purchase again',
                    'Too complicated to use, terrible experience'
                ]
            },
            'mixed': [
                '整体来说product quality还不错，但价格有点贵',
                'The interface界面设计很漂亮，但functionality功能不够完善',
                '我觉得这个app is just average, nothing special'
            ],
            'complex': [
                '虽然产品有一些小缺点，但总体来说还是非常好的',
                '尽管客服回应较慢，但问题最终得到了完美解决，非常感谢',
                'Despite initial problems, the overall experience was positive'
            ]
        }
        
        # 保存测试数据
        test_data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'sentiment_test_data.json')
        os.makedirs(os.path.dirname(test_data_path), exist_ok=True)
        with open(test_data_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, ensure_ascii=False, indent=2)
    
    def test_sentiment_classification_chinese(self):
        """测试中文情感分类"""
        for sentiment, texts in self.test_data['chinese'].items():
            for text in texts:
                result = self.sentiment_analyzer.analyze(text)
                self.assertIn('sentiment', result)
                self.assertEqual(result['sentiment'], sentiment, f"中文文本'{text}'情感分析错误")
                self.assertIn('confidence', result)
                self.assertGreater(result['confidence'], 0.6, f"中文文本'{text}'情感分析置信度过低")
    
    def test_sentiment_classification_english(self):
        """测试英文情感分类"""
        for sentiment, texts in self.test_data['english'].items():
            for text in texts:
                result = self.sentiment_analyzer.analyze(text)
                self.assertIn('sentiment', result)
                self.assertEqual(result['sentiment'], sentiment, f"英文文本'{text}'情感分析错误")
                self.assertIn('confidence', result)
                self.assertGreater(result['confidence'], 0.6, f"英文文本'{text}'情感分析置信度过低")
    
    def test_sentiment_classification_mixed(self):
        """测试混合语言情感分类"""
        for text in self.test_data['mixed']:
            result = self.sentiment_analyzer.analyze(text)
            self.assertIn('sentiment', result)
            self.assertIn(result['sentiment'], ['positive', 'neutral', 'negative'])
            self.assertIn('confidence', result)
            # 混合语言文本可能置信度较低，但应该有基本的分析能力
            self.assertGreater(result['confidence'], 0.5)
    
    def test_sentiment_classification_complex(self):
        """测试复杂情感场景分类"""
        for text in self.test_data['complex']:
            result = self.sentiment_analyzer.analyze(text)
            self.assertIn('sentiment', result)
            # 这些复杂的例子应该被识别为正面情感
            self.assertEqual(result['sentiment'], 'positive', f"复杂情感文本'{text}'分析错误")
    
    def test_sentiment_intensity(self):
        """测试情感强度分析"""
        # 简单句子的情感强度测试
        weak_positive = '这个产品还不错'
        strong_positive = '这个产品太棒了，超级满意！！！'
        
        weak_result = self.sentiment_analyzer.analyze(weak_positive, include_intensity=True)
        strong_result = self.sentiment_analyzer.analyze(strong_positive, include_intensity=True)
        
        self.assertIn('intensity', weak_result)
        self.assertIn('intensity', strong_result)
        self.assertGreater(strong_result['intensity'], weak_result['intensity'],
                          "强烈情感文本的强度应高于弱情感文本")
    
    def test_sentiment_aspects(self):
        """测试方面级情感分析"""
        text = "手机屏幕很棒，但电池续航很差，相机性能一般"
        result = self.sentiment_analyzer.analyze_aspects(text)
        
        self.assertIsInstance(result, dict)
        self.assertIn('aspects', result)
        self.assertIsInstance(result['aspects'], list)
        
        # 验证识别出的方面
        aspects = {aspect['name']: aspect['sentiment'] for aspect in result['aspects']}
        self.assertIn('屏幕', aspects)
        self.assertIn('电池续航', aspects)
        self.assertIn('相机', aspects)
        
        # 验证各方面的情感极性
        self.assertEqual(aspects['屏幕'], 'positive')
        self.assertEqual(aspects['电池续航'], 'negative')
        self.assertEqual(aspects['相机'], 'neutral')
    
    def test_batch_sentiment_analysis(self):
        """测试批量情感分析"""
        all_chinese_texts = []
        expected_sentiments = []
        
        for sentiment, texts in self.test_data['chinese'].items():
            all_chinese_texts.extend(texts)
            expected_sentiments.extend([sentiment] * len(texts))
        
        results = self.sentiment_analyzer.batch_analyze(all_chinese_texts)
        
        self.assertEqual(len(results), len(all_chinese_texts))
        for i, result in enumerate(results):
            self.assertIn('sentiment', result)
            self.assertEqual(result['sentiment'], expected_sentiments[i])
    
    @patch('app.nlp.sentiment.SentimentAnalyzer._load_model')
    def test_model_loading(self, mock_load):
        """测试模型加载功能"""
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        
        analyzer = SentimentAnalyzer(model_name='custom_model')
        mock_load.assert_called_once_with('custom_model')
        self.assertEqual(analyzer.model, mock_model)
    
    def test_sentiment_benchmark(self):
        """情感分析性能基准测试"""
        import time
        
        # 单个文本分析
        start_time = time.time()
        for _ in range(20):
            self.sentiment_analyzer.analyze(self.test_data['chinese']['positive'][0])
        single_time = time.time() - start_time
        
        # 批量分析
        all_texts = []
        for lang in ['chinese', 'english']:
            for sentiment, texts in self.test_data[lang].items():
                all_texts.extend(texts)
        
        start_time = time.time()
        self.sentiment_analyzer.batch_analyze(all_texts)
        batch_time = time.time() - start_time
        
        # 记录性能指标
        print(f"情感分析性能基准测试: 单个文本: {single_time:.4f}秒, 批量({len(all_texts)}个文本): {batch_time:.4f}秒")
        
        # 确保性能在可接受范围内
        self.assertLess(single_time, 3.0, "单个文本情感分析性能测试超时")
        self.assertLess(batch_time, 10.0, "批量情感分析性能测试超时")
        
    def test_sentiment_model_consistency(self):
        """测试模型一致性"""
        # 针对同一文本多次分析，结果应当一致
        text = "这个产品非常好用，我很满意"
        results = [self.sentiment_analyzer.analyze(text) for _ in range(5)]
        
        # 验证所有结果相同
        for i in range(1, len(results)):
            self.assertEqual(results[0]['sentiment'], results[i]['sentiment'])
            # 允许置信度有微小差异
            self.assertAlmostEqual(results[0]['confidence'], results[i]['confidence'], places=5)
            
if __name__ == '__main__':
    unittest.main()