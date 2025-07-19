#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化策略元数据记录模块

负责记录量化策略变更事件和相关性能指标，便于后续分析和可视化。
支持多种输出格式和存储后端，包括JSON文件、CSV和时序数据库。
"""

import os
import sys
import json
import time
import datetime
import threading
import csv
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径以解决导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.memory_guard import MemoryGuard
from src.utils.quant_config_loader import get_quant_config


class QuantLogger:
    """量化策略记录器，用于记录量化策略变更事件和相关性能指标"""
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        memory_guard: Optional[MemoryGuard] = None,
        enable_influxdb: bool = False,
        influxdb_config: Optional[Dict[str, Any]] = None,
        auto_save: bool = True,
        save_interval: int = 300,  # 默认5分钟自动保存一次
        max_records: int = 10000,  # 内存中保留的最大记录数
    ):
        """
        初始化量化策略记录器
        
        Args:
            log_dir: 日志存储目录，默认为项目根目录下的 logs 文件夹
            memory_guard: 内存监控器实例，未提供则创建新实例
            enable_influxdb: 是否启用 InfluxDB 存储
            influxdb_config: InfluxDB 连接配置
            auto_save: 是否启用自动保存
            save_interval: 自动保存间隔(秒)
            max_records: 内存中保留的最大记录数
        """
        # 设置日志目录
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'logs'
        )
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 实例化依赖组件
        self.memory_guard = memory_guard or MemoryGuard()
        self.quant_config = get_quant_config()
        
        # 初始化存储设置
        self.enable_influxdb = enable_influxdb
        self.influxdb_client = None
        self.influxdb_config = influxdb_config or {}
        
        if self.enable_influxdb:
            self._init_influxdb()
        
        # 内存记录存储
        self.strategy_records: List[Dict[str, Any]] = []
        self.max_records = max_records
        
        # 文件路径
        self.json_path = os.path.join(self.log_dir, 'quant_strategy_logs.json')
        self.csv_path = os.path.join(self.log_dir, 'quant_strategy_logs.csv')
        
        # 自动保存设置
        self.auto_save = auto_save
        self.save_interval = save_interval
        self._last_save_time = time.time()
        
        # 线程安全锁
        self._record_lock = threading.RLock()
        
        # 自动保存线程
        self._stop_auto_save = threading.Event()
        self._auto_save_thread = None
        
        # 记录字段定义
        self.metadata_fields = [
            'timestamp', 'from', 'to', 'free_mem', 'used_mem', 'memory_change',
            'cpu_percent', 'elapsed', 'quality_diff', 'performance_change',
            'score', 'reason', 'success', 'model'
        ]
        
        # 启动自动保存
        if self.auto_save:
            self._start_auto_save()
        
        # 加载现有记录
        self._load_existing_records()
        
        logger.info("量化策略记录器已初始化")
    
    def log_strategy(
        self, 
        old_quant: Optional[str], 
        new_quant: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        记录量化策略变更事件
        
        Args:
            old_quant: 旧量化级别，如 "Q4_K_M"，首次加载时可为 None
            new_quant: 新量化级别，如 "Q2_K"
            context: 上下文信息，包含性能指标和切换原因等
            
        Returns:
            Dict: 记录的事件数据
        """
        with self._record_lock:
            # 获取当前时间和内存状态
            now = time.time()
            timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            memory_info = self.memory_guard.get_memory_info()
            
            # 计算内存变化（如有提供）
            memory_change = 0
            if 'memory_before' in context and 'memory_after' in context:
                memory_change = (
                    context['memory_after'].get('used', 0) - 
                    context['memory_before'].get('used', 0)
                ) / (1024 * 1024)  # 转换为MB
            
            # 汇总所有信息
            record = {
                "timestamp": timestamp,
                "from": old_quant or "None",
                "to": new_quant,
                "free_mem": context.get('free_mem', memory_info.get('available', 0) / (1024 * 1024)),
                "used_mem": memory_info.get('used', 0) / (1024 * 1024),
                "memory_change": context.get('memory_change', memory_change),
                "cpu_percent": context.get('cpu_percent', self._get_cpu_usage()),
                "elapsed": context.get('switch_time', context.get('elapsed', 0)),
                "quality_diff": context.get('quality_diff', self._get_quality_diff(old_quant, new_quant)),
                "performance_change": context.get('performance_change', 0),
                "score": context.get('score', 0),
                "reason": context.get('reason', ''),
                "success": context.get('success', True),
                "model": context.get('model', '')
            }
            
            # 记录到内存
            self.strategy_records.append(record)
            
            # 限制内存记录数
            if len(self.strategy_records) > self.max_records:
                self.strategy_records.pop(0)
            
            # 如果启用了InfluxDB，写入时序数据库
            if self.enable_influxdb and self.influxdb_client:
                try:
                    self._write_to_influxdb(record)
                except Exception as e:
                    logger.error(f"写入InfluxDB失败: {str(e)}")
            
            # 检查是否需要自动保存
            if self.auto_save and (now - self._last_save_time) > self.save_interval:
                self.save_to_disk()
                self._last_save_time = now
            
            logger.debug(f"已记录量化策略变更: {old_quant} -> {new_quant}")
            return record
    
    def log_evaluation(
        self,
        evaluation_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录量化策略评估结果
        
        Args:
            evaluation_result: 评估结果数据
            context: 额外上下文信息
            
        Returns:
            Dict: 记录的事件数据
        """
        ctx = context or {}
        
        # 从评估结果提取信息
        before_level = evaluation_result.get('reference_level') or ctx.get('from_level', 'unknown')
        current_level = evaluation_result.get('evaluated_level') or ctx.get('to_level', 'unknown')
        
        # 构建记录上下文
        eval_context = {
            'reason': 'evaluation',
            'score': evaluation_result.get('score', 0),
            'memory_change': evaluation_result.get('mem_saved', 0),
            'quality_diff': evaluation_result.get('quality_drop', 0),
            'success': not evaluation_result.get('needs_warning', False),
        }
        
        # 合并额外上下文
        eval_context.update(ctx)
        
        # 记录事件
        return self.log_strategy(before_level, current_level, eval_context)
    
    def log_fallback(
        self,
        from_level: Optional[str],
        to_level: str,
        emergency_level: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录安全降级事件
        
        Args:
            from_level: 降级前的量化级别
            to_level: 降级后的量化级别
            emergency_level: 紧急程度
            context: 额外上下文信息
            
        Returns:
            Dict: 记录的事件数据
        """
        ctx = context or {}
        
        # 构建记录上下文
        fallback_context = {
            'reason': f'fallback_{emergency_level.lower()}',
            'emergency_level': emergency_level,
        }
        
        # 合并额外上下文
        fallback_context.update(ctx)
        
        # 记录事件
        return self.log_strategy(from_level, to_level, fallback_context)
    
    def save_to_disk(self) -> Tuple[bool, bool]:
        """
        将记录保存到磁盘文件中
        
        Returns:
            Tuple[bool, bool]: (JSON保存结果, CSV保存结果)
        """
        with self._record_lock:
            json_success = self._save_to_json()
            csv_success = self._save_to_csv()
            
            if json_success and csv_success:
                logger.info(f"量化策略记录已保存到: {self.log_dir}")
            else:
                logger.warning(f"量化策略记录保存部分失败: JSON={json_success}, CSV={csv_success}")
                
            return json_success, csv_success
    
    def get_records(
        self, 
        limit: Optional[int] = None, 
        from_level: Optional[str] = None,
        to_level: Optional[str] = None,
        reason: Optional[str] = None,
        success: Optional[bool] = None,
        min_score: Optional[float] = None,
        start_time: Optional[Union[str, datetime.datetime]] = None,
        end_time: Optional[Union[str, datetime.datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询策略变更记录
        
        Args:
            limit: 返回记录的最大数量
            from_level: 筛选特定的起始量化级别
            to_level: 筛选特定的目标量化级别
            reason: 筛选特定的变更原因
            success: 筛选成功/失败的变更
            min_score: 筛选最低评分
            start_time: 起始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 满足条件的记录列表
        """
        with self._record_lock:
            # 转换时间格式
            start_timestamp = None
            end_timestamp = None
            
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_timestamp = start_time.timestamp()
                
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_timestamp = end_time.timestamp()
            
            # 过滤记录
            filtered_records = []
            for record in self.strategy_records:
                # 转换记录时间戳为时间戳数值
                record_time = datetime.datetime.fromisoformat(
                    record['timestamp'].replace('Z', '+00:00')
                ).timestamp()
                
                # 时间范围过滤
                if start_timestamp and record_time < start_timestamp:
                    continue
                if end_timestamp and record_time > end_timestamp:
                    continue
                
                # 其他条件过滤
                if from_level is not None and record['from'] != from_level:
                    continue
                if to_level is not None and record['to'] != to_level:
                    continue
                if reason is not None and record['reason'] != reason:
                    continue
                if success is not None and record['success'] != success:
                    continue
                if min_score is not None and record['score'] < min_score:
                    continue
                
                filtered_records.append(record)
            
            # 应用限制
            if limit is not None and limit > 0:
                filtered_records = filtered_records[-limit:]
                
            return filtered_records
    
    def analyze_strategy_changes(self) -> Dict[str, Any]:
        """
        分析策略变更历史，提供统计洞察
        
        Returns:
            Dict: 包含各种统计指标的分析结果
        """
        with self._record_lock:
            if not self.strategy_records:
                return {"error": "No records available for analysis"}
            
            # 初始化统计数据
            stats = {
                "total_changes": len(self.strategy_records),
                "successful_changes": 0,
                "failed_changes": 0,
                "avg_switch_time": 0,
                "common_transitions": {},
                "level_frequency": {},
                "reason_distribution": {},
                "quality_impact": {},
                "memory_savings": {},
                "performance_changes": {},
            }
            
            # 收集统计数据
            total_time = 0
            level_count = {}
            reason_count = {}
            transition_count = {}
            quality_sum = {}
            memory_sum = {}
            performance_sum = {}
            
            for record in self.strategy_records:
                # 成功/失败统计
                if record['success']:
                    stats["successful_changes"] += 1
                else:
                    stats["failed_changes"] += 1
                
                # 总切换时间
                total_time += record['elapsed']
                
                # 统计量化级别和转换频率
                from_level = record['from']
                to_level = record['to']
                level_count[to_level] = level_count.get(to_level, 0) + 1
                
                # 统计转换路径
                transition = f"{from_level}->{to_level}"
                transition_count[transition] = transition_count.get(transition, 0) + 1
                
                # 统计转换原因
                reason = record['reason']
                reason_count[reason] = reason_count.get(reason, 0) + 1
                
                # 统计质量影响
                if to_level not in quality_sum:
                    quality_sum[to_level] = {"sum": 0, "count": 0}
                quality_sum[to_level]["sum"] += record['quality_diff']
                quality_sum[to_level]["count"] += 1
                
                # 统计内存节省
                if transition not in memory_sum:
                    memory_sum[transition] = {"sum": 0, "count": 0}
                memory_sum[transition]["sum"] += record['memory_change']
                memory_sum[transition]["count"] += 1
                
                # 统计性能变化
                if to_level not in performance_sum:
                    performance_sum[to_level] = {"sum": 0, "count": 0}
                performance_sum[to_level]["sum"] += record['performance_change']
                performance_sum[to_level]["count"] += 1
            
            # 计算均值和汇总
            stats["avg_switch_time"] = total_time / len(self.strategy_records)
            stats["level_frequency"] = level_count
            stats["common_transitions"] = transition_count
            stats["reason_distribution"] = reason_count
            
            # 计算各量化级别的平均质量影响
            quality_impact = {}
            for level, data in quality_sum.items():
                if data["count"] > 0:
                    quality_impact[level] = data["sum"] / data["count"]
            stats["quality_impact"] = quality_impact
            
            # 计算各转换路径的平均内存节省
            memory_savings = {}
            for transition, data in memory_sum.items():
                if data["count"] > 0:
                    memory_savings[transition] = data["sum"] / data["count"]
            stats["memory_savings"] = memory_savings
            
            # 计算各量化级别的平均性能变化
            performance_changes = {}
            for level, data in performance_sum.items():
                if data["count"] > 0:
                    performance_changes[level] = data["sum"] / data["count"]
            stats["performance_changes"] = performance_changes
            
            return stats
    
    def get_strategy_timeline(
        self,
        start_time: Optional[Union[str, datetime.datetime]] = None,
        end_time: Optional[Union[str, datetime.datetime]] = None,
        interval: str = "hour"
    ) -> List[Dict[str, Any]]:
        """
        获取策略变更的时间线数据
        
        Args:
            start_time: 起始时间
            end_time: 结束时间
            interval: 时间间隔 ('minute', 'hour', 'day')
            
        Returns:
            List[Dict]: 时间线数据点列表
        """
        # 获取筛选的记录
        records = self.get_records(start_time=start_time, end_time=end_time)
        
        if not records:
            return []
        
        # 按时间分组
        timeline_data = {}
        
        for record in records:
            record_time = datetime.datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            
            # 根据间隔确定时间点
            if interval == "minute":
                time_key = record_time.strftime('%Y-%m-%dT%H:%M:00Z')
            elif interval == "hour":
                time_key = record_time.strftime('%Y-%m-%dT%H:00:00Z')
            elif interval == "day":
                time_key = record_time.strftime('%Y-%m-%dT00:00:00Z')
            else:
                time_key = record_time.strftime('%Y-%m-%dT%H:00:00Z')
            
            # 初始化时间点数据
            if time_key not in timeline_data:
                timeline_data[time_key] = {
                    "time": time_key,
                    "count": 0,
                    "levels": {},
                    "avg_memory_change": 0,
                    "memory_changes": [],
                    "avg_quality_diff": 0,
                    "quality_diffs": [],
                    "success_rate": 0,
                    "success_count": 0
                }
            
            # 更新统计数据
            point = timeline_data[time_key]
            point["count"] += 1
            
            to_level = record['to']
            point["levels"][to_level] = point["levels"].get(to_level, 0) + 1
            
            point["memory_changes"].append(record['memory_change'])
            point["quality_diffs"].append(record['quality_diff'])
            
            if record['success']:
                point["success_count"] += 1
        
        # 计算每个时间点的平均值和成功率
        for point in timeline_data.values():
            if point["count"] > 0:
                # 平均内存变化
                point["avg_memory_change"] = sum(point["memory_changes"]) / len(point["memory_changes"])
                point["memory_changes"] = None  # 移除原始数据节省空间
                
                # 平均质量差异
                point["avg_quality_diff"] = sum(point["quality_diffs"]) / len(point["quality_diffs"])
                point["quality_diffs"] = None  # 移除原始数据节省空间
                
                # 成功率
                point["success_rate"] = point["success_count"] / point["count"]
        
        # 转换为列表并按时间排序
        timeline_list = list(timeline_data.values())
        timeline_list.sort(key=lambda x: x["time"])
        
        return timeline_list
    
    def get_best_strategies(self, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        获取评分最高的策略变更
        
        Args:
            top_n: 返回的结果数量
            
        Returns:
            List[Dict]: 最佳策略列表
        """
        with self._record_lock:
            # 筛选有评分的记录
            scored_records = [r for r in self.strategy_records if r['score'] > 0]
            
            # 按评分降序排序
            scored_records.sort(key=lambda x: x['score'], reverse=True)
            
            return scored_records[:top_n]
    
    def get_worst_strategies(self, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        获取评分最低的策略变更
        
        Args:
            top_n: 返回的结果数量
            
        Returns:
            List[Dict]: 最差策略列表
        """
        with self._record_lock:
            # 筛选有评分的记录
            scored_records = [r for r in self.strategy_records if r['score'] > 0]
            
            # 按评分升序排序
            scored_records.sort(key=lambda x: x['score'])
            
            return scored_records[:top_n]
    
    def _load_existing_records(self) -> None:
        """加载现有的记录文件"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    loaded_records = json.load(f)
                    
                    # 验证记录格式
                    valid_records = []
                    for record in loaded_records:
                        if isinstance(record, dict) and 'timestamp' in record and 'to' in record:
                            valid_records.append(record)
                    
                    self.strategy_records = valid_records[-self.max_records:]
                    logger.info(f"从文件加载了 {len(self.strategy_records)} 条量化策略记录")
        except Exception as e:
            logger.error(f"加载现有记录失败: {str(e)}")
    
    def _save_to_json(self) -> bool:
        """保存记录到JSON文件"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.strategy_records, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存记录到JSON失败: {str(e)}")
            return False
    
    def _save_to_csv(self) -> bool:
        """保存记录到CSV文件"""
        try:
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.metadata_fields)
                writer.writeheader()
                writer.writerows(self.strategy_records)
            return True
        except Exception as e:
            logger.error(f"保存记录到CSV失败: {str(e)}")
            return False
    
    def _init_influxdb(self) -> None:
        """初始化InfluxDB连接"""
        try:
            # 动态导入InfluxDB库以避免硬依赖
            from influxdb_client import InfluxDBClient
            
            # 设置默认配置
            default_config = {
                'url': 'http://localhost:8086',
                'token': '',
                'org': '',
                'bucket': 'quant_metrics'
            }
            
            # 合并用户配置
            config = {**default_config, **self.influxdb_config}
            
            # 创建客户端
            self.influxdb_client = InfluxDBClient(
                url=config['url'],
                token=config['token'],
                org=config['org']
            )
            
            # 设置默认桶
            self.influxdb_bucket = config['bucket']
            
            logger.info(f"已连接InfluxDB: {config['url']}")
            
        except ImportError:
            logger.warning("未安装InfluxDB客户端库，禁用InfluxDB存储")
            self.enable_influxdb = False
        except Exception as e:
            logger.error(f"连接InfluxDB失败: {str(e)}")
            self.enable_influxdb = False
    
    def _write_to_influxdb(self, record: Dict[str, Any]) -> None:
        """
        将记录写入InfluxDB
        
        Args:
            record: 要写入的记录
        """
        if not self.influxdb_client:
            return
        
        try:
            # 创建写入API
            write_api = self.influxdb_client.write_api()
            
            # 准备数据点
            data_point = {
                "measurement": "quant_change",
                "tags": {
                    "from": record['from'],
                    "to": record['to'],
                    "success": str(record['success']),
                    "reason": record['reason'],
                    "model": record['model'] or "unknown"
                },
                "fields": {
                    "free_mem": float(record['free_mem']),
                    "used_mem": float(record['used_mem']),
                    "memory_change": float(record['memory_change']),
                    "cpu_percent": float(record['cpu_percent']),
                    "elapsed": float(record['elapsed']),
                    "quality_diff": float(record['quality_diff']),
                    "performance_change": float(record['performance_change']),
                    "score": float(record['score'])
                },
                "time": record['timestamp']
            }
            
            # 写入数据
            write_api.write(bucket=self.influxdb_bucket, record=data_point)
            
        except Exception as e:
            logger.error(f"写入InfluxDB失败: {str(e)}")
    
    def _start_auto_save(self) -> None:
        """启动自动保存线程"""
        if self._auto_save_thread is None or not self._auto_save_thread.is_alive():
            self._stop_auto_save.clear()
            self._auto_save_thread = threading.Thread(
                target=self._auto_save_worker,
                daemon=True
            )
            self._auto_save_thread.start()
            logger.debug("已启动自动保存线程")
    
    def _auto_save_worker(self) -> None:
        """自动保存工作线程"""
        while not self._stop_auto_save.is_set():
            try:
                # 等待指定时间
                self._stop_auto_save.wait(self.save_interval)
                
                # 如果收到停止信号，退出
                if self._stop_auto_save.is_set():
                    break
                
                # 执行保存
                if self.strategy_records:
                    self.save_to_disk()
                    self._last_save_time = time.time()
                
            except Exception as e:
                logger.error(f"自动保存时发生错误: {str(e)}")
    
    def _get_cpu_usage(self) -> float:
        """获取当前CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0
    
    def _get_quality_diff(self, old_quant: Optional[str], new_quant: str) -> float:
        """
        计算两个量化级别之间的质量差异
        
        Args:
            old_quant: 旧量化级别
            new_quant: 新量化级别
            
        Returns:
            float: 质量差异值
        """
        if not old_quant:
            return 0.0
        
        old_info = self.quant_config.get_level_info(old_quant) or {}
        new_info = self.quant_config.get_level_info(new_quant) or {}
        
        old_quality = old_info.get('quality_score', 100)
        new_quality = new_info.get('quality_score', 100)
        
        return (old_quality - new_quality) / 100.0
    
    def stop(self) -> None:
        """停止记录器并保存数据"""
        try:
            # 停止自动保存线程
            if self._auto_save_thread and self._auto_save_thread.is_alive():
                self._stop_auto_save.set()
                self._auto_save_thread.join(timeout=5.0)
            
            # 保存数据
            self.save_to_disk()
            
            # 关闭InfluxDB连接
            if self.influxdb_client:
                self.influxdb_client.close()
            
            logger.info("量化策略记录器已停止并保存数据")
            
        except Exception as e:
            logger.error(f"停止记录器时发生错误: {str(e)}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 便捷的全局接口函数
_quant_logger = None

def get_quant_logger() -> QuantLogger:
    """获取全局量化策略记录器实例"""
    global _quant_logger
    if _quant_logger is None:
        _quant_logger = QuantLogger()
    return _quant_logger

def log_strategy_change(old_quant: Optional[str], new_quant: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """记录量化策略变更"""
    return get_quant_logger().log_strategy(old_quant, new_quant, context)

def log_evaluation_result(evaluation_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """记录评估结果"""
    return get_quant_logger().log_evaluation(evaluation_result, context)

def log_fallback_event(from_level: Optional[str], to_level: str, emergency_level: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """记录安全降级事件"""
    return get_quant_logger().log_fallback(from_level, to_level, emergency_level, context)

def get_strategy_analytics() -> Dict[str, Any]:
    """获取策略分析数据"""
    return get_quant_logger().analyze_strategy_changes()

def get_best_strategies(top_n: int = 3) -> List[Dict[str, Any]]:
    """获取最佳策略"""
    return get_quant_logger().get_best_strategies(top_n)


# 使用示例
if __name__ == "__main__":
    # 初始化记录器
    logger = QuantLogger()
    
    # 示例1: 记录策略变更
    print("\n策略变更记录示例:")
    print("=" * 60)
    
    context = {
        'free_mem': 890,
        'elapsed': 2.7,
        'reason': '内存压力'
    }
    
    record = logger.log_strategy('Q4_K_M', 'Q2_K', context)
    print(f"记录ID: {record['timestamp']}")
    print(f"策略变更: {record['from']} -> {record['to']}")
    print(f"可用内存: {record['free_mem']} MB")
    print(f"切换耗时: {record['elapsed']} 秒")
    print(f"质量变化: {record['quality_diff']:.4f}")
    
    # 示例2: 查询记录
    print("\n查询记录示例:")
    print("=" * 60)
    
    # 再添加几条记录以便演示
    logger.log_strategy('Q2_K', 'Q3_K_M', {'reason': '内存恢复'})
    logger.log_strategy('Q3_K_M', 'Q4_K_M', {'reason': '质量优化'})
    logger.log_strategy('Q4_K_M', 'Q5_K_M', {'reason': '用户请求'})
    
    # 查询特定原因的记录
    records = logger.get_records(reason='内存压力')
    print(f"找到 {len(records)} 条内存压力相关记录")
    
    # 查询特定转换路径的记录
    records = logger.get_records(from_level='Q4_K_M')
    print(f"找到 {len(records)} 条从Q4_K_M开始的记录")
    
    # 示例3: 分析策略变更
    print("\n策略分析示例:")
    print("=" * 60)
    
    analysis = logger.analyze_strategy_changes()
    print(f"总策略变更次数: {analysis['total_changes']}")
    print(f"平均切换时间: {analysis['avg_switch_time']:.2f} 秒")
    
    print("\n级别使用频率:")
    for level, count in analysis['level_frequency'].items():
        print(f"  {level}: {count} 次")
    
    print("\n变更原因分布:")
    for reason, count in analysis['reason_distribution'].items():
        print(f"  {reason}: {count} 次")
    
    # 保存记录
    logger.save_to_disk()
    print(f"\n记录已保存到 {logger.log_dir}") 