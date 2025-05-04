"""隐私管理器模块

此模块提供个人隐私信息(PII)检测、匿名化和编辑功能
"""

import re
import json
import logging
import hashlib
import uuid
from typing import Dict, List, Any, Union, Tuple, Optional, Set

# 配置日志
logger = logging.getLogger(__name__)

class PrivacyManager:
    """隐私管理器类，用于检测和处理个人隐私信息(PII)"""
    
    def __init__(self, config_path: str = None):
        """初始化隐私管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.pii_patterns = {
            "phone": r'1[3-9]\d{9}',  # 中国手机号
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 电子邮件
            "id_card": r'\d{17}[\dXx]',  # 中国身份证号
            "credit_card": r'\b(?:\d{4}[ -]?){3}\d{4}\b',  # 信用卡号
            "address": r'(?:省|市|区|县|路|街道|号)(?:[^，。；\n\r\t]{2,30})',  # 简单的地址匹配
            "passport": r'[A-Z]{1,2}\d{6,9}',  # 护照号码
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IPv4地址
            "name": r'(?:先生|女士|小姐)(?:\s*)[^\s，。；\n\r\t]{2,4}'  # 简单的姓名匹配
        }
        
        # 初始化已检测到的PII哈希集合，用于追踪检测到的PII
        self.detected_pii_hashes = set()
        
        # 初始化匿名化映射表
        self.anonymization_map = {}
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """检测文本中的个人隐私信息
        
        Args:
            text: 待检测的文本
            
        Returns:
            包含检测到的PII信息的列表
        """
        results = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                start, end = match.span()
                pii_value = match.group()
                
                # 计算PII值的哈希用于跟踪
                pii_hash = hashlib.md5(pii_value.encode()).hexdigest()
                
                # 将检测到的PII添加到结果中
                results.append({
                    "type": pii_type,
                    "value": pii_value,
                    "start": start,
                    "end": end,
                    "hash": pii_hash
                })
                
                # 添加到已检测的PII集合中
                self.detected_pii_hashes.add(pii_hash)
        
        return results
    
    def anonymize_pii(self, data: Union[str, Dict, List]) -> Union[str, Dict, List]:
        """匿名化数据中的个人隐私信息
        
        Args:
            data: 待匿名化的数据，可以是字符串、字典或列表
            
        Returns:
            匿名化后的数据
        """
        if isinstance(data, str):
            return self._anonymize_text(data)
        elif isinstance(data, dict):
            return self._anonymize_dict(data)
        elif isinstance(data, list):
            return self._anonymize_list(data)
        else:
            # 不支持的数据类型
            logger.warning(f"不支持的数据类型: {type(data)}")
            return data
    
    def _anonymize_text(self, text: str) -> str:
        """匿名化文本中的个人隐私信息
        
        Args:
            text: 待匿名化的文本
            
        Returns:
            匿名化后的文本
        """
        anonymized_text = text
        
        # 检测PII
        pii_items = self.detect_pii(text)
        
        # 按照从最后到最前的顺序匿名化，避免位置偏移问题
        pii_items.sort(key=lambda x: x["start"], reverse=True)
        
        for pii_item in pii_items:
            pii_type = pii_item["type"]
            pii_value = pii_item["value"]
            start, end = pii_item["start"], pii_item["end"]
            
            # 获取或生成匿名化值
            if pii_value not in self.anonymization_map:
                self.anonymization_map[pii_value] = self._generate_anonymous_value(pii_type)
            
            anonymous_value = self.anonymization_map[pii_value]
            
            # 替换文本
            anonymized_text = anonymized_text[:start] + anonymous_value + anonymized_text[end:]
        
        return anonymized_text
    
    def _anonymize_dict(self, data: Dict) -> Dict:
        """匿名化字典中的个人隐私信息
        
        Args:
            data: 待匿名化的字典
            
        Returns:
            匿名化后的字典
        """
        anonymized_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                anonymized_data[key] = self._anonymize_text(value)
            elif isinstance(value, dict):
                anonymized_data[key] = self._anonymize_dict(value)
            elif isinstance(value, list):
                anonymized_data[key] = self._anonymize_list(value)
            else:
                anonymized_data[key] = value
        
        return anonymized_data
    
    def _anonymize_list(self, data: List) -> List:
        """匿名化列表中的个人隐私信息
        
        Args:
            data: 待匿名化的列表
            
        Returns:
            匿名化后的列表
        """
        anonymized_data = []
        
        for item in data:
            if isinstance(item, str):
                anonymized_data.append(self._anonymize_text(item))
            elif isinstance(item, dict):
                anonymized_data.append(self._anonymize_dict(item))
            elif isinstance(item, list):
                anonymized_data.append(self._anonymize_list(item))
            else:
                anonymized_data.append(item)
        
        return anonymized_data
    
    def _generate_anonymous_value(self, pii_type: str) -> str:
        """根据PII类型生成匿名化值
        
        Args:
            pii_type: PII类型
            
        Returns:
            匿名化值
        """
        if pii_type == "phone":
            return "[手机号]"
        elif pii_type == "email":
            return f"[电子邮件-{str(uuid.uuid4())[:8]}]"
        elif pii_type == "id_card":
            return "[身份证号]"
        elif pii_type == "credit_card":
            return "[信用卡号]"
        elif pii_type == "address":
            return "[地址信息]"
        elif pii_type == "passport":
            return "[护照号]"
        elif pii_type == "ip_address":
            return "[IP地址]"
        elif pii_type == "name":
            return "[姓名]"
        else:
            return f"[已匿名化数据-{str(uuid.uuid4())[:8]}]"
    
    def redact_pii(self, text: str, replacement_char: str = "*") -> str:
        """编辑文本中的个人隐私信息，使用指定字符替换
        
        Args:
            text: 待编辑的文本
            replacement_char: 替换字符，默认为*
            
        Returns:
            编辑后的文本
        """
        redacted_text = text
        
        # 检测PII
        pii_items = self.detect_pii(text)
        
        # 按照从最后到最前的顺序编辑，避免位置偏移问题
        pii_items.sort(key=lambda x: x["start"], reverse=True)
        
        for pii_item in pii_items:
            pii_value = pii_item["value"]
            start, end = pii_item["start"], pii_item["end"]
            length = end - start
            
            # 替换为替代字符
            redacted_value = replacement_char * length
            
            # 替换文本
            redacted_text = redacted_text[:start] + redacted_value + redacted_text[end:]
        
        return redacted_text
    
    def extract_pii_from_json(self, json_data: Union[str, Dict]) -> List[Dict[str, Any]]:
        """从JSON数据中提取个人隐私信息
        
        Args:
            json_data: JSON数据，可以是字符串或字典
            
        Returns:
            提取到的PII信息列表
        """
        # 如果是字符串，尝试解析为JSON
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError:
                logger.error("无效的JSON字符串")
                return []
        else:
            data = json_data
        
        # 提取所有文本值
        extracted_texts = self._extract_text_values(data)
        
        # 检测所有文本值中的PII
        all_pii = []
        for text in extracted_texts:
            pii_items = self.detect_pii(text)
            all_pii.extend(pii_items)
        
        return all_pii
    
    def _extract_text_values(self, data: Any) -> List[str]:
        """递归提取所有文本值
        
        Args:
            data: 任意数据类型
            
        Returns:
            提取到的文本值列表
        """
        texts = []
        
        if isinstance(data, str):
            texts.append(data)
        elif isinstance(data, dict):
            for value in data.values():
                texts.extend(self._extract_text_values(value))
        elif isinstance(data, list):
            for item in data:
                texts.extend(self._extract_text_values(item))
        
        return texts
    
    def get_pii_statistics(self) -> Dict[str, Any]:
        """获取PII检测统计信息
        
        Returns:
            PII统计信息字典
        """
        # 按类型计数
        type_counts = {}
        for pii_type in self.pii_patterns.keys():
            type_counts[pii_type] = 0
        
        for pii_value, anonymous_value in self.anonymization_map.items():
            # 根据匿名化值的格式推断PII类型
            if anonymous_value == "[手机号]":
                type_counts["phone"] += 1
            elif anonymous_value.startswith("[电子邮件-"):
                type_counts["email"] += 1
            elif anonymous_value == "[身份证号]":
                type_counts["id_card"] += 1
            elif anonymous_value == "[信用卡号]":
                type_counts["credit_card"] += 1
            elif anonymous_value == "[地址信息]":
                type_counts["address"] += 1
            elif anonymous_value == "[护照号]":
                type_counts["passport"] += 1
            elif anonymous_value == "[IP地址]":
                type_counts["ip_address"] += 1
            elif anonymous_value == "[姓名]":
                type_counts["name"] += 1
        
        return {
            "total_unique_pii": len(self.detected_pii_hashes),
            "anonymized_count": len(self.anonymization_map),
            "type_counts": type_counts
        } 