#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义文本嵌入模块 - 使用sentence-transformers库
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
import hashlib

# 设置日志记录器
logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                         "cache", "embeddings")
os.makedirs(CACHE_DIR, exist_ok=True)

class CustomEmbeddingModel:
    """使用sentence-transformers的嵌入模型"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """初始化嵌入模型"""
        self.model_name = model_name
        self.model = None
        self.use_cache = True
        self.is_loaded = False
        logger.info(f"初始化自定义嵌入模型: {model_name}")
    
    def load_model(self):
        """加载模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True
            logger.info(f"已加载sentence-transformers模型: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"加载sentence-transformers模型失败: {e}")
            return False
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """将文本编码为向量"""
        if not self.is_loaded:
            if not self.load_model():
                # 如果加载失败，使用备用方法
                return self._fallback_encode(texts)
        
        try:
            # 使用sentence-transformers模型编码
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.warning(f"文本编码出错: {e}")
            return self._fallback_encode(texts)
    
    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        """备用的编码方法"""
        # 生成伪随机向量
        embeddings = []
        embedding_dim = 384  # 常见维度
        
        for text in texts:
            # 使用文本的hash作为随机种子，确保相同文本得到相同向量
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
            np.random.seed(seed)
            
            # 生成随机向量并归一化
            vector = np.random.randn(embedding_dim)
            vector = vector / np.linalg.norm(vector)
            embeddings.append(vector)
        
        return np.array(embeddings)
    
    def get_cache_key(self, text: str) -> str:
        """为文本生成缓存键"""
        key = f"{self.model_name}_{hashlib.md5(text.encode()).hexdigest()}"
        return key
    
    def load_from_cache(self, text: str) -> Optional[np.ndarray]:
        """从缓存加载嵌入向量"""
        if not self.use_cache:
            return None
            
        cache_key = self.get_cache_key(text)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.npy")
        
        if os.path.exists(cache_path):
            try:
                return np.load(cache_path)
            except Exception as e:
                logger.warning(f"从缓存加载失败: {e}")
                
        return None
    
    def save_to_cache(self, text: str, embedding: np.ndarray) -> bool:
        """将嵌入向量保存到缓存"""
        if not self.use_cache:
            return False
            
        cache_key = self.get_cache_key(text)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.npy")
        
        try:
            np.save(cache_path, embedding)
            return True
        except Exception as e:
            logger.warning(f"保存到缓存失败: {e}")
            return False

# 全局模型实例
_embedding_model = None

def get_embedding_model() -> CustomEmbeddingModel:
    """获取嵌入模型实例"""
    global _embedding_model
    
    if _embedding_model is None:
        _embedding_model = CustomEmbeddingModel()
        
    return _embedding_model

def get_sentence_embeddings(sentences: Union[List[str], str]) -> np.ndarray:
    """获取句子的嵌入向量"""
    model = get_embedding_model()
    
    # 处理单个句子的情况
    if isinstance(sentences, str):
        return model.encode([sentences])[0]
    
    return model.encode(sentences)

def get_document_embedding(document: str) -> np.ndarray:
    """获取文档的嵌入向量"""
    # 将整个文档作为一个句子处理
    return get_sentence_embeddings(document)

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)

def clear_embedding_cache() -> int:
    """清除嵌入缓存，返回删除的文件数量"""
    count = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith(".npy"):
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
                count += 1
            except:
                pass
                
    return count 