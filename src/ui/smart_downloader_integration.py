#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 智能下载器UI集成模块
确保智能下载器功能与主界面的完美集成
"""

import logging
import sys
from typing import Dict, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class SmartDownloaderUIIntegration:
    """智能下载器UI集成管理器"""
    
    def __init__(self):
        self.integration_status = {
            "main_window": False,
            "enhanced_dialog": False,
            "progress_components": False,
            "error_handling": False
        }
        self.components = {}
        self.main_window = None
        
    def initialize_integration(self, main_window=None) -> Dict[str, bool]:
        """初始化UI集成"""
        logger.info("🔧 开始初始化智能下载器UI集成")
        
        try:
            # 1. 集成主窗口
            self._integrate_main_window(main_window)
            
            # 2. 集成增强下载对话框
            self._integrate_enhanced_dialog()
            
            # 3. 集成进度组件
            self._integrate_progress_components()
            
            # 4. 集成错误处理
            self._integrate_error_handling()
            
            logger.info("✅ 智能下载器UI集成完成")
            return self.integration_status
            
        except Exception as e:
            logger.error(f"❌ UI集成失败: {e}")
            return self.integration_status
    
    def _integrate_main_window(self, main_window=None):
        """集成主窗口"""
        try:
            if main_window:
                self.main_window = main_window
                self.integration_status["main_window"] = True
                logger.info("✅ 主窗口集成成功 (外部提供)")
                return
            
            # 尝试导入MainWindow
            try:
                from src.ui.main_window import MainWindow
                self.components["MainWindow"] = MainWindow
                self.integration_status["main_window"] = True
                logger.info("✅ MainWindow类导入成功")
            except ImportError as e:
                logger.warning(f"⚠️ MainWindow导入失败: {e}")
                # 尝试备用路径
                try:
                    from ui.main_window import MainWindow
                    self.components["MainWindow"] = MainWindow
                    self.integration_status["main_window"] = True
                    logger.info("✅ MainWindow类导入成功 (备用路径)")
                except ImportError:
                    logger.error("❌ 所有MainWindow导入路径都失败")
                    self.integration_status["main_window"] = False
                    
        except Exception as e:
            logger.error(f"❌ 主窗口集成失败: {e}")
            self.integration_status["main_window"] = False
    
    def _integrate_enhanced_dialog(self):
        """集成增强下载对话框"""
        try:
            # 尝试导入EnhancedDownloadDialog
            try:
                from src.ui.enhanced_download_dialog import EnhancedDownloadDialog
                self.components["EnhancedDownloadDialog"] = EnhancedDownloadDialog
                self.integration_status["enhanced_dialog"] = True
                logger.info("✅ EnhancedDownloadDialog导入成功")
            except ImportError as e:
                logger.warning(f"⚠️ EnhancedDownloadDialog导入失败: {e}")
                # 尝试备用路径
                try:
                    from ui.enhanced_download_dialog import EnhancedDownloadDialog
                    self.components["EnhancedDownloadDialog"] = EnhancedDownloadDialog
                    self.integration_status["enhanced_dialog"] = True
                    logger.info("✅ EnhancedDownloadDialog导入成功 (备用路径)")
                except ImportError:
                    logger.error("❌ 所有EnhancedDownloadDialog导入路径都失败")
                    self.integration_status["enhanced_dialog"] = False
                    
        except Exception as e:
            logger.error(f"❌ 增强下载对话框集成失败: {e}")
            self.integration_status["enhanced_dialog"] = False
    
    def _integrate_progress_components(self):
        """集成进度组件"""
        try:
            # 检查PyQt6可用性
            try:
                from PyQt6.QtWidgets import QProgressDialog, QProgressBar
                from PyQt6.QtCore import QThread, pyqtSignal
                
                self.components["QProgressDialog"] = QProgressDialog
                self.components["QProgressBar"] = QProgressBar
                self.components["QThread"] = QThread
                self.components["pyqtSignal"] = pyqtSignal
                
                self.integration_status["progress_components"] = True
                logger.info("✅ 进度组件集成成功")
                
            except ImportError as e:
                logger.error(f"❌ PyQt6进度组件导入失败: {e}")
                self.integration_status["progress_components"] = False
                
        except Exception as e:
            logger.error(f"❌ 进度组件集成失败: {e}")
            self.integration_status["progress_components"] = False
    
    def _integrate_error_handling(self):
        """集成错误处理"""
        try:
            # 检查错误处理组件
            try:
                from PyQt6.QtWidgets import QMessageBox, QErrorMessage
                
                self.components["QMessageBox"] = QMessageBox
                self.components["QErrorMessage"] = QErrorMessage
                
                self.integration_status["error_handling"] = True
                logger.info("✅ 错误处理组件集成成功")
                
            except ImportError as e:
                logger.error(f"❌ 错误处理组件导入失败: {e}")
                self.integration_status["error_handling"] = False
                
        except Exception as e:
            logger.error(f"❌ 错误处理集成失败: {e}")
            self.integration_status["error_handling"] = False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        total_components = len(self.integration_status)
        successful_components = sum(1 for status in self.integration_status.values() if status)
        
        return {
            "integration_status": self.integration_status,
            "components": list(self.components.keys()),
            "success_rate": successful_components / total_components if total_components > 0 else 0,
            "fully_integrated": successful_components == total_components,
            "partially_integrated": successful_components >= total_components * 0.7,
            "functional": successful_components >= total_components * 0.5
        }
    
    def create_download_dialog(self, parent=None, **kwargs):
        """创建下载对话框"""
        try:
            if "EnhancedDownloadDialog" in self.components:
                dialog_class = self.components["EnhancedDownloadDialog"]
                return dialog_class(parent, **kwargs)
            else:
                logger.warning("⚠️ EnhancedDownloadDialog不可用，使用基础对话框")
                if "QMessageBox" in self.components:
                    return self.components["QMessageBox"](parent)
                else:
                    return None
        except Exception as e:
            logger.error(f"❌ 创建下载对话框失败: {e}")
            return None
    
    def create_progress_dialog(self, parent=None, **kwargs):
        """创建进度对话框"""
        try:
            if "QProgressDialog" in self.components:
                progress_class = self.components["QProgressDialog"]
                return progress_class(parent)
            else:
                logger.warning("⚠️ QProgressDialog不可用")
                return None
        except Exception as e:
            logger.error(f"❌ 创建进度对话框失败: {e}")
            return None
    
    def show_error_message(self, message: str, parent=None):
        """显示错误消息"""
        try:
            if "QMessageBox" in self.components:
                msg_box = self.components["QMessageBox"]
                msg_box.critical(parent, "错误", message)
            else:
                logger.error(f"UI错误: {message}")
        except Exception as e:
            logger.error(f"❌ 显示错误消息失败: {e}")

# 全局集成管理器实例
_integration_manager = None

def get_integration_manager() -> SmartDownloaderUIIntegration:
    """获取全局集成管理器实例"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = SmartDownloaderUIIntegration()
    return _integration_manager

def initialize_smart_downloader_ui(main_window=None) -> Dict[str, Any]:
    """初始化智能下载器UI集成"""
    manager = get_integration_manager()
    manager.initialize_integration(main_window)
    return manager.get_integration_status()

def test_ui_integration() -> Dict[str, Any]:
    """测试UI集成状态"""
    logger.info("🧪 开始测试UI集成状态")
    
    manager = get_integration_manager()
    
    # 如果还未初始化，先初始化
    if not any(manager.integration_status.values()):
        manager.initialize_integration()
    
    status = manager.get_integration_status()
    
    logger.info(f"📊 UI集成测试结果:")
    logger.info(f"  - 成功率: {status['success_rate']:.1%}")
    logger.info(f"  - 完全集成: {status['fully_integrated']}")
    logger.info(f"  - 部分集成: {status['partially_integrated']}")
    logger.info(f"  - 功能可用: {status['functional']}")
    
    for component, integrated in status['integration_status'].items():
        status_icon = "✅" if integrated else "❌"
        logger.info(f"  - {component}: {status_icon}")
    
    return status

if __name__ == "__main__":
    # 独立测试
    test_result = test_ui_integration()
    print(f"UI集成测试完成，成功率: {test_result['success_rate']:.1%}")
