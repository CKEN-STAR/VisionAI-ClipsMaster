#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工作流审计集成模块

将合规审计功能与剪映导出工作流集成，确保导出内容符合GDPR和个人信息保护法要求。
"""

import os
import sys
import datetime
import json
import hashlib
import hmac
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# 导入审计相关模块
from src.exporters.log_audit import AuditReportGenerator
from src.exporters.xml_template import XMLTemplateProcessor
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("workflow_audit")

class WorkflowAuditIntegrator:
    """工作流审计集成器"""
    
    def __init__(self):
        """初始化工作流审计集成器"""
        # 创建审计报告生成器
        self.audit_generator = AuditReportGenerator()
        
        # 工作流事件记录
        self.workflow_events = []
        
        # 开始时间
        self.start_time = datetime.datetime.now()
    
    def record_workflow_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        记录工作流事件
        
        Args:
            event_type: 事件类型
            details: 事件详情
        """
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        
        self.workflow_events.append(event)
        logger.info(f"记录工作流事件: {event_type}")
    
    def record_project_initialization(self, project_info: Dict[str, Any]) -> None:
        """
        记录项目初始化事件
        
        Args:
            project_info: 项目信息
        """
        self.record_workflow_event("project_initialization", project_info)
    
    def record_timeline_conversion(self, timeline_info: Dict[str, Any]) -> None:
        """
        记录时间轴转换事件
        
        Args:
            timeline_info: 时间轴信息
        """
        self.record_workflow_event("timeline_conversion", timeline_info)
    
    def record_xml_template_filling(self, template_info: Dict[str, Any]) -> None:
        """
        记录XML模板填充事件
        
        Args:
            template_info: 模板信息
        """
        self.record_workflow_event("xml_template_filling", template_info)
    
    def record_legal_info_injection(self, legal_info: Dict[str, Any]) -> None:
        """
        记录法律声明注入事件
        
        Args:
            legal_info: 法律声明信息
        """
        self.record_workflow_event("legal_info_injection", legal_info)
    
    def record_validation_result(self, is_valid: bool, validation_details: Dict[str, Any]) -> None:
        """
        记录验证结果事件
        
        Args:
            is_valid: 是否验证通过
            validation_details: 验证详情
        """
        self.record_workflow_event("validation", {
            "is_valid": is_valid,
            **validation_details
        })
    
    def record_export_completion(self, export_info: Dict[str, Any]) -> None:
        """
        记录导出完成事件
        
        Args:
            export_info: 导出信息
        """
        self.record_workflow_event("export_completion", export_info)
    
    def record_error(self, error_info: Dict[str, Any]) -> None:
        """
        记录错误事件
        
        Args:
            error_info: 错误信息
        """
        self.record_workflow_event("error", error_info)
    
    def verify_legal_compliance(self, xml_processor: XMLTemplateProcessor) -> Tuple[bool, str]:
        """
        验证法律合规性
        
        Args:
            xml_processor: XML模板处理器
            
        Returns:
            是否合规，合规消息
        """
        # 检查是否包含法律声明
        legal = xml_processor.root.find("legal_info")
        if legal is None:
            return False, "缺少法律声明部分"
        
        # 检查必要的法律声明元素
        required_elements = ["copyright", "data_processing"]
        for element in required_elements:
            if legal.find(element) is None:
                return False, f"法律声明缺少必要元素: {element}"
        
        # 检查数据处理声明是否符合要求
        data_processing = legal.find("data_processing")
        if data_processing is None or not data_processing.text:
            return False, "数据处理声明为空"
        
        # 检查数据处理声明是否包含必要的关键词
        required_keywords = ["GDPR", "个人信息保护法", "数据", "处理"]
        data_processing_text = data_processing.text.lower()
        missing_keywords = [kw for kw in required_keywords if kw.lower() not in data_processing_text]
        
        if missing_keywords:
            return False, f"数据处理声明缺少必要的关键词: {', '.join(missing_keywords)}"
        
        return True, "法律合规性验证通过"
    
    def generate_workflow_audit_report(self, output_path: Union[str, Path]) -> bool:
        """
        生成工作流审计报告
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        # 计算工作流时长
        duration = (datetime.datetime.now() - self.start_time).total_seconds()
        
        # 构建审计报告
        report = {
            "workflow": "jianying_export",
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.datetime.now().isoformat(),
            "duration_seconds": duration,
            "events": self.workflow_events,
            "summary": {
                "total_events": len(self.workflow_events),
                "events_by_type": self._count_events_by_type(),
                "errors": self._count_errors(),
                "completed_successfully": self._is_completed_successfully()
            }
        }
        
        # 计算报告指纹
        report_json = json.dumps(report, ensure_ascii=False, sort_keys=True)
        report["fingerprint"] = hashlib.sha256(report_json.encode('utf-8')).hexdigest()
        
        # 保存报告
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"工作流审计报告已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存工作流审计报告失败: {str(e)}")
            return False
    
    def _count_events_by_type(self) -> Dict[str, int]:
        """
        统计各类型事件数量
        
        Returns:
            事件类型统计
        """
        event_counts = {}
        for event in self.workflow_events:
            event_type = event["type"]
            if event_type in event_counts:
                event_counts[event_type] += 1
            else:
                event_counts[event_type] = 1
        
        return event_counts
    
    def _count_errors(self) -> int:
        """
        统计错误数量
        
        Returns:
            错误数量
        """
        return sum(1 for event in self.workflow_events if event["type"] == "error")
    
    def _is_completed_successfully(self) -> bool:
        """
        检查工作流是否成功完成
        
        Returns:
            是否成功完成
        """
        # 检查是否存在导出完成事件
        has_export_completion = any(event["type"] == "export_completion" for event in self.workflow_events)
        
        # 检查是否有错误事件
        has_errors = self._count_errors() > 0
        
        return has_export_completion and not has_errors
    
    def create_comprehensive_audit_report(self, 
                                        project_info: Dict[str, Any],
                                        output_path: Union[str, Path]) -> bool:
        """
        创建综合审计报告
        
        Args:
            project_info: 项目信息
            output_path: 输出文件路径
            
        Returns:
            是否成功创建
        """
        try:
            # 获取当前日期
            today = datetime.date.today()
            
            # 生成标准审计报告
            audit_report = self.audit_generator.generate_audit_report(
                start_date=today - datetime.timedelta(days=30),
                end_date=today,
                report_type="all",
                output_format="json",
                include_details=True
            )
            
            # 生成工作流审计报告
            workflow_report_path = Path(output_path).with_suffix(".workflow.json")
            self.generate_workflow_audit_report(workflow_report_path)
            
            # 合并报告
            comprehensive_report = {
                "project_info": project_info,
                "audit_report": audit_report,
                "workflow_events": self.workflow_events,
                "generation_time": datetime.datetime.now().isoformat(),
                "compliance_status": self._assess_compliance_status()
            }
            
            # 保存综合报告
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"综合审计报告已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建综合审计报告失败: {str(e)}")
            return False
    
    def _assess_compliance_status(self) -> Dict[str, Any]:
        """
        评估合规状态
        
        Returns:
            合规状态信息
        """
        # 检查是否所有必要步骤都已完成
        required_steps = [
            "project_initialization",
            "timeline_conversion",
            "xml_template_filling",
            "legal_info_injection",
            "validation",
            "export_completion"
        ]
        
        completed_steps = set(event["type"] for event in self.workflow_events)
        missing_steps = [step for step in required_steps if step not in completed_steps]
        
        # 检查是否有验证失败事件
        validation_events = [event for event in self.workflow_events if event["type"] == "validation"]
        validation_failed = any(not event["details"].get("is_valid", False) for event in validation_events)
        
        # 评估合规状态
        is_compliant = not missing_steps and not validation_failed and self._count_errors() == 0
        
        return {
            "is_compliant": is_compliant,
            "missing_steps": missing_steps,
            "validation_failed": validation_failed,
            "error_count": self._count_errors(),
            "is_workflow_completed": self._is_completed_successfully()
        }


# 模块函数

def create_workflow_auditor() -> WorkflowAuditIntegrator:
    """
    创建工作流审计集成器
    
    Returns:
        工作流审计集成器实例
    """
    return WorkflowAuditIntegrator()

def verify_compliance(xml_processor: XMLTemplateProcessor) -> Tuple[bool, str]:
    """
    验证合规性
    
    Args:
        xml_processor: XML模板处理器
        
    Returns:
        是否合规，合规消息
    """
    auditor = WorkflowAuditIntegrator()
    return auditor.verify_legal_compliance(xml_processor)

def generate_export_audit(project_info: Dict[str, Any], 
                         workflow_events: List[Dict[str, Any]],
                         output_path: Union[str, Path]) -> bool:
    """
    生成导出审计报告
    
    Args:
        project_info: 项目信息
        workflow_events: 工作流事件列表
        output_path: 输出文件路径
        
    Returns:
        是否成功生成
    """
    auditor = WorkflowAuditIntegrator()
    
    # 添加工作流事件
    for event in workflow_events:
        auditor.workflow_events.append(event)
    
    # 创建综合审计报告
    return auditor.create_comprehensive_audit_report(project_info, output_path)


if __name__ == "__main__":
    # 测试代码
    auditor = WorkflowAuditIntegrator()
    
    # 记录各类事件
    auditor.record_project_initialization({
        "name": "测试项目",
        "creation_time": datetime.datetime.now().isoformat()
    })
    
    auditor.record_timeline_conversion({
        "fps": "30",
        "duration": "60.0"
    })
    
    auditor.record_xml_template_filling({
        "template_version": "1.0"
    })
    
    auditor.record_legal_info_injection({
        "copyright": "© 2023 测试项目",
        "data_processing": "本导出内容符合GDPR和中国个人信息保护法规定"
    })
    
    auditor.record_validation_result(True, {
        "validation_items": ["项目元数据", "时间轴", "资源", "法律声明"],
        "all_passed": True
    })
    
    auditor.record_export_completion({
        "output_path": "测试项目.zip",
        "format": "project",
        "size_bytes": 1024 * 1024
    })
    
    # 生成工作流审计报告
    auditor.generate_workflow_audit_report("workflow_audit.json")
    
    # 创建综合审计报告
    auditor.create_comprehensive_audit_report(
        {"name": "测试项目", "author": "测试用户"},
        "comprehensive_audit.json"
    ) 