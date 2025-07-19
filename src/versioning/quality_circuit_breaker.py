#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
质量熔断器模块

监控生成内容的质量，当连续检测到多个低质量版本时触发熔断机制，
防止质量不合格的内容推送给用户，确保系统输出的持续稳定性。
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta

from src.utils.log_handler import get_logger
from src.evaluation.coherence_checker import check_coherence
from src.evaluation.emotion_flow_evaluator import evaluate_emotion_flow
from src.evaluation.pacing_evaluator import evaluate_pacing
from src.evaluation.narrative_structure_evaluator import evaluate_narrative_structure
from src.evaluation.audience_engagement_predictor import predict_engagement_score

# 配置日志
logger = get_logger("quality_circuit_breaker")

class QualityCollapseError(Exception):
    """质量熔断异常，当连续多个版本质量不合格时触发"""
    pass

class CircuitBreakerState:
    """熔断器状态定义"""
    
    CLOSED = "closed"       # 正常状态，允许生成内容
    OPEN = "open"           # 熔断状态，阻止生成内容
    HALF_OPEN = "half_open" # 半开状态，允许尝试生成少量内容进行测试
    
class QualityThreshold:
    """质量阈值定义"""
    
    # 默认质量检查阈值
    COHERENCE_THRESHOLD = 0.75       # 叙事连贯性阈值
    EMOTION_FLOW_THRESHOLD = 0.70    # 情感流畅度阈值
    PACING_THRESHOLD = 0.65          # 节奏控制阈值
    STRUCTURE_THRESHOLD = 0.72       # 结构完整度阈值
    ENGAGEMENT_THRESHOLD = 0.68      # 观众参与度预测阈值
    
    # 不同用户组的质量阈值
    GROUP_THRESHOLDS = {
        "internal": {  # 内部测试组阈值，更宽松
            "coherence": 0.65,
            "emotion_flow": 0.60,
            "pacing": 0.55,
            "structure": 0.62,
            "engagement": 0.58
        },
        "beta": {  # 测试用户组阈值，中等
            "coherence": 0.70,
            "emotion_flow": 0.65,
            "pacing": 0.60,
            "structure": 0.68,
            "engagement": 0.63
        },
        "stable": {  # 稳定用户组阈值，更严格
            "coherence": 0.75,
            "emotion_flow": 0.70,
            "pacing": 0.65,
            "structure": 0.72,
            "engagement": 0.68
        }
    }
    
    @staticmethod
    def get_thresholds(user_group: str = "stable") -> Dict[str, float]:
        """获取指定用户组的质量阈值
        
        Args:
            user_group: 用户组名称
            
        Returns:
            质量阈值字典
        """
        if user_group in QualityThreshold.GROUP_THRESHOLDS:
            return QualityThreshold.GROUP_THRESHOLDS[user_group]
        
        # 默认返回稳定组阈值
        return QualityThreshold.GROUP_THRESHOLDS["stable"]

class QualityGuardian:
    """质量守护者
    
    监控生成内容的质量，确保系统输出内容满足质量要求，
    当连续检测到低质量内容时触发熔断机制。
    """
    
    def __init__(self, 
                config_path: Optional[str] = None, 
                failure_threshold: int = 3,
                recovery_threshold: int = 2,
                reset_window: int = 3600):
        """初始化质量守护者
        
        Args:
            config_path: 配置文件路径，可选
            failure_threshold: 触发熔断的连续失败次数阈值
            recovery_threshold: 恢复正常所需的连续成功次数阈值
            reset_window: 自动重置失败计数的时间窗口(秒)
        """
        self.failure_count = 0
        self.success_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.reset_window = reset_window
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.state_change_time = datetime.now()
        self.quality_metrics_history = []
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 自定义检查器和阈值
        self.custom_checkers = {}
        self.custom_thresholds = {}
        
        # 记录初始化信息
        logger.info(f"质量守护者初始化完成，熔断阈值={failure_threshold}，恢复阈值={recovery_threshold}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        default_config = {
            "failure_threshold": self.failure_threshold,
            "recovery_threshold": self.recovery_threshold,
            "reset_window": self.reset_window,
            "thresholds": QualityThreshold.GROUP_THRESHOLDS,
            "check_metrics": ["coherence", "emotion_flow", "pacing", "structure", "engagement"]
        }
        
        if not config_path:
            return default_config
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并配置，确保所有必要字段都存在
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.error(f"加载质量守护者配置失败: {str(e)}")
        
        return default_config
    
    def add_custom_checker(self, name: str, checker_func: Callable, threshold: float) -> None:
        """添加自定义质量检查器
        
        Args:
            name: 检查器名称
            checker_func: 检查函数，接收版本作为参数，返回质量分数
            threshold: 质量阈值
        """
        self.custom_checkers[name] = checker_func
        self.custom_thresholds[name] = threshold
        logger.info(f"已添加自定义质量检查器: {name}, 阈值: {threshold}")
    
    def monitor(self, versions: List[Dict[str, Any]], user_group: str = "stable") -> None:
        """监控多个版本的质量
        
        连续检测到多个不合格版本时触发熔断异常
        
        Args:
            versions: 待检查的版本列表
            user_group: 用户组，用于确定质量阈值
            
        Raises:
            QualityCollapseError: 当触发熔断条件时抛出
        """
        # 检查是否需要自动重置失败计数
        self._check_auto_reset()
        
        # 当前熔断器已开启时，拒绝所有请求
        if self.state == CircuitBreakerState.OPEN:
            # 检查是否到达半开状态的时间
            if self._should_transition_to_half_open():
                self.state = CircuitBreakerState.HALF_OPEN
                self.state_change_time = datetime.now()
                logger.info("质量熔断器状态从OPEN转为HALF_OPEN")
            else:
                raise QualityCollapseError(f"质量熔断器处于开启状态，拒绝生成请求，请等待系统恢复")
        
        # 获取当前用户组的质量阈值
        thresholds = QualityThreshold.get_thresholds(user_group)
        
        # 半开状态下只检查一个版本
        if self.state == CircuitBreakerState.HALF_OPEN:
            if not versions:
                return
                
            version = versions[0]
            if self._pass_quality_check(version, thresholds):
                self.success_count += 1
                if self.success_count >= self.recovery_threshold:
                    # 连续成功达到恢复阈值，关闭熔断器
                    self.state = CircuitBreakerState.CLOSED
                    self.state_change_time = datetime.now()
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"质量检查连续{self.recovery_threshold}次通过，熔断器已关闭")
            else:
                # 半开状态下检测失败，重新开启熔断器
                self.state = CircuitBreakerState.OPEN
                self.state_change_time = datetime.now()
                self.success_count = 0
                logger.warning("半开状态下质量检查失败，熔断器重新开启")
                raise QualityCollapseError("质量检测失败，系统熔断保护已重新激活")
            
            return
        
        # 正常状态下检查所有版本
        for version in versions:
            if not self._pass_quality_check(version, thresholds):
                self.failure_count += 1
                self.success_count = 0
                self.last_failure_time = datetime.now()
                
                logger.warning(f"版本 {version.get('id', 'unknown')} 质量检查未通过，当前失败计数：{self.failure_count}/{self.failure_threshold}")
                
                if self.failure_count >= self.failure_threshold:
                    # 开启熔断器
                    self.state = CircuitBreakerState.OPEN
                    self.state_change_time = datetime.now()
                    logger.error(f"连续{self.failure_threshold}个版本质量不合格，熔断器已开启")
                    raise QualityCollapseError(f"生成质量持续低下，已熔断")
            else:
                # 成功时增加成功计数，重置失败计数
                self.success_count += 1
                if self.success_count >= 2:  # 连续2次成功后重置失败计数
                    self.failure_count = 0
                    
                logger.info(f"版本 {version.get('id', 'unknown')} 质量检查通过")
    
    def _check_auto_reset(self) -> None:
        """检查是否需要自动重置失败计数"""
        if (self.last_failure_time and 
            (datetime.now() - self.last_failure_time).total_seconds() > self.reset_window):
            if self.failure_count > 0:
                logger.info(f"自动重置失败计数：{self.reset_window}秒内无新失败")
                self.failure_count = 0
    
    def _should_transition_to_half_open(self) -> bool:
        """检查是否应该从开启状态转为半开状态"""
        # 默认开启状态持续5分钟后尝试半开
        waiting_period = 300  # 秒
        elapsed = (datetime.now() - self.state_change_time).total_seconds()
        return elapsed >= waiting_period
    
    def _pass_quality_check(self, version: Dict[str, Any], thresholds: Dict[str, float]) -> bool:
        """检查版本是否通过质量检查
        
        Args:
            version: 版本信息
            thresholds: 质量阈值字典
            
        Returns:
            是否通过检查
        """
        # 收集所有质量检查结果
        quality_metrics = {}
        
        # 检查核心质量指标
        if "coherence" in self.config["check_metrics"]:
            coherence_score = check_coherence(version)
            quality_metrics["coherence"] = coherence_score
            if coherence_score < thresholds["coherence"]:
                logger.warning(f"版本 {version.get('id', 'unknown')} 连贯性检查未通过: {coherence_score:.2f} < {thresholds['coherence']}")
                self._record_quality_metrics(version, quality_metrics, False)
                return False
        
        if "emotion_flow" in self.config["check_metrics"]:
            emotion_score = evaluate_emotion_flow(version)
            quality_metrics["emotion_flow"] = emotion_score
            if emotion_score < thresholds["emotion_flow"]:
                logger.warning(f"版本 {version.get('id', 'unknown')} 情感流检查未通过: {emotion_score:.2f} < {thresholds['emotion_flow']}")
                self._record_quality_metrics(version, quality_metrics, False)
                return False
        
        if "pacing" in self.config["check_metrics"]:
            pacing_score = evaluate_pacing(version)
            quality_metrics["pacing"] = pacing_score
            if pacing_score < thresholds["pacing"]:
                logger.warning(f"版本 {version.get('id', 'unknown')} 节奏控制检查未通过: {pacing_score:.2f} < {thresholds['pacing']}")
                self._record_quality_metrics(version, quality_metrics, False)
                return False
        
        if "structure" in self.config["check_metrics"]:
            structure_score = evaluate_narrative_structure(version)
            quality_metrics["structure"] = structure_score
            if structure_score < thresholds["structure"]:
                logger.warning(f"版本 {version.get('id', 'unknown')} 叙事结构检查未通过: {structure_score:.2f} < {thresholds['structure']}")
                self._record_quality_metrics(version, quality_metrics, False)
                return False
        
        if "engagement" in self.config["check_metrics"]:
            engagement_score = predict_engagement_score(version)
            quality_metrics["engagement"] = engagement_score
            if engagement_score < thresholds["engagement"]:
                logger.warning(f"版本 {version.get('id', 'unknown')} 观众参与度预测未通过: {engagement_score:.2f} < {thresholds['engagement']}")
                self._record_quality_metrics(version, quality_metrics, False)
                return False
        
        # 检查自定义质量指标
        for name, checker in self.custom_checkers.items():
            score = checker(version)
            quality_metrics[name] = score
            if score < self.custom_thresholds[name]:
                logger.warning(f"版本 {version.get('id', 'unknown')} 自定义检查 {name} 未通过: {score:.2f} < {self.custom_thresholds[name]}")
                self._record_quality_metrics(version, quality_metrics, False)
                return False
        
        # 所有检查通过
        self._record_quality_metrics(version, quality_metrics, True)
        return True
    
    def _record_quality_metrics(self, version: Dict[str, Any], metrics: Dict[str, float], passed: bool) -> None:
        """记录版本质量指标历史
        
        Args:
            version: 版本信息
            metrics: 质量指标
            passed: 是否通过检查
        """
        record = {
            "version_id": version.get("id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "passed": passed
        }
        self.quality_metrics_history.append(record)
        
        # 保持历史记录不超过100条
        if len(self.quality_metrics_history) > 100:
            self.quality_metrics_history = self.quality_metrics_history[-100:]
    
    def get_quality_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的质量检查历史
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            质量检查历史记录
        """
        return self.quality_metrics_history[-limit:]
    
    def get_status(self) -> Dict[str, Any]:
        """获取熔断器当前状态
        
        Returns:
            状态信息字典
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_threshold": self.recovery_threshold,
            "state_change_time": self.state_change_time.isoformat(),
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }
    
    def manually_reset(self) -> None:
        """手动重置熔断器状态"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.state_change_time = datetime.now()
        logger.info("熔断器已手动重置为关闭状态")
    
    def manually_open(self, reason: str = "手动触发") -> None:
        """手动开启熔断器
        
        Args:
            reason: 开启原因
        """
        self.state = CircuitBreakerState.OPEN
        self.state_change_time = datetime.now()
        logger.warning(f"熔断器已手动开启，原因: {reason}")

# 全局熔断器实例
_global_guardian = None

def get_quality_guardian(config_path: Optional[str] = None) -> QualityGuardian:
    """获取质量守护者全局实例
    
    Args:
        config_path: 配置文件路径，可选
        
    Returns:
        QualityGuardian实例
    """
    global _global_guardian
    
    if _global_guardian is None:
        _global_guardian = QualityGuardian(config_path)
    
    return _global_guardian

# 演示用例
def demo():
    """演示质量熔断器功能"""
    guardian = QualityGuardian(failure_threshold=2)
    
    # 模拟版本评估
    print("模拟版本质量检查...")
    
    # 创建模拟版本
    versions = [
        {"id": "v1.0.0", "quality_score": 0.85, "narrative_coherence": 0.9},
        {"id": "v1.1.0", "quality_score": 0.75, "narrative_coherence": 0.8},
        {"id": "v1.2.0-bad", "quality_score": 0.55, "narrative_coherence": 0.4},
        {"id": "v1.2.1-bad", "quality_score": 0.45, "narrative_coherence": 0.3}
    ]
    
    # 添加自定义检查器
    guardian.add_custom_checker(
        "quality_score", 
        lambda v: v.get("quality_score", 0), 
        0.7
    )
    
    # 测试质量监控
    try:
        # 这两个版本应该能通过
        guardian.monitor([versions[0], versions[1]])
        print("前两个版本通过质量检查")
        
        # 这两个版本应该会触发熔断
        guardian.monitor([versions[2], versions[3]])
    except QualityCollapseError as e:
        print(f"熔断器已触发: {str(e)}")
    
    # 显示熔断器状态
    status = guardian.get_status()
    print(f"熔断器状态: {status['state']}")
    print(f"失败计数: {status['failure_count']}/{status['failure_threshold']}")
    
    # 手动重置熔断器
    print("手动重置熔断器...")
    guardian.manually_reset()
    
    # 显示重置后状态
    status = guardian.get_status()
    print(f"重置后熔断器状态: {status['state']}")
    print(f"失败计数: {status['failure_count']}/{status['failure_threshold']}")
    
    # 显示质量检查历史
    history = guardian.get_quality_history()
    print(f"\n质量检查历史记录 (最近{len(history)}条):")
    for record in history:
        print(f"版本 {record['version_id']}: {'通过' if record['passed'] else '未通过'}")
        for metric, score in record['metrics'].items():
            print(f"  - {metric}: {score:.2f}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行演示
    demo() 