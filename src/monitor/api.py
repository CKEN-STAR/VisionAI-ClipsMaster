#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
历史数据分析API接口

提供HTTP API访问历史数据分析和报告功能。
"""

import os
import json
import time
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, abort
from typing import Dict, Any, List, Optional

from src.monitor.history_analyzer import (
    get_history_analyzer, 
    generate_daily_report,
    generate_weekly_report,
    analyze_memory_trends,
    analyze_cache_performance,
    analyze_oom_risks,
    get_latest_reports
)

# 创建Blueprint
history_api = Blueprint('history_api', __name__)


@history_api.route('/reports/daily', methods=['GET'])
def get_daily_report():
    """获取最新的每日报告"""
    try:
        reports = get_latest_reports("daily", 1)
        if not reports:
            return jsonify({
                "success": False,
                "message": "未找到每日报告"
            }), 404
            
        return jsonify({
            "success": True,
            "report": reports[0]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取报告失败: {str(e)}"
        }), 500


@history_api.route('/reports/weekly', methods=['GET'])
def get_weekly_report():
    """获取最新的每周报告"""
    try:
        reports = get_latest_reports("weekly", 1)
        if not reports:
            return jsonify({
                "success": False,
                "message": "未找到每周报告"
            }), 404
            
        return jsonify({
            "success": True,
            "report": reports[0]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取报告失败: {str(e)}"
        }), 500


@history_api.route('/reports/list', methods=['GET'])
def list_reports():
    """获取报告列表"""
    try:
        # 获取查询参数
        report_type = request.args.get('type')  # daily, weekly, 或None表示所有
        limit = request.args.get('limit', 10, type=int)
        
        reports = get_latest_reports(report_type, limit)
        
        # 简化报告数据，只保留基本信息
        simplified = []
        for report in reports:
            simplified.append({
                "type": "daily" if "daily" in report.get('file_name', '') else "weekly",
                "datetime": report.get('datetime'),
                "timestamp": report.get('timestamp'),
                "file_path": report.get('file_path'),
                "file_name": report.get('file_name')
            })
            
        return jsonify({
            "success": True,
            "reports": simplified,
            "count": len(simplified)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取报告列表失败: {str(e)}"
        }), 500


@history_api.route('/reports/download/<path:filename>', methods=['GET'])
def download_report(filename):
    """下载报告文件"""
    try:
        # 获取历史分析器实例以获取报告目录
        analyzer = get_history_analyzer()
        file_path = os.path.join(analyzer.reports_dir, filename)
        
        if not os.path.exists(file_path):
            abort(404)
            
        return send_file(
            file_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"下载报告失败: {str(e)}"
        }), 500


@history_api.route('/charts/download/<path:filename>', methods=['GET'])
def download_chart(filename):
    """下载图表文件"""
    try:
        # 获取历史分析器实例以获取报告目录
        analyzer = get_history_analyzer()
        file_path = os.path.join(analyzer.reports_dir, "charts", filename)
        
        if not os.path.exists(file_path):
            abort(404)
            
        return send_file(
            file_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"下载图表失败: {str(e)}"
        }), 500


@history_api.route('/reports/generate/daily', methods=['POST'])
def create_daily_report():
    """生成每日报告"""
    try:
        report = generate_daily_report()
        
        return jsonify({
            "success": True,
            "message": "每日报告生成成功",
            "report": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"生成每日报告失败: {str(e)}"
        }), 500


@history_api.route('/reports/generate/weekly', methods=['POST'])
def create_weekly_report():
    """生成每周报告"""
    try:
        report = generate_weekly_report()
        
        return jsonify({
            "success": True,
            "message": "每周报告生成成功",
            "report": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"生成每周报告失败: {str(e)}"
        }), 500


@history_api.route('/analysis/memory', methods=['GET'])
def get_memory_analysis():
    """获取内存使用趋势分析"""
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)
        
        result = analyze_memory_trends(days)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"分析内存趋势失败: {str(e)}"
        }), 500


@history_api.route('/analysis/cache', methods=['GET'])
def get_cache_analysis():
    """获取缓存性能分析"""
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)
        
        result = analyze_cache_performance(days)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"分析缓存性能失败: {str(e)}"
        }), 500


@history_api.route('/analysis/oom', methods=['GET'])
def get_oom_analysis():
    """获取OOM风险分析"""
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)
        
        result = analyze_oom_risks(days)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"分析OOM风险失败: {str(e)}"
        }), 500


# 注册API
def register_history_api(app):
    """注册历史数据分析API
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(history_api, url_prefix='/api/history') 