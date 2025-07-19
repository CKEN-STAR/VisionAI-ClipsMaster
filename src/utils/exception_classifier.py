#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常分类体系模块

提供一个完整的异常分类系统，用于对系统中的异常进行分类、分析和处理：
1. 按严重程度分类（致命、严重、警告、信息）
2. 按来源分类（系统、模型、数据、用户、网络等）
3. 按影响范围分类（全局、模块、功能、数据）
4. 按可恢复性分类（可自动恢复、需用户干预、不可恢复）
"""

import enum
from typing import Dict, List, Optional, Any, Union, Callable, Set, Tuple
from loguru import logger
from dataclasses import dataclass

from src.utils.exceptions import ClipMasterError, ErrorCode


class SeverityLevel(enum.Enum):
    """异常严重程度枚举"""
    FATAL = 0       # 致命错误，导致程序无法继续运行
    CRITICAL = 1    # 严重错误，导致主要功能无法使用
    ERROR = 2       # 一般错误，影响部分功能
    WARNING = 3     # 警告，可能影响功能但不会导致失败
    INFO = 4        # 信息性异常，通常不影响功能


class ErrorSource(enum.Enum):
    """异常来源枚举"""
    SYSTEM = 0      # 系统级错误（OS、内存等）
    MODEL = 1       # 模型相关错误（加载、推理等）
    DATA = 2        # 数据相关错误（文件、格式等）
    USER = 3        # 用户输入相关错误
    NETWORK = 4     # 网络相关错误
    RESOURCE = 5    # 资源相关错误（GPU、CPU等）
    CONFIG = 6      # 配置相关错误
    ALGORITHM = 7   # 算法相关错误
    UNKNOWN = 8     # 未知来源


class ImpactScope(enum.Enum):
    """影响范围枚举"""
    GLOBAL = 0      # 全局影响
    MODULE = 1      # 模块级影响
    FEATURE = 2     # 功能级影响
    DATA = 3        # 数据级影响
    COSMETIC = 4    # 仅影响界面/外观


class RecoveryType(enum.Enum):
    """可恢复性枚举"""
    AUTO = 0        # 可自动恢复
    USER_ASSISTED = 1  # 需用户干预恢复
    NON_RECOVERABLE = 2  # 不可恢复


@dataclass
class ErrorClassification:
    """错误分类数据类"""
    severity: SeverityLevel
    source: ErrorSource
    impact: ImpactScope
    recovery: RecoveryType
    error_code: Optional[ErrorCode] = None
    description: str = ""
    recommended_action: str = ""
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"[{self.severity.name}] {self.source.name} 错误 - "
                f"影响: {self.impact.name}, 恢复: {self.recovery.name}"
                f"{f' - {self.error_code.name}' if self.error_code else ''}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "severity": self.severity.name,
            "source": self.source.name,
            "impact": self.impact.name,
            "recovery": self.recovery.name,
            "error_code": self.error_code.name if self.error_code else None,
            "description": self.description,
            "recommended_action": self.recommended_action
        }


class ExceptionClassifier:
    """异常分类器"""
    
    def __init__(self):
        """初始化异常分类器"""
        # 预定义的错误代码分类映射
        self._error_code_map = self._init_error_code_map()
        
        # 错误类型映射
        self._error_type_map = self._init_error_type_map()
        
        # 自定义分类规则
        self._custom_rules: List[Tuple[Callable[[Exception, Dict[str, Any]], bool], ErrorClassification]] = []
    
    def _init_error_code_map(self) -> Dict[ErrorCode, ErrorClassification]:
        """初始化错误代码映射"""
        return {
            ErrorCode.GENERAL_ERROR: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.UNKNOWN,
                impact=ImpactScope.MODULE,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.GENERAL_ERROR,
                description="一般性错误",
                recommended_action="检查错误详情并尝试重新操作"
            ),
            ErrorCode.FILE_NOT_FOUND: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.DATA,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.FILE_NOT_FOUND,
                description="文件未找到",
                recommended_action="检查文件路径是否正确，文件是否存在"
            ),
            ErrorCode.PERMISSION_DENIED: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.PERMISSION_DENIED,
                description="权限被拒绝",
                recommended_action="检查文件或资源的访问权限"
            ),
            ErrorCode.DEPENDENCY_ERROR: ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.GLOBAL,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.DEPENDENCY_ERROR,
                description="依赖项错误",
                recommended_action="检查并安装所需的依赖项"
            ),
            ErrorCode.MEMORY_ERROR: ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.RESOURCE,
                impact=ImpactScope.GLOBAL,
                recovery=RecoveryType.AUTO,
                error_code=ErrorCode.MEMORY_ERROR,
                description="内存错误",
                recommended_action="关闭其他应用程序释放内存或使用更小的模型"
            ),
            ErrorCode.MODEL_ERROR: ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.MODEL,
                impact=ImpactScope.MODULE,
                recovery=RecoveryType.AUTO,
                error_code=ErrorCode.MODEL_ERROR,
                description="模型错误",
                recommended_action="尝试重新加载模型或使用备用模型"
            ),
            ErrorCode.VALIDATION_ERROR: ErrorClassification(
                severity=SeverityLevel.WARNING,
                source=ErrorSource.DATA,
                impact=ImpactScope.DATA,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.VALIDATION_ERROR,
                description="验证错误",
                recommended_action="检查输入数据是否符合要求"
            ),
            ErrorCode.PROCESSING_ERROR: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.ALGORITHM,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.AUTO,
                error_code=ErrorCode.PROCESSING_ERROR,
                description="处理错误",
                recommended_action="检查处理参数或尝试使用不同的处理方法"
            ),
            ErrorCode.FORMAT_ERROR: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.DATA,
                impact=ImpactScope.DATA,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.FORMAT_ERROR,
                description="格式错误",
                recommended_action="检查输入数据格式是否正确"
            ),
            ErrorCode.NETWORK_ERROR: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.NETWORK,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.AUTO,
                error_code=ErrorCode.NETWORK_ERROR,
                description="网络错误",
                recommended_action="检查网络连接或稍后重试"
            ),
            ErrorCode.USER_INPUT_ERROR: ErrorClassification(
                severity=SeverityLevel.WARNING,
                source=ErrorSource.USER,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.USER_INPUT_ERROR,
                description="用户输入错误",
                recommended_action="检查输入内容是否符合要求"
            ),
            ErrorCode.SYSTEM_ERROR: ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.GLOBAL,
                recovery=RecoveryType.NON_RECOVERABLE,
                error_code=ErrorCode.SYSTEM_ERROR,
                description="系统错误",
                recommended_action="重启应用程序或联系技术支持"
            ),
            ErrorCode.TIMEOUT_ERROR: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.AUTO,
                error_code=ErrorCode.TIMEOUT_ERROR,
                description="超时错误",
                recommended_action="检查网络连接或增加超时时间"
            ),
            ErrorCode.CONFIG_ERROR: ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.CONFIG,
                impact=ImpactScope.MODULE,
                recovery=RecoveryType.USER_ASSISTED,
                error_code=ErrorCode.CONFIG_ERROR,
                description="配置错误",
                recommended_action="检查配置文件是否正确"
            ),
        }
    
    def _init_error_type_map(self) -> Dict[str, ErrorClassification]:
        """初始化错误类型映射"""
        return {
            # 系统错误
            "MemoryError": ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.RESOURCE,
                impact=ImpactScope.GLOBAL,
                recovery=RecoveryType.AUTO,
                description="Python内存错误",
                recommended_action="关闭其他应用程序释放内存或使用更小的模型"
            ),
            "OSError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="操作系统错误",
                recommended_action="检查系统资源或权限"
            ),
            "PermissionError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="权限错误",
                recommended_action="检查文件或资源的访问权限"
            ),
            
            # 文件错误
            "FileNotFoundError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.DATA,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="文件未找到",
                recommended_action="检查文件路径是否正确，文件是否存在"
            ),
            "IOError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.DATA,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="输入输出错误",
                recommended_action="检查文件是否可访问或磁盘空间是否充足"
            ),
            
            # 值错误
            "ValueError": ErrorClassification(
                severity=SeverityLevel.WARNING,
                source=ErrorSource.USER,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="值错误",
                recommended_action="检查输入参数是否符合要求"
            ),
            "TypeError": ErrorClassification(
                severity=SeverityLevel.WARNING,
                source=ErrorSource.USER,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="类型错误",
                recommended_action="检查输入参数类型是否正确"
            ),
            
            # 自定义错误
            "MemoryOverflowError": ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.RESOURCE,
                impact=ImpactScope.GLOBAL,
                recovery=RecoveryType.AUTO,
                description="内存溢出错误",
                recommended_action="关闭其他应用程序释放内存或使用更小的模型"
            ),
            "ModelCorruptionError": ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.MODEL,
                impact=ImpactScope.MODULE,
                recovery=RecoveryType.AUTO,
                description="模型损坏错误",
                recommended_action="重新下载模型或使用备用模型"
            ),
            "InvalidSRTError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.DATA,
                impact=ImpactScope.DATA,
                recovery=RecoveryType.USER_ASSISTED,
                description="无效的SRT文件",
                recommended_action="检查SRT文件格式是否正确"
            ),
            
            # 网络错误
            "ConnectionError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.NETWORK,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.AUTO,
                description="连接错误",
                recommended_action="检查网络连接或稍后重试"
            ),
            "TimeoutError": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.NETWORK,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.AUTO,
                description="超时错误",
                recommended_action="检查网络连接或增加超时时间"
            ),
            
            # 模型错误
            "ModelLoadError": ErrorClassification(
                severity=SeverityLevel.CRITICAL,
                source=ErrorSource.MODEL,
                impact=ImpactScope.MODULE,
                recovery=RecoveryType.AUTO,
                description="模型加载错误",
                recommended_action="检查模型文件是否完整或使用备用模型"
            ),
            
            # 默认错误
            "Exception": ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.UNKNOWN,
                impact=ImpactScope.MODULE,
                recovery=RecoveryType.USER_ASSISTED,
                description="未知错误",
                recommended_action="检查错误详情并尝试重新操作"
            ),
        }
    
    def add_custom_rule(self, 
                      condition: Callable[[Exception, Dict[str, Any]], bool],
                      classification: ErrorClassification) -> None:
        """添加自定义分类规则
        
        Args:
            condition: 条件函数，接受异常和上下文，返回是否匹配
            classification: 匹配时的分类结果
        """
        self._custom_rules.append((condition, classification))
    
    def classify(self, 
               exception: Exception, 
               context: Dict[str, Any] = None) -> ErrorClassification:
        """分类异常
        
        Args:
            exception: 异常对象
            context: 上下文信息
            
        Returns:
            ErrorClassification: 异常分类结果
        """
        context = context or {}
        
        # 1. 检查自定义规则
        for condition, classification in self._custom_rules:
            try:
                if condition(exception, context):
                    logger.debug(f"异常 {type(exception).__name__} 匹配自定义规则")
                    return classification
            except Exception as e:
                logger.warning(f"评估自定义规则时出错: {e}")
        
        # 2. 检查是否为ClipMasterError并有错误代码
        if isinstance(exception, ClipMasterError) and hasattr(exception, "code") and exception.code:
            if exception.code in self._error_code_map:
                logger.debug(f"异常 {type(exception).__name__} 匹配错误代码 {exception.code}")
                return self._error_code_map[exception.code]
        
        # 3. 根据异常类型匹配
        error_type = type(exception).__name__
        if error_type in self._error_type_map:
            logger.debug(f"异常 {error_type} 匹配类型映射")
            return self._error_type_map[error_type]
        
        # 4. 检查异常类的父类
        for base in type(exception).__mro__[1:]:  # 跳过自身
            base_name = base.__name__
            if base_name in self._error_type_map:
                logger.debug(f"异常 {error_type} 匹配父类 {base_name}")
                return self._error_type_map[base_name]
        
        # 5. 默认分类
        logger.debug(f"异常 {error_type} 使用默认分类")
        return self._error_type_map["Exception"]
    
    def get_error_stats(self) -> Dict[str, Dict[str, int]]:
        """获取错误统计信息
        
        Returns:
            Dict[str, Dict[str, int]]: 按不同维度统计的错误数量
        """
        # 从错误处理器获取统计信息
        try:
            from src.core.error_handler import get_error_handler
            error_handler = get_error_handler()
            return {
                "by_severity": self._count_by_attribute("severity"),
                "by_source": self._count_by_attribute("source"),
                "by_impact": self._count_by_attribute("impact"),
                "by_recovery": self._count_by_attribute("recovery"),
                "total": error_handler.error_stats["total_errors"]
            }
        except Exception as e:
            logger.warning(f"获取错误统计信息失败: {e}")
            return {}
    
    def _count_by_attribute(self, attribute: str) -> Dict[str, int]:
        """按属性统计错误
        
        Args:
            attribute: 属性名称
            
        Returns:
            Dict[str, int]: 统计结果
        """
        try:
            from src.core.error_handler import get_error_handler
            error_handler = get_error_handler()
            
            result = {}
            for error_type, count in error_handler.error_stats["by_type"].items():
                try:
                    # 创建一个临时异常对象用于分类
                    temp_exception = type(error_type, (Exception,), {})()
                    classification = self.classify(temp_exception)
                    
                    # 获取属性值
                    attr_value = getattr(classification, attribute).name
                    
                    # 更新计数
                    if attr_value in result:
                        result[attr_value] += count
                    else:
                        result[attr_value] = count
                except Exception:
                    # 忽略无法分类的错误类型
                    pass
            
            return result
        except Exception as e:
            logger.warning(f"按 {attribute} 统计错误失败: {e}")
            return {}


# 单例模式
_exception_classifier = None

def get_exception_classifier() -> ExceptionClassifier:
    """获取异常分类器单例
    
    Returns:
        ExceptionClassifier: 异常分类器实例
    """
    global _exception_classifier
    if _exception_classifier is None:
        _exception_classifier = ExceptionClassifier()
    return _exception_classifier 