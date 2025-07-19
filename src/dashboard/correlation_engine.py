#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能关联分析引擎

该模块提供智能关联分析功能，用于发现系统异常事件之间的关联关系，
帮助用户更好地理解系统性能问题和内存使用模式，尤其是在4GB内存的
低端硬件环境下，可以快速定位内存压力、缓存失效和系统中断等关联事件。
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np
from pathlib import Path

# 导入项目相关模块
from src.utils.exceptions import AnalysisError
from src.exporters.log_query import search_logs, get_log_statistics

# 初始化日志
logger = logging.getLogger("correlation_engine")


class CorrelationAnalyzer:
    """智能关联分析器，用于分析系统中的事件关联性和因果关系"""
    
    # 事件类型定义
    EVENT_TYPES = {
        "MEMORY": ["memory_allocation", "memory_release", "memory_pressure", "oom_risk"],
        "MODEL": ["model_loading", "model_inference", "model_unloading", "cache_miss"],
        "SYSTEM": ["temperature_high", "disk_io", "hardware_interrupt", "system_freeze"],
        "CACHE": ["cache_hit", "cache_miss", "cache_eviction", "cache_refresh"],
        "PROCESS": ["process_start", "process_end", "thread_spawn", "thread_terminate"]
    }
    
    # 关联类型定义
    CORRELATION_TYPES = {
        "CAUSAL": "因果关系",
        "TEMPORAL": "时间关联",
        "STATISTICAL": "统计相关",
        "CONTEXTUAL": "上下文关联"
    }
    
    def __init__(self, log_db=None, data_aggregator=None):
        """初始化关联分析器
        
        Args:
            log_db: 日志数据库接口
            data_aggregator: 数据聚合器实例
        """
        # 日志数据库连接
        self.log_db = log_db or self._get_default_log_db()
        
        # 数据聚合器
        self.data_aggregator = data_aggregator
        
        # 事件缓存
        self.event_cache = {}
        
        # 已识别的关联模式
        self.known_patterns = self._load_known_patterns()
        
        # 最近分析结果缓存
        self.analysis_cache = {}
        
        logger.info("智能关联分析引擎初始化完成")
    
    def _get_default_log_db(self):
        """获取默认日志数据库连接"""
        # 如果没有提供日志数据库，使用内部简单实现
        class SimpleLogDB:
            def query(self, query_str):
                """简单查询实现"""
                try:
                    # 使用log_query模块搜索日志
                    return search_logs(query_str)
                except Exception as e:
                    logger.error(f"日志查询失败: {e}")
                    return []
        
        return SimpleLogDB()
    
    def _load_known_patterns(self) -> Dict[str, Any]:
        """加载已知的关联模式
        
        Returns:
            Dict: 包含已知关联模式的字典
        """
        # 尝试从配置文件加载
        patterns_file = Path("configs/analysis/correlation_patterns.json")
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"无法加载关联模式文件: {e}")
        
        # 返回默认模式
        return {
            "memory_pressure_model_load": {
                "pattern": ["memory_pressure", "model_loading"],
                "time_window": 300,  # 5分钟
                "confidence": 0.8,
                "description": "模型加载前后的内存压力变化"
            },
            "cache_miss_model_inference": {
                "pattern": ["cache_miss", "model_inference", "memory_allocation"],
                "time_window": 60,  # 1分钟
                "confidence": 0.7,
                "description": "缓存失效导致的模型推理和内存分配"
            },
            "system_freeze_memory_pressure": {
                "pattern": ["memory_pressure", "system_freeze", "hardware_interrupt"],
                "time_window": 180,  # 3分钟
                "confidence": 0.9,
                "description": "内存压力导致的系统冻结和硬件中断"
            }
        }
    
    def find_anomaly_correlations(self, anomaly_time):
        """分析异常时刻的关联事件
        
        Args:
            anomaly_time: 异常发生的时间戳
            
        Returns:
            Dict: 包含关联分析结果
        """
        """分析异常时刻的关联事件"""
        # 查询异常前后的事件
        events = self.log_db.query(f"timestamp BETWEEN {anomaly_time-300} AND {anomaly_time}")
        
        return {
            "top_modules": self._count_by_module(events),
            "event_chain": self._build_causality_chain(events)
        }
    
    def analyze_time_period(self, start_time, end_time, focus_areas=None):
        """分析指定时间段内的事件关联性
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            focus_areas: 关注的领域，如 ["MEMORY", "MODEL"]
            
        Returns:
            Dict: 分析结果
        """
        # 生成缓存键
        cache_key = f"{start_time}_{end_time}_{focus_areas}"
        
        # 检查缓存
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 查询事件
        query_areas = ""
        if focus_areas:
            area_types = [event for area in focus_areas for event in self.EVENT_TYPES.get(area, [])]
            if area_types:
                query_areas = f" AND event_type IN ({','.join(area_types)})"
        
        events = self.log_db.query(f"timestamp BETWEEN {start_time} AND {end_time}{query_areas}")
        
        # 执行分析
        analysis_result = {
            "event_count": len(events),
            "time_range": {
                "start": start_time,
                "end": end_time,
                "duration_seconds": end_time - start_time
            },
            "top_modules": self._count_by_module(events),
            "event_distribution": self._analyze_event_distribution(events),
            "key_correlations": self._find_key_correlations(events),
            "anomaly_points": self._detect_anomaly_points(events),
            "causality_chains": self._build_causality_chain(events)
        }
        
        # 缓存结果
        self.analysis_cache[cache_key] = analysis_result
        
        return analysis_result
    
    def _count_by_module(self, events) -> Dict[str, int]:
        """按模块统计事件数量
        
        Args:
            events: 事件列表
            
        Returns:
            Dict: 各模块的事件数量统计
        """
        # 统计各模块的事件数量
        module_counts = Counter()
        
        for event in events:
            module = event.get("module", "unknown")
            module_counts[module] += 1
        
        # 返回按数量降序排列的模块统计
        return dict(module_counts.most_common(10))
    
    def _analyze_event_distribution(self, events) -> Dict[str, Any]:
        """分析事件分布
        
        Args:
            events: 事件列表
            
        Returns:
            Dict: 事件分布分析结果
        """
        # 按类型统计事件
        type_counts = Counter()
        severity_counts = Counter()
        temporal_distribution = defaultdict(int)
        
        for event in events:
            # 统计事件类型
            event_type = event.get("event_type", "unknown")
            type_counts[event_type] += 1
            
            # 统计严重级别
            severity = event.get("severity", "info")
            severity_counts[severity] += 1
            
            # 时间分布（按小时分组）
            try:
                event_time = event.get("timestamp")
                if isinstance(event_time, (int, float)):
                    hour = datetime.fromtimestamp(event_time).hour
                    temporal_distribution[hour] += 1
            except (ValueError, TypeError):
                pass
        
        return {
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
            "temporal": dict(sorted(temporal_distribution.items()))
        }
    
    def _find_key_correlations(self, events) -> List[Dict[str, Any]]:
        """查找关键关联关系
        
        Args:
            events: 事件列表
            
        Returns:
            List: 关键关联关系列表
        """
        correlations = []
        
        # 按时间排序事件
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        # 查找匹配已知模式的事件序列
        for pattern_name, pattern_info in self.known_patterns.items():
            pattern_seq = pattern_info["pattern"]
            time_window = pattern_info["time_window"]
            
            # 查找匹配模式的事件序列
            for i in range(len(sorted_events)):
                if self._match_pattern(sorted_events[i:], pattern_seq, time_window):
                    # 找到匹配，添加到关联列表
                    correlations.append({
                        "pattern": pattern_name,
                        "description": pattern_info["description"],
                        "confidence": pattern_info["confidence"],
                        "events": sorted_events[i:i+len(pattern_seq)],
                        "start_time": sorted_events[i].get("timestamp"),
                        "end_time": sorted_events[min(i+len(pattern_seq)-1, len(sorted_events)-1)].get("timestamp")
                    })
        
        # 按置信度排序
        return sorted(correlations, key=lambda x: x["confidence"], reverse=True)
    
    def _match_pattern(self, events, pattern, time_window) -> bool:
        """检查事件序列是否匹配给定模式
        
        Args:
            events: 事件列表
            pattern: 模式序列
            time_window: 时间窗口（秒）
            
        Returns:
            bool: 是否匹配
        """
        if len(events) < len(pattern):
            return False
        
        # 检查第一个和最后一个事件的时间差
        try:
            start_time = events[0].get("timestamp", 0)
            end_time = events[len(pattern)-1].get("timestamp", 0)
            
            if end_time - start_time > time_window:
                return False
        except (IndexError, TypeError):
            return False
        
        # 检查事件类型是否匹配模式
        for i, pattern_type in enumerate(pattern):
            if i >= len(events):
                return False
                
            event_type = events[i].get("event_type", "unknown")
            if event_type != pattern_type:
                return False
        
        return True
    
    def _detect_anomaly_points(self, events) -> List[Dict[str, Any]]:
        """检测异常点
        
        Args:
            events: 事件列表
            
        Returns:
            List: 异常点列表
        """
        anomalies = []
        
        # 按时间排序事件
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        # 查找异常密度（短时间内大量事件）
        if len(sorted_events) >= 3:
            for i in range(len(sorted_events) - 2):
                start_time = sorted_events[i].get("timestamp", 0)
                end_time = sorted_events[i+2].get("timestamp", 0)
                
                # 如果3个事件在10秒内，可能是异常
                if end_time - start_time <= 10:
                    anomalies.append({
                        "type": "event_burst",
                        "description": "短时间内事件突发",
                        "timestamp": start_time,
                        "events": sorted_events[i:i+3],
                        "severity": "medium"
                    })
        
        # 查找关键错误事件
        for event in sorted_events:
            if event.get("severity") in ["error", "critical"] or event.get("level") in ["ERROR", "CRITICAL"]:
                anomalies.append({
                    "type": "critical_error",
                    "description": event.get("message", "关键错误"),
                    "timestamp": event.get("timestamp", 0),
                    "event": event,
                    "severity": "high"
                })
        
        return anomalies
    
    def _build_causality_chain(self, events) -> List[Dict[str, Any]]:
        """构建事件因果链
        
        Args:
            events: 事件列表
            
        Returns:
            List: 因果链列表
        """
        # 按时间排序事件
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        # 创建因果链
        chains = []
        current_chain = []
        
        # 定义可能的因果关系
        causal_pairs = [
            ("memory_allocation", "memory_pressure"),
            ("model_loading", "memory_pressure"),
            ("cache_miss", "model_inference"),
            ("memory_pressure", "system_freeze"),
            ("system_freeze", "hardware_interrupt")
        ]
        
        # 分析事件序列，构建因果链
        for i in range(len(sorted_events) - 1):
            current_event = sorted_events[i]
            next_event = sorted_events[i + 1]
            
            current_type = current_event.get("event_type", "unknown")
            next_type = next_event.get("event_type", "unknown")
            
            # 检查是否是因果对
            for cause, effect in causal_pairs:
                if current_type == cause and next_type == effect:
                    # 创建新链或继续现有链
                    if not current_chain:
                        current_chain = [current_event]
                    
                    current_chain.append(next_event)
                    break
            else:
                # 不是因果对，结束当前链
                if len(current_chain) >= 2:
                    chains.append({
                        "events": current_chain.copy(),
                        "start_time": current_chain[0].get("timestamp", 0),
                        "end_time": current_chain[-1].get("timestamp", 0),
                        "description": self._describe_chain(current_chain)
                    })
                    current_chain = []
        
        # 处理最后一个链
        if len(current_chain) >= 2:
            chains.append({
                "events": current_chain,
                "start_time": current_chain[0].get("timestamp", 0),
                "end_time": current_chain[-1].get("timestamp", 0),
                "description": self._describe_chain(current_chain)
            })
        
        return chains
    
    def _describe_chain(self, chain) -> str:
        """为因果链生成描述
        
        Args:
            chain: 事件链
            
        Returns:
            str: 链描述
        """
        if not chain:
            return "空事件链"
        
        # 获取链中的事件类型
        event_types = [event.get("event_type", "unknown") for event in chain]
        
        # 通过模式匹配获取描述
        if set(event_types) == set(["memory_allocation", "memory_pressure"]):
            return "内存分配与释放调用栈"
        elif set(event_types) == set(["model_loading", "memory_pressure"]):
            return "模型加载与缓存失效事件"
        elif set(event_types) == set(["memory_pressure", "system_freeze", "hardware_interrupt"]):
            return "系统调度与硬件中断"
        else:
            return f"事件序列: {' -> '.join(event_types)}"
    
    def recommend_optimizations(self, analysis_result) -> List[Dict[str, Any]]:
        """基于分析结果推荐优化方案
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            List: 优化建议列表
        """
        recommendations = []
        
        # 检查分析结果中的关键点
        if not analysis_result:
            return recommendations
        
        # 内存优化建议
        if "top_modules" in analysis_result:
            top_modules = analysis_result["top_modules"]
            if top_modules:
                # 找出事件最多的模块
                top_module = next(iter(top_modules))
                
                recommendations.append({
                    "target": "memory",
                    "priority": "high" if top_modules[top_module] > 5 else "medium",
                    "description": f"优化 {top_module} 模块的内存使用",
                    "action": "review_memory_usage",
                    "details": f"模块 {top_module} 在分析期间产生了 {top_modules[top_module]} 个事件"
                })
        
        # 模型加载优化建议
        if "causality_chains" in analysis_result:
            for chain in analysis_result["causality_chains"]:
                if "模型加载" in chain.get("description", ""):
                    recommendations.append({
                        "target": "model_loading",
                        "priority": "high",
                        "description": "优化模型加载策略",
                        "action": "implement_progressive_loading",
                        "details": "检测到模型加载与内存压力的因果关系，建议实施渐进式加载策略"
                    })
                elif "系统调度" in chain.get("description", ""):
                    recommendations.append({
                        "target": "system",
                        "priority": "medium",
                        "description": "检查系统中断处理",
                        "action": "optimize_interrupt_handling",
                        "details": "检测到系统中断可能导致性能问题，建议优化中断处理逻辑"
                    })
        
        return recommendations
    
    def explain_correlation(self, correlation_id, detail_level="medium") -> Dict[str, Any]:
        """解释特定关联的详细情况
        
        Args:
            correlation_id: 关联ID或索引
            detail_level: 详细程度（low/medium/high）
            
        Returns:
            Dict: 关联解释
        """
        # 查找关联详情
        correlation = None
        
        # 假设correlation_id是最近分析结果的索引
        if isinstance(correlation_id, int):
            recent_results = list(self.analysis_cache.values())
            if recent_results and 0 <= correlation_id < len(recent_results[-1].get("key_correlations", [])):
                correlation = recent_results[-1]["key_correlations"][correlation_id]
        
        if not correlation:
            return {"error": "未找到指定的关联"}
        
        # 生成不同详细程度的解释
        explanation = {
            "correlation": correlation["pattern"],
            "description": correlation["description"],
            "confidence": correlation["confidence"],
            "time_range": {
                "start": correlation["start_time"],
                "end": correlation["end_time"],
                "duration": correlation["end_time"] - correlation["start_time"]
            }
        }
        
        # 添加更详细的信息
        if detail_level in ["medium", "high"]:
            explanation["events"] = [self._summarize_event(e) for e in correlation["events"]]
            
            if detail_level == "high":
                explanation["raw_data"] = correlation["events"]
                explanation["technical_explanation"] = self._generate_technical_explanation(correlation)
        
        return explanation
    
    def _summarize_event(self, event) -> Dict[str, Any]:
        """生成事件摘要
        
        Args:
            event: 完整事件数据
            
        Returns:
            Dict: 事件摘要
        """
        return {
            "type": event.get("event_type", "unknown"),
            "time": event.get("timestamp", 0),
            "module": event.get("module", "unknown"),
            "summary": event.get("message", "")[:100] + ("..." if len(event.get("message", "")) > 100 else "")
        }
    
    def _generate_technical_explanation(self, correlation) -> str:
        """生成技术解释
        
        Args:
            correlation: 关联数据
            
        Returns:
            str: 技术解释文本
        """
        pattern_name = correlation["pattern"]
        
        # 根据模式类型提供技术解释
        if "memory_pressure" in pattern_name:
            return (
                "内存压力事件通常表示系统内存接近极限。当模型加载或大量数据处理时，"
                "可能导致内存压力增加。在4GB低内存环境中，这种情况尤为常见，因为可用"
                "内存十分有限。建议考虑实施渐进式加载、部分量化或内存优化策略。"
            )
        elif "cache_miss" in pattern_name:
            return (
                "缓存未命中通常会触发额外的模型推理计算，这会导致性能下降和额外的"
                "内存分配。在低内存环境中，频繁的缓存未命中可能导致严重的性能问题。"
                "建议优化缓存策略，增加热点数据的缓存优先级。"
            )
        elif "system_freeze" in pattern_name:
            return (
                "系统冻结通常是由于内存压力过大或处理器过载导致的。当系统尝试恢复时，"
                "可能会生成硬件中断以释放资源。这种情况在资源受限的系统中尤为常见。"
                "建议检查系统资源监控和调度逻辑，优化关键路径的资源使用。"
            )
        else:
            return (
                f"此关联模式 '{pattern_name}' 反映了系统中多个组件之间的相互作用。"
                "通过分析事件的时间顺序和上下文，可以推断出这些事件之间存在因果关系。"
                "建议深入研究这些事件的详细日志以确定优化策略。"
            )

# 工厂函数
def create_correlation_analyzer(log_db=None, data_aggregator=None):
    """创建关联分析器实例
    
    Args:
        log_db: 日志数据库接口
        data_aggregator: 数据聚合器实例
        
    Returns:
        CorrelationAnalyzer: 关联分析器实例
    """
    return CorrelationAnalyzer(log_db, data_aggregator)


if __name__ == "__main__":
    # 测试关联分析器
    analyzer = CorrelationAnalyzer()
    
    # 模拟异常时间
    anomaly_time = int(time.time())
    
    # 分析关联事件
    result = analyzer.find_anomaly_correlations(anomaly_time)
    
    # 打印分析结果
    print(json.dumps(result, indent=2, ensure_ascii=False)) 