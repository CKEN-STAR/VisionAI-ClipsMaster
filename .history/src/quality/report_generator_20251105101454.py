#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
质量报告生成模块

生成质量评估报告（JSON/HTML）
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# JSON 序列化容错（处理 numpy 标量/数组、集合、时间等类型）

def _json_default(o):
    try:
        import numpy as _np
        if isinstance(o, (_np.integer,)):
            return int(o)
        if isinstance(o, (_np.floating,)):
            return float(o)
        if isinstance(o, (_np.bool_,)):
            return bool(o)
        if isinstance(o, _np.ndarray):
            return o.tolist()
    except Exception:
        pass
    if hasattr(o, "isoformat"):
        try:
            return o.isoformat()
        except Exception:
            pass
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


class QualityReport:
    """
    质量报告类
    """

    def __init__(self, report_name: str = ""):
        """
        初始化质量报告
        """
        self.report_name = report_name or f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.issues: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self.created_at = datetime.now()

    def add_metric(self, name: str, value: Any, category: str = "general") -> None:
        """
        添加指标
        """
        if category not in self.metrics:
            self.metrics[category] = {}
        self.metrics[category][name] = value

    def add_issue(self, issue: str, severity: str = "medium") -> None:
        """
        添加问题
        """
        self.issues.append({
            "description": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })

    def add_recommendation(self, recommendation: str) -> None:
        """
        添加建议
        """
        self.recommendations.append({
            "description": recommendation,
            "timestamp": datetime.now().isoformat()
        })

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            "report_name": self.report_name,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics,
            "issues": self.issues,
            "recommendations": self.recommendations
        }

    def save(self, filepath: Optional[str] = None) -> str:
        """
        保存报告
        """
        if filepath is None:
            # 创建默认路径
            os.makedirs("data/quality_reports", exist_ok=True)
            filepath = f"data/quality_reports/{self.report_name}.json"

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 保存为JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2, default=_json_default)

        return filepath


def generate_quality_report(
    data: Dict[str, Any],
    output_dir: Optional[str] = None,
    formats: Optional[List[str]] = None,
    report_name: str = ""
) -> Dict[str, str]:
    """
    生成质量报告文件，返回格式->路径的映射

    Args:
        data: 质量数据（通常为 probe.probe_data 或其 summary 字段）
        output_dir: 报告输出目录（默认 data/quality_reports）
        formats: 需要生成的格式列表，如 ["json", "html"]
        report_name: 报告基名（可选）

    Returns:
        Dict[str, str]: 形如 {"json": path, "html": path}
    """
    # 规范化参数
    fmts = [f.lower() for f in (formats or ["json"])]
    base_dir = output_dir or os.path.join("data", "quality_reports")
    os.makedirs(base_dir, exist_ok=True)
    base_name = report_name or f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    report_paths: Dict[str, str] = {}

    # JSON 报告
    if "json" in fmts:
        json_path = os.path.join(base_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)
        report_paths["json"] = json_path

    # 简单 HTML 报告（可选）
    if "html" in fmts:
        try:
            import html as _html
            html_path = os.path.join(base_dir, f"{base_name}.html")
            overall_quality = None
            try:
                overall_quality = data.get('summary', {}).get('overall_quality', None)
                if overall_quality is None and 'overall_quality' in data:
                    overall_quality = data.get('overall_quality')
            except Exception:
                overall_quality = None
            issues = data.get('summary', {}).get('issues', data.get('issues', []))
            recommendations = data.get('summary', {}).get('recommendations', data.get('recommendations', []))
            body = "<h2>Quality Report</h2>"
            if overall_quality is not None:
                body += f"<p>Overall Quality: {_html.escape(str(overall_quality))}</p>"
            if issues:
                body += "<h3>Issues</h3><ul>" + "".join(f"<li>{_html.escape(str(i))}</li>" for i in issues) + "</ul>"
            if recommendations:
                body += "<h3>Recommendations</h3><ul>" + "".join(f"<li>{_html.escape(str(r))}</li>" for r in recommendations) + "</ul>"
            body += "<h3>Raw Data</h3><pre>" + _html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=_json_default)) + "</pre>"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"<!doctype html><html><head><meta charset='utf-8'><title>{_html.escape(base_name)}</title></head><body>{body}</body></html>")
            report_paths["html"] = html_path
        except Exception:
            # HTML 生成失败不应阻断主流程
            pass

    return report_paths

