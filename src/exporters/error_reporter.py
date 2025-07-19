#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误聚合报告器

提供集中式的错误收集、分类和报告功能，用于验证和导出流程。
主要功能：
1. 聚合不同类型的错误和警告
2. 按严重性和类型分类错误
3. 生成结构化的错误报告
4. 提供多种格式的报告输出（JSON、文本、HTML等）
"""

import os
import json
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from enum import Enum, auto
import traceback

from src.utils.exceptions import ErrorCode, ClipMasterError, ValidationError
from src.utils.log_handler import get_logger

# 获取日志记录器
logger = get_logger("error_reporter")

class ErrorLevel(Enum):
    """错误级别枚举"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    
    @classmethod
    def from_string(cls, level_str: str) -> 'ErrorLevel':
        """从字符串转换为错误级别"""
        level_map = {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "critical": cls.CRITICAL
        }
        return level_map.get(level_str.lower(), cls.ERROR)

class ErrorCategory(Enum):
    """错误类别枚举"""
    VALIDATION = auto()       # 验证错误
    REFERENCE = auto()        # 引用错误
    TIMELINE = auto()         # 时间轴错误
    LEGAL = auto()            # 法律合规性错误
    FORMAT = auto()           # 格式错误
    RESOURCE = auto()         # 资源错误
    SYSTEM = auto()           # 系统错误
    USER = auto()             # 用户输入错误
    COMPATIBILITY = auto()    # 兼容性错误
    UNKNOWN = auto()          # 未知错误
    
    @classmethod
    def from_error_code(cls, error_code: ErrorCode) -> 'ErrorCategory':
        """从错误代码获取错误类别"""
        category_map = {
            ErrorCode.VALIDATION_ERROR: cls.VALIDATION,
            ErrorCode.FILE_NOT_FOUND: cls.RESOURCE,
            ErrorCode.PERMISSION_DENIED: cls.SYSTEM,
            ErrorCode.DEPENDENCY_ERROR: cls.SYSTEM,
            ErrorCode.MEMORY_ERROR: cls.RESOURCE,
            ErrorCode.MODEL_ERROR: cls.SYSTEM,
            ErrorCode.PROCESSING_ERROR: cls.SYSTEM,
            ErrorCode.FORMAT_ERROR: cls.FORMAT,
            ErrorCode.NETWORK_ERROR: cls.SYSTEM,
            ErrorCode.USER_INPUT_ERROR: cls.USER,
            ErrorCode.SYSTEM_ERROR: cls.SYSTEM,
            ErrorCode.TIMEOUT_ERROR: cls.SYSTEM,
            ErrorCode.CONFIG_ERROR: cls.VALIDATION
        }
        return category_map.get(error_code, cls.UNKNOWN)

class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, message: str, code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code or "VALIDATION_ERROR"
        self.msg = message
        self.context = context or {}
        self.critical = False

class ErrorInfo:
    """错误信息"""
    def __init__(self, 
                code: str, 
                message: str,
                level: Union[str, ErrorLevel] = ErrorLevel.ERROR,
                category: Union[str, ErrorCategory] = ErrorCategory.UNKNOWN,
                location: str = None,
                context: Dict[str, Any] = None,
                exception: Exception = None):
        """
        初始化错误信息
        
        Args:
            code: 错误代码
            message: 错误消息
            level: 错误级别
            category: 错误类别
            location: 错误位置（文件、行号等）
            context: 错误上下文信息
            exception: 原始异常对象
        """
        self.code = code
        self.message = message
        self.level = level if isinstance(level, ErrorLevel) else ErrorLevel.from_string(level)
        self.category = category if isinstance(category, ErrorCategory) else ErrorCategory.UNKNOWN
        self.location = location
        self.context = context or {}
        self.timestamp = datetime.datetime.now().isoformat()
        self.exception = exception
        self.traceback = None
        
        if exception:
            self.traceback = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        result = {
            "code": self.code,
            "message": self.message,
            "level": self.level.name,
            "category": self.category.name,
            "timestamp": self.timestamp
        }
        
        if self.location:
            result["location"] = self.location
        
        if self.context:
            result["context"] = self.context
        
        if self.traceback:
            result["traceback"] = "".join(self.traceback)
        
        return result
    
    @classmethod
    def from_exception(cls, error: Exception, context: Dict[str, Any] = None) -> 'ErrorInfo':
        """从异常创建错误信息"""
        if isinstance(error, ClipMasterError):
            code = error.code.name if hasattr(error, 'code') else "UNKNOWN_ERROR"
            message = str(error)
            level = ErrorLevel.CRITICAL if getattr(error, 'critical', False) else ErrorLevel.ERROR
            category = ErrorCategory.from_error_code(error.code) if hasattr(error, 'code') else ErrorCategory.UNKNOWN
            
            # 提取位置信息（如果有）
            location = None
            if hasattr(error, 'file_path'):
                location = error.file_path
            
            # 合并上下文
            error_context = getattr(error, 'details', {}) or {}
            merged_context = {**error_context, **(context or {})}
            
            return cls(
                code=code,
                message=message,
                level=level,
                category=category,
                location=location,
                context=merged_context,
                exception=error
            )
        elif isinstance(error, ValidationError):
            return cls(
                code=error.code,
                message=error.msg,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.VALIDATION,
                context=error.context,
                exception=error
            )
        else:
            # 通用异常处理
            return cls(
                code="GENERAL_ERROR",
                message=str(error),
                level=ErrorLevel.ERROR,
                category=ErrorCategory.UNKNOWN,
                context=context,
                exception=error
            )

class ValidationResult:
    """验证结果"""
    def __init__(self):
        """初始化验证结果"""
        self.errors = []
        self.warnings = []
        self.infos = []
        self.error_categories = set()
        self.has_critical = False
        self.validation_context = {}
        self.start_time = time.time()
        self.end_time = None
    
    def add_error(self, error: Union[Exception, ErrorInfo, Dict, str]) -> None:
        """
        添加错误信息
        
        按严重性分类存储错误，并记录错误类型
        
        Args:
            error: 错误对象，可以是异常、ErrorInfo、字典或字符串
        """
        # 将各种格式的错误标准化为ErrorInfo对象
        error_info = self._normalize_error(error)
        
        # 按级别分类存储
        if error_info.level == ErrorLevel.WARNING:
            self.warnings.append(error_info)
        elif error_info.level in [ErrorLevel.INFO, ErrorLevel.DEBUG]:
            self.infos.append(error_info)
        else:  # ERROR 或 CRITICAL
            self.errors.append(error_info)
            if error_info.level == ErrorLevel.CRITICAL:
                self.has_critical = True
        
        # 记录错误类别
        self.error_categories.add(error_info.category)
        
        # 记录到日志
        if error_info.level == ErrorLevel.DEBUG:
            logger.debug(f"{error_info.code}: {error_info.message}")
        elif error_info.level == ErrorLevel.INFO:
            logger.info(f"{error_info.code}: {error_info.message}")
        elif error_info.level == ErrorLevel.WARNING:
            logger.warning(f"{error_info.code}: {error_info.message}")
        elif error_info.level == ErrorLevel.ERROR:
            logger.error(f"{error_info.code}: {error_info.message}")
        elif error_info.level == ErrorLevel.CRITICAL:
            logger.critical(f"{error_info.code}: {error_info.message}")
    
    def _normalize_error(self, error: Union[Exception, ErrorInfo, Dict, str]) -> ErrorInfo:
        """将各种格式的错误标准化为ErrorInfo对象"""
        if isinstance(error, ErrorInfo):
            return error
        elif isinstance(error, Exception):
            return ErrorInfo.from_exception(error, self.validation_context)
        elif isinstance(error, dict):
            # 从字典创建ErrorInfo
            return ErrorInfo(
                code=error.get("code", "UNKNOWN_ERROR"),
                message=error.get("message", str(error)),
                level=error.get("level", "ERROR"),
                category=error.get("category", ErrorCategory.UNKNOWN),
                location=error.get("location"),
                context=error.get("context")
            )
        elif isinstance(error, str):
            # 从字符串创建基本ErrorInfo
            return ErrorInfo(
                code="GENERAL_ERROR",
                message=error,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.UNKNOWN,
                context=self.validation_context
            )
        else:
            # 未知类型，转为字符串处理
            return ErrorInfo(
                code="UNKNOWN_ERROR_TYPE",
                message=f"Unknown error type: {type(error).__name__}, value: {str(error)}",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.UNKNOWN,
                context=self.validation_context
            )
    
    @property
    def is_valid(self) -> bool:
        """验证是否通过（没有错误）"""
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def set_context(self, **kwargs) -> None:
        """设置验证上下文"""
        self.validation_context.update(kwargs)
    
    def complete(self) -> None:
        """完成验证，记录结束时间"""
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """获取验证持续时间（秒）"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def get_error_summary(self) -> Dict[str, int]:
        """获取错误类型摘要统计"""
        summary = {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "total_infos": len(self.infos)
        }
        
        # 按类别统计
        category_counts = {}
        for error in self.errors:
            category = error.category.name
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 按级别统计
        level_counts = {}
        for error in self.errors + self.warnings + self.infos:
            level = error.level.name
            level_counts[level] = level_counts.get(level, 0) + 1
        
        summary["by_category"] = category_counts
        summary["by_level"] = level_counts
        
        return summary
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """获取详细报告"""
        self.complete()  # 确保结束时间已设置
        
        # 基本信息
        report = {
            "valid": self.is_valid,
            "has_warnings": self.has_warnings,
            "has_critical": self.has_critical,
            "duration": self.duration,
            "start_time": datetime.datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.infos),
            "context": self.validation_context,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "infos": [info.to_dict() for info in self.infos],
            "summary": self.get_error_summary()
        }
        
        return report
    
    def generate_report(self, format: str = "json", output_file: str = None) -> Union[str, Dict]:
        """
        生成格式化的报告
        
        Args:
            format: 报告格式，支持 "json", "text", "html", "dict"
            output_file: 输出文件路径，None表示不保存到文件
            
        Returns:
            格式化的报告字符串或字典
        """
        # 获取完整报告数据
        report_data = self.get_detailed_report()
        
        # 根据格式生成报告
        if format.lower() == "json":
            report = json.dumps(report_data, indent=2, ensure_ascii=False)
        elif format.lower() == "text":
            report = self._generate_text_report(report_data)
        elif format.lower() == "html":
            report = self._generate_html_report(report_data)
        elif format.lower() == "dict":
            report = report_data
        else:
            raise ValueError(f"不支持的报告格式: {format}")
        
        # 如果指定了输出文件，保存报告
        if output_file and format.lower() != "dict":
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report)
                logger.info(f"已保存报告到: {output_file}")
            except Exception as e:
                logger.error(f"保存报告时出错: {e}")
        
        return report
    
    def _generate_text_report(self, report_data: Dict[str, Any]) -> str:
        """生成文本格式的报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("验证报告")
        lines.append("=" * 60)
        
        # 基本信息
        valid_status = "通过" if report_data["valid"] else "失败"
        lines.append(f"验证状态: {valid_status}")
        lines.append(f"执行时间: {report_data['duration']:.3f} 秒")
        lines.append(f"开始时间: {report_data['start_time']}")
        lines.append(f"结束时间: {report_data['end_time']}")
        lines.append(f"错误数量: {report_data['error_count']}")
        lines.append(f"警告数量: {report_data['warning_count']}")
        lines.append(f"信息数量: {report_data['info_count']}")
        
        # 上下文信息
        if report_data['context']:
            lines.append("\n上下文信息:")
            for key, value in report_data['context'].items():
                lines.append(f"  {key}: {value}")
        
        # 错误详情
        if report_data['errors']:
            lines.append("\n错误详情:")
            for i, error in enumerate(report_data['errors'], 1):
                lines.append(f"  {i}. [{error['level']}] {error['code']}: {error['message']}")
                if 'location' in error:
                    lines.append(f"     位置: {error['location']}")
        
        # 警告详情
        if report_data['warnings']:
            lines.append("\n警告详情:")
            for i, warning in enumerate(report_data['warnings'], 1):
                lines.append(f"  {i}. [{warning['level']}] {warning['code']}: {warning['message']}")
                if 'location' in warning:
                    lines.append(f"     位置: {warning['location']}")
        
        # 摘要统计
        summary = report_data['summary']
        lines.append("\n错误摘要:")
        lines.append(f"  总错误: {summary['total_errors']}")
        lines.append(f"  总警告: {summary['total_warnings']}")
        lines.append(f"  总信息: {summary['total_infos']}")
        
        if 'by_category' in summary and summary['by_category']:
            lines.append("\n  按类别:")
            for category, count in summary['by_category'].items():
                lines.append(f"    {category}: {count}")
        
        if 'by_level' in summary and summary['by_level']:
            lines.append("\n  按级别:")
            for level, count in summary['by_level'].items():
                lines.append(f"    {level}: {count}")
        
        return "\n".join(lines)
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """生成HTML格式的报告"""
        valid_class = "success" if report_data["valid"] else "danger"
        valid_status = "通过" if report_data["valid"] else "失败"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>验证报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .success {{ color: green; }}
        .danger {{ color: red; }}
        .warning {{ color: orange; }}
        .info {{ color: blue; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .section {{ margin-bottom: 20px; }}
        h2 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>验证报告</h1>
        <p>验证状态: <span class="{valid_class}">{valid_status}</span></p>
        <p>执行时间: {report_data['duration']:.3f} 秒</p>
        <p>开始时间: {report_data['start_time']}</p>
        <p>结束时间: {report_data['end_time']}</p>
        <p>错误数量: {report_data['error_count']}</p>
        <p>警告数量: {report_data['warning_count']}</p>
        <p>信息数量: {report_data['info_count']}</p>
    </div>
"""
        
        # 上下文信息
        if report_data['context']:
            html += """
    <div class="section">
        <h2>上下文信息</h2>
        <table>
            <tr><th>键</th><th>值</th></tr>
"""
            for key, value in report_data['context'].items():
                html += f"""
            <tr><td>{key}</td><td>{value}</td></tr>
"""
            html += """
        </table>
    </div>
"""
        
        # 错误详情
        if report_data['errors']:
            html += """
    <div class="section">
        <h2>错误详情</h2>
        <table>
            <tr><th>#</th><th>级别</th><th>代码</th><th>消息</th><th>位置</th></tr>
"""
            for i, error in enumerate(report_data['errors'], 1):
                location = error.get('location', '')
                html += f"""
            <tr class="danger">
                <td>{i}</td>
                <td>{error['level']}</td>
                <td>{error['code']}</td>
                <td>{error['message']}</td>
                <td>{location}</td>
            </tr>
"""
            html += """
        </table>
    </div>
"""
        
        # 警告详情
        if report_data['warnings']:
            html += """
    <div class="section">
        <h2>警告详情</h2>
        <table>
            <tr><th>#</th><th>级别</th><th>代码</th><th>消息</th><th>位置</th></tr>
"""
            for i, warning in enumerate(report_data['warnings'], 1):
                location = warning.get('location', '')
                html += f"""
            <tr class="warning">
                <td>{i}</td>
                <td>{warning['level']}</td>
                <td>{warning['code']}</td>
                <td>{warning['message']}</td>
                <td>{location}</td>
            </tr>
"""
            html += """
        </table>
    </div>
"""
        
        # 摘要统计
        summary = report_data['summary']
        html += """
    <div class="summary">
        <h2>错误摘要</h2>
        <p>总错误: {0}</p>
        <p>总警告: {1}</p>
        <p>总信息: {2}</p>
        
""".format(summary['total_errors'], summary['total_warnings'], summary['total_infos'])
        
        if 'by_category' in summary and summary['by_category']:
            html += """
        <h3>按类别</h3>
        <table>
            <tr><th>类别</th><th>数量</th></tr>
"""
            for category, count in summary['by_category'].items():
                html += f"""
            <tr><td>{category}</td><td>{count}</td></tr>
"""
            html += """
        </table>
"""
        
        if 'by_level' in summary and summary['by_level']:
            html += """
        <h3>按级别</h3>
        <table>
            <tr><th>级别</th><th>数量</th></tr>
"""
            for level, count in summary['by_level'].items():
                html += f"""
            <tr><td>{level}</td><td>{count}</td></tr>
"""
            html += """
        </table>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return html

# 便捷函数

def create_validation_result() -> ValidationResult:
    """创建一个新的验证结果对象"""
    return ValidationResult()

def generate_error_report(errors: List[Union[Exception, Dict, str]], 
                         format: str = "json",
                         output_file: str = None,
                         context: Dict[str, Any] = None) -> Union[str, Dict]:
    """
    从错误列表生成报告
    
    Args:
        errors: 错误列表
        format: 报告格式，支持 "json", "text", "html", "dict"
        output_file: 输出文件路径，None表示不保存到文件
        context: 上下文信息
    
    Returns:
        格式化的报告
    """
    result = ValidationResult()
    
    if context:
        result.set_context(**context)
    
    for error in errors:
        result.add_error(error)
    
    return result.generate_report(format, output_file)

def combine_validation_results(*results: ValidationResult) -> ValidationResult:
    """
    合并多个验证结果
    
    Args:
        *results: 要合并的验证结果对象
    
    Returns:
        合并后的验证结果
    """
    combined = ValidationResult()
    
    for result in results:
        # 合并错误、警告和信息
        for error in result.errors:
            combined.errors.append(error)
        for warning in result.warnings:
            combined.warnings.append(warning)
        for info in result.infos:
            combined.infos.append(info)
        
        # 合并错误类别
        combined.error_categories.update(result.error_categories)
        
        # 更新关键标志
        if result.has_critical:
            combined.has_critical = True
        
        # 合并上下文（优先保留先前的值）
        for key, value in result.validation_context.items():
            if key not in combined.validation_context:
                combined.validation_context[key] = value
    
    # 使用最早的开始时间
    combined.start_time = min(r.start_time for r in results)
    
    # 使用最晚的结束时间
    end_times = [r.end_time for r in results if r.end_time is not None]
    if end_times:
        combined.end_time = max(end_times)
    
    return combined

if __name__ == "__main__":
    # 测试代码
    from src.utils.exceptions import ValidationError
    
    # 创建验证结果
    result = ValidationResult()
    
    # 添加一些错误
    result.add_error(ValidationError("测试验证错误", field="username", value="admin"))
    result.add_error({
        "code": "FORMAT_ERROR",
        "message": "JSON格式错误",
        "level": "ERROR",
        "category": ErrorCategory.FORMAT,
        "location": "config.json:25"
    })
    result.add_error("这是一个字符串错误")
    
    # 添加警告
    result.add_error({
        "code": "TIMELINE_WARNING",
        "message": "时间轴可能存在空隙",
        "level": "WARNING",
        "category": ErrorCategory.TIMELINE,
        "location": "timeline.xml:42"
    })
    
    # 设置上下文
    result.set_context(filename="test.json", operation="validate")
    
    # 生成报告
    print(result.generate_report("text")) 