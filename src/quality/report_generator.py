#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
质量报告生成模块

生成质量评估报告
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class QualityReport:
    """质量报告类"""
    
    def __init__(self, report_name: str = ""):
        """初始化质量报告"""
        self.report_name = report_name or f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metrics = {}
        self.issues = []
        self.recommendations = []
        self.created_at = datetime.now()
    
    def add_metric(self, name: str, value: Any, category: str = "general") -> None:
        """添加指标"""
        if category not in self.metrics:
            self.metrics[category] = {}
        self.metrics[category][name] = value
    
    def add_issue(self, issue: str, severity: str = "medium") -> None:
        """添加问题"""
        self.issues.append({
            "description": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_recommendation(self, recommendation: str) -> None:
        """添加建议"""
        self.recommendations.append({
            "description": recommendation,
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "report_name": self.report_name,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics,
            "issues": self.issues,
            "recommendations": self.recommendations
        }
    
    def save(self, filepath: Optional[str] = None) -> str:
        """保存报告"""
        if filepath is None:
            # 创建默认路径
            os.makedirs("data/quality_reports", exist_ok=True)
            filepath = f"data/quality_reports/{self.report_name}.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存为JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        return filepath


def generate_quality_report(data: Dict[str, Any], report_name: str = "") -> QualityReport:
    """生成质量报告"""
    report = QualityReport(report_name)
    
    # 添加基本指标
    for category, metrics in data.items():
        if isinstance(metrics, dict):
            for name, value in metrics.items():
                report.add_metric(name, value, category)
        
        # 添加问题和建议
    if "issues" in data:
        for issue in data["issues"]:
            if isinstance(issue, dict) and "description" in issue:
                report.add_issue(issue["description"], issue.get("severity", "medium"))
            elif isinstance(issue, str):
                report.add_issue(issue)
    
    if "recommendations" in data:
        for rec in data["recommendations"]:
            if isinstance(rec, dict) and "description" in rec:
                report.add_recommendation(rec["description"])
            elif isinstance(rec, str):
                report.add_recommendation(rec)
    
    return report 