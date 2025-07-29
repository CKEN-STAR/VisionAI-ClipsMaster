#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态下载器集成管理器 - VisionAI-ClipsMaster
整合动态硬件监控、模型推荐和智能下载功能
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class DynamicDownloaderIntegrationManager(QObject):
    """动态下载器集成管理器 - 主管理类"""

    download_completed = pyqtSignal(str, bool)  # 下载完成信号
    hardware_changed = pyqtSignal(object)  # 硬件变化信号
    recommendation_updated = pyqtSignal(str, object)  # 推荐更新信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.integration = DynamicDownloaderIntegration(parent)

        # 连接信号
        self.integration.download_completed.connect(self.download_completed)
        self.integration.hardware_changed.connect(self.hardware_changed)
        self.integration.recommendation_updated.connect(self.recommendation_updated)

        logger.info("动态下载器集成管理器初始化完成")

    def show_smart_downloader(self, model_name: str = None):
        """显示智能下载器"""
        return self.integration.show_smart_downloader(model_name)

    def refresh_hardware_info(self):
        """刷新硬件信息"""
        return self.integration.refresh_hardware_info()

    def get_recommendation(self, model_name: str):
        """获取推荐"""
        return self.integration.get_recommendation(model_name)

class DynamicDownloaderIntegration(QObject):
    """动态下载器集成管理器"""
    
    download_completed = pyqtSignal(str, bool)  # 下载完成信号 (model_name, success)
    hardware_changed = pyqtSignal(object)  # 硬件变化信号
    recommendation_updated = pyqtSignal(str, object)  # 推荐更新信号 (model_name, recommendation)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.current_dialog = None
        self.hardware_change_callbacks = []
        self.download_callbacks = []
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 检查依赖组件
            self._check_dependencies()
            
            logger.info("动态下载器集成管理器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化动态下载器集成管理器失败: {e}")
            raise
    
    def _check_dependencies(self):
        """检查依赖组件"""
        try:
            # 检查硬件监控组件
            from src.ui.dynamic_hardware_monitor import RealTimeHardwareInfoWidget
            
            # 检查模型推荐组件
            from src.ui.dynamic_model_recommendation import DynamicModelRecommendationWidget
            
            # 检查增强对话框
            from src.ui.enhanced_smart_downloader_dialog import EnhancedSmartDownloaderDialog
            
            # 检查核心组件
            from src.core.enhanced_model_downloader import EnhancedModelDownloader
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            logger.info("所有依赖组件检查通过")
            
        except ImportError as e:
            logger.error(f"依赖组件检查失败: {e}")
            raise
    
    def show_smart_downloader(self, model_name: str, parent_widget: QWidget = None) -> bool:
        """显示智能下载器对话框"""
        try:
            # 导入增强对话框
            from src.ui.enhanced_smart_downloader_dialog import EnhancedSmartDownloaderDialog
            
            # 创建对话框
            parent = parent_widget or self.parent_widget
            dialog = EnhancedSmartDownloaderDialog(model_name, parent)
            
            # 连接信号
            dialog.download_requested.connect(self._handle_download_request)
            dialog.hardware_changed.connect(self._handle_hardware_change)
            
            # 保存当前对话框引用
            self.current_dialog = dialog
            
            # 显示对话框
            result = dialog.exec()
            
            # 清除引用
            self.current_dialog = None
            
            return result == dialog.DialogCode.Accepted
            
        except Exception as e:
            logger.error(f"显示智能下载器失败: {e}")
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "错误",
                    f"智能下载器启动失败:\n{e}"
                )
            return False
    
    def _handle_download_request(self, model_name: str, variant_info):
        """处理下载请求"""
        try:
            logger.info(f"收到下载请求: {model_name}, 变体: {variant_info.name}")
            
            # 导入增强下载器
            from src.core.enhanced_model_downloader import EnhancedModelDownloader
            
            # 创建下载器
            downloader = EnhancedModelDownloader()
            
            # 执行下载
            success = self._execute_download(downloader, model_name, variant_info)
            
            # 发送完成信号
            self.download_completed.emit(model_name, success)
            
            # 调用回调函数
            for callback in self.download_callbacks:
                try:
                    callback(model_name, variant_info, success)
                except Exception as e:
                    logger.error(f"下载回调执行失败: {e}")
            
        except Exception as e:
            logger.error(f"处理下载请求失败: {e}")
            self.download_completed.emit(model_name, False)
    
    def _execute_download(self, downloader, model_name: str, variant_info) -> bool:
        """执行下载"""
        try:
            # 这里可以根据variant_info的信息来执行具体的下载逻辑
            # 目前使用基础下载功能
            
            logger.info(f"开始下载 {model_name} ({variant_info.name})")
            
            # 调用下载器的下载方法
            success = downloader.download_model(model_name, self.parent_widget)
            
            if success:
                logger.info(f"下载完成: {model_name}")
            else:
                logger.warning(f"下载失败或取消: {model_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"执行下载失败: {e}")
            return False
    
    def _handle_hardware_change(self, hardware_snapshot):
        """处理硬件变化"""
        try:
            logger.info("检测到硬件配置变化")
            
            # 发送硬件变化信号
            self.hardware_changed.emit(hardware_snapshot)
            
            # 调用硬件变化回调
            for callback in self.hardware_change_callbacks:
                try:
                    callback(hardware_snapshot)
                except Exception as e:
                    logger.error(f"硬件变化回调执行失败: {e}")
            
        except Exception as e:
            logger.error(f"处理硬件变化失败: {e}")
    
    def register_download_callback(self, callback: Callable):
        """注册下载回调函数"""
        if callback not in self.download_callbacks:
            self.download_callbacks.append(callback)
            logger.info("下载回调函数已注册")
    
    def register_hardware_change_callback(self, callback: Callable):
        """注册硬件变化回调函数"""
        if callback not in self.hardware_change_callbacks:
            self.hardware_change_callbacks.append(callback)
            logger.info("硬件变化回调函数已注册")
    
    def unregister_download_callback(self, callback: Callable):
        """注销下载回调函数"""
        if callback in self.download_callbacks:
            self.download_callbacks.remove(callback)
            logger.info("下载回调函数已注销")
    
    def unregister_hardware_change_callback(self, callback: Callable):
        """注销硬件变化回调函数"""
        if callback in self.hardware_change_callbacks:
            self.hardware_change_callbacks.remove(callback)
            logger.info("硬件变化回调函数已注销")
    
    def get_hardware_info(self) -> Optional[Dict]:
        """获取当前硬件信息"""
        try:
            if self.current_dialog and hasattr(self.current_dialog, 'hardware_widget'):
                return self.current_dialog.hardware_widget.get_hardware_info()
            
            # 如果没有活动对话框，直接检测硬件
            from src.utils.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            return {
                'gpu_type': str(getattr(hardware_info, 'gpu_type', 'unknown')),
                'gpu_memory_gb': getattr(hardware_info, 'gpu_memory_gb', 0),
                'gpu_count': getattr(hardware_info, 'gpu_count', 0),
                'gpu_names': getattr(hardware_info, 'gpu_names', []),
                'system_ram_gb': getattr(hardware_info, 'total_memory_gb', 0),
                'available_ram_gb': getattr(hardware_info, 'available_memory_gb', 0),
                'cpu_cores': getattr(hardware_info, 'cpu_cores', 0),
                'cpu_freq_mhz': getattr(hardware_info, 'cpu_freq_mhz', 0),
                'performance_level': str(getattr(hardware_info, 'performance_level', 'unknown')),
                'recommended_quantization': getattr(hardware_info, 'recommended_quantization', 'unknown'),
                'gpu_acceleration': getattr(hardware_info, 'gpu_acceleration', False),
                'has_gpu': getattr(hardware_info, 'gpu_memory_gb', 0) > 0,
                'detection_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"获取硬件信息失败: {e}")
            return None
    
    def get_model_recommendation(self, model_name: str) -> Optional[Dict]:
        """获取模型推荐"""
        try:
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            selector = IntelligentModelSelector()
            recommendation = selector.recommend_model_version(model_name)
            
            if recommendation and recommendation.variant:
                return {
                    'model_name': recommendation.model_name,
                    'variant_name': recommendation.variant.name,
                    'quantization': recommendation.variant.quantization.value,
                    'size_gb': recommendation.variant.size_gb,
                    'quality_retention': recommendation.variant.quality_retention,
                    'recommendation_reason': getattr(recommendation, 'reason', '智能推荐')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取模型推荐失败: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        try:
            # 关闭当前对话框
            if self.current_dialog:
                self.current_dialog.close()
                self.current_dialog = None
            
            # 清除回调函数
            self.download_callbacks.clear()
            self.hardware_change_callbacks.clear()
            
            logger.info("动态下载器集成管理器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

# 便捷函数
def create_dynamic_downloader_integration(parent_widget: QWidget = None) -> DynamicDownloaderIntegration:
    """创建动态下载器集成管理器"""
    return DynamicDownloaderIntegration(parent_widget)

def show_enhanced_smart_downloader(model_name: str, parent_widget: QWidget = None) -> bool:
    """显示增强智能下载器（便捷函数）"""
    try:
        integration = create_dynamic_downloader_integration(parent_widget)
        result = integration.show_smart_downloader(model_name, parent_widget)
        integration.cleanup()
        return result
        
    except Exception as e:
        logger.error(f"显示增强智能下载器失败: {e}")
        if parent_widget:
            QMessageBox.critical(
                parent_widget,
                "错误",
                f"智能下载器启动失败:\n{e}"
            )
        return False
