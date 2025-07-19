"""模型加载适配器

此模块提供适配器，将按需加载引擎(OnDemandLoader)与模型切换器(ModelSwitcher)集成。
"""

import gc
import time
from typing import Dict, Optional, Any, List
from loguru import logger

from src.core.on_demand_loader import OnDemandLoader, ModelLoadRequest
from src.core.model_switcher import ModelSwitcher
from src.core.language_detector import LanguageDetector

# 导入预警系统
try:
    from src.monitoring.alert_system import (
        AlertLevel, AlertCategory, check_model_latency, 
        check_memory_usage, trigger_custom_alert
    )
    ALERT_SYSTEM_AVAILABLE = True
except ImportError:
    logger.warning("预警系统模块不可用，将禁用模型加载预警")
    ALERT_SYSTEM_AVAILABLE = False

class ModelLoaderAdapter:
    """模型加载适配器
    
    将按需加载引擎与模型切换器集成，提供统一的模型管理接口
    """
    
    def __init__(
        self,
        on_demand_loader: Optional[OnDemandLoader] = None,
        model_switcher: Optional[ModelSwitcher] = None,
        language_detector: Optional[LanguageDetector] = None,
        enable_alerts: bool = True
    ):
        """初始化模型加载适配器
        
        Args:
            on_demand_loader: 按需加载引擎实例
            model_switcher: 模型切换器实例
            language_detector: 语言检测器实例
            enable_alerts: 是否启用预警
        """
        self.on_demand_loader = on_demand_loader or OnDemandLoader()
        self.model_switcher = model_switcher or ModelSwitcher()
        self.language_detector = language_detector or LanguageDetector()
        self.enable_alerts = enable_alerts and ALERT_SYSTEM_AVAILABLE
        
        # 当前活动模型
        self.active_model = None
        
        # 性能监控数据
        self.performance_stats = {
            "switch_times": [],  # 模型切换耗时记录
            "last_memory_check": 0,  # 上次内存检查时间
            "memory_check_interval": 30,  # 内存检查间隔(秒)
        }
        
        logger.info("模型加载适配器初始化完成")
    
    def switch_to_language(self, language: str) -> bool:
        """切换到指定语言的模型
        
        Args:
            language: 语言代码(zh/en)
            
        Returns:
            bool: 是否成功切换
        """
        logger.info(f"切换到语言: {language}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 使用按需加载引擎切换语言
            success = self.on_demand_loader.switch_language(language)
            if success:
                # 获取当前活动模型
                self.active_model = self.on_demand_loader.active_model
                
                # 通知模型切换器
                self.model_switcher.switch_model(self.active_model)
                
                logger.info(f"已切换到语言 {language}, 模型: {self.active_model}")
                
                # 记录切换耗时
                elapsed_time = time.time() - start_time
                self.performance_stats["switch_times"].append(elapsed_time)
                
                # 限制历史记录长度
                if len(self.performance_stats["switch_times"]) > 20:
                    self.performance_stats["switch_times"] = self.performance_stats["switch_times"][-20:]
                
                # 如果启用了预警系统，检查切换时间
                if self.enable_alerts:
                    self._check_switch_time(elapsed_time, language)
                    
                    # 定期检查内存使用
                    now = time.time()
                    if now - self.performance_stats["last_memory_check"] >= self.performance_stats["memory_check_interval"]:
                        self._check_memory_usage()
                        self.performance_stats["last_memory_check"] = now
            else:
                # 切换失败预警
                if self.enable_alerts:
                    self._alert_switch_failed(language)
                    
            return success
            
        except Exception as e:
            logger.error(f"切换模型异常: {str(e)}")
            
            # 异常预警
            if self.enable_alerts:
                self._alert_switch_exception(language, str(e))
                
            return False
    
    def _check_switch_time(self, elapsed_time: float, language: str) -> None:
        """检查模型切换时间并触发预警
        
        Args:
            elapsed_time: 切换耗时(秒)
            language: 语言代码
        """
        if not ALERT_SYSTEM_AVAILABLE:
            return
            
        try:
            # 将秒转换为毫秒
            elapsed_ms = elapsed_time * 1000
            model_name = f"{language}_switch"
            
            # 检查模型切换延迟
            check_model_latency(
                elapsed_ms,
                model_name,
                {
                    "operation": "model_switch",
                    "language": language,
                    "recommendation": "考虑优化模型量化级别或减少模型加载频率" if elapsed_ms > 3000 else None
                }
            )
            
        except Exception as e:
            logger.error(f"检查模型切换时间异常: {str(e)}")
    
    def _check_memory_usage(self) -> None:
        """检查内存使用情况
        """
        if not ALERT_SYSTEM_AVAILABLE:
            return
            
        try:
            import psutil
            
            # 获取当前内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 检查内存使用率
            check_memory_usage(
                memory_percent,
                {
                    "operation": "model_loaded",
                    "model": self.active_model,
                    "available_mb": memory.available // (1024 * 1024)
                }
            )
            
        except ImportError:
            logger.warning("psutil模块不可用，跳过内存检查")
        except Exception as e:
            logger.error(f"检查内存使用异常: {str(e)}")
    
    def _alert_switch_failed(self, language: str) -> None:
        """触发模型切换失败预警
        
        Args:
            language: 语言代码
        """
        if not ALERT_SYSTEM_AVAILABLE:
            return
            
        try:
            trigger_custom_alert(
                AlertLevel.ERROR,
                AlertCategory.MODEL,
                f"model_switch_{language}",
                0,  # 失败状态值
                f"切换到{language}语言模型失败",
                {
                    "recommendation": "检查模型文件是否完整，尝试重新加载"
                }
            )
        except Exception as e:
            logger.error(f"触发模型切换失败预警异常: {str(e)}")
    
    def _alert_switch_exception(self, language: str, error_message: str) -> None:
        """触发模型切换异常预警
        
        Args:
            language: 语言代码
            error_message: 错误消息
        """
        if not ALERT_SYSTEM_AVAILABLE:
            return
            
        try:
            trigger_custom_alert(
                AlertLevel.ERROR,
                AlertCategory.MODEL,
                f"model_switch_exception_{language}",
                0,  # 异常状态值
                f"切换到{language}语言模型发生异常",
                {
                    "error": error_message,
                    "recommendation": "检查日志获取详细错误信息，尝试重启应用"
                }
            )
        except Exception as e:
            logger.error(f"触发模型切换异常预警异常: {str(e)}")
    
    def detect_and_switch(self, text: str) -> str:
        """检测文本语言并切换到相应模型
        
        Args:
            text: 输入文本
            
        Returns:
            str: 检测到的语言代码
        """
        # 记录开始时间
        start_time = time.time()
        
        # 检测语言
        language = self.language_detector.detect_from_text(text)
        logger.info(f"检测到语言: {language}")
        
        # 检测耗时
        detection_time = time.time() - start_time
        
        # 如果启用了预警系统，检查语言检测时间
        if self.enable_alerts and ALERT_SYSTEM_AVAILABLE and detection_time > 0.5:  # 超过500ms视为过慢
            try:
                trigger_custom_alert(
                    AlertLevel.WARNING,
                    AlertCategory.PERFORMANCE,
                    "language_detection",
                    detection_time * 1000,  # 转换为毫秒
                    f"语言检测耗时过长: {detection_time:.2f}秒",
                    {
                        "text_length": len(text),
                        "recommendation": "考虑优化语言检测算法或减少文本长度"
                    }
                )
            except Exception as e:
                logger.error(f"触发语言检测预警异常: {str(e)}")
        
        # 切换到相应语言
        self.switch_to_language(language)
        
        return language
    
    def get_active_model_info(self) -> Dict:
        """获取当前活动模型信息
        
        Returns:
            Dict: 模型信息
        """
        return self.on_demand_loader.get_model_info()
    
    def get_available_models(self) -> List[Dict]:
        """获取所有可用模型信息
        
        Returns:
            List[Dict]: 模型信息列表
        """
        return self.on_demand_loader.get_available_models()
    
    def unload_all_models(self) -> None:
        """卸载所有模型"""
        logger.info("卸载所有模型")
        
        # 获取所有已加载模型
        models = self.on_demand_loader.get_available_models()
        for model in models:
            if model.get("loaded", False):
                self.on_demand_loader.unload_model(model["name"])
        
        self.active_model = None
        
        # 释放内存
        gc.collect()
        
        # 记录内存释放预警
        if self.enable_alerts and ALERT_SYSTEM_AVAILABLE:
            try:
                trigger_custom_alert(
                    AlertLevel.INFO,
                    AlertCategory.MEMORY,
                    "model_unload",
                    0,
                    "所有模型已卸载，内存已释放",
                    {}
                )
            except Exception as e:
                logger.error(f"触发模型卸载预警异常: {str(e)}")
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息
        
        Returns:
            Dict: 性能统计信息
        """
        stats = self.performance_stats.copy()
        
        # 计算平均切换时间
        switch_times = stats.get("switch_times", [])
        if switch_times:
            stats["avg_switch_time"] = sum(switch_times) / len(switch_times)
            stats["max_switch_time"] = max(switch_times)
            stats["min_switch_time"] = min(switch_times)
        
        return stats
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.unload_all_models() 