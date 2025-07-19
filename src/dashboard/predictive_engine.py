#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
预测性趋势投影引擎

该模块提供基于机器学习的预测功能，用于预测系统未来的资源使用趋势，
包括内存使用预测、OOM风险评估和缓存效率预测，设计为低资源消耗，
可在4GB RAM环境中高效运行。
"""

import os
import sys
import time
import json
import logging
import numpy as np
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import pickle

# 设置日志
logger = logging.getLogger("predictive_engine")

# 尝试导入机器学习相关库
try:
    from sklearn.preprocessing import MinMaxScaler
    try:
    import tensorflow as tf
except ImportError:
    # 使用模拟模块
    import tensorflow_mock as tf
    print("使用TensorFlow模拟模块")
    try:
    from tensorflow
except ImportError:
    # 使用模拟模块
    from tensorflow_mock.keras.models import Sequential, load_model, save_model
    try:
    from tensorflow
except ImportError:
    # 使用模拟模块
    from tensorflow_mock.keras.layers import LSTM, Dense, Dropout
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logger.warning("未安装TensorFlow/Keras，将使用轻量级预测回退方案")

# 尝试导入项目内部模块
try:
    from src.utils.memory_guard import get_memory_guard
    from src.memory.resource_tracker import get_resource_tracker
except ImportError:
    logger.warning("未能导入内存管理模块，某些功能可能受限")


class MemoryProphet:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存使用预测器，使用LSTM模型预测未来内存使用趋势"""
    
    def __init__(self, data_aggregator=None, model_path=None):
        """初始化内存预测器
        
        Args:
            data_aggregator: 数据聚合器实例
            model_path: 预训练模型路径
        """
        self.data_aggregator = data_aggregator
        self.model_path = model_path or "models/lstm_memory_prophet.h5"
        
        # 初始化数据缓存
        self.history_data = deque(maxlen=1000)  # 存储最近1000个数据点
        self.prediction_cache = {}
        
        # 初始化预处理器
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # 初始化模型
        self.model = None
        self.fallback_enabled = not HAS_ML_LIBS
        
        # 加载或创建模型
        if not self.fallback_enabled:
            self._load_or_create_model()
        
        # 线程锁，保护并发访问
        self.lock = threading.Lock()
        
        logger.info("内存预测器初始化完成")
    
    def _load_or_create_model(self):
        """加载现有模型或创建新模型"""
        try:
            # 尝试加载现有模型
            if os.path.exists(self.model_path):
                logger.info(f"加载预训练LSTM模型: {self.model_path}")
                self.model = load_model(self.model_path)
                return
            
            # 如果模型不存在，创建默认模型
            logger.info("创建新的LSTM模型")
            self.model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(12, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(1)
            ])
            
            self.model.compile(optimizer='adam', loss='mse')
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
        except Exception as e:
            logger.error(f"模型加载/创建失败: {e}")
            self.fallback_enabled = True
    
    def update_history(self, memory_data):
        """更新历史数据
        
        Args:
            memory_data: 内存使用数据
        """
        with self.lock:
            # 添加新数据点，包含时间戳和内存使用值
            current_time = time.time()
            data_point = {
                "timestamp": current_time,
                "memory_used": memory_data.get("used_memory", 0),
                "memory_percent": memory_data.get("percent", 0),
                "active_models": memory_data.get("active_models", 0)
            }
            
            self.history_data.append(data_point)
            
            # 如果有足够的数据，可以考虑重新训练模型
            if len(self.history_data) >= 200 and not self.fallback_enabled:
                self._consider_retraining()
    
    def _consider_retraining(self):
        """评估是否需要重新训练模型"""
        # 每积累200个新数据点就考虑重新训练一次
        # 此处简化，实际应用中可以设置更复杂的条件
        last_trained = getattr(self, "_last_trained", 0)
        if time.time() - last_trained > 3600:  # 限制训练频率，至少1小时一次
            try:
                threading.Thread(target=self._retrain_model, daemon=True).start()
                logger.info("已启动模型重训练线程")
            except Exception as e:
                logger.error(f"启动重训练线程失败: {e}")
    
    def _retrain_model(self):
        """后台重新训练模型"""
        try:
            logger.info("开始重新训练内存预测模型")
            
            with self.lock:
                # 准备训练数据
                data = list(self.history_data)
                memory_values = np.array([point["memory_percent"] for point in data]).reshape(-1, 1)
                
                # 重新拟合scaler
                scaled_data = self.scaler.fit_transform(memory_values)
                
                # 准备训练集
                X, y = [], []
                for i in range(12, len(scaled_data)):
                    X.append(scaled_data[i-12:i, 0])
                    y.append(scaled_data[i, 0])
                
                X = np.array(X).reshape(-1, 12, 1)
                y = np.array(y)
                
                # 如果数据足够，训练模型
                if len(X) > 50:
                    self.model.fit(X, y, epochs=10, batch_size=16, verbose=0)
                    
                    # 保存模型
                    save_model(self.model, self.model_path)
                    self._last_trained = time.time()
                    logger.info(f"模型重训练完成，已保存到: {self.model_path}")
                else:
                    logger.info("数据点不足，跳过模型训练")
                
        except Exception as e:
            logger.error(f"模型重训练失败: {e}")
    
    def _prepare_forecast_data(self, history=None, steps=12):
        """准备预测数据
        
        Args:
            history: 历史数据，如果为None则使用内部缓存
            steps: 预测步数
            
        Returns:
            预处理后的预测输入数据
        """
        with self.lock:
            # 使用提供的历史数据或内部缓存
            if history is None:
                if len(self.history_data) < 12:
                    logger.warning("历史数据不足，无法进行预测")
                    return None
                
                # 使用最近的历史数据
                history = [point["memory_percent"] for point in list(self.history_data)[-12:]]
            
            # 确保历史数据充足
            if len(history) < 12:
                logger.warning("输入历史数据不足，无法进行预测")
                return None
            
            # 预处理数据
            history_array = np.array(history).reshape(-1, 1)
            scaled_history = self.scaler.fit_transform(history_array)
            
            # 准备输入形状
            return scaled_history[-12:].reshape(1, 12, 1)
    
    def forecast(self, history=None, steps=12):
        """基于LSTM模型预测未来内存使用趋势
        
        Args:
            history: 历史内存使用数据
            steps: 预测的时间步数
            
        Returns:
            List: 预测结果列表
        """
        if self.fallback_enabled:
            return self._fallback_forecast(history, steps)
        
        try:
            # 准备预测数据
            X_forecast = self._prepare_forecast_data(history, steps)
            if X_forecast is None:
                return self._fallback_forecast(history, steps)
            
            # 预测未来steps步
            predictions = []
            current_input = X_forecast.copy()
            
            for _ in range(steps):
                # 进行一步预测
                forecast = self.model.predict(current_input, verbose=0)
                predictions.append(float(forecast[0, 0]))
                
                # 更新预测输入，将预测值加入序列，移除最旧的值
                current_input = np.append(current_input[:, 1:, :], 
                                        [[forecast]], 
                                        axis=1)
            
            # 反向转换预测值
            predictions_reshaped = np.array(predictions).reshape(-1, 1)
            predictions_rescaled = self.scaler.inverse_transform(predictions_reshaped)
            
            return predictions_rescaled.flatten().tolist()
            
        except Exception as e:
            logger.error(f"内存使用预测失败: {e}")
            return self._fallback_forecast(history, steps)
    
    def _fallback_forecast(self, history=None, steps=12):
        """在模型不可用时使用简单方法进行预测
        
        Args:
            history: 历史数据，如果为None则使用内部缓存
            steps: 预测步数
            
        Returns:
            List: 预测结果列表
        """
        # 获取历史数据
        if history is None:
            if len(self.history_data) < 3:
                # 数据太少，返回固定值
                return [50.0] * steps
            
            # 使用内部缓存的最近数据
            history = [point["memory_percent"] for point in list(self.history_data)[-5:]]
        
        # 确保有足够的历史数据
        if len(history) < 3:
            return [50.0] * steps
        
        # 计算简单线性趋势
        x = np.arange(len(history))
        y = np.array(history)
        
        # 计算线性回归参数
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # 预测未来值
        predictions = [(m * (len(history) + i) + c) for i in range(steps)]
        
        # 确保预测值在合理范围内
        predictions = [max(0, min(100, p)) for p in predictions]
        
        return predictions
    
    def predict_oom_risk(self, forecast=None, threshold=90.0):
        """预测OOM风险
        
        Args:
            forecast: 内存使用预测
            threshold: 风险阈值百分比
            
        Returns:
            Dict: 风险评估结果
        """
        if forecast is None:
            forecast = self.forecast()
        
        # 计算风险指标
        max_predicted = max(forecast) if forecast else 0
        exceeds_threshold = max_predicted > threshold
        
        # 如果预测值超过阈值，计算何时会发生
        time_to_threshold = None
        if exceeds_threshold:
            for i, value in enumerate(forecast):
                if value > threshold:
                    time_to_threshold = i * 5  # 假设每个预测点间隔5分钟
                    break
        
        return {
            "risk_level": "high" if exceeds_threshold else "low",
            "max_memory_predicted": max_predicted,
            "threshold": threshold,
            "time_to_threshold_minutes": time_to_threshold,
            "confidence": 0.8 if not self.fallback_enabled else 0.5  # 使用备用方法时降低置信度
        }
    
    def predict_cache_efficiency(self, history=None, steps=12):
        """预测缓存效率趋势
        
        Args:
            history: 历史缓存效率数据
            steps: 预测步数
            
        Returns:
            Dict: 缓存效率预测结果
        """
        # 获取缓存效率历史数据
        if history is None and self.data_aggregator:
            try:
                # 从数据聚合器获取缓存效率数据
                cache_data = self.data_aggregator.get_cached_data("cache")
                if cache_data and "metrics" in cache_data:
                    history = []
                    for point in cache_data["metrics"][-12:]:
                        if "hit_rate" in point:
                            history.append(point["hit_rate"] * 100)  # 转换为百分比
            except Exception as e:
                logger.error(f"获取缓存效率数据失败: {e}")
        
        # 如果没有历史数据，使用简单假设
        if not history or len(history) < 3:
            # 假设缓存效率从80%线性下降
            start_efficiency = 80.0
            decay_rate = 0.5  # 每步下降0.5%
            return {
                "predicted_efficiency": [max(0, start_efficiency - decay_rate * i) for i in range(steps)],
                "trend": "decreasing",
                "confidence": 0.4  # 低置信度
            }
        
        # 使用简单线性回归预测
        x = np.arange(len(history))
        y = np.array(history)
        
        # 计算线性趋势
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # 预测未来值
        predictions = [(m * (len(history) + i) + c) for i in range(steps)]
        
        # 确保预测值在合理范围内
        predictions = [max(0, min(100, p)) for p in predictions]
        
        # 确定趋势
        if m < -0.5:
            trend = "decreasing"
        elif m > 0.5:
            trend = "increasing"
        else:
            trend = "stable"
        
        return {
            "predicted_efficiency": predictions,
            "trend": trend,
            "slope": m,
            "confidence": 0.6
        }
    
    def get_full_prediction(self):
        """获取全套预测结果
        
        Returns:
            Dict: 完整预测结果
        """
        try:
            # 获取内存使用预测
            memory_forecast = self.forecast()
            
            # 计算OOM风险
            oom_risk = self.predict_oom_risk(memory_forecast)
            
            # 预测缓存效率
            cache_efficiency = self.predict_cache_efficiency()
            
            # 组合预测结果
            prediction = {
                "memory_forecast": {
                    "values": memory_forecast,
                    "interval_minutes": 5,  # 默认每5分钟一个预测点
                    "total_minutes": len(memory_forecast) * 5
                },
                "oom_risk": oom_risk,
                "cache_efficiency": cache_efficiency,
                "timestamp": time.time(),
                "is_fallback": self.fallback_enabled
            }
            
            # 计算预测时间点
            current_time = datetime.now()
            prediction["forecast_times"] = [
                (current_time + timedelta(minutes=i * 5)).strftime("%H:%M") 
                for i in range(len(memory_forecast))
            ]
            
            return prediction
            
        except Exception as e:
            logger.error(f"生成完整预测失败: {e}")
            return {
                "error": str(e),
                "is_fallback": True,
                "timestamp": time.time()
            }


class WorkloadPredictor:
    """工作负载预测器，预测系统未来的工作负载趋势"""
    
    def __init__(self, data_aggregator=None):
        """初始化工作负载预测器
        
        Args:
            data_aggregator: 数据聚合器实例
        """
        self.data_aggregator = data_aggregator
        
        # 工作负载历史数据
        self.workload_history = deque(maxlen=500)
        
        # 上次预测时间
        self.last_prediction_time = 0
        
        # 预测缓存
        self.prediction_cache = None
        
        logger.info("工作负载预测器初始化完成")
    
    def update_history(self, workload_data):
        """更新工作负载历史数据
        
        Args:
            workload_data: 工作负载数据
        """
        current_time = time.time()
        
        # 添加新数据点
        data_point = {
            "timestamp": current_time,
            "cpu_percent": workload_data.get("cpu_percent", 0),
            "request_count": workload_data.get("request_count", 0),
            "active_connections": workload_data.get("active_connections", 0)
        }
        
        self.workload_history.append(data_point)
    
    def predict_workload(self, hours_ahead=1):
        """预测未来工作负载
        
        Args:
            hours_ahead: 预测未来多少小时
            
        Returns:
            Dict: 工作负载预测结果
        """
        current_time = time.time()
        
        # 检查缓存是否有效（10分钟内）
        if (self.prediction_cache and 
            current_time - self.last_prediction_time < 600):
            return self.prediction_cache
        
        # 如果历史数据不足，返回基本预测
        if len(self.workload_history) < 24:
            prediction = self._basic_workload_prediction(hours_ahead)
        else:
            prediction = self._advanced_workload_prediction(hours_ahead)
        
        # 更新缓存
        self.prediction_cache = prediction
        self.last_prediction_time = current_time
        
        return prediction
    
    def _basic_workload_prediction(self, hours_ahead):
        """基本工作负载预测方法
        
        Args:
            hours_ahead: 预测未来多少小时
            
        Returns:
            Dict: 工作负载预测结果
        """
        # 简单假设：未来负载与当前相似，略有波动
        if not self.workload_history:
            # 无历史数据时使用默认值
            current_cpu = 30.0
            current_requests = 10
        else:
            # 使用最近数据的平均值
            recent = list(self.workload_history)[-min(6, len(self.workload_history)):]
            current_cpu = sum(point["cpu_percent"] for point in recent) / len(recent)
            current_requests = sum(point.get("request_count", 0) for point in recent) / len(recent)
        
        # 创建时间点（每30分钟一个点）
        points_count = int(hours_ahead * 2)  # 每小时2个点
        
        # 生成预测序列，添加一些随机波动
        cpu_predictions = []
        request_predictions = []
        
        for i in range(points_count):
            # 添加轻微波动，但维持在合理范围内
            random_factor = (i % 3 - 1) * 5  # -5, 0, 或 5
            cpu_pred = max(5, min(95, current_cpu + random_factor))
            cpu_predictions.append(cpu_pred)
            
            req_factor = (i % 3 - 1) * 3  # -3, 0, 或 3
            req_pred = max(1, current_requests + req_factor)
            request_predictions.append(req_pred)
        
        # 返回预测结果
        return {
            "cpu_percent": cpu_predictions,
            "request_count": request_predictions,
            "interval_minutes": 30,
            "confidence": 0.5,  # 中等置信度
            "prediction_method": "basic"
        }
    
    def _advanced_workload_prediction(self, hours_ahead):
        """高级工作负载预测方法
        
        Args:
            hours_ahead: 预测未来多少小时
            
        Returns:
            Dict: 工作负载预测结果
        """
        # 从历史数据中提取模式
        history = list(self.workload_history)
        
        # 提取CPU使用率和请求数量
        cpu_history = [point["cpu_percent"] for point in history]
        request_history = [point.get("request_count", 0) for point in history]
        
        # 使用简单的时间序列分解
        # 实际应用中可以使用更复杂的方法，如ARIMA或Prophet
        
        # 1. 计算趋势(简单的移动平均线)
        window_size = min(12, len(cpu_history) // 3)
        cpu_trend = np.convolve(cpu_history, np.ones(window_size)/window_size, mode='valid')
        request_trend = np.convolve(request_history, np.ones(window_size)/window_size, mode='valid')
        
        # 2. 计算季节性(假设24小时周期)
        # 简化处理，提取前后两个周期的平均模式
        period = 48  # 假设每30分钟一个点，24小时就是48个点
        
        # 预测点数
        points_count = int(hours_ahead * 2)  # 每小时2个点
        
        # 使用趋势和季节性生成预测
        cpu_predictions = []
        request_predictions = []
        
        for i in range(points_count):
            # 确定当前点在周期中的位置
            cycle_position = (len(cpu_history) + i) % period
            
            # 获取趋势值（使用最新的趋势点）
            trend_cpu = cpu_trend[-1] if len(cpu_trend) > 0 else cpu_history[-1]
            trend_request = request_trend[-1] if len(request_trend) > 0 else request_history[-1]
            
            # 添加轻微的随机波动
            random_factor = (np.random.random() - 0.5) * 5
            cpu_pred = max(5, min(95, trend_cpu + random_factor))
            cpu_predictions.append(cpu_pred)
            
            req_random = (np.random.random() - 0.5) * 4
            req_pred = max(1, trend_request + req_random)
            request_predictions.append(req_pred)
        
        # 返回预测结果
        return {
            "cpu_percent": cpu_predictions,
            "request_count": request_predictions,
            "interval_minutes": 30,
            "confidence": 0.7,  # 较高置信度
            "prediction_method": "advanced"
        }


class PredictiveEngine:
    """预测性趋势引擎，整合多种预测器提供综合预测"""
    
    def __init__(self, data_aggregator=None):
        """初始化预测引擎
        
        Args:
            data_aggregator: 数据聚合器实例
        """
        self.data_aggregator = data_aggregator
        
        # 初始化预测器
        self.memory_prophet = MemoryProphet(data_aggregator)
        self.workload_predictor = WorkloadPredictor(data_aggregator)
        
        # 最后更新时间
        self.last_update = 0
        
        # 自动更新线程
        self.update_thread = None
        self.should_stop = False
        
        logger.info("预测性趋势引擎初始化完成")
        
        # 启动自动更新
        self.start_auto_update()
    
    def update_data(self):
        """从数据聚合器更新数据"""
        try:
            if not self.data_aggregator:
                logger.warning("无数据聚合器，跳过数据更新")
                return
            
            # 获取当前系统数据
            current_data = self.data_aggregator.fetch_realtime_data()
            
            # 更新内存预测器
            if "memory" in current_data:
                self.memory_prophet.update_history(current_data["memory"])
            
            # 更新工作负载预测器
            workload_data = {
                "cpu_percent": current_data.get("system", {}).get("cpu_percent", 0),
                "request_count": current_data.get("metrics", {}).get("request_count", 0),
                "active_connections": current_data.get("metrics", {}).get("active_connections", 0)
            }
            self.workload_predictor.update_history(workload_data)
            
            # 更新时间戳
            self.last_update = time.time()
            
        except Exception as e:
            logger.error(f"更新预测数据失败: {e}")
    
    def start_auto_update(self, interval_seconds=120):
        """启动自动更新线程
        
        Args:
            interval_seconds: 更新间隔秒数
        """
        if self.update_thread and self.update_thread.is_alive():
            logger.warning("更新线程已在运行")
            return
        
        self.should_stop = False
        
        def update_loop():
            """定期更新循环"""
            while not self.should_stop:
                try:
                    self.update_data()
                except Exception as e:
                    logger.error(f"自动更新失败: {e}")
                
                # 等待下一次更新
                time.sleep(interval_seconds)
        
        # 启动更新线程
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"预测引擎自动更新已启动，间隔 {interval_seconds} 秒")
    
    def stop_auto_update(self):
        """停止自动更新线程"""
        self.should_stop = True
        if self.update_thread:
            self.update_thread.join(timeout=5)
            logger.info("预测引擎自动更新已停止")
    
    def get_memory_predictions(self, timeframe="medium"):
        """获取内存使用预测
        
        Args:
            timeframe: 时间范围('short'=5m, 'medium'=15m, 'long'=30m)
            
        Returns:
            Dict: 内存预测结果
        """
        # 根据时间范围确定预测步数
        steps_map = {
            "short": 6,    # 5分钟步长，预测30分钟
            "medium": 18,  # 5分钟步长，预测1.5小时
            "long": 36     # 5分钟步长，预测3小时
        }
        
        steps = steps_map.get(timeframe, 12)
        
        # 获取预测
        forecast = self.memory_prophet.forecast(steps=steps)
        oom_risk = self.memory_prophet.predict_oom_risk(forecast)
        
        # 计算预测时间点
        current_time = datetime.now()
        forecast_times = [
            (current_time + timedelta(minutes=i * 5)).strftime("%H:%M") 
            for i in range(len(forecast))
        ]
        
        return {
            "values": forecast,
            "times": forecast_times,
            "interval_minutes": 5,
            "oom_risk": oom_risk,
            "timeframe": timeframe
        }
    
    def get_workload_predictions(self, hours=2):
        """获取工作负载预测
        
        Args:
            hours: 预测未来小时数
            
        Returns:
            Dict: 工作负载预测结果
        """
        return self.workload_predictor.predict_workload(hours_ahead=hours)
    
    def get_cache_efficiency_forecast(self):
        """获取缓存效率预测
        
        Returns:
            Dict: 缓存效率预测结果
        """
        return self.memory_prophet.predict_cache_efficiency()
    
    def get_comprehensive_forecast(self):
        """获取综合预测
        
        Returns:
            Dict: 包含所有预测的综合结果
        """
        memory_pred = self.get_memory_predictions("medium")
        workload_pred = self.get_workload_predictions(hours=2)
        cache_pred = self.get_cache_efficiency_forecast()
        
        # 构建综合预测结果
        forecast = {
            "timestamp": time.time(),
            "memory": memory_pred,
            "workload": workload_pred,
            "cache": cache_pred,
            "system_status": self._predict_system_status(memory_pred, workload_pred)
        }
        
        return forecast
    
    def _predict_system_status(self, memory_pred, workload_pred):
        """预测系统整体状态
        
        Args:
            memory_pred: 内存预测
            workload_pred: 工作负载预测
            
        Returns:
            Dict: 系统状态预测
        """
        # 分析内存趋势
        memory_values = memory_pred.get("values", [])
        if not memory_values:
            return {"status": "unknown", "confidence": 0.0}
        
        # 计算内存使用趋势
        memory_current = memory_values[0] if memory_values else 0
        memory_future = memory_values[-1] if memory_values else 0
        memory_trend = memory_future - memory_current
        
        # 分析工作负载趋势
        cpu_values = workload_pred.get("cpu_percent", [])
        cpu_trend = 0
        if cpu_values and len(cpu_values) > 1:
            cpu_current = cpu_values[0]
            cpu_future = cpu_values[-1]
            cpu_trend = cpu_future - cpu_current
        
        # 确定系统状态
        status = "stable"  # 默认状态
        confidence = 0.7
        
        # 检查内存压力
        if memory_future > 90:
            status = "critical"
            confidence = 0.9
        elif memory_future > 80 or (memory_trend > 15 and memory_future > 70):
            status = "warning"
            confidence = 0.8
            
        # 考虑CPU压力
        if cpu_trend > 20 and status == "stable":
            status = "warning"
            confidence = 0.75
        elif cpu_trend > 30 and status == "warning":
            status = "critical"
            confidence = 0.85
            
        # 返回状态预测
        return {
            "status": status,
            "confidence": confidence,
            "trends": {
                "memory": "increasing" if memory_trend > 5 else "decreasing" if memory_trend < -5 else "stable",
                "cpu": "increasing" if cpu_trend > 10 else "decreasing" if cpu_trend < -10 else "stable"
            },
            "recommendation": self._get_recommendation(status, memory_pred, workload_pred)
        }
    
    def _get_recommendation(self, status, memory_pred, workload_pred):
        """基于预测生成建议
        
        Args:
            status: 系统状态
            memory_pred: 内存预测
            workload_pred: 工作负载预测
            
        Returns:
            str: 建议
        """
        if status == "critical":
            # 检查OOM风险
            oom_risk = memory_pred.get("oom_risk", {})
            if oom_risk.get("risk_level") == "high":
                time_to_oom = oom_risk.get("time_to_threshold_minutes", 0)
                if time_to_oom:
                    return f"预计 {time_to_oom} 分钟内可能发生内存不足，建议立即释放资源或减少负载"
                return "系统面临高内存压力风险，建议立即释放资源"
            
            return "系统负载趋势不佳，建议考虑资源优化"
            
        elif status == "warning":
            return "系统资源压力增长，建议监控并准备优化策略"
            
        else:  # stable
            return "系统资源利用稳定，无需干预"


# 全局单例
_predictive_engine = None

def get_predictive_engine(data_aggregator=None):

def is_tensor(obj):
    """检查对象是否为张量
    
    Args:
        obj: 要检查的对象
    
    Returns:
        bool: 是否为张量
    """
    # 在模拟模块中总是返回False
    # 这是一个简单的实现实际TensorFlow中会检查对象类型
    return False

    """获取预测引擎单例
    
    Args:
        data_aggregator: 数据聚合器实例
        
    Returns:
        PredictiveEngine: 预测引擎实例
    """
    global _predictive_engine
    
    if _predictive_engine is None:
        _predictive_engine = PredictiveEngine(data_aggregator)
    
    return _predictive_engine 