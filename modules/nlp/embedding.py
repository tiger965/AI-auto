# -*- coding: utf-8 -*-
"""
NLP模块: 词嵌入
功能描述: 提供文本词嵌入功能，支持多种嵌入模型和向量操作
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

import os
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

# 尝试导入可选依赖
try:
    from gensim.models import Word2Vec, KeyedVectors

    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False

try:
    import torch
    from transformers import AutoTokenizer, AutoModel

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# 初始化日志记录器
logger = logging.getLogger(__name__)


class EmbeddingModel:
    """文本词嵌入模型类"""

    SUPPORTED_TYPES = ["word2vec", "fasttext", "glove", "bert", "custom"]

    def __init__(
        self,
        model_type: str = "word2vec",
        model_path: Optional[str] = None,
        embedding_dim: int = 300,
        device: str = "cpu",
        **kwargs,
    ):
        """
        初始化词嵌入模型

        参数:
            model_type: 模型类型，支持 "word2vec", "fasttext", "glove", "bert", "custom"
            model_path: 模型路径，用于加载预训练模型
            embedding_dim: 嵌入维度，仅用于自定义模型
            device: 计算设备，"cpu" 或 "cuda"
            **kwargs: 其他参数
        """
        self.model_type = model_type.lower()
        self.model_path = model_path
        self.embedding_dim = embedding_dim
        self.device = device
        self.kwargs = kwargs
        self.model = None
        self.tokenizer = None
        self.word_vectors = {}  # 词向量缓存

        # 验证模型类型
        if self.model_type not in self.SUPPORTED_TYPES:
            logger.warning(
                f"不支持的嵌入模型类型: {self.model_type}，使用默认类型: word2vec"
            )
            self.model_type = "word2vec"

        # 初始化模型
        self._initialize_model()
        logger.info(f"初始化词嵌入模型: {self.model_type}, 维度: {self.embedding_dim}")

    def _initialize_model(self):
        """初始化词嵌入模型"""
        try:
            if self.model_path and os.path.exists(self.model_path):
                if self.model_type == "word2vec" and GENSIM_AVAILABLE:
                    self.model = KeyedVectors.load_word2vec_format(
                        self.model_path, binary=self.kwargs.get("binary", True)
                    )
                    self.embedding_dim = self.model.vector_size

                elif self.model_type == "fasttext" and GENSIM_AVAILABLE:
                    self.model = KeyedVectors.load(self.model_path)
                    self.embedding_dim = self.model.vector_size

                elif self.model_type == "glove" and GENSIM_AVAILABLE:
                    self.model = KeyedVectors.load_word2vec_format(
                        self.model_path)
                    self.embedding_dim = self.model.vector_size

                elif self.model_type == "bert" and TRANSFORMERS_AVAILABLE:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_path)
                    self.model = AutoModel.from_pretrained(self.model_path)
                    if self.device == "cuda" and torch.cuda.is_available():
                        self.model = self.model.to("cuda")
                    self.embedding_dim = self.model.config.hidden_size

                elif self.model_type == "custom":
                    # 加载自定义词向量模型
                    with open(self.model_path, "rb") as f:
                        self.word_vectors = pickle.load(f)
                        # 获取第一个向量的维度
                        first_vector = next(iter(self.word_vectors.values()))
                        self.embedding_dim = len(first_vector)

                logger.info(f"成功加载{self.model_type}模型: {self.model_path}")
            else:
                logger.warning(f"模型路径不存在: {self.model_path}")
                self._initialize_empty_model()

        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            self._initialize_empty_model()

    def _initialize_empty_model(self):
        """初始化空模型，当无法加载预训练模型时使用"""
        logger.warning(f"初始化空的{self.model_type}模型")
        self.word_vectors = {}

    def _get_bert_embedding(self, text: str) -> np.ndarray:
        """
        获取BERT模型的文本嵌入

        参数:
            text: 输入文本

        返回:
            文本嵌入向量
        """
        if not TRANSFORMERS_AVAILABLE or self.model is None:
            return np.zeros(self.embedding_dim)

        # 将文本转换为模型输入
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True
        )
        if self.device == "cuda" and torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        # 获取模型输出
        with torch.no_grad():
            outputs = self.model(**inputs)

        # 使用[CLS]标记的最后隐藏状态作为句子嵌入
        sentence_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return sentence_embedding[0]  # 返回第一个样本的嵌入

    def get_word_vector(self, word: str) -> np.ndarray:
        """
        获取单词的词向量

        参数:
            word: 输入单词

        返回:
            词向量，如果单词不存在则返回零向量
        """
        # 检查缓存
        if word in self.word_vectors:
            return self.word_vectors[word]

        vector = np.zeros(self.embedding_dim)

        try:
            if (
                self.model_type in ["word2vec", "fasttext", "glove"]
                and GENSIM_AVAILABLE
                and self.model is not None
            ):
                if word in self.model:
                    vector = self.model[word]

            elif self.model_type == "custom" and word in self.word_vectors:
                vector = self.word_vectors[word]

            # 缓存结果
            self.word_vectors[word] = vector

        except Exception as e:
            logger.debug(f"获取词向量失败: {word}, 错误: {str(e)}")

        return vector

    def get_text_embedding(
        self, text: str, tokens: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        获取文本的嵌入向量

        参数:
            text: 输入文本
            tokens: 可选的分词列表，如果提供则直接使用

        返回:
            文本嵌入向量
        """
        if (
            self.model_type == "bert"
            and TRANSFORMERS_AVAILABLE
            and self.model is not None
        ):
            return self._get_bert_embedding(text)

        # 如果没有提供分词，则将文本按空格分割
        if tokens is None:
            tokens = text.split()

        if not tokens:
            return np.zeros(self.embedding_dim)

        # 获取每个词的向量，然后取平均
        vectors = [self.get_word_vector(token) for token in tokens]
        return np.mean(vectors, axis=0)

    def get_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度

        参数:
            text1: 第一段文本
            text2: 第二段文本

        返回:
            相似度评分，范围[0,1]
        """
        vec1 = self.get_text_embedding(text1)
        vec2 = self.get_text_embedding(text2)

        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def most_similar_words(self, word: str, n: int = 10) -> List[Tuple[str, float]]:
        """
        查找与给定词最相似的n个词

        参数:
            word: 查询词
            n: 返回结果数量

        返回:
            相似词及其相似度的列表，按相似度降序排序
        """
        if (
            self.model_type in ["word2vec", "fasttext", "glove"]
            and GENSIM_AVAILABLE
            and self.model is not None
        ):
            try:
                return self.model.most_similar(word, topn=n)
            except:
                pass

        return []

    def save_word_vectors(self, save_path: str):
        """
        保存词向量缓存到文件

        参数:
            save_path: 保存路径
        """
        try:
            directory = os.path.dirname(save_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(save_path, "wb") as f:
                pickle.dump(self.word_vectors, f)
            logger.info(f"词向量缓存已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存词向量失败: {str(e)}")


def load_embedding_model(model_config: Dict[str, Any]) -> EmbeddingModel:
    """
    根据配置加载词嵌入模型

    参数:
        model_config: 模型配置字典

    返回:
        初始化后的EmbeddingModel实例
    """
    # 获取配置参数
    model_type = model_config.get("model_type", "word2vec")
    model_path = model_config.get("model_path")
    embedding_dim = model_config.get("embedding_dim", 300)
    device = model_config.get("device", "cpu")

    # 从环境变量中获取模型路径（如果配置了）
    if model_path and model_path.startswith("$"):
        env_var = model_path[1:]
        model_path = os.environ.get(env_var)
        if not model_path:
            logger.warning(f"环境变量 {env_var} 未设置，使用默认路径")
            model_path = None

    # 创建并返回嵌入模型
    return EmbeddingModel(
        model_type=model_type,
        model_path=model_path,
        embedding_dim=embedding_dim,
        device=device,
        **{
            k: v
            for k, v in model_config.items()
            if k not in ["model_type", "model_path", "embedding_dim", "device"]
        },
    )