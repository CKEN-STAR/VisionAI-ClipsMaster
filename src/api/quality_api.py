#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
质量熔断器API

提供质量熔断器相关的API接口，包括状态查询、手动熔断和重置等。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app

from src.versioning.quality_circuit_breaker import (
    QualityGuardian, 
    QualityCollapseError,
    CircuitBreakerState,
    get_quality_guardian
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("quality_api")

# 创建Blueprint
quality_api = Blueprint('quality_api', __name__)

@quality_api.route('/status', methods=['GET'])
def get_circuit_breaker_status():
    """获取熔断器状态
    
    Returns:
        熔断器当前状态信息
    """
    try:
        guardian = get_quality_guardian()
        status = guardian.get_status()
        
        return jsonify({
            "success": True,
            "data": {
                "state": status["state"],
                "failure_count": status["failure_count"],
                "failure_threshold": status["failure_threshold"],
                "success_count": status["success_count"],
                "recovery_threshold": status["recovery_threshold"],
                "state_change_time": status["state_change_time"],
                "last_failure_time": status["last_failure_time"]
            }
        }), 200
    except Exception as e:
        logger.error(f"获取熔断器状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"获取熔断器状态失败: {str(e)}"
        }), 500

@quality_api.route('/history', methods=['GET'])
def get_quality_history():
    """获取质量检查历史
    
    Returns:
        最近的质量检查记录
    """
    try:
        # 获取请求参数
        limit = request.args.get('limit', default=10, type=int)
        
        guardian = get_quality_guardian()
        history = guardian.get_quality_history(limit)
        
        return jsonify({
            "success": True,
            "data": {
                "history": history,
                "count": len(history)
            }
        }), 200
    except Exception as e:
        logger.error(f"获取质量检查历史失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"获取质量检查历史失败: {str(e)}"
        }), 500

@quality_api.route('/reset', methods=['POST'])
def reset_circuit_breaker():
    """手动重置熔断器
    
    Returns:
        重置结果
    """
    try:
        guardian = get_quality_guardian()
        guardian.manually_reset()
        
        status = guardian.get_status()
        
        return jsonify({
            "success": True,
            "message": "熔断器已重置",
            "data": {
                "state": status["state"],
                "failure_count": status["failure_count"],
                "success_count": status["success_count"]
            }
        }), 200
    except Exception as e:
        logger.error(f"重置熔断器失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"重置熔断器失败: {str(e)}"
        }), 500

@quality_api.route('/open', methods=['POST'])
def open_circuit_breaker():
    """手动开启熔断器
    
    Returns:
        开启结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        reason = data.get('reason', '手动触发')
        
        guardian = get_quality_guardian()
        guardian.manually_open(reason)
        
        status = guardian.get_status()
        
        return jsonify({
            "success": True,
            "message": f"熔断器已开启，原因：{reason}",
            "data": {
                "state": status["state"],
                "state_change_time": status["state_change_time"]
            }
        }), 200
    except Exception as e:
        logger.error(f"开启熔断器失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"开启熔断器失败: {str(e)}"
        }), 500

@quality_api.route('/check', methods=['POST'])
def check_quality():
    """检查内容质量
    
    检查提交的内容是否满足质量要求
    
    Returns:
        检查结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据为空"
            }), 400
        
        # 获取版本信息
        version = data.get('version')
        if not version:
            return jsonify({
                "success": False,
                "error": "缺少版本信息"
            }), 400
        
        # 获取用户组
        user_group = data.get('user_group', 'stable')
        
        # 执行质量检查
        guardian = get_quality_guardian()
        
        try:
            guardian.monitor([version], user_group)
            
            # 获取最新的检查记录
            history = guardian.get_quality_history(1)
            latest_record = history[0] if history else None
            
            return jsonify({
                "success": True,
                "message": "质量检查通过",
                "data": {
                    "passed": True,
                    "metrics": latest_record["metrics"] if latest_record else {},
                    "version_id": version.get("id", "unknown")
                }
            }), 200
        except QualityCollapseError as e:
            # 获取最新的检查记录
            history = guardian.get_quality_history(1)
            latest_record = history[0] if history else None
            
            return jsonify({
                "success": False,
                "message": str(e),
                "data": {
                    "passed": False,
                    "metrics": latest_record["metrics"] if latest_record else {},
                    "version_id": version.get("id", "unknown"),
                    "state": guardian.state
                }
            }), 400
            
    except Exception as e:
        logger.error(f"执行质量检查失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"执行质量检查失败: {str(e)}"
        }), 500

@quality_api.route('/configure', methods=['POST'])
def configure_quality_guardian():
    """配置质量守护者
    
    设置质量阈值和熔断参数
    
    Returns:
        配置结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据为空"
            }), 400
        
        guardian = get_quality_guardian()
        
        # 更新熔断阈值
        if 'failure_threshold' in data:
            guardian.failure_threshold = data['failure_threshold']
        
        if 'recovery_threshold' in data:
            guardian.recovery_threshold = data['recovery_threshold']
        
        if 'reset_window' in data:
            guardian.reset_window = data['reset_window']
        
        # 自定义检查器
        if 'custom_checkers' in data:
            for checker in data['custom_checkers']:
                name = checker.get('name')
                threshold = checker.get('threshold')
                
                if name and threshold is not None:
                    # 实际应用中，这里需要更安全的处理方式
                    # 这里简单处理，使用已存在的检查函数
                    if name == 'coherence':
                        from src.evaluation.coherence_checker import check_coherence
                        guardian.add_custom_checker(name, lambda v: check_coherence(v), threshold)
                    elif name == 'emotion_flow':
                        from src.evaluation.emotion_flow_evaluator import evaluate_emotion_flow
                        guardian.add_custom_checker(name, lambda v: evaluate_emotion_flow(v), threshold)
                    elif name == 'pacing':
                        from src.evaluation.pacing_evaluator import evaluate_pacing
                        guardian.add_custom_checker(name, lambda v: evaluate_pacing(v), threshold)
                    elif name == 'narrative_structure':
                        from src.evaluation.narrative_structure_evaluator import evaluate_narrative_structure
                        guardian.add_custom_checker(name, lambda v: evaluate_narrative_structure(v), threshold)
                    elif name == 'audience_engagement':
                        from src.evaluation.audience_engagement_predictor import predict_engagement_score
                        guardian.add_custom_checker(name, lambda v: predict_engagement_score(v), threshold)
        
        return jsonify({
            "success": True,
            "message": "质量守护者配置已更新",
            "data": {
                "failure_threshold": guardian.failure_threshold,
                "recovery_threshold": guardian.recovery_threshold,
                "reset_window": guardian.reset_window
            }
        }), 200
    except Exception as e:
        logger.error(f"配置质量守护者失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"配置质量守护者失败: {str(e)}"
        }), 500

def register_quality_api(app):
    """注册质量API到Flask应用
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(quality_api, url_prefix='/api/quality') 