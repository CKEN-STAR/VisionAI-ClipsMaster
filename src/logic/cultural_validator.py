#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文化语境验证器

此模块提供用于验证视频场景中文化上下文的一致性的工具。主要功能包括：
1. 时代文化一致性检查 - 确保场景中的服饰、道具、语言等符合特定历史时期
2. 文化禁忌检测 - 识别特定文化环境中不适宜的元素
3. 跨文化适配性分析 - 评估内容在不同文化背景下的适应性
4. 文化刻板印象检测 - 识别和提示可能的文化刻板印象
5. 历史准确性验证 - 验证历史场景中的文化元素是否符合史实
"""

from typing import Dict, List, Set, Tuple, Any, Optional, Union
from enum import Enum, auto
import re
import logging
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    logging.warning("无法导入完整的异常处理模块，将使用基础异常类")
    
    class ErrorCode:
        CULTURAL_ERROR = 1700
    
    class ClipMasterError(Exception):
        def __init__(self, message, code=None, details=None):
            self.message = message
            self.code = code
            self.details = details or {}
            super().__init__(message)

# 配置日志
logger = logging.getLogger(__name__)


class CulturalErrorType(Enum):
    """文化错误类型"""
    ANACHRONISM = auto()         # 时代错误：不符合特定历史时期
    CULTURAL_MIXING = auto()     # 文化混杂：不同文化元素不当混合
    TABOO_VIOLATION = auto()     # 禁忌违反：触犯特定文化禁忌
    STEREOTYPE = auto()          # 刻板印象：强化文化刻板印象
    HISTORICAL_INACCURACY = auto() # 历史不准确：与史实不符
    CULTURAL_APPROPRIATION = auto() # 文化挪用：不当使用他文化元素


class CulturalEra(Enum):
    """历史文化时代"""
    PREHISTORIC = "史前时代"            # 史前时代 (10万年前-公元前3000年)
    ANCIENT = "古代"                    # 古代 (公元前3000年-公元476年)
    MEDIEVAL = "中世纪"                 # 中世纪 (476年-1453年)
    RENAISSANCE = "文艺复兴"            # 文艺复兴 (1350年-1600年)
    EARLY_MODERN = "早期现代"           # 早期现代 (1600年-1760年)
    INDUSTRIAL = "工业时代"             # 工业时代 (1760年-1914年)
    MODERN = "现代"                     # 现代 (1914年-2000年)
    CONTEMPORARY = "当代"               # 当代 (2000年至今)
    
    # 中国历史时期
    ANCIENT_CHINA = "中国古代"          # 中国古代 (夏商周-秦汉)
    IMPERIAL_CHINA = "中国帝制时期"      # 中国帝制时期 (秦汉-清朝)
    REPUBLICAN_CHINA = "民国时期"        # 民国时期 (1912年-1949年)
    MODERN_CHINA = "中国现代"            # 中国现代 (1949年至今)
    
    # 特定时代
    VICTORIAN = "维多利亚时代"           # 维多利亚时代 (1837年-1901年)
    ROARING_TWENTIES = "咆哮的二十年代"   # 咆哮的二十年代 (1920年-1929年)
    POST_WAR = "战后时期"                # 战后时期 (1945年-1970年)
    DIGITAL_AGE = "数字时代"             # 数字时代 (1990年至今)
    
    @classmethod
    def get_by_year(cls, year: int) -> 'CulturalEra':
        """根据年份获取对应的时代
        
        Args:
            year: 年份，可以是负数（表示公元前）
            
        Returns:
            对应的时代枚举值
        """
        if year < -3000:
            return cls.PREHISTORIC
        elif -3000 <= year < 476:
            return cls.ANCIENT
        elif 476 <= year < 1453:
            return cls.MEDIEVAL
        elif 1350 <= year < 1600:
            return cls.RENAISSANCE
        elif 1600 <= year < 1760:
            return cls.EARLY_MODERN
        elif 1760 <= year < 1914:
            return cls.INDUSTRIAL
        elif 1914 <= year < 2000:
            return cls.MODERN
        else:
            return cls.CONTEMPORARY


class CulturalRegion(Enum):
    """文化区域"""
    EAST_ASIA = "东亚"           # 中国、日本、韩国等
    SOUTH_ASIA = "南亚"          # 印度、巴基斯坦等
    SOUTHEAST_ASIA = "东南亚"    # 泰国、越南、印尼等
    MIDDLE_EAST = "中东"         # 沙特、伊朗、土耳其等
    AFRICA = "非洲"              # 埃及、尼日利亚、肯尼亚等
    EUROPE = "欧洲"              # 英国、法国、德国等
    NORTH_AMERICA = "北美"       # 美国、加拿大
    LATIN_AMERICA = "拉丁美洲"   # 墨西哥、巴西、阿根廷等
    OCEANIA = "大洋洲"           # 澳大利亚、新西兰等
    
    # 特定文化区域
    CHINA = "中国"
    JAPAN = "日本"
    KOREA = "韩国"
    INDIA = "印度"
    MIDDLE_EAST_ISLAMIC = "伊斯兰中东"
    WESTERN_EUROPE = "西欧"
    EASTERN_EUROPE = "东欧"
    NORTH_AMERICA_US = "美国"
    

class CulturalError(ClipMasterError):
    """文化错误异常
    
    当检测到文化上下文错误时抛出。
    """
    
    def __init__(self, message: str, error_type: CulturalErrorType, 
                 details: Optional[Dict[str, Any]] = None):
        """初始化文化错误异常
        
        Args:
            message: 错误信息
            error_type: 错误类型
            details: 详细信息，包含错误的具体描述
        """
        super().__init__(
            message,
            code=ErrorCode.CULTURAL_ERROR,
            details=details or {"error_type": error_type.name}
        )
        self.error_type = error_type


@dataclass
class CulturalRule:
    """文化规则
    
    定义特定文化上下文中的验证规则。
    """
    id: str                                # 规则ID
    name: str                              # 规则名称
    description: str                       # 规则描述
    era: Optional[CulturalEra] = None      # 适用时代
    region: Optional[CulturalRegion] = None # 适用区域
    keywords: Set[str] = field(default_factory=set)  # 关键词
    forbidden_elements: Set[str] = field(default_factory=set)  # 禁止元素
    required_elements: Set[str] = field(default_factory=set)   # 必需元素
    error_type: CulturalErrorType = CulturalErrorType.ANACHRONISM  # 错误类型
    
    def check(self, scene: Dict[str, Any]) -> Optional[str]:
        """检查场景是否违反此规则
        
        Args:
            scene: 场景数据
            
        Returns:
            如果违反规则，返回错误描述；否则返回None
        """
        # 检查是否适用于此场景
        if not self._is_applicable(scene):
            return None
            
        # 检查禁止元素
        forbidden = self._check_forbidden_elements(scene)
        if forbidden:
            return f"场景包含不符合{self.era.value if self.era else ''}文化背景的元素: {forbidden}"
            
        # 检查必需元素
        missing = self._check_required_elements(scene)
        if missing and self.required_elements:
            return f"场景缺少符合{self.era.value if self.era else ''}文化背景的必要元素: {missing}"
            
        return None
    
    def _is_applicable(self, scene: Dict[str, Any]) -> bool:
        """检查规则是否适用于此场景
        
        Args:
            scene: 场景数据
            
        Returns:
            是否适用
        """
        # 检查时代匹配
        if self.era and "era" in scene:
            # 如果场景指定了时代，检查是否匹配
            return scene["era"] == self.era.value or scene.get("era") == self.era.name
        
        # 检查区域匹配
        if self.region and "region" in scene:
            return scene["region"] == self.region.value or scene.get("region") == self.region.name
            
        # 如果没有指定时代和区域，检查关键词
        if self.keywords:
            # 检查场景描述、对话等是否包含关键词
            scene_text = " ".join([
                str(scene.get("description", "")),
                str(scene.get("dialogue", "")),
                " ".join(str(prop) for prop in scene.get("props", []))
            ])
            
            return any(keyword in scene_text for keyword in self.keywords)
            
        # 默认不适用
        return False
    
    def _check_forbidden_elements(self, scene: Dict[str, Any]) -> List[str]:
        """检查场景中是否包含禁止元素
        
        Args:
            scene: 场景数据
            
        Returns:
            包含的禁止元素列表
        """
        found_elements = []
        
        # 检查道具
        props = scene.get("props", [])
        if isinstance(props, list):
            for prop in props:
                if isinstance(prop, str) and any(elem in prop for elem in self.forbidden_elements):
                    found_elements.append(prop)
                elif isinstance(prop, dict) and "name" in prop:
                    if any(elem in prop["name"] for elem in self.forbidden_elements):
                        found_elements.append(prop["name"])
        
        # 检查服装
        costumes = scene.get("costumes", [])
        if isinstance(costumes, list):
            for costume in costumes:
                if isinstance(costume, str) and any(elem in costume for elem in self.forbidden_elements):
                    found_elements.append(costume)
                elif isinstance(costume, dict) and "name" in costume:
                    if any(elem in costume["name"] for elem in self.forbidden_elements):
                        found_elements.append(costume["name"])
        
        # 检查场景描述
        description = scene.get("description", "")
        if description:
            for elem in self.forbidden_elements:
                if elem in description:
                    found_elements.append(elem)
        
        return found_elements
    
    def _check_required_elements(self, scene: Dict[str, Any]) -> List[str]:
        """检查场景中是否缺少必需元素
        
        Args:
            scene: 场景数据
            
        Returns:
            缺少的必需元素列表
        """
        missing_elements = list(self.required_elements)
        
        # 检查场景中的所有文本内容
        scene_text = " ".join([
            str(scene.get("description", "")),
            str(scene.get("dialogue", "")),
            " ".join(str(prop) for prop in scene.get("props", [])),
            " ".join(str(costume) for costume in scene.get("costumes", []))
        ])
        
        # 移除已找到的元素
        for elem in list(missing_elements):
            if elem in scene_text:
                missing_elements.remove(elem)
        
        return missing_elements


class CulturalRuleDatabase:
    """文化规则数据库
    
    管理和加载文化验证规则。
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """初始化文化规则数据库
        
        Args:
            rules_path: 规则文件路径，默认为None时使用内置规则
        """
        self.rules: List[CulturalRule] = []
        self._load_rules(rules_path)
    
    def _load_rules(self, rules_path: Optional[str]) -> None:
        """加载规则
        
        Args:
            rules_path: 规则文件路径
        """
        # 首先加载内置规则
        self._load_builtin_rules()
        
        # 如果提供了外部规则路径，尝试加载
        if rules_path:
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                for rule_data in rules_data:
                    try:
                        # 解析时代和区域枚举
                        era = (CulturalEra[rule_data["era"]] 
                               if "era" in rule_data and rule_data["era"] 
                               else None)
                        
                        region = (CulturalRegion[rule_data["region"]] 
                                 if "region" in rule_data and rule_data["region"] 
                                 else None)
                        
                        error_type = (CulturalErrorType[rule_data["error_type"]] 
                                     if "error_type" in rule_data 
                                     else CulturalErrorType.ANACHRONISM)
                        
                        rule = CulturalRule(
                            id=rule_data["id"],
                            name=rule_data["name"],
                            description=rule_data["description"],
                            era=era,
                            region=region,
                            keywords=set(rule_data.get("keywords", [])),
                            forbidden_elements=set(rule_data.get("forbidden_elements", [])),
                            required_elements=set(rule_data.get("required_elements", [])),
                            error_type=error_type
                        )
                        
                        self.rules.append(rule)
                    except Exception as e:
                        logger.warning(f"解析规则时出错: {e}")
                
                logger.info(f"从{rules_path}加载了{len(rules_data)}条文化规则")
            except Exception as e:
                logger.warning(f"加载规则文件失败: {e}")
    
    def _load_builtin_rules(self) -> None:
        """加载内置规则"""
        # 内置一些基本规则
        
        # 中国古代与现代科技冲突
        self.rules.append(CulturalRule(
            id="ancient_china_tech",
            name="中国古代与现代科技冲突",
            description="检查中国古代场景中是否出现现代科技元素",
            era=CulturalEra.ANCIENT_CHINA,
            region=CulturalRegion.CHINA,
            keywords={"古代", "古代中国", "古装", "朝代", "皇帝", "官员", "宫廷"},
            forbidden_elements={"手机", "电脑", "电视", "汽车", "飞机", "电灯", "电", "塑料", "尼龙"},
            error_type=CulturalErrorType.ANACHRONISM
        ))
        
        # 中世纪欧洲与现代物品冲突
        self.rules.append(CulturalRule(
            id="medieval_europe_modern",
            name="中世纪欧洲与现代物品冲突",
            description="检查中世纪欧洲场景中是否出现现代物品",
            era=CulturalEra.MEDIEVAL,
            region=CulturalRegion.EUROPE,
            keywords={"中世纪", "骑士", "城堡", "领主", "农奴", "教会"},
            forbidden_elements={"手表", "眼镜", "打火机", "香烟", "塑料", "铝", "皮夹克"},
            error_type=CulturalErrorType.ANACHRONISM
        ))
        
        # 维多利亚时代服饰要求
        self.rules.append(CulturalRule(
            id="victorian_costume",
            name="维多利亚时代服饰要求",
            description="检查维多利亚时代场景中的服饰是否符合时代特征",
            era=CulturalEra.VICTORIAN,
            region=CulturalRegion.WESTERN_EUROPE,
            keywords={"维多利亚", "英国", "19世纪", "工业革命"},
            required_elements={"长裙", "礼帽", "手套", "燕尾服", "马甲", "高领"},
            forbidden_elements={"牛仔裤", "T恤", "运动鞋", "短裙", "比基尼"},
            error_type=CulturalErrorType.ANACHRONISM
        ))
        
        # 伊斯兰文化禁忌
        self.rules.append(CulturalRule(
            id="islamic_taboos",
            name="伊斯兰文化禁忌",
            description="检查伊斯兰文化场景中是否出现文化禁忌",
            region=CulturalRegion.MIDDLE_EAST_ISLAMIC,
            keywords={"伊斯兰", "穆斯林", "清真寺", "古兰经"},
            forbidden_elements={"猪肉", "酒精", "赌博", "暴露服装"},
            error_type=CulturalErrorType.TABOO_VIOLATION
        ))
        
        # 现代与古代服饰混搭
        self.rules.append(CulturalRule(
            id="costume_mixing",
            name="服饰时代混搭",
            description="检查是否存在不同时代服饰的不当混搭",
            keywords={"服饰", "装扮", "着装", "打扮"},
            forbidden_elements={"西装配汉服", "牛仔裤配长袍", "西装配草鞋"},
            error_type=CulturalErrorType.CULTURAL_MIXING
        ))
        
        logger.info(f"加载了{len(self.rules)}条内置文化规则")
    
    def get_applicable_rules(self, scene: Dict[str, Any]) -> List[CulturalRule]:
        """获取适用于特定场景的规则
        
        Args:
            scene: 场景数据
            
        Returns:
            适用的规则列表
        """
        return [rule for rule in self.rules if rule._is_applicable(scene)]
    
    def get_rules_by_era(self, era: CulturalEra) -> List[CulturalRule]:
        """获取适用于特定时代的规则
        
        Args:
            era: 时代
            
        Returns:
            规则列表
        """
        return [rule for rule in self.rules if rule.era == era]
    
    def get_rules_by_region(self, region: CulturalRegion) -> List[CulturalRule]:
        """获取适用于特定区域的规则
        
        Args:
            region: 区域
            
        Returns:
            规则列表
        """
        return [rule for rule in self.rules if rule.region == region]


class CulturalContextChecker:
    """文化上下文检查器
    
    验证场景中的文化元素是否符合特定时代和文化背景。
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """初始化文化上下文检查器
        
        Args:
            rules_path: 规则文件路径，默认为None时使用内置规则
        """
        self.cultural_rules = CulturalRuleDatabase(rules_path)
    
    def validate_context(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证文化元素的准确性
        
        检查场景中的文化元素是否符合特定时代和文化背景。
        
        Args:
            scene: 场景数据，包括时代、区域、道具、服装等信息
            
        Returns:
            如果存在文化错误，返回错误描述；否则返回None
        """
        # 获取适用于此场景的规则
        applicable_rules = self.cultural_rules.get_applicable_rules(scene)
        
        # 检查每条规则
        for rule in applicable_rules:
            error = rule.check(scene)
            if error:
                return error
        
        return None
    
    def get_cultural_suggestions(self, scene: Dict[str, Any]) -> List[str]:
        """获取文化适配建议
        
        为场景提供文化元素的改进建议。
        
        Args:
            scene: 场景数据
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 确定场景的时代和区域
        era = None
        if "era" in scene:
            try:
                # 尝试将字符串转换为枚举
                era = next((e for e in CulturalEra if e.value == scene["era"] or e.name == scene["era"]), None)
            except:
                pass
        
        # 如果能确定时代，提供相关建议
        if era:
            # 获取该时代的规则
            era_rules = self.cultural_rules.get_rules_by_era(era)
            
            # 从规则中提取建议
            for rule in era_rules:
                if rule.required_elements:
                    elements_str = "、".join(rule.required_elements)
                    suggestions.append(f"建议在{era.value}场景中加入: {elements_str}")
                
                if rule.forbidden_elements:
                    elements_str = "、".join(rule.forbidden_elements)
                    suggestions.append(f"建议在{era.value}场景中避免出现: {elements_str}")
        
        return suggestions
    
    def analyze_cultural_accuracy(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """分析场景的文化准确性
        
        提供详细的文化准确性分析报告。
        
        Args:
            scene: 场景数据
            
        Returns:
            分析报告
        """
        # 获取适用于此场景的规则
        applicable_rules = self.cultural_rules.get_applicable_rules(scene)
        
        # 初始化结果
        result = {
            "is_accurate": True,
            "errors": [],
            "warnings": [],
            "suggestions": self.get_cultural_suggestions(scene),
            "applicable_rules": [rule.name for rule in applicable_rules]
        }
        
        # 检查每条规则
        for rule in applicable_rules:
            error = rule.check(scene)
            if error:
                result["is_accurate"] = False
                result["errors"].append({
                    "rule": rule.name,
                    "description": error,
                    "type": rule.error_type.name
                })
        
        # 添加警告
        # 例如：检查可能构成刻板印象的元素
        stereotype_keywords = {
            "东方神秘主义", "东方主义", "刻板印象", "种族歧视", 
            "性别刻板", "文化挪用", "文化误用"
        }
        
        scene_text = " ".join([
            str(scene.get("description", "")),
            str(scene.get("dialogue", "")),
            " ".join(str(prop) for prop in scene.get("props", []))
        ])
        
        for keyword in stereotype_keywords:
            if keyword in scene_text:
                result["warnings"].append({
                    "type": CulturalErrorType.STEREOTYPE.name,
                    "description": f"场景中可能包含文化刻板印象: '{keyword}'"
                })
        
        return result


def validate_cultural_context(scene: Dict[str, Any]) -> Dict[str, Any]:
    """验证场景的文化上下文
    
    便捷函数，用于验证场景中的文化元素是否符合特定时代和文化背景。
    
    Args:
        scene: 场景数据，包括时代、区域、道具、服装等信息
        
    Returns:
        验证结果
    """
    checker = CulturalContextChecker()
    return checker.analyze_cultural_accuracy(scene) 