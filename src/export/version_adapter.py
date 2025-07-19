#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本适配器模块

负责不同版本格式间的兼容转换，确保生成的文件能够被不同版本的软件正确解析。
主要功能：
1. XML版本降级/升级适配
2. 特性兼容性处理
3. 元数据格式转换
"""

import re
import logging
import xml.etree.ElementTree as ET
from packaging import version
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class VersionAdapter:
    """
    版本适配器类
    
    处理不同版本间的格式转换，确保兼容性
    """
    
    def __init__(self):
        """初始化版本适配器"""
        # 支持的最新版本
        self.latest_version = "3.0"
        
        # 支持的最低版本
        self.minimum_version = "2.0"
        
        # 版本别名映射
        self.version_aliases = {
            "专业版": "3.0",  # 专业版使用3.0格式
            "移动版": "2.9",  # 移动版使用2.9格式
            "标准版": "2.5",  # 标准版使用2.5格式
            "基础版": "2.0"   # 基础版使用2.0格式
        }
        
        # 版本之间的特性差异映射
        self.version_features = {
            "3.0": ["多轨道", "效果层", "字幕轨", "音频特效", "嵌套序列", "高级效果"],
            "2.9": ["多轨道", "效果层", "字幕轨"],
            "2.5": ["多轨道", "字幕轨"],
            "2.0": ["单轨道"]
        }
        
        # 版本特有效果支持
        self.version_effects = {
            "3.0": ["blur", "color", "transform", "audio", "transition", "text"],
            "2.9": ["transition"], # 2.9版本仅支持转场效果
            "2.5": [],
            "2.0": []
        }
        
        # 初始化Logger
        self.logger = logger
    
    def adapt_for_version(self, xml_content: str, target_version: str) -> str:
        """
        根据目标版本调整XML结构
        
        Args:
            xml_content: 原始XML内容
            target_version: 目标版本号或别名
            
        Returns:
            适配后的XML内容
        """
        # 解析目标版本
        resolved_target = self._resolve_version(target_version)
        
        # 提取当前XML版本
        current_version = self._extract_version(xml_content)
        
        # 如果版本一致，无需转换
        if current_version == resolved_target:
            return xml_content
            
        # 检查版本兼容性
        self._check_version_compatibility(current_version, resolved_target)
        
        # 根据版本差异进行转换
        if version.parse(current_version) > version.parse(resolved_target):
            # 降级操作 - 从高版本转换为低版本
            return self._downgrade_version(xml_content, current_version, resolved_target)
        else:
            # 升级操作 - 从低版本转换为高版本
            return self._upgrade_version(xml_content, current_version, resolved_target)
    
    def _resolve_version(self, version_str: str) -> str:
        """解析版本号或别名为标准版本号"""
        # 如果是别名，转换为对应版本号
        if version_str in self.version_aliases:
            return self.version_aliases[version_str]
        
        # 否则直接返回输入版本号
        return version_str
    
    def _extract_version(self, xml_content: str) -> str:
        """从XML内容中提取版本号"""
        # 尝试从project标签中匹配版本号
        project_match = re.search(r'<project[^>]*version=["\']([\d\.]+)["\']', xml_content)
        if project_match:
            return project_match.group(1)
            
        # 尝试从fcpxml标签中匹配版本号
        fcpxml_match = re.search(r'<fcpxml[^>]*version=["\']([\d\.]+)["\']', xml_content)
        if fcpxml_match:
            return fcpxml_match.group(1)
            
        # 尝试从xmeml标签中匹配版本号
        xmeml_match = re.search(r'<xmeml[^>]*version=["\']([\d\.]+)["\']', xml_content)
        if xmeml_match:
            return xmeml_match.group(1)
        
        # 如果没有找到版本信息，使用默认最新版本
        self.logger.warning("XML内容中未找到版本信息，假设为最新版本")
        return self.latest_version
    
    def _check_version_compatibility(self, source_version: str, target_version: str) -> None:
        """
        检查版本兼容性
        
        Args:
            source_version: 源版本号
            target_version: 目标版本号
            
        Raises:
            ValueError: 如果版本不兼容
        """
        # 检查目标版本是否在支持范围内
        if version.parse(target_version) < version.parse(self.minimum_version):
            raise ValueError(f"不支持的目标版本: {target_version}。最低支持版本: {self.minimum_version}")
        
        # 对于特殊版本对，可能需要特殊处理
        if source_version == "3.0" and target_version == "2.0":
            self.logger.warning("从3.0降级到2.0可能导致高级功能丢失")
    
    def _downgrade_version(self, xml_content: str, source_version: str, target_version: str) -> str:
        """
        降级XML版本
        
        Args:
            xml_content: 原始XML内容
            source_version: 源版本号
            target_version: 目标版本号
            
        Returns:
            降级后的XML内容
        """
        self.logger.info(f"将XML从版本 {source_version} 降级为 {target_version}")
        
        # 首先替换所有版本号
        modified_content = xml_content
        
        # 替换project标签中的版本
        modified_content = re.sub(r'(<project[^>]*version=)["\'][\d\.]+["\']', 
                               f'\\1"{target_version}"', modified_content)
        
        # 替换fcpxml标签中的版本
        modified_content = re.sub(r'(<fcpxml[^>]*version=)["\'][\d\.]+["\']', 
                               f'\\1"{target_version}"', modified_content)
        
        # 替换xmeml标签中的版本
        modified_content = re.sub(r'(<xmeml[^>]*version=)["\'][\d\.]+["\']', 
                               f'\\1"{target_version}"', modified_content)
        
        # 获取源版本和目标版本的功能集
        source_features = self.version_features.get(source_version, [])
        target_features = self.version_features.get(target_version, [])
        
        # 计算需要移除的功能
        features_to_remove = [f for f in source_features if f not in target_features]
        
        # 如果是从高版本到2.9，需要特殊处理效果
        if target_version == "2.9" and "高级效果" not in features_to_remove and "效果层" in source_features:
            # 确保高级效果处理被执行
            features_to_remove.append("高级效果")
        
        # 针对每个需要移除的功能进行特定处理
        for feature in features_to_remove:
            modified_content = self._remove_feature(modified_content, feature, target_version)
        
        # 特殊情况：2.9版本只支持transition效果，需要直接处理效果层
        if target_version == "2.9" and "效果层" in target_features:
            # 尝试使用ET解析处理
            try:
                # 使用正则提取效果层
                effects_pattern = r'(<effects>.*?</effects>)'
                effects_match = re.search(effects_pattern, modified_content, re.DOTALL)
                
                if effects_match:
                    effects_content = effects_match.group(1)
                    
                    # 只保留transition效果
                    new_effects = "<effects>\n"
                    transition_pattern = r'<effect\s+[^>]*?type=(["\'])transition\1[^>]*>.*?</effect>'
                    transitions = re.findall(transition_pattern, effects_content, re.DOTALL)
                    
                    # 如果有transition效果，保留它们
                    if transitions:
                        for trans in transitions:
                            new_effects += "    " + trans + "\n"
                    
                    new_effects += "  </effects>"
                    
                    # 替换原始效果层
                    modified_content = re.sub(effects_pattern, new_effects, modified_content, flags=re.DOTALL)
                    
                # 直接处理效果标签
                # 移除所有非transition效果
                modified_content = re.sub(
                    r'<effect\s+[^>]*?type=(["\'])(?!transition\1)[^"\']+\1[^>]*>.*?</effect>\s*',
                    '',
                    modified_content,
                    flags=re.DOTALL
                )
                
            except Exception as e:
                # 解析失败，使用简单的替换方法
                self.logger.warning(f"使用ET解析失败，回退到正则替换: {e}")
                
                # 移除blur效果
                modified_content = re.sub(
                    r'<effect\s+[^>]*?type=(["\'])blur\1[^>]*>.*?</effect>\s*',
                    '',
                    modified_content,
                    flags=re.DOTALL
                )
                # 移除color效果
                modified_content = re.sub(
                    r'<effect\s+[^>]*?type=(["\'])color\1[^>]*>.*?</effect>\s*',
                    '',
                    modified_content,
                    flags=re.DOTALL
                )
                # 移除transform效果
                modified_content = re.sub(
                    r'<effect\s+[^>]*?type=(["\'])transform\1[^>]*>.*?</effect>\s*',
                    '',
                    modified_content,
                    flags=re.DOTALL
                )
                # 移除text效果
                modified_content = re.sub(
                    r'<effect\s+[^>]*?type=(["\'])text\1[^>]*>.*?</effect>\s*',
                    '',
                    modified_content,
                    flags=re.DOTALL
                )
                # 移除audio效果
                modified_content = re.sub(
                    r'<effect\s+[^>]*?type=(["\'])audio\1[^>]*>.*?</effect>\s*',
                    '',
                    modified_content,
                    flags=re.DOTALL
                )
                
        # 清理可能出现的空效果层
        modified_content = re.sub(
            r'<effects>\s*</effects>',
            '<effects>\n  </effects>',
            modified_content
        )
        
        return modified_content
    
    def _upgrade_version(self, xml_content: str, source_version: str, target_version: str) -> str:
        """
        升级XML版本
        
        Args:
            xml_content: 原始XML内容
            source_version: 源版本号
            target_version: 目标版本号
            
        Returns:
            升级后的XML内容
        """
        self.logger.info(f"将XML从版本 {source_version} 升级为 {target_version}")
        
        # 首先替换所有版本号
        modified_content = xml_content
        
        # 替换project标签中的版本
        modified_content = re.sub(r'(<project[^>]*version=)["\'][\d\.]+["\']', 
                               f'\\1"{target_version}"', modified_content)
        
        # 替换fcpxml标签中的版本
        modified_content = re.sub(r'(<fcpxml[^>]*version=)["\'][\d\.]+["\']', 
                               f'\\1"{target_version}"', modified_content)
        
        # 替换xmeml标签中的版本
        modified_content = re.sub(r'(<xmeml[^>]*version=)["\'][\d\.]+["\']', 
                               f'\\1"{target_version}"', modified_content)
        
        # 获取源版本和目标版本的功能集
        source_features = self.version_features.get(source_version, [])
        target_features = self.version_features.get(target_version, [])
        
        # 计算需要添加的功能
        features_to_add = [f for f in target_features if f not in source_features]
        
        # 针对每个需要添加的功能进行特定处理
        for feature in features_to_add:
            modified_content = self._add_feature(modified_content, feature)
        
        return modified_content
    
    def _remove_feature(self, xml_content: str, feature: str, target_version: str = None) -> str:
        """
        移除特定功能的相关XML内容
        
        Args:
            xml_content: 原始XML内容
            feature: 要移除的功能
            target_version: 目标版本，某些功能需要根据目标版本进行特殊处理
            
        Returns:
            处理后的XML内容
        """
        modified_content = xml_content
        
        if feature == "多轨道" and "单轨道" in self.version_features.get("2.0", []):
            # 保留主轨道，移除其他轨道
            # 使用负向前瞻，确保不匹配main_video_track
            modified_content = re.sub(
                r'<track\s+[^>]*?id=(["\'])(?!main_video_track\1)[^"\']+\1[^>]*?>.*?</track>\s*', 
                '', 
                modified_content, 
                flags=re.DOTALL
            )
            # 移除字幕轨
            modified_content = re.sub(
                r'<subtitle_track>.*?</subtitle_track>\s*', 
                '', 
                modified_content, 
                flags=re.DOTALL
            )
        
        elif feature == "效果层":
            # 如果目标版本不支持效果层，完全移除
            if not target_version or target_version in ["2.0", "2.5"]:
                # 移除整个效果层
                modified_content = re.sub(
                    r'<effects>.*?</effects>\s*', 
                    '', 
                    modified_content, 
                    flags=re.DOTALL
                )
        
        elif feature == "高级效果" and target_version == "2.9":
            # 2.9版本只需要保留transition效果
            # 移除不支持的效果，在downgrade方法中专门处理
            pass
        
        elif feature == "字幕轨":
            # 移除字幕轨相关内容
            modified_content = re.sub(
                r'<subtitle_track>.*?</subtitle_track>\s*', 
                '', 
                modified_content, 
                flags=re.DOTALL
            )
        
        elif feature == "音频特效":
            # 移除音频特效相关内容
            modified_content = re.sub(
                r'<audio_effect[^>]*>.*?</audio_effect>\s*', 
                '', 
                modified_content, 
                flags=re.DOTALL
            )
            # 还要移除效果层中的音频特效
            modified_content = re.sub(
                r'<effect[^>]*?type=(["\'])audio[^"\']*\1[^>]*>.*?</effect>\s*', 
                '', 
                modified_content, 
                flags=re.DOTALL
            )
        
        elif feature == "嵌套序列":
            # 将嵌套序列展开为普通片段
            modified_content = self._flatten_nested_sequences(modified_content)
        
        return modified_content
    
    def _add_feature(self, xml_content: str, feature: str) -> str:
        """
        添加特定功能的相关XML内容
        
        Args:
            xml_content: 原始XML内容
            feature: 要添加的功能
            
        Returns:
            处理后的XML内容
        """
        modified_content = xml_content
        
        if feature == "多轨道":
            # 如果只有单轨道，添加空的辅助轨道
            if "<tracks>" in modified_content and not re.search(r'<track[^>]*id=(["\'])aux_video_track\1', modified_content):
                modified_content = modified_content.replace("</tracks>", '''  <track id="aux_video_track">
    <segments/>
  </track>
</tracks>''')
        
        elif feature == "字幕轨":
            # 添加空的字幕轨
            if "<tracks>" in modified_content and not "<subtitle_track>" in modified_content:
                modified_content = modified_content.replace("</tracks>", '''  <subtitle_track>
    <segments/>
  </subtitle_track>
</tracks>''')
        
        elif feature == "效果层":
            # 添加空的效果层
            if "</project>" in modified_content and not "<effects>" in modified_content:
                modified_content = modified_content.replace("</project>", '''  <effects>
  </effects>
</project>''')
        
        return modified_content
    
    def _flatten_nested_sequences(self, xml_content: str) -> str:
        """
        展开嵌套序列为普通片段
        
        Args:
            xml_content: 原始XML内容
            
        Returns:
            处理后的XML内容
        """
        # 实际实现中需要解析XML，识别嵌套序列并展开
        # 这里提供简化实现，使用正则替换
        pattern = r'<nested_sequence[^>]*id=(["\'])([^"\']+)\1[^>]*>.*?</nested_sequence>'
        
        def replace_nested(match):
            seq_id = match.group(2)
            return f'<clip id="{seq_id}" is_flattened="true"></clip>'
        
        return re.sub(pattern, replace_nested, xml_content, flags=re.DOTALL)
    
    def get_supported_versions(self) -> List[str]:
        """
        获取支持的所有版本
        
        Returns:
            支持的版本列表
        """
        return list(self.version_features.keys())
    
    def get_version_aliases(self) -> Dict[str, str]:
        """
        获取版本别名映射
        
        Returns:
            版本别名映射
        """
        return self.version_aliases
    
    def get_version_features(self, version_str: str) -> List[str]:
        """
        获取特定版本支持的功能
        
        Args:
            version_str: 版本号或别名
            
        Returns:
            功能列表
        """
        resolved_version = self._resolve_version(version_str)
        return self.version_features.get(resolved_version, [])

# 创建单例实例
version_adapter = VersionAdapter()

def adapt_for_version(xml_content: str, target_version: str) -> str:
    """
    根据目标版本调整XML结构
    
    Args:
        xml_content: 原始XML内容
        target_version: 目标版本号或别名
        
    Returns:
        适配后的XML内容
    """
    return version_adapter.adapt_for_version(xml_content, target_version)

def get_supported_versions() -> List[str]:
    """
    获取支持的所有版本
    
    Returns:
        支持的版本列表
    """
    return version_adapter.get_supported_versions()

def get_version_aliases() -> Dict[str, str]:
    """
    获取版本别名映射
    
    Returns:
        版本别名映射
    """
    return version_adapter.get_version_aliases()

def get_version_features(version_str: str) -> List[str]:
    """
    获取特定版本支持的功能
    
    Args:
        version_str: 版本号或别名
        
    Returns:
        功能列表
    """
    return version_adapter.get_version_features(version_str) 