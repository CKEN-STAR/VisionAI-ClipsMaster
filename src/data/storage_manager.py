#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
存储管理器模块

管理用户数据、内容数据和系统配置的存储和检索。
提供统一的接口，屏蔽底层存储实现细节。
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
import uuid
from pathlib import Path
import sqlite3
import logging
from loguru import logger

from src.utils.log_handler import get_logger

# 配置日志
storage_logger = get_logger("storage_manager")

# 全局存储管理器实例
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """获取存储管理器实例
    
    Returns:
        StorageManager: 存储管理器实例
    """
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager

class StorageManager:
    """存储管理器
    
    统一管理系统数据的存储和检索，支持多种存储后端。
    当前版本为演示用途，使用简单的文件系统存储。
    """
    
    def __init__(self, data_dir: str = None):
        """初始化存储管理器
        
        Args:
            data_dir: 数据存储目录，默认为src/data
        """
        # 设置数据目录
        if data_dir is None:
            # 使用相对于当前文件的路径
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
        else:
            self.data_dir = data_dir
        
        # 创建必要的目录结构
        self._ensure_directories()
        
        # 初始化数据库连接（如果需要）
        self.db_conn = None
        
        storage_logger.info(f"存储管理器初始化完成，数据目录: {self.data_dir}")
    
    def _ensure_directories(self):
        """确保必要的目录结构存在"""
        dirs = [
            "users",           # 用户数据
            "profiles",        # 用户画像
            "content",         # 内容数据
            "actions",         # 用户动作
            "views",           # 内容观看记录
            "sessions",        # 用户会话
            "feedback",        # 用户反馈
            "cache",           # 缓存数据
            "config"           # 配置数据
        ]
        
        for dir_name in dirs:
            dir_path = os.path.join(self.data_dir, dir_name)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                    storage_logger.debug(f"创建目录: {dir_path}")
                except Exception as e:
                    storage_logger.error(f"创建目录 {dir_path} 失败: {str(e)}")
        
        # 确保用户目录下的视图目录存在
        views_dir = os.path.join(self.data_dir, "views")
        if os.path.exists(views_dir):
            # 创建测试用户的视图目录
            test_user_views_dir = os.path.join(views_dir, "test_user_001")
            if not os.path.exists(test_user_views_dir):
                try:
                    os.makedirs(test_user_views_dir)
                    storage_logger.debug(f"创建目录: {test_user_views_dir}")
                except Exception as e:
                    storage_logger.error(f"创建目录 {test_user_views_dir} 失败: {str(e)}")
    
    def _get_user_dir(self, user_id: str) -> str:
        """获取用户数据目录
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户数据目录路径
        """
        user_dir = os.path.join(self.data_dir, "users", user_id)
        if not os.path.exists(user_dir):
            try:
                os.makedirs(user_dir)
            except Exception as e:
                storage_logger.error(f"创建用户目录 {user_dir} 失败: {str(e)}")
        return user_dir
    
    def _save_json(self, data: Any, file_path: str) -> bool:
        """将数据保存为JSON文件
        
        Args:
            data: 要保存的数据
            file_path: 文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            storage_logger.error(f"保存数据到 {file_path} 失败: {str(e)}")
            return False
    
    def _load_json(self, file_path: str) -> Optional[Any]:
        """从JSON文件加载数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Any]: 加载的数据，如果失败则返回None
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            storage_logger.error(f"从 {file_path} 加载数据失败: {str(e)}")
            return None
    
    # 用户画像相关方法
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """保存用户画像
        
        Args:
            user_id: 用户ID
            profile: 用户画像数据
            
        Returns:
            bool: 保存是否成功
        """
        file_path = os.path.join(self.data_dir, "profiles", f"{user_id}.json")
        return self._save_json(profile, file_path)
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户画像数据，如果不存在则返回None
        """
        file_path = os.path.join(self.data_dir, "profiles", f"{user_id}.json")
        return self._load_json(file_path)
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户基本数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户基本数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "user_data.json")
        return self._load_json(file_path)
    
    def get_user_devices(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户设备数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户设备数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "devices.json")
        return self._load_json(file_path)
    
    def get_user_biometric_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户生物识别数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户生物识别数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "biometric.json")
        return self._load_json(file_path)
    
    # 用户行为相关方法
    
    def store_user_action(self, user_id: str, action_data: Dict[str, Any]) -> bool:
        """存储用户动作
        
        Args:
            user_id: 用户ID
            action_data: 动作数据
            
        Returns:
            bool: 存储是否成功
        """
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        action_id = action_data.get("action_id", str(uuid.uuid4()))
        file_name = f"{timestamp}_{action_id}.json"
        
        # 保存动作数据
        file_path = os.path.join(self.data_dir, "actions", user_id, file_name)
        return self._save_json(action_data, file_path)
    
    def get_user_actions(self, user_id: str, start_date: datetime = None, 
                      end_date: datetime = None) -> List[Dict[str, Any]]:
        """获取用户动作
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict[str, Any]]: 用户动作列表
        """
        # 用户动作目录
        actions_dir = os.path.join(self.data_dir, "actions", user_id)
        
        # 确保目录存在
        if not os.path.exists(actions_dir):
            return []
        
        # 获取所有动作文件
        action_files = [f for f in os.listdir(actions_dir) if f.endswith(".json")]
        
        # 如果没有设置日期范围，返回所有动作
        if start_date is None and end_date is None:
            actions = []
            for file_name in action_files:
                file_path = os.path.join(actions_dir, file_name)
                action = self._load_json(file_path)
                if action:
                    actions.append(action)
            return actions
        
        # 设置默认日期范围
        if start_date is None:
            start_date = datetime.min
        if end_date is None:
            end_date = datetime.max
        
        # 按日期范围过滤动作
        filtered_actions = []
        for file_name in action_files:
            file_path = os.path.join(actions_dir, file_name)
            action = self._load_json(file_path)
            
            if action and "timestamp" in action:
                try:
                    action_date = datetime.fromisoformat(action["timestamp"])
                    if start_date <= action_date <= end_date:
                        filtered_actions.append(action)
                except:
                    # 忽略日期解析错误
                    pass
        
        return filtered_actions
    
    def get_user_behavior_data(self, user_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """获取用户行为数据
        
        Args:
            user_id: 用户ID
            days: 天数
            
        Returns:
            Optional[Dict[str, Any]]: 用户行为数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "behavior.json")
        behavior_data = self._load_json(file_path)
        
        # 如果没有行为数据，构造一个空的结构
        if behavior_data is None:
            return {
                "completions": [],
                "sessions": [],
                "genre_views": {},
                "content_types": {},
                "binge_data": {"is_binger": False}
            }
        
        return behavior_data
    
    def get_user_temporal_data(self, user_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """获取用户时间模式数据
        
        Args:
            user_id: 用户ID
            days: 天数
            
        Returns:
            Optional[Dict[str, Any]]: 用户时间模式数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "temporal.json")
        return self._load_json(file_path)
    
    def get_user_interaction_data(self, user_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """获取用户交互数据
        
        Args:
            user_id: 用户ID
            days: 天数
            
        Returns:
            Optional[Dict[str, Any]]: 用户交互数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "interaction.json")
        return self._load_json(file_path)
    
    def get_user_social_data(self, user_id: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """获取用户社交数据
        
        Args:
            user_id: 用户ID
            days: 天数
            
        Returns:
            Optional[Dict[str, Any]]: 用户社交数据，如果不存在则返回None
        """
        file_path = os.path.join(self._get_user_dir(user_id), "social.json")
        return self._load_json(file_path)
    
    def get_user_view_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户观看历史
        
        Args:
            user_id: 用户ID
            limit: 历史记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 观看历史记录
        """
        try:
            view_path = os.path.join(self.data_dir, "views", user_id, "view_history.json")
            if not os.path.exists(view_path):
                return []
            
            with open(view_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 限制记录数量
            return history[:limit] if history else []
        except Exception as e:
            storage_logger.error(f"获取用户 {user_id} 观看历史失败: {str(e)}")
            return [] 