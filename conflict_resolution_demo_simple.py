#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
冲突解决校验器简易演示

独立演示冲突解决校验器功能，无需依赖完整项目。
"""

import sys
import json
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union

# 简化的异常类
class ErrorCode:
    NARRATIVE_ANALYSIS_ERROR = 1405

class ClipMasterError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

# 冲突类型枚举
class ConflictType(Enum):
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
        lower_type = conflict_type.lower()
        for enum_type in cls:
            if enum_type.name.lower() in lower_type:
                return enum_type
        return cls.VERBAL

# 解决方法枚举
class ResolutionMethod(Enum):
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
        lower_method = method.lower()
        for enum_method in cls:
            if enum_method.name.lower() in lower_method:
                return enum_method
        return cls.NEGOTIATION

# 冲突解决错误
class ConflictResolutionError(ClipMasterError):
    """冲突解决不合理异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=ErrorCode.NARRATIVE_ANALYSIS_ERROR, details=details or {})

# 冲突解决校验器
class ConflictResolver:
    """冲突解决校验器简化版"""
    
    def __init__(self):
        """初始化校验器"""
        self.resolution_issues = []
    
    def verify_resolutions(self, conflicts: List[Dict[str, Any]]) -> Optional[str]:
        """验证冲突解决方案合理性"""
        self.resolution_issues = []
        
        for conflict in conflicts:
            if "resolution" not in conflict or "type" not in conflict["resolution"]:
                continue
                
            resolution_type = conflict["resolution"]["type"].lower()
            
            # 检查武力解决方案
            if "force" in resolution_type or "武力" in resolution_type:
                self._check_physical_resolution(conflict)
                
            # 检查仲裁解决方案
            elif "arbitration" in resolution_type or "仲裁" in resolution_type:
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
        
    def generate_suggestions(self, conflicts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """生成建议"""
        suggestions = {}
        
        # 先验证解决方案
        self.verify_resolutions(conflicts)
        
        for issue in self.resolution_issues:
            conflict_id = issue["conflict_id"]
            
            if conflict_id not in suggestions:
                suggestions[conflict_id] = []
                
            if issue["type"] == "strength_mismatch":
                suggestions[conflict_id].append({
                    "problem": issue["message"],
                    "suggestion": "调整参与方的力量对比，确保武力解决方案的合理性，或改用其他解决方式"
                })
            elif issue["type"] == "missing_arbitrator":
                suggestions[conflict_id].append({
                    "problem": issue["message"],
                    "suggestion": "添加一个合适的第三方仲裁者，具备仲裁能力和权威性"
                })
        
        return suggestions

def validate_conflict_resolution(conflicts, raise_exception=False):
    """简化的便捷验证函数"""
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

def load_demo_conflicts():
    """加载示例冲突数据"""
    # 场景1：适当的冲突解决方案
    appropriate_resolutions = [
        {
            "id": "conflict1",
            "type": "verbal",
            "description": "张三和李四关于项目方向的争论",
            "parties": [
                {"id": "char1", "name": "张三", "strength": 7},
                {"id": "char2", "name": "李四", "strength": 5}
            ],
            "resolution": {
                "type": "negotiation",
                "outcome": "双方达成折中方案，融合两种方法"
            },
            "resolver": {
                "id": "char1",
                "name": "张三",
                "skills": ["negotiation", "diplomacy"]
            }
        }
    ]
    
    # 场景2：问题冲突解决方案
    problematic_resolutions = [
        {
            "id": "problem1",
            "type": "physical",
            "description": "吴九和郑十的打斗",
            "parties": [
                {"id": "char1", "name": "吴九", "strength": 4},
                {"id": "char2", "name": "郑十", "strength": 8}
            ],
            "resolution": {
                "type": "force",
                "outcome": "吴九战胜郑十"  # 力量对比不合理
            }
        },
        {
            "id": "problem2",
            "type": "verbal",
            "description": "冯十一和陈十二的关系冲突",
            "parties": [
                {"id": "char3", "name": "冯十一", "strength": 5},
                {"id": "char4", "name": "陈十二", "strength": 5}
            ],
            "resolution": {
                "type": "arbitration",  # 缺少仲裁者
                "outcome": "双方接受第三方仲裁结果"
            }
        }
    ]
    
    return {
        "appropriate": appropriate_resolutions,
        "problematic": problematic_resolutions
    }

def main():
    """主函数"""
    print("===== 冲突解决校验器演示 =====\n")
    
    conflicts = load_demo_conflicts()
    
    # 测试1: 验证有效的冲突
    print("1. 验证合理的冲突解决方案")
    result = validate_conflict_resolution(conflicts["appropriate"])
    print(f"  验证结果: {'通过' if result['valid'] else '未通过'}")
    print(f"  检测到问题数量: {len(result['issues'])}")
    
    # 测试2: 验证有问题的冲突
    print("\n2. 验证存在问题的冲突解决方案")
    result = validate_conflict_resolution(conflicts["problematic"])
    print(f"  验证结果: {'通过' if result['valid'] else '未通过'}")
    print(f"  检测到问题数量: {len(result['issues'])}")
    
    # 显示问题详情
    if not result["valid"]:
        print("\n  问题详情:")
        for i, issue in enumerate(result["issues"], 1):
            print(f"  {i}. {issue['message']} (冲突ID: {issue['conflict_id']})")
    
    # 显示建议
    if result["suggestions"]:
        print("\n  改进建议:")
        for conflict_id, suggestions in result["suggestions"].items():
            print(f"  冲突 {conflict_id} 的建议:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"    {i}. {suggestion['suggestion']}")
    
    # 测试3: 异常抛出
    print("\n3. 测试异常抛出功能")
    try:
        validate_conflict_resolution(conflicts["problematic"], raise_exception=True)
        print("  未抛出预期异常")
    except ConflictResolutionError as e:
        print(f"  成功抛出异常: {e}")

if __name__ == "__main__":
    main() 