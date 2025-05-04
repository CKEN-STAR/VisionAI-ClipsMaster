#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私安全适配器独立测试

这是一个完全独立的测试脚本，不依赖于项目的其他模块，可以直接运行。
此脚本包含了必要的模拟类和测试用例，验证隐私适配器的核心功能。
"""

import unittest
from unittest.mock import MagicMock
import json
import random
import hashlib
from datetime import datetime, timedelta
import traceback

print("开始隐私安全适配器独立测试...")

class MockStorageManager:
    """模拟存储管理器"""
    
    def __init__(self):
        """初始化模拟存储管理器"""
        self.user_consents = {}
    
    def get_user_consents(self, user_id):
        """获取用户同意记录"""
        if user_id not in self.user_consents:
            return {}
        return self.user_consents[user_id]
    
    def save_user_consent(self, user_id, feature, consent_record):
        """保存用户同意记录"""
        if user_id not in self.user_consents:
            self.user_consents[user_id] = {}
        self.user_consents[user_id][feature] = consent_record
        return True
    
    def clean_user_data(self, user_id, data_type, cutoff_date):
        """清理用户数据"""
        # 模拟清理数据，返回固定数值
        if data_type == "behavior":
            return 5
        elif data_type == "preference":
            return 3
        elif data_type == "profile":
            return 2
        elif data_type == "sensitive":
            return 1
        else:
            return 0

class MockPrivacyManager:
    """模拟隐私管理器"""
    
    def detect_pii(self, content):
        """检测个人隐私信息"""
        result = {}
        if "test@example.com" in content:
            result["email"] = ["test@example.com"]
        if "13812345678" in content:
            result["phone"] = ["13812345678"]
        return result
    
    def redact_pii(self, text):
        """编辑隐私信息"""
        text = text.replace("test@example.com", "[电子邮件]")
        text = text.replace("13812345678", "[手机号]")
        return text

# 自定义异常类
class ConsentRequiredError(Exception):
    """用户未同意隐私协议异常"""
    pass

class FeatureDisabledError(Exception):
    """功能被用户禁用异常"""
    pass

class PrivacyAdapter:
    """隐私安全适配器
    
    为用户画像、行为跟踪和偏好分析提供隐私保护层，
    通过数据匿名化、差分隐私和同意管理保护用户隐私。
    """
    
    def __init__(self):
        """初始化隐私安全适配器"""
        # 获取存储管理器
        self.storage = MockStorageManager()
        
        # 初始化隐私管理器
        self.utils_privacy_manager = MockPrivacyManager()
        self.core_privacy_manager = MockPrivacyManager()
        
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
        
        print("隐私安全适配器初始化完成")
    
    def anonymize_data(self, raw_data):
        """实施差分隐私保护
        
        对用户数据应用差分隐私技术，添加随机化噪声保护用户隐私。
        
        Args:
            raw_data: 原始用户数据
            
        Returns:
            Dict[str, Any]: 经过匿名化处理的数据
        """
        if not raw_data:
            return {}
        
        # 创建结果副本，不修改原始数据
        result = {}
        
        # 处理年龄数据 - 添加随机噪声
        if "age" in raw_data:
            try:
                age = float(raw_data["age"])
                # 添加随机噪声
                noise = random.uniform(-self.dp_config["age_noise"], self.dp_config["age_noise"])
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
                
                # 添加位置噪声
                lat_noise = random.uniform(-self.dp_config["location_noise"], self.dp_config["location_noise"])
                lng_noise = random.uniform(-self.dp_config["location_noise"], self.dp_config["location_noise"])
                
                result["location"] = {
                    "latitude": lat + lat_noise,
                    "longitude": lng + lng_noise,
                    "precision": "city"  # 降低精度标记
                }
            else:
                # 对于字符串形式的位置，直接复制
                result["location"] = raw_data["location"]
        
        # 处理偏好数据 - 添加噪声
        if "preferences" in raw_data and isinstance(raw_data["preferences"], dict):
            result["preferences"] = {}
            for category, score in raw_data["preferences"].items():
                try:
                    original_score = float(score)
                    # 添加随机噪声
                    noise = random.uniform(-self.dp_config["preference_noise"], self.dp_config["preference_noise"])
                    # 确保分数在0-1范围内
                    anonymized_score = max(0.0, min(1.0, original_score + noise))
                    result["preferences"][category] = round(anonymized_score, 2)
                except (ValueError, TypeError):
                    result["preferences"][category] = score
        
        # 对其他非敏感字段直接复制
        for key, value in raw_data.items():
            if key not in result and key not in ["id", "user_id", "email", "phone", "id_card"]:
                result[key] = value
        
        return result
    
    def enforce_consent(self, user_id, feature):
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
        # 验证功能是否存在
        if feature not in self.consent_options:
            # 对于未知功能，默认需要同意
            feature = "data_sharing"
        
        # 检查用户同意状态
        has_consent = self.check_consent(user_id, feature)
        
        if not has_consent:
            feature_name = self.consent_options.get(feature, feature)
            error_message = f"缺少用户对{feature_name}的授权"
            raise ConsentRequiredError(error_message)
        
        return True
    
    def check_consent(self, user_id, feature):
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
                            return False
                    
                    return True
            
            return False
            
        except Exception as e:
            # 出错时默认为未同意，以保护用户隐私
            return False
    
    def record_consent(self, user_id, feature, status, metadata=None):
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
                "consent_id": str(random.randint(10000, 99999)),
                "version": metadata.get("version", "1.0")
            }
            
            # 存储同意记录
            self.storage.save_user_consent(user_id, feature, consent_record)
            
            return True
            
        except Exception as e:
            return False
    
    def get_all_consents(self, user_id):
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
            return {}
    
    def apply_data_retention(self, user_id):
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
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def detect_sensitive_data(self, content):
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
    
    def redact_sensitive_data(self, content):
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

class TestPrivacyAdapter(unittest.TestCase):
    """隐私安全适配器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建被测对象
        self.privacy_adapter = PrivacyAdapter()
        
        # 测试用户ID
        self.test_user_id = "test_user_123"
        
        # 测试原始数据
        self.test_raw_data = {
            "user_id": self.test_user_id,
            "age": 30,
            "gender": "male",
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "preferences": {
                "art": 0.8,
                "music": 0.6,
                "sports": 0.4
            },
            "email": "test@example.com",
            "phone": "13812345678"
        }
    
    def test_anonymize_data(self):
        """测试数据匿名化功能"""
        # 调用被测方法
        anonymized_data = self.privacy_adapter.anonymize_data(self.test_raw_data)
        
        # 验证结果结构
        self.assertIn("age", anonymized_data)
        self.assertIn("gender", anonymized_data)
        self.assertIn("location", anonymized_data)
        self.assertIn("preferences", anonymized_data)
        
        # 验证敏感字段是否被移除
        self.assertNotIn("email", anonymized_data)
        self.assertNotIn("phone", anonymized_data)
        
        # 验证年龄是否在合理范围内
        self.assertGreaterEqual(anonymized_data["age"], 18)
        self.assertLessEqual(anonymized_data["age"], 100)
        
        # 验证位置信息是否被模糊化
        if isinstance(anonymized_data["location"], dict):
            self.assertIn("precision", anonymized_data["location"])
            self.assertEqual(anonymized_data["location"]["precision"], "city")
        
        # 验证偏好数据是否保持在0-1范围内
        for category, score in anonymized_data["preferences"].items():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        print("✓ 数据匿名化测试通过")
    
    def test_consent_management(self):
        """测试同意管理功能"""
        # 测试记录用户同意
        result = self.privacy_adapter.record_consent(
            self.test_user_id,
            "preference_tracking",
            "granted",
            {"ip_address": "192.168.1.1"}
        )
        self.assertTrue(result)
        
        # 测试检查用户同意
        has_consent = self.privacy_adapter.check_consent(self.test_user_id, "preference_tracking")
        self.assertTrue(has_consent)
        
        # 测试强制检查用户同意
        self.assertTrue(self.privacy_adapter.enforce_consent(self.test_user_id, "preference_tracking"))
        
        # 测试拒绝同意
        self.privacy_adapter.record_consent(self.test_user_id, "data_sharing", "denied")
        
        # 测试拒绝同意的强制检查
        with self.assertRaises(ConsentRequiredError):
            self.privacy_adapter.enforce_consent(self.test_user_id, "data_sharing")
        
        # 测试未记录的功能
        with self.assertRaises(ConsentRequiredError):
            self.privacy_adapter.enforce_consent(self.test_user_id, "cross_platform_integration")
        
        print("✓ 同意管理测试通过")
    
    def test_get_all_consents(self):
        """测试获取所有同意记录"""
        # 记录两个同意状态
        self.privacy_adapter.record_consent(self.test_user_id, "preference_tracking", "granted")
        self.privacy_adapter.record_consent(self.test_user_id, "behavior_analysis", "denied")
        
        # 获取所有同意记录
        all_consents = self.privacy_adapter.get_all_consents(self.test_user_id)
        
        # 验证结果
        self.assertIn("preference_tracking", all_consents)
        self.assertIn("behavior_analysis", all_consents)
        self.assertEqual(all_consents["preference_tracking"]["status"], "granted")
        self.assertEqual(all_consents["behavior_analysis"]["status"], "denied")
        
        print("✓ 获取所有同意记录测试通过")
    
    def test_sensitive_data_protection(self):
        """测试敏感数据保护功能"""
        # 测试敏感数据检测
        sensitive_data = self.privacy_adapter.detect_sensitive_data(self.test_raw_data)
        self.assertIsInstance(sensitive_data, dict)
        if "email" in sensitive_data:
            self.assertIn("test@example.com", sensitive_data["email"])
        
        # 测试敏感数据编辑
        redacted_data = self.privacy_adapter.redact_sensitive_data(self.test_raw_data)
        self.assertIsInstance(redacted_data, dict)
        
        print("✓ 敏感数据保护测试通过")
    
    def test_data_retention(self):
        """测试数据保留策略"""
        # 测试应用数据保留策略
        result = self.privacy_adapter.apply_data_retention(self.test_user_id)
        
        # 验证结果
        self.assertEqual(result["behavior_data_removed"], 5)
        self.assertEqual(result["preference_data_removed"], 3)
        self.assertEqual(result["profile_data_removed"], 2)
        self.assertEqual(result["sensitive_data_removed"], 1)
        
        print("✓ 数据保留策略测试通过")

if __name__ == "__main__":
    try:
        unittest.main()
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc() 