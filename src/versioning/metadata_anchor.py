#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
元数据锚点系统

为版本管理提供元数据锚点支持，包括版本指纹、元数据标注和版本关系追踪。
元数据锚点可以用于快速定位、比较和跟踪不同版本间的关系和演变历史。
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import logging
from collections import defaultdict
import re

from src.versioning.version_tree import VersionNode, VersionTree
from src.versioning.snapshot_manager import Snapshotter, SnapshotType

# 配置日志
logger = logging.getLogger("metadata_anchor")

class VersionAnnotator:
    """版本元数据注解器，为版本添加丰富的元数据信息"""
    
    def __init__(self, 
                snapshotter: Optional[Snapshotter] = None,
                metadata_dir: Optional[str] = None):
        """
        初始化版本注解器
        
        Args:
            snapshotter: 快照管理器实例
            metadata_dir: 元数据存储目录
        """
        self.snapshotter = snapshotter or Snapshotter()
        self.metadata_dir = metadata_dir or os.path.join("data", "version_metadata")
        
        # 确保目录存在
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # 缓存版本元数据
        self.metadata_cache = {}
        
    def tag_versions(self, versions: List[Dict[str, Any]], base_version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """为每个版本添加不可变元数据
        
        Args:
            versions: 版本列表
            base_version_id: 基础版本ID
            
        Returns:
            List[Dict[str, Any]]: 带有元数据的版本列表
        """
        """为每个版本添加不可变元数据"""
        for v in versions:
            # 提取内容并计算指纹
            content = self._extract_version_content(v)
            
            # 获取参数，处理可能的字典或属性访问
            params = v.get("params", {}) if isinstance(v, dict) else getattr(v, "params", {})
            
            # 创建元数据字典
            metadata = {
                "fingerprint": hashlib.sha256(content.encode()).hexdigest(),
                "generated_at": datetime.now().isoformat(),
                "param_config": params,
                "parent_version": base_version_id
            }
            
            # 设置元数据，处理可能的字典或属性访问
            if isinstance(v, dict):
                v["metadata"] = metadata
            else:
                v.metadata = metadata
            
        return versions
    
    def annotate_version(self, 
                        version: Dict[str, Any], 
                        annotations: Dict[str, Any],
                        version_id: Optional[str] = None) -> str:
        """
        为版本添加注解
        
        Args:
            version: 版本内容
            annotations: 注解信息
            version_id: 版本ID，如果为None则使用现有版本ID或创建新ID
            
        Returns:
            str: 版本ID
        """
        # 获取或创建版本ID
        if version_id is None:
            if "id" in version:
                version_id = version["id"]
            else:
                # 使用指纹作为ID的一部分
                content = self._extract_version_content(version)
                fingerprint = hashlib.sha256(content.encode()).hexdigest()[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                version_id = f"v_{timestamp}_{fingerprint}"
                version["id"] = version_id
        
        # 合并和存储元数据
        metadata = self._get_version_metadata(version_id) or {}
        
        # 更新注解，但保留不可变字段
        immutable_fields = {"fingerprint", "generated_at", "parent_version"}
        for key, value in annotations.items():
            if key not in immutable_fields or key not in metadata:
                metadata[key] = value
        
        # 保存注解
        self._save_version_metadata(version_id, metadata)
        
        # 更新缓存
        self.metadata_cache[version_id] = metadata
        
        return version_id
    
    def create_version_anchor(self, 
                             version: Dict[str, Any], 
                             anchor_type: str,
                             anchor_data: Dict[str, Any],
                             parent_id: Optional[str] = None) -> str:
        """
        创建版本锚点
        
        Args:
            version: 版本内容
            anchor_type: 锚点类型
            anchor_data: 锚点数据
            parent_id: 父版本ID
            
        Returns:
            str: 创建的锚点ID
        """
        # 提取版本内容和计算指纹
        content = self._extract_version_content(version)
        fingerprint = hashlib.sha256(content.encode()).hexdigest()
        
        # 创建锚点元数据
        anchor_metadata = {
            "fingerprint": fingerprint,
            "type": anchor_type,
            "created_at": datetime.now().isoformat(),
            "data": anchor_data
        }
        
        if parent_id:
            anchor_metadata["parent_id"] = parent_id
            
        # 生成锚点ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        anchor_id = f"anchor_{anchor_type}_{timestamp}"
        
        # 存储锚点元数据
        self._save_version_metadata(anchor_id, anchor_metadata)
        
        # 创建快照
        description = f"锚点: {anchor_type}"
        if "description" in anchor_data:
            description += f" - {anchor_data['description']}"
            
        snapshot_id = self.snapshotter.take_snapshot(
            version,
            operation=f"创建{anchor_type}锚点",
            snapshot_type=SnapshotType.CUSTOM,
            description=description,
            tags=[anchor_type, "anchor"]
        )
        
        # 关联锚点和快照
        anchor_metadata["snapshot_id"] = snapshot_id
        self._save_version_metadata(anchor_id, anchor_metadata)
        
        return anchor_id
    
    def find_anchors_by_type(self, anchor_type: str) -> List[Dict[str, Any]]:
        """
        按类型查找锚点
        
        Args:
            anchor_type: 锚点类型
            
        Returns:
            List[Dict[str, Any]]: 锚点列表
        """
        anchors = []
        
        # 扫描元数据目录
        for filename in os.listdir(self.metadata_dir):
            if filename.startswith(f"anchor_{anchor_type}_") and filename.endswith(".json"):
                anchor_id = filename[:-5]  # 移除.json后缀
                metadata = self._get_version_metadata(anchor_id)
                if metadata:
                    metadata["id"] = anchor_id
                    anchors.append(metadata)
        
        # 按创建时间排序
        anchors.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return anchors
    
    def find_anchors_by_fingerprint(self, fingerprint: str, partial_match: bool = False) -> List[Dict[str, Any]]:
        """
        按指纹查找锚点
        
        Args:
            fingerprint: 版本指纹
            partial_match: 是否允许部分匹配
            
        Returns:
            List[Dict[str, Any]]: 锚点列表
        """
        anchors = []
        
        # 扫描元数据目录
        for filename in os.listdir(self.metadata_dir):
            if filename.endswith(".json"):
                anchor_id = filename[:-5]
                metadata = self._get_version_metadata(anchor_id)
                
                if metadata and "fingerprint" in metadata:
                    meta_fingerprint = metadata["fingerprint"]
                    
                    if (partial_match and fingerprint in meta_fingerprint) or meta_fingerprint == fingerprint:
                        metadata["id"] = anchor_id
                        anchors.append(metadata)
        
        # 按创建时间排序
        anchors.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return anchors
    
    def compare_version_metadata(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """
        比较两个版本的元数据
        
        Args:
            version_id1: 第一个版本ID
            version_id2: 第二个版本ID
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        metadata1 = self._get_version_metadata(version_id1) or {}
        metadata2 = self._get_version_metadata(version_id2) or {}
        
        # 比较元数据
        common_keys = set(metadata1.keys()) & set(metadata2.keys())
        only_in_1 = set(metadata1.keys()) - set(metadata2.keys())
        only_in_2 = set(metadata2.keys()) - set(metadata1.keys())
        
        # 找出共同键但值不同的项
        differences = {}
        for key in common_keys:
            if metadata1[key] != metadata2[key]:
                differences[key] = {
                    "version1": metadata1[key],
                    "version2": metadata2[key]
                }
        
        return {
            "common_keys": list(common_keys),
            "only_in_version1": list(only_in_1),
            "only_in_version2": list(only_in_2),
            "differences": differences
        }
    
    def enrich_snapshot_metadata(self, snapshot_id: str, metadata: Dict[str, Any]) -> bool:
        """
        丰富快照元数据
        
        Args:
            snapshot_id: 快照ID
            metadata: 要添加的元数据
            
        Returns:
            bool: 是否成功
        """
        # 获取快照元数据
        snapshot_metadata = self.snapshotter.get_snapshot_metadata(snapshot_id)
        if not snapshot_metadata:
            logger.warning(f"快照不存在: {snapshot_id}")
            return False
        
        # 更新元数据
        node = self.snapshotter.version_tree.get_node(snapshot_id)
        if not node:
            logger.warning(f"版本节点不存在: {snapshot_id}")
            return False
        
        # 更新节点元数据
        for key, value in metadata.items():
            node.metadata[key] = value
        
        # 保存版本树
        self.snapshotter._save_version_tree()
        
        # 同时保存在元数据系统中
        self._save_version_metadata(snapshot_id, metadata)
        
        return True
    
    def find_version_ancestry(self, version_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        查找版本祖先
        
        Args:
            version_id: 版本ID
            max_depth: 最大深度
            
        Returns:
            List[Dict[str, Any]]: 祖先列表
        """
        ancestry = []
        current_id = version_id
        depth = 0
        
        while current_id and depth < max_depth:
            metadata = self._get_version_metadata(current_id)
            if not metadata:
                break
                
            ancestry.append({
                "id": current_id,
                "metadata": metadata
            })
            
            # 查找父版本
            current_id = metadata.get("parent_version")
            depth += 1
        
        return ancestry
    
    def track_version_evolution(self, base_version_id: str) -> List[Dict[str, Any]]:
        """
        追踪版本演变
        
        Args:
            base_version_id: 基础版本ID
            
        Returns:
            List[Dict[str, Any]]: 演变路径
        """
        # 找到所有以此版本为基础的版本
        evolution = []
        
        # 扫描元数据目录
        for filename in os.listdir(self.metadata_dir):
            if filename.endswith(".json"):
                version_id = filename[:-5]
                metadata = self._get_version_metadata(version_id)
                
                if metadata and metadata.get("parent_version") == base_version_id:
                    evolution.append({
                        "id": version_id,
                        "metadata": metadata
                    })
        
        # 按创建时间排序
        evolution.sort(key=lambda x: x["metadata"].get("created_at", ""))
        
        return evolution
    
    def _extract_version_content(self, version: Dict[str, Any]) -> str:
        """
        提取版本内容用于生成指纹
        
        Args:
            version: 版本内容
            
        Returns:
            str: 提取的文本
        """
        content = ""
        
        # 从不同格式中提取文本
        if "screenplay" in version and isinstance(version["screenplay"], list):
            # 从场景列表中提取
            for scene in version["screenplay"]:
                if isinstance(scene, dict):
                    if "content" in scene:
                        content += scene["content"] + "\n"
                    if "dialogue" in scene and isinstance(scene["dialogue"], list):
                        for line in scene["dialogue"]:
                            if isinstance(line, dict) and "text" in line:
                                content += line["text"] + "\n"
                            elif isinstance(line, str):
                                content += line + "\n"
        
        # 如果是字幕格式
        elif "subtitles" in version and isinstance(version["subtitles"], list):
            for subtitle in version["subtitles"]:
                if isinstance(subtitle, dict) and "text" in subtitle:
                    content += subtitle["text"] + "\n"
        
        # 如果有脚本文本字段
        elif "script_text" in version and isinstance(version["script_text"], str):
            content += version["script_text"]
            
        # 如果提供了原始内容
        elif "content" in version and isinstance(version["content"], str):
            content += version["content"]
            
        # 清理文本以获得一致的指纹
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _get_version_metadata(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        获取版本元数据
        
        Args:
            version_id: 版本ID
            
        Returns:
            Optional[Dict[str, Any]]: 元数据，如果不存在则返回None
        """
        # 检查缓存
        if version_id in self.metadata_cache:
            return self.metadata_cache[version_id]
            
        # 从文件加载
        metadata_path = os.path.join(self.metadata_dir, f"{version_id}.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                # 更新缓存
                self.metadata_cache[version_id] = metadata
                return metadata
            except Exception as e:
                logger.error(f"加载元数据失败: {str(e)}")
                
        return None
    
    def _save_version_metadata(self, version_id: str, metadata: Dict[str, Any]) -> bool:
        """
        保存版本元数据
        
        Args:
            version_id: 版本ID
            metadata: 元数据
            
        Returns:
            bool: 是否成功
        """
        metadata_path = os.path.join(self.metadata_dir, f"{version_id}.json")
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            # 更新缓存
            self.metadata_cache[version_id] = metadata
            return True
        except Exception as e:
            logger.error(f"保存元数据失败: {str(e)}")
            return False


class AnchorManager:
    """元数据锚点管理器，提供创建和查询锚点的接口"""
    
    def __init__(self, 
                snapshotter: Optional[Snapshotter] = None,
                annotator: Optional[VersionAnnotator] = None):
        """
        初始化锚点管理器
        
        Args:
            snapshotter: 快照管理器实例
            annotator: 版本注解器实例
        """
        self.snapshotter = snapshotter or Snapshotter()
        self.annotator = annotator or VersionAnnotator(snapshotter=self.snapshotter)
        
    def create_milestone(self, 
                        version: Dict[str, Any], 
                        name: str,
                        description: str = "",
                        tags: Optional[List[str]] = None) -> str:
        """
        创建里程碑锚点
        
        Args:
            version: 版本内容
            name: 里程碑名称
            description: 里程碑描述
            tags: 标签列表
            
        Returns:
            str: 创建的锚点ID
        """
        milestone_data = {
            "name": name,
            "description": description,
            "tags": tags or []
        }
        
        anchor_id = self.annotator.create_version_anchor(
            version,
            "milestone",
            milestone_data
        )
        
        logger.info(f"创建里程碑: {name} (ID: {anchor_id})")
        return anchor_id
    
    def create_reference_point(self, 
                              version: Dict[str, Any],
                              reference_type: str,
                              reference_data: Dict[str, Any]) -> str:
        """
        创建参考点锚点
        
        Args:
            version: 版本内容
            reference_type: 参考点类型
            reference_data: 参考点数据
            
        Returns:
            str: 创建的锚点ID
        """
        reference_data["type"] = reference_type
        
        anchor_id = self.annotator.create_version_anchor(
            version,
            "reference",
            reference_data
        )
        
        logger.info(f"创建参考点: {reference_type} (ID: {anchor_id})")
        return anchor_id
    
    def mark_critical_version(self, 
                            version: Dict[str, Any],
                            importance: int = 5,
                            reason: str = "") -> str:
        """
        标记关键版本
        
        Args:
            version: 版本内容
            importance: 重要性级别(1-10)
            reason: 重要性原因
            
        Returns:
            str: 创建的锚点ID
        """
        critical_data = {
            "importance": max(1, min(10, importance)),
            "reason": reason,
            "marked_at": datetime.now().isoformat()
        }
        
        anchor_id = self.annotator.create_version_anchor(
            version,
            "critical",
            critical_data
        )
        
        logger.info(f"标记关键版本 (级别: {importance}, ID: {anchor_id})")
        return anchor_id
    
    def list_milestones(self) -> List[Dict[str, Any]]:
        """
        列出所有里程碑
        
        Returns:
            List[Dict[str, Any]]: 里程碑列表
        """
        return self.annotator.find_anchors_by_type("milestone")
    
    def list_reference_points(self, reference_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出参考点
        
        Args:
            reference_type: 参考点类型筛选
            
        Returns:
            List[Dict[str, Any]]: 参考点列表
        """
        references = self.annotator.find_anchors_by_type("reference")
        
        if reference_type:
            references = [
                ref for ref in references 
                if ref.get("data", {}).get("type") == reference_type
            ]
            
        return references
    
    def list_critical_versions(self, min_importance: int = 1) -> List[Dict[str, Any]]:
        """
        列出关键版本
        
        Args:
            min_importance: 最小重要性级别
            
        Returns:
            List[Dict[str, Any]]: 关键版本列表
        """
        criticals = self.annotator.find_anchors_by_type("critical")
        
        if min_importance > 1:
            criticals = [
                critical for critical in criticals 
                if critical.get("data", {}).get("importance", 0) >= min_importance
            ]
            
        return criticals
    
    def find_similar_versions(self, version: Dict[str, Any], threshold: float = 0.9) -> List[Dict[str, Any]]:
        """
        查找相似版本
        
        Args:
            version: 版本内容
            threshold: 相似度阈值
            
        Returns:
            List[Dict[str, Any]]: 相似版本列表
        """
        # 计算当前版本的指纹
        content = self.annotator._extract_version_content(version)
        fingerprint = hashlib.sha256(content.encode()).hexdigest()
        
        # 查找具有相同或部分相同指纹的版本
        anchors = self.annotator.find_anchors_by_fingerprint(
            fingerprint[:int(len(fingerprint) * threshold)], 
            partial_match=True
        )
        
        # 为每个锚点加载对应的快照内容
        results = []
        for anchor in anchors:
            snapshot_id = anchor.get("snapshot_id")
            if snapshot_id:
                snapshot = self.snapshotter.restore_snapshot(snapshot_id)
                if snapshot:
                    results.append({
                        "anchor": anchor,
                        "snapshot": snapshot
                    })
        
        return results
    
    def get_version_with_metadata(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        获取带有元数据的版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            Optional[Dict[str, Any]]: 带有元数据的版本
        """
        # 首先尝试加载元数据
        metadata = self.annotator._get_version_metadata(version_id)
        
        # 检查是否有对应的快照ID
        snapshot_id = metadata.get("snapshot_id") if metadata else None
        
        # 如果没有，可能version_id本身就是快照ID
        if not snapshot_id:
            snapshot_id = version_id
        
        # 加载快照内容
        snapshot = self.snapshotter.restore_snapshot(snapshot_id)
        if not snapshot:
            return None
            
        # 组合结果
        return {
            "id": version_id,
            "metadata": metadata or {},
            "content": snapshot
        }
    
    def build_ancestry_graph(self, version_ids: List[str]) -> Dict[str, Any]:
        """
        构建版本祖先关系图
        
        Args:
            version_ids: 版本ID列表
            
        Returns:
            Dict[str, Any]: 关系图数据
        """
        # 构建节点和边
        nodes = []
        edges = []
        node_ids = set()
        
        # 处理每个版本
        for version_id in version_ids:
            ancestry = self.annotator.find_version_ancestry(version_id)
            
            # 添加节点
            for i, ancestor in enumerate(ancestry):
                current_id = ancestor["id"]
                metadata = ancestor["metadata"]
                
                if current_id not in node_ids:
                    node_ids.add(current_id)
                    nodes.append({
                        "id": current_id,
                        "metadata": metadata,
                        "level": i
                    })
                
                # 添加边
                if i < len(ancestry) - 1:
                    parent_id = ancestry[i+1]["id"]
                    edges.append({
                        "from": parent_id,
                        "to": current_id,
                        "type": "parent"
                    })
        
        return {
            "nodes": nodes,
            "edges": edges
        }


# 全局实例
_ANNOTATOR = None
_ANCHOR_MANAGER = None

def get_version_annotator() -> VersionAnnotator:
    """获取版本注解器实例"""
    global _ANNOTATOR
    if _ANNOTATOR is None:
        _ANNOTATOR = VersionAnnotator()
    return _ANNOTATOR

def get_anchor_manager() -> AnchorManager:
    """获取锚点管理器实例"""
    global _ANCHOR_MANAGER
    if _ANCHOR_MANAGER is None:
        _ANCHOR_MANAGER = AnchorManager()
    return _ANCHOR_MANAGER

def tag_versions(versions: List[Dict[str, Any]], base_version_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """为版本添加元数据标签"""
    annotator = get_version_annotator()
    return annotator.tag_versions(versions, base_version_id)

def create_milestone(version: Dict[str, Any], name: str, description: str = "") -> str:
    """创建里程碑锚点"""
    manager = get_anchor_manager()
    return manager.create_milestone(version, name, description)

def list_milestones() -> List[Dict[str, Any]]:
    """列出所有里程碑"""
    manager = get_anchor_manager()
    return manager.list_milestones()

def mark_critical_version(version: Dict[str, Any], importance: int = 5, reason: str = "") -> str:
    """标记关键版本"""
    manager = get_anchor_manager()
    return manager.mark_critical_version(version, importance, reason) 