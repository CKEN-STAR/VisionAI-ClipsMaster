#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster UI组件工厂
提供统一的UI组件创建和管理接口
"""

import logging
from typing import Dict, Optional, Any, Type
from PyQt6.QtWidgets import QWidget, QDialog, QProgressDialog, QMessageBox
from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)

class UIComponentFactory:
    """UI组件工厂类"""
    
    def __init__(self):
        self._component_registry = {}
        self._instances = {}
        self._initialization_status = {}
        
        # 注册基础组件
        self._register_base_components()
    
    def _register_base_components(self):
        """注册基础UI组件"""
        try:
            # 注册PyQt6基础组件
            from PyQt6.QtWidgets import (
                QMainWindow, QDialog, QWidget, QProgressDialog, 
                QProgressBar, QMessageBox, QLabel, QPushButton
            )
            
            self._component_registry.update({
                'QMainWindow': QMainWindow,
                'QDialog': QDialog,
                'QWidget': QWidget,
                'QProgressDialog': QProgressDialog,
                'QProgressBar': QProgressBar,
                'QMessageBox': QMessageBox,
                'QLabel': QLabel,
                'QPushButton': QPushButton
            })
            
            logger.info("✅ 基础UI组件注册成功")
            
        except ImportError as e:
            logger.error(f"❌ 基础UI组件注册失败: {e}")
    
    def register_component(self, name: str, component_class: Type, force: bool = False):
        """注册UI组件"""
        if name in self._component_registry and not force:
            logger.warning(f"⚠️ 组件 {name} 已存在，跳过注册")
            return False
        
        try:
            self._component_registry[name] = component_class
            self._initialization_status[name] = True
            logger.info(f"✅ 组件 {name} 注册成功")
            return True
        except Exception as e:
            logger.error(f"❌ 组件 {name} 注册失败: {e}")
            self._initialization_status[name] = False
            return False
    
    def create_component(self, name: str, parent=None, **kwargs) -> Optional[QWidget]:
        """创建UI组件实例"""
        if name not in self._component_registry:
            logger.error(f"❌ 未找到组件: {name}")
            return None

        try:
            # 检查是否有QApplication实例
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()

            if app is None and name.startswith('Q'):
                # 没有QApplication且是Qt组件，不能创建实例
                logger.warning(f"⚠️ 没有QApplication实例，无法创建 {name} 实例")
                return None

            component_class = self._component_registry[name]

            # 创建实例
            if parent is not None:
                instance = component_class(parent, **kwargs)
            else:
                instance = component_class(**kwargs)

            # 缓存实例
            instance_key = f"{name}_{id(instance)}"
            self._instances[instance_key] = instance

            logger.info(f"✅ 组件 {name} 创建成功")
            return instance

        except Exception as e:
            logger.error(f"❌ 组件 {name} 创建失败: {e}")
            return None
    
    def get_component_class(self, name: str) -> Optional[Type]:
        """获取组件类"""
        return self._component_registry.get(name)
    
    def is_component_available(self, name: str) -> bool:
        """检查组件是否可用"""
        return name in self._component_registry and self._initialization_status.get(name, False)
    
    def get_available_components(self) -> Dict[str, bool]:
        """获取所有可用组件"""
        return {
            name: self.is_component_available(name) 
            for name in self._component_registry.keys()
        }
    
    def initialize_smart_downloader_components(self) -> Dict[str, bool]:
        """初始化智能下载器相关组件"""
        logger.info("🔧 初始化智能下载器UI组件")
        
        results = {}
        
        # 1. 注册MainWindow
        try:
            from src.ui.main_window import MainWindow
            results['MainWindow'] = self.register_component('MainWindow', MainWindow, force=True)
        except ImportError as e:
            logger.warning(f"⚠️ MainWindow导入失败: {e}")
            results['MainWindow'] = False
        
        # 2. 注册EnhancedDownloadDialog
        try:
            from src.ui.enhanced_download_dialog import EnhancedDownloadDialog
            results['EnhancedDownloadDialog'] = self.register_component('EnhancedDownloadDialog', EnhancedDownloadDialog, force=True)
        except ImportError as e:
            logger.warning(f"⚠️ EnhancedDownloadDialog导入失败: {e}")
            results['EnhancedDownloadDialog'] = False
        
        # 3. 注册ProgressDashboard
        try:
            from src.ui.progress_dashboard import ProgressDashboard
            results['ProgressDashboard'] = self.register_component('ProgressDashboard', ProgressDashboard, force=True)
        except ImportError as e:
            logger.warning(f"⚠️ ProgressDashboard导入失败: {e}")
            results['ProgressDashboard'] = False
        
        # 4. 注册TrainingPanel
        try:
            from src.ui.training_panel import TrainingPanel
            results['TrainingPanel'] = self.register_component('TrainingPanel', TrainingPanel, force=True)
        except ImportError as e:
            logger.warning(f"⚠️ TrainingPanel导入失败: {e}")
            results['TrainingPanel'] = False
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"📊 智能下载器组件初始化完成: {success_count}/{total_count}")
        
        return results
    
    def create_progress_dialog(self, parent=None, title="下载进度", **kwargs) -> Optional[QProgressDialog]:
        """创建进度对话框"""
        try:
            progress_dialog = self.create_component('QProgressDialog', parent, **kwargs)
            if progress_dialog:
                progress_dialog.setWindowTitle(title)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setAutoClose(True)
                progress_dialog.setAutoReset(True)
            return progress_dialog
        except Exception as e:
            logger.error(f"❌ 创建进度对话框失败: {e}")
            return None
    
    def create_recommendation_dialog(self, parent=None, **kwargs) -> Optional[QDialog]:
        """创建推荐对话框"""
        try:
            if self.is_component_available('EnhancedDownloadDialog'):
                return self.create_component('EnhancedDownloadDialog', parent, **kwargs)
            else:
                # 回退到基础对话框
                dialog = self.create_component('QDialog', parent)
                if dialog:
                    dialog.setWindowTitle("模型推荐")
                    dialog.resize(600, 400)
                return dialog
        except Exception as e:
            logger.error(f"❌ 创建推荐对话框失败: {e}")
            return None
    
    def show_error_message(self, message: str, title: str = "错误", parent=None):
        """显示错误消息"""
        try:
            if self.is_component_available('QMessageBox'):
                msg_box_class = self.get_component_class('QMessageBox')
                msg_box_class.critical(parent, title, message)
            else:
                logger.error(f"UI错误 - {title}: {message}")
        except Exception as e:
            logger.error(f"❌ 显示错误消息失败: {e}")
    
    def show_info_message(self, message: str, title: str = "信息", parent=None):
        """显示信息消息"""
        try:
            if self.is_component_available('QMessageBox'):
                msg_box_class = self.get_component_class('QMessageBox')
                msg_box_class.information(parent, title, message)
            else:
                logger.info(f"UI信息 - {title}: {message}")
        except Exception as e:
            logger.error(f"❌ 显示信息消息失败: {e}")
    
    def cleanup_instances(self):
        """清理组件实例"""
        try:
            for instance_key, instance in self._instances.items():
                if hasattr(instance, 'close'):
                    instance.close()
                if hasattr(instance, 'deleteLater'):
                    instance.deleteLater()
            
            self._instances.clear()
            logger.info("✅ UI组件实例清理完成")
            
        except Exception as e:
            logger.error(f"❌ UI组件清理失败: {e}")
    
    def get_factory_status(self) -> Dict[str, Any]:
        """获取工厂状态"""
        available_components = self.get_available_components()

        # 分别统计智能下载器组件和基础组件
        smart_downloader_components = [
            'MainWindow', 'EnhancedDownloadDialog', 'ProgressDashboard', 'TrainingPanel'
        ]

        smart_components_available = sum(
            1 for name in smart_downloader_components
            if available_components.get(name, False)
        )
        smart_components_total = len(smart_downloader_components)

        total_components = len(self._component_registry)
        available_count = sum(1 for available in available_components.values() if available)

        # 检查是否有QApplication实例
        has_qapp = False
        try:
            from PyQt6.QtWidgets import QApplication
            has_qapp = QApplication.instance() is not None
        except:
            pass

        # 如果没有QApplication，主要关注智能下载器组件的可用性
        if not has_qapp:
            primary_availability_rate = smart_components_available / smart_components_total if smart_components_total > 0 else 0
            fully_functional = smart_components_available >= smart_components_total * 0.8
        else:
            primary_availability_rate = available_count / total_components if total_components > 0 else 0
            fully_functional = available_count >= total_components * 0.8

        return {
            "total_components": total_components,
            "available_components": available_count,
            "availability_rate": available_count / total_components if total_components > 0 else 0,
            "smart_downloader_availability_rate": smart_components_available / smart_components_total if smart_components_total > 0 else 0,
            "primary_availability_rate": primary_availability_rate,
            "component_status": available_components,
            "smart_downloader_status": {
                name: available_components.get(name, False)
                for name in smart_downloader_components
            },
            "active_instances": len(self._instances),
            "fully_functional": fully_functional,
            "has_qapplication": has_qapp,
            "smart_components_available": smart_components_available,
            "smart_components_total": smart_components_total
        }

# 全局工厂实例
_component_factory = None

def get_component_factory() -> UIComponentFactory:
    """获取全局组件工厂实例"""
    global _component_factory
    if _component_factory is None:
        _component_factory = UIComponentFactory()
    return _component_factory

def initialize_ui_components() -> Dict[str, bool]:
    """初始化UI组件"""
    factory = get_component_factory()
    return factory.initialize_smart_downloader_components()

def test_component_factory() -> Dict[str, Any]:
    """测试组件工厂"""
    logger.info("🧪 开始测试UI组件工厂")
    
    factory = get_component_factory()
    
    # 初始化组件
    init_results = factory.initialize_smart_downloader_components()
    
    # 获取状态
    status = factory.get_factory_status()
    
    logger.info(f"📊 组件工厂测试结果:")
    logger.info(f"  - 总组件数: {status['total_components']}")
    logger.info(f"  - 可用组件数: {status['available_components']}")
    logger.info(f"  - 可用率: {status['availability_rate']:.1%}")
    logger.info(f"  - 完全功能: {status['fully_functional']}")
    
    return {
        "initialization_results": init_results,
        "factory_status": status
    }

if __name__ == "__main__":
    # 独立测试
    test_result = test_component_factory()
    print(f"组件工厂测试完成，可用率: {test_result['factory_status']['availability_rate']:.1%}")
