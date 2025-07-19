"""隐私管理模块

此模块提供隐私数据管理功能，包括：
1. 个人信息识别与保护
2. 数据匿名化
3. 隐私数据加密
4. 数据保留期限管理
5. 数据脱敏
"""

import os
import re
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional, Tuple, Union
import logging
from loguru import logger


class PrivacyManager:
    """隐私管理器，负责处理和保护用户隐私数据"""
    
    def __init__(self, config_path: str = "configs/security_policy.json"):
        """初始化隐私管理器
        
        Args:
            config_path: 安全配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 隐私数据模式
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:(?:\+|00)86)?1[3-9]\d{9}\b',  # 中国手机号
            "id_card": r'\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}(?:\d|X|x)\b',  # 中国身份证
            "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            "address": r'\b\d{1,3}(?:号|室|弄|单元)|(?:路|街|道|巷|小区|大厦|广场|公寓)\b',
            "name": r'\b(?:[\u4e00-\u9fa5]{2,4})\b'  # 中文姓名2-4个字
        }
        
        # 隐私保护策略
        self.privacy_policy = self.config.get("privacy_protection", {
            "anonymize_method": "hash",  # 匿名化方法: hash/mask/token
            "retention_days": 30,  # 数据保留天数
            "encryption_enabled": True,  # 是否加密
            "secure_deletion": True,  # 安全删除
            "auto_redact": True  # 自动编辑
        })
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def detect_pii(self, content: str) -> Dict[str, List[str]]:
        """检测内容中的个人身份信息（PII）
        
        Args:
            content: 要检查的文本内容
            
        Returns:
            检测到的各类个人信息列表，按类型分组
        """
        if not content:
            return {}
        
        result = {}
        
        # 检测各类隐私信息
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                result[pii_type] = matches
        
        return result
    
    def anonymize_data(self, data: str, data_type: str = None) -> str:
        """匿名化处理数据
        
        Args:
            data: 要匿名化的数据
            data_type: 数据类型，如果指定将使用特定的匿名化方法
            
        Returns:
            匿名化处理后的数据
        """
        if not data:
            return data
        
        method = self.privacy_policy.get("anonymize_method", "hash")
        
        # 根据数据类型选择特定处理方法
        if data_type == "email":
            return self._anonymize_email(data)
        elif data_type == "phone":
            return self._anonymize_phone(data)
        elif data_type == "id_card":
            return self._anonymize_id_card(data)
        elif data_type == "name":
            return self._anonymize_name(data)
        
        # 通用匿名化方法
        if method == "hash":
            # 对数据进行哈希处理
            return hashlib.sha256(data.encode()).hexdigest()[:8]
        elif method == "mask":
            # 使用*遮蔽部分字符
            if len(data) <= 2:
                return "*" * len(data)
            else:
                return data[0] + "*" * (len(data) - 2) + data[-1]
        elif method == "token":
            # 使用随机令牌替换
            return f"TOKEN_{hash(data) % 10000:04d}"
        else:
            # 默认返回原始数据
            return data
    
    def _anonymize_email(self, email: str) -> str:
        """匿名化电子邮箱
        
        Args:
            email: 电子邮箱地址
            
        Returns:
            匿名化后的电子邮箱
        """
        if '@' not in email:
            return self.anonymize_data(email)
        
        username, domain = email.split('@', 1)
        if len(username) <= 2:
            masked_username = username[0] + "*"
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    def _anonymize_phone(self, phone: str) -> str:
        """匿名化电话号码
        
        Args:
            phone: 电话号码
            
        Returns:
            匿名化后的电话号码
        """
        if len(phone) < 7:
            return "*" * len(phone)
        
        # 保留前3位和后4位，中间用*代替
        return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]
    
    def _anonymize_id_card(self, id_card: str) -> str:
        """匿名化身份证号
        
        Args:
            id_card: 身份证号
            
        Returns:
            匿名化后的身份证号
        """
        if len(id_card) != 18:
            return "*" * len(id_card)
        
        # 保留前6位（地区码）和最后4位，中间使用*代替
        return id_card[:6] + "*" * 8 + id_card[-4:]
    
    def _anonymize_name(self, name: str) -> str:
        """匿名化姓名
        
        Args:
            name: 姓名
            
        Returns:
            匿名化后的姓名
        """
        if len(name) <= 1:
            return name
        elif len(name) == 2:
            return name[0] + "*"
        else:
            # 保留姓氏，其余用*代替
            return name[0] + "*" * (len(name) - 1)
    
    def redact_pii(self, content: str) -> str:
        """编辑处理文本中的个人身份信息
        
        Args:
            content: 包含PII的文本
            
        Returns:
            编辑后的文本
        """
        if not content:
            return content
        
        result = content
        
        # 检测并处理各类隐私数据
        pii_data = self.detect_pii(content)
        
        for pii_type, instances in pii_data.items():
            for instance in instances:
                anonymized = self.anonymize_data(instance, pii_type)
                result = result.replace(instance, anonymized)
        
        return result
    
    def encrypt_data(self, data: str, key: str = None) -> str:
        """加密数据
        
        Args:
            data: 要加密的数据
            key: 加密密钥
            
        Returns:
            加密后的数据
        """
        if not data:
            return data
        
        if not self.privacy_policy.get("encryption_enabled", True):
            return data
        
        try:
            # 使用简单的base64编码作为示例
            # 实际应用中应使用更安全的加密算法
            encoded = base64.b64encode(data.encode()).decode()
            return encoded
        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str, key: str = None) -> str:
        """解密数据
        
        Args:
            encrypted_data: 加密的数据
            key: 解密密钥
            
        Returns:
            解密后的数据
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            # 使用base64解码
            decoded = base64.b64decode(encrypted_data.encode()).decode()
            return decoded
        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            return encrypted_data
    
    def should_retain_data(self, timestamp: datetime) -> bool:
        """检查数据是否应该保留
        
        Args:
            timestamp: 数据时间戳
            
        Returns:
            是否应保留数据
        """
        retention_days = self.privacy_policy.get("retention_days", 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        return timestamp > cutoff_date
    
    def secure_delete(self, file_path: str) -> bool:
        """安全删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功删除
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False
        
        try:
            # 如果启用安全删除，先用随机数据覆盖文件
            if self.privacy_policy.get("secure_deletion", True):
                file_size = os.path.getsize(file_path)
                with open(file_path, "wb") as f:
                    # 写入随机数据
                    f.write(os.urandom(file_size))
            
            # 删除文件
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"安全删除文件失败: {e}")
            return False 