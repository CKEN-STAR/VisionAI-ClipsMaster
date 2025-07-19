#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志审计报告生成器

生成符合GDPR和中国个人信息保护法的合规审计报告。
提供数据处理活动、数据主体操作和安全事件的详细记录。
支持多种报告格式和定制化输出。
"""

import os
import sys
import json
import time
import datetime
import hashlib
import hmac
import base64
import re
import csv
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set

# 导入日志查询和处理模块
from src.utils.logger import get_module_logger
from src.exporters.log_query import LogSearcher, get_log_searcher
from src.exporters.log_path import get_log_directory
from src.exporters.structured_logger import get_structured_logger
from src.exporters.legal_logger import LegalAuditLogger, get_legal_logger

# 模块日志记录器
logger = get_module_logger("log_audit")

# 数据处理状态枚举
class DataProcessingStatus(Enum):
    """数据处理状态枚举"""
    ACTIVE = "active"            # 活跃处理
    ARCHIVED = "archived"        # 已归档
    ANONYMIZED = "anonymized"    # 已匿名化
    DELETED = "deleted"          # 已删除
    SUSPENDED = "suspended"      # 已暂停
    
# 安全事件类型枚举
class SecurityIncidentType(Enum):
    """安全事件类型枚举"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"    # 未授权访问
    DATA_BREACH = "data_breach"                    # 数据泄露
    TECHNICAL_ISSUE = "technical_issue"            # 技术问题
    CONFIGURATION_ERROR = "configuration_error"    # 配置错误
    SUSPICIOUS_ACTIVITY = "suspicious_activity"    # 可疑活动
    OTHER = "other"                                # 其他

class AuditReportGenerator:
    """审计报告生成器
    
    生成合规审计报告，提供数据处理活动、数据主体操作和安全事件的详细记录。
    支持GDPR和中国个人信息保护法的要求。
    """
    
    def __init__(self):
        """初始化审计报告生成器"""
        # 获取日志查询器
        self.log_searcher = get_log_searcher()
        
        # 获取结构化日志记录器
        self.structured_logger = get_structured_logger()
        
        # 获取法律审计日志记录器
        self.legal_logger = get_legal_logger()
        
        # 报告签名密钥
        self._report_key = os.environ.get("AUDIT_REPORT_KEY", "VisionAI-ClipsMaster-Audit-Key")
        
    def generate_audit_report(self, 
                            start_date: Union[str, datetime.datetime, datetime.date], 
                            end_date: Union[str, datetime.datetime, datetime.date],
                            report_type: str = "gdpr",
                            output_format: str = "json",
                            include_details: bool = True) -> Dict[str, Any]:
        """
        生成审计报告
        
        Args:
            start_date: 报告开始日期
            end_date: 报告结束日期
            report_type: 报告类型 ('gdpr', 'pipl', 'all')
            output_format: 输出格式 ('json', 'csv', 'text')
            include_details: 是否包含详细信息
            
        Returns:
            生成的审计报告
        """
        # 转换日期为datetime对象
        start_date_dt = self._normalize_date(start_date)
        end_date_dt = self._normalize_date(end_date)
        
        # 记录生成审计报告的操作
        logger.info(f"生成审计报告: {start_date_dt} 至 {end_date_dt}, 类型: {report_type}")
        
        # 构建基本报告结构
        report = {
            "period": f"{start_date_dt.isoformat()} 至 {end_date_dt.isoformat()}",
            "generation_time": datetime.datetime.now().isoformat(),
            "report_type": report_type,
            "operations": self._count_operations(start_date_dt, end_date_dt),
            "data_subjects": self._list_masked_users(start_date_dt, end_date_dt),
            "security_incidents": self._list_security_events(start_date_dt, end_date_dt),
            "data_processing_activities": self._list_data_processing(start_date_dt, end_date_dt),
            "legal_compliance_actions": self._list_legal_actions(start_date_dt, end_date_dt),
        }
        
        # 添加详细信息（如果需要）
        if include_details:
            report["details"] = {
                "operations_detail": self._get_operations_detail(start_date_dt, end_date_dt),
                "security_incidents_detail": self._get_security_incidents_detail(start_date_dt, end_date_dt),
                "data_subject_rights": self._get_data_subject_rights(start_date_dt, end_date_dt),
            }
        
        # 生成报告摘要
        report["summary"] = self._generate_summary(report)
        
        # 计算报告指纹和签名
        report_json = json.dumps(report, ensure_ascii=False, sort_keys=True)
        report["fingerprint"] = hashlib.sha256(report_json.encode('utf-8')).hexdigest()
        report["signature"] = self._sign_report(report["fingerprint"])
        
        # 根据输出格式转换报告
        if output_format == "json":
            return report
        elif output_format == "csv":
            return self._report_to_csv(report)
        elif output_format == "text":
            return self._report_to_text(report)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _normalize_date(self, date_obj: Union[str, datetime.datetime, datetime.date]) -> datetime.datetime:
        """
        规范化日期对象
        
        Args:
            date_obj: 日期对象（字符串或datetime对象）
            
        Returns:
            规范化的datetime对象
        """
        if isinstance(date_obj, str):
            # 尝试解析不同格式的字符串
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f"
            ]
            
            for fmt in formats:
                try:
                    return datetime.datetime.strptime(date_obj, fmt)
                except ValueError:
                    continue
                    
            raise ValueError(f"无法解析日期字符串: {date_obj}")
            
        elif isinstance(date_obj, datetime.date) and not isinstance(date_obj, datetime.datetime):
            # 如果是date但不是datetime，转换为datetime
            return datetime.datetime.combine(date_obj, datetime.time.min)
            
        elif isinstance(date_obj, datetime.datetime):
            return date_obj
            
        else:
            raise TypeError(f"不支持的日期类型: {type(date_obj)}")
    
    def _count_operations(self, start_date: datetime.datetime, 
                         end_date: datetime.datetime) -> Dict[str, int]:
        """
        统计操作数量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            操作统计字典
        """
        # 查询日志
        date_query = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        logs = self.log_searcher.search(date_query, limit=10000)
        
        # 统计不同操作类型
        operation_counts = {}
        for log in logs:
            operation = log.get("operation", "unknown")
            if operation in operation_counts:
                operation_counts[operation] += 1
            else:
                operation_counts[operation] = 1
        
        # 添加总操作数
        operation_counts["total"] = sum(operation_counts.values())
        
        return operation_counts
    
    def _list_masked_users(self, start_date: datetime.datetime, 
                          end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        列出脱敏后的用户数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            脱敏用户数据列表
        """
        # 这里使用一个模拟实现，实际应用中应从日志中提取并脱敏用户数据
        return list_masked_users()
    
    def _list_security_events(self, start_date: datetime.datetime, 
                             end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        列出安全事件
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            安全事件列表
        """
        # 查询安全事件日志
        security_query = f"错误 或 警告 或 安全 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        security_logs = self.log_searcher.search(security_query, limit=1000)
        
        # 提取安全事件
        security_events = []
        for log in security_logs:
            if "error" in log or "warning" in log or "security" in log:
                event = {
                    "timestamp": log.get("timestamp", ""),
                    "type": self._classify_security_event(log),
                    "severity": log.get("level", "INFO"),
                    "description": log.get("message", "")[:200]  # 截断描述
                }
                security_events.append(event)
        
        return security_events
    
    def _classify_security_event(self, log_entry: Dict[str, Any]) -> str:
        """
        分类安全事件
        
        Args:
            log_entry: 日志条目
            
        Returns:
            安全事件类型
        """
        message = log_entry.get("message", "").lower()
        
        if any(term in message for term in ["unauthorized", "permission", "access denied"]):
            return SecurityIncidentType.UNAUTHORIZED_ACCESS.value
            
        if any(term in message for term in ["leak", "breach", "exposure", "disclosed"]):
            return SecurityIncidentType.DATA_BREACH.value
            
        # 优先检查配置错误 (优先级更高，放到其他技术问题之前)
        if any(term in message for term in ["config", "configuration", "setting", "configuration error"]):
            return SecurityIncidentType.CONFIGURATION_ERROR.value
            
        if any(term in message for term in ["error", "exception", "crash", "failed"]):
            return SecurityIncidentType.TECHNICAL_ISSUE.value
            
        if any(term in message for term in ["suspicious", "unusual", "anomaly"]):
            return SecurityIncidentType.SUSPICIOUS_ACTIVITY.value
            
        return SecurityIncidentType.OTHER.value
    
    def _list_data_processing(self, start_date: datetime.datetime, 
                             end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        列出数据处理活动
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            数据处理活动列表
        """
        # 这里使用模拟实现，实际应用中应从日志中提取数据处理活动
        return list_data_processing_activities()
    
    def _list_legal_actions(self, start_date: datetime.datetime, 
                          end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        列出法律合规操作
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            法律合规操作列表
        """
        # 获取法律审计日志
        legal_logs = self.legal_logger.export_logs(
            output_format="dict",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        # 转换为摘要格式
        legal_actions = []
        for log in legal_logs:
            action = {
                "timestamp": log.get("timestamp", ""),
                "operation_type": log.get("operation_type", ""),
                "status": log.get("status", ""),
                "details": log.get("details", {}).get("summary", "No details provided")
            }
            legal_actions.append(action)
            
        return legal_actions
    
    def _get_operations_detail(self, start_date: datetime.datetime, 
                              end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        获取操作详情
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            操作详情列表
        """
        # 查询操作日志
        date_query = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        logs = self.log_searcher.search(date_query, limit=1000, sort_by="timestamp")
        
        # 提取操作详情
        operations_detail = []
        for log in logs:
            if "operation" in log:
                detail = {
                    "timestamp": log.get("timestamp", ""),
                    "operation": log.get("operation", ""),
                    "result": log.get("result", ""),
                    "module": log.get("module", ""),
                    "resource_usage": self._extract_resource_usage(log)
                }
                operations_detail.append(detail)
        
        return operations_detail
    
    def _extract_resource_usage(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """
        提取资源使用情况
        
        Args:
            log_entry: 日志条目
            
        Returns:
            资源使用情况字典
        """
        resource_usage = {}
        
        # 尝试从不同字段提取资源使用情况
        if "resource_usage" in log_entry and isinstance(log_entry["resource_usage"], dict):
            resource_usage = log_entry["resource_usage"]
        else:
            # 尝试从消息中提取资源使用情况
            message = log_entry.get("message", "")
            
            # 尝试提取内存使用
            memory_match = re.search(r"memory[:\s]+([0-9.]+)\s*MB", message, re.IGNORECASE)
            if memory_match:
                resource_usage["memory_mb"] = float(memory_match.group(1))
                
            # 尝试提取CPU使用
            cpu_match = re.search(r"cpu[:\s]+([0-9.]+)%", message, re.IGNORECASE)
            if cpu_match:
                resource_usage["cpu_percent"] = float(cpu_match.group(1))
        
        return resource_usage
    
    def _get_security_incidents_detail(self, start_date: datetime.datetime, 
                                    end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        获取安全事件详情
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            安全事件详情列表
        """
        # 查询安全事件日志（优先获取错误和警告）
        security_logs = self.log_searcher.search("ERROR OR WARNING", limit=500, sort_by="timestamp")
        
        # 筛选时间范围内的日志
        start_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        
        filtered_logs = []
        for log in security_logs:
            try:
                log_time = self._parse_log_timestamp(log.get("timestamp", ""))
                if start_timestamp <= log_time <= end_timestamp:
                    filtered_logs.append(log)
            except (ValueError, TypeError):
                continue
        
        # 提取安全事件详情
        incidents_detail = []
        for log in filtered_logs:
            detail = {
                "timestamp": log.get("timestamp", ""),
                "level": log.get("level", ""),
                "module": log.get("module", ""),
                "message": log.get("message", ""),
                "error_code": log.get("error_code", ""),
                "exception": log.get("exception", ""),
                "resolution": log.get("resolution", ""),
                "type": self._classify_security_event(log)
            }
            incidents_detail.append(detail)
        
        return incidents_detail
    
    def _parse_log_timestamp(self, timestamp_str: str) -> float:
        """
        解析日志时间戳
        
        Args:
            timestamp_str: 时间戳字符串
            
        Returns:
            时间戳（秒）
        """
        if not timestamp_str:
            raise ValueError("空时间戳")
            
        # 尝试解析ISO格式时间戳
        try:
            dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except ValueError:
            pass
            
        # 尝试解析常见日志格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S",
            "%b %d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(timestamp_str, fmt)
                return dt.timestamp()
            except ValueError:
                continue
                
        raise ValueError(f"无法解析时间戳: {timestamp_str}")
    
    def _get_data_subject_rights(self, start_date: datetime.datetime, 
                               end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """
        获取数据主体权利行使情况
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            数据主体权利行使列表
        """
        # 这里使用模拟实现，实际应用中应从日志中提取数据主体权利行使情况
        return get_data_subject_rights_exercises()
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成报告摘要
        
        Args:
            report: 完整报告
            
        Returns:
            报告摘要
        """
        operations = report.get("operations", {})
        security_incidents = report.get("security_incidents", [])
        data_subjects = report.get("data_subjects", [])
        
        return {
            "total_operations": operations.get("total", 0),
            "security_incidents_count": len(security_incidents),
            "data_subjects_count": len(data_subjects),
            "period": report.get("period", ""),
            "compliant": self._assess_compliance(report)
        }
    
    def _assess_compliance(self, report: Dict[str, Any]) -> bool:
        """
        评估合规性
        
        Args:
            report: 完整报告
            
        Returns:
            是否合规
        """
        # 检查是否有严重安全事件
        security_incidents = report.get("security_incidents", [])
        serious_incidents = [
            incident for incident in security_incidents
            if incident.get("type") in [
                SecurityIncidentType.UNAUTHORIZED_ACCESS.value,
                SecurityIncidentType.DATA_BREACH.value
            ]
        ]
        
        # 如果有严重安全事件，则不合规
        if serious_incidents:
            return False
            
        # 其他合规检查...
        # 实际应用中应根据具体合规要求进行更详细的检查
        
        return True
    
    def _sign_report(self, fingerprint: str) -> str:
        """
        签名报告
        
        Args:
            fingerprint: 报告指纹
            
        Returns:
            报告签名
        """
        h = hmac.new(
            self._report_key.encode('utf-8'),
            fingerprint.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(h.digest()).decode('utf-8')
    
    def _report_to_csv(self, report: Dict[str, Any]) -> str:
        """
        将报告转换为CSV格式
        
        Args:
            report: 报告字典
            
        Returns:
            CSV格式报告
        """
        # 实际应用中应根据具体需求实现CSV转换
        # 这里返回一个简单的实现
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题
        writer.writerow(["审计报告", report.get("period", "")])
        writer.writerow(["生成时间", report.get("generation_time", "")])
        writer.writerow([])
        
        # 写入操作统计
        writer.writerow(["操作统计"])
        operations = report.get("operations", {})
        for op_type, count in operations.items():
            writer.writerow([op_type, count])
        writer.writerow([])
        
        # 写入安全事件
        writer.writerow(["安全事件"])
        writer.writerow(["时间", "类型", "严重性", "描述"])
        for incident in report.get("security_incidents", []):
            writer.writerow([
                incident.get("timestamp", ""),
                incident.get("type", ""),
                incident.get("severity", ""),
                incident.get("description", "")
            ])
        
        return output.getvalue()
    
    def _report_to_text(self, report: Dict[str, Any]) -> str:
        """
        将报告转换为文本格式
        
        Args:
            report: 报告字典
            
        Returns:
            文本格式报告
        """
        # 构建文本报告
        lines = []
        lines.append("=" * 80)
        lines.append(f"审计报告: {report.get('period', '')}")
        lines.append(f"生成时间: {report.get('generation_time', '')}")
        lines.append("=" * 80)
        lines.append("")
        
        # 添加摘要
        summary = report.get("summary", {})
        lines.append("摘要:")
        lines.append(f"  总操作数: {summary.get('total_operations', 0)}")
        lines.append(f"  安全事件数: {summary.get('security_incidents_count', 0)}")
        lines.append(f"  数据主体数: {summary.get('data_subjects_count', 0)}")
        lines.append(f"  合规状态: {'合规' if summary.get('compliant', False) else '不合规'}")
        lines.append("")
        
        # 添加操作统计
        lines.append("操作统计:")
        operations = report.get("operations", {})
        for op_type, count in operations.items():
            lines.append(f"  {op_type}: {count}")
        lines.append("")
        
        # 添加安全事件
        lines.append("安全事件:")
        for incident in report.get("security_incidents", [])[:10]:  # 仅显示前10个
            lines.append(f"  [{incident.get('timestamp', '')}] {incident.get('type', '')}: {incident.get('description', '')}")
        
        if len(report.get("security_incidents", [])) > 10:
            lines.append(f"  ... 还有 {len(report.get('security_incidents', [])) - 10} 个安全事件未显示")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"报告指纹: {report.get('fingerprint', '')}")
        
        return "\n".join(lines)
        
    def export_audit_report(self, 
                          start_date: Union[str, datetime.datetime, datetime.date], 
                          end_date: Union[str, datetime.datetime, datetime.date],
                          output_file: Union[str, Path],
                          report_type: str = "gdpr",
                          output_format: str = "json") -> bool:
        """
        导出审计报告到文件
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            output_file: 输出文件路径
            report_type: 报告类型
            output_format: 输出格式
            
        Returns:
            是否成功导出
        """
        # 生成报告
        report = self.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            output_format=output_format
        )
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_format == "json":
                    json.dump(report, f, ensure_ascii=False, indent=2)
                else:
                    f.write(report)
            
            logger.info(f"已导出审计报告到: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出审计报告失败: {str(e)}")
            return False

# 帮助函数

def list_masked_users() -> List[Dict[str, Any]]:
    """列出脱敏后的用户数据"""
    # 模拟实现，实际应用中应从日志中提取并脱敏用户数据
    return [
        {
            "user_id_hash": hashlib.sha256(f"user1".encode()).hexdigest()[:8],
            "operations_count": 15,
            "last_activity": (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat()
        },
        {
            "user_id_hash": hashlib.sha256(f"user2".encode()).hexdigest()[:8],
            "operations_count": 8,
            "last_activity": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
        },
        {
            "user_id_hash": hashlib.sha256(f"user3".encode()).hexdigest()[:8],
            "operations_count": 23,
            "last_activity": datetime.datetime.now().isoformat()
        }
    ]

def list_data_processing_activities() -> List[Dict[str, Any]]:
    """列出数据处理活动"""
    # 模拟实现，实际应用中应从日志中提取数据处理活动
    return [
        {
            "activity": "用户视频处理",
            "data_categories": ["视频内容", "字幕内容"],
            "processing_purpose": "内容混剪生成",
            "retention_period": "90天",
            "status": DataProcessingStatus.ACTIVE.value
        },
        {
            "activity": "用户偏好分析",
            "data_categories": ["用户行为", "内容特征"],
            "processing_purpose": "个性化推荐",
            "retention_period": "180天",
            "status": DataProcessingStatus.ACTIVE.value
        },
        {
            "activity": "历史内容归档",
            "data_categories": ["处理过的视频", "生成内容"],
            "processing_purpose": "系统功能改进",
            "retention_period": "365天",
            "status": DataProcessingStatus.ARCHIVED.value
        }
    ]

def get_data_subject_rights_exercises() -> List[Dict[str, Any]]:
    """获取数据主体权利行使情况"""
    # 模拟实现，实际应用中应从日志中提取数据主体权利行使情况
    return [
        {
            "right_type": "访问权",
            "request_date": (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat(),
            "status": "已完成",
            "completion_date": (datetime.datetime.now() - datetime.timedelta(days=13)).isoformat()
        },
        {
            "right_type": "删除权",
            "request_date": (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(),
            "status": "处理中",
            "completion_date": None
        }
    ]

# 模块函数

def generate_audit_report(start_date: Union[str, datetime.datetime, datetime.date], 
                        end_date: Union[str, datetime.datetime, datetime.date],
                        **kwargs) -> Dict[str, Any]:
    """
    生成审计报告
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        **kwargs: 其他参数，传递给AuditReportGenerator.generate_audit_report
        
    Returns:
        生成的审计报告
    """
    generator = AuditReportGenerator()
    return generator.generate_audit_report(start_date, end_date, **kwargs)

def count_operations(start_date: Union[str, datetime.datetime, datetime.date], 
                   end_date: Union[str, datetime.datetime, datetime.date]) -> Dict[str, int]:
    """
    统计指定时间范围内的操作数量
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        操作统计字典
    """
    generator = AuditReportGenerator()
    start_date_dt = generator._normalize_date(start_date)
    end_date_dt = generator._normalize_date(end_date)
    return generator._count_operations(start_date_dt, end_date_dt)

def list_security_events(start_date: Union[str, datetime.datetime, datetime.date], 
                       end_date: Union[str, datetime.datetime, datetime.date]) -> List[Dict[str, Any]]:
    """
    列出指定时间范围内的安全事件
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        安全事件列表
    """
    generator = AuditReportGenerator()
    start_date_dt = generator._normalize_date(start_date)
    end_date_dt = generator._normalize_date(end_date)
    return generator._list_security_events(start_date_dt, end_date_dt)
    
def export_audit_report(start_date: Union[str, datetime.datetime, datetime.date], 
                      end_date: Union[str, datetime.datetime, datetime.date],
                      output_file: Union[str, Path],
                      **kwargs) -> bool:
    """
    导出审计报告到文件
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        output_file: 输出文件路径
        **kwargs: 其他参数，传递给AuditReportGenerator.export_audit_report
        
    Returns:
        是否成功导出
    """
    generator = AuditReportGenerator()
    return generator.export_audit_report(start_date, end_date, output_file, **kwargs)


if __name__ == "__main__":
    # 测试代码
    
    # 生成报告
    today = datetime.date.today()
    one_month_ago = today - datetime.timedelta(days=30)
    
    report = generate_audit_report(
        start_date=one_month_ago,
        end_date=today,
        report_type="gdpr",
        output_format="text"
    )
    
    print(report)
    
    # 导出到文件
    export_audit_report(
        start_date=one_month_ago,
        end_date=today,
        output_file="audit_report.json",
        report_type="gdpr"
    ) 