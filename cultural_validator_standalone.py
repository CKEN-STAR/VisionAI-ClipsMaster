#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文化语境验证器独立测试脚本

提供文化语境验证器的独立测试功能，无需依赖完整项目。
"""

import sys
import os
import logging
from pathlib import Path
import json
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from dataclasses import dataclass, field

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===========================================
# 简化的模型代码，用于独立运行
# ===========================================

class ErrorCode:
    CULTURAL_ERROR = 1700


class ClipMasterError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


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
        """根据年份获取对应的时代"""
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
    """文化错误异常"""
    def __init__(self, message: str, error_type: CulturalErrorType, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=ErrorCode.CULTURAL_ERROR, 
                        details=details or {"error_type": error_type.name})
        self.error_type = error_type


@dataclass
class CulturalRule:
    """文化规则"""
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
        """检查场景是否违反此规则"""
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
        """检查规则是否适用于此场景"""
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
        """检查场景中是否包含禁止元素"""
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
        """检查场景中是否缺少必需元素"""
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
    """文化规则数据库"""
    def __init__(self, rules_path: Optional[str] = None):
        self.rules: List[CulturalRule] = []
        self._load_rules(rules_path)
    
    def _load_rules(self, rules_path: Optional[str]) -> None:
        """加载规则"""
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
        """获取适用于特定场景的规则"""
        return [rule for rule in self.rules if rule._is_applicable(scene)]
    
    def get_rules_by_era(self, era: CulturalEra) -> List[CulturalRule]:
        """获取适用于特定时代的规则"""
        return [rule for rule in self.rules if rule.era == era]
    
    def get_rules_by_region(self, region: CulturalRegion) -> List[CulturalRule]:
        """获取适用于特定区域的规则"""
        return [rule for rule in self.rules if rule.region == region]


class CulturalContextChecker:
    """文化上下文检查器"""
    def __init__(self, rules_path: Optional[str] = None):
        self.cultural_rules = CulturalRuleDatabase(rules_path)
    
    def validate_context(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证文化元素的准确性"""
        # 获取适用于此场景的规则
        applicable_rules = self.cultural_rules.get_applicable_rules(scene)
        
        # 检查每条规则
        for rule in applicable_rules:
            error = rule.check(scene)
            if error:
                return error
        
        return None
    
    def get_cultural_suggestions(self, scene: Dict[str, Any]) -> List[str]:
        """获取文化适配建议"""
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
        """分析场景的文化准确性"""
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
    """验证场景的文化上下文"""
    checker = CulturalContextChecker()
    return checker.analyze_cultural_accuracy(scene)


# ===========================================
# 测试数据和测试函数
# ===========================================

def create_test_data():
    """创建测试数据"""
    # 创建测试场景
    ancient_china_scene = {
        "era": "中国古代",
        "region": "中国",
        "description": "一个古代中国的宫廷场景，皇帝坐在龙椅上接见大臣。",
        "props": ["龙椅", "朝服", "玉玺", "手机"],  # 手机是错误的
        "costumes": ["朝服", "官帽", "布鞋"],
        "characters": ["皇帝", "大臣", "侍女"]
    }
    
    victorian_scene = {
        "era": "维多利亚时代",
        "region": "西欧",
        "description": "19世纪末的英国贵族沙龙，人们正在社交。",
        "props": ["茶具", "书籍", "蜡烛", "手表"],
        "costumes": ["长裙", "燕尾服", "牛仔裤"],  # 牛仔裤是错误的
        "characters": ["男爵", "女伯爵", "管家"]
    }
    
    modern_scene = {
        "era": "当代",
        "region": "北美",
        "description": "现代办公室，人们正在工作。",
        "props": ["电脑", "手机", "咖啡杯", "文件夹"],
        "costumes": ["西装", "衬衫", "牛仔裤", "运动鞋"],
        "characters": ["经理", "职员", "实习生"]
    }
    
    mixed_culture_scene = {
        "description": "一个混合了东西方元素的场景，人物穿着各种不同风格的服饰。",
        "props": ["筷子", "叉子", "茶杯", "咖啡杯"],
        "costumes": ["西装配汉服", "牛仔裤配长袍"],
        "characters": ["混搭爱好者"]
    }
    
    islamic_scene = {
        "region": "伊斯兰中东",
        "description": "在清真寺附近的餐厅，人们正在享用猪肉和酒精饮料。",
        "props": ["古兰经", "酒瓶", "猪肉菜肴"],
        "costumes": ["传统长袍", "头巾"],
        "characters": ["伊玛目", "游客"]
    }
    
    return {
        "ancient_china": ancient_china_scene,
        "victorian": victorian_scene,
        "modern": modern_scene,
        "mixed_culture": mixed_culture_scene,
        "islamic": islamic_scene
    }


def test_cultural_validator():
    """测试文化语境验证器"""
    print("\n===== 测试文化语境验证器 =====")
    
    # 获取测试数据
    test_data = create_test_data()
    
    for name, scene in test_data.items():
        print(f"\n--- 测试场景: {name} ---")
        print(f"描述: {scene.get('description', '')}")
        print(f"时代: {scene.get('era', '未指定')}")
        print(f"区域: {scene.get('region', '未指定')}")
        
        if "props" in scene:
            print(f"道具: {', '.join(scene['props'])}")
        if "costumes" in scene:
            print(f"服装: {', '.join(scene['costumes'])}")
        
        # 验证场景
        result = validate_cultural_context(scene)
        
        print(f"\n验证结果: {'通过' if result['is_accurate'] else '失败'}")
        
        if not result['is_accurate']:
            print("\n检测到的问题:")
            for i, error in enumerate(result['errors'], 1):
                print(f"  {i}. [{error['type']}] {error['description']}")
        
        if result['warnings']:
            print("\n警告:")
            for i, warning in enumerate(result['warnings'], 1):
                print(f"  {i}. [{warning['type']}] {warning['description']}")
        
        if result['suggestions']:
            print("\n建议:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
        print(f"\n适用的规则: {', '.join(result['applicable_rules'])}")
        print("\n" + "-" * 50)


def test_custom_rule():
    """测试自定义规则"""
    print("\n===== 测试自定义规则 =====")
    
    # 创建自定义规则
    custom_rule = CulturalRule(
        id="test_rule",
        name="测试规则",
        description="测试用规则",
        keywords={"测试"},
        forbidden_elements={"禁止元素"}
    )
    
    # 创建测试场景
    test_scene = {
        "description": "这是一个测试场景，包含一些元素。",
        "props": ["测试道具", "禁止元素"]
    }
    
    # 检查规则
    print(f"规则: {custom_rule.name}")
    print(f"场景描述: {test_scene['description']}")
    print(f"场景道具: {', '.join(test_scene['props'])}")
    
    error = custom_rule.check(test_scene)
    
    if error:
        print(f"\n检测到问题: {error}")
    else:
        print("\n未检测到问题")


def main():
    """主函数"""
    print("===== 文化语境验证器独立测试 =====")
    
    try:
        # 测试文化语境验证器
        test_cultural_validator()
        
        # 测试自定义规则
        test_custom_rule()
        
        print("\n所有测试完成!")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 