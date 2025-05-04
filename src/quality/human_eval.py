#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
人工评估接口模块

为视频剪辑作品提供人工评估功能，收集和分析人类评价数据，
用于评估AI生成内容的质量，同时可作为自动评估系统的基准。
"""

import os
import json
import uuid
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

from src.utils.file_handler import ensure_dir_exists, load_json, save_json


class CrowdRatingSystem:
    """众包评分系统，管理用户提交的评分"""
    
    def __init__(self, storage_dir: str = "data/human_ratings"):
        """初始化众包评分系统"""
        self.storage_dir = storage_dir
        ensure_dir_exists(storage_dir)
        
        # 评分标准和权重
        self.criteria = {
            "clarity": {"name": "清晰度", "description": "视频内容的清晰度和可理解性", "weight": 1.0},
            "engagement": {"name": "吸引力", "description": "视频吸引和保持观众注意力的能力", "weight": 1.2},
            "artistry": {"name": "艺术性", "description": "视频的艺术表现和创意水平", "weight": 1.0}
        }
        
        # 评分数据
        self.ratings = {}
    
    def collect_ratings(self, video_id: str, criteria: Optional[List[str]] = None) -> Dict:
        """收集人工评估数据（模拟）"""
        # 模拟人工评分
        ratings = {
            "clarity": random.uniform(3.5, 5),
            "engagement": random.uniform(3.7, 4.9),
            "artistry": random.uniform(3.0, 5)
        }
        
        # 只返回请求的标准
        if criteria:
            return {k: v for k, v in ratings.items() if k in criteria}
        return ratings
    
    def submit_rating(self, video_id: str, rating_data: Dict[str, Any], user_id: str = None) -> str:
        """提交评分"""
        if not user_id:
            user_id = f"user_{int(time.time())}"
            
        # 生成评分ID
        rating_id = str(uuid.uuid4())
        
        # 创建评分记录
        rating_record = {
            "id": rating_id,
            "video_id": video_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "ratings": rating_data
        }
        
        # 保存评分
        if video_id not in self.ratings:
            self.ratings[video_id] = []
        
        self.ratings[video_id].append(rating_record)
        
        return rating_id
    
    def get_ratings(self, video_id: str) -> List[Dict[str, Any]]:
        """获取视频的评分列表"""
        return self.ratings.get(video_id, [])
    
    def calculate_average_ratings(self, video_id: str) -> Dict[str, float]:
        """计算视频的平均评分"""
        ratings = self.get_ratings(video_id)
        
        if not ratings:
            return {}
        
        # 收集所有评分维度
        all_criteria = set()
        for rating in ratings:
            all_criteria.update(rating.get("ratings", {}).keys())
        
        # 计算每个维度的平均分
        avg_ratings = {}
        for criterion in all_criteria:
            values = [r["ratings"].get(criterion) for r in ratings if criterion in r.get("ratings", {})]
            if values:
                avg_ratings[criterion] = sum(values) / len(values)
        
        # 计算总体平均分
        if avg_ratings:
            avg_ratings["overall"] = sum(avg_ratings.values()) / len(avg_ratings)
        
        return avg_ratings
    
    def get_rating_summary(self, video_id: str) -> Dict[str, Any]:
        """获取评分摘要"""
        ratings = self.get_ratings(video_id)
        avg_ratings = self.calculate_average_ratings(video_id)
        
        if not ratings:
            return {"video_id": video_id, "ratings_count": 0, "average_ratings": {}}
        
        return {
            "video_id": video_id,
            "ratings_count": len(ratings),
            "average_ratings": avg_ratings
        }


class EvaluationCampaign:
    """评估活动，管理一组视频的评估任务"""
    
    def __init__(self, campaign_id: str = None, name: str = ""):
        """初始化评估活动"""
        self.campaign_id = campaign_id or f"campaign_{int(time.time())}"
        self.name = name or f"评估活动 {self.campaign_id}"
        self.created_at = datetime.now().isoformat()
        self.status = "created"  # created, active, paused, completed
        self.video_ids = []
        self.metadata = {}
        self.participants = {}  # user_id -> 状态
        
        # 保存目录
        self.storage_dir = os.path.join("data/evaluation_campaigns", self.campaign_id)
        ensure_dir_exists(self.storage_dir)
        
        self.rating_system = CrowdRatingSystem()
    
    def add_video(self, video_id: str, metadata: Dict = None) -> None:
        """添加视频到评估活动"""
        if video_id not in self.video_ids:
            self.video_ids.append(video_id)
            
            if metadata:
                if "videos" not in self.metadata:
                    self.metadata["videos"] = {}
                self.metadata["videos"][video_id] = metadata
    
    def add_participant(self, user_id: str, role: str = "evaluator") -> None:
        """添加参与者"""
        self.participants[user_id] = {
            "role": role,
            "added_at": datetime.now().isoformat(),
            "status": "active",
            "completed_videos": []
        }
    
    def start_campaign(self) -> bool:
        """启动评估活动"""
        if not self.video_ids:
            return False
        
        self.status = "active"
        self.metadata["started_at"] = datetime.now().isoformat()
        self.save()
        return True
    
    def complete_campaign(self) -> bool:
        """完成评估活动"""
        self.status = "completed"
        self.metadata["completed_at"] = datetime.now().isoformat()
        self.save()
        return True
    
    def save(self) -> bool:
        """保存评估活动"""
        data = {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "created_at": self.created_at,
            "status": self.status,
            "video_ids": self.video_ids,
            "metadata": self.metadata,
            "participants": self.participants
        }
        
        try:
            save_json(data, os.path.join(self.storage_dir, "campaign.json"))
            return True
        except Exception as e:
            logger.error(f"保存评估活动失败: {e}")
            return False
    
    @classmethod
    def load(cls, campaign_id: str) -> 'EvaluationCampaign':
        """加载评估活动"""
        storage_dir = os.path.join("data/evaluation_campaigns", campaign_id)
        
        if not os.path.exists(storage_dir):
            return None
        
        try:
            data = load_json(os.path.join(storage_dir, "campaign.json"))
            
            campaign = cls(campaign_id=data["campaign_id"], name=data["name"])
            campaign.created_at = data["created_at"]
            campaign.status = data["status"]
            campaign.video_ids = data["video_ids"]
            campaign.metadata = data["metadata"]
            campaign.participants = data["participants"]
            
            return campaign
        except Exception as e:
            logger.error(f"加载评估活动失败: {e}")
            return None
    
    def get_summary(self) -> Dict[str, Any]:
        """获取评估活动摘要"""
        # 收集所有视频的评分摘要
        video_summaries = {}
        for video_id in self.video_ids:
            video_summaries[video_id] = self.rating_system.get_rating_summary(video_id)
        
        # 计算活动级别的统计信息
        total_ratings = sum(summary["ratings_count"] for summary in video_summaries.values())
        
        # 创建摘要
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "status": self.status,
            "video_count": len(self.video_ids),
            "total_ratings": total_ratings,
            "video_summaries": video_summaries
        }


class HumanEvaluator:
    """人工评估器，提供人工评估界面和数据管理"""
    
    def __init__(self):
        """初始化人工评估器"""
        self.rating_system = CrowdRatingSystem()
        self.campaigns = {}  # campaign_id -> EvaluationCampaign
        
        # 加载所有评估活动
        self._load_campaigns()
    
    def _load_campaigns(self) -> None:
        """加载所有评估活动"""
        campaigns_dir = "data/evaluation_campaigns"
        ensure_dir_exists(campaigns_dir)
        
        # 查找所有活动目录
        for item in os.listdir(campaigns_dir):
            campaign_dir = os.path.join(campaigns_dir, item)
            if os.path.isdir(campaign_dir) and os.path.exists(os.path.join(campaign_dir, "campaign.json")):
                campaign = EvaluationCampaign.load(item)
                if campaign:
                    self.campaigns[item] = campaign
    
    def create_campaign(self, name: str, metadata: Dict = None) -> EvaluationCampaign:
        """创建评估活动"""
        campaign = EvaluationCampaign(name=name)
        
        if metadata:
            campaign.metadata.update(metadata)
        
        self.campaigns[campaign.campaign_id] = campaign
        campaign.save()
        
        return campaign
    
    def submit_rating(self, video_id: str, user_id: str, ratings: Dict[str, float], 
                     campaign_id: str = None, comments: str = "") -> str:
        """提交评分"""
        # 提交到评分系统
        rating_id = self.rating_system.submit_rating(video_id, ratings, user_id)
        
        # 如果指定了活动，更新活动参与者状态
        if campaign_id and campaign_id in self.campaigns:
            campaign = self.campaigns[campaign_id]
            
            if user_id in campaign.participants:
                if video_id not in campaign.participants[user_id].get("completed_videos", []):
                    campaign.participants[user_id].setdefault("completed_videos", []).append(video_id)
                    campaign.save()
        
        return rating_id
    
    def get_evaluation_report(self, video_ids: List[str] = None, 
                             campaign_id: str = None) -> Dict[str, Any]:
        """获取评估报告"""
        # 如果指定了活动
        if campaign_id:
            if campaign_id not in self.campaigns:
                return {"error": f"评估活动 {campaign_id} 不存在"}
            
            campaign = self.campaigns[campaign_id]
            return campaign.get_summary()
        
        # 否则，创建一个所有指定视频的报告
        if not video_ids:
            return {"error": "未指定视频ID或评估活动"}
        
        # 收集所有视频的评分摘要
        video_summaries = {}
        for video_id in video_ids:
            video_summaries[video_id] = self.rating_system.get_rating_summary(video_id)
        
        # 创建报告
        return {
            "report_type": "custom",
            "video_count": len(video_ids),
            "video_summaries": video_summaries
        }


# 导出类
__all__ = ['CrowdRatingSystem', 'EvaluationCampaign', 'HumanEvaluator']
