# -*- coding: utf-8 -*-
"""
NLP模块: 分词器
功能描述: 提供文本分词功能，支持多种分词策略和语言
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

import start
import re
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# 尝试导入可选依赖
try:
import ui.views
JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

try:
SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# 初始化日志记录器
logger = logging.getLogger(__name__)


@dataclass
class TokenizerConfig:
    """分词器配置类"""

    tokenizer_type: str = "basic"  # 分词器类型: basic, jieba, spacy
    language: str = "en"  # 语言: en, zh, etc.
    lowercase: bool = True  # 是否转换为小写
    remove_punctuation: bool = True  # 是否移除标点符号
    remove_numbers: bool = False  # 是否移除数字
    remove_stopwords: bool = False  # 是否移除停用词
    custom_stopwords: List[str] = None  # 自定义停用词列表
    spacy_model: str = "en_core_web_sm"  # SpaCy模型名称

    def __post_init__(self):
        """数据校验和默认值设置"""
        if self.custom_stopwords is None:
            self.custom_stopwords = []

        # 验证分词器类型
        valid_tokenizers = ["basic", "jieba", "spacy"]
        if self.tokenizer_type not in valid_tokenizers:
            logger.warning(f"无效的分词器类型: {self.tokenizer_type}，使用默认类型: basic")
            self.tokenizer_type = "basic"

        # 验证分词器依赖
        if self.tokenizer_type == "jieba" and not JIEBA_AVAILABLE:
            logger.warning("Jieba未安装，回退到基础分词器")
            self.tokenizer_type = "basic"

        if self.tokenizer_type == "spacy" and not SPACY_AVAILABLE:
            logger.warning("SpaCy未安装，回退到基础分词器")
            self.tokenizer_type = "basic"


class Tokenizer:
    """文本分词器类"""

    def __init__(self, config: Optional[Union[Dict[str, Any], TokenizerConfig]] = None):
        """
        初始化分词器

        参数:
            config: 分词器配置，可以是TokenizerConfig实例或字典
        """
        if config is None:
            self.config = TokenizerConfig()
        elif isinstance(config, dict):
            self.config = TokenizerConfig(**config)
        else:
            self.config = config

        # 加载和初始化分词资源
        self._initialize_tokenizer()
        logger.info(
            f"初始化分词器: {self.config.tokenizer_type}, 语言: {self.config.language}")

    def _initialize_tokenizer(self):
        """初始化分词器资源"""
        if self.config.tokenizer_type == "jieba" and JIEBA_AVAILABLE:
            # 如果使用结巴分词，可以在这里添加自定义词典
            pass

        elif self.config.tokenizer_type == "spacy" and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(self.config.spacy_model)
                logger.info(f"已加载SpaCy模型: {self.config.spacy_model}")
            except OSError:
                logger.error(
                    f"无法加载SpaCy模型: {self.config.spacy_model}，回退到基础分词器")
                self.config.tokenizer_type = "basic"

        # 编译标点符号正则表达式
        self.punctuation_pattern = re.compile(r'[^\w\s]')
        self.number_pattern = re.compile(r'\d+')

    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本

        参数:
            text: 输入文本

        返回:
            预处理后的文本
        """
        if self.config.lowercase:
            text = text.lower()

        if self.config.remove_punctuation:
            text = self.punctuation_pattern.sub(' ', text)

        if self.config.remove_numbers:
            text = self.number_pattern.sub(' ', text)

        return text

    def _remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        移除停用词

        参数:
            tokens: 分词列表

        返回:
            移除停用词后的分词列表
        """
        if not self.config.remove_stopwords:
            return tokens

        # 根据语言获取停用词列表
        stopwords = set(self.config.custom_stopwords)

        if self.config.tokenizer_type == "spacy" and SPACY_AVAILABLE:
            # 使用SpaCy的停用词
            stopwords.update(
                [token.text for token in self.nlp('').vocab if token.is_stop])

        # 过滤停用词
        return [token for token in tokens if token not in stopwords]

    def tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词

        参数:
            text: 输入文本

        返回:
            分词后的标记列表
        """
        # 预处理文本
        text = self._preprocess_text(text)

        # 根据分词器类型选择分词策略
        if self.config.tokenizer_type == "jieba" and JIEBA_AVAILABLE:
            tokens = list(jieba.cut(text))

        elif self.config.tokenizer_type == "spacy" and SPACY_AVAILABLE:
            doc = self.nlp(text)
            tokens = [token.text for token in doc]

        else:  # basic tokenizer
            # 基础分词，按空白字符分割
            tokens = text.split()

        # 移除停用词
        tokens = self._remove_stopwords(tokens)

        # 移除空标记
        tokens = [token for token in tokens if token.strip()]

        return tokens

    def tokenize_batch(self, texts: List[str]) -> List[List[str]]:
        """
        批量分词

        参数:
            texts: 文本列表

        返回:
            分词结果列表，每个元素是一个标记列表
        """
        return [self.tokenize(text) for text in texts]


# 为配置加载器提供默认配置
DEFAULT_TOKENIZER_CONFIG = {
    "tokenizer_type": "basic",
    "language": "en",
    "lowercase": True,
    "remove_punctuation": True,
    "remove_stopwords": False
}