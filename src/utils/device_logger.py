"""设备日志审计模块

此模块负责记录和审计设备运行状态，包括：
1. 设备事件记录
2. 资源使用统计
3. 性能指标跟踪
4. 异常情况记录
5. 审计报告生成
"""

import time
import json
import psutil
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from loguru import logger

from src.utils.os_compat import OSCompat
from src.utils.device_manager import HybridDevice
from src.utils.resource_predictor import ResourcePredictor

class DeviceAuditor:
    """设备运行状态审计类"""
    
    def __init__(self, log_dir: str = "logs/device_audit"):
        """初始化设备审计器
        
        Args:
            log_dir: 日志存储目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log = []
        self.os_compat = OSCompat()
        self.device_manager = HybridDevice()
        self.resource_predictor = ResourcePredictor()
        
        # 审计配置
        self.max_log_entries = 1000  # 最大日志条目数
        self.warning_thresholds = {
            "cpu_usage": 80.0,  # CPU使用率警告阈值
            "memory_usage": 80.0,  # 内存使用率警告阈值
            "gpu_memory": 80.0,  # GPU内存使用率警告阈值
            "disk_usage": 90.0,  # 磁盘使用率警告阈值
            "temperature": 80.0  # 温度警告阈值（摄氏度）
        }
        
        # 初始化日志文件
        self._init_log_files()
    
    def _init_log_files(self):
        """初始化日志文件"""
        self.current_log_file = self.log_dir / f"device_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.summary_file = self.log_dir / "audit_summary.json"
        
        # 创建日志文件
        if not self.current_log_file.exists():
            self.current_log_file.write_text("[]")
        if not self.summary_file.exists():
            self.summary_file.write_text("{}")
    
    def record(self, event: str, details: Optional[Dict] = None):
        """记录设备事件
        
        Args:
            event: 事件名称
            details: 事件详细信息
        """
        try:
            # 获取系统状态
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取GPU状态（如果可用）
            gpu_info = self.device_manager.get_gpu_info() if self.device_manager.has_gpu else {}
            
            # 创建日志条目
            entry = {
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "event": event,
                "details": details or {},
                "system_status": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent
                    },
                    "disk_usage": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": disk.percent
                    },
                    "gpu_status": gpu_info,
                    "process_info": self._get_process_info()
                }
            }
            
            # 检查是否超过警告阈值
            warnings = self._check_warnings(entry["system_status"])
            if warnings:
                entry["warnings"] = warnings
                logger.warning(f"系统状态警告: {warnings}")
            
            # 添加到内存日志
            self.log.append(entry)
            if len(self.log) > self.max_log_entries:
                self.log.pop(0)
            
            # 写入日志文件
            self._write_log_entry(entry)
            
            # 更新审计摘要
            self._update_audit_summary(entry)
            
        except Exception as e:
            logger.error(f"记录设备事件失败: {str(e)}")
    
    def _get_process_info(self) -> Dict:
        """获取当前进程信息"""
        process = psutil.Process()
        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_info": process.memory_info()._asdict(),
            "num_threads": process.num_threads(),
            "status": process.status()
        }
    
    def _check_warnings(self, status: Dict) -> List[str]:
        """检查系统状态是否超过警告阈值"""
        warnings = []
        
        # CPU使用率检查
        if status["cpu_usage"] > self.warning_thresholds["cpu_usage"]:
            warnings.append(f"CPU使用率过高: {status['cpu_usage']}%")
        
        # 内存使用率检查
        if status["memory_usage"]["percent"] > self.warning_thresholds["memory_usage"]:
            warnings.append(f"内存使用率过高: {status['memory_usage']['percent']}%")
        
        # 磁盘使用率检查
        if status["disk_usage"]["percent"] > self.warning_thresholds["disk_usage"]:
            warnings.append(f"磁盘使用率过高: {status['disk_usage']['percent']}%")
        
        # GPU状态检查
        if "gpu_status" in status and status["gpu_status"]:
            gpu_memory_used = status["gpu_status"].get("memory_used_percent", 0)
            if gpu_memory_used > self.warning_thresholds["gpu_memory"]:
                warnings.append(f"GPU内存使用率过高: {gpu_memory_used}%")
            
            gpu_temp = status["gpu_status"].get("temperature", 0)
            if gpu_temp > self.warning_thresholds["temperature"]:
                warnings.append(f"GPU温度过高: {gpu_temp}°C")
        
        return warnings
    
    def _write_log_entry(self, entry: Dict):
        """写入日志条目到文件"""
        try:
            # 读取现有日志
            current_logs = json.loads(self.current_log_file.read_text())
            current_logs.append(entry)
            
            # 写入更新后的日志
            self.current_log_file.write_text(json.dumps(current_logs, indent=2))
            
        except Exception as e:
            logger.error(f"写入日志条目失败: {str(e)}")
    
    def _update_audit_summary(self, entry: Dict):
        """更新审计摘要"""
        try:
            # 读取现有摘要
            summary = json.loads(self.summary_file.read_text())
            
            # 更新统计信息
            if "stats" not in summary:
                summary["stats"] = {
                    "total_events": 0,
                    "warnings": 0,
                    "avg_cpu_usage": 0,
                    "avg_memory_usage": 0,
                    "peak_cpu_usage": 0,
                    "peak_memory_usage": 0,
                    "last_update": ""
                }
            
            stats = summary["stats"]
            stats["total_events"] += 1
            if "warnings" in entry:
                stats["warnings"] += len(entry["warnings"])
            
            # 更新平均值和峰值
            cpu_usage = entry["system_status"]["cpu_usage"]
            memory_usage = entry["system_status"]["memory_usage"]["percent"]
            
            stats["avg_cpu_usage"] = (stats["avg_cpu_usage"] * (stats["total_events"] - 1) + cpu_usage) / stats["total_events"]
            stats["avg_memory_usage"] = (stats["avg_memory_usage"] * (stats["total_events"] - 1) + memory_usage) / stats["total_events"]
            stats["peak_cpu_usage"] = max(stats["peak_cpu_usage"], cpu_usage)
            stats["peak_memory_usage"] = max(stats["peak_memory_usage"], memory_usage)
            stats["last_update"] = entry["datetime"]
            
            # 写入更新后的摘要
            self.summary_file.write_text(json.dumps(summary, indent=2))
            
        except Exception as e:
            logger.error(f"更新审计摘要失败: {str(e)}")
    
    def get_audit_summary(self) -> Dict:
        """获取审计摘要
        
        Returns:
            Dict: 审计摘要信息
        """
        try:
            return json.loads(self.summary_file.read_text())
        except Exception as e:
            logger.error(f"读取审计摘要失败: {str(e)}")
            return {}
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """获取最近的事件记录
        
        Args:
            limit: 返回的事件数量限制
            
        Returns:
            List[Dict]: 最近的事件记录列表
        """
        return self.log[-limit:]
    
    def get_warnings(self) -> List[Dict]:
        """获取所有警告事件
        
        Returns:
            List[Dict]: 警告事件列表
        """
        return [entry for entry in self.log if "warnings" in entry]
    
    def generate_audit_report(self) -> Dict:
        """生成审计报告
        
        Returns:
            Dict: 审计报告
        """
        summary = self.get_audit_summary()
        recent_events = self.get_recent_events()
        warnings = self.get_warnings()
        
        return {
            "summary": summary,
            "recent_events": recent_events,
            "warnings": warnings,
            "system_info": self.os_compat.get_platform_summary(),
            "report_generated_at": datetime.now().isoformat()
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """清理旧的日志文件
        
        Args:
            days_to_keep: 保留的天数
        """
        try:
            current_time = time.time()
            for log_file in self.log_dir.glob("device_audit_*.json"):
                if log_file.stat().st_mtime < current_time - (days_to_keep * 86400):
                    log_file.unlink()
                    logger.info(f"已删除旧日志文件: {log_file}")
        except Exception as e:
            logger.error(f"清理旧日志文件失败: {str(e)}") 