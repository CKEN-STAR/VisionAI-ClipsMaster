#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
认知负荷评估集成模块

将认知负荷评估功能集成到VisionAI-ClipsMaster主应用程序中，
提供用户体验监测和认知负荷分析能力。
"""

import os
import sys
import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cognitive_load_integration")

# 确保测试模块可导入
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 默认阈值和配置
DEFAULT_THRESHOLD = 3.0
CONFIG_FILE = os.path.join(project_root, "config", "cognitive_load.json")

class CognitiveLoadMonitor:
    """认知负荷监控器，集成到主应用程序中"""
    
    def __init__(self, config_file: str = CONFIG_FILE, auto_start: bool = False):
        """
        初始化认知负荷监控器
        
        Args:
            config_file: 配置文件路径
            auto_start: 是否自动启动监控
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.assessor = None
        self.visualization = None
        self._monitoring_thread = None
        self._stop_flag = threading.Event()
        
        # 初始化组件
        self._init_components()
        
        # 如果自动启动，则启动监控
        if auto_start:
            self.start_monitoring()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            配置字典
        """
        # 默认配置
        default_config = {
            "threshold": DEFAULT_THRESHOLD,
            "monitoring_interval": 3600,  # 默认每小时监控一次
            "auto_visualization": True,
            "notification_enabled": True,
            "data_collection": {
                "enabled": True,
                "anonymous": True,
                "user_consent_required": True
            },
            "language_models": {
                "chinese": {
                    "enabled": True,
                    "model": "Qwen2.5-7B",
                    "collect_metrics": True
                },
                "english": {
                    "enabled": False,
                    "model": "Mistral-7B",
                    "collect_metrics": True
                }
            }
        }
        
        # 尝试加载配置文件
        config = default_config
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                
                # 合并配置
                for key, value in loaded_config.items():
                    if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                        # 递归合并嵌套字典
                        for subkey, subvalue in value.items():
                            config[key][subkey] = subvalue
                    else:
                        config[key] = value
                
                logger.info(f"已从 {self.config_file} 加载配置")
            else:
                # 如果配置文件不存在，创建默认配置
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已创建默认配置文件: {self.config_file}")
        except Exception as e:
            logger.error(f"加载配置文件出错: {e}")
        
        return config
    
    def _init_components(self):
        """初始化组件"""
        try:
            # 导入认知负荷评估模块
            from tests.user_experience.cognitive_load import CognitiveLoadAssessor
            self.assessor = CognitiveLoadAssessor()
            
            # 尝试导入可视化模块
            try:
                from tests.user_experience.cognitive_load_visualization import check_visualization_available
                if check_visualization_available():
                    from tests.user_experience.cognitive_load_visualization import visualize_report
                    self.visualization = visualize_report
                    logger.info("认知负荷可视化模块已加载")
                else:
                    logger.warning("认知负荷可视化功能不可用，请安装matplotlib和numpy")
            except ImportError:
                logger.warning("认知负荷可视化模块导入失败")
            
            logger.info("认知负荷评估组件已初始化")
        except ImportError:
            logger.error("导入认知负荷评估模块失败，请确保模块存在")
            self.assessor = None
    
    def start_monitoring(self, interval: Optional[int] = None) -> bool:
        """
        启动认知负荷监控
        
        Args:
            interval: 监控间隔(秒)，如果为None则使用配置的间隔
            
        Returns:
            是否成功启动
        """
        if self.assessor is None:
            logger.error("认知负荷评估器未初始化，无法启动监控")
            return False
        
        if self._monitoring_thread is not None and self._monitoring_thread.is_alive():
            logger.warning("监控线程已在运行")
            return True
        
        # 重置停止标志
        self._stop_flag.clear()
        
        # 使用配置的间隔或指定的间隔
        if interval is None:
            interval = self.config.get("monitoring_interval", 3600)
        
        # 启动监控线程
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        
        logger.info(f"认知负荷监控已启动，间隔: {interval}秒")
        return True
    
    def stop_monitoring(self) -> bool:
        """
        停止认知负荷监控
        
        Returns:
            是否成功停止
        """
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            logger.warning("监控线程未运行")
            return True
        
        # 设置停止标志
        self._stop_flag.set()
        
        # 等待线程结束
        self._monitoring_thread.join(timeout=5)
        
        if self._monitoring_thread.is_alive():
            logger.warning("监控线程未能在超时时间内停止")
            return False
        
        logger.info("认知负荷监控已停止")
        return True
    
    def _monitoring_worker(self, interval: int):
        """
        监控工作线程
        
        Args:
            interval: 监控间隔(秒)
        """
        while not self._stop_flag.is_set():
            try:
                # 执行认知负荷评估
                self._perform_assessment()
                
                # 等待下一次评估
                # 使用小间隔检查停止标志，以便能够及时响应停止请求
                for _ in range(interval * 2):  # 每0.5秒检查一次
                    if self._stop_flag.is_set():
                        break
                    time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"执行认知负荷评估时出错: {e}")
                # 出错后等待一段时间再重试
                time.sleep(60)
    
    def _perform_assessment(self):
        """执行认知负荷评估"""
        try:
            # 这里应该根据应用当前状态收集实际用户体验数据
            # 在集成环境中，可以通过UI交互、记录用户行为等方式收集
            # 这里仅作为示例，使用模拟数据
            
            # 检查语言模型配置
            chinese_enabled = self.config.get("language_models", {}).get("chinese", {}).get("enabled", True)
            english_enabled = self.config.get("language_models", {}).get("english", {}).get("enabled", False)
            
            # 执行适当的评估
            if chinese_enabled:
                from tests.user_experience.cognitive_load import measure_mental_effort
                
                # 针对中文处理的评估
                scores = measure_mental_effort(
                    user_id="system_monitor",
                    task_type="chinese_content_processing"
                )
                
                logger.info(f"已执行中文处理认知负荷评估，平均分: {sum(scores.values()) / len(scores):.2f}")
                
                # 检查是否需要可视化
                if self.config.get("auto_visualization", True) and self.visualization:
                    # 生成报告数据
                    report_data = {
                        "scores": scores,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "task_type": "chinese_content_processing"
                    }
                    
                    # 可视化
                    output_dir = os.path.join(project_root, "reports", "visualizations")
                    self.visualization(report_data, output_dir, show=False)
            
            if english_enabled:
                # 英文处理的评估（配置为未来使用）
                logger.info("英文处理评估已配置但尚未实现")
        
        except Exception as e:
            logger.error(f"执行认知负荷评估时出错: {e}")
    
    def add_assessment(self, user_id: str, task_type: str, scores: Dict[str, float],
                     comments: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        添加认知负荷评估数据
        
        Args:
            user_id: 用户ID
            task_type: 任务类型
            scores: 评分数据
            comments: 用户评论
            metadata: 元数据
            
        Returns:
            评估记录或None
        """
        if self.assessor is None:
            logger.error("认知负荷评估器未初始化，无法添加评估")
            return None
        
        try:
            # 添加评估
            assessment = self.assessor.add_assessment(
                user_id=user_id,
                task_type=task_type,
                scores=scores,
                comments=comments,
                metadata=metadata
            )
            
            logger.info(f"已添加认知负荷评估: {user_id} - {task_type}")
            return assessment
        except Exception as e:
            logger.error(f"添加认知负荷评估时出错: {e}")
            return None
    
    def get_report(self, user_id: Optional[str] = None, 
                 task_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取认知负荷评估报告
        
        Args:
            user_id: 用户ID，如果为None则包含所有用户
            task_type: 任务类型，如果为None则包含所有任务类型
            
        Returns:
            评估报告或None
        """
        if self.assessor is None:
            logger.error("认知负荷评估器未初始化，无法获取报告")
            return None
        
        try:
            # 获取报告
            report = self.assessor.get_cognitive_load_report(
                user_id=user_id,
                task_type=task_type
            )
            
            return report
        except Exception as e:
            logger.error(f"获取认知负荷评估报告时出错: {e}")
            return None
    
    def check_threshold(self, user_id: Optional[str] = None,
                      task_type: Optional[str] = None) -> bool:
        """
        检查认知负荷是否在可接受范围内
        
        Args:
            user_id: 用户ID，如果为None则包含所有用户
            task_type: 任务类型，如果为None则包含所有任务类型
            
        Returns:
            认知负荷是否可接受
        """
        if self.assessor is None:
            logger.error("认知负荷评估器未初始化，无法检查阈值")
            return True  # 默认返回True以避免误报
        
        try:
            # 获取阈值
            threshold = self.config.get("threshold", DEFAULT_THRESHOLD)
            
            # 检查是否在可接受范围内
            acceptable = self.assessor.is_cognitive_load_acceptable(
                user_id=user_id,
                task_type=task_type,
                threshold=threshold
            )
            
            if not acceptable:
                logger.warning(f"认知负荷超过阈值 {threshold}")
                
                # 如果启用了通知，发送通知
                if self.config.get("notification_enabled", True):
                    self._send_notification(
                        f"认知负荷警告: 用户 {user_id or '所有用户'} 在 {task_type or '所有任务'} 中的认知负荷超过阈值"
                    )
            
            return acceptable
        except Exception as e:
            logger.error(f"检查认知负荷阈值时出错: {e}")
            return True  # 默认返回True以避免误报
    
    def visualize_assessment(self, data: Dict[str, Any], output_dir: Optional[str] = None,
                          show: bool = False) -> List[str]:
        """
        可视化认知负荷评估数据
        
        Args:
            data: 评估数据
            output_dir: 输出目录
            show: 是否显示图表
            
        Returns:
            生成的图表文件路径列表
        """
        if self.visualization is None:
            logger.error("认知负荷可视化功能不可用")
            return []
        
        try:
            # 设置默认输出目录
            if output_dir is None:
                output_dir = os.path.join(project_root, "reports", "visualizations")
            
            # 可视化
            return self.visualization(data, output_dir, show=show)
        except Exception as e:
            logger.error(f"可视化认知负荷评估数据时出错: {e}")
            return []
    
    def _send_notification(self, message: str):
        """
        发送通知
        
        Args:
            message: 通知消息
        """
        # 实际应用中应根据通知系统实现此方法
        # 这里仅作为示意
        logger.info(f"通知: {message}")
        
        # 尝试使用系统通知工具
        try:
            from src.utils.notifications import send_notification
            send_notification("认知负荷警告", message, level="warning")
        except ImportError:
            pass


# 单例模式实现
_cognitive_load_monitor = None

def get_cognitive_load_monitor() -> CognitiveLoadMonitor:
    """
    获取认知负荷监控器实例
    
    Returns:
        认知负荷监控器实例
    """
    global _cognitive_load_monitor
    
    if _cognitive_load_monitor is None:
        _cognitive_load_monitor = CognitiveLoadMonitor()
    
    return _cognitive_load_monitor

def initialize_cognitive_load_monitoring(auto_start: bool = True) -> bool:
    """
    初始化认知负荷监控
    
    Args:
        auto_start: 是否自动启动监控
        
    Returns:
        是否成功初始化
    """
    try:
        monitor = get_cognitive_load_monitor()
        
        if auto_start:
            monitor.start_monitoring()
        
        logger.info("认知负荷监控已初始化")
        return True
    except Exception as e:
        logger.error(f"初始化认知负荷监控时出错: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    initialize_cognitive_load_monitoring()
    
    # 获取监控器
    monitor = get_cognitive_load_monitor()
    
    # 添加模拟评估
    monitor.add_assessment(
        user_id="test_user",
        task_type="test_task",
        scores={
            "mental_demand": 2.5,
            "physical_demand": 1.2,
            "temporal_demand": 2.0,
            "performance": 1.8,
            "effort": 2.7,
            "frustration": 1.5
        },
        comments="测试评估"
    )
    
    # 获取报告
    report = monitor.get_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 可视化报告
    monitor.visualize_assessment(
        data={"scores": {
            "mental_demand": 2.5,
            "physical_demand": 1.2,
            "temporal_demand": 2.0,
            "performance": 1.8,
            "effort": 2.7,
            "frustration": 1.5,
            "overall": 2.0
        }},
        show=True
    )
    
    # 停止监控
    monitor.stop_monitoring() 