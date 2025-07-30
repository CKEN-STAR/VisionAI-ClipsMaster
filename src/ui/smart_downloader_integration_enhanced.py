#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强智能推荐下载器集成模块

将优化的UI与现有系统集成，确保：
1. 硬件信息实时更新
2. 推荐内容动态响应
3. 设备迁移适配
4. 错误处理和状态指示
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class SmartDownloaderIntegrationManager(QObject):
    """智能下载器集成管理器"""
    
    # 信号定义
    hardware_detected = pyqtSignal(dict)           # 硬件检测完成
    recommendation_updated = pyqtSignal(str, dict) # 推荐更新 (model_name, recommendation)
    download_started = pyqtSignal(str, dict)       # 下载开始 (model_name, variant_info)
    integration_status_changed = pyqtSignal(str)   # 集成状态变化
    
    def __init__(self):
        super().__init__()
        self.is_initialized = False
        self.components = {}
        self.hardware_cache = {}
        self.recommendation_cache = {}
        self.download_callback = None
        
        # 集成状态
        self.integration_status = {
            "ui_components": False,
            "hardware_detector": False,
            "intelligent_selector": False,
            "download_manager": False
        }
    
    def initialize(self, download_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """初始化集成管理器

        Args:
            download_callback: 下载回调函数

        Returns:
            Dict[str, Any]: 初始化结果和状态信息
        """
        result = {
            "success": False,
            "status": "initializing",
            "components": {},
            "errors": [],
            "timestamp": time.time()
        }

        try:
            logger.info("🔧 开始初始化智能下载器集成管理器")

            self.download_callback = download_callback

            # 1. 初始化UI组件
            try:
                self._initialize_ui_components()
                result["components"]["ui_components"] = True
            except Exception as e:
                result["components"]["ui_components"] = False
                result["errors"].append(f"UI组件初始化失败: {e}")

            # 2. 初始化硬件检测器
            try:
                self._initialize_hardware_detector()
                result["components"]["hardware_detector"] = True
            except Exception as e:
                result["components"]["hardware_detector"] = False
                result["errors"].append(f"硬件检测器初始化失败: {e}")

            # 3. 初始化智能选择器
            try:
                self._initialize_intelligent_selector()
                result["components"]["intelligent_selector"] = True
            except Exception as e:
                result["components"]["intelligent_selector"] = False
                result["errors"].append(f"智能选择器初始化失败: {e}")

            # 4. 初始化下载管理器
            try:
                self._initialize_download_manager()
                result["components"]["download_manager"] = True
            except Exception as e:
                result["components"]["download_manager"] = False
                result["errors"].append(f"下载管理器初始化失败: {e}")

            # 检查整体初始化状态
            successful_components = sum(result["components"].values())
            total_components = len(result["components"])

            if successful_components == total_components:
                self.is_initialized = True
                result["success"] = True
                result["status"] = "initialized"
                logger.info("✅ 智能下载器集成管理器初始化完成")
                self.integration_status_changed.emit("initialized")
            else:
                result["status"] = "partially_initialized"
                logger.warning(f"⚠️ 集成管理器部分初始化成功: {successful_components}/{total_components}")
                self.integration_status_changed.emit("partially_initialized")

            return result

        except Exception as e:
            logger.error(f"❌ 集成管理器初始化失败: {e}")
            result["success"] = False
            result["status"] = "failed"
            result["errors"].append(str(e))
            self.integration_status_changed.emit(f"failed: {e}")
            return result

    def cleanup(self):
        """清理集成管理器资源"""
        try:
            logger.info("🧹 开始清理智能下载器集成管理器")

            # 清理组件缓存
            self.components.clear()
            self.hardware_cache.clear()
            self.recommendation_cache.clear()

            # 重置状态
            self.is_initialized = False
            self.download_callback = None

            # 重置集成状态
            for key in self.integration_status:
                self.integration_status[key] = False

            logger.info("✅ 智能下载器集成管理器清理完成")
            self.integration_status_changed.emit("cleaned")

        except Exception as e:
            logger.error(f"❌ 集成管理器清理失败: {e}")

    def _initialize_ui_components(self):
        """初始化UI组件"""
        try:
            from src.ui.smart_downloader_ui_optimized import (
                SmartDownloaderDialog,
                RealTimeHardwareInfoWidget,
                DynamicRecommendationWidget
            )
            
            self.components["SmartDownloaderDialog"] = SmartDownloaderDialog
            self.components["RealTimeHardwareInfoWidget"] = RealTimeHardwareInfoWidget
            self.components["DynamicRecommendationWidget"] = DynamicRecommendationWidget
            
            self.integration_status["ui_components"] = True
            logger.info("✅ UI组件初始化成功")
            
        except ImportError as e:
            logger.error(f"❌ UI组件导入失败: {e}")
            self.integration_status["ui_components"] = False
            raise
    
    def _initialize_hardware_detector(self):
        """初始化硬件检测器"""
        try:
            from src.core.hardware_detector import HardwareDetector
            
            self.components["HardwareDetector"] = HardwareDetector
            self.integration_status["hardware_detector"] = True
            logger.info("✅ 硬件检测器初始化成功")
            
        except ImportError as e:
            logger.error(f"❌ 硬件检测器导入失败: {e}")
            self.integration_status["hardware_detector"] = False
            raise
    
    def _initialize_intelligent_selector(self):
        """初始化智能选择器"""
        try:
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            self.components["IntelligentModelSelector"] = IntelligentModelSelector
            self.integration_status["intelligent_selector"] = True
            logger.info("✅ 智能选择器初始化成功")
            
        except ImportError as e:
            logger.error(f"❌ 智能选择器导入失败: {e}")
            self.integration_status["intelligent_selector"] = False
            raise
    
    def _initialize_download_manager(self):
        """初始化下载管理器"""
        try:
            # 尝试导入增强模型下载器
            try:
                from src.core.enhanced_model_downloader import EnhancedModelDownloader
                self.components["EnhancedModelDownloader"] = EnhancedModelDownloader
                logger.info("✅ 增强模型下载器导入成功")
            except ImportError:
                logger.warning("⚠️ 增强模型下载器不可用，使用基础下载功能")
            
            self.integration_status["download_manager"] = True
            logger.info("✅ 下载管理器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 下载管理器初始化失败: {e}")
            self.integration_status["download_manager"] = False
            raise
    
    def create_smart_downloader_dialog(self, model_name: str, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """创建智能下载器对话框
        
        Args:
            model_name: 模型名称
            parent: 父窗口
            
        Returns:
            Optional[QWidget]: 创建的对话框，失败时返回None
        """
        if not self.is_initialized:
            logger.error("❌ 集成管理器未初始化")
            return None
        
        try:
            dialog_class = self.components.get("SmartDownloaderDialog")
            if not dialog_class:
                logger.error("❌ SmartDownloaderDialog组件不可用")
                return None
            
            # 创建对话框
            dialog = dialog_class(model_name, parent)
            
            # 连接下载信号
            dialog.download_requested.connect(self._handle_download_request)
            
            logger.info(f"✅ 创建智能下载器对话框: {model_name}")
            return dialog
            
        except Exception as e:
            logger.error(f"❌ 创建智能下载器对话框失败: {e}")
            return None
    
    def _handle_download_request(self, model_name: str, variant_info: Dict):
        """处理下载请求
        
        Args:
            model_name: 模型名称
            variant_info: 变体信息
        """
        try:
            logger.info(f"📥 处理下载请求: {model_name}")
            logger.debug(f"变体信息: {variant_info}")
            
            # 发送下载开始信号
            self.download_started.emit(model_name, variant_info)
            
            # 调用下载回调
            if self.download_callback:
                self.download_callback(model_name, variant_info)
            else:
                # 使用默认下载逻辑
                self._default_download_handler(model_name, variant_info)
                
        except Exception as e:
            logger.error(f"❌ 处理下载请求失败: {e}")
    
    def _default_download_handler(self, model_name: str, variant_info: Dict):
        """默认下载处理器
        
        Args:
            model_name: 模型名称
            variant_info: 变体信息
        """
        try:
            # 尝试使用增强模型下载器
            downloader_class = self.components.get("EnhancedModelDownloader")
            if downloader_class:
                downloader = downloader_class()
                
                # 构建下载参数
                download_params = {
                    "model_name": model_name,
                    "variant_name": variant_info.get("variant_name"),
                    "quantization": variant_info.get("quantization"),
                    "auto_select": True
                }
                
                # 开始下载
                success = downloader.download_model(**download_params)
                
                if success:
                    logger.info(f"✅ 模型下载成功: {model_name}")
                else:
                    logger.error(f"❌ 模型下载失败: {model_name}")
            else:
                logger.warning("⚠️ 增强模型下载器不可用，请手动处理下载")
                
        except Exception as e:
            logger.error(f"❌ 默认下载处理失败: {e}")
    
    def get_hardware_info(self, force_refresh: bool = False) -> Dict:
        """获取硬件信息
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            Dict: 硬件信息
        """
        if force_refresh or not self.hardware_cache:
            try:
                detector_class = self.components.get("HardwareDetector")
                if detector_class:
                    detector = detector_class()
                    hardware_info = detector.detect_hardware()
                    
                    # 转换为字典格式并缓存
                    self.hardware_cache = {
                        'gpu_type': str(getattr(hardware_info, 'gpu_type', 'unknown')),
                        'gpu_memory_gb': getattr(hardware_info, 'gpu_memory_gb', 0),
                        'system_ram_gb': getattr(hardware_info, 'total_memory_gb', 0),
                        'cpu_cores': getattr(hardware_info, 'cpu_cores', 0),
                        'performance_level': str(getattr(hardware_info, 'performance_level', 'unknown')),
                        'detection_timestamp': time.time()
                    }
                    
                    # 发送硬件检测信号
                    self.hardware_detected.emit(self.hardware_cache)
                    
            except Exception as e:
                logger.error(f"❌ 获取硬件信息失败: {e}")
                return {}
        
        return self.hardware_cache.copy()
    
    def get_recommendation(self, model_name: str, force_refresh: bool = False) -> Dict:
        """获取模型推荐
        
        Args:
            model_name: 模型名称
            force_refresh: 是否强制刷新
            
        Returns:
            Dict: 推荐信息
        """
        cache_key = model_name
        
        if force_refresh or cache_key not in self.recommendation_cache:
            try:
                selector_class = self.components.get("IntelligentModelSelector")
                if selector_class:
                    selector = selector_class()
                    
                    # 强制刷新硬件配置
                    if force_refresh:
                        selector.force_refresh_hardware()
                    
                    # 获取推荐
                    recommendation = selector.recommend_model_version(model_name)
                    
                    if recommendation:
                        # 转换为字典格式并缓存
                        recommendation_dict = {
                            'model_name': recommendation.model_name,
                            'variant_name': recommendation.variant.name if recommendation.variant else None,
                            'quantization': recommendation.variant.quantization.value if recommendation.variant else None,
                            'size_gb': recommendation.variant.size_gb if recommendation.variant else None,
                            'memory_requirement_gb': recommendation.variant.memory_requirement_gb if recommendation.variant else None,
                            'reasoning': recommendation.reasoning if hasattr(recommendation, 'reasoning') else [],
                            'recommendation_timestamp': time.time()
                        }
                        
                        self.recommendation_cache[cache_key] = recommendation_dict
                        
                        # 发送推荐更新信号
                        self.recommendation_updated.emit(model_name, recommendation_dict)
                    else:
                        logger.warning(f"⚠️ 未获取到模型推荐: {model_name}")
                        return {}
                        
            except Exception as e:
                logger.error(f"❌ 获取模型推荐失败: {e}")
                return {}
        
        return self.recommendation_cache.get(cache_key, {})
    
    def show_smart_downloader(self, model_name: str, parent: Optional[QWidget] = None) -> bool:
        """显示智能下载器对话框
        
        Args:
            model_name: 模型名称
            parent: 父窗口
            
        Returns:
            bool: 是否成功显示
        """
        try:
            dialog = self.create_smart_downloader_dialog(model_name, parent)
            if dialog:
                result = dialog.exec()
                return result == dialog.DialogCode.Accepted
            else:
                # 回退到简单消息框
                QMessageBox.information(
                    parent,
                    "智能下载器",
                    f"智能下载器暂时不可用。\n请手动下载模型: {model_name}"
                )
                return False
                
        except Exception as e:
            logger.error(f"❌ 显示智能下载器失败: {e}")
            QMessageBox.critical(
                parent,
                "错误",
                f"智能下载器启动失败: {e}"
            )
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态
        
        Returns:
            Dict[str, Any]: 集成状态信息
        """
        return {
            "is_initialized": self.is_initialized,
            "components": self.integration_status.copy(),
            "hardware_cache_size": len(self.hardware_cache),
            "recommendation_cache_size": len(self.recommendation_cache)
        }


# 全局集成管理器实例
_integration_manager = None


def get_integration_manager() -> SmartDownloaderIntegrationManager:
    """获取全局集成管理器实例"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = SmartDownloaderIntegrationManager()
    return _integration_manager


def initialize_smart_downloader_integration(download_callback: Optional[Callable] = None) -> bool:
    """初始化智能下载器集成

    Args:
        download_callback: 下载回调函数

    Returns:
        bool: 初始化是否成功
    """
    manager = get_integration_manager()
    result = manager.initialize(download_callback)

    # 兼容性处理：如果返回字典，提取success字段
    if isinstance(result, dict):
        return result.get("success", False)

    # 如果返回布尔值，直接返回
    return bool(result)


def show_smart_downloader_dialog(model_name: str, parent: Optional[QWidget] = None) -> bool:
    """显示智能下载器对话框
    
    Args:
        model_name: 模型名称
        parent: 父窗口
        
    Returns:
        bool: 是否成功显示并确认下载
    """
    manager = get_integration_manager()
    return manager.show_smart_downloader(model_name, parent)


if __name__ == "__main__":
    # 测试代码
    import time
    
    app = QApplication(sys.argv)
    
    # 初始化集成管理器
    def test_download_callback(model_name, variant_info):
        print(f"测试下载回调: {model_name}")
        print(f"变体信息: {variant_info}")
    
    success = initialize_smart_downloader_integration(test_download_callback)
    print(f"集成初始化结果: {success}")
    
    if success:
        # 显示智能下载器
        result = show_smart_downloader_dialog("qwen2.5-7b")
        print(f"对话框结果: {result}")
    
    sys.exit(0)
