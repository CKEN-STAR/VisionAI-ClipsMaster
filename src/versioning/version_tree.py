#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本树模块

实现版本树结构，支持分支管理、版本历史查询和版本恢复功能。
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import uuid

# 设置日志记录器
logger = logging.getLogger("version_tree")

class VersionNode:
    """版本节点类，表示版本树中的一个节点"""
    
    def __init__(self, 
                node_id: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None,
                parent: Optional['VersionNode'] = None):
        """
        初始化版本节点
        
        Args:
            node_id: 节点ID，如果为None则自动生成
            metadata: 节点元数据
            parent: 父节点
        """
        self.node_id = node_id if node_id else str(uuid.uuid4())
        self.metadata = metadata or {}
        self.parent = parent
        self.children = []
        self.created_at = time.time()
        
    def add_child(self, child: 'VersionNode') -> None:
        """添加子节点"""
        child.parent = self
        self.children.append(child)
        
    def get_path(self) -> List[str]:
        """获取从根节点到当前节点的路径"""
        if not self.parent:
            return [self.node_id]
        
        return self.parent.get_path() + [self.node_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """将节点转换为字典"""
        return {
            "id": self.node_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "children": [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], parent: Optional['VersionNode'] = None) -> 'VersionNode':
        """从字典创建节点"""
        node = cls(node_id=data["id"], metadata=data["metadata"], parent=parent)
        node.created_at = data.get("created_at", time.time())
        
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data, node)
            node.add_child(child)
            
        return node


class VersionTree:
    """版本树类，管理版本节点的层次结构"""
    
    def __init__(self, root_metadata: Optional[Dict[str, Any]] = None):
        """
        初始化版本树
        
        Args:
            root_metadata: 根节点元数据
        """
        # 创建根节点
        root_meta = root_metadata or {"type": "root", "description": "初始版本"}
        self.root = VersionNode(node_id="root", metadata=root_meta)
        self.current_node = self.root
        self.nodes_by_id = {"root": self.root}
        
    def add_node(self, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> str:
        """
        添加新节点
        
        Args:
            metadata: 节点元数据
            parent_id: 父节点ID，如果为None则使用当前节点
            
        Returns:
            新节点的ID
        """
        # 确定父节点
        parent = self.current_node
        if parent_id:
            if parent_id in self.nodes_by_id:
                parent = self.nodes_by_id[parent_id]
            else:
                raise ValueError(f"父节点ID不存在: {parent_id}")
        
        # 创建新节点
        new_node = VersionNode(metadata=metadata, parent=parent)
        parent.add_child(new_node)
        
        # 更新索引并设置为当前节点
        self.nodes_by_id[new_node.node_id] = new_node
        self.current_node = new_node
        
        logger.info(f"创建新版本节点: {new_node.node_id}")
        return new_node.node_id
    
    def get_node(self, node_id: str) -> Optional[VersionNode]:
        """获取指定ID的节点"""
        return self.nodes_by_id.get(node_id)
    
    def switch_to(self, node_id: str) -> bool:
        """切换当前节点"""
        if node_id in self.nodes_by_id:
            self.current_node = self.nodes_by_id[node_id]
            logger.info(f"切换到节点: {node_id}")
            return True
        return False
    
    def get_current_path(self) -> List[str]:
        """获取当前路径"""
        return self.current_node.get_path()
    
    def get_history(self, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取历史记录
        
        Args:
            node_id: 节点ID，如果为None则使用当前节点
            
        Returns:
            历史记录列表
        """
        # 确定起始节点
        start_node = self.current_node
        if node_id:
            if node_id in self.nodes_by_id:
                start_node = self.nodes_by_id[node_id]
            else:
                return []
        
        # 收集历史记录
        history = []
        current = start_node
        
        while current:
            history.insert(0, {
                "id": current.node_id,
                "metadata": current.metadata,
                "created_at": current.created_at
            })
            current = current.parent
            
        return history
    
    def find_branch_point(self, node_id1: str, node_id2: str) -> Optional[str]:
        """查找两个节点的分支点"""
        if node_id1 not in self.nodes_by_id or node_id2 not in self.nodes_by_id:
            return None
            
        path1 = self.nodes_by_id[node_id1].get_path()
        path2 = self.nodes_by_id[node_id2].get_path()
        
        # 查找最后一个共同祖先
        i = 0
        while i < len(path1) and i < len(path2) and path1[i] == path2[i]:
            i += 1
            
        if i > 0:
            return path1[i-1]
        return None
    
    def get_all_leaf_nodes(self) -> List[VersionNode]:
        """获取所有叶子节点"""
        leaves = []
        
        def collect_leaves(node):
            if not node.children:
                leaves.append(node)
            else:
                for child in node.children:
                    collect_leaves(child)
        
        collect_leaves(self.root)
        return leaves
    
    def to_dict(self) -> Dict[str, Any]:
        """将版本树转换为字典"""
        return {
            "root": self.root.to_dict(),
            "current_node_id": self.current_node.node_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionTree':
        """从字典创建版本树"""
        tree = cls()
        
        # 清除默认的根节点
        tree.root = VersionNode.from_dict(data["root"])
        tree.nodes_by_id = {}
        
        # 索引所有节点
        def index_nodes(node):
            tree.nodes_by_id[node.node_id] = node
            for child in node.children:
                index_nodes(child)
        
        index_nodes(tree.root)
        
        # 设置当前节点
        current_id = data.get("current_node_id", "root")
        if current_id in tree.nodes_by_id:
            tree.current_node = tree.nodes_by_id[current_id]
        else:
            tree.current_node = tree.root
            
        return tree
    
    def save_to_file(self, filepath: str) -> bool:
        """保存版本树到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"版本树已保存到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存版本树失败: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['VersionTree']:
        """从文件加载版本树"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tree = cls.from_dict(data)
            logger.info(f"从文件加载版本树: {filepath}")
            return tree
        except Exception as e:
            logger.error(f"加载版本树失败: {e}")
            return None


# 便捷函数
def create_version_tree(root_metadata: Optional[Dict[str, Any]] = None) -> VersionTree:
    """创建新的版本树"""
    return VersionTree(root_metadata)


if __name__ == "__main__":
    # 简单测试
    tree = create_version_tree({"description": "测试版本树"})
    
    # 添加一些节点
    node1 = tree.add_node({"operation": "初始线性版本", "type": "linear"})
    node2 = tree.add_node({"operation": "添加场景", "type": "linear"})
    
    # 切换回第一个节点并创建分支
    tree.switch_to(node1)
    node3 = tree.add_node({"operation": "重构版本", "type": "restructured"})
    
    # 打印历史记录
    print(f"当前节点: {tree.current_node.node_id}")
    print("历史记录:")
    for item in tree.get_history():
        print(f"  - {item['id']}: {item['metadata'].get('operation', 'N/A')}")
    
    # 打印所有叶子节点
    print("\n叶子节点:")
    for leaf in tree.get_all_leaf_nodes():
        print(f"  - {leaf.node_id}: {leaf.metadata.get('operation', 'N/A')}") 