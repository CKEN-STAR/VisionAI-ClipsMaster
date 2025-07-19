#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误日志系统与异常分类系统集成模块

提供智能错误日志系统与异常分类系统的无缝集成，实现更高级的错误分析和处理能力。
主要功能：
1. 自动将错误日志与异常分类系统关联
2. 根据异常分类提供智能恢复建议
3. 错误模式分析与预测
4. 自动化的错误报告和统计
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
import threading
import json
import datetime
import time

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.exporters.error_logger import ExportLogger, get_export_logger, with_error_logging
from src.utils.log_handler import get_logger

# 尝试导入错误消息系统
try:
    from src.exporters.error_messages import get_error_message, format_error
    ERROR_MESSAGES_AVAILABLE = True
except ImportError:
    ERROR_MESSAGES_AVAILABLE = False

# 尝试导入异常分类系统
try:
    from src.utils.exception_classifier import (
        get_exception_classifier,
        classify_exception,
        SeverityLevel,
        ErrorSource,
        ExceptionClassification
    )
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False

# 获取日志记录器
logger = get_logger("error_logger_integration")


class IntegratedErrorLogger:
    """集成了异常分类系统的错误日志记录器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(IntegratedErrorLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """初始化集成日志记录器"""
        if getattr(self, '_initialized', False):
            return
            
        # 获取基础错误日志记录器
        self.logger = get_export_logger()
        
        # 检查异常分类系统是否可用
        self.classifier_available = CLASSIFIER_AVAILABLE
        if self.classifier_available:
            try:
                self.classifier = get_exception_classifier()
                logger.info("已成功集成异常分类系统")
            except Exception as e:
                logger.warning(f"异常分类系统初始化失败: {e}")
                self.classifier_available = False
        else:
            logger.warning("异常分类系统不可用，将使用基本错误日志功能")
        
        # 检查错误消息系统是否可用
        self.error_messages_available = ERROR_MESSAGES_AVAILABLE
        if self.error_messages_available:
            logger.info("已成功集成错误消息系统")
        else:
            logger.warning("错误消息系统不可用，将使用默认错误消息")
            
        # 恢复策略映射
        self.recovery_strategies = {}
        
        # 初始化完成
        self._initialized = True
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """注册错误恢复策略
        
        Args:
            error_type: 错误类型或模式
            strategy: 恢复策略函数，接收错误和上下文作为参数
        """
        self.recovery_strategies[error_type] = strategy
        logger.info(f"注册恢复策略: {error_type} -> {strategy.__name__}")
    
    def log_with_classification(self, error: Exception, phase: str = None, 
                               video_hash: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """记录带有分类信息的错误
        
        Args:
            error: 错误对象
            phase: 当前阶段
            video_hash: 当前视频哈希
            context: 额外上下文
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        context = context or {}
        
        # 设置上下文
        if phase or video_hash:
            self.logger.set_context(phase, video_hash)
        
        # 尝试使用异常分类系统
        if self.classifier_available:
            try:
                # 分类异常
                classification = classify_exception(error, context)
                
                # 添加分类信息到上下文
                context["classification"] = {
                    "severity": classification.severity.name,
                    "source": classification.source.name,
                    "error_type": classification.error_type,
                    "confidence": classification.confidence,
                    "recovery_chance": classification.recovery_chance,
                    "description": classification.description
                }
                
                # 根据严重性级别调整日志级别
                if classification.severity == SeverityLevel.CRITICAL:
                    logger.critical(f"严重错误: {str(error)}")
                elif classification.severity == SeverityLevel.HIGH:
                    logger.error(f"高级错误: {str(error)}")
                
                # 尝试应用恢复策略
                if classification.recovery_chance > 0.5:
                    self._try_recovery(error, classification, context)
            except Exception as e:
                logger.warning(f"错误分类失败: {e}")
                # 添加分类失败信息到上下文
                context["classification_error"] = str(e)
        
        # 尝试获取用户友好错误消息
        if self.error_messages_available:
            try:
                # 获取中英文错误消息
                zh_message = get_error_message(error, "zh")
                en_message = get_error_message(error, "en")
                
                # 添加到上下文
                context["user_messages"] = {
                    "zh": zh_message,
                    "en": en_message
                }
            except Exception as e:
                logger.warning(f"生成用户友好错误消息失败: {e}")
                context["error_message_error"] = str(e)
        
        # 记录错误
        return self.logger.log_structured_error(error, context)
    
    def _try_recovery(self, error: Exception, classification: 'ExceptionClassification', 
                     context: Dict[str, Any]) -> bool:
        """尝试应用恢复策略
        
        Args:
            error: 错误对象
            classification: 异常分类
            context: 上下文信息
            
        Returns:
            bool: 是否成功恢复
        """
        # 查找匹配的恢复策略
        for error_type, strategy in self.recovery_strategies.items():
            if error_type == classification.error_type or (
                hasattr(error, "__class__") and error.__class__.__name__ == error_type
            ):
                try:
                    # 标记为恢复尝试
                    context["recovery_attempt"] = True
                    context["recovery_strategy"] = strategy.__name__
                    
                    # 应用恢复策略
                    start_time = time.time()
                    result = strategy(error, context)
                    duration = time.time() - start_time
                    
                    # 记录恢复结果
                    context["recovery_result"] = {
                        "success": bool(result),
                        "duration": duration
                    }
                    
                    logger.info(f"恢复策略 '{strategy.__name__}' 应用于错误类型 '{error_type}': {'成功' if result else '失败'}")
                    return bool(result)
                except Exception as recovery_error:
                    logger.error(f"恢复策略执行失败: {recovery_error}")
                    context["recovery_error"] = str(recovery_error)
                    return False
        
        logger.info(f"未找到匹配的恢复策略: {classification.error_type}")
        return False
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """分析错误模式
        
        Returns:
            Dict[str, Any]: 错误模式分析结果
        """
        # 获取基础统计
        stats = self.logger.get_error_stats()
        
        # 添加分类统计
        if self.classifier_available:
            # 从日志文件读取错误
            logs = []
            if os.path.exists(self.logger.log_file):
                try:
                    with open(self.logger.log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except Exception:
                    pass
            
            # 按分类统计错误
            classification_stats = {}
            for log in logs:
                if "context" in log and "classification" in log["context"]:
                    classification = log["context"]["classification"]
                    severity = classification.get("severity", "UNKNOWN")
                    source = classification.get("source", "UNKNOWN")
                    error_type = classification.get("error_type", "UNKNOWN")
                    
                    # 更新统计
                    if severity not in classification_stats:
                        classification_stats[severity] = {"count": 0, "sources": {}, "types": {}}
                    
                    classification_stats[severity]["count"] += 1
                    
                    # 更新来源统计
                    if source not in classification_stats[severity]["sources"]:
                        classification_stats[severity]["sources"][source] = 0
                    classification_stats[severity]["sources"][source] += 1
                    
                    # 更新类型统计
                    if error_type not in classification_stats[severity]["types"]:
                        classification_stats[severity]["types"][error_type] = 0
                    classification_stats[severity]["types"][error_type] += 1
            
            # 添加到结果
            stats["classification"] = classification_stats
        
        return stats
    
    def get_user_message(self, error: Exception, lang: str = "zh") -> str:
        """获取用户友好的错误消息
        
        Args:
            error: 错误对象
            lang: 语言代码 ('zh'为中文, 'en'为英文)
            
        Returns:
            str: 用户友好的错误消息
        """
        if self.error_messages_available:
            try:
                return get_error_message(error, lang)
            except Exception as e:
                logger.warning(f"获取用户友好错误消息失败: {e}")
        
        # 降级到简单错误消息
        if lang == "zh":
            return f"程序错误: {str(error)}"
        else:
            return f"Application error: {str(error)}"
    
    def generate_advanced_report(self, format: str = "html", output_file: str = None) -> Optional[str]:
        """生成高级错误报告
        
        Args:
            format: 报告格式 ("html", "json", "md")
            output_file: 输出文件路径
            
        Returns:
            Optional[str]: 如果未指定输出文件，则返回报告内容
        """
        # 分析错误模式
        analysis = self.analyze_error_patterns()
        
        # 获取当前时间
        now = datetime.datetime.now().isoformat()
        
        if format == "json":
            # JSON格式报告
            report = {
                "generated_at": now,
                "summary": analysis,
                "details": self.logger.pending_logs,
            }
            output = json.dumps(report, indent=2, ensure_ascii=False)
        
        elif format == "md":
            # Markdown格式报告
            parts = [
                "# 错误报告分析\n",
                f"生成时间: {now}\n",
                "\n## 错误统计\n",
                f"- 总错误数: {analysis['total_errors']}\n",
                f"- 独立错误数: {analysis['unique_errors']}\n",
                "\n## 最常见错误\n"
            ]
            
            for error_hash, count in analysis.get("most_frequent", {}).items():
                parts.append(f"- {error_hash}: {count}次\n")
            
            # 添加分类统计
            if "classification" in analysis:
                parts.append("\n## 按严重性分类\n")
                for severity, data in analysis["classification"].items():
                    parts.append(f"\n### {severity} ({data['count']}次)\n")
                    
                    # 添加来源
                    parts.append("\n#### 错误来源\n")
                    for source, count in data["sources"].items():
                        parts.append(f"- {source}: {count}次\n")
                    
                    # 添加类型
                    parts.append("\n#### 错误类型\n")
                    for error_type, count in data["types"].items():
                        parts.append(f"- {error_type}: {count}次\n")
            
            output = "".join(parts)
            
        else:  # html
            # HTML格式报告
            parts = [
                '<!DOCTYPE html><html><head><meta charset="utf-8">',
                '<title>高级错误报告</title>',
                '<style>',
                'body{font-family:Arial,sans-serif;line-height:1.6;max-width:1200px;margin:0 auto;padding:20px;color:#333}',
                'h1,h2,h3{color:#444}',
                'table{border-collapse:collapse;width:100%;margin-bottom:20px}',
                'th,td{text-align:left;padding:12px;border-bottom:1px solid #ddd}',
                'th{background-color:#f8f8f8;font-weight:bold}',
                'tr:hover{background-color:#f5f5f5}',
                '.critical{color:#d32f2f}',
                '.high{color:#f57c00}',
                '.medium{color:#fbc02d}',
                '.low{color:#388e3c}',
                '.chart{height:200px;margin:20px 0}',
                '.user-message{padding:10px;background:#f0f0f0;border-left:4px solid #2196f3;margin:10px 0;}',
                '</style>',
                '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
                '</head><body>',
                f'<h1>高级错误报告</h1>',
                f'<p>生成时间: {now}</p>',
                '<div style="display:flex;justify-content:space-between">',
                '<div style="width:48%">',
                '<h2>错误统计</h2>',
                '<table>',
                '<tr><th>指标</th><th>值</th></tr>',
                f'<tr><td>总错误数</td><td>{analysis["total_errors"]}</td></tr>',
                f'<tr><td>独立错误数</td><td>{analysis["unique_errors"]}</td></tr>',
                '</table>',
                
                '<h2>最常见错误</h2>',
                '<table>',
                '<tr><th>错误哈希</th><th>出现次数</th></tr>'
            ]
            
            for error_hash, count in analysis.get("most_frequent", {}).items():
                parts.append(f'<tr><td>{error_hash}</td><td>{count}</td></tr>')
            
            parts.append('</table></div>')
            
            # 添加分类统计
            if "classification" in analysis:
                parts.append('<div style="width:48%"><h2>按严重性分类</h2>')
                
                # 饼图容器
                parts.append('<div class="chart"><canvas id="severityChart"></canvas></div>')
                
                # 表格
                parts.append('<table><tr><th>严重性</th><th>次数</th></tr>')
                
                severity_data = []
                for severity, data in analysis["classification"].items():
                    severity_class = severity.lower()
                    parts.append(f'<tr><td class="{severity_class}">{severity}</td><td>{data["count"]}</td></tr>')
                    severity_data.append({"severity": severity, "count": data["count"]})
                
                parts.append('</table>')
                
                # 添加JavaScript用于生成图表
                parts.append('</div></div>')
                parts.append('<script>')
                parts.append('document.addEventListener("DOMContentLoaded", function() {')
                parts.append('  const severityCtx = document.getElementById("severityChart").getContext("2d");')
                parts.append('  const severityData = ' + json.dumps(severity_data) + ';')
                parts.append('  new Chart(severityCtx, {')
                parts.append('    type: "pie",')
                parts.append('    data: {')
                parts.append('      labels: severityData.map(item => item.severity),')
                parts.append('      datasets: [{')
                parts.append('        data: severityData.map(item => item.count),')
                parts.append('        backgroundColor: [')
                parts.append('          "#d32f2f", "#f57c00", "#fbc02d", "#388e3c", "#1976d2"')
                parts.append('        ]')
                parts.append('      }]')
                parts.append('    }')
                parts.append('  });')
                parts.append('});')
                parts.append('</script>')
                
                # 详细分类统计
                parts.append('<h2>详细错误分类</h2>')
                for severity, data in analysis["classification"].items():
                    severity_class = severity.lower()
                    parts.append(f'<h3 class="{severity_class}">{severity} ({data["count"]}次)</h3>')
                    
                    # 错误来源
                    parts.append('<h4>错误来源</h4><table><tr><th>来源</th><th>次数</th></tr>')
                    for source, count in data["sources"].items():
                        parts.append(f'<tr><td>{source}</td><td>{count}</td></tr>')
                    parts.append('</table>')
                    
                    # 错误类型
                    parts.append('<h4>错误类型</h4><table><tr><th>类型</th><th>次数</th></tr>')
                    for error_type, count in data["types"].items():
                        parts.append(f'<tr><td>{error_type}</td><td>{count}</td></tr>')
                    parts.append('</table>')
            
            # 添加用户友好错误消息部分
            if self.error_messages_available:
                parts.append('<h2>用户友好错误消息示例</h2>')
                parts.append('<table>')
                parts.append('<tr><th>错误码</th><th>中文</th><th>英文</th></tr>')
                
                # 获取一些常见错误代码的消息
                common_codes = ['0xE100', '0xE200', '0xE400', '0xE600', '0xE700']
                for code in common_codes:
                    try:
                        from src.exporters.error_messages import generate_user_message
                        zh_msg = generate_user_message(code, 'zh')
                        en_msg = generate_user_message(code, 'en')
                        parts.append(f'<tr><td>{code}</td><td class="user-message">{zh_msg}</td><td class="user-message">{en_msg}</td></tr>')
                    except Exception:
                        pass
                
                parts.append('</table>')
            
            parts.append('</body></html>')
            output = ''.join(parts)
        
        # 输出到文件或返回
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"高级错误报告已导出到: {output_file}")
            return None
        else:
            return output


# 单例访问函数
def get_integrated_logger() -> IntegratedErrorLogger:
    """获取集成日志记录器单例
    
    Returns:
        IntegratedErrorLogger: 集成日志记录器实例
    """
    return IntegratedErrorLogger()


# 辅助函数：记录分类错误
def log_classified_error(error: Exception, phase: str = None, 
                       video_hash: str = None, context: Dict[str, Any] = None) -> None:
    """记录带有分类的错误
    
    Args:
        error: 错误对象
        phase: 当前阶段
        video_hash: 当前视频哈希
        context: 额外上下文
    """
    logger = get_integrated_logger()
    logger.log_with_classification(error, phase, video_hash, context)


# 辅助函数：记录分类错误并返回用户友好消息
def log_and_get_user_message(error: Exception, phase: str = None, 
                           video_hash: str = None, lang: str = "zh") -> str:
    """记录带有分类的错误并返回用户友好消息
    
    Args:
        error: 错误对象
        phase: 当前阶段
        video_hash: 当前视频哈希
        lang: 语言代码
        
    Returns:
        str: 用户友好的错误消息
    """
    logger = get_integrated_logger()
    # 记录错误
    logger.log_with_classification(error, phase, video_hash)
    # 返回用户友好消息
    return logger.get_user_message(error, lang)


# 装饰器：带分类的错误日志记录
def with_classified_logging(phase: str = None):
    """为函数添加带分类的错误日志记录
    
    Args:
        phase: 导出阶段名称
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_integrated_logger()
            
            # 尝试提取视频哈希
            video_hash = None
            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, dict) and "video_hash" in arg:
                    video_hash = arg["video_hash"]
                    break
                elif hasattr(arg, "video_hash"):
                    video_hash = arg.video_hash
                    break
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 记录带分类的错误
                logger.log_with_classification(e, phase, video_hash)
                # 重新抛出异常
                raise
        
        return wrapper
    
    return decorator


# 常见错误的恢复策略示例
def memory_error_recovery(error: Exception, context: Dict[str, Any]) -> bool:
    """内存错误恢复策略
    
    Args:
        error: 错误对象
        context: 上下文信息
        
    Returns:
        bool: 是否成功恢复
    """
    import gc
    
    # 强制垃圾回收
    gc.collect()
    
    # 尝试减少内存使用
    for i in range(3):
        gc.collect()
        
    logger.info("已执行内存恢复策略: 强制垃圾回收")
    return True


# 初始化：注册默认恢复策略
def initialize_error_recovery():
    """初始化错误恢复系统"""
    integrated_logger = get_integrated_logger()
    
    # 注册内存错误恢复策略
    integrated_logger.register_recovery_strategy("MemoryError", memory_error_recovery)
    
    # 注册其他通用恢复策略
    if integrated_logger.classifier_available:
        # 注册基于分类的恢复策略
        try:
            # 可以从配置文件加载额外的恢复策略
            logger.info("已初始化错误恢复系统")
        except Exception as e:
            logger.warning(f"初始化错误恢复系统失败: {e}") 