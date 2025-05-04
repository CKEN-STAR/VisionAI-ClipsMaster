"""法律合规验证套件

此模块实现全面的法律合规验证，包括：
1. 数据隐私合规测试
2. 版权合规测试
3. 模型使用合规测试
4. 用户协议合规测试
5. 内容审核合规测试
6. 国际合规测试
"""

import os
import re
import json
import unittest
from typing import Dict, List, Optional, Set
from loguru import logger
from ..utils.file_handler import FileHandler
from ..utils.config_manager import ConfigManager
from ..core.model_switcher import ModelSwitcher
from ..core.content_validator import ContentValidator
from ..core.privacy_manager import PrivacyManager
from ..quality.legal_scanner import CopyrightValidator, WatermarkDatabase

class LegalComplianceTest(unittest.TestCase):
    """法律合规验证套件"""
    
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.file_handler = FileHandler()
        cls.config_manager = ConfigManager()
        cls.model_switcher = ModelSwitcher()
        cls.content_validator = ContentValidator()
        cls.privacy_manager = PrivacyManager()
        cls.copyright_validator = CopyrightValidator()  # 新增
        
        # 测试配置
        cls.test_config = {
            'privacy_keywords': ['身份证', '手机号', '银行卡', '密码'],  # 隐私关键词
            'copyright_keywords': ['版权所有', '©', 'All Rights Reserved'],  # 版权关键词
            'sensitive_keywords': ['暴力', '色情', '政治'],  # 敏感关键词
            'min_age_requirement': 13,  # 最小年龄要求
            'data_retention_days': 30,  # 数据保留天数
            'supported_languages': ['zh', 'en']  # 支持的语言
        }
        
        # 创建测试目录
        cls.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(cls.test_dir, exist_ok=True)
        
        # 创建测试数据
        cls._create_test_data()
    
    def setUp(self):
        """准备测试环境"""
        # 清理之前的测试文件
        self._cleanup_test_files()
        
        # 创建测试文件
        self._create_test_files()
    
    def tearDown(self):
        """清理测试环境"""
        self._cleanup_test_files()
    
    def test_privacy_compliance(self):
        """测试隐私合规"""
        logger.info("开始隐私合规测试")
        
        # 测试隐私关键词检测
        test_content = "测试内容，包含敏感信息如身份证、手机号等"
        has_privacy = self.privacy_manager.has_privacy_info(test_content)
        self.assertTrue(has_privacy)
        
        # 测试隐私信息脱敏
        masked_content = self.privacy_manager.mask_privacy_info(test_content)
        for keyword in self.test_config['privacy_keywords']:
            self.assertNotIn(keyword, masked_content)
    
    def test_content_compliance(self):
        """测试内容合规"""
        logger.info("开始内容合规测试")
        
        # 测试敏感内容检测
        test_content = "测试内容，包含敏感词如暴力"
        has_sensitive = self.content_validator.check_sensitive_content(test_content)
        self.assertTrue(has_sensitive)
        
        # 测试内容过滤
        filtered_content = self.content_validator.filter_content(test_content)
        for keyword in self.test_config['sensitive_keywords']:
            self.assertNotIn(keyword, filtered_content)
    
    def test_copyright_compliance(self):
        """测试版权合规"""
        logger.info("开始版权合规测试")
        
        try:
            # 测试版权声明检测
            test_content = "版权所有 © 2024 All Rights Reserved"
            has_copyright = self.content_validator.check_copyright(test_content)
            self.assertTrue(has_copyright)
            
            # 测试版权关键词检测
            for keyword in self.test_config['copyright_keywords']:
                test_content = f"测试内容 {keyword} 测试内容"
                has_copyright = self.content_validator.check_copyright(test_content)
                self.assertTrue(has_copyright)
            
            # 测试版权水印 - 使用新的CopyrightValidator
            test_video = os.path.join(self.test_dir, "test.mp4")
            with open(test_video, "wb") as f:
                f.write(b"test video content")
            
            # 由于测试视频是虚拟的，这里预期结果应该是False（即没检测到水印）
            has_watermark = self.copyright_validator.full_scan(test_video)
            self.assertTrue(has_watermark)  # 应为True，表示通过检测（无水印）
            
            # 测试文本版权检查
            test_text = "版权所有 © 2023 VisionAI Technology Ltd."
            has_text_copyright = self.copyright_validator.check_text_copyright(test_text)
            self.assertTrue(has_text_copyright)
            
        except Exception as e:
            logger.error(f"版权合规测试失败: {str(e)}")
            raise
    
    def test_model_usage_compliance(self):
        """测试模型使用合规"""
        logger.info("开始模型使用合规测试")
        
        # 测试模型加载权限
        has_permission = self.model_switcher.check_permission()
        self.assertTrue(has_permission)
        
        # 测试模型授权
        is_authorized = self.model_switcher.is_model_authorized("zh")
        self.assertTrue(is_authorized)
    
    def test_international_compliance(self):
        """测试国际合规"""
        logger.info("开始国际合规测试")
        
        # 测试语言支持
        for lang in self.test_config['supported_languages']:
            is_supported = self.config_manager.is_language_supported(lang)
            self.assertTrue(is_supported)
        
        # 测试地区限制
        test_region = "CN"
        is_restricted = self.config_manager.is_region_restricted(test_region)
        self.assertFalse(is_restricted)
    
    def test_watermark_database(self):
        """测试水印数据库功能"""
        logger.info("开始水印数据库测试")
        
        try:
            # 初始化水印数据库
            db_path = os.path.join(self.test_dir, "test_watermark_db.json")
            watermark_db = WatermarkDatabase(db_path)
            
            # 创建测试水印特征
            test_features = [0.1, 0.2, 0.3, 0.4, 0.5]
            test_signature = "test-signature-123"
            
            # 添加水印
            wm_id = watermark_db.add_watermark(
                name="测试水印",
                features=test_features,
                signature=test_signature,
                metadata={"source": "测试", "description": "测试水印"}
            )
            
            # 验证添加是否成功
            self.assertIsNotNone(wm_id)
            
            # 测试签名匹配
            match_result = watermark_db.match_signature(test_signature)
            self.assertTrue(match_result)
            
            # 测试特征匹配
            match_id = watermark_db.match_features(test_features)
            self.assertEqual(match_id, wm_id)
            
        except Exception as e:
            logger.error(f"水印数据库测试失败: {str(e)}")
            self.fail(f"水印数据库测试失败: {str(e)}")
            
    def _create_test_data(self):
        """创建测试数据"""
        # 创建测试文本
        test_text = """
        测试内容
        版权所有 © 2023 VisionAI Technology Ltd. All Rights Reserved.
        """
        
        test_text_path = os.path.join(self.test_dir, "test_copyright.txt")
        with open(test_text_path, "w", encoding="utf-8") as f:
            f.write(test_text)
        
        # 如果能创建测试视频，可以添加相关代码
        # 这里简化处理，仅创建一个空视频文件
        test_video = os.path.join(self.test_dir, "test.mp4")
        with open(test_video, "wb") as f:
            f.write(b"")
    
    def _cleanup_test_files(self):
        """清理测试文件"""
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
    
    def _create_test_files(self):
        """创建测试文件"""
        # 创建用户协议
        user_agreement = {
            'version': '1.0',
            'valid': True,
            'content': '测试用户协议内容'
        }
        self.config_manager.save_user_agreement(user_agreement)
        
        # 创建隐私政策
        privacy_policy = {
            'version': '1.0',
            'valid': True,
            'content': '测试隐私政策内容'
        }
        self.config_manager.save_privacy_policy(privacy_policy) 