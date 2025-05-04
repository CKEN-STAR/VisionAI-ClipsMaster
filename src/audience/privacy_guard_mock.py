#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私安全适配器模拟模块

为演示和测试提供模拟存储和隐私管理器。
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class MockStorageManager:
    """模拟存储管理器，用于演示和测试隐私安全适配器"""
    
    def __init__(self):
        """初始化模拟存储管理器"""
        # 用户同意存储
        self.user_consents = {}
        
        # 用户数据存储
        self.user_data = {}
        
        # 测试数据（默认为空）
        self.test_data = {}
    
    def get_user_consents(self, user_id: str) -> Dict[str, Any]:
        """获取用户同意记录
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户同意记录
        """
        if user_id not in self.user_consents:
            return {}
        
        return self.user_consents[user_id]
    
    def save_user_consent(self, user_id: str, feature: str, consent_record: Dict[str, Any]) -> bool:
        """保存用户同意记录
        
        Args:
            user_id: 用户ID
            feature: 功能名称
            consent_record: 同意记录
            
        Returns:
            bool: 是否成功保存
        """
        if user_id not in self.user_consents:
            self.user_consents[user_id] = {}
        
        self.user_consents[user_id][feature] = consent_record
        return True
    
    def clean_user_data(self, user_id: str, data_type: str, cutoff_date: datetime) -> int:
        """清理用户数据
        
        Args:
            user_id: 用户ID
            data_type: 数据类型
            cutoff_date: 截止日期
            
        Returns:
            int: 清理的数据数量
        """
        # 模拟清理数据，根据数据类型返回不同数量
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


class MockUtilsPrivacyManager:
    """模拟工具隐私管理器"""
    
    def __init__(self):
        """初始化模拟工具隐私管理器"""
        pass
    
    def redact_pii(self, text: str) -> str:
        """编辑文本中的隐私信息
        
        Args:
            text: 要编辑的文本
            
        Returns:
            str: 编辑后的文本
        """
        # 简单的模拟编辑逻辑
        text = text.replace('"email": "zhangsan@example.com"', '"email": "[电子邮件]"')
        text = text.replace('"phone": "13912345678"', '"phone": "[手机号]"')
        text = text.replace('"address": "北京市海淀区中关村南大街5号"', '"address": "[地址信息]"')
        
        return text


class MockCorePrivacyManager:
    """模拟核心隐私管理器"""
    
    def __init__(self):
        """初始化模拟核心隐私管理器"""
        pass
    
    def detect_pii(self, content: str) -> Dict[str, List[str]]:
        """检测内容中的隐私信息
        
        Args:
            content: 要检测的内容
            
        Returns:
            Dict[str, List[str]]: 检测到的隐私信息
        """
        result = {}
        
        # 简单的模拟检测逻辑
        if "zhangsan@example.com" in content:
            result["email"] = ["zhangsan@example.com"]
        
        if "13912345678" in content:
            result["phone"] = ["13912345678"]
        
        if "北京市海淀区中关村南大街5号" in content:
            result["address"] = ["北京市海淀区中关村南大街5号"]
        
        if "张三" in content:
            result["name"] = ["张三"]
        
        return result


# 模拟对象单例
_mock_storage_manager = None
_mock_utils_privacy_manager = None
_mock_core_privacy_manager = None

def get_storage_manager() -> MockStorageManager:
    """获取模拟存储管理器实例
    
    Returns:
        MockStorageManager: 模拟存储管理器实例
    """
    global _mock_storage_manager
    if _mock_storage_manager is None:
        _mock_storage_manager = MockStorageManager()
    return _mock_storage_manager

def get_utils_privacy_manager() -> MockUtilsPrivacyManager:
    """获取模拟工具隐私管理器实例
    
    Returns:
        MockUtilsPrivacyManager: 模拟工具隐私管理器实例
    """
    global _mock_utils_privacy_manager
    if _mock_utils_privacy_manager is None:
        _mock_utils_privacy_manager = MockUtilsPrivacyManager()
    return _mock_utils_privacy_manager

def get_core_privacy_manager() -> MockCorePrivacyManager:
    """获取模拟核心隐私管理器实例
    
    Returns:
        MockCorePrivacyManager: 模拟核心隐私管理器实例
    """
    global _mock_core_privacy_manager
    if _mock_core_privacy_manager is None:
        _mock_core_privacy_manager = MockCorePrivacyManager()
    return _mock_core_privacy_manager 