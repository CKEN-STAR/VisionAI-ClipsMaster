"""训练数据预处理模块

此模块负责对训练数据进行预处理，包括:
1. 语言检测和隔离
2. 数据清洗和标准化
3. 文本格式验证
4. 重复数据检测和处理
"""

import os
import hashlib
from typing import List, Dict, Optional, Tuple
import langdetect
from loguru import logger
from pathlib import Path

from src.utils.exceptions import DataCleaningError
from src.utils.data_validator import DataPathValidator


class DataCleaner:
    """数据清洗器类"""

    def __init__(self, data_validator: Optional[DataPathValidator] = None):
        """初始化数据清洗器
        
        Args:
            data_validator: 数据路径验证器实例
        """
        self.data_validator = data_validator or DataPathValidator()
        self.supported_languages = {'zh', 'en'}
        self.min_text_length = 10  # 最小文本长度
        self.max_text_length = 1000  # 最大文本长度
        
        # 初始化统计信息
        self.stats = {
            'processed_files': 0,
            'cleaned_files': 0,
            'removed_files': 0,
            'errors': []
        }

    def detect_language(self, text: str) -> str:
        """检测文本语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            str: 检测到的语言代码 ('zh' 或 'en')
        """
        try:
            lang = langdetect.detect(text)
            # 将langdetect的语言代码映射到我们的支持语言
            lang_mapping = {
                'zh-cn': 'zh',
                'zh-tw': 'zh',
                'en': 'en'
            }
            return lang_mapping.get(lang, 'unknown')
        except Exception as e:
            logger.warning(f"语言检测失败: {str(e)}")
            return 'unknown'

    def validate_text_format(self, text: str) -> Tuple[bool, Optional[str]]:
        """验证文本格式
        
        Args:
            text: 要验证的文本
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if len(text) < self.min_text_length:
            return False, f"文本长度过短 ({len(text)} < {self.min_text_length})"
        
        if len(text) > self.max_text_length:
            return False, f"文本长度过长 ({len(text)} > {self.max_text_length})"
            
        # 检查是否包含基本的标点符号
        if not any(char in text for char in '.,!?。，！？'):
            return False, "文本缺少基本标点符号"
            
        return True, None

    def clean_text(self, text: str) -> str:
        """清理和标准化文本
        
        Args:
            text: 要清理的文本
            
        Returns:
            str: 清理后的文本
        """
        # 移除多余的空白字符
        text = ' '.join(text.split())
        
        # 标准化标点符号
        punctuation_map = {
            '，': ',',
            '。': '.',
            '！': '!',
            '？': '?',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'"
        }
        for ch, en in punctuation_map.items():
            text = text.replace(ch, en)
            
        return text

    def calculate_text_hash(self, text: str) -> str:
        """计算文本的哈希值用于重复检测
        
        Args:
            text: 要计算哈希的文本
            
        Returns:
            str: 文本的哈希值
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def filter_by_language(self, file_path: str, target_lang: str) -> bool:
        """根据语言过滤文件
        
        Args:
            file_path: 文件路径
            target_lang: 目标语言
            
        Returns:
            bool: 是否保留该文件
        """
        if target_lang not in self.supported_languages:
            raise DataCleaningError(f"不支持的语言: {target_lang}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read(4096)  # 读取前4KB用于语言检测
                detected_lang = self.detect_language(text)
                
                if detected_lang != target_lang:
                    logger.warning(f"删除跨语言文件: {file_path}")
                    os.remove(file_path)
                    self.stats['removed_files'] += 1
                    return False
                    
                return True
        except Exception as e:
            self.stats['errors'].append(f"处理文件 {file_path} 时出错: {str(e)}")
            return False

    def process_file(self, file_path: str, target_lang: str) -> bool:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            target_lang: 目标语言
            
        Returns:
            bool: 处理是否成功
        """
        self.stats['processed_files'] += 1
        
        try:
            # 首先验证文件路径
            if not self.data_validator.validate_path_exists(file_path):
                raise DataCleaningError(f"文件不存在: {file_path}")
                
            # 检查语言隔离
            if not self.filter_by_language(file_path, target_lang):
                return False
                
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # 验证文本格式
            is_valid, error_msg = self.validate_text_format(text)
            if not is_valid:
                logger.warning(f"文件 {file_path} 格式无效: {error_msg}")
                os.remove(file_path)
                self.stats['removed_files'] += 1
                return False
                
            # 清理文本
            cleaned_text = self.clean_text(text)
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
                
            self.stats['cleaned_files'] += 1
            return True
            
        except Exception as e:
            self.stats['errors'].append(f"处理文件 {file_path} 时出错: {str(e)}")
            return False

    def process_directory(self, directory: str, target_lang: str) -> Dict:
        """处理整个目录
        
        Args:
            directory: 目录路径
            target_lang: 目标语言
            
        Returns:
            Dict: 处理统计信息
        """
        if not os.path.isdir(directory):
            raise DataCleaningError(f"目录不存在: {directory}")
            
        # 重置统计信息
        self.stats = {
            'processed_files': 0,
            'cleaned_files': 0,
            'removed_files': 0,
            'errors': []
        }
        
        # 遍历目录下的所有文件
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt') or file.endswith('.srt'):
                    file_path = os.path.join(root, file)
                    self.process_file(file_path, target_lang)
                    
        return self.stats

    def get_statistics(self) -> Dict:
        """获取处理统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.stats 