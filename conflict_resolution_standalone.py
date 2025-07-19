#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
冲突解决校验器独立测试脚本

提供冲突解决校验器的独立测试功能，无需依赖完整项目。
"""

import sys
import os
import logging
from pathlib import Path
import json
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple, Set, Union

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 基本异常类
class ErrorCode:
    NARRATIVE_ANALYSIS_ERROR = 1405

class ClipMasterError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ConflictType(Enum):
    """冲突类型枚举"""
    PHYSICAL = auto()
    VERBAL = auto()
    EMOTIONAL = auto()
    IDEOLOGICAL = auto()
    RESOURCE = auto()
    INTEREST = auto()
    RELATIONAL = auto()
    INTERNAL = auto()
    
    @classmethod
    def from_string(cls, conflict_type: str) -> 'ConflictType':
        """从字符串获取冲突类型"""
        mapping = {
            "物理": cls.PHYSICAL,
            "physical": cls.PHYSICAL,
            "言语": cls.VERBAL,
            "verbal": cls.VERBAL,
            "情感": cls.EMOTIONAL,
            "emotional": cls.EMOTIONAL,
            "意识形态": cls.IDEOLOGICAL,
            "ideological": cls.IDEOLOGICAL,
            "资源": cls.RESOURCE,
            "resource": cls.RESOURCE,
            "利益": cls.INTEREST,
            "interest": cls.INTEREST,
            "关系": cls.RELATIONAL,
            "relational": cls.RELATIONAL,
            "内心": cls.INTERNAL,
            "internal": cls.INTERNAL
        }
        
        lower_type = conflict_type.lower()
        if lower_type in mapping:
            return mapping[lower_type]
        
        for key, value in mapping.items():
            if key in lower_type:
                return value
        
        return cls.VERBAL


class ResolutionMethod(Enum):
    """冲突解决方法枚举"""
    FORCE = auto()
    NEGOTIATION = auto()
    COMPROMISE = auto()
    AVOIDANCE = auto()
    COLLABORATION = auto()
    MEDIATION = auto()
    ARBITRATION = auto()
    SURRENDER = auto()
    SABOTAGE = auto()

    @classmethod
    def from_string(cls, method: str) -> 'ResolutionMethod':
        """从字符串获取解决方法类型"""
        mapping = {
            "武力": cls.FORCE,
            "force": cls.FORCE,
            "谈判": cls.NEGOTIATION,
            "negotiation": cls.NEGOTIATION,
            "妥协": cls.COMPROMISE,
            "compromise": cls.COMPROMISE,
            "回避": cls.AVOIDANCE,
            "avoidance": cls.AVOIDANCE,
            "合作": cls.COLLABORATION,
            "collaboration": cls.COLLABORATION,
            "调解": cls.MEDIATION,
            "mediation": cls.MEDIATION,
            "仲裁": cls.ARBITRATION,
            "arbitration": cls.ARBITRATION,
            "投降": cls.SURRENDER,
            "surrender": cls.SURRENDER,
            "破坏": cls.SABOTAGE,
            "sabotage": cls.SABOTAGE
        }
        
        lower_method = method.lower()
        if lower_method in mapping:
            return mapping[lower_method]
        
        for key, value in mapping.items():
            if key in lower_method:
                return value
        
        return cls.NEGOTIATION


class ConflictResolutionError(ClipMasterError):
    """冲突解决不合理异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=ErrorCode.NARRATIVE_ANALYSIS_ERROR, details=details or {})


class ConflictResolver:
    """冲突解决校验器"""
    
    # 冲突类型与解决方法兼容性简化
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
        ConflictType.IDEOLOGICAL: {
            "high": [ResolutionMethod.NEGOTIATION, ResolutionMethod.COMPROMISE, ResolutionMethod.AVOIDANCE],
            "medium": [ResolutionMethod.MEDIATION, ResolutionMethod.COLLABORATION],
            "low": [ResolutionMethod.FORCE, ResolutionMethod.SABOTAGE]
        }
    }
    
    def __init__(self):
        """初始化冲突解决校验器"""
        self.resolution_issues = []
    
    def verify_resolutions(self, conflicts: List[Dict[str, Any]]) -> Optional[str]:
        """验证冲突解决方案合理性"""
        self.resolution_issues = []
        
        for conflict in conflicts:
            if "resolution" not in conflict or "type" not in conflict["resolution"]:
                continue
                
            resolution_type = conflict["resolution"]["type"].lower()
            
            # 检查武力解决方案
            if "武力" in resolution_type or "force" in resolution_type:
                self._check_physical_resolution(conflict)
                
            # 检查仲裁解决方案
            elif "仲裁" in resolution_type or "arbitration" in resolution_type:
                self._check_arbitration_resolution(conflict)
        
        if self.resolution_issues:
            return self.resolution_issues[0]["message"]
        
        return None
    
    def _check_physical_resolution(self, conflict: Dict[str, Any]) -> None:
        """检查武力解决方案合理性"""
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
    
    def _check_arbitration_resolution(self, conflict: Dict[str, Any]) -> None:
        """检查仲裁解决方案合理性"""
        # 检查是否有仲裁者
        if "resolver" not in conflict:
            self._add_issue(
                "missing_arbitrator",
                conflict,
                "仲裁方式缺少仲裁者",
                {}
            )
    
    def _add_issue(self, issue_type: str, conflict: Dict[str, Any], message: str, details: Dict[str, Any]) -> None:
        """添加问题"""
        issue = {
            "type": issue_type,
            "conflict_id": conflict.get("id", "unknown"),
            "message": message,
            "details": details
        }
        self.resolution_issues.append(issue)
    
    def get_all_issues(self) -> List[Dict[str, Any]]:
        """获取所有问题"""
        return self.resolution_issues


def create_test_conflicts():
    """创建测试冲突数据"""
    valid_conflicts = [
        {
            "id": "conflict1",
            "type": "verbal",
            "parties": [
                {"id": "char1", "name": "张三", "strength": 7},
                {"id": "char2", "name": "李四", "strength": 5}
            ],
            "resolution": {
                "type": "negotiation",
                "outcome": "reached agreement"
            },
            "resolver": {
                "id": "char1",
                "name": "张三",
                "skills": ["negotiation", "diplomacy"]
            }
        }
    ]
    
    invalid_conflicts = [
        {
            "id": "invalid1",
            "type": "physical",
            "parties": [
                {"id": "char1", "name": "张三", "strength": 4},
                {"id": "char2", "name": "李四", "strength": 8}
            ],
            "resolution": {
                "type": "force",
                "outcome": "char1 won"
            },
            "resolver": {
                "id": "char1",
                "name": "张三",
                "skills": ["combat"]
            }
        },
        {
            "id": "invalid2",
            "type": "verbal",
            "parties": [
                {"id": "char3", "name": "王五", "strength": 6},
                {"id": "char4", "name": "赵六", "strength": 6}
            ],
            "resolution": {
                "type": "arbitration",
                "outcome": "resolved by arbitration"
            }
            # 缺少仲裁者
        }
    ]
    
    return {
        "valid": valid_conflicts,
        "invalid": invalid_conflicts
    }


def test_resolver():
    """测试冲突解决校验器"""
    print("\n=== 测试冲突解决校验器 ===")
    
    conflicts = create_test_conflicts()
    resolver = ConflictResolver()
    
    # 测试有效冲突
    error = resolver.verify_resolutions(conflicts["valid"])
    if error:
        print(f"有效冲突检测到错误: {error}")
    else:
        print("有效冲突检测通过")
    
    # 测试无效冲突
    error = resolver.verify_resolutions(conflicts["invalid"])
    if error:
        print(f"无效冲突检测到错误: {error}")
        issues = resolver.get_all_issues()
        for issue in issues:
            print(f"- {issue['message']}")
    else:
        print("无效冲突未检测到错误")


def main():
    """主函数"""
    print("=== 冲突解决校验器独立测试 ===")
    
    try:
        # 测试冲突解决校验器
        test_resolver()
        
        print("\n所有测试完成!")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


 