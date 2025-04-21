# -*- coding: utf-8 -*-
"""
NLP模块: 情感分析
功能描述: 提供文本情感分析功能，支持多种情感分析模型
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

from .. config.config_loader import ConfigLoader
from transformers import pipeline
import core
import os
import re
import logging
import pickle
from typing import Dict, List, Any, Optional, Union, Tuple
import modules.nlp as np

# 尝试导入可选依赖
try:
import modules.nlp
from modules.nlp.sentiment import SentimentIntensityAnalyzer
NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# 从配置加载器获取配置
try:
config_loader = ConfigLoader()
SENTIMENT_CONFIG = config_loader.load("modules.nlp.sentiment")
except ImportError:
    SENTIMENT_CONFIG = {
        "default_analyzer": "basic",
        "sentiment_thresholds": {
            "positive": 0.6,
            "negative": 0.6,
            "neutral": 0.2
        }
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情感分析器类"""

    SUPPORTED_ANALYZERS = ["basic", "vader", "transformer", "custom"]

    def __init__(self,
                 analyzer_type: str = "basic",
                 model_path: Optional[str] = None,
                 sentiment_lexicon: Optional[Dict[str, float]] = None,
                 thresholds: Optional[Dict[str, float]] = None,
                 language: str = "en",
                 device: str = "cpu"):
        """
        初始化情感分析器

        参数:
            analyzer_type: 分析器类型，支持 "basic", "vader", "transformer", "custom"
            model_path: 预训练模型路径，用于transformer类型
            sentiment_lexicon: 情感词典，用于basic和custom类型
            thresholds: 情感分类阈值，如 {"positive": 0.6, "negative": 0.6, "neutral": 0.2}
            language: 语言代码，如 "en", "zh"
            device: 计算设备，"cpu" 或 "cuda"
        """
        self.analyzer_type = analyzer_type.lower()
        self.model_path = model_path
        self.language = language
        self.device = device
        self.analyzer = None

        # 设置情感阈值
        if thresholds is None:
            self.thresholds = SENTIMENT_CONFIG.get("sentiment_thresholds", {
                "positive": 0.6,
                "negative": 0.6,
                "neutral": 0.2
            })
        else:
            self.thresholds = thresholds

        # 设置情感词典
        if sentiment_lexicon is None:
            self.sentiment_lexicon = {}
        else:
            self.sentiment_lexicon = sentiment_lexicon

        # 验证分析器类型
        if self.analyzer_type not in self.SUPPORTED_ANALYZERS:
            logger.warning(f"不支持的情感分析器类型: {self.analyzer_type}，使用默认类型: basic")
            self.analyzer_type = "basic"

        # 初始化分析器
        self._initialize_analyzer()
        logger.info(f"初始化情感分析器: {self.analyzer_type}, 语言: {self.language}")

    def _initialize_analyzer(self):
        """初始化情感分析器"""
        try:
            if self.analyzer_type == "vader" and NLTK_AVAILABLE:
                # 使用NLTK的VADER情感分析器
                try:
                    nltk.data.find('sentiment/vader_lexicon.zip')
                except LookupError:
                    logger.info("下载VADER情感词典")
                    nltk.download('vader_lexicon')

                self.analyzer = SentimentIntensityAnalyzer()
                logger.info("VADER情感分析器初始化成功")

            elif self.analyzer_type == "transformer" and TRANSFORMERS_AVAILABLE:
                # 使用Transformers的情感分析管道
                if self.model_path:
                    # 设置设备
                    if self.device == "cuda" and torch.cuda.is_available():
                        device = 0  # 使用第一个CUDA设备
                    else:
                        device = -1  # 使用CPU

                    self.analyzer = pipeline("sentiment-analysis",
                                             model=self.model_path,
                                             device=device)
                    logger.info(f"Transformer情感分析器初始化成功: {self.model_path}")
                else:
                    logger.warning("未指定transformer模型路径，使用基础分析器")
                    self.analyzer_type = "basic"

            elif self.analyzer_type == "custom" and self.model_path and os.path.exists(self.model_path):
                # 加载自定义情感分析模型
                with open(self.model_path, 'rb') as f:
                    self.analyzer = pickle.load(f)
                logger.info(f"成功加载自定义情感分析模型: {self.model_path}")

            # 对于basic类型或其他情况，使用基于词典的简单分析器
            if self.analyzer_type == "basic" or self.analyzer is None:
                self._load_basic_sentiment_lexicon()

        except Exception as e:
            logger.error(f"情感分析器初始化失败: {str(e)}")
            self.analyzer_type = "basic"
            self._load_basic_sentiment_lexicon()

    def _load_basic_sentiment_lexicon(self):
        """加载基础情感词典"""
        # 如果已提供词典，则使用它
        if self.sentiment_lexicon:
            return

        # 尝试从配置中加载词典路径
        lexicon_path = SENTIMENT_CONFIG.get("sentiment_lexicon_path")
        if lexicon_path and os.path.exists(lexicon_path):
            try:
                with open(lexicon_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            word, score = parts[0], float(parts[1])
                            self.sentiment_lexicon[word] = score
                logger.info(
                    f"从 {lexicon_path} 加载情感词典，共 {len(self.sentiment_lexicon)} 个词条")
            except Exception as e:
                logger.error(f"加载情感词典失败: {str(e)}")

        # 如果词典为空，则使用简单的默认词典
        if not self.sentiment_lexicon:
            logger.warning("使用默认的简单情感词典")
            # 英文默认词典
            if self.language == "en":
                self.sentiment_lexicon = {
                    "good": 0.7, "great": 0.8, "excellent": 0.9, "amazing": 0.85, "wonderful": 0.85,
                    "bad": -0.7, "terrible": -0.8, "awful": -0.85, "horrible": -0.9, "poor": -0.6,
                    "like": 0.5, "love": 0.8, "hate": -0.8, "dislike": -0.5,
                    "happy": 0.7, "sad": -0.7, "angry": -0.7, "excited": 0.7
                }
            # 中文默认词典
            elif self.language == "zh":
                self.sentiment_lexicon = {
                    "好": 0.7, "很好": 0.8, "优秀": 0.9, "棒": 0.85, "精彩": 0.85,
                    "坏": -0.7, "糟糕": -0.8, "差": -0.6, "可怕": -0.85, "糟": -0.7,
                    "喜欢": 0.5, "爱": 0.8, "恨": -0.8, "讨厌": -0.5,
                    "高兴": 0.7, "悲伤": -0.7, "愤怒": -0.7, "兴奋": 0.7
                }

    def _analyze_basic(self, text: str) -> Dict[str, float]:
        """
        使用基础词典分析文本情感

        参数:
            text: 输入文本

        返回:
            情感得分字典，包含 positive, negative, neutral 和 compound 得分
        """
        # 文本预处理
        text = text.lower()
        # 分词（简单使用空格分割）
        words = re.findall(r'\w+', text)

        # 计算情感得分
        positive_score = 0.0
        negative_score = 0.0
        total_matches = 0

        for word in words:
            if word in self.sentiment_lexicon:
                score = self.sentiment_lexicon[word]
                if score > 0:
                    positive_score += score
                else:
                    negative_score += abs(score)
                total_matches += 1

        # 计算复合得分
        if total_matches > 0:
            positive_avg = positive_score / total_matches if positive_score > 0 else 0
            negative_avg = negative_score / total_matches if negative_score > 0 else 0
            compound = positive_avg - negative_avg
            neutral = 1.0 - (positive_avg + negative_avg)
        else:
            positive_avg = 0.0
            negative_avg = 0.0
            compound = 0.0
            neutral = 1.0

        return {
            "positive": positive_avg,
            "negative": negative_avg,
            "neutral": neutral,
            "compound": compound
        }

    def _analyze_vader(self, text: str) -> Dict[str, float]:
        """
        使用VADER分析文本情感

        参数:
            text: 输入文本

        返回:
            情感得分字典
        """
        if not NLTK_AVAILABLE or self.analyzer is None:
            return self._analyze_basic(text)

        scores = self.analyzer.polarity_scores(text)
        return {
            "positive": scores["pos"],
            "negative": scores["neg"],
            "neutral": scores["neu"],
            "compound": scores["compound"]
        }

    def _analyze_transformer(self, text: str) -> Dict[str, float]:
        """
        使用Transformer模型分析文本情感

        参数:
            text: 输入文本

        返回:
            情感得分字典
        """
        if not TRANSFORMERS_AVAILABLE or self.analyzer is None:
            return self._analyze_basic(text)

        try:
            # 使用pipeline获取结果
            result = self.analyzer(text)

            # 解析结果
            if result and isinstance(result, list) and len(result) > 0:
                label = result[0]["label"].lower()
                score = result[0]["score"]

                # 转换为标准格式
                if "positive" in label:
                    return {
                        "positive": score,
                        "negative": 1.0 - score,
                        "neutral": 0.0,
                        "compound": 2 * score - 1.0  # 将[0,1]映射到[-1,1]
                    }
                elif "negative" in label:
                    return {
                        "positive": 1.0 - score,
                        "negative": score,
                        "neutral": 0.0,
                        "compound": 1.0 - 2 * score  # 将[0,1]映射到[1,-1]
                    }
                elif "neutral" in label:
                    neutral_score = score
                    # 平分剩余概率
                    remaining = 1.0 - neutral_score
                    half_remaining = remaining / 2.0
                    return {
                        "positive": half_remaining,
                        "negative": half_remaining,
                        "neutral": neutral_score,
                        "compound": 0.0  # 中性结果复合得分为0
                    }
        except Exception as e:
            logger.error(f"Transformer情感分析错误: {str(e)}")

        # 失败时回退到基础分析
        return self._analyze_basic(text)

    def _analyze_custom(self, text: str) -> Dict[str, float]:
        """
        使用自定义模型分析文本情感

        参数:
            text: 输入文本

        返回:
            情感得分字典
        """
        if self.analyzer is None:
            return self._analyze_basic(text)

        try:
            # 假设自定义分析器有一个predict方法
            result = self.analyzer.predict(text)

            # 转换结果格式
            if isinstance(result, dict) and "positive" in result and "negative" in result:
                # 如果返回格式已经匹配，直接使用
                return result
            elif isinstance(result, (list, tuple)) and len(result) >= 2:
                # 假设结果为[positive_score, negative_score]
                pos, neg = result[0], result[1]
                neutral = 1.0 - (pos + neg) if pos + neg <= 1.0 else 0.0
                return {
                    "positive": pos,
                    "negative": neg,
                    "neutral": neutral,
                    "compound": pos - neg
                }
        except Exception as e:
            logger.error(f"自定义情感分析错误: {str(e)}")

        # 失败时回退到基础分析
        return self._analyze_basic(text)

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感

        参数:
            text: 输入文本

        返回:
            情感分析结果，包含得分和标签
        """
        # 如果文本为空，返回中性结果
        if not text or not text.strip():
            return {
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0},
                "label": "neutral",
                "confidence": 1.0
            }

        # 根据分析器类型选择分析方法
        if self.analyzer_type == "vader":
            scores = self._analyze_vader(text)
        elif self.analyzer_type == "transformer":
            scores = self._analyze_transformer(text)
        elif self.analyzer_type == "custom":
            scores = self._analyze_custom(text)
        else:  # basic
            scores = self._analyze_basic(text)

        # 根据阈值确定情感标签
        label = "neutral"
        if scores["positive"] >= self.thresholds["positive"] and scores["positive"] > scores["negative"]:
            label = "positive"
        elif scores["negative"] >= self.thresholds["negative"] and scores["negative"] > scores["positive"]:
            label = "negative"

        # 计算置信度
        if label == "positive":
            confidence = scores["positive"]
        elif label == "negative":
            confidence = scores["negative"]
        else:
            confidence = scores["neutral"]

        return {
            "scores": scores,
            "label": label,
            "confidence": confidence
        }

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        批量分析文本情感

        参数:
            texts: 文本列表

        返回:
            情感分析结果列表
        """
        return [self.analyze(text) for text in texts]

    def extract_sentiment_aspects(self, text: str, aspects: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        分析文本中特定方面的情感

        参数:
            text: 输入文本
            aspects: 需要分析的方面列表

        返回:
            各方面的情感分析结果
        """
        results = {}
        sentences = re.split(r'[.!?；。！？]', text)

        for aspect in aspects:
            aspect_sentences = [
                s for s in sentences if aspect.lower() in s.lower()]

            if aspect_sentences:
                aspect_text = " ".join(aspect_sentences)
                results[aspect] = self.analyze(aspect_text)
            else:
                # 如果没有找到包含该方面的句子，返回中性结果
                results[aspect] = {
                    "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0},
                    "label": "neutral",
                    "confidence": 0.0
                }

        return results