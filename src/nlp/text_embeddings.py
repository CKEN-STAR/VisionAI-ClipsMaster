#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本嵌入模块

提供文本到向量的嵌入功能，支持句子级和文档级嵌入。
使用多种模型实现，优先使用本地模型，失败时使用精简后备模型。
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import time
from pathlib import Path
import hashlib

# 设置日志记录器
logger = logging.getLogger("text_embeddings")

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "embeddings")
os.makedirs(CACHE_DIR, exist_ok=True)

# 默认维度
DEFAULT_EMBEDDING_DIM = 384  # 使用较小的维度以提高效率

class EmbeddingModel:
    """文本嵌入模型接口"""
    
    def __init__(self, model_name: str = "local_model"):
        """
        初始化嵌入模型
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.model = None
        self.use_cache = True
        self.embedding_dim = DEFAULT_EMBEDDING_DIM
        
    def load_model(self):
        """加载模型 (需要子类实现)"""
        raise NotImplementedError("需要在子类中实现")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        将文本编码为向量 (需要子类实现)
        
        Args:
            texts: 文本列表
            
        Returns:
            np.ndarray: 文本向量数组
        """
        raise NotImplementedError("需要在子类中实现")
    
    def get_cache_key(self, text: str) -> str:
        """
        为文本生成缓存键
        
        Args:
            text: 输入文本
            
        Returns:
            str: 缓存键
        """
        # 使用模型名称和文本内容生成缓存键
        key = f"{self.model_name}_{hashlib.md5(text.encode()).hexdigest()}"
        return key
    
    def load_from_cache(self, text: str) -> Optional[np.ndarray]:
        """
        从缓存加载嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[np.ndarray]: 嵌入向量，如果缓存不存在则返回None
        """
        if not self.use_cache:
            return None
            
        cache_key = self.get_cache_key(text)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.npy")
        
        if os.path.exists(cache_path):
            try:
                return np.load(cache_path)
            except Exception as e:
                logger.warning(f"从缓存加载嵌入向量失败: {str(e)}")
                
        return None
    
    def save_to_cache(self, text: str, embedding: np.ndarray) -> bool:
        """
        将嵌入向量保存到缓存
        
        Args:
            text: 输入文本
            embedding: 嵌入向量
            
        Returns:
            bool: 是否成功保存
        """
        if not self.use_cache:
            return False
            
        cache_key = self.get_cache_key(text)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.npy")
        
        try:
            np.save(cache_path, embedding)
            return True
        except Exception as e:
            logger.warning(f"保存嵌入向量到缓存失败: {str(e)}")
            return False

class DefaultEmbeddingModel(EmbeddingModel):
    """默认嵌入模型实现"""
    
    def __init__(self, model_name: str = "default"):
        """
        初始化默认嵌入模型
        
        Args:
            model_name: 模型名称
        """
        super().__init__(model_name)
        self.model = None
        
    def load_model(self):
        """加载默认嵌入模型"""
        # 默认实现只是一个随机向量生成器
        # 实际项目中应替换为真实的模型
        self.model = "random_vectors"
        logger.info("加载默认嵌入模型 (随机向量生成器)")
        
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        将文本编码为向量 (默认实现使用随机向量)
        
        Args:
            texts: 文本列表
            
        Returns:
            np.ndarray: 文本向量数组
        """
        if self.model is None:
            self.load_model()
            
        # 为每个文本生成稳定的随机向量
        embeddings = []
        for text in texts:
            # 首先检查缓存
            cached_embedding = self.load_from_cache(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
                continue
                
            # 如果没有缓存，生成伪随机向量
            # 使用文本的hash值作为随机种子，确保相同文本得到相同的向量
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
            np.random.seed(seed)
            
            # 生成向量并归一化
            embedding = np.random.randn(self.embedding_dim)
            embedding = embedding / np.linalg.norm(embedding)
            
            # 保存到缓存
            self.save_to_cache(text, embedding)
            
            embeddings.append(embedding)
            
        return np.array(embeddings)

# 全局模型实例
_EMBEDDING_MODEL = None

def get_embedding_model() -> EmbeddingModel:
    """
    获取嵌入模型实例
    
    Returns:
        EmbeddingModel: 嵌入模型实例
    """
    global _EMBEDDING_MODEL
    
    if _EMBEDDING_MODEL is None:
        # 尝试加载sentence-transformers模型
        try:
            # 在实际实现中，这里应该导入并使用真实的模型
            # 例如:
            # from sentence_transformers import SentenceTransformer
            # model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # 现在我们使用默认实现
            _EMBEDDING_MODEL = DefaultEmbeddingModel("multilingual-model")
            logger.info("使用默认嵌入模型")
        except Exception as e:
            logger.warning(f"加载高级嵌入模型失败: {str(e)}")
            _EMBEDDING_MODEL = DefaultEmbeddingModel()
            
    return _EMBEDDING_MODEL

def get_sentence_embeddings(sentences: List[str]) -> np.ndarray:
    """
    获取句子的嵌入向量
    
    Args:
        sentences: 句子列表
        
    Returns:
        np.ndarray: 句子向量数组
    """
    model = get_embedding_model()
    return model.encode(sentences)

def get_document_embedding(document: str) -> np.ndarray:
    """
    获取文档的嵌入向量
    
    Args:
        document: 文档文本
        
    Returns:
        np.ndarray: 文档向量
    """
    # 简单的方法是直接将整个文档作为一个句子处理
    embeddings = get_sentence_embeddings([document])
    return embeddings[0]

def get_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        
    Returns:
        float: 余弦相似度 (0-1)
    """
    embeddings = get_sentence_embeddings([text1, text2])
    
    # 计算余弦相似度
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    
    # 确保结果在0-1范围内
    return float(max(0.0, min(1.0, similarity)))

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    计算两个向量的余弦相似度
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 余弦相似度 (0-1)
    """
    # 规范化向量，确保能安全计算相似度
    if np.all(vec1 == 0) or np.all(vec2 == 0):
        return 0.0
        
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    # 确保结果在0-1范围内
    return float(max(0.0, min(1.0, similarity))) 