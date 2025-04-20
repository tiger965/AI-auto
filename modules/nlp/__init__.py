# -*- coding: utf-8 -*-
"""
NLP模块: 自然语言处理子包初始化
功能描述: 提供自然语言处理功能，包括分词、词嵌入和情感分析
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

# 版本信息
__version__ = "1.0.0"

# 导出子模块类和函数
from .tokenizer import Tokenizer, TokenizerConfig
from .embedding import EmbeddingModel, load_embedding_model
from .sentiment import SentimentAnalyzer

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"NLP模块初始化完成，版本 {__version__}")

# 从配置加载器加载NLP特定配置
try:
    from ...config.config_loader import ConfigLoader
    # 初始化配置加载器
    config_loader = ConfigLoader()
    NLP_CONFIG = config_loader.load("modules.nlp")
except ImportError:
    import warnings
    warnings.warn("配置加载器未找到，使用默认NLP配置")
    NLP_CONFIG = {
        "default_tokenizer": "basic",
        "embedding_model_path": "models/embeddings/default",
        "sentiment_model_path": "models/sentiment/default"
    }

# 导出的模块、类和函数
__all__ = [
    "Tokenizer",
    "TokenizerConfig",
    "EmbeddingModel",
    "load_embedding_model",
    "SentimentAnalyzer",
    "get_nlp_config"
]

def get_nlp_config():
    """
    获取NLP模块配置
    
    返回:
        dict: NLP模块的配置字典
    """
    return NLP_CONFIG