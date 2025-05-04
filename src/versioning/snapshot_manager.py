#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快照管理器

提供脚本和场景内容的快照功能，允许创建、恢复和管理不同版本的内容。
支持多种快照类型：线性版本、倒叙重构版、多线实验版和最终优化版。
"""

import os
import json
import time
import logging
import hashlib
import shutil
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from datetime import datetime

# 导入版本树
from .version_tree import VersionTree, create_version_tree

# 创建日志记录器
logger = logging.getLogger("snapshot_manager")

# 定义快照类型
class SnapshotType(Enum):
    """快照类型枚举"""
    LINEAR = "linear"            # 初始线性版
    RESTRUCTURED = "restructured"  # 倒叙重构版
    EXPERIMENTAL = "experimental"  # 多线实验版
    OPTIMIZED = "optimized"      # 最终优化版
    CUSTOM = "custom"            # 自定义类型


class Snapshotter:
    """快照管理器，负责创建和管理内容快照"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化快照管理器
        
        Args:
            storage_dir: 快照存储目录，默认为 data/snapshots
        """
        # 初始化版本树
        self.version_tree = VersionTree()
        
        # 设置存储目录
        self.storage_dir = storage_dir or os.path.join("data", "snapshots")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 版本树存储路径
        self.version_tree_path = os.path.join(self.storage_dir, "version_tree.json")
        
        # 尝试加载现有版本树
        self._load_version_tree()
        
        logger.info("快照管理器初始化完成")
    
    def _load_version_tree(self) -> None:
        """加载版本树"""
        if os.path.exists(self.version_tree_path):
            loaded_tree = VersionTree.load_from_file(self.version_tree_path)
            if loaded_tree:
                self.version_tree = loaded_tree
                logger.info("加载现有版本树")
            else:
                logger.warning("加载版本树失败，使用新的版本树")
        else:
            logger.info("未找到现有版本树，创建新版本树")
    
    def _save_version_tree(self) -> None:
        """保存版本树"""
        self.version_tree.save_to_file(self.version_tree_path)
    
    def take_snapshot(self, 
                     script: Dict[str, Any], 
                     operation: str,
                     snapshot_type: Union[SnapshotType, str] = SnapshotType.LINEAR,
                     description: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     parent_id: Optional[str] = None) -> str:
        """
        创建内容快照
        
        Args:
            script: 脚本内容（场景、字幕等）
            operation: 操作描述
            snapshot_type: 快照类型
            description: 快照描述
            tags: 标签列表
            parent_id: 父节点ID
            
        Returns:
            快照ID
        """
        # 如果传入的是字符串，转换为枚举
        if isinstance(snapshot_type, str):
            try:
                snapshot_type = SnapshotType(snapshot_type)
            except ValueError:
                snapshot_type = SnapshotType.CUSTOM
        
        # 计算内容哈希
        script_hash = self._hash_script(script)
        
        # 准备元数据
        metadata = {
            "hash": script_hash,
            "operation": operation,
            "type": snapshot_type.value if isinstance(snapshot_type, SnapshotType) else snapshot_type,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
        }
        
        if description:
            metadata["description"] = description
        
        if tags:
            metadata["tags"] = tags
        
        # 添加到版本树
        snapshot_id = self.version_tree.add_node(metadata, parent_id)
        
        # 保存内容
        self._save_snapshot_content(snapshot_id, script)
        
        # 保存版本树
        self._save_version_tree()
        
        logger.info(f"创建快照: {snapshot_id}, 操作: {operation}, 类型: {metadata['type']}")
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复快照内容
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的内容，失败返回None
        """
        # 检查快照是否存在
        if not self.version_tree.get_node(snapshot_id):
            logger.error(f"快照不存在: {snapshot_id}")
            return None
        
        # 切换到该节点
        self.version_tree.switch_to(snapshot_id)
        
        # 加载内容
        content = self._load_snapshot_content(snapshot_id)
        if not content:
            logger.error(f"无法加载快照内容: {snapshot_id}")
            return None
        
        # 保存版本树状态
        self._save_version_tree()
        
        logger.info(f"恢复快照: {snapshot_id}")
        return content
    
    def get_current_snapshot_id(self) -> str:
        """获取当前快照ID"""
        return self.version_tree.current_node.node_id
    
    def list_snapshots(self, 
                      snapshot_type: Optional[Union[SnapshotType, str]] = None,
                      tag: Optional[str] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        列出快照
        
        Args:
            snapshot_type: 按类型筛选
            tag: 按标签筛选
            limit: 返回数量限制
            
        Returns:
            快照列表
        """
        # 获取所有节点
        snapshots = []
        
        for node_id, node in self.version_tree.nodes_by_id.items():
            if node_id == "root":
                continue  # 跳过根节点
                
            # 获取节点元数据
            metadata = node.metadata.copy()
            metadata["id"] = node_id
            
            # 类型筛选
            if snapshot_type:
                type_value = snapshot_type.value if isinstance(snapshot_type, SnapshotType) else snapshot_type
                if metadata.get("type") != type_value:
                    continue
            
            # 标签筛选
            if tag and "tags" in metadata:
                if tag not in metadata["tags"]:
                    continue
            
            # 添加到结果
            snapshots.append(metadata)
        
        # 按时间排序（新的在前）
        snapshots.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # 应用限制
        if limit and limit > 0:
            return snapshots[:limit]
            
        return snapshots
    
    def get_snapshot_metadata(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        获取快照元数据
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照元数据
        """
        node = self.version_tree.get_node(snapshot_id)
        if not node or snapshot_id == "root":
            return None
            
        metadata = node.metadata.copy()
        metadata["id"] = snapshot_id
        metadata["created_at"] = node.created_at
        
        # 添加路径信息
        metadata["path"] = node.get_path()
        
        # 添加父节点和子节点信息
        if node.parent and node.parent.node_id != "root":
            metadata["parent_id"] = node.parent.node_id
        
        if node.children:
            metadata["children"] = [child.node_id for child in node.children]
        
        return metadata
    
    def compare_snapshots(self, 
                         snapshot_id1: str, 
                         snapshot_id2: str) -> Optional[Dict[str, Any]]:
        """
        比较两个快照
        
        Args:
            snapshot_id1: 第一个快照ID
            snapshot_id2: 第二个快照ID
            
        Returns:
            比较结果，包含差异信息
        """
        # 检查快照是否存在
        node1 = self.version_tree.get_node(snapshot_id1)
        node2 = self.version_tree.get_node(snapshot_id2)
        
        if not node1 or not node2:
            logger.error("快照ID无效")
            return None
        
        # 获取内容
        content1 = self._load_snapshot_content(snapshot_id1)
        content2 = self._load_snapshot_content(snapshot_id2)
        
        if not content1 or not content2:
            logger.error("无法加载快照内容")
            return None
        
        # 查找分支点
        branch_point = self.version_tree.find_branch_point(snapshot_id1, snapshot_id2)
        
        # 准备比较结果
        result = {
            "snapshot1": {
                "id": snapshot_id1,
                "metadata": node1.metadata
            },
            "snapshot2": {
                "id": snapshot_id2,
                "metadata": node2.metadata
            },
            "branch_point": branch_point,
            "differences": {}
        }
        
        # 比较场景数量变化
        scenes1 = content1.get("scenes", [])
        scenes2 = content2.get("scenes", [])
        
        result["differences"]["scene_count"] = {
            "snapshot1": len(scenes1),
            "snapshot2": len(scenes2),
            "difference": len(scenes2) - len(scenes1)
        }
        
        # TODO: 更详细的比较逻辑，根据实际应用场景扩展
        
        return result
    
    def delete_snapshot(self, snapshot_id: str, recursive: bool = False) -> bool:
        """
        删除快照
        
        Args:
            snapshot_id: 快照ID
            recursive: 是否递归删除子节点
            
        Returns:
            是否删除成功
        """
        # 检查快照是否存在
        node = self.version_tree.get_node(snapshot_id)
        if not node or snapshot_id == "root":
            logger.error(f"无法删除快照: {snapshot_id}")
            return False
        
        # 检查是否有子节点且不递归删除
        if node.children and not recursive:
            logger.error(f"快照 {snapshot_id} 有子节点，无法删除。使用 recursive=True 递归删除")
            return False
        
        # 如果是当前节点，先切换到父节点
        if self.version_tree.current_node.node_id == snapshot_id:
            if node.parent:
                self.version_tree.switch_to(node.parent.node_id)
            else:
                logger.error("无法删除当前活动的根节点")
                return False
        
        # 收集要删除的节点ID
        to_delete = [snapshot_id]
        
        if recursive:
            def collect_children(node):
                for child in node.children:
                    to_delete.append(child.node_id)
                    collect_children(child)
            
            collect_children(node)
        
        # 从父节点移除
        if node.parent:
            node.parent.children = [c for c in node.parent.children if c.node_id != snapshot_id]
        
        # 从索引中移除
        for node_id in to_delete:
            if node_id in self.version_tree.nodes_by_id:
                del self.version_tree.nodes_by_id[node_id]
            
            # 删除内容文件
            content_path = self._get_snapshot_path(node_id)
            if os.path.exists(content_path):
                try:
                    os.remove(content_path)
                except Exception as e:
                    logger.warning(f"删除快照内容文件失败: {e}")
        
        # 保存版本树
        self._save_version_tree()
        
        logger.info(f"删除快照: {snapshot_id}, 递归: {recursive}, 共删除 {len(to_delete)} 个节点")
        return True
    
    def create_branch(self, 
                     from_snapshot_id: str, 
                     operation: str,
                     snapshot_type: Union[SnapshotType, str],
                     description: Optional[str] = None) -> Optional[str]:
        """
        从指定快照创建分支
        
        Args:
            from_snapshot_id: 源快照ID
            operation: 操作描述
            snapshot_type: 新分支类型
            description: 描述
            
        Returns:
            新分支ID，失败返回None
        """
        # 检查快照是否存在
        if not self.version_tree.get_node(from_snapshot_id):
            logger.error(f"源快照不存在: {from_snapshot_id}")
            return None
        
        # 加载源快照内容
        content = self._load_snapshot_content(from_snapshot_id)
        if not content:
            logger.error(f"无法加载源快照内容: {from_snapshot_id}")
            return None
        
        # 切换到源快照
        self.version_tree.switch_to(from_snapshot_id)
        
        # 创建新快照
        return self.take_snapshot(
            script=content,
            operation=operation,
            snapshot_type=snapshot_type,
            description=description
        )
    
    def _hash_script(self, script: Dict[str, Any]) -> str:
        """计算脚本内容的哈希值"""
        script_str = json.dumps(script, sort_keys=True)
        return hashlib.sha256(script_str.encode('utf-8')).hexdigest()
    
    def _get_snapshot_path(self, snapshot_id: str) -> str:
        """获取快照内容存储路径"""
        return os.path.join(self.storage_dir, f"{snapshot_id}.json")
    
    def _save_snapshot_content(self, snapshot_id: str, content: Dict[str, Any]) -> bool:
        """保存快照内容"""
        try:
            filepath = self._get_snapshot_path(snapshot_id)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存快照内容失败: {e}")
            return False
    
    def _load_snapshot_content(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照内容"""
        try:
            filepath = self._get_snapshot_path(snapshot_id)
            if not os.path.exists(filepath):
                logger.error(f"快照内容文件不存在: {filepath}")
                return None
                
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载快照内容失败: {e}")
            return None
    
    def get_snapshot_history(self, snapshot_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取快照历史记录"""
        return self.version_tree.get_history(snapshot_id)


# 便捷函数
_global_snapshotter = None

def get_snapshotter(storage_dir: Optional[str] = None) -> Snapshotter:
    """获取全局快照管理器实例"""
    global _global_snapshotter
    if _global_snapshotter is None:
        _global_snapshotter = Snapshotter(storage_dir)
    return _global_snapshotter

def take_snapshot(script: Dict[str, Any], 
                operation: str,
                snapshot_type: Union[SnapshotType, str] = SnapshotType.LINEAR,
                description: Optional[str] = None,
                tags: Optional[List[str]] = None) -> str:
    """创建快照的便捷函数"""
    return get_snapshotter().take_snapshot(script, operation, snapshot_type, description, tags)

def restore_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """恢复快照的便捷函数"""
    return get_snapshotter().restore_snapshot(snapshot_id)

def compare_snapshots(snapshot_id1: str, snapshot_id2: str) -> Optional[Dict[str, Any]]:
    """比较快照的便捷函数"""
    return get_snapshotter().compare_snapshots(snapshot_id1, snapshot_id2)

def list_snapshots(snapshot_type: Optional[Union[SnapshotType, str]] = None, 
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """列出快照的便捷函数"""
    return get_snapshotter().list_snapshots(snapshot_type, None, limit)

def get_snapshot_metadata(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """获取快照元数据的便捷函数"""
    return get_snapshotter().get_snapshot_metadata(snapshot_id)


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建快照管理器
    snapshotter = Snapshotter("temp_snapshots")
    
    # 测试脚本
    test_script = {
        "title": "测试脚本",
        "scenes": [
            {
                "id": "scene1",
                "content": "场景1内容"
            },
            {
                "id": "scene2",
                "content": "场景2内容"
            }
        ]
    }
    
    # 创建初始快照
    snapshot1 = snapshotter.take_snapshot(
        test_script,
        "初始版本",
        SnapshotType.LINEAR,
        "测试脚本的初始版本"
    )
    
    print(f"创建初始快照: {snapshot1}")
    
    # 修改脚本
    test_script["scenes"].append({
        "id": "scene3",
        "content": "场景3内容"
    })
    
    # 创建第二个快照
    snapshot2 = snapshotter.take_snapshot(
        test_script,
        "添加场景3",
        SnapshotType.LINEAR,
        "添加了新场景"
    )
    
    print(f"创建第二个快照: {snapshot2}")
    
    # 列出快照
    snapshots = snapshotter.list_snapshots(limit=5)
    print("\n所有快照:")
    for snap in snapshots:
        print(f"  {snap['id']}: {snap.get('operation')} - {snap.get('description', '')}")
    
    # 比较快照
    comparison = snapshotter.compare_snapshots(snapshot1, snapshot2)
    if comparison:
        print(f"\n快照比较结果: 场景数变化 {comparison['differences']['scene_count']['difference']}")
    
    # 从第一个快照创建分支
    branch = snapshotter.create_branch(
        snapshot1,
        "创建实验分支",
        SnapshotType.EXPERIMENTAL,
        "基于初始版本的实验分支"
    )
    
    print(f"\n创建分支: {branch}")
    
    # 获取当前快照的历史
    history = snapshotter.get_snapshot_history()
    print("\n当前快照历史:")
    for item in history:
        print(f"  {item['id']}: {item['metadata'].get('operation', '')}")
    
    print("\n测试完成，清理临时文件...")
    shutil.rmtree("temp_snapshots", ignore_errors=True) 