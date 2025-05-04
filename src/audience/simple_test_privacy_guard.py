#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私安全适配器简化测试

这是一个独立的简化测试脚本，不依赖于项目的其他模块。
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 导入模拟模块
import src.audience.privacy_guard_mock as mock

# 替换真实模块为模拟模块
sys.modules['src.data.storage_manager'] = mock
sys.modules['src.utils.privacy_manager'] = mock
sys.modules['src.core.privacy_manager'] = mock

# 导入被测模块
from src.audience.privacy_guard import (
    PrivacyAdapter, 
    ConsentRequiredError
)

class TestPrivacyAdapter(unittest.TestCase):
    """隐私安全适配器简化测试类"""
    
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
    unittest.main() 