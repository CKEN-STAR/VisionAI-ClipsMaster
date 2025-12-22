#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主UI集成模块

将优化的智能推荐下载器集成到主界面中，提供：
1. 菜单项集成
2. 工具栏按钮集成
3. 快捷键支持
4. 状态栏信息显示
5. 设备变化监控
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QToolBar, QStatusBar,
    QMessageBox, QWidget, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QKeySequence, QAction

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class MainUIIntegrator(QObject):
    """主UI集成器"""
    
    # 信号定义
    hardware_status_changed = pyqtSignal(str)      # 硬件状态变化
    download_progress_updated = pyqtSignal(int)    # 下载进度更新
    integration_ready = pyqtSignal()               # 集成准备就绪
    
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window
        self.integration_manager = None
        self.hardware_monitor_timer = None
        self.status_widgets = {}
        self.menu_actions = {}
        self.toolbar_actions = {}
        
        # 初始化集成
        self.initialize_integration()
    
    def initialize_integration(self):
        """初始化UI集成"""
        try:
            logger.info("🔧 开始初始化主UI集成")
            
            # 1. 初始化智能下载器集成管理器
            self._initialize_integration_manager()
            
            # 2. 集成菜单项
            self._integrate_menu_items()
            
            # 3. 集成工具栏
            self._integrate_toolbar()
            
            # 4. 集成状态栏
            self._integrate_status_bar()
            
            # 5. 设置快捷键
            self._setup_shortcuts()
            
            # 6. 启动硬件监控
            self._start_hardware_monitoring()
            
            logger.info("✅ 主UI集成完成")
            self.integration_ready.emit()
            
        except Exception as e:
            logger.error(f"❌ 主UI集成失败: {e}")
    
    def _initialize_integration_manager(self):
        """初始化集成管理器"""
        try:
            from src.ui.smart_downloader_integration_enhanced import get_integration_manager
            
            self.integration_manager = get_integration_manager()
            
            # 设置下载回调
            success = self.integration_manager.initialize(self._handle_model_download)
            
            if success:
                # 连接信号
                self.integration_manager.hardware_detected.connect(self._on_hardware_detected)
                self.integration_manager.download_started.connect(self._on_download_started)
                self.integration_manager.integration_status_changed.connect(self._on_integration_status_changed)
                
                logger.info("✅ 集成管理器初始化成功")
            else:
                logger.error("❌ 集成管理器初始化失败")
                
        except Exception as e:
            logger.error(f"❌ 集成管理器初始化异常: {e}")
            self.integration_manager = None
    
    def _integrate_menu_items(self):
        """集成菜单项"""
        try:
            # 获取或创建菜单栏
            menubar = self.main_window.menuBar()
            if not menubar:
                menubar = QMenuBar(self.main_window)
                self.main_window.setMenuBar(menubar)
            
            # 工具菜单集成已完全移除 - 用户要求移除
            # 所有菜单项(智能下载器、硬件信息)都已移除
            # 不再创建或查找工具菜单

            # # 查找或创建"工具"菜单
            # tools_menu = None
            # for action in menubar.actions():
            #     if action.text() in ["工具", "Tools", "&Tools", "&工具"]:
            #         tools_menu = action.menu()
            #         break
            #
            # if not tools_menu:
            #     tools_menu = menubar.addMenu("工具(&T)")
            #
            # # 智能下载器菜单项已移除 - 恢复UI界面到原始状态
            # # 保留后端功能，仅移除UI元素
            #
            # # 硬件信息菜单项已移除 - 用户要求移除
            # # hardware_info_action = QAction("🔧 硬件信息", self.main_window)
            # # hardware_info_action.setStatusTip("查看当前硬件配置信息")
            # # hardware_info_action.triggered.connect(self._show_hardware_info)
            # # tools_menu.addAction(hardware_info_action)
            # # self.menu_actions["hardware_info"] = hardware_info_action

            logger.info("✅ 菜单项集成完成(工具菜单已移除)")
            
        except Exception as e:
            logger.error(f"❌ 菜单项集成失败: {e}")
    
    def _integrate_toolbar(self):
        """集成工具栏"""
        try:
            # 小机器人头像按钮已移除 - 恢复UI界面到原始状态
            logger.info("✅ 工具栏集成完成（小机器人头像按钮已移除）")

        except Exception as e:
            logger.error(f"❌ 工具栏集成失败: {e}")
    
    def _integrate_status_bar(self):
        """集成状态栏"""
        try:
            # 获取或创建状态栏
            statusbar = self.main_window.statusBar()
            if not statusbar:
                statusbar = QStatusBar(self.main_window)
                self.main_window.setStatusBar(statusbar)
            
            # 硬件状态标签已移除 - 恢复UI界面到原始状态
            
            # 添加下载进度条（初始隐藏）
            download_progress = QProgressBar()
            download_progress.setVisible(False)
            download_progress.setMaximumWidth(200)
            statusbar.addPermanentWidget(download_progress)
            self.status_widgets["download_progress"] = download_progress
            
            # 连接信号
            # 硬件状态信号连接已移除 - 恢复UI界面到原始状态
            self.download_progress_updated.connect(self._update_download_progress)
            
            logger.info("✅ 状态栏集成完成")
            
        except Exception as e:
            logger.error(f"❌ 状态栏集成失败: {e}")
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        try:
            # 智能下载器快捷键已移除 - 恢复UI界面到原始状态

            # 硬件信息快捷键已移除 - 用户要求移除
            # if "hardware_info" in self.menu_actions:
            #     self.menu_actions["hardware_info"].setShortcut(QKeySequence("Ctrl+Shift+H"))

            logger.info("✅ 快捷键设置完成")

        except Exception as e:
            logger.error(f"❌ 快捷键设置失败: {e}")
    
    def _start_hardware_monitoring(self):
        """启动硬件监控"""
        try:
            # 创建硬件监控定时器
            self.hardware_monitor_timer = QTimer()
            self.hardware_monitor_timer.timeout.connect(self._check_hardware_status)
            self.hardware_monitor_timer.start(60000)  # 每分钟检查一次
            
            # 立即执行一次检查
            QTimer.singleShot(1000, self._check_hardware_status)
            
            logger.info("✅ 硬件监控启动完成")
            
        except Exception as e:
            logger.error(f"❌ 硬件监控启动失败: {e}")
    
    def _check_hardware_status(self):
        """检查硬件状态"""
        try:
            if self.integration_manager:
                hardware_info = self.integration_manager.get_hardware_info(force_refresh=False)

                # 硬件状态显示信息已移除 - 恢复UI界面到原始状态
                # 保留硬件检测后端功能，仅移除UI状态显示
                # 硬件检测逻辑继续运行，但不显示状态信息
                pass

        except Exception as e:
            logger.error(f"❌ 硬件状态检查失败: {e}")
            # 硬件状态显示信息已移除
    
    def _show_smart_downloader_menu(self):
        """显示智能下载器菜单"""
        try:
            if not self.integration_manager:
                QMessageBox.warning(
                    self.main_window,
                    "智能下载器",
                    "智能下载器集成管理器未初始化"
                )
                return
            
            # 显示模型选择对话框
            from PyQt6.QtWidgets import QInputDialog
            
            # 预定义的模型列表（Qwen3和Mistral系列）
            models = [
                "qwen3-0.6b (入门级)",
                "qwen3-1.7b (进阶级)",
                "qwen3-8b (中高级)",
                "qwen3-32b (旗舰级)",
                "mistral-7b (基础级)",
                "mistral-12b-nemo (进阶级)",
                "mistral-24b-small (中高级)",
                "mistral-large2 (旗舰级)",
                "其他..."
            ]
            
            model_name, ok = QInputDialog.getItem(
                self.main_window,
                "选择模型",
                "请选择要下载的模型:",
                models,
                0,
                False
            )
            
            if ok and model_name:
                if model_name == "其他...":
                    # 手动输入模型名称
                    model_name, ok = QInputDialog.getText(
                        self.main_window,
                        "输入模型名称",
                        "请输入模型名称:"
                    )
                else:
                    # 移除括号中的说明文字（如"qwen3-0.6b (入门级)" -> "qwen3-0.6b"）
                    model_name = model_name.split(' (')[0].strip()

                if ok and model_name:
                    # 显示智能下载器对话框
                    success = self.integration_manager.show_smart_downloader(model_name, self.main_window)
                    if success:
                        logger.info(f"✅ 智能下载器对话框完成: {model_name}")
                    else:
                        logger.info(f"ℹ️ 智能下载器对话框取消: {model_name}")
                        
        except Exception as e:
            logger.error(f"❌ 显示智能下载器失败: {e}")
            QMessageBox.critical(
                self.main_window,
                "错误",
                f"智能下载器启动失败:\n{e}"
            )
    
    def _show_hardware_info(self):
        """显示硬件信息"""
        try:
            if not self.integration_manager:
                QMessageBox.warning(
                    self.main_window,
                    "硬件信息",
                    "集成管理器未初始化"
                )
                return
            
            # 获取硬件信息
            hardware_info = self.integration_manager.get_hardware_info(force_refresh=True)
            
            if hardware_info:
                # 硬件状态显示信息已移除 - 恢复UI界面到原始状态
                # 格式化硬件信息（移除GPU相关显示）
                info_text = "🔧 当前系统配置:\n\n"
                info_text += f"系统内存: {hardware_info.get('system_ram_gb', 0):.1f} GB\n"
                info_text += f"CPU核心: {hardware_info.get('cpu_cores', 0)} 核\n"
                info_text += f"性能等级: {hardware_info.get('performance_level', 'unknown')}\n"

                QMessageBox.information(
                    self.main_window,
                    "系统信息",
                    info_text
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "硬件信息",
                    "无法获取硬件信息"
                )
                
        except Exception as e:
            logger.error(f"❌ 显示硬件信息失败: {e}")
            QMessageBox.critical(
                self.main_window,
                "错误",
                f"获取硬件信息失败:\n{e}"
            )
    
    def _handle_model_download(self, model_name: str, variant_info: Dict):
        """处理模型下载"""
        try:
            logger.info(f"📥 开始下载模型: {model_name}")
            logger.debug(f"变体信息: {variant_info}")
            
            # 显示下载进度
            self._show_download_progress(True)
            
            # 这里可以集成实际的下载逻辑
            # 目前只是模拟
            QTimer.singleShot(100, lambda: self._simulate_download_progress(model_name, variant_info))
            
        except Exception as e:
            logger.error(f"❌ 处理模型下载失败: {e}")
    
    def _simulate_download_progress(self, model_name: str, variant_info: Dict):
        """模拟下载进度"""
        # 这是一个简单的模拟，实际应该连接到真实的下载器
        progress = 0
        
        def update_progress():
            nonlocal progress
            progress += 10
            self.download_progress_updated.emit(progress)
            
            if progress >= 100:
                self._show_download_progress(False)
                QMessageBox.information(
                    self.main_window,
                    "下载完成",
                    f"模型 {model_name} 下载完成！"
                )
            else:
                QTimer.singleShot(500, update_progress)
        
        update_progress()
    
    def _show_download_progress(self, show: bool):
        """显示/隐藏下载进度"""
        if "download_progress" in self.status_widgets:
            progress_bar = self.status_widgets["download_progress"]
            progress_bar.setVisible(show)
            if show:
                progress_bar.setValue(0)
    
    def _update_download_progress(self, progress: int):
        """更新下载进度"""
        if "download_progress" in self.status_widgets:
            self.status_widgets["download_progress"].setValue(progress)
    
    def _on_hardware_detected(self, hardware_info: Dict):
        """硬件检测完成回调"""
        logger.info("✅ 硬件检测完成")
        self._check_hardware_status()
    
    def _on_download_started(self, model_name: str, variant_info: Dict):
        """下载开始回调"""
        logger.info(f"📥 下载开始: {model_name}")
    
    def _on_integration_status_changed(self, status: str):
        """集成状态变化回调"""
        logger.info(f"🔄 集成状态: {status}")


def integrate_smart_downloader_to_main_ui(main_window: QMainWindow) -> MainUIIntegrator:
    """将智能下载器集成到主UI
    
    Args:
        main_window: 主窗口
        
    Returns:
        MainUIIntegrator: 集成器实例
    """
    try:
        integrator = MainUIIntegrator(main_window)
        logger.info("✅ 智能下载器主UI集成完成")
        return integrator
    except Exception as e:
        logger.error(f"❌ 智能下载器主UI集成失败: {e}")
        raise


if __name__ == "__main__":
    # 测试代码
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建测试主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("主UI集成测试")
    main_window.resize(800, 600)
    
    # 集成智能下载器
    integrator = integrate_smart_downloader_to_main_ui(main_window)
    
    main_window.show()
    sys.exit(app.exec())
