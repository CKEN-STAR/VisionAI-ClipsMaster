#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时间轴版本管理面板

提供用户友好的界面来管理短剧混剪项目的时间轴版本，
包括版本历史查看、比较、恢复和导出功能。
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Callable

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.timecode import TimelineArchiver

class TimelineVersionPanel:
    """
    时间轴版本管理面板
    
    提供GUI界面来管理混剪项目的时间轴版本，
    包括版本历史查看、比较、恢复和导出等功能。
    
    注意: 这是UI组件的基础实现，实际使用时需要与PyQt5/PySide2等GUI框架集成。
    """
    
    def __init__(self, project_id: str = None, storage_dir: str = None):
        """
        初始化版本管理面板
        
        Args:
            project_id: 项目ID
            storage_dir: 存储目录
        """
        self.archiver = TimelineArchiver(project_id, storage_dir)
        self.current_version_id: Optional[str] = None
        self.selected_version_id: Optional[str] = None
        self.version_list: List[Dict] = []
        
        # 设置默认回调函数
        self.on_version_selected = lambda v_id: None
        self.on_version_loaded = lambda scenes: None
        self.on_version_deleted = lambda success: None
        
        # 加载初始版本列表
        self.refresh_version_list()
    
    def refresh_version_list(self) -> List[Dict]:
        """
        刷新版本列表
        
        Returns:
            版本信息列表
        """
        self.version_list = self.archiver.get_version_list()
        
        # 更新当前版本ID
        current_version = self.archiver.get_current_version()
        if current_version:
            self.current_version_id = current_version["metadata"]["version_id"]
        
        return self.version_list
    
    def set_on_version_selected(self, callback: Callable[[str], None]) -> None:
        """设置版本选择回调函数"""
        self.on_version_selected = callback
    
    def set_on_version_loaded(self, callback: Callable[[List[Dict]], None]) -> None:
        """设置版本加载回调函数"""
        self.on_version_loaded = callback
    
    def set_on_version_deleted(self, callback: Callable[[bool], None]) -> None:
        """设置版本删除回调函数"""
        self.on_version_deleted = callback
    
    def select_version(self, version_id: str) -> None:
        """
        选择版本
        
        Args:
            version_id: 要选择的版本ID
        """
        self.selected_version_id = version_id
        self.on_version_selected(version_id)
    
    def load_selected_version(self) -> Optional[List[Dict]]:
        """
        加载当前选中的版本
        
        Returns:
            加载的场景数据，如果没有选中版本则返回None
        """
        if not self.selected_version_id:
            return None
        
        scenes = self.archiver.load_version(self.selected_version_id)
        if scenes:
            self.current_version_id = self.selected_version_id
            self.on_version_loaded(scenes)
        
        return scenes
    
    def delete_selected_version(self) -> bool:
        """
        删除当前选中的版本
        
        Returns:
            删除操作是否成功
        """
        if not self.selected_version_id:
            return False
        
        success = self.archiver.delete_version(self.selected_version_id)
        if success:
            self.refresh_version_list()
            
            # 如果删除的是当前选中的版本，重置选中状态
            if self.selected_version_id == self.archiver.current_version_id:
                self.selected_version_id = self.archiver.current_version_id
            
        self.on_version_deleted(success)
        return success
    
    def save_new_version(self, scenes: List[Dict], note: str = "") -> Optional[str]:
        """
        保存新版本
        
        Args:
            scenes: 场景数据
            note: 版本说明
            
        Returns:
            新版本ID
        """
        version_id = self.archiver.save_version(scenes, note)
        if version_id:
            self.refresh_version_list()
            self.selected_version_id = version_id
            self.current_version_id = version_id
        return version_id
    
    def export_selected_version(self, export_path: str) -> bool:
        """
        导出选中的版本
        
        Args:
            export_path: 导出文件路径
            
        Returns:
            导出操作是否成功
        """
        if not self.selected_version_id:
            return False
        
        return self.archiver.export_version(self.selected_version_id, export_path)
    
    def import_version(self, import_path: str, note: str = None) -> Optional[str]:
        """
        导入版本
        
        Args:
            import_path: 导入文件路径
            note: 可选的版本说明
            
        Returns:
            导入的版本ID
        """
        version_id = self.archiver.import_version(import_path, note)
        if version_id:
            self.refresh_version_list()
            self.selected_version_id = version_id
        return version_id
    
    def compare_with_current(self) -> Optional[Dict]:
        """
        比较选中版本与当前版本
        
        Returns:
            比较结果
        """
        if not self.selected_version_id or not self.current_version_id:
            return None
        
        if self.selected_version_id == self.current_version_id:
            return {"error": "不能与自身比较"}
        
        return self.archiver.compare_versions(
            self.current_version_id,
            self.selected_version_id
        )
    
    def get_version_details(self, version_id: str) -> Optional[Dict]:
        """
        获取版本详细信息
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本详细信息
        """
        for version in self.version_list:
            if version["version_id"] == version_id:
                return version
        return None
    
    def format_version_list_for_display(self) -> List[Dict]:
        """
        格式化版本列表用于显示
        
        Returns:
            格式化后的版本列表
        """
        return [
            {
                "id": v["version_id"],
                "time": v["formatted_time"],
                "note": v["note"],
                "scenes": v["scene_count"],
                "is_current": v["version_id"] == self.current_version_id,
                "is_selected": v["version_id"] == self.selected_version_id
            }
            for v in self.version_list
        ]
    
    # 以下方法需要在具体GUI框架中实现
    
    def render(self):
        """
        渲染UI组件
        
        注意: 此方法需要在具体GUI框架(如PyQt5)中实现
        """
        pass
    
    def create_context_menu(self):
        """
        创建右键菜单
        
        注意: 此方法需要在具体GUI框架中实现
        """
        pass
    
    def create_diff_view(self, comparison_result):
        """
        创建差异对比视图
        
        注意: 此方法需要在具体GUI框架中实现
        """
        pass 