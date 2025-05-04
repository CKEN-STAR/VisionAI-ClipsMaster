#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多样性管理器模块

提供版本多样性控制，确保不同剧本版本之间有足够差异，
避免生成过于相似的版本，增强用户混剪选择的实用性。
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import difflib
import re
import time

from src.nlp.text_embeddings import get_sentence_embeddings
from src.versioning.snapshot_manager import Snapshotter, SnapshotType

# 设置日志记录器
logger = logging.getLogger("diversity_manager")

class DiversityMethod(Enum):
    """多样性计算方法枚举"""
    COSINE_SIMILARITY = "cosine_similarity"  # 余弦相似度
    EDIT_DISTANCE = "edit_distance"          # 编辑距离
    TEXT_DIFF = "text_diff"                  # 文本差异比例
    HYBRID = "hybrid"                        # 混合方法

class DiversityManager:
    """版本多样性管理器"""
    
    def __init__(self, 
                 similarity_threshold: float = 0.65,
                 method: Union[DiversityMethod, str] = DiversityMethod.HYBRID,
                 snapshotter: Optional[Snapshotter] = None):
        """
        初始化多样性管理器
        
        Args:
            similarity_threshold: 相似度阈值，超过此值则认为版本过于相似
            method: 多样性计算方法
            snapshotter: 快照管理器实例，如果为None则创建新实例
        """
        self.similarity_threshold = similarity_threshold
        
        # 如果传入的是字符串，转换为枚举
        if isinstance(method, str):
            try:
                self.method = DiversityMethod(method)
            except ValueError:
                logger.warning(f"未知多样性计算方法: {method}，使用混合方法")
                self.method = DiversityMethod.HYBRID
        else:
            self.method = method
            
        # 初始化快照管理器
        self.snapshotter = snapshotter or Snapshotter()
        
        logger.info(f"多样性管理器初始化完成，方法: {self.method.value}, 阈值: {self.similarity_threshold}")
        
    def ensure_variance(self, 
                        new_version: Dict[str, Any], 
                        compared_versions: Optional[List[str]] = None,
                        max_attempts: int = 3) -> Tuple[bool, float, Optional[str]]:
        """
        确保新版本与已有版本有足够差异
        
        Args:
            new_version: 新版本内容
            compared_versions: 要比较的版本ID列表，None则比较最近的几个版本
            max_attempts: 最大尝试次数
            
        Returns:
            Tuple[bool, float, Optional[str]]:
                - 是否通过多样性检查
                - 最高相似度
                - 最相似版本的ID
        """
        # 如果没有指定比较版本，获取最近的几个叶子节点版本
        if compared_versions is None:
            leaf_nodes = self.snapshotter.version_tree.get_all_leaf_nodes()
            # 按时间排序，最新的在前
            leaf_nodes.sort(key=lambda x: x.created_at, reverse=True)
            # 取最近的5个或更少
            compared_versions = [node.node_id for node in leaf_nodes[:5] if node.node_id != "root"]
        
        # 如果没有比较对象，直接通过
        if not compared_versions:
            logger.info("没有用于比较的先前版本，直接通过多样性检查")
            return True, 0.0, None
        
        # 比较版本相似度
        highest_similarity = 0.0
        most_similar_version = None
        
        for version_id in compared_versions:
            # 获取比较版本内容
            compare_version = self.snapshotter._load_snapshot_content(version_id)
            if not compare_version:
                logger.warning(f"无法加载版本内容: {version_id}")
                continue
                
            # 计算相似度
            similarity = self._calculate_similarity(new_version, compare_version)
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_similar_version = version_id
                
            # 如果任一版本相似度过高，直接返回失败
            if similarity >= self.similarity_threshold:
                logger.warning(f"版本相似度过高 ({similarity:.2f}), 超过阈值 {self.similarity_threshold}")
                return False, similarity, version_id
        
        # 都通过检查，返回结果
        logger.info(f"版本通过多样性检查，最高相似度: {highest_similarity:.2f}")
        return True, highest_similarity, most_similar_version
    
    def _calculate_similarity(self, version1: Dict[str, Any], version2: Dict[str, Any]) -> float:
        """
        计算两个版本之间的相似度
        
        Args:
            version1: 第一个版本内容
            version2: 第二个版本内容
            
        Returns:
            float: 相似度，范围 [0-1]，越高表示越相似
        """
        # 根据不同方法计算相似度
        if self.method == DiversityMethod.COSINE_SIMILARITY:
            return self._cosine_similarity(version1, version2)
        elif self.method == DiversityMethod.EDIT_DISTANCE:
            return self._edit_distance_similarity(version1, version2)
        elif self.method == DiversityMethod.TEXT_DIFF:
            return self._text_diff_similarity(version1, version2)
        else:  # 混合方法
            return self._hybrid_similarity(version1, version2)
    
    def _cosine_similarity(self, version1: Dict[str, Any], version2: Dict[str, Any]) -> float:
        """
        使用余弦相似度计算版本差异
        
        Args:
            version1: 第一个版本内容
            version2: 第二个版本内容
            
        Returns:
            float: 相似度 [0-1]
        """
        try:
            # 提取关键文本内容
            text1 = self._extract_screenplay_text(version1)
            text2 = self._extract_screenplay_text(version2)
            
            # 获取句子嵌入向量
            embeddings1 = get_sentence_embeddings(text1)
            embeddings2 = get_sentence_embeddings(text2)
            
            if len(embeddings1) == 0 or len(embeddings2) == 0:
                logger.warning("无法获取有效的嵌入向量")
                return 0.0
                
            # 计算平均嵌入向量
            avg_emb1 = np.mean(embeddings1, axis=0)
            avg_emb2 = np.mean(embeddings2, axis=0)
            
            # 计算余弦相似度
            cosine = np.dot(avg_emb1, avg_emb2) / (np.linalg.norm(avg_emb1) * np.linalg.norm(avg_emb2))
            return float(cosine)
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {str(e)}")
            # 失败时使用后备方法
            return self._text_diff_similarity(version1, version2)
    
    def _edit_distance_similarity(self, version1: Dict[str, Any], version2: Dict[str, Any]) -> float:
        """
        使用编辑距离计算版本差异
        
        Args:
            version1: 第一个版本内容
            version2: 第二个版本内容
            
        Returns:
            float: 相似度 [0-1]
        """
        # 提取文本
        text1 = self._extract_screenplay_text(version1)
        text2 = self._extract_screenplay_text(version2)
        
        # 计算简化的编辑距离 (使用difflib)
        matcher = difflib.SequenceMatcher(None, text1, text2)
        similarity = matcher.ratio()
        
        return similarity
    
    def _text_diff_similarity(self, version1: Dict[str, Any], version2: Dict[str, Any]) -> float:
        """
        使用文本差异比例计算版本差异
        
        Args:
            version1: 第一个版本内容
            version2: 第二个版本内容
            
        Returns:
            float: 相似度 [0-1]
        """
        # 提取文本
        text1 = self._extract_screenplay_text(version1)
        text2 = self._extract_screenplay_text(version2)
        
        # 获取差异
        diff = difflib.unified_diff(
            text1.splitlines(), 
            text2.splitlines(), 
            n=0
        )
        
        # 计算差异行数
        diff_lines = list(diff)
        diff_count = sum(1 for line in diff_lines if line.startswith('+') or line.startswith('-'))
        
        # 计算总行数
        total_lines = len(text1.splitlines()) + len(text2.splitlines())
        
        if total_lines == 0:
            return 0.0
            
        # 计算相似度 (1 - 差异比例)
        similarity = 1.0 - (diff_count / total_lines)
        return similarity
    
    def _hybrid_similarity(self, version1: Dict[str, Any], version2: Dict[str, Any]) -> float:
        """
        使用混合方法计算版本差异
        
        Args:
            version1: 第一个版本内容
            version2: 第二个版本内容
            
        Returns:
            float: 相似度 [0-1]
        """
        # 计算各种相似度
        try:
            cosine_sim = self._cosine_similarity(version1, version2)
        except:
            cosine_sim = 0.5  # 默认中间值
            
        edit_sim = self._edit_distance_similarity(version1, version2)
        text_sim = self._text_diff_similarity(version1, version2)
        
        # 加权平均 (余弦相似度权重较高)
        weights = [0.5, 0.3, 0.2]
        similarity = weights[0] * cosine_sim + weights[1] * edit_sim + weights[2] * text_sim
        
        return similarity
    
    def _extract_screenplay_text(self, version: Dict[str, Any]) -> str:
        """
        从版本中提取脚本文本用于比较
        
        Args:
            version: 版本内容
            
        Returns:
            str: 提取的文本
        """
        text = ""
        
        # 尝试从不同格式中提取文本
        if "screenplay" in version and isinstance(version["screenplay"], list):
            # 从场景列表中提取
            for scene in version["screenplay"]:
                if isinstance(scene, dict):
                    if "content" in scene:
                        text += scene["content"] + "\n"
                    if "dialogue" in scene and isinstance(scene["dialogue"], list):
                        for line in scene["dialogue"]:
                            if isinstance(line, dict) and "text" in line:
                                text += line["text"] + "\n"
                            elif isinstance(line, str):
                                text += line + "\n"
        
        # 如果是字幕格式
        elif "subtitles" in version and isinstance(version["subtitles"], list):
            for subtitle in version["subtitles"]:
                if isinstance(subtitle, dict) and "text" in subtitle:
                    text += subtitle["text"] + "\n"
        
        # 如果有脚本文本字段
        elif "script_text" in version and isinstance(version["script_text"], str):
            text += version["script_text"]
        
        # 简单清理文本
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def evaluate_diversity(self, versions: List[str]) -> Dict[str, Any]:
        """
        评估一组版本之间的多样性
        
        Args:
            versions: 版本ID列表
            
        Returns:
            Dict[str, Any]: 多样性评估结果
        """
        if len(versions) < 2:
            return {
                "diversity_score": 1.0,
                "avg_similarity": 0.0,
                "similar_pairs": [],
                "timestamp": time.time()
            }
        
        # 加载所有版本内容
        version_contents = {}
        for version_id in versions:
            content = self.snapshotter._load_snapshot_content(version_id)
            if content:
                version_contents[version_id] = content
        
        if len(version_contents) < 2:
            logger.warning("无法加载足够的版本内容进行比较")
            return {
                "diversity_score": 1.0,
                "avg_similarity": 0.0,
                "similar_pairs": [],
                "timestamp": time.time()
            }
        
        # 计算所有版本对之间的相似度
        similarities = []
        similar_pairs = []
        
        for i, (id1, content1) in enumerate(version_contents.items()):
            versions_list = list(version_contents.items())
            for id2, content2 in versions_list[i+1:]:
                similarity = self._calculate_similarity(content1, content2)
                similarities.append(similarity)
                
                if similarity >= self.similarity_threshold:
                    similar_pairs.append({
                        "version1": id1,
                        "version2": id2,
                        "similarity": similarity
                    })
        
        # 计算平均相似度和多样性分数
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        diversity_score = 1.0 - avg_similarity
        
        return {
            "diversity_score": diversity_score,
            "avg_similarity": avg_similarity,
            "similar_pairs": similar_pairs,
            "timestamp": time.time()
        }


def get_diversity_manager(similarity_threshold: float = 0.65,
                         method: Union[DiversityMethod, str] = DiversityMethod.HYBRID,
                         snapshotter: Optional[Snapshotter] = None) -> DiversityManager:
    """
    获取多样性管理器实例
    
    Args:
        similarity_threshold: 相似度阈值
        method: 多样性计算方法
        snapshotter: 快照管理器实例
        
    Returns:
        DiversityManager: 多样性管理器实例
    """
    return DiversityManager(
        similarity_threshold=similarity_threshold,
        method=method,
        snapshotter=snapshotter
    )


def ensure_version_diversity(new_version: Dict[str, Any],
                            similarity_threshold: float = 0.65,
                            compared_versions: Optional[List[str]] = None) -> Tuple[bool, float, Optional[str]]:
    """
    快捷函数：确保新版本与现有版本有足够差异
    
    Args:
        new_version: 新版本内容
        similarity_threshold: 相似度阈值
        compared_versions: 要比较的版本ID列表
        
    Returns:
        Tuple[bool, float, Optional[str]]:
            - 是否通过多样性检查
            - 最高相似度
            - 最相似版本的ID
    """
    manager = get_diversity_manager(similarity_threshold=similarity_threshold)
    return manager.ensure_variance(new_version, compared_versions) 