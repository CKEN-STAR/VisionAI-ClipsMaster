#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
熔断知识库系统
----------
提供内存问题诊断和解决方案的知识库
基于历史案例和模式识别进行智能诊断
"""

import os
import json
import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fuse_knowledge_base")


class FuseKB:
    """熔断知识库，提供内存问题诊断和解决方案"""
    
    # 案例数据库 - 记录已知的内存问题案例
    CASE_DB = {
        # 内存溢出案例 - Out Of Memory
        "OOM_001": {
            "symptoms": "内存5分钟内从60%升至98%",
            "pattern": "rapid_increase",
            "root_cause": "模型分片泄漏",
            "solution": "升级分片加载器v2.3+",
            "severity": "critical",
            "impact": ["视频处理中断", "可能导致系统崩溃"],
            "detection": "检测到内存使用率在短时间内快速增长超过35%"
        },
        "OOM_002": {
            "symptoms": "内存缓慢增长不释放，最终达到95%以上",
            "pattern": "steady_increase",
            "root_cause": "视频缓冲区未释放",
            "solution": "在视频切换时强制调用gc并手动清理缓冲区",
            "severity": "high",
            "impact": ["系统变慢", "最终导致内存不足"],
            "detection": "监测到GC后内存占用无明显下降"
        },
        "OOM_003": {
            "symptoms": "处理大型视频时内存瞬间飙升至90%以上",
            "pattern": "spike",
            "root_cause": "视频解码缓冲区过大",
            "solution": "使用流式解码方式，限制最大缓冲区大小",
            "severity": "high",
            "impact": ["大型视频处理失败"],
            "detection": "监测到内存使用率瞬间增加超过40%"
        },
        
        # 内存碎片案例
        "FRAG_001": {
            "symptoms": "内存使用率中等但分配新内存时失败",
            "pattern": "fragmentation",
            "root_cause": "长时间运行导致内存碎片化",
            "solution": "定期完全重启服务或使用压缩内存分配器",
            "severity": "medium",
            "impact": ["大型视频处理失败", "系统不稳定"],
            "detection": "已使用内存低于70%但内存分配仍然失败"
        },
        "FRAG_002": {
            "symptoms": "系统长时间运行后逐渐变慢，内存使用不高",
            "pattern": "fragmentation",
            "root_cause": "字幕处理导致的内存碎片",
            "solution": "优化字幕缓存管理，定期整理内存",
            "severity": "low",
            "impact": ["系统性能下降"],
            "detection": "系统运行超过72小时且处理速度下降30%以上"
        },
        
        # 内存泄漏案例
        "LEAK_001": {
            "symptoms": "内存使用率稳定增长，重启后恢复",
            "pattern": "steady_increase",
            "root_cause": "字幕解析器资源未释放",
            "solution": "修复字幕解析器的资源管理机制",
            "severity": "medium",
            "impact": ["需要频繁重启", "长视频处理失败"],
            "detection": "每处理100个字幕内存增加约5MB且不释放"
        },
        "LEAK_002": {
            "symptoms": "GPU内存缓慢增长直至耗尽",
            "pattern": "steady_increase",
            "root_cause": "CUDA张量缓存未正确释放",
            "solution": "在模型推理后显式清理CUDA缓存",
            "severity": "high",
            "impact": ["GPU加速失效", "系统自动切换到CPU模式变慢"],
            "detection": "GPU内存监控显示使用量持续增长不释放"
        },
        
        # 资源争用案例
        "CONT_001": {
            "symptoms": "并行处理时内存使用忽高忽低",
            "pattern": "fluctuation",
            "root_cause": "多任务资源争用",
            "solution": "实现更智能的任务调度和资源分配机制",
            "severity": "medium",
            "impact": ["处理效率下降", "任务完成时间不稳定"],
            "detection": "内存使用率波动超过25%且CPU使用率达到90%以上"
        },
        
        # 配置不当案例
        "CONF_001": {
            "symptoms": "启动即达到高内存占用",
            "pattern": "immediate_high",
            "root_cause": "视频缓冲区初始配置过大",
            "solution": "调整配置文件中的max_buffer_size参数",
            "severity": "medium",
            "impact": ["无法处理多个视频", "系统启动慢"],
            "detection": "启动5分钟内内存使用率即超过60%"
        },
        "CONF_002": {
            "symptoms": "特定类型视频处理时内存溢出",
            "pattern": "specific_trigger",
            "root_cause": "高分辨率视频的缓冲策略不当",
            "solution": "为高分辨率视频实现自适应缓冲策略",
            "severity": "medium",
            "impact": ["高清视频处理失败"],
            "detection": "处理分辨率高于4K的视频时内存使用率超过85%"
        }
    }
    
    def __init__(self, custom_cases_path: str = None):
        """
        初始化熔断知识库
        
        Args:
            custom_cases_path: 自定义案例数据库的JSON文件路径
        """
        self.cases = self.CASE_DB.copy()
        
        # 加载自定义案例
        if custom_cases_path and os.path.exists(custom_cases_path):
            self._load_custom_cases(custom_cases_path)
            
        # 统计信息
        self.diagnosis_count = 0
        self.match_history = []
        self.last_update_time = time.time()
        
        logger.info(f"熔断知识库初始化完成，共加载 {len(self.cases)} 个案例")
    
    def _load_custom_cases(self, file_path: str):
        """
        加载自定义案例数据库
        
        Args:
            file_path: JSON文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                custom_cases = json.load(f)
                
            # 合并到现有案例
            for case_id, case_data in custom_cases.items():
                self.cases[case_id] = case_data
                
            logger.info(f"从 {file_path} 加载了 {len(custom_cases)} 个自定义案例")
        except Exception as e:
            logger.error(f"加载自定义案例失败: {e}")
    
    def diagnose(self, pressure_data: Union[List, Dict, np.ndarray], 
                system_info: Dict = None) -> Dict:
        """
        基于历史案例和模式识别诊断内存问题
        
        Args:
            pressure_data: 内存压力数据，可以是时间序列或特征图
            system_info: 系统信息，如运行时间、任务类型等
            
        Returns:
            包含诊断结果和建议的字典
        """
        # 记录诊断计数
        self.diagnosis_count += 1
        
        # 提取内存压力模式
        pattern = self._extract_pattern(pressure_data)
        
        # 查找最相似的案例
        similar_cases = self._find_similar_cases(pattern, system_info)
        
        # 如果没有找到相似案例，返回通用建议
        if not similar_cases:
            return self._generate_generic_advice(pattern, system_info)
        
        # 获取最匹配的案例
        best_match = similar_cases[0]
        case_id = best_match["case_id"]
        case = self.cases[case_id]
        similarity = best_match["similarity"]
        
        # 记录匹配历史
        self.match_history.append({
            "timestamp": time.time(),
            "pattern": pattern,
            "matched_case": case_id,
            "similarity": similarity
        })
        
        # 构建诊断结果
        result = {
            "diagnosis_id": f"DIAG_{int(time.time())}_{self.diagnosis_count}",
            "timestamp": datetime.datetime.now().isoformat(),
            "matched_case": case_id,
            "confidence": similarity,
            "root_cause": case["root_cause"],
            "solution": case["solution"],
            "severity": case["severity"],
            "impact": case.get("impact", []),
            "similar_cases": [c["case_id"] for c in similar_cases[1:3]]  # 次优匹配
        }
        
        logger.info(f"诊断完成: 匹配案例 {case_id}，置信度 {similarity:.2f}")
        return result
    
    def _extract_pattern(self, pressure_data) -> Dict:
        """
        从内存压力数据中提取模式特征
        
        Args:
            pressure_data: 内存压力数据
            
        Returns:
            提取的模式特征字典
        """
        # 转换输入数据为numpy数组以便处理
        if isinstance(pressure_data, dict) and "readings" in pressure_data:
            # 从仪表盘数据格式提取
            values = [reading[1] for reading in pressure_data["readings"]]
            timestamps = [reading[0] for reading in pressure_data["readings"]]
            data = np.array(values)
        elif isinstance(pressure_data, list):
            if all(isinstance(item, dict) and "value" in item for item in pressure_data):
                # 从事件记录格式提取
                data = np.array([item["value"] for item in pressure_data])
            else:
                # 假设是纯数值列表
                data = np.array(pressure_data)
        else:
            # 直接使用（假设已经是numpy数组）
            data = pressure_data
        
        # 确保数据是一维数组
        if hasattr(data, 'ndim') and data.ndim > 1:
            data = data.flatten()
            
        # 如果数据太少，无法提取有意义的模式
        if len(data) < 3:
            return {"pattern": "unknown", "features": {}}
            
        # 计算基本统计特征
        features = {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "range": float(np.max(data) - np.min(data)),
            "current": float(data[-1])
        }
        
        # 计算增长率
        if len(data) >= 2:
            growth_rate = (data[-1] - data[0]) / max(1, len(data))
            features["growth_rate"] = float(growth_rate)
            
            # 计算局部增长率（最近3个点）
            if len(data) >= 3:
                recent_growth = (data[-1] - data[-3]) / 2
                features["recent_growth"] = float(recent_growth)
        
        # 计算波动性 - 使用变异系数
        if features["mean"] > 0:
            features["volatility"] = float(features["std"] / features["mean"])
        else:
            features["volatility"] = 0.0
            
        # 计算趋势 - 使用简单线性回归斜率
        x = np.arange(len(data))
        if len(x) > 1:
            polyfit = np.polyfit(x, data, 1)
            features["trend"] = float(polyfit[0])
        else:
            features["trend"] = 0.0
            
        # 识别模式类型
        pattern = self._identify_pattern(features, data)
        
        return {
            "pattern": pattern,
            "features": features
        }
    
    def _identify_pattern(self, features: Dict, data: np.ndarray) -> str:
        """
        根据特征识别内存压力模式
        
        Args:
            features: 提取的特征
            data: 原始数据
            
        Returns:
            模式类型
        """
        # 快速增长模式
        if features["trend"] > 5 and features["range"] > 30:
            return "rapid_increase"
            
        # 平稳增长模式
        if 0.5 < features["trend"] < 5 and features["volatility"] < 0.2:
            return "steady_increase"
            
        # 峰值模式 - 检查是否有短时间内的大幅上升
        if features["range"] > 40 and features["volatility"] > 0.3:
            return "spike"
            
        # 波动模式
        if features["volatility"] > 0.25 and abs(features["trend"]) < 1:
            return "fluctuation"
            
        # 高原模式 - 维持在高位
        if features["mean"] > 75 and features["volatility"] < 0.15:
            return "plateau_high"
            
        # 立即高位模式 - 一开始就很高
        if features["min"] > 60 and len(data) > 5:
            return "immediate_high"
            
        # 碎片化模式 - 理论上难以直接从内存使用率检测，需要结合其他信息
        if "fragmentation_hint" in features:
            return "fragmentation"
            
        # 默认模式
        if features["trend"] > 0:
            return "gradual_increase"
        elif features["trend"] < 0:
            return "gradual_decrease"
        else:
            return "stable"
    
    def _find_similar_cases(self, pattern: Dict, system_info: Dict = None) -> List[Dict]:
        """
        查找与当前问题最相似的案例
        
        Args:
            pattern: 当前问题的模式特征
            system_info: 系统信息
            
        Returns:
            按相似度排序的案例列表
        """
        pattern_type = pattern["pattern"]
        features = pattern["features"]
        
        matched_cases = []
        
        for case_id, case in self.cases.items():
            # 计算模式匹配分数
            pattern_score = self._calculate_pattern_match(pattern_type, case.get("pattern", "unknown"))
            
            # 如果模式完全不匹配，跳过此案例
            if pattern_score == 0:
                continue
                
            # 计算特征相似度
            feature_score = self._calculate_feature_similarity(features, case)
            
            # 计算系统信息匹配分数
            context_score = 1.0
            if system_info:
                context_score = self._calculate_context_match(system_info, case)
                
            # 计算总相似度
            similarity = pattern_score * 0.5 + feature_score * 0.3 + context_score * 0.2
            
            matched_cases.append({
                "case_id": case_id,
                "similarity": similarity,
                "pattern_score": pattern_score,
                "feature_score": feature_score,
                "context_score": context_score
            })
        
        # 按相似度排序
        matched_cases.sort(key=lambda x: x["similarity"], reverse=True)
        
        return matched_cases
    
    def _calculate_pattern_match(self, current_pattern: str, case_pattern: str) -> float:
        """
        计算模式匹配分数
        
        Args:
            current_pattern: 当前问题的模式
            case_pattern: 案例的模式
            
        Returns:
            匹配分数 (0-1)
        """
        # 如果模式完全匹配
        if current_pattern == case_pattern:
            return 1.0
            
        # 模式相关性表 - 表示不同模式之间的相关程度
        pattern_similarity = {
            "rapid_increase": {
                "steady_increase": 0.6,
                "spike": 0.7,
                "gradual_increase": 0.5
            },
            "steady_increase": {
                "rapid_increase": 0.6,
                "gradual_increase": 0.8,
                "plateau_high": 0.4
            },
            "spike": {
                "rapid_increase": 0.7,
                "fluctuation": 0.5
            },
            "fluctuation": {
                "spike": 0.5
            },
            "plateau_high": {
                "immediate_high": 0.6,
                "steady_increase": 0.4
            },
            "immediate_high": {
                "plateau_high": 0.6
            },
            "fragmentation": {
                "gradual_increase": 0.3
            },
            "gradual_increase": {
                "steady_increase": 0.8,
                "rapid_increase": 0.5
            },
            "gradual_decrease": {},
            "stable": {}
        }
        
        # 查找相关模式的匹配分数
        if current_pattern in pattern_similarity and case_pattern in pattern_similarity[current_pattern]:
            return pattern_similarity[current_pattern][case_pattern]
            
        # 默认返回低相关性
        return 0.1
    
    def _calculate_feature_similarity(self, features: Dict, case: Dict) -> float:
        """
        计算特征相似度
        
        Args:
            features: 当前问题的特征
            case: 候选案例
            
        Returns:
            特征相似度分数 (0-1)
        """
        # 提取案例中的症状描述，用于启发式匹配
        symptoms = case.get("symptoms", "")
        
        # 基于症状的启发式匹配
        score = 0.5  # 默认中等相似度
        
        # 高内存使用率相关匹配
        if "使用率" in symptoms and "高" in symptoms:
            if features["max"] > 90:
                score += 0.2
            elif features["max"] > 80:
                score += 0.1
                
        # 内存增长相关匹配
        if "增长" in symptoms:
            if "快速" in symptoms or "飙升" in symptoms:
                if features["trend"] > 3:
                    score += 0.3
                elif features["trend"] > 1:
                    score += 0.1
            elif "缓慢" in symptoms or "逐渐" in symptoms:
                if 0 < features["trend"] < 2:
                    score += 0.3
                    
        # 波动相关匹配
        if "波动" in symptoms or "忽高忽低" in symptoms:
            if features["volatility"] > 0.25:
                score += 0.2
                
        # 确保分数在0-1范围内
        return min(1.0, max(0.0, score))
    
    def _calculate_context_match(self, system_info: Dict, case: Dict) -> float:
        """
        计算系统上下文匹配分数
        
        Args:
            system_info: 当前系统信息
            case: 候选案例
            
        Returns:
            上下文匹配分数 (0-1)
        """
        # 默认中等匹配度
        score = 0.5
        
        # 提取案例可能包含的上下文信息
        case_impacts = case.get("impact", [])
        detection_rule = case.get("detection", "")
        
        # 根据任务类型匹配
        if "task_type" in system_info:
            task = system_info["task_type"]
            
            if any(impact_text for impact_text in case_impacts if task.lower() in impact_text.lower()):
                score += 0.2
                
        # 根据运行时间匹配
        if "uptime_hours" in system_info and "长时间" in detection_rule:
            uptime = system_info["uptime_hours"]
            if uptime > 72 and "长时间" in detection_rule:
                score += 0.2
                
        # 根据视频大小或类型匹配
        if "video_size_gb" in system_info:
            video_size = system_info["video_size_gb"]
            if video_size > 2 and any("大型视频" in impact for impact in case_impacts):
                score += 0.2
                
        # 确保分数在0-1范围内
        return min(1.0, max(0.0, score))
    
    def _generate_generic_advice(self, pattern: Dict, system_info: Dict = None) -> Dict:
        """
        当没有匹配案例时生成通用建议
        
        Args:
            pattern: 当前问题的模式
            system_info: 系统信息
            
        Returns:
            通用建议
        """
        pattern_type = pattern["pattern"]
        features = pattern["features"]
        
        # 根据不同模式给出通用建议
        if pattern_type == "rapid_increase":
            advice = {
                "diagnosis_id": f"GENERIC_{int(time.time())}",
                "timestamp": datetime.datetime.now().isoformat(),
                "matched_case": None,
                "confidence": 0.4,
                "root_cause": "可能存在大量资源未释放或内存泄漏",
                "solution": "检查最近添加的代码，启用详细内存监控，考虑增加内存释放点",
                "severity": "high",
                "impact": ["系统可能很快发生内存不足", "处理大型数据可能失败"]
            }
        elif pattern_type == "steady_increase":
            advice = {
                "diagnosis_id": f"GENERIC_{int(time.time())}",
                "timestamp": datetime.datetime.now().isoformat(),
                "matched_case": None,
                "confidence": 0.4,
                "root_cause": "可能存在累积性内存泄漏",
                "solution": "启用定期内存清理，检查循环中的资源管理，考虑定期重启服务",
                "severity": "medium",
                "impact": ["长时间运行后系统将变慢", "最终可能需要重启"]
            }
        elif pattern_type == "fluctuation":
            advice = {
                "diagnosis_id": f"GENERIC_{int(time.time())}",
                "timestamp": datetime.datetime.now().isoformat(),
                "matched_case": None,
                "confidence": 0.3,
                "root_cause": "资源争用或不当的内存管理策略",
                "solution": "优化并发任务调度，检查内存分配与释放的时机",
                "severity": "low",
                "impact": ["系统性能不稳定", "可能在高负载时出现问题"]
            }
        else:
            advice = {
                "diagnosis_id": f"GENERIC_{int(time.time())}",
                "timestamp": datetime.datetime.now().isoformat(),
                "matched_case": None,
                "confidence": 0.2,
                "root_cause": "未知原因导致的内存压力",
                "solution": "监控内存使用情况，收集更多诊断信息，如问题持续可考虑减少并发任务数量",
                "severity": "unknown",
                "impact": ["可能影响系统稳定性"]
            }
            
        logger.info(f"生成通用建议: 模式 {pattern_type}, 置信度 0.4")
        return advice
    
    def learn_from_incident(self, incident_data: Dict) -> bool:
        """
        从内存事件中学习并更新知识库
        
        Args:
            incident_data: 事件数据，包括模式、根本原因和解决方案
            
        Returns:
            是否成功添加到知识库
        """
        # 验证必要字段
        required_fields = ["pattern", "root_cause", "solution", "symptoms"]
        for field in required_fields:
            if field not in incident_data:
                logger.error(f"学习失败: 缺少必要字段 {field}")
                return False
                
        try:
            # 生成唯一案例ID
            case_type = "OOM"  # 默认类型
            if "case_type" in incident_data:
                case_type = incident_data["case_type"]
                
            # 查找当前此类案例的最大序号
            max_id = 0
            for existing_id in self.cases.keys():
                if existing_id.startswith(f"{case_type}_"):
                    try:
                        id_num = int(existing_id.split("_")[1])
                        max_id = max(max_id, id_num)
                    except:
                        pass
            
            # 创建新案例ID
            new_id = f"{case_type}_{max_id + 1:03d}"
            
            # 添加到案例库
            self.cases[new_id] = {
                "symptoms": incident_data["symptoms"],
                "pattern": incident_data["pattern"],
                "root_cause": incident_data["root_cause"],
                "solution": incident_data["solution"],
                "severity": incident_data.get("severity", "medium"),
                "impact": incident_data.get("impact", []),
                "detection": incident_data.get("detection", ""),
                "source": "learned",
                "added_time": datetime.datetime.now().isoformat()
            }
            
            logger.info(f"从事件中学习并添加新案例: {new_id}")
            
            # 更新时间戳
            self.last_update_time = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"添加学习案例失败: {e}")
            return False
    
    def export_cases(self, file_path: str) -> bool:
        """
        导出案例库到JSON文件
        
        Args:
            file_path: 要导出到的文件路径
            
        Returns:
            是否成功导出
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cases, f, ensure_ascii=False, indent=2)
            
            logger.info(f"案例库已导出到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出案例库失败: {e}")
            return False
    
    def get_case(self, case_id: str) -> Optional[Dict]:
        """
        获取指定ID的案例
        
        Args:
            case_id: 案例ID
            
        Returns:
            案例数据或None
        """
        return self.cases.get(case_id)
    
    def get_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            统计信息字典
        """
        # 按类型统计案例数
        case_types = defaultdict(int)
        for case_id in self.cases:
            case_type = case_id.split("_")[0]
            case_types[case_type] += 1
            
        # 统计最近的匹配情况
        recent_matches = self.match_history[-10:] if self.match_history else []
        top_matches = {}
        for match in self.match_history:
            case_id = match["matched_case"]
            if case_id in top_matches:
                top_matches[case_id] += 1
            else:
                top_matches[case_id] = 1
                
        # 按匹配次数排序
        top_matches = dict(sorted(top_matches.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            "total_cases": len(self.cases),
            "case_types": dict(case_types),
            "diagnosis_count": self.diagnosis_count,
            "top_matched_cases": top_matches,
            "last_update": self.last_update_time
        }


# 单例管理
_kb_instance = None

def get_knowledge_base() -> FuseKB:
    """
    获取全局知识库实例
    
    Returns:
        FuseKB实例
    """
    global _kb_instance
    
    if _kb_instance is None:
        custom_cases_path = os.environ.get("FUSE_CUSTOM_CASES_PATH", "")
        if not custom_cases_path or not os.path.exists(custom_cases_path):
            custom_cases_path = None
            
        _kb_instance = FuseKB(custom_cases_path)
        
    return _kb_instance


if __name__ == "__main__":
    # 简单测试
    kb = get_knowledge_base()
    
    # 测试一个内存快速增长的案例
    test_data = np.array([30, 35, 42, 55, 70, 82, 95])
    result = kb.diagnose(test_data)
    
    print("诊断结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试KB状态
    print("\n知识库统计:")
    stats = kb.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False)) 