#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私安全适配器测试模块

测试隐私保护、匿名化和同意管理功能。
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import numpy as np
from datetime import datetime, timedelta

# 修改Python路径以导入项目模块
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.audience.privacy_guard import (
    PrivacyAdapter, get_privacy_adapter, anonymize_data, 
    enforce_consent, check_consent, record_consent,
    ConsentRequiredError
)

class TestPrivacyAdapter(unittest.TestCase):
    """隐私安全适配器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 模拟存储管理器
        self.mock_storage = MagicMock()
        
        # 模拟隐私管理器
        self.mock_utils_privacy_manager = MagicMock()
        self.mock_core_privacy_manager = MagicMock()
        
        # 创建被测对象
        with patch('src.audience.privacy_guard.get_storage_manager', return_value=self.mock_storage), \
             patch('src.audience.privacy_guard.UtilsPrivacyManager', return_value=self.mock_utils_privacy_manager), \
             patch('src.audience.privacy_guard.CorePrivacyManager', return_value=self.mock_core_privacy_manager):
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
    
    def test_check_consent_no_record(self):
        """测试用户没有同意记录时的检查"""
        # 设置模拟返回值
        self.mock_storage.get_user_consents.return_value = None
        
        # 调用被测方法
        result = self.privacy_adapter.check_consent(self.test_user_id, "preference_tracking")
        
        # 验证结果
        self.assertFalse(result)
        self.mock_storage.get_user_consents.assert_called_once_with(self.test_user_id)
    
    def test_check_consent_granted(self):
        """测试用户已同意时的检查"""
        # 设置模拟返回值
        mock_consents = {
            "preference_tracking": {
                "status": "granted",
                "timestamp": datetime.now().isoformat(),
                "feature": "preference_tracking"
            }
        }
        self.mock_storage.get_user_consents.return_value = mock_consents
        
        # 调用被测方法
        result = self.privacy_adapter.check_consent(self.test_user_id, "preference_tracking")
        
        # 验证结果
        self.assertTrue(result)
    
    def test_check_consent_expired(self):
        """测试用户同意已过期时的检查"""
        # 设置模拟返回值 - 设置为370天前（超过365天有效期）
        expired_time = datetime.now() - timedelta(days=370)
        mock_consents = {
            "preference_tracking": {
                "status": "granted",
                "timestamp": expired_time.isoformat(),
                "feature": "preference_tracking"
            }
        }
        self.mock_storage.get_user_consents.return_value = mock_consents
        
        # 调用被测方法
        result = self.privacy_adapter.check_consent(self.test_user_id, "preference_tracking")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_check_consent_denied(self):
        """测试用户拒绝同意时的检查"""
        # 设置模拟返回值
        mock_consents = {
            "preference_tracking": {
                "status": "denied",
                "timestamp": datetime.now().isoformat(),
                "feature": "preference_tracking"
            }
        }
        self.mock_storage.get_user_consents.return_value = mock_consents
        
        # 调用被测方法
        result = self.privacy_adapter.check_consent(self.test_user_id, "preference_tracking")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_enforce_consent_granted(self):
        """测试用户已同意时的强制检查"""
        # 设置模拟返回值
        mock_consents = {
            "preference_tracking": {
                "status": "granted",
                "timestamp": datetime.now().isoformat(),
                "feature": "preference_tracking"
            }
        }
        self.mock_storage.get_user_consents.return_value = mock_consents
        
        # 调用被测方法
        result = self.privacy_adapter.enforce_consent(self.test_user_id, "preference_tracking")
        
        # 验证结果
        self.assertTrue(result)
    
    def test_enforce_consent_denied(self):
        """测试用户拒绝同意时的强制检查"""
        # 设置模拟返回值
        mock_consents = {
            "preference_tracking": {
                "status": "denied",
                "timestamp": datetime.now().isoformat(),
                "feature": "preference_tracking"
            }
        }
        self.mock_storage.get_user_consents.return_value = mock_consents
        
        # 调用被测方法并验证异常
        with self.assertRaises(ConsentRequiredError):
            self.privacy_adapter.enforce_consent(self.test_user_id, "preference_tracking")
    
    def test_record_consent(self):
        """测试记录用户同意状态"""
        # 调用被测方法
        result = self.privacy_adapter.record_consent(
            self.test_user_id, 
            "preference_tracking", 
            "granted",
            {"ip_address": "192.168.1.1", "user_agent": "Test Browser"}
        )
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证存储方法被调用
        self.mock_storage.save_user_consent.assert_called_once()
        
        # 获取保存的数据
        call_args = self.mock_storage.save_user_consent.call_args
        saved_user_id, saved_feature, saved_record = call_args[0]
        
        # 验证数据内容
        self.assertEqual(saved_user_id, self.test_user_id)
        self.assertEqual(saved_feature, "preference_tracking")
        self.assertEqual(saved_record["status"], "granted")
        self.assertEqual(saved_record["feature"], "preference_tracking")
        self.assertEqual(saved_record["feature_name"], "偏好追踪")
        self.assertEqual(saved_record["ip_address"], "192.168.1.1")
        self.assertEqual(saved_record["user_agent"], "Test Browser")
    
    def test_get_all_consents(self):
        """测试获取所有同意记录"""
        # 设置模拟返回值
        now = datetime.now()
        mock_consents = {
            "preference_tracking": {
                "status": "granted",
                "timestamp": now.isoformat(),
                "feature": "preference_tracking"
            },
            "behavior_analysis": {
                "status": "denied",
                "timestamp": now.isoformat(),
                "feature": "behavior_analysis"
            },
            "unknown_feature": {
                "status": "granted",
                "timestamp": now.isoformat(),
                "feature": "unknown_feature"
            }
        }
        self.mock_storage.get_user_consents.return_value = mock_consents
        
        # 调用被测方法
        result = self.privacy_adapter.get_all_consents(self.test_user_id)
        
        # 验证结果
        self.assertIn("preference_tracking", result)
        self.assertIn("behavior_analysis", result)
        self.assertNotIn("unknown_feature", result)  # 不应包含未知功能
        
        # 验证格式化后的内容
        self.assertEqual(result["preference_tracking"]["status"], "granted")
        self.assertEqual(result["preference_tracking"]["feature_name"], "偏好追踪")
        self.assertTrue(result["preference_tracking"]["is_valid"])
        
        self.assertEqual(result["behavior_analysis"]["status"], "denied")
        self.assertEqual(result["behavior_analysis"]["feature_name"], "行为分析")
        self.assertFalse(result["behavior_analysis"]["is_valid"])
    
    def test_apply_data_retention(self):
        """测试应用数据保留策略"""
        # 设置模拟返回值
        self.mock_storage.clean_user_data.side_effect = [5, 3, 2, 1]
        
        # 调用被测方法
        result = self.privacy_adapter.apply_data_retention(self.test_user_id)
        
        # 验证结果
        self.assertEqual(result["behavior_data_removed"], 5)
        self.assertEqual(result["preference_data_removed"], 3)
        self.assertEqual(result["profile_data_removed"], 2)
        self.assertEqual(result["sensitive_data_removed"], 1)
        
        # 验证调用次数
        self.assertEqual(self.mock_storage.clean_user_data.call_count, 4)
    
    def test_detect_sensitive_data(self):
        """测试敏感数据检测"""
        # 设置模拟返回值
        mock_detection_result = {
            "email": ["test@example.com"],
            "phone": ["13812345678"]
        }
        self.mock_core_privacy_manager.detect_pii.return_value = mock_detection_result
        
        # 调用被测方法
        result = self.privacy_adapter.detect_sensitive_data(self.test_raw_data)
        
        # 验证结果
        self.assertEqual(result, mock_detection_result)
        self.mock_core_privacy_manager.detect_pii.assert_called_once()
    
    def test_redact_sensitive_data(self):
        """测试敏感数据编辑"""
        # 设置模拟返回值
        redacted_json = json.dumps({
            "user_id": self.test_user_id,
            "age": 30,
            "gender": "male",
            "email": "[电子邮件]",
            "phone": "[手机号]"
        })
        self.mock_utils_privacy_manager.redact_pii.return_value = redacted_json
        
        # 调用被测方法
        result = self.privacy_adapter.redact_sensitive_data(self.test_raw_data)
        
        # 验证结果
        self.assertIn("user_id", result)
        self.assertIn("email", result)
        self.assertEqual(result["email"], "[电子邮件]")
        self.assertEqual(result["phone"], "[手机号]")

    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试前设置单例为测试实例
        with patch('src.audience.privacy_guard._privacy_adapter', self.privacy_adapter):
            # 测试anonymize_data
            self.privacy_adapter.anonymize_data = MagicMock(return_value={"anonymized": True})
            result = anonymize_data(self.test_raw_data)
            self.privacy_adapter.anonymize_data.assert_called_once_with(self.test_raw_data)
            self.assertEqual(result, {"anonymized": True})
            
            # 测试enforce_consent
            self.privacy_adapter.enforce_consent = MagicMock(return_value=True)
            result = enforce_consent(self.test_user_id, "preference_tracking")
            self.privacy_adapter.enforce_consent.assert_called_once_with(self.test_user_id, "preference_tracking")
            self.assertTrue(result)
            
            # 测试check_consent
            self.privacy_adapter.check_consent = MagicMock(return_value=True)
            result = check_consent(self.test_user_id, "preference_tracking")
            self.privacy_adapter.check_consent.assert_called_once_with(self.test_user_id, "preference_tracking")
            self.assertTrue(result)
            
            # 测试record_consent
            self.privacy_adapter.record_consent = MagicMock(return_value=True)
            metadata = {"ip": "127.0.0.1"}
            result = record_consent(self.test_user_id, "preference_tracking", "granted", metadata)
            self.privacy_adapter.record_consent.assert_called_once_with(
                self.test_user_id, "preference_tracking", "granted", metadata
            )
            self.assertTrue(result)

if __name__ == "__main__":
    unittest.main() 