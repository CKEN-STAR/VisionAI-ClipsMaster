#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
偏好进化追踪器

追踪和分析用户内容偏好随时间的变化，检测趋势转变，预测未来偏好演变。
为内容创作者和平台提供用户兴趣演变的动态视图。
"""

import os
import json
import time
import copy
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict

# 导入所需的本地模块
try:
    from src.utils.log_handler import get_logger
    from src.data.storage_manager import get_storage_manager
    from src.audience.preference_analyzer import PreferenceAnalyzer
except ImportError:
    # 模拟依赖
    class MockLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def debug(self, msg): print(f"[DEBUG] {msg}")
        def warning(self, msg): print(f"[WARNING] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    
    def get_logger(name):
        return MockLogger()
    
    class MockStorageManager:
        def get_preference_history(self, user_id, days=90):
            return []
        
        def save_preference_evolution(self, user_id, data):
            pass
    
    def get_storage_manager():
        return MockStorageManager()
    
    class PreferenceAnalyzer:
        def analyze_user_preferences(self, user_id):
            return {}

# 配置日志
evolution_logger = get_logger("preference_evolution")

class PreferenceEvolution:
    """偏好进化追踪器
    
    检测和分析用户偏好随时间的变化趋势，识别偏好转变，
    预测未来可能的偏好演变方向。
    """
    
    def __init__(self):
        """初始化偏好进化追踪器"""
        evolution_logger.info("初始化偏好进化追踪器")
        self.db = get_storage_manager()
        self.analyzer = PreferenceAnalyzer()
        
        # 偏好维度
        self.tracked_dimensions = [
            "genre",        # 内容类型
            "narrative",    # 叙述风格
            "pace",         # 节奏偏好 
            "visuals",      # 视觉风格
            "audio",        # 音频风格
            "complexity",   # 复杂度
            "emotional",    # 情感偏好
            "themes"        # 主题偏好
        ]
        
        # 预测模型配置
        self.forecast_window = 30  # 未来30天预测窗口
        self.min_history_points = 5  # 最少需要5个历史数据点进行预测
        self.trend_detection_threshold = 0.2  # 趋势变化阈值
        
        # 时间衰减因子
        self.time_decay = 0.95  # 指数衰减因子，越近的数据权重越高
    
    def detect_shift(self, user_id: str) -> Dict[str, Any]:
        """识别用户偏好迁移趋势
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 偏好迁移分析结果，包含当前趋势和预测转变
        """
        evolution_logger.info(f"开始分析用户 {user_id} 的偏好迁移趋势")
        
        # 获取用户偏好历史数据
        history = self.db.get_preference_history(user_id)
        
        return {
            "current_trend": self._calc_trend(history[-6:]),
            "predicted_shift": self._prophet_forecast(history)
        }
    
    def _calc_trend(self, recent_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算最近偏好趋势
        
        分析最近几次偏好数据，计算各维度的变化趋势。
        
        Args:
            recent_history: 最近的偏好历史记录
            
        Returns:
            Dict: 各维度的趋势变化
        """
        if not recent_history or len(recent_history) < 2:
            return {"status": "insufficient_data"}
        
        evolution_logger.debug(f"计算偏好趋势，数据点: {len(recent_history)}")
        
        # 初始化趋势结果
        trends = {dim: {"direction": "stable", "magnitude": 0.0} for dim in self.tracked_dimensions}
        
        # 对每个维度分别计算趋势
        for dimension in self.tracked_dimensions:
            try:
                # 提取该维度数据
                dim_data = self._extract_dimension_values(recent_history, dimension)
                if not dim_data or len(dim_data) < 2:
                    continue
                
                # 计算线性趋势
                slope, correlation = self._calculate_trend_slope(dim_data)
                
                # 确定趋势方向和强度
                if abs(slope) < 0.05 or abs(correlation) < 0.3:
                    direction = "stable"
                    magnitude = 0.0
                elif slope > 0:
                    direction = "increasing"
                    magnitude = min(1.0, slope * 2)  # 归一化到0-1
                else:
                    direction = "decreasing"
                    magnitude = min(1.0, abs(slope) * 2)  # 归一化到0-1
                
                # 更新结果
                trends[dimension] = {
                    "direction": direction,
                    "magnitude": round(magnitude, 2),
                    "correlation": round(correlation, 2),
                    "confidence": self._calculate_trend_confidence(dim_data, correlation)
                }
            except Exception as e:
                evolution_logger.error(f"计算 {dimension} 趋势时出错: {str(e)}")
                trends[dimension] = {"direction": "error", "magnitude": 0.0}
        
        # 找出最显著的变化维度
        significant_shifts = []
        for dim, data in trends.items():
            if data.get("magnitude", 0) > self.trend_detection_threshold:
                significant_shifts.append({
                    "dimension": dim,
                    "direction": data["direction"],
                    "magnitude": data["magnitude"],
                    "confidence": data.get("confidence", 0.0)
                })
        
        # 按变化幅度排序
        significant_shifts.sort(key=lambda x: x["magnitude"], reverse=True)
        
        return {
            "status": "success",
            "analyzed_at": datetime.now().isoformat(),
            "dimension_trends": trends,
            "significant_shifts": significant_shifts[:3],  # 最多返回前3个最显著的变化
            "overall_stability": self._calculate_overall_stability(trends)
        }
    
    def _prophet_forecast(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测未来偏好变化
        
        基于历史数据预测未来一段时间的偏好趋势。
        
        Args:
            history: 偏好历史记录
            
        Returns:
            Dict: 预测的偏好变化
        """
        if not history or len(history) < self.min_history_points:
            return {"status": "insufficient_data"}
        
        evolution_logger.debug(f"预测偏好趋势，历史数据点: {len(history)}")
        
        # 初始化预测结果
        forecasts = {}
        
        # 对每个维度分别进行预测
        for dimension in self.tracked_dimensions:
            try:
                # 提取该维度数据
                dim_data = self._extract_dimension_values(history, dimension)
                if not dim_data or len(dim_data) < self.min_history_points:
                    continue
                
                # 进行时间序列预测 (简化版，实际项目中可用Prophet或ARIMA等)
                forecast = self._simple_forecast(dim_data)
                
                # 存储预测结果
                forecasts[dimension] = {
                    "current_value": dim_data[-1]["value"] if dim_data else 0,
                    "predicted_value": forecast["predicted_value"],
                    "change_direction": forecast["direction"],
                    "confidence": forecast["confidence"],
                    "predicted_at": datetime.now().isoformat(),
                    "prediction_window": f"{self.forecast_window} days"
                }
            except Exception as e:
                evolution_logger.error(f"预测 {dimension} 趋势时出错: {str(e)}")
        
        # 找出可能的重大偏好转变
        potential_shifts = []
        for dim, data in forecasts.items():
            # 计算变化幅度
            current = data.get("current_value", 0)
            predicted = data.get("predicted_value", 0)
            
            if current == 0:
                continue
                
            change_pct = abs((predicted - current) / current)
            
            # 如果变化超过阈值，标记为潜在转变
            if change_pct > self.trend_detection_threshold:
                potential_shifts.append({
                    "dimension": dim,
                    "current_value": current,
                    "predicted_value": predicted,
                    "change_percentage": round(change_pct * 100, 1),
                    "direction": data["change_direction"],
                    "confidence": data["confidence"]
                })
        
        # 按变化幅度排序
        potential_shifts.sort(key=lambda x: x["change_percentage"], reverse=True)
        
        return {
            "status": "success",
            "forecasted_at": datetime.now().isoformat(),
            "forecast_window": f"{self.forecast_window} days",
            "dimension_forecasts": forecasts,
            "potential_shifts": potential_shifts[:3]  # 最多返回前3个最大的潜在变化
        }
    
    def _extract_dimension_values(self, history: List[Dict[str, Any]], dimension: str) -> List[Dict[str, Any]]:
        """提取特定维度的历史值
        
        Args:
            history: 偏好历史记录
            dimension: 要提取的维度
            
        Returns:
            List: 包含时间戳和值的列表
        """
        result = []
        for entry in history:
            timestamp = entry.get("timestamp", entry.get("analyzed_at"))
            if not timestamp:
                continue
                
            # 处理不同格式的时间戳
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        continue
            else:
                dt = timestamp
                
            # 提取该维度的值
            pref_data = entry.get("preferences", {})
            dim_data = pref_data.get(dimension, {})
            
            # 根据维度类型提取指标值
            value = self._get_dimension_metric(dim_data, dimension)
            if value is not None:
                result.append({
                    "timestamp": dt,
                    "value": value
                })
        
        # 按时间排序
        result.sort(key=lambda x: x["timestamp"])
        return result
    
    def _get_dimension_metric(self, dim_data: Dict[str, Any], dimension: str) -> Optional[float]:
        """根据维度类型提取关键指标值
        
        不同维度有不同的关键指标
        
        Args:
            dim_data: 维度数据
            dimension: 维度名称
            
        Returns:
            Optional[float]: 归一化的指标值(0-1之间)
        """
        try:
            if dimension == "genre":
                # 提取首选类型的强度
                if "favorites" in dim_data and dim_data["favorites"] and "strength_map" in dim_data:
                    genre = dim_data["favorites"][0]
                    if genre in dim_data["strength_map"]:
                        return dim_data["strength_map"][genre].get("ratio", 0)
                return 0.5  # 默认值
                
            elif dimension == "pace":
                # 将节奏偏好转为数值
                pace_map = {"very_slow": 0.0, "slow": 0.25, "moderate": 0.5, "fast": 0.75, "very_fast": 1.0}
                pref_pace = dim_data.get("preferred_pace", "moderate")
                return pace_map.get(pref_pace, 0.5)
                
            elif dimension == "complexity":
                # 将复杂度偏好转为数值
                complexity_map = {"very_simple": 0.0, "simple": 0.25, "moderate": 0.5, 
                                 "complex": 0.75, "very_complex": 1.0}
                pref_complex = dim_data.get("preferred_complexity", "moderate")
                return complexity_map.get(pref_complex, 0.5)
                
            elif dimension in ["visuals", "audio", "narrative"]:
                # 提取首选风格的强度
                if "preferred_styles" in dim_data and dim_data["preferred_styles"] and "strength_map" in dim_data:
                    style = dim_data["preferred_styles"][0]
                    if style in dim_data["strength_map"]:
                        return dim_data["strength_map"][style].get("ratio", 0)
                return 0.5  # 默认值
                
            elif dimension == "emotional":
                # 提取情感偏好的强度
                if "preferred_emotions" in dim_data and dim_data["preferred_emotions"] and "strength_map" in dim_data:
                    emotion = dim_data["preferred_emotions"][0]
                    if emotion in dim_data["strength_map"]:
                        return dim_data["strength_map"][emotion].get("ratio", 0)
                return 0.5  # 默认值
                
            elif dimension == "themes":
                # 提取主题偏好的强度
                if "preferred_themes" in dim_data and dim_data["preferred_themes"] and "strength_map" in dim_data:
                    theme = dim_data["preferred_themes"][0]
                    if theme in dim_data["strength_map"]:
                        return dim_data["strength_map"][theme].get("ratio", 0)
                return 0.5  # 默认值
                
            return 0.5  # 默认返回中性值
        except Exception as e:
            evolution_logger.error(f"提取维度 {dimension} 指标时出错: {str(e)}")
            return 0.5  # 错误时返回中性值
    
    def _calculate_trend_slope(self, time_series: List[Dict[str, Any]]) -> Tuple[float, float]:
        """计算时间序列的线性趋势斜率
        
        Args:
            time_series: 时间序列数据，每项包含timestamp和value
            
        Returns:
            Tuple[float, float]: (斜率, 相关系数)
        """
        if not time_series or len(time_series) < 2:
            return 0.0, 0.0
            
        # 准备X和Y数据
        base_time = time_series[0]["timestamp"]
        x_data = [(entry["timestamp"] - base_time).total_seconds() / (24 * 3600) for entry in time_series]  # 转为天数
        y_data = [entry["value"] for entry in time_series]
        
        # 计算简单的线性回归
        n = len(x_data)
        x_mean = sum(x_data) / n
        y_mean = sum(y_data) / n
        
        # 计算斜率
        numerator = sum((x_data[i] - x_mean) * (y_data[i] - y_mean) for i in range(n))
        denominator = sum((x_data[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, 0.0
            
        slope = numerator / denominator
        
        # 计算相关系数
        ss_xx = sum((x - x_mean) ** 2 for x in x_data)
        ss_yy = sum((y - y_mean) ** 2 for y in y_data)
        ss_xy = sum((x_data[i] - x_mean) * (y_data[i] - y_mean) for i in range(n))
        
        if ss_xx == 0 or ss_yy == 0:
            correlation = 0.0
        else:
            correlation = ss_xy / (ss_xx * ss_yy) ** 0.5
        
        return slope, correlation
    
    def _calculate_trend_confidence(self, time_series: List[Dict[str, Any]], correlation: float) -> float:
        """计算趋势预测的置信度
        
        基于数据点数量和相关性
        
        Args:
            time_series: 时间序列数据
            correlation: 相关系数
            
        Returns:
            float: 置信度(0-1)
        """
        # 数据点数量因子
        n = len(time_series)
        data_factor = min(1.0, n / 10)  # 至少10个点达到最高置信度
        
        # 相关性因子
        corr_factor = abs(correlation)
        
        # 时间范围因子
        if n >= 2:
            time_range = (time_series[-1]["timestamp"] - time_series[0]["timestamp"]).total_seconds() / (24 * 3600)
            time_factor = min(1.0, time_range / 30)  # 至少30天范围达到最高置信度
        else:
            time_factor = 0.0
        
        # 综合计算置信度
        confidence = (data_factor * 0.4 + corr_factor * 0.4 + time_factor * 0.2)
        return round(confidence, 2)
    
    def _calculate_overall_stability(self, trends: Dict[str, Dict[str, Any]]) -> float:
        """计算整体偏好稳定性指数
        
        Args:
            trends: 各维度趋势
            
        Returns:
            float: 稳定性指数(0-1)，值越高表示越稳定
        """
        if not trends:
            return 0.5
        
        # 计算各维度变化幅度的平均值
        magnitudes = [data.get("magnitude", 0) for data in trends.values() if isinstance(data, dict)]
        if not magnitudes:
            return 0.5
            
        avg_magnitude = sum(magnitudes) / len(magnitudes)
        
        # 转换为稳定性指数：值越小表示越稳定
        stability = 1.0 - avg_magnitude
        return round(stability, 2)
    
    def _simple_forecast(self, time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """简单时间序列预测
        
        基于历史数据做简单的线性预测
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            Dict: 预测结果
        """
        if not time_series or len(time_series) < 2:
            return {
                "predicted_value": time_series[-1]["value"] if time_series else 0.5,
                "direction": "stable",
                "confidence": 0.0
            }
        
        # 计算线性趋势
        slope, correlation = self._calculate_trend_slope(time_series)
        
        # 预测未来值 
        last_value = time_series[-1]["value"]
        predicted_value = last_value + (slope * self.forecast_window)
        
        # 限制预测值在0-1之间
        predicted_value = max(0.0, min(1.0, predicted_value))
        
        # 确定变化方向
        if abs(predicted_value - last_value) < 0.05:
            direction = "stable"
        elif predicted_value > last_value:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        # 计算置信度
        confidence = self._calculate_trend_confidence(time_series, correlation)
        
        return {
            "predicted_value": round(predicted_value, 2),
            "direction": direction,
            "confidence": confidence
        }
    
    def track_preference_evolution(self, user_id: str) -> Dict[str, Any]:
        """追踪并记录用户偏好演变
        
        分析当前偏好，与历史记录对比，追踪变化并存储。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 偏好演变分析结果
        """
        evolution_logger.info(f"开始追踪用户 {user_id} 的偏好演变")
        
        # 获取当前偏好
        current_preferences = self.analyzer.analyze_user_preferences(user_id)
        if not current_preferences or "status" not in current_preferences or current_preferences["status"] != "success":
            evolution_logger.warning(f"无法获取用户 {user_id} 的当前偏好")
            return {"status": "error", "message": "无法获取当前偏好"}
        
        # 获取历史偏好
        history = self.db.get_preference_history(user_id)
        
        # 检测偏好变化
        shifts = self.detect_shift(user_id)
        
        # 记录当前偏好到历史
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "preferences": current_preferences,
            "shifts": shifts
        }
        
        # 保存到存储
        try:
            self.db.save_preference_evolution(user_id, history_entry)
            evolution_logger.info(f"用户 {user_id} 的偏好演变记录已保存")
        except Exception as e:
            evolution_logger.error(f"保存用户 {user_id} 的偏好演变记录失败: {str(e)}")
            return {"status": "error", "message": "保存偏好演变记录失败"}
        
        return {
            "status": "success",
            "tracked_at": datetime.now().isoformat(),
            "current_preferences": current_preferences,
            "shifts": shifts
        }
    
    def get_evolution_summary(self, user_id: str, time_range: int = 90) -> Dict[str, Any]:
        """获取用户偏好演变摘要
        
        提供指定时间范围内的偏好变化摘要。
        
        Args:
            user_id: 用户ID
            time_range: 时间范围(天)
            
        Returns:
            Dict: 偏好演变摘要
        """
        evolution_logger.info(f"获取用户 {user_id} 的偏好演变摘要，时间范围: {time_range}天")
        
        # 获取历史偏好
        history = self.db.get_preference_history(user_id)
        if not history:
            return {"status": "no_data", "message": "没有历史偏好数据"}
        
        # 过滤指定时间范围的数据
        cutoff_date = datetime.now() - timedelta(days=time_range)
        
        # 处理时间戳格式
        filtered_history = []
        for entry in history:
            timestamp = entry.get("timestamp", entry.get("analyzed_at"))
            if not timestamp:
                continue
                
            # 处理不同格式的时间戳
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        continue
            else:
                dt = timestamp
                
            if dt >= cutoff_date:
                filtered_history.append(entry)
        
        if not filtered_history:
            return {"status": "no_data_in_range", "message": f"在指定的{time_range}天范围内没有偏好数据"}
        
        # 计算主要趋势变化
        trend = self._calc_trend(filtered_history)
        
        # 预测未来变化
        forecast = self._prophet_forecast(filtered_history)
        
        # 提取重要变化
        significant_changes = []
        
        # 从趋势分析中提取
        if trend.get("status") == "success" and "significant_shifts" in trend:
            for shift in trend["significant_shifts"]:
                significant_changes.append({
                    "type": "observed_trend",
                    "dimension": shift["dimension"],
                    "direction": shift["direction"],
                    "magnitude": shift["magnitude"],
                    "confidence": shift.get("confidence", 0.0)
                })
        
        # 从预测中提取
        if forecast.get("status") == "success" and "potential_shifts" in forecast:
            for shift in forecast["potential_shifts"]:
                significant_changes.append({
                    "type": "predicted_shift",
                    "dimension": shift["dimension"],
                    "direction": shift["direction"],
                    "change_percentage": shift["change_percentage"],
                    "confidence": shift.get("confidence", 0.0)
                })
        
        # 按照置信度排序
        significant_changes.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return {
            "status": "success",
            "user_id": user_id,
            "time_range": f"{time_range} days",
            "generated_at": datetime.now().isoformat(),
            "history_points": len(filtered_history),
            "overall_stability": trend.get("overall_stability", 0.5),
            "significant_changes": significant_changes[:5],  # 最多返回5个最显著的变化
            "trend": trend,
            "forecast": forecast
        }


def get_evolution_tracker() -> PreferenceEvolution:
    """获取偏好进化追踪器实例
    
    Returns:
        PreferenceEvolution: 偏好进化追踪器实例
    """
    return PreferenceEvolution()


def detect_preference_shift(user_id: str) -> Dict[str, Any]:
    """检测用户偏好迁移
    
    便捷函数，用于检测用户偏好的变化。
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 偏好变化分析结果
    """
    tracker = get_evolution_tracker()
    return tracker.detect_shift(user_id)


def track_preference_changes(user_id: str) -> Dict[str, Any]:
    """追踪记录用户偏好变化
    
    便捷函数，用于追踪并记录用户偏好的演变。
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 跟踪结果
    """
    tracker = get_evolution_tracker()
    return tracker.track_preference_evolution(user_id)


def get_preference_evolution_summary(user_id: str, days: int = 90) -> Dict[str, Any]:
    """获取用户偏好演变摘要
    
    便捷函数，用于获取用户偏好变化的摘要。
    
    Args:
        user_id: 用户ID
        days: 时间范围(天)
        
    Returns:
        Dict: 偏好演变摘要
    """
    tracker = get_evolution_tracker()
    return tracker.get_evolution_summary(user_id, days) 