#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 地域合规适配器

根据不同地区的法律法规要求，对视频处理和数据存储进行适配，
确保系统在全球范围内的合规性。主要包括：
- 中国大陆的数据本地化和内容审核要求
- 欧盟GDPR要求（数据处理协议、被遗忘权、算法解释权）
- 美国DMCA合规要求
- 全球通用的内容安全和版权保护需求
"""

import os
import sys
import json
import logging
import datetime
import importlib
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# 尝试导入项目日志模块
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("region_compliance")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("region_compliance")

# 配置文件路径
CONFIG_DIR = os.path.join(PROJECT_ROOT, "configs")
REGION_CONFIG_PATH = os.path.join(CONFIG_DIR, "regional", "compliance_rules.json")

# 确保配置目录存在
os.makedirs(os.path.join(CONFIG_DIR, "regional"), exist_ok=True)


class RegionalComplianceError(Exception):
    """区域合规性错误"""
    def __init__(self, message: str, region: str = "", requirement: str = ""):
        self.region = region
        self.requirement = requirement
        self.compliance_info = {
            "region": region,
            "requirement": requirement,
            "timestamp": datetime.datetime.now().isoformat()
        }
        super().__init__(message)


class RegionalCompliance:
    """地域合规适配器"""
    
    # 单例实例
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式，确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super(RegionalCompliance, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, region: str = None, config_path: str = None):
        """
        初始化区域合规适配器
        
        Args:
            region: 区域代码，如CN(中国)、EU(欧盟)、US(美国)，默认自动检测
            config_path: 配置文件路径，默认使用configs/regional/compliance_rules.json
        """
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return
            
        self.region = region or self._detect_region()
        self.config_path = config_path or REGION_CONFIG_PATH
        
        # 配置不同地区的规则
        self.rules = {
            # 中国大陆规则
            "CN": {
                "watermark": True,           # 要求添加水印
                "data_localization": True,    # 数据本地化存储
                "content_review": True,       # 内容审核
                "real_name_verification": True, # 实名认证
                "minor_protection": True,     # 未成年人保护
                "algorithm_transparency": False, # 算法透明度
                "model_registration": True    # 模型备案
            },
            # 欧盟规则
            "EU": {
                "gdpr_compliance": True,      # GDPR合规
                "right_to_explain": True,     # 算法解释权
                "right_to_be_forgotten": True, # 被遗忘权
                "data_portability": True,     # 数据可携带性
                "consent_management": True,   # 同意管理
                "data_breach_notification": True, # 数据泄露通知
                "algorithm_transparency": True  # 算法透明度
            },
            # 美国规则
            "US": {
                "dmca_compliance": True,      # DMCA合规
                "ccpa_compliance": True,      # 加州消费者隐私法
                "coppa_compliance": True,     # 儿童在线隐私保护法
                "fair_use": True,             # 合理使用
                "state_specific_rules": True  # 州特定规则
            },
            # 全球通用规则
            "GLOBAL": {
                "content_safety": True,       # 内容安全
                "copyright_protection": True, # 版权保护
                "data_security": True,        # 数据安全
                "privacy_policy": True,       # 隐私政策
                "terms_of_service": True      # 服务条款
            }
        }
        
        # 加载配置文件
        self._load_config()
        
        # 初始化完成标记
        self._initialized = True
        
        logger.info(f"地域合规适配器初始化完成，当前区域: {self.region}")
    
    def _detect_region(self) -> str:
        """
        自动检测区域
        
        Returns:
            str: 区域代码 (CN/EU/US/GLOBAL)
        """
        # 尝试从系统配置中读取
        try:
            config_file = os.path.join(CONFIG_DIR, "system", "settings.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "region" in config:
                        return config["region"]
        except Exception as e:
            logger.warning(f"从系统配置检测区域失败: {str(e)}")
        
        # 尝试从环境变量中读取
        region = os.environ.get("VISIONAI_REGION")
        if region:
            return region
            
        # 尝试从语言设置推断
        try:
            import locale
            loc = locale.getlocale()[0]
            if loc:
                if loc.startswith("zh_CN"):
                    return "CN"
                elif loc.startswith(("de", "fr", "it", "es")) or "EU" in loc:
                    return "EU"
                elif loc.startswith("en_US"):
                    return "US"
        except Exception:
            pass
        
        # 默认返回全球设置
        return "GLOBAL"
    
    def _load_config(self) -> None:
        """从配置文件加载规则"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 更新默认规则
                    for region, rules in config.items():
                        if region in self.rules:
                            self.rules[region].update(rules)
                logger.info(f"已从 {self.config_path} 加载区域合规规则")
            else:
                # 创建默认配置文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.rules, f, ensure_ascii=False, indent=2)
                logger.info(f"已创建默认区域合规规则配置文件: {self.config_path}")
        except Exception as e:
            logger.error(f"加载区域合规规则失败: {str(e)}，使用默认规则")
    
    def apply_policy(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据地区应用不同合规策略
        
        Args:
            video: 视频数据字典
            
        Returns:
            Dict: 处理后的视频数据
        """
        # 如果视频没有设置地区，则使用当前实例的地区
        region = video.get("target_region", self.region)
        
        logger.info(f"为视频应用 {region} 区域合规政策")
        
        # 应用地区特定规则
        if region == "CN" and self.rules["CN"]["data_localization"]:
            video = self._store_in_china_region(video)
            
        if region == "EU" and self.rules["EU"]["gdpr_compliance"]:
            video = self._add_data_processing_agreement(video)
            
        if region == "US" and self.rules["US"]["dmca_compliance"]:
            video = self._add_dmca_compliance(video)
        
        # 应用通用规则
        if self.rules["GLOBAL"]["copyright_protection"]:
            video = self._add_copyright_protection(video)
            
        # 添加合规处理记录
        if "compliance" not in video:
            video["compliance"] = {}
            
        video["compliance"].update({
            "region": region,
            "processed_at": datetime.datetime.now().isoformat(),
            "rules_applied": self._get_applied_rules(region)
        })
        
        return video
    
    def _store_in_china_region(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        实现中国区域的数据本地化存储
        
        Args:
            video: 视频数据
            
        Returns:
            Dict: 处理后的视频数据
        """
        # 检查是否需要迁移存储位置
        if not video.get("storage_region") == "CN":
            logger.info("应用中国数据本地化要求，设置本地存储")
            
            # 更新存储区域
            video["storage_region"] = "CN"
            
            # 更新存储路径
            if "file_path" in video:
                # 更新为中国区域存储路径
                original_path = video["file_path"]
                new_path = original_path.replace("/global/", "/cn/")
                video["file_path"] = new_path
                video["original_path"] = original_path
                
                logger.info(f"更新存储路径: {original_path} -> {new_path}")
            
            # 标记要进行内容审核
            video["requires_content_review"] = True
        
        return video
    
    def _add_data_processing_agreement(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加欧盟GDPR数据处理协议信息
        
        Args:
            video: 视频数据
            
        Returns:
            Dict: 处理后的视频数据
        """
        logger.info("应用欧盟GDPR合规要求")
        
        # 添加GDPR元数据
        if "metadata" not in video:
            video["metadata"] = {}
            
        video["metadata"]["gdpr_compliant"] = True
        video["metadata"]["user_consent_obtained"] = True
        video["metadata"]["data_retention_policy"] = "30 days"
        video["metadata"]["right_to_explain_url"] = "https://visionai-clipsmaster.example.com/algorithm-explanation"
        video["metadata"]["data_controller"] = "VisionAI-ClipsMaster"
        
        # 确保有删除权限设置
        video["deletion_enabled"] = True
        
        return video
    
    def _add_dmca_compliance(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加美国DMCA合规信息
        
        Args:
            video: 视频数据
            
        Returns:
            Dict: 处理后的视频数据
        """
        logger.info("应用美国DMCA合规要求")
        
        # 添加DMCA元数据
        if "metadata" not in video:
            video["metadata"] = {}
            
        video["metadata"]["dmca_compliant"] = True
        video["metadata"]["copyright_notice"] = "© " + str(datetime.datetime.now().year) + " Original Content Owners"
        video["metadata"]["fair_use_claim"] = "This content may incorporate copyrighted material under fair use principles"
        video["metadata"]["dmca_agent_contact"] = "dmca@visionai-clipsmaster.example.com"
        
        return video
    
    def _add_copyright_protection(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加版权保护信息
        
        Args:
            video: 视频数据
            
        Returns:
            Dict: 处理后的视频数据
        """
        logger.info("应用全球版权保护要求")
        
        # 添加水印设置
        if "rendering" not in video:
            video["rendering"] = {}
            
        video["rendering"]["watermark"] = True
        video["rendering"]["watermark_text"] = "VisionAI-ClipsMaster"
        video["rendering"]["watermark_opacity"] = 0.7
        video["rendering"]["credits_section"] = True
        
        # 添加版权元数据
        if "metadata" not in video:
            video["metadata"] = {}
            
        video["metadata"]["copyright_protected"] = True
        
        return video
    
    def _get_applied_rules(self, region: str) -> Dict[str, Any]:
        """
        获取应用的规则列表
        
        Args:
            region: 区域代码
            
        Returns:
            Dict: 应用的规则列表
        """
        applied_rules = {}
        
        # 添加区域特定规则
        if region in self.rules:
            applied_rules.update(self.rules[region])
            
        # 添加全局规则
        applied_rules.update(self.rules["GLOBAL"])
        
        return applied_rules
    
    def change_region(self, region: str) -> None:
        """
        更改当前区域
        
        Args:
            region: 区域代码 (CN/EU/US/GLOBAL)
        """
        if region not in self.rules:
            raise ValueError(f"不支持的区域: {region}")
            
        self.region = region
        logger.info(f"区域已切换为: {region}")
    
    def get_rule(self, region: str, rule_name: str) -> Any:
        """
        获取特定区域的规则值
        
        Args:
            region: 区域代码
            rule_name: 规则名称
            
        Returns:
            Any: 规则值
        """
        if region not in self.rules:
            raise ValueError(f"不支持的区域: {region}")
            
        if rule_name not in self.rules[region]:
            raise ValueError(f"区域 {region} 中没有规则: {rule_name}")
            
        return self.rules[region][rule_name]
    
    def set_rule(self, region: str, rule_name: str, value: Any) -> None:
        """
        设置特定区域的规则值
        
        Args:
            region: 区域代码
            rule_name: 规则名称
            value: 规则值
        """
        if region not in self.rules:
            raise ValueError(f"不支持的区域: {region}")
            
        # 更新规则
        self.rules[region][rule_name] = value
        logger.info(f"已设置 {region} 区域的 {rule_name} 规则为: {value}")
        
        # 保存配置
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存区域合规规则失败: {str(e)}")
    
    def get_requirements(self, region: str = None) -> Dict[str, Any]:
        """
        获取区域合规要求
        
        Args:
            region: 区域代码，默认使用当前区域
            
        Returns:
            Dict: 合规要求
        """
        region = region or self.region
        
        if region not in self.rules:
            raise ValueError(f"不支持的区域: {region}")
            
        # 返回区域合规要求
        requirements = {
            "region": region,
            "rules": self.rules[region],
            "common_rules": self.rules["GLOBAL"]
        }
        
        return requirements
        
    def verify_compliance(self, video: Dict[str, Any], region: str = None) -> Tuple[bool, List[str]]:
        """
        验证视频是否符合区域合规要求
        
        Args:
            video: 视频数据
            region: 区域代码，默认使用视频指定的区域或当前区域
            
        Returns:
            Tuple[bool, List[str]]: (是否合规, 不合规项列表)
        """
        # 确定要检查的区域
        check_region = region or video.get("target_region", self.region)
        
        if check_region not in self.rules:
            raise ValueError(f"不支持的区域: {check_region}")
        
        non_compliant_items = []
        
        # 检查地区特定要求
        if check_region == "CN":
            # 检查数据本地化
            if self.rules["CN"]["data_localization"] and video.get("storage_region") != "CN":
                non_compliant_items.append("数据本地化存储")
                
            # 检查内容审核
            if self.rules["CN"]["content_review"] and not video.get("content_reviewed", False):
                non_compliant_items.append("内容审核")
                
            # 检查水印
            if self.rules["CN"]["watermark"] and not video.get("rendering", {}).get("watermark", False):
                non_compliant_items.append("水印要求")
        
        elif check_region == "EU":
            # 检查GDPR合规
            if self.rules["EU"]["gdpr_compliance"]:
                metadata = video.get("metadata", {})
                if not metadata.get("gdpr_compliant", False):
                    non_compliant_items.append("GDPR合规")
                    
                if not metadata.get("user_consent_obtained", False):
                    non_compliant_items.append("用户同意")
                    
                if not video.get("deletion_enabled", False):
                    non_compliant_items.append("被遗忘权")
        
        elif check_region == "US":
            # 检查DMCA合规
            if self.rules["US"]["dmca_compliance"]:
                metadata = video.get("metadata", {})
                if not metadata.get("dmca_compliant", False):
                    non_compliant_items.append("DMCA合规")
                    
                if not metadata.get("copyright_notice"):
                    non_compliant_items.append("版权声明")
        
        # 检查全局要求
        if self.rules["GLOBAL"]["copyright_protection"]:
            if not video.get("metadata", {}).get("copyright_protected", False):
                non_compliant_items.append("版权保护")
        
        # 返回验证结果
        is_compliant = len(non_compliant_items) == 0
        return is_compliant, non_compliant_items


# 单例访问器
def get_regional_compliance(region: str = None) -> RegionalCompliance:
    """
    获取区域合规适配器实例
    
    Args:
        region: 区域代码，默认自动检测
        
    Returns:
        RegionalCompliance: 区域合规适配器实例
    """
    return RegionalCompliance(region)


# 快速测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("区域合规适配器自测")
    
    # 创建适配器实例
    compliance = RegionalCompliance()
    
    # 测试不同区域的视频处理
    regions = ["CN", "EU", "US", "GLOBAL"]
    for region in regions:
        # 切换区域
        compliance.change_region(region)
        logger.info(f"当前区域: {region}")
        
        # 创建测试视频数据
        test_video = {
            "id": "test-123",
            "title": "Test Video",
            "file_path": "/global/videos/test.mp4",
            "target_region": region
        }
        
        # 应用合规策略
        processed_video = compliance.apply_policy(test_video)
        
        # 验证合规性
        is_compliant, non_compliant_items = compliance.verify_compliance(processed_video)
        logger.info(f"合规性验证: {'通过' if is_compliant else '不通过'}")
        
        if non_compliant_items:
            logger.warning(f"不合规项: {', '.join(non_compliant_items)}") 