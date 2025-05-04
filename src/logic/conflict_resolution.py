#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
冲突解决校验模块

此模块提供用于检验视频中冲突解决方案合理性的工具。主要功能包括：
1. 冲突解决方式分析 - 评估不同冲突解决方法的适当性
2. 冲突解决强度校验 - 确保解决方案的强度与冲突程度匹配
3. 冲突解决者能力验证 - 验证解决者是否具备解决特定冲突的能力
4. 冲突解决连贯性检查 - 分析整体冲突解决过程的逻辑连贯性
5. 冲突解决建议 - 提供更合适的冲突解决方案建议

通过分析冲突的性质、程度和相关方的特性，评估解决方案的适当性和有效性。
"""

import logging
import json
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from pathlib import Path

# 尝试导入项目内部模块
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    logging.warning("无法导入完整的异常处理模块，将使用基础异常类")
    
    class ErrorCode:
        VALIDATION_ERROR = 1005
        NARRATIVE_ANALYSIS_ERROR = 1405
    
    class ClipMasterError(Exception):
        def __init__(self, message, code=None, details=None):
            self.message = message
            self.code = code
            self.details = details or {}
            super().__init__(message)

# 配置日志
logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型枚举"""
    PHYSICAL = auto()     # 物理冲突（武力、打斗）
    VERBAL = auto()       # 言语冲突（争论、辩论）
    EMOTIONAL = auto()    # 情感冲突（情绪对抗）
    IDEOLOGICAL = auto()  # 意识形态冲突（信仰、价值观）
    RESOURCE = auto()     # 资源冲突（争夺资源）
    INTEREST = auto()     # 利益冲突（利益争夺）
    RELATIONAL = auto()   # 关系冲突（人际关系）
    INTERNAL = auto()     # 内心冲突（自我矛盾）
    
    @classmethod
    def from_string(cls, conflict_type: str) -> 'ConflictType':
        """从字符串获取冲突类型"""
        mapping = {
            "物理": cls.PHYSICAL,
            "physical": cls.PHYSICAL,
            "武力": cls.PHYSICAL,
            "打斗": cls.PHYSICAL,
            "fight": cls.PHYSICAL,
            
            "言语": cls.VERBAL,
            "verbal": cls.VERBAL,
            "争论": cls.VERBAL,
            "辩论": cls.VERBAL,
            "argument": cls.VERBAL,
            "debate": cls.VERBAL,
            
            "情感": cls.EMOTIONAL,
            "emotional": cls.EMOTIONAL,
            "情绪": cls.EMOTIONAL,
            "emotion": cls.EMOTIONAL,
            
            "意识形态": cls.IDEOLOGICAL,
            "ideological": cls.IDEOLOGICAL,
            "信仰": cls.IDEOLOGICAL,
            "价值观": cls.IDEOLOGICAL,
            "belief": cls.IDEOLOGICAL,
            "value": cls.IDEOLOGICAL,
            
            "资源": cls.RESOURCE,
            "resource": cls.RESOURCE,
            
            "利益": cls.INTEREST,
            "interest": cls.INTEREST,
            
            "关系": cls.RELATIONAL,
            "relational": cls.RELATIONAL,
            "relationship": cls.RELATIONAL,
            
            "内心": cls.INTERNAL,
            "internal": cls.INTERNAL,
            "自我": cls.INTERNAL,
            "inner": cls.INTERNAL
        }
        
        lower_type = conflict_type.lower()
        if lower_type in mapping:
            return mapping[lower_type]
        
        # 尝试部分匹配
        for key, value in mapping.items():
            if key in lower_type:
                return value
        
        return cls.VERBAL  # 默认为言语冲突


class ResolutionMethod(Enum):
    """冲突解决方法枚举"""
    FORCE = auto()        # 武力解决
    NEGOTIATION = auto()  # 谈判解决
    COMPROMISE = auto()   # 妥协解决
    AVOIDANCE = auto()    # 回避解决
    COLLABORATION = auto() # 合作解决
    MEDIATION = auto()    # 调解解决
    ARBITRATION = auto()  # 仲裁解决
    SURRENDER = auto()    # 投降/屈服
    SABOTAGE = auto()     # 破坏/阻挠

    @classmethod
    def from_string(cls, method: str) -> 'ResolutionMethod':
        """从字符串获取解决方法类型"""
        mapping = {
            "武力": cls.FORCE,
            "force": cls.FORCE,
            "暴力": cls.FORCE,
            "打斗": cls.FORCE,
            "physical": cls.FORCE,
            
            "谈判": cls.NEGOTIATION,
            "negotiation": cls.NEGOTIATION,
            "交涉": cls.NEGOTIATION,
            "协商": cls.NEGOTIATION,
            
            "妥协": cls.COMPROMISE,
            "compromise": cls.COMPROMISE,
            "让步": cls.COMPROMISE,
            "调和": cls.COMPROMISE,
            
            "回避": cls.AVOIDANCE,
            "avoidance": cls.AVOIDANCE,
            "逃避": cls.AVOIDANCE,
            "避免": cls.AVOIDANCE,
            
            "合作": cls.COLLABORATION,
            "collaboration": cls.COLLABORATION,
            "协作": cls.COLLABORATION,
            "共赢": cls.COLLABORATION,
            
            "调解": cls.MEDIATION,
            "mediation": cls.MEDIATION,
            "协调": cls.MEDIATION,
            
            "仲裁": cls.ARBITRATION,
            "arbitration": cls.ARBITRATION,
            "裁决": cls.ARBITRATION,
            "判决": cls.ARBITRATION,
            
            "投降": cls.SURRENDER,
            "surrender": cls.SURRENDER,
            "屈服": cls.SURRENDER,
            "让步": cls.SURRENDER,
            
            "破坏": cls.SABOTAGE,
            "sabotage": cls.SABOTAGE,
            "阻挠": cls.SABOTAGE,
            "妨碍": cls.SABOTAGE
        }
        
        lower_method = method.lower()
        if lower_method in mapping:
            return mapping[lower_method]
        
        # 尝试部分匹配
        for key, value in mapping.items():
            if key in lower_method:
                return value
        
        return cls.NEGOTIATION  # 默认为谈判解决


class ConflictResolutionError(ClipMasterError):
    """冲突解决不合理异常
    
    当冲突解决方案与冲突性质不匹配或不合理时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化冲突解决不合理异常
        
        Args:
            message: 错误信息
            details: 详细信息，包含冲突解决不合理的具体描述
        """
        super().__init__(
            message,
            code=ErrorCode.NARRATIVE_ANALYSIS_ERROR,
            details=details or {}
        )


class ConflictResolver:
    """冲突解决校验器
    
    用于检验冲突解决方案的合理性，确保解决方式与冲突性质相符。
    """
    
    # 冲突类型与适合的解决方法对应关系
    CONFLICT_RESOLUTION_COMPATIBILITY = {
        ConflictType.PHYSICAL: {
            "high": [ResolutionMethod.FORCE, ResolutionMethod.SURRENDER, ResolutionMethod.MEDIATION],
            "medium": [ResolutionMethod.ARBITRATION, ResolutionMethod.NEGOTIATION],
            "low": [ResolutionMethod.AVOIDANCE, ResolutionMethod.COMPROMISE]
        },
        ConflictType.VERBAL: {
            "high": [ResolutionMethod.NEGOTIATION, ResolutionMethod.MEDIATION, ResolutionMethod.COMPROMISE],
            "medium": [ResolutionMethod.ARBITRATION, ResolutionMethod.COLLABORATION],
            "low": [ResolutionMethod.AVOIDANCE, ResolutionMethod.FORCE]
        },
        ConflictType.EMOTIONAL: {
            "high": [ResolutionMethod.MEDIATION, ResolutionMethod.AVOIDANCE, ResolutionMethod.COMPROMISE],
            "medium": [ResolutionMethod.NEGOTIATION, ResolutionMethod.COLLABORATION],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        },
        ConflictType.IDEOLOGICAL: {
            "high": [ResolutionMethod.NEGOTIATION, ResolutionMethod.COMPROMISE, ResolutionMethod.AVOIDANCE],
            "medium": [ResolutionMethod.MEDIATION, ResolutionMethod.COLLABORATION],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        },
        ConflictType.RESOURCE: {
            "high": [ResolutionMethod.NEGOTIATION, ResolutionMethod.ARBITRATION, ResolutionMethod.COLLABORATION],
            "medium": [ResolutionMethod.COMPROMISE, ResolutionMethod.MEDIATION],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        },
        ConflictType.INTEREST: {
            "high": [ResolutionMethod.NEGOTIATION, ResolutionMethod.COMPROMISE, ResolutionMethod.COLLABORATION],
            "medium": [ResolutionMethod.ARBITRATION, ResolutionMethod.MEDIATION],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        },
        ConflictType.RELATIONAL: {
            "high": [ResolutionMethod.MEDIATION, ResolutionMethod.COMPROMISE, ResolutionMethod.COLLABORATION],
            "medium": [ResolutionMethod.NEGOTIATION, ResolutionMethod.AVOIDANCE],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        },
        ConflictType.INTERNAL: {
            "high": [ResolutionMethod.COMPROMISE, ResolutionMethod.COLLABORATION, ResolutionMethod.AVOIDANCE],
            "medium": [ResolutionMethod.MEDIATION, ResolutionMethod.NEGOTIATION],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        }
    }
    
    # 技能与解决方法对应关系
    SKILLS_RESOLUTION_MAPPING = {
        ResolutionMethod.FORCE: ["战斗", "格斗", "武术", "体能", "力量"],
        ResolutionMethod.NEGOTIATION: ["外交", "谈判", "口才", "说服", "语言"],
        ResolutionMethod.COMPROMISE: ["共情", "同理心", "柔软", "适应", "谦让"],
        ResolutionMethod.AVOIDANCE: ["隐匿", "潜行", "速度", "敏捷", "察觉"],
        ResolutionMethod.COLLABORATION: ["领导", "合作", "团队", "协调", "规划"],
        ResolutionMethod.MEDIATION: ["外交", "调解", "沟通", "平衡", "公正"],
        ResolutionMethod.ARBITRATION: ["判断", "法律", "规则", "威严", "公正"],
        ResolutionMethod.SURRENDER: ["认输", "屈服", "示弱", "忍让"],
        ResolutionMethod.SABOTAGE: ["隐匿", "破坏", "计谋", "欺骗", "陷阱"]
    }
    
    def __init__(self, compatibility_path: str = None):
        """初始化冲突解决校验器
        
        Args:
            compatibility_path: 冲突与解决方法兼容性配置文件路径
        """
        self.compatibility_matrix = self._load_compatibility_matrix(compatibility_path)
        self.resolution_issues = []  # 存储检测到的问题
        
    def _load_compatibility_matrix(self, path: Optional[str]) -> Dict[ConflictType, Dict[str, List[ResolutionMethod]]]:
        """加载冲突与解决方法兼容性矩阵
        
        Args:
            path: 配置文件路径
            
        Returns:
            兼容性矩阵
        """
        if not path:
            return self.CONFLICT_RESOLUTION_COMPATIBILITY
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                custom_matrix = json.load(f)
                
                # 转换字符串键为枚举类型
                converted_matrix = {}
                for conflict_str, levels in custom_matrix.items():
                    conflict_type = ConflictType.from_string(conflict_str)
                    converted_levels = {}
                    
                    for level, methods in levels.items():
                        converted_methods = [ResolutionMethod.from_string(m) for m in methods]
                        converted_levels[level] = converted_methods
                    
                    converted_matrix[conflict_type] = converted_levels
                
                return converted_matrix
        except Exception as e:
            logger.warning(f"加载冲突兼容性矩阵失败: {e}，将使用默认配置")
            return self.CONFLICT_RESOLUTION_COMPATIBILITY
    
    def verify_resolutions(self, conflicts: List[Dict[str, Any]]) -> Optional[str]:
        """验证所有冲突的解决方案合理性
        
        Args:
            conflicts: 冲突列表，每个冲突包含类型、强度、解决方案等信息
            
        Returns:
            如果发现问题，返回错误信息；否则返回None
        """
        self.resolution_issues = []  # 重置问题列表
        
        for conflict in conflicts:
            if "resolution" not in conflict or "type" not in conflict["resolution"]:
                continue
                
            resolution_type = conflict["resolution"]["type"].lower()
            
            # 检查武力解决方案
            if resolution_type == "武力解决" or resolution_type == "physical":
                if self._check_physical_resolution(conflict):
                    return self.resolution_issues[-1]["message"]
                    
            # 检查谈判解决方案
            elif resolution_type == "谈判" or resolution_type == "negotiation":
                if self._check_negotiation_resolution(conflict):
                    return self.resolution_issues[-1]["message"]
                    
            # 检查调解解决方案
            elif resolution_type == "调解" or resolution_type == "mediation":
                if self._check_mediation_resolution(conflict):
                    return self.resolution_issues[-1]["message"]
                    
            # 检查仲裁解决方案
            elif resolution_type == "仲裁" or resolution_type == "arbitration":
                if self._check_arbitration_resolution(conflict):
                    return self.resolution_issues[-1]["message"]
        
        # 检查整体解决方案连贯性
        self._check_resolution_coherence(conflicts)
        
        if self.resolution_issues:
            return self.resolution_issues[0]["message"]
        
        return None
    
    def _check_physical_resolution(self, conflict: Dict[str, Any]) -> bool:
        """检查武力解决方案的合理性
        
        Args:
            conflict: 冲突信息
            
        Returns:
            如果有问题返回True，否则返回False
        """
        # 检查是否适合用武力解决
        conflict_type = self._get_conflict_type(conflict)
        compatibility = self._check_resolution_compatibility(
            conflict_type, 
            ResolutionMethod.FORCE,
            conflict.get("intensity", "medium")
        )
        
        if compatibility < 0.5:
            self._add_issue(
                "resolution_mismatch",
                conflict,
                f"武力值不适合解决{conflict_type.name}类型的冲突",
                {
                    "conflict_type": conflict_type.name,
                    "resolution_type": ResolutionMethod.FORCE.name,
                    "compatibility": compatibility
                }
            )
            return True
        
        # 检查力量对比
        if "parties" in conflict and len(conflict["parties"]) >= 2:
            if conflict["parties"][0].get("strength", 0) < conflict["parties"][1].get("strength", 0):
                self._add_issue(
                    "strength_mismatch",
                    conflict,
                    "武力值不符合解决结果",
                    {
                        "initiator_strength": conflict["parties"][0].get("strength", 0),
                        "target_strength": conflict["parties"][1].get("strength", 0)
                    }
                )
                return True
        
        return False
    
    def _check_negotiation_resolution(self, conflict: Dict[str, Any]) -> bool:
        """检查谈判解决方案的合理性
        
        Args:
            conflict: 冲突信息
            
        Returns:
            如果有问题返回True，否则返回False
        """
        # 检查是否适合用谈判解决
        conflict_type = self._get_conflict_type(conflict)
        compatibility = self._check_resolution_compatibility(
            conflict_type, 
            ResolutionMethod.NEGOTIATION,
            conflict.get("intensity", "medium")
        )
        
        if compatibility < 0.3:
            self._add_issue(
                "resolution_mismatch",
                conflict,
                f"谈判不适合解决{conflict_type.name}类型的冲突",
                {
                    "conflict_type": conflict_type.name,
                    "resolution_type": ResolutionMethod.NEGOTIATION.name,
                    "compatibility": compatibility
                }
            )
            return True
        
        # 检查解决者是否具备谈判技能
        if "resolver" in conflict and "skills" in conflict["resolver"]:
            resolver_skills = [s.lower() for s in conflict["resolver"]["skills"]]
            required_skills = [s.lower() for s in self.SKILLS_RESOLUTION_MAPPING[ResolutionMethod.NEGOTIATION]]
            
            if not any(skill in resolver_skills for skill in required_skills):
                self._add_issue(
                    "skill_mismatch",
                    conflict,
                    "调解者缺乏外交技能",
                    {
                        "resolver": conflict["resolver"].get("name", "未知"),
                        "required_skills": required_skills,
                        "actual_skills": resolver_skills
                    }
                )
                return True
        
        return False
    
    def _check_mediation_resolution(self, conflict: Dict[str, Any]) -> bool:
        """检查调解解决方案的合理性
        
        Args:
            conflict: 冲突信息
            
        Returns:
            如果有问题返回True，否则返回False
        """
        # 检查是否有第三方调解者
        if "resolver" not in conflict:
            self._add_issue(
                "missing_mediator",
                conflict,
                "调解方式缺少第三方调解者",
                {}
            )
            return True
            
        # 检查调解者是否有适当技能
        if "skills" in conflict["resolver"]:
            resolver_skills = [s.lower() for s in conflict["resolver"]["skills"]]
            if "diplomat" not in resolver_skills and "调解" not in resolver_skills:
                self._add_issue(
                    "skill_mismatch",
                    conflict,
                    "调解者缺乏外交技能",
                    {
                        "resolver": conflict["resolver"].get("name", "未知"),
                        "required_skills": ["diplomat", "调解", "外交"],
                        "actual_skills": resolver_skills
                    }
                )
                return True
        
        return False
    
    def _check_arbitration_resolution(self, conflict: Dict[str, Any]) -> bool:
        """检查仲裁解决方案的合理性
        
        Args:
            conflict: 冲突信息
            
        Returns:
            如果有问题返回True，否则返回False
        """
        # 检查是否有仲裁者
        if "resolver" not in conflict:
            self._add_issue(
                "missing_arbitrator",
                conflict,
                "仲裁方式缺少仲裁者",
                {}
            )
            return True
            
        # 检查仲裁者是否有权威
        if "authority" not in conflict["resolver"] or not conflict["resolver"]["authority"]:
            self._add_issue(
                "insufficient_authority",
                conflict,
                "仲裁者缺乏足够权威",
                {
                    "resolver": conflict["resolver"].get("name", "未知")
                }
            )
            return True
        
        # 检查仲裁者是否有适当技能
        if "skills" in conflict["resolver"]:
            resolver_skills = [s.lower() for s in conflict["resolver"]["skills"]]
            required_skills = ["judge", "arbitrator", "authority", "法律", "仲裁", "权威"]
            
            if not any(skill in resolver_skills for skill in required_skills):
                self._add_issue(
                    "skill_mismatch",
                    conflict,
                    "仲裁者缺乏仲裁技能",
                    {
                        "resolver": conflict["resolver"].get("name", "未知"),
                        "required_skills": required_skills,
                        "actual_skills": resolver_skills
                    }
                )
                return True
        
        return False
    
    def _check_resolution_coherence(self, conflicts: List[Dict[str, Any]]) -> None:
        """检查一系列冲突解决方案之间的连贯性
        
        Args:
            conflicts: 冲突列表
        """
        if len(conflicts) <= 1:
            return
        
        # 相同角色不应在相邻冲突中使用截然不同的解决方式
        for i in range(1, len(conflicts)):
            prev_conflict = conflicts[i-1]
            curr_conflict = conflicts[i]
            
            # 检查是否为同一个角色
            if not self._is_same_resolver(prev_conflict, curr_conflict):
                continue
                
            prev_method = self._get_resolution_method(prev_conflict)
            curr_method = self._get_resolution_method(curr_conflict)
            
            # 检查解决方式是否冲突
            if self._are_methods_conflicting(prev_method, curr_method):
                resolver_name = self._get_resolver_name(curr_conflict)
                self._add_issue(
                    "inconsistent_resolution",
                    curr_conflict,
                    f"角色{resolver_name}的解决方式不一致: {prev_method.name} -> {curr_method.name}",
                    {
                        "resolver": resolver_name,
                        "prev_method": prev_method.name,
                        "curr_method": curr_method.name
                    }
                )
    
    def _get_conflict_type(self, conflict: Dict[str, Any]) -> ConflictType:
        """获取冲突类型
        
        Args:
            conflict: 冲突信息
            
        Returns:
            冲突类型枚举
        """
        if "type" in conflict:
            return ConflictType.from_string(conflict["type"])
        return ConflictType.VERBAL  # 默认为言语冲突
    
    def _get_resolution_method(self, conflict: Dict[str, Any]) -> ResolutionMethod:
        """获取解决方法
        
        Args:
            conflict: 冲突信息
            
        Returns:
            解决方法枚举
        """
        if "resolution" in conflict and "type" in conflict["resolution"]:
            return ResolutionMethod.from_string(conflict["resolution"]["type"])
        return ResolutionMethod.NEGOTIATION  # 默认为谈判解决
    
    def _check_resolution_compatibility(
        self, 
        conflict_type: ConflictType, 
        resolution_method: ResolutionMethod,
        intensity: str
    ) -> float:
        """检查解决方式与冲突类型的兼容性
        
        Args:
            conflict_type: 冲突类型
            resolution_method: 解决方法
            intensity: 冲突强度("low", "medium", "high")
            
        Returns:
            兼容性评分 (0-1)
        """
        if conflict_type not in self.compatibility_matrix:
            return 0.5  # 默认中等兼容性
            
        compatibility = 0.0
        
        # 检查是否在高度适合的方法中
        if resolution_method in self.compatibility_matrix[conflict_type].get("high", []):
            compatibility = 0.9
        # 检查是否在中等适合的方法中
        elif resolution_method in self.compatibility_matrix[conflict_type].get("medium", []):
            compatibility = 0.6
        # 检查是否在低度适合的方法中
        elif resolution_method in self.compatibility_matrix[conflict_type].get("low", []):
            compatibility = 0.3
        else:
            compatibility = 0.1  # 不在兼容性矩阵中，低兼容性
        
        # 根据冲突强度调整兼容性
        if intensity == "high":
            # 高强度冲突需要更适合的解决方法
            compatibility *= 0.8
        elif intensity == "low":
            # 低强度冲突对解决方法要求较低
            compatibility = min(1.0, compatibility * 1.2)
            
        return compatibility
    
    def _is_same_resolver(self, conflict1: Dict[str, Any], conflict2: Dict[str, Any]) -> bool:
        """检查两个冲突是否由同一个角色解决
        
        Args:
            conflict1: 第一个冲突
            conflict2: 第二个冲突
            
        Returns:
            如果是同一个解决者返回True，否则返回False
        """
        resolver1_id = None
        resolver2_id = None
        
        if "resolver" in conflict1:
            resolver1_id = conflict1["resolver"].get("id", conflict1["resolver"].get("name"))
            
        if "resolver" in conflict2:
            resolver2_id = conflict2["resolver"].get("id", conflict2["resolver"].get("name"))
            
        return resolver1_id is not None and resolver1_id == resolver2_id
    
    def _get_resolver_name(self, conflict: Dict[str, Any]) -> str:
        """获取解决者名称
        
        Args:
            conflict: 冲突信息
            
        Returns:
            解决者名称
        """
        if "resolver" in conflict:
            return conflict["resolver"].get("name", "未知角色")
        return "未知角色"
    
    def _are_methods_conflicting(self, method1: ResolutionMethod, method2: ResolutionMethod) -> bool:
        """检查两种解决方法是否冲突
        
        Args:
            method1: 第一种解决方法
            method2: 第二种解决方法
            
        Returns:
            如果方法冲突返回True，否则返回False
        """
        # 定义冲突的方法对
        conflicting_pairs = [
            {ResolutionMethod.FORCE, ResolutionMethod.NEGOTIATION},
            {ResolutionMethod.FORCE, ResolutionMethod.COMPROMISE},
            {ResolutionMethod.SABOTAGE, ResolutionMethod.COLLABORATION},
            {ResolutionMethod.AVOIDANCE, ResolutionMethod.FORCE},
            {ResolutionMethod.SURRENDER, ResolutionMethod.NEGOTIATION}
        ]
        
        return any(method1 in pair and method2 in pair for pair in conflicting_pairs)
    
    def _add_issue(
        self, 
        issue_type: str, 
        conflict: Dict[str, Any],
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """添加一个解决方案问题
        
        Args:
            issue_type: 问题类型
            conflict: 问题相关的冲突
            message: 问题描述信息
            details: 问题详细信息
        """
        issue = {
            "type": issue_type,
            "conflict_id": conflict.get("id", "unknown"),
            "message": message,
            "details": details
        }
        
        self.resolution_issues.append(issue)
    
    def get_all_issues(self) -> List[Dict[str, Any]]:
        """获取所有发现的问题
        
        Returns:
            问题列表
        """
        return self.resolution_issues
    
    def generate_suggestions(self, conflicts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """为冲突解决方案生成改进建议
        
        Args:
            conflicts: 冲突列表
            
        Returns:
            改进建议
        """
        suggestions = {}
        
        # 先验证冲突解决方案
        self.verify_resolutions(conflicts)
        
        for issue in self.resolution_issues:
            conflict_id = issue["conflict_id"]
            
            if conflict_id not in suggestions:
                suggestions[conflict_id] = []
                
            suggestion = self._generate_suggestion_for_issue(issue)
            if suggestion:
                suggestions[conflict_id].append(suggestion)
        
        return suggestions
    
    def _generate_suggestion_for_issue(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """为特定问题生成改进建议
        
        Args:
            issue: 问题信息
            
        Returns:
            改进建议
        """
        issue_type = issue["type"]
        
        if issue_type == "resolution_mismatch":
            return {
                "problem": issue["message"],
                "suggestion": self._suggest_better_resolution(issue["details"])
            }
        elif issue_type == "strength_mismatch":
            return {
                "problem": issue["message"],
                "suggestion": "调整参与方的力量对比，确保武力解决方案的合理性，或改用其他解决方式"
            }
        elif issue_type == "skill_mismatch":
            return {
                "problem": issue["message"],
                "suggestion": f"为解决者添加所需技能: {', '.join(issue['details'].get('required_skills', []))}"
            }
        elif issue_type == "missing_mediator":
            return {
                "problem": issue["message"],
                "suggestion": "添加一个合适的第三方调解者，具备外交或调解能力"
            }
        elif issue_type == "insufficient_authority":
            return {
                "problem": issue["message"],
                "suggestion": "提升仲裁者的权威性，或更换为具有足够权威的角色"
            }
        elif issue_type == "inconsistent_resolution":
            return {
                "problem": issue["message"],
                "suggestion": "确保同一角色的解决方式保持一致，或添加角色成长/变化的解释"
            }
        
        return None
    
    def _suggest_better_resolution(self, details: Dict[str, Any]) -> str:
        """根据冲突类型建议更合适的解决方法
        
        Args:
            details: 问题详细信息
            
        Returns:
            建议内容
        """
        conflict_type_str = details.get("conflict_type", "VERBAL")
        
        try:
            conflict_type = ConflictType[conflict_type_str]
        except (KeyError, ValueError):
            conflict_type = ConflictType.VERBAL
        
        # 获取该冲突类型的高适应性解决方法
        if conflict_type in self.compatibility_matrix:
            high_methods = self.compatibility_matrix[conflict_type].get("high", [])
            if high_methods:
                method_names = [method.name for method in high_methods]
                return f"建议使用以下解决方式: {', '.join(method_names)}"
        
        return "建议使用谈判或调解等和平方式解决冲突"


def validate_conflict_resolution(
    conflicts: List[Dict[str, Any]],
    raise_exception: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：验证冲突解决方案
    
    Args:
        conflicts: 冲突列表
        raise_exception: 是否在发现问题时抛出异常
        
    Returns:
        验证结果和建议
        
    Raises:
        ConflictResolutionError: 如果raise_exception为True且发现问题，则抛出异常
    """
    resolver = ConflictResolver()
    
    error_message = resolver.verify_resolutions(conflicts)
    issues = resolver.get_all_issues()
    
    if issues and raise_exception:
        raise ConflictResolutionError(
            message=error_message or "冲突解决方案存在问题",
            details={"issues": issues}
        )
    
    suggestions = resolver.generate_suggestions(conflicts)
    
    return {
        "valid": not issues,
        "issues": issues,
        "suggestions": suggestions
    } 