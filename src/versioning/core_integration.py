#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心集成模块

将版本快照功能与核心处理模块集成，提供场景、剧本和脚本的版本控制功能。
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import time
from datetime import datetime

# 导入快照管理器
from .snapshot_manager import (
    Snapshotter, 
    SnapshotType, 
    take_snapshot,
    restore_snapshot,
    get_snapshotter
)

# 创建日志记录器
logger = logging.getLogger("versioning_integration")

class SceneVersionManager:
    """场景版本管理器，集成到剧本工程师中"""
    
    def __init__(self, project_name: Optional[str] = None):
        """
        初始化场景版本管理器
        
        Args:
            project_name: 项目名称，用于创建专用存储目录
        """
        self.project_name = project_name or "default_project"
        
        # 设置存储目录
        storage_dir = os.path.join("data", "snapshots", self.project_name)
        os.makedirs(storage_dir, exist_ok=True)
        
        # 初始化快照管理器
        self.snapshotter = get_snapshotter(storage_dir)
        
    def save_scene_version(self, 
                         scenes: List[Dict[str, Any]], 
                         operation: str,
                         snapshot_type: Union[SnapshotType, str] = SnapshotType.LINEAR,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        保存场景版本
        
        Args:
            scenes: 场景列表
            operation: 操作描述
            snapshot_type: 快照类型
            metadata: 附加元数据
            
        Returns:
            快照ID
        """
        # 准备快照内容
        script_content = {
            "type": "scene_collection",
            "scenes": scenes,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        # 添加一些统计信息
        scene_count = len(scenes)
        script_content["metadata"]["scene_count"] = scene_count
        
        # 计算总时长
        total_duration = sum(
            scene.get("duration", 0) for scene in scenes
        )
        script_content["metadata"]["total_duration"] = total_duration
        
        # 提取主要角色
        characters = set()
        for scene in scenes:
            if "character" in scene:
                if isinstance(scene["character"], list):
                    characters.update(scene["character"])
                else:
                    characters.add(scene["character"])
            
            if "characters" in scene:
                if isinstance(scene["characters"], list):
                    characters.update(scene["characters"])
                elif isinstance(scene["characters"], str):
                    characters.add(scene["characters"])
        
        script_content["metadata"]["characters"] = list(characters)
        
        # 创建快照
        snapshot_id = self.snapshotter.take_snapshot(
            script=script_content,
            operation=operation,
            snapshot_type=snapshot_type,
            description=metadata.get("description") if metadata else None,
            tags=metadata.get("tags") if metadata else None
        )
        
        logger.info(f"保存场景版本: {snapshot_id}, 场景数: {scene_count}, 总时长: {total_duration:.1f}秒")
        return snapshot_id
    
    def load_scene_version(self, snapshot_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        加载场景版本
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            场景列表，失败返回None
        """
        content = self.snapshotter.restore_snapshot(snapshot_id)
        if not content:
            logger.error(f"加载场景版本失败: {snapshot_id}")
            return None
            
        # 验证内容类型
        if content.get("type") != "scene_collection":
            logger.error(f"快照类型不匹配，期望场景集合，但得到: {content.get('type')}")
            return None
            
        scenes = content.get("scenes", [])
        logger.info(f"已加载场景版本: {snapshot_id}, 场景数: {len(scenes)}")
        
        return scenes
    
    def create_experimental_branch(self, 
                                 from_snapshot_id: str, 
                                 operation: str,
                                 metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """创建实验分支"""
        return self.snapshotter.create_branch(
            from_snapshot_id,
            operation,
            SnapshotType.EXPERIMENTAL,
            metadata.get("description") if metadata else None
        )
    
    def create_restructured_branch(self,
                                 from_snapshot_id: str,
                                 operation: str,
                                 metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """创建倒叙重构分支"""
        return self.snapshotter.create_branch(
            from_snapshot_id,
            operation,
            SnapshotType.RESTRUCTURED,
            metadata.get("description") if metadata else None
        )
    
    def create_optimized_branch(self,
                              from_snapshot_id: str,
                              operation: str,
                              metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """创建最终优化分支"""
        return self.snapshotter.create_branch(
            from_snapshot_id,
            operation,
            SnapshotType.OPTIMIZED,
            metadata.get("description") if metadata else None
        )
    
    def get_version_history(self, snapshot_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return self.snapshotter.get_snapshot_history(snapshot_id)
    
    def list_versions(self, 
                     snapshot_type: Optional[Union[SnapshotType, str]] = None,
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出版本"""
        return self.snapshotter.list_snapshots(snapshot_type, None, limit)


# 集成到剧本工程师的插件函数
def integrate_versioning_to_screenplay_engineer():
    """将版本管理集成到剧本工程师"""
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        # 保存原始生成方法的引用
        original_generate = ScreenplayEngineer.generate_screenplay
        
        # 创建场景版本管理器
        version_manager = SceneVersionManager("screenplay_versions")
        
        def versioned_generate_screenplay(self, original_subtitles, language="auto"):
            """添加版本控制的场景生成方法"""
            # 调用原始方法
            result = original_generate(self, original_subtitles, language)
            
            # 如果生成成功，保存版本
            if result.get('status') == 'success':
                segments = result.get('segments', [])
                if segments:
                    # 创建快照
                    metadata = {
                        "template_used": result.get('template_used', "unknown"),
                        "language": language,
                        "processing_time": result.get('processing_time', 0),
                        "character_count": result.get('character_count', 0),
                        "scene_count": result.get('scene_count', 0),
                        "tags": ["auto_generated"]
                    }
                    
                    snapshot_id = version_manager.save_scene_version(
                        segments,
                        "自动生成剧本",
                        SnapshotType.LINEAR,
                        metadata
                    )
                    
                    # 将快照ID添加到结果中
                    result['snapshot_id'] = snapshot_id
                    
                    logger.info(f"已创建自动生成剧本版本: {snapshot_id}")
            
            return result
        
        # 替换方法
        ScreenplayEngineer.generate_screenplay = versioned_generate_screenplay
        
        # 添加版本管理相关方法
        ScreenplayEngineer.list_versions = lambda self: version_manager.list_versions()
        ScreenplayEngineer.load_version = lambda self, snapshot_id: version_manager.load_scene_version(snapshot_id)
        ScreenplayEngineer.get_version_history = lambda self, snapshot_id=None: version_manager.get_version_history(snapshot_id)
        
        logger.info("已将版本管理功能集成到剧本工程师")
        return True
    except Exception as e:
        logger.error(f"集成版本管理到剧本工程师失败: {e}")
        return False


# 初始化时自动集成
try:
    # 延迟集成，等待所有模块加载完成
    import threading
    threading.Timer(1.0, integrate_versioning_to_screenplay_engineer).start()
except Exception as e:
    logger.error(f"启动版本管理集成失败: {e}")


# 便捷函数
def get_scene_version_manager(project_name: Optional[str] = None) -> SceneVersionManager:
    """获取场景版本管理器"""
    return SceneVersionManager(project_name) 