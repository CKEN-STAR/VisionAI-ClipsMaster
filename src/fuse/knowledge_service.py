#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
熔断知识库服务
----------
将熔断知识库集成到熔断系统中
提供诊断API和知识管理功能
"""

import os
import sys
import json
import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import threading

# 系统路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入知识库
from knowledge_base import get_knowledge_base, FuseKB

# 尝试导入熔断相关组件，但不强制依赖
FUSE_COMPONENTS_AVAILABLE = False
try:
    # 首先尝试本地导入
    from pressure_detector import get_pressure_detector
    from event_tracer import get_audit
    FUSE_COMPONENTS_AVAILABLE = True
except ImportError:
    try:
        # 然后尝试从src.fuse导入
        from src.fuse.pressure_detector import get_pressure_detector
        from src.fuse.event_tracer import get_audit
        FUSE_COMPONENTS_AVAILABLE = True
    except ImportError:
        pass

# 尝试导入熔断管理器
try:
    from src.memory.fuse_manager import get_fuse_manager
except ImportError:
    # 创建一个空的 get_fuse_manager 函数
    def get_fuse_manager():
        return None

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fuse_knowledge_service")


class KnowledgeService:
    """熔断知识库服务，集成知识库与熔断系统"""
    
    def __init__(self, auto_diagnosis: bool = True, diagnosis_interval: int = 300):
        """
        初始化知识库服务
        
        Args:
            auto_diagnosis: 是否自动进行诊断
            diagnosis_interval: 自动诊断间隔(秒)
        """
        self.kb = get_knowledge_base()
        self.auto_diagnosis = auto_diagnosis
        self.diagnosis_interval = diagnosis_interval
        
        # 最近的诊断结果
        self.recent_diagnoses = []
        self.max_diagnoses = 20
        
        # 获取熔断组件
        self.pressure_detector = None
        self.fuse_manager = None
        self.event_tracer = None
        
        if FUSE_COMPONENTS_AVAILABLE:
            self.pressure_detector = get_pressure_detector()
            self.fuse_manager = get_fuse_manager()
            self.event_tracer = get_audit()
            
        # 自动诊断控制
        self._stop_auto_diagnosis = threading.Event()
        self._auto_diagnosis_thread = None
        
        # 学习控制
        self.auto_learning = False
        self.learning_threshold = 0.8
        
        logger.info("熔断知识库服务初始化完成")
        
        # 启动自动诊断
        if auto_diagnosis:
            self.start_auto_diagnosis()
    
    def start_auto_diagnosis(self):
        """启动自动诊断线程"""
        if self._auto_diagnosis_thread is not None and self._auto_diagnosis_thread.is_alive():
            logger.warning("自动诊断已在运行")
            return
            
        self._stop_auto_diagnosis.clear()
        self._auto_diagnosis_thread = threading.Thread(
            target=self._auto_diagnosis_worker,
            daemon=True
        )
        self._auto_diagnosis_thread.start()
        logger.info(f"启动自动诊断，间隔 {self.diagnosis_interval} 秒")
    
    def stop_auto_diagnosis(self):
        """停止自动诊断线程"""
        if self._auto_diagnosis_thread is None or not self._auto_diagnosis_thread.is_alive():
            return
            
        self._stop_auto_diagnosis.set()
        self._auto_diagnosis_thread.join(timeout=10)
        logger.info("停止自动诊断")
    
    def _auto_diagnosis_worker(self):
        """自动诊断工作线程"""
        last_diagnosis_time = 0
        
        while not self._stop_auto_diagnosis.is_set():
            current_time = time.time()
            
            # 检查是否需要执行诊断
            if current_time - last_diagnosis_time >= self.diagnosis_interval:
                try:
                    # 进行诊断
                    result = self.diagnose_current_state()
                    last_diagnosis_time = current_time
                    
                    # 记录高置信度的问题
                    if result and result.get("confidence", 0) > 0.7:
                        logger.warning(f"检测到高置信度问题: {result['root_cause']}")
                        
                        # 如果启用了自动学习，尝试从事件学习
                        if self.auto_learning and self.event_tracer:
                            self._try_learn_from_events()
                            
                except Exception as e:
                    logger.error(f"自动诊断错误: {e}")
                    
            # 等待一段时间
            self._stop_auto_diagnosis.wait(min(10, self.diagnosis_interval / 10))
    
    def diagnose_current_state(self) -> Dict[str, Any]:
        """
        诊断当前内存状态
        
        Returns:
            诊断结果
        """
        # 检查必要的组件是否可用
        if not FUSE_COMPONENTS_AVAILABLE or not self.pressure_detector:
            logger.warning("无法诊断当前状态: 熔断组件不可用")
            return None
            
        try:
            # 获取当前系统状态
            system_info = self._collect_system_info()
            
            # 获取压力历史数据
            pressure_history = self.pressure_detector.get_history()
            if not pressure_history:
                logger.warning("无法诊断当前状态: 无压力历史数据")
                return None
                
            # 进行诊断
            result = self.kb.diagnose(pressure_history, system_info)
            
            # 记录诊断结果
            self.recent_diagnoses.append(result)
            if len(self.recent_diagnoses) > self.max_diagnoses:
                self.recent_diagnoses = self.recent_diagnoses[-self.max_diagnoses:]
                
            # 记录诊断事件
            if self.event_tracer:
                self._record_diagnosis_event(result)
                
            return result
            
        except Exception as e:
            logger.error(f"诊断当前状态失败: {e}")
            import traceback

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

            logger.debug(traceback.format_exc())
            return None
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """
        收集系统信息
        
        Returns:
            系统信息字典
        """
        info = {
            "timestamp": time.time(),
            "uptime_hours": 0
        }
        
        # 获取系统启动时间
        if hasattr(self.pressure_detector, "start_time"):
            start_time = getattr(self.pressure_detector, "start_time", 0)
            uptime_seconds = time.time() - start_time
            info["uptime_hours"] = uptime_seconds / 3600
            
        # 获取当前任务信息
        if hasattr(self.fuse_manager, "current_task"):
            info["task_type"] = getattr(self.fuse_manager, "current_task", "unknown")
            
        # 获取当前处理的视频信息
        if hasattr(self.fuse_manager, "current_video"):
            video_info = getattr(self.fuse_manager, "current_video", {})
            if isinstance(video_info, dict):
                if "size_bytes" in video_info:
                    info["video_size_gb"] = video_info["size_bytes"] / (1024 * 1024 * 1024)
                if "resolution" in video_info:
                    info["video_resolution"] = video_info["resolution"]
        
        return info
    
    def _record_diagnosis_event(self, diagnosis: Dict[str, Any]):
        """
        记录诊断事件
        
        Args:
            diagnosis: 诊断结果
        """
        if not self.event_tracer:
            return
            
        # 判断严重性
        severity = diagnosis.get("severity", "low")
        confidence = diagnosis.get("confidence", 0)
        
        if severity == "critical" and confidence > 0.7:
            event_type = "MEMORY_CRITICAL"
        elif severity == "high" and confidence > 0.6:
            event_type = "MEMORY_WARNING"
        else:
            event_type = "MEMORY_INFO"
            
        # 记录事件
        self.event_tracer.record_event(
            event_type=event_type,
            source="knowledge_service",
            details={
                "diagnosis_id": diagnosis.get("diagnosis_id"),
                "matched_case": diagnosis.get("matched_case"),
                "confidence": confidence,
                "root_cause": diagnosis.get("root_cause"),
                "solution": diagnosis.get("solution")
            }
        )
    
    def get_recent_diagnoses(self, count: int = None) -> List[Dict[str, Any]]:
        """
        获取最近的诊断结果
        
        Args:
            count: 要返回的结果数，None表示全部
            
        Returns:
            诊断结果列表
        """
        if count is None:
            return self.recent_diagnoses
            
        return self.recent_diagnoses[-count:]
    
    def diagnose_custom(self, 
                       pressure_data: Union[List, Dict],
                       system_info: Dict = None) -> Dict[str, Any]:
        """
        使用自定义数据进行诊断
        
        Args:
            pressure_data: 内存压力数据
            system_info: 系统信息
            
        Returns:
            诊断结果
        """
        return self.kb.diagnose(pressure_data, system_info)
    
    def _try_learn_from_events(self) -> bool:
        """
        尝试从熔断事件中学习
        
        Returns:
            是否成功学习
        """
        if not self.event_tracer:
            return False
            
        try:
            # 获取最近的熔断事件
            # 假设event_tracer有一个get_recent_events方法
            if not hasattr(self.event_tracer, "get_recent_events"):
                return False
                
            recent_events = self.event_tracer.get_recent_events(count=10)
            if not recent_events:
                return False
                
            # 分析事件，寻找可能的学习机会
            for event in recent_events:
                # 只关注熔断和恢复事件
                if not hasattr(event, "event_type") or not hasattr(event, "details"):
                    continue
                    
                if event.event_type not in ["CIRCUIT_BREAK", "RECOVERY_SUCCESS"]:
                    continue
                    
                # 提取相关信息
                if hasattr(event, "details") and isinstance(event.details, dict):
                    details = event.details
                    
                    # 检查是否有足够的信息生成学习案例
                    if "pressure_pattern" in details and "resolution" in details:
                        incident_data = {
                            "pattern": details.get("pressure_pattern", "unknown"),
                            "symptoms": details.get("symptoms", "内存压力异常"),
                            "root_cause": details.get("cause", "未确定根本原因"),
                            "solution": details.get("resolution", "系统自动恢复"),
                            "severity": details.get("severity", "medium"),
                            "impact": details.get("impact", []),
                            "case_type": "AUTO"
                        }
                        
                        # 尝试添加学习案例
                        success = self.kb.learn_from_incident(incident_data)
                        if success:
                            logger.info(f"从事件自动学习成功: {incident_data['symptoms']}")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"从事件学习失败: {e}")
            return False
    
    def add_learned_case(self, case_data: Dict[str, Any]) -> bool:
        """
        手动添加学习案例
        
        Args:
            case_data: 案例数据
            
        Returns:
            是否成功添加
        """
        return self.kb.learn_from_incident(case_data)
    
    def export_knowledge(self, file_path: str = None) -> Optional[str]:
        """
        导出知识库
        
        Args:
            file_path: 导出文件路径，None则自动生成
            
        Returns:
            导出文件路径或None
        """
        if file_path is None:
            # 生成默认文件路径
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"fuse_knowledge_{timestamp}.json"
            
        success = self.kb.export_cases(file_path)
        return file_path if success else None
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息
        """
        kb_stats = self.kb.get_stats()
        
        service_stats = {
            "auto_diagnosis": self.auto_diagnosis,
            "diagnosis_interval": self.diagnosis_interval,
            "auto_learning": self.auto_learning,
            "recent_diagnoses_count": len(self.recent_diagnoses)
        }
        
        return {
            "knowledge_base": kb_stats,
            "service": service_stats
        }


# 单例实例
_service_instance = None

def get_knowledge_service() -> KnowledgeService:
    """
    获取知识库服务单例
    
    Returns:
        KnowledgeService实例
    """
    global _service_instance
    
    if _service_instance is None:
        # 从环境变量获取配置
        auto_diagnosis = os.environ.get("FUSE_AUTO_DIAGNOSIS", "1") == "1"
        interval = int(os.environ.get("FUSE_DIAGNOSIS_INTERVAL", "300"))
        
        _service_instance = KnowledgeService(
            auto_diagnosis=auto_diagnosis,
            diagnosis_interval=interval
        )
        
    return _service_instance


if __name__ == "__main__":
    # 简单测试
    service = get_knowledge_service()
    
    # 诊断当前状态
    result = service.diagnose_current_state()
    if result:
        print("当前系统诊断结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("无法获取当前诊断结果，使用测试数据")
        
        # 测试数据
        test_data = [30, 35, 40, 50, 65, 75, 90]
        test_info = {"uptime_hours": 24, "task_type": "video_processing"}
        
        result = service.diagnose_custom(test_data, test_info)
        print("测试诊断结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 显示知识库统计
    stats = service.get_knowledge_stats()
    print("\n知识库统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 停止自动诊断
    service.stop_auto_diagnosis() 