#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私安全适配器模块

提供用户数据隐私保护、数据匿名化和用户同意管理功能，
确保VisionAI-ClipsMaster项目符合GDPR等隐私保护法规要求。
"""

import os
import json
import time
import uuid
import random
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set
import numpy as np
from loguru import logger

from src.utils.log_handler import get_logger
from src.data.storage_manager import get_storage_manager
from src.utils.privacy_manager import PrivacyManager as UtilsPrivacyManager
from src.core.privacy_manager import PrivacyManager as CorePrivacyManager

# 自定义异常类
class ConsentRequiredError(Exception):
    """用户未同意隐私协议异常"""
    pass

class FeatureDisabledError(Exception):
    """功能被用户禁用异常"""
    pass

# 配置日志
privacy_logger = get_logger("privacy_adapter")

class PrivacyAdapter:
    """隐私安全适配器
    
    为用户画像、行为跟踪和偏好分析提供隐私保护层，
    通过数据匿名化、差分隐私和同意管理保护用户隐私。
    """
    
    def __init__(self):
        """初始化隐私安全适配器"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 初始化隐私管理器
        self.utils_privacy_manager = UtilsPrivacyManager()
        self.core_privacy_manager = CorePrivacyManager()
        
        # 同意选项配置
        self.consent_options = {
            "preference_tracking": "偏好追踪",
            "behavior_analysis": "行为分析",
            "cross_platform_integration": "跨平台整合",
            "personalized_content": "个性化内容",
            "data_sharing": "数据共享",
            "recommendation": "推荐系统"
        }
        
        # 差分隐私配置
        self.dp_config = {
            "age_noise": 1.0,       # 年龄噪声参数
            "location_noise": 0.05,  # 位置噪声参数
            "preference_noise": 0.1, # 偏好噪声参数
            "threshold": 0.3,        # 随机化阈值
            "min_group_size": 5      # 最小分组大小（k匿名性）
        }
        
        # 隐私数据保留期（天）
        self.retention_periods = {
            "behavior_data": 90,      # 行为数据保留90天
            "preference_data": 180,   # 偏好数据保留180天
            "profile_data": 365,      # 画像数据保留365天
            "sensitive_data": 30      # 敏感数据保留30天
        }
        
        privacy_logger.info("隐私安全适配器初始化完成")
    
    def anonymize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """实施差分隐私保护
        
        对用户数据应用差分隐私技术，添加随机化噪声保护用户隐私。
        
        Args:
            raw_data: 原始用户数据
            
        Returns:
            Dict[str, Any]: 经过匿名化处理的数据
        """
        privacy_logger.debug("对用户数据应用差分隐私保护")
        
        if not raw_data:
            return {}
        
        # 创建结果副本，不修改原始数据
        result = {}
        
        # 处理年龄数据 - 添加拉普拉斯噪声
        if "age" in raw_data:
            try:
                age = float(raw_data["age"])
                # 添加拉普拉斯噪声
                noise = np.random.laplace(0, self.dp_config["age_noise"])
                # 四舍五入到整数
                anonymized_age = round(age + noise)
                # 确保年龄在合理范围内
                anonymized_age = max(18, min(anonymized_age, 100))
                result["age"] = anonymized_age
            except (ValueError, TypeError):
                result["age"] = raw_data["age"]
        
        # 处理性别数据 - 随机化
        if "gender" in raw_data:
            # 有概率替换为"unknown"
            if random.random() < self.dp_config["threshold"]:
                result["gender"] = "unknown"
            else:
                result["gender"] = raw_data["gender"]
        
        # 处理位置数据 - 添加噪声或降低精度
        if "location" in raw_data:
            if isinstance(raw_data["location"], dict) and "latitude" in raw_data["location"] and "longitude" in raw_data["location"]:
                lat = raw_data["location"]["latitude"]
                lng = raw_data["location"]["longitude"]
                
                # 添加位置噪声（约±500米范围）
                lat_noise = np.random.normal(0, self.dp_config["location_noise"])
                lng_noise = np.random.normal(0, self.dp_config["location_noise"])
                
                result["location"] = {
                    "latitude": lat + lat_noise,
                    "longitude": lng + lng_noise,
                    "precision": "city"  # 降低精度标记
                }
            else:
                # 对于字符串形式的位置，保留省市级别
                location_str = str(raw_data["location"])
                # 从位置字符串中提取省市信息
                location_parts = location_str.split()
                if len(location_parts) > 1:
                    # 仅保留省市信息
                    result["location"] = " ".join(location_parts[:2])
                else:
                    result["location"] = location_str
        
        # 处理偏好数据 - 添加噪声
        if "preferences" in raw_data and isinstance(raw_data["preferences"], dict):
            result["preferences"] = {}
            for category, score in raw_data["preferences"].items():
                try:
                    original_score = float(score)
                    # 添加随机噪声
                    noise = np.random.normal(0, self.dp_config["preference_noise"])
                    # 确保分数在0-1范围内
                    anonymized_score = max(0.0, min(1.0, original_score + noise))
                    result["preferences"][category] = round(anonymized_score, 2)
                except (ValueError, TypeError):
                    result["preferences"][category] = score
        
        # 对其他非敏感字段直接复制
        for key, value in raw_data.items():
            if key not in result and key not in ["id", "user_id", "email", "phone", "id_card"]:
                result[key] = value
        
        # 记录数据匿名化操作
        privacy_logger.debug(f"数据匿名化完成，处理了 {len(result)} 个字段")
        
        return result
    
    def enforce_consent(self, user_id: str, feature: str) -> bool:
        """验证用户是否同意特定功能
        
        检查用户是否同意使用特定功能，如偏好追踪、行为分析等。
        
        Args:
            user_id: 用户ID
            feature: 功能名称
            
        Returns:
            bool: 用户是否同意
            
        Raises:
            ConsentRequiredError: 如果用户未同意使用该功能
        """
        privacy_logger.debug(f"验证用户 {user_id} 对功能 {feature} 的同意状态")
        
        # 验证功能是否存在
        if feature not in self.consent_options:
            privacy_logger.warning(f"未知功能: {feature}")
            # 对于未知功能，默认需要同意
            feature = "data_sharing"
        
        # 检查用户同意状态
        has_consent = self.check_consent(user_id, feature)
        
        if not has_consent:
            feature_name = self.consent_options.get(feature, feature)
            error_message = f"缺少用户对{feature_name}的授权"
            privacy_logger.warning(f"用户 {user_id} 未同意: {feature}")
            raise ConsentRequiredError(error_message)
        
        return True
    
    def check_consent(self, user_id: str, feature: str) -> bool:
        """检查用户是否同意特定功能
        
        Args:
            user_id: 用户ID
            feature: 功能名称
            
        Returns:
            bool: 用户是否同意
        """
        try:
            # 从存储中获取用户同意记录
            user_consents = self.storage.get_user_consents(user_id)
            
            if not user_consents:
                privacy_logger.debug(f"用户 {user_id} 没有同意记录")
                return False
            
            # 检查特定功能的同意状态
            if feature in user_consents:
                consent_record = user_consents[feature]
                
                # 检查同意状态
                if consent_record.get("status") == "granted":
                    # 检查同意是否过期
                    if "timestamp" in consent_record:
                        consent_time = datetime.fromisoformat(consent_record["timestamp"])
                        # 默认同意有效期为1年
                        if (datetime.now() - consent_time).days > 365:
                            privacy_logger.debug(f"用户 {user_id} 对 {feature} 的同意已过期")
                            return False
                    
                    privacy_logger.debug(f"用户 {user_id} 已同意 {feature}")
                    return True
            
            privacy_logger.debug(f"用户 {user_id} 未同意 {feature}")
            return False
            
        except Exception as e:
            privacy_logger.error(f"检查用户 {user_id} 同意状态失败: {str(e)}")
            # 出错时默认为未同意，以保护用户隐私
            return False
    
    def record_consent(self, user_id: str, feature: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """记录用户同意状态
        
        Args:
            user_id: 用户ID
            feature: 功能名称
            status: 同意状态 (granted/denied)
            metadata: 额外元数据
            
        Returns:
            bool: 是否成功记录
        """
        try:
            if not metadata:
                metadata = {}
            
            # 创建同意记录
            consent_record = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "feature": feature,
                "feature_name": self.consent_options.get(feature, feature),
                "ip_address": metadata.get("ip_address", ""),
                "user_agent": metadata.get("user_agent", ""),
                "consent_id": str(uuid.uuid4()),
                "version": metadata.get("version", "1.0")
            }
            
            # 存储同意记录
            self.storage.save_user_consent(user_id, feature, consent_record)
            
            privacy_logger.info(f"记录用户 {user_id} 对 {feature} 的同意状态: {status}")
            return True
            
        except Exception as e:
            privacy_logger.error(f"记录用户 {user_id} 同意状态失败: {str(e)}")
            return False
    
    def get_all_consents(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """获取用户所有的同意记录
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Dict[str, Any]]: 用户所有同意记录
        """
        try:
            # 从存储中获取用户同意记录
            user_consents = self.storage.get_user_consents(user_id)
            
            if not user_consents:
                return {}
            
            # 格式化同意记录
            formatted_consents = {}
            for feature, consent_data in user_consents.items():
                if feature in self.consent_options:
                    formatted_consents[feature] = {
                        "status": consent_data.get("status", "unknown"),
                        "timestamp": consent_data.get("timestamp", ""),
                        "feature_name": self.consent_options[feature],
                        "is_valid": self.check_consent(user_id, feature)
                    }
            
            return formatted_consents
            
        except Exception as e:
            privacy_logger.error(f"获取用户 {user_id} 同意记录失败: {str(e)}")
            return {}
    
    def apply_data_retention(self, user_id: str) -> Dict[str, Any]:
        """应用数据保留策略
        
        根据数据保留期限，清理过期的用户数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 清理结果统计
        """
        try:
            result = {
                "behavior_data_removed": 0,
                "preference_data_removed": 0,
                "profile_data_removed": 0,
                "sensitive_data_removed": 0
            }
            
            # 当前时间
            now = datetime.now()
            
            # 清理行为数据
            behavior_cutoff = now - timedelta(days=self.retention_periods["behavior_data"])
            removed = self.storage.clean_user_data(user_id, "behavior", behavior_cutoff)
            result["behavior_data_removed"] = removed
            
            # 清理偏好数据
            preference_cutoff = now - timedelta(days=self.retention_periods["preference_data"])
            removed = self.storage.clean_user_data(user_id, "preference", preference_cutoff)
            result["preference_data_removed"] = removed
            
            # 清理画像数据
            profile_cutoff = now - timedelta(days=self.retention_periods["profile_data"])
            removed = self.storage.clean_user_data(user_id, "profile", profile_cutoff)
            result["profile_data_removed"] = removed
            
            # 清理敏感数据
            sensitive_cutoff = now - timedelta(days=self.retention_periods["sensitive_data"])
            removed = self.storage.clean_user_data(user_id, "sensitive", sensitive_cutoff)
            result["sensitive_data_removed"] = removed
            
            privacy_logger.info(f"应用数据保留策略，用户 {user_id}，结果: {result}")
            return result
            
        except Exception as e:
            privacy_logger.error(f"应用数据保留策略失败，用户 {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def detect_sensitive_data(self, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """检测内容中的敏感信息
        
        使用正则表达式和模式匹配识别内容中的敏感信息
        
        Args:
            content: 要检测的内容
            
        Returns:
            Dict[str, List[str]]: 检测到的敏感信息
        """
        if not content:
            return {}
            
        # 将字典转换为字符串进行检测
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = str(content)
            
        # 使用隐私管理器检测PII
        return self.core_privacy_manager.detect_pii(content_str)
    
    def redact_sensitive_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """编辑内容中的敏感信息
        
        将内容中的敏感信息替换为占位符
        
        Args:
            content: 要编辑的内容
            
        Returns:
            Dict[str, Any]: 编辑后的内容
        """
        if not content:
            return {}
            
        # 将内容转换为字符串
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = str(content)
            
        # 使用隐私管理器编辑PII
        redacted_str = self.utils_privacy_manager.redact_pii(content_str)
        
        # 尝试将结果转换回字典
        try:
            if isinstance(content, dict):
                return json.loads(redacted_str)
            else:
                return redacted_str
        except json.JSONDecodeError:
            # 如果无法解析JSON，返回字符串
            return {"redacted_content": redacted_str}


# 全局单例
_privacy_adapter = None

def get_privacy_adapter() -> PrivacyAdapter:
    """获取隐私安全适配器实例
    
    Returns:
        PrivacyAdapter: 隐私安全适配器实例
    """
    global _privacy_adapter
    if _privacy_adapter is None:
        _privacy_adapter = PrivacyAdapter()
    return _privacy_adapter

def anonymize_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """匿名化数据的便捷函数
    
    Args:
        raw_data: 原始数据
        
    Returns:
        Dict[str, Any]: 匿名化后的数据
    """
    adapter = get_privacy_adapter()
    return adapter.anonymize_data(raw_data)

def enforce_consent(user_id: str, feature: str) -> bool:
    """验证用户同意的便捷函数
    
    Args:
        user_id: 用户ID
        feature: 功能名称
        
    Returns:
        bool: 用户是否同意
        
    Raises:
        ConsentRequiredError: 如果用户未同意
    """
    adapter = get_privacy_adapter()
    return adapter.enforce_consent(user_id, feature)

def check_consent(user_id: str, feature: str) -> bool:
    """检查用户同意状态的便捷函数
    
    Args:
        user_id: 用户ID
        feature: 功能名称
        
    Returns:
        bool: 用户是否同意
    """
    adapter = get_privacy_adapter()
    return adapter.check_consent(user_id, feature)

def record_consent(user_id: str, feature: str, status: str, metadata: Dict[str, Any] = None) -> bool:
    """记录用户同意状态的便捷函数
    
    Args:
        user_id: 用户ID
        feature: 功能名称
        status: 同意状态
        metadata: 额外元数据
        
    Returns:
        bool: 是否成功记录
    """
    adapter = get_privacy_adapter()
    return adapter.record_consent(user_id, feature, status, metadata) 