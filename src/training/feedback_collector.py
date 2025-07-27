#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反馈收集器
收集和处理用户反馈数据
"""

import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self):
        """初始化反馈收集器"""
        self.feedback_storage = []
        logger.info("反馈收集器初始化完成")
    
    def collect_feedback(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        收集反馈数据
        
        Args:
            feedback_data: 反馈数据列表
            
        Returns:
            收集结果
        """
        try:
            logger.info(f"开始收集 {len(feedback_data)} 条反馈")
            
            start_time = time.time()
            
            # 处理每条反馈
            processed_feedback = []
            for feedback in feedback_data:
                processed_item = {
                    "content_id": feedback.get("content_id", ""),
                    "user_rating": feedback.get("user_rating", 0.0),
                    "engagement_metrics": feedback.get("engagement_metrics", {}),
                    "feedback_type": feedback.get("feedback_type", "neutral"),
                    "timestamp": time.time(),
                    "processed": True
                }
                processed_feedback.append(processed_item)
            
            # 存储反馈
            self.feedback_storage.extend(processed_feedback)
            
            collection_time = time.time() - start_time
            
            result = {
                "status": "success",
                "collected_count": len(processed_feedback),
                "total_stored": len(self.feedback_storage),
                "collection_time": collection_time
            }
            
            logger.info(f"反馈收集完成，收集了 {len(processed_feedback)} 条反馈")
            return result
            
        except Exception as e:
            logger.error(f"反馈收集失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "collected_count": 0,
                "collection_time": 0.0
            }
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """获取反馈摘要"""
        try:
            if not self.feedback_storage:
                return {"total_feedback": 0, "average_rating": 0.0}
            
            total_rating = sum(item.get("user_rating", 0.0) for item in self.feedback_storage)
            average_rating = total_rating / len(self.feedback_storage)
            
            return {
                "total_feedback": len(self.feedback_storage),
                "average_rating": average_rating,
                "feedback_types": self._count_feedback_types()
            }
            
        except Exception as e:
            logger.error(f"获取反馈摘要失败: {e}")
            return {"total_feedback": 0, "average_rating": 0.0, "error": str(e)}
    
    def _count_feedback_types(self) -> Dict[str, int]:
        """统计反馈类型"""
        type_counts = {}
        for item in self.feedback_storage:
            feedback_type = item.get("feedback_type", "neutral")
            type_counts[feedback_type] = type_counts.get(feedback_type, 0) + 1
        return type_counts
