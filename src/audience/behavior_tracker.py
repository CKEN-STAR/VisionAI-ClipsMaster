#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户行为跟踪器模块

跟踪和记录用户的内容观看行为、交互动作和反馈，为用户画像构建和偏好分析提供数据支持。
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
import uuid
from collections import defaultdict, Counter
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager

# 配置日志
behavior_logger = get_logger("behavior_tracker")

class BehaviorTracker:
    """用户行为跟踪器
    
    跟踪和分析用户的观看行为、交互动作和反馈，
    为个性化内容推荐和用户体验优化提供数据支持。
    """
    
    def __init__(self):
        """初始化行为跟踪器"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 行为类型定义
        self.action_types = {
            # 内容交互
            "view": "内容观看",
            "complete": "完成观看",
            "like": "点赞",
            "comment": "评论",
            "share": "分享",
            "save": "收藏",
            "skip": "跳过",
            "pause": "暂停",
            "replay": "重播",
            "rate": "评分",
            
            # 界面交互
            "search": "搜索",
            "filter": "筛选",
            "navigate": "导航",
            "scroll": "滚动",
            "click": "点击",
            "hover": "悬停",
            
            # 用户反馈
            "feedback": "反馈",
            "error_report": "错误报告",
            "suggestion": "建议"
        }
        
        # 会话超时时间（分钟）
        self.session_timeout = 30
        
        # 活跃会话缓存
        self.active_sessions = {}
        
        behavior_logger.info("用户行为跟踪器初始化完成") 

    def track_user_action(self, user_id: str, action_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """跟踪用户动作
        
        记录用户的任何交互动作，包括界面交互、内容交互和反馈。
        
        Args:
            user_id: 用户ID
            action_type: 动作类型
            context: 动作上下文信息
            
        Returns:
            Dict[str, Any]: 记录的动作数据
        """
        # 验证动作类型
        if action_type not in self.action_types:
            behavior_logger.warning(f"未知动作类型: {action_type}, 用户: {user_id}")
            action_type = "unknown"
        
        # 初始化上下文
        if context is None:
            context = {}
        
        # 生成动作记录
        action_data = {
            "user_id": user_id,
            "action_type": action_type,
            "action_name": self.action_types.get(action_type, "未知动作"),
            "timestamp": datetime.now().isoformat(),
            "session_id": self._get_or_create_session(user_id),
            "context": context
        }
        
        # 记录动作
        try:
            self.storage.store_user_action(user_id, action_data)
            behavior_logger.debug(f"记录用户 {user_id} 的动作: {action_type}")
        except Exception as e:
            behavior_logger.error(f"保存用户 {user_id} 动作数据失败: {str(e)}")
        
        # 根据动作类型进行特定处理
        self._process_specific_action(user_id, action_type, action_data)
        
        return action_data
    
    def track_content_view(self, user_id: str, content_id: str, 
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """跟踪内容观看事件
        
        记录用户开始观看内容的事件，包含内容元数据。
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            metadata: 内容元数据
            
        Returns:
            Dict[str, Any]: 内容观看记录
        """
        # 初始化元数据
        if metadata is None:
            metadata = {}
        
        # 添加时间戳
        start_time = datetime.now()
        
        # 创建观看记录
        view_data = {
            "user_id": user_id,
            "content_id": content_id,
            "start_time": start_time.isoformat(),
            "session_id": self._get_or_create_session(user_id),
            "metadata": metadata,
            "timeline": [],
            "completion_status": "started",
            "view_id": str(uuid.uuid4())
        }
        
        # 保存观看记录
        try:
            self.storage.store_content_view(user_id, content_id, view_data)
            
            # 将此次观看添加到活跃会话
            session_id = view_data["session_id"]
            if session_id in self.active_sessions and "current_views" in self.active_sessions[session_id]:
                self.active_sessions[session_id]["current_views"].append(view_data["view_id"])
            
            behavior_logger.debug(f"记录用户 {user_id} 观看内容: {content_id}")
        except Exception as e:
            behavior_logger.error(f"保存用户 {user_id} 内容观看数据失败: {str(e)}")
        
        # 同时记录一个view动作
        context = {
            "content_id": content_id,
            "content_type": metadata.get("type", "unknown"),
            "view_id": view_data["view_id"]
        }
        self.track_user_action(user_id, "view", context)
        
        return view_data
    
    def update_content_view(self, user_id: str, view_id: str, 
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新内容观看记录
        
        更新现有的内容观看记录，添加时间线事件或更新状态。
        
        Args:
            user_id: 用户ID
            view_id: 观看ID
            updates: 更新数据
            
        Returns:
            Dict[str, Any]: 更新后的观看记录
        """
        # 验证必要参数
        if not view_id:
            behavior_logger.error(f"缺少view_id参数，无法更新观看记录")
            return {}
        
        try:
            # 获取现有观看记录
            view_data = self.storage.get_content_view(user_id, view_id)
            
            if not view_data:
                behavior_logger.warning(f"未找到用户 {user_id} 的观看记录: {view_id}")
                return {}
            
            # 更新记录
            for key, value in updates.items():
                # 对时间线进行特殊处理 - 添加而不是替换
                if key == "timeline" and isinstance(value, list):
                    if "timeline" not in view_data:
                        view_data["timeline"] = []
                    view_data["timeline"].extend(value)
                else:
                    view_data[key] = value
            
            # 保存更新后的记录
            content_id = view_data.get("content_id")
            self.storage.update_content_view(user_id, view_id, view_data)
            behavior_logger.debug(f"更新用户 {user_id} 的观看记录: {view_id}")
            
            return view_data
        except Exception as e:
            behavior_logger.error(f"更新用户 {user_id} 观看记录失败: {str(e)}")
            return {}
    
    def track_content_completion(self, user_id: str, view_id: str, 
                               completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """跟踪内容观看完成
        
        记录用户完成观看内容的事件，包括完成度和观看时长等指标。
        
        Args:
            user_id: 用户ID
            view_id: 观看ID
            completion_data: 完成数据
            
        Returns:
            Dict[str, Any]: 更新后的观看记录
        """
        # 验证必要参数
        if not view_id:
            behavior_logger.error(f"缺少view_id参数，无法记录完成事件")
            return {}
        
        try:
            # 获取现有观看记录
            view_data = self.storage.get_content_view(user_id, view_id)
            
            if not view_data:
                behavior_logger.warning(f"未找到用户 {user_id} 的观看记录: {view_id}")
                return {}
            
            # 计算观看时长
            end_time = datetime.now()
            start_time = datetime.fromisoformat(view_data.get("start_time", end_time.isoformat()))
            duration_seconds = (end_time - start_time).total_seconds()
            
            # 更新完成数据
            completion_info = {
                "completion_status": "completed",
                "end_time": end_time.isoformat(),
                "duration_seconds": int(duration_seconds),
                "completion_rate": completion_data.get("completion_rate", 1.0),
                "progress_seconds": completion_data.get("progress_seconds", int(duration_seconds))
            }
            
            # 合并用户提供的完成数据
            completion_info.update(completion_data)
            
            # 更新观看记录
            view_data.update(completion_info)
            
            # 保存更新后的记录
            content_id = view_data.get("content_id")
            self.storage.update_content_view(user_id, view_id, view_data)
            behavior_logger.debug(f"记录用户 {user_id} 完成观看内容: {content_id}")
            
            # 同时记录一个complete动作
            context = {
                "content_id": content_id,
                "view_id": view_id,
                "duration_seconds": int(duration_seconds),
                "completion_rate": completion_info["completion_rate"]
            }
            self.track_user_action(user_id, "complete", context)
            
            return view_data
        except Exception as e:
            behavior_logger.error(f"保存用户 {user_id} 内容完成数据失败: {str(e)}")
            return {}
    
    def track_user_feedback(self, user_id: str, feedback_type: str, content_id: str = None,
                         feedback_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """跟踪用户反馈
        
        记录用户对内容或平台的反馈，如点赞、评论、评分等。
        
        Args:
            user_id: 用户ID
            feedback_type: 反馈类型（如like, comment, rate, feedback等）
            content_id: 相关内容ID（可选）
            feedback_data: 反馈数据
            
        Returns:
            Dict[str, Any]: 反馈记录
        """
        # 验证反馈类型
        valid_feedback_types = ["like", "comment", "share", "save", "rate", "feedback", "error_report", "suggestion"]
        if feedback_type not in valid_feedback_types:
            behavior_logger.warning(f"未知反馈类型: {feedback_type}, 用户: {user_id}")
            feedback_type = "feedback"  # 使用通用反馈类型
        
        # 初始化反馈数据
        if feedback_data is None:
            feedback_data = {}
        
        # 创建反馈记录
        feedback_record = {
            "user_id": user_id,
            "feedback_type": feedback_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": self._get_or_create_session(user_id),
            "data": feedback_data
        }
        
        # 如果提供了内容ID，添加到记录中
        if content_id:
            feedback_record["content_id"] = content_id
        
        # 保存反馈记录
        try:
            self.storage.store_user_feedback(user_id, feedback_record)
            behavior_logger.debug(f"记录用户 {user_id} 的 {feedback_type} 反馈")
        except Exception as e:
            behavior_logger.error(f"保存用户 {user_id} 反馈数据失败: {str(e)}")
        
        # 同时记录一个对应的动作
        context = {
            "feedback_type": feedback_type,
            "content_id": content_id
        }
        if feedback_data:
            context.update(feedback_data)
        
        self.track_user_action(user_id, feedback_type, context)
        
        return feedback_record
    
    def _get_or_create_session(self, user_id: str) -> str:
        """获取或创建用户会话
        
        检查用户是否有活跃会话，如果没有则创建新会话。
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 会话ID
        """
        # 检查用户是否有活跃会话
        now = datetime.now()
        active_session = None
        
        if user_id in self.active_sessions:
            session_data = self.active_sessions[user_id]
            last_activity = datetime.fromisoformat(session_data.get("last_activity", ""))
            
            # 检查会话是否超时
            if (now - last_activity).total_seconds() < self.session_timeout * 60:
                active_session = session_data
                # 更新最后活动时间
                active_session["last_activity"] = now.isoformat()
        
        # 如果没有活跃会话，创建新会话
        if not active_session:
            session_id = str(uuid.uuid4())
            active_session = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": now.isoformat(),
                "last_activity": now.isoformat(),
                "current_views": []
            }
            
            # 保存新会话
            self.active_sessions[user_id] = active_session
            
            # 同时保存到存储
            try:
                self.storage.create_user_session(user_id, active_session)
            except Exception as e:
                behavior_logger.error(f"保存用户 {user_id} 会话数据失败: {str(e)}")
        
        return active_session["session_id"]
    
    def _process_specific_action(self, user_id: str, action_type: str, action_data: Dict[str, Any]) -> None:
        """处理特定类型的动作
        
        根据动作类型执行特定的处理逻辑。
        
        Args:
            user_id: 用户ID
            action_type: 动作类型
            action_data: 动作数据
        """
        context = action_data.get("context", {})
        
        # 根据动作类型进行处理
        if action_type == "like":
            content_id = context.get("content_id")
            if content_id:
                self._update_content_interaction_stats(user_id, content_id, "like", 1)
        
        elif action_type == "share":
            content_id = context.get("content_id")
            platform = context.get("platform", "unknown")
            if content_id:
                self._update_content_interaction_stats(user_id, content_id, "share", 1)
                # 记录分享平台数据
                self._update_share_stats(user_id, content_id, platform)
        
        elif action_type == "search":
            query = context.get("query")
            if query:
                self._update_search_history(user_id, query)
        
        elif action_type == "rate":
            content_id = context.get("content_id")
            rating = context.get("rating")
            if content_id and rating is not None:
                self._update_content_interaction_stats(user_id, content_id, "rate", rating)
    
    def _update_content_interaction_stats(self, user_id: str, content_id: str, 
                                       interaction_type: str, value: Any) -> None:
        """更新内容互动统计
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            interaction_type: 互动类型
            value: 互动值
        """
        try:
            self.storage.update_content_interaction(user_id, content_id, interaction_type, value)
        except Exception as e:
            behavior_logger.error(f"更新内容互动统计失败: {str(e)}")
    
    def _update_share_stats(self, user_id: str, content_id: str, platform: str) -> None:
        """更新分享统计
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            platform: 分享平台
        """
        try:
            self.storage.update_share_stats(user_id, content_id, platform)
        except Exception as e:
            behavior_logger.error(f"更新分享统计失败: {str(e)}")
    
    def _update_search_history(self, user_id: str, query: str) -> None:
        """更新搜索历史
        
        Args:
            user_id: 用户ID
            query: 搜索查询
        """
        try:
            self.storage.add_search_query(user_id, query)
        except Exception as e:
            behavior_logger.error(f"更新搜索历史失败: {str(e)}")
    
    def get_user_behavior_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取用户行为摘要
        
        提供用户的行为摘要数据，包括观看历史、互动统计等。
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 用户行为摘要
        """
        # 计算开始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # 获取观看历史
            view_history = self.storage.get_user_view_history(user_id, limit=100)
            
            # 获取动作统计
            actions = self.storage.get_user_actions(user_id, start_date, end_date)
            
            # 统计各类动作
            action_counts = defaultdict(int)
            for action in actions:
                action_type = action.get("action_type")
                if action_type:
                    action_counts[action_type] += 1
            
            # 获取会话统计
            sessions = self.storage.get_user_sessions(user_id, start_date, end_date)
            session_durations = []
            for session in sessions:
                start = datetime.fromisoformat(session.get("start_time", ""))
                end = datetime.fromisoformat(session.get("end_time", start.isoformat()))
                duration_minutes = (end - start).total_seconds() / 60
                session_durations.append(duration_minutes)
            
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
            
            # 计算完成率
            completions = [view for view in view_history if view.get("completion_status") == "completed"]
            completion_rate = len(completions) / len(view_history) if view_history else 0
            
            # 组织行为数据摘要
            behavior_summary = {
                "user_id": user_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "action_counts": dict(action_counts),
                "view_count": len(view_history),
                "completion_count": len(completions),
                "completion_rate": round(completion_rate, 3),
                "avg_session_duration_minutes": round(avg_session_duration, 2),
                "total_sessions": len(sessions),
                "recent_searches": self._get_recent_searches(user_id, 10)
            }
            
            return behavior_summary
        except Exception as e:
            behavior_logger.error(f"获取用户 {user_id} 行为摘要失败: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e)
            }
    
    def _get_recent_searches(self, user_id: str, limit: int = 10) -> List[str]:
        """获取用户最近的搜索查询
        
        Args:
            user_id: 用户ID
            limit: 返回结果数量限制
            
        Returns:
            List[str]: 最近搜索查询列表
        """
        try:
            return self.storage.get_recent_searches(user_id, limit)
        except Exception as e:
            behavior_logger.error(f"获取用户 {user_id} 搜索历史失败: {str(e)}")
            return []


# 模块级函数

_behavior_tracker_instance = None

def get_behavior_tracker() -> BehaviorTracker:
    """获取行为跟踪器单例实例
    
    Returns:
        BehaviorTracker: 行为跟踪器实例
    """
    global _behavior_tracker_instance
    if _behavior_tracker_instance is None:
        _behavior_tracker_instance = BehaviorTracker()
    return _behavior_tracker_instance

def track_user_action(user_id: str, action_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """跟踪用户动作
    
    Args:
        user_id: 用户ID
        action_type: 动作类型
        context: 动作上下文信息
        
    Returns:
        Dict[str, Any]: 记录的动作数据
    """
    tracker = get_behavior_tracker()
    return tracker.track_user_action(user_id, action_type, context)

def track_content_view(user_id: str, content_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """跟踪内容观看事件
    
    Args:
        user_id: 用户ID
        content_id: 内容ID
        metadata: 内容元数据
        
    Returns:
        Dict[str, Any]: 内容观看记录
    """
    tracker = get_behavior_tracker()
    return tracker.track_content_view(user_id, content_id, metadata)

def track_content_completion(user_id: str, view_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
    """跟踪内容观看完成
    
    Args:
        user_id: 用户ID
        view_id: 观看ID
        completion_data: 完成数据
        
    Returns:
        Dict[str, Any]: 更新后的观看记录
    """
    tracker = get_behavior_tracker()
    return tracker.track_content_completion(user_id, view_id, completion_data)

def track_user_feedback(user_id: str, feedback_type: str, content_id: str = None,
                       feedback_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """跟踪用户反馈
    
    Args:
        user_id: 用户ID
        feedback_type: 反馈类型
        content_id: 内容ID
        feedback_data: 反馈数据
        
    Returns:
        Dict[str, Any]: 反馈记录
    """
    tracker = get_behavior_tracker()
    return tracker.track_user_feedback(user_id, feedback_type, content_id, feedback_data) 