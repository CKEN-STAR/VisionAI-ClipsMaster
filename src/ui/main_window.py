#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 主窗口
应用程序的主界面，集成所有功能模块

功能特性：
1. 统一的用户界面
2. 模块化组件集成
3. 菜单和工具栏
4. 状态栏和进度显示
"""

import sys
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTabWidget, QMenuBar, QStatusBar, QToolBar,
                                QAction, QLabel, QProgressBar, QSplitter,
                                QApplication, QMessageBox)
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QIcon, QKeySequence
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # 创建模拟的pyqtSignal用于类定义
    class MockSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass
    pyqtSignal = MockSignal

# 获取日志记录器
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow if PYQT_AVAILABLE else object):
    """主窗口类"""

    # 信号定义
    window_closing = pyqtSignal()
    
    def __init__(self):
        """初始化主窗口"""
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for MainWindow")

        super().__init__()

        # 窗口配置
        self.setWindowTitle("VisionAI-ClipsMaster - AI短剧视频编辑工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 组件存储
        self.ui_components = {}

        # 错误恢复机制
        self.initialization_errors = []

        try:
            # 快速初始化基础UI
            self._init_ui_fast()
            self._init_menu_bar()
            self._init_tool_bar()
            self._init_status_bar()

            # 应用样式
            self._apply_styles()

            # 延迟加载重型组件
            if PYQT_AVAILABLE:
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, self._load_heavy_components)

            logger.info("主窗口快速初始化完成")

        except Exception as e:
            logger.error(f"主窗口初始化失败: {str(e)}")
            self.initialization_errors.append(str(e))
            self._show_initialization_error(str(e))
    
    def _init_ui_fast(self):
        """快速初始化用户界面（仅基础结构）"""
        # 中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板（功能选项卡）
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumWidth(400)
        splitter.addWidget(self.tab_widget)

        # 右侧面板（监控和状态）
        right_panel = QWidget()
        right_panel.setMaximumWidth(350)
        self.right_layout = QVBoxLayout(right_panel)

        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setStretchFactor(0, 3)  # 左侧占3/4
        splitter.setStretchFactor(1, 1)  # 右侧占1/4

        # 添加基础选项卡（占位符）
        self._add_placeholder_tabs()

    def _load_heavy_components(self):
        """延迟加载重型组件"""
        try:
            # 添加监控组件
            self._add_monitoring_components(self.right_layout)

            # 替换占位符选项卡为真实组件
            self._replace_placeholder_tabs()

            # 连接组件信号
            self._connect_component_signals()

            logger.info("重型组件加载完成")

        except Exception as e:
            logger.error(f"重型组件加载失败: {str(e)}")
            self.initialization_errors.append(f"重型组件加载失败: {str(e)}")

    def _add_placeholder_tabs(self):
        """添加占位符选项卡"""
        # 视频处理占位符
        video_placeholder = QWidget()
        video_layout = QVBoxLayout(video_placeholder)
        video_layout.addWidget(QLabel("视频处理功能加载中..."))
        self.tab_widget.addTab(video_placeholder, "视频处理")

        # 模型训练占位符
        training_placeholder = QWidget()
        training_layout = QVBoxLayout(training_placeholder)
        training_layout.addWidget(QLabel("模型训练功能加载中..."))
        self.tab_widget.addTab(training_placeholder, "模型训练")

        # 设置占位符
        settings_placeholder = QWidget()
        settings_layout = QVBoxLayout(settings_placeholder)
        settings_layout.addWidget(QLabel("设置功能加载中..."))
        self.tab_widget.addTab(settings_placeholder, "设置")

    def _replace_placeholder_tabs(self):
        """替换占位符选项卡为真实组件"""
        # 清除占位符
        self.tab_widget.clear()

        # 添加真实功能选项卡
        self._add_function_tabs()

    def _init_ui(self):
        """初始化用户界面"""
        # 中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板（功能选项卡）
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumWidth(400)
        splitter.addWidget(self.tab_widget)
        
        # 右侧面板（监控和状态）
        right_panel = QWidget()
        right_panel.setMaximumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        
        # 添加监控组件
        self._add_monitoring_components(right_layout)
        
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 3)  # 左侧占3/4
        splitter.setStretchFactor(1, 1)  # 右侧占1/4
        
        # 添加功能选项卡
        self._add_function_tabs()

        # 连接组件信号
        self._connect_component_signals()
    
    def _add_function_tabs(self):
        """添加功能选项卡"""
        try:
            # 视频处理选项卡
            self._add_video_processing_tab()
            
            # 模型训练选项卡
            self._add_model_training_tab()
            
            # 设置选项卡
            self._add_settings_tab()
            
        except Exception as e:
            logger.error(f"添加功能选项卡失败: {str(e)}")
    
    def _add_video_processing_tab(self):
        """添加视频处理选项卡"""
        try:
            video_widget = QWidget()
            video_layout = QVBoxLayout(video_widget)
            
            # 标题
            title_label = QLabel("视频处理")
            title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
            video_layout.addWidget(title_label)
            
            # 功能区域
            # 这里可以添加具体的视频处理组件
            placeholder_label = QLabel("视频处理功能正在开发中...")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            video_layout.addWidget(placeholder_label)
            
            video_layout.addStretch()
            
            self.tab_widget.addTab(video_widget, "视频处理")
            
        except Exception as e:
            logger.error(f"添加视频处理选项卡失败: {str(e)}")
    
    def _add_model_training_tab(self):
        """添加模型训练选项卡"""
        try:
            # 尝试导入训练面板
            from src.ui.training_panel import TrainingPanel
            
            training_panel = TrainingPanel()
            self.ui_components["training_panel"] = training_panel
            self.tab_widget.addTab(training_panel, "模型训练")
            
        except ImportError as e:
            logger.warning(f"无法导入训练面板: {str(e)}")
            # 创建占位符
            training_widget = QWidget()
            training_layout = QVBoxLayout(training_widget)
            
            title_label = QLabel("模型训练")
            title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
            training_layout.addWidget(title_label)
            
            placeholder_label = QLabel("训练面板组件未找到")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            training_layout.addWidget(placeholder_label)
            
            training_layout.addStretch()
            self.tab_widget.addTab(training_widget, "模型训练")
        
        except Exception as e:
            logger.error(f"添加模型训练选项卡失败: {str(e)}")
    
    def _add_settings_tab(self):
        """添加设置选项卡"""
        try:
            # 尝试导入设置面板
            from src.ui.settings_panel import SettingsPanel
            
            settings_panel = SettingsPanel()
            self.ui_components["settings_panel"] = settings_panel
            self.tab_widget.addTab(settings_panel, "设置")
            
        except ImportError as e:
            logger.warning(f"无法导入设置面板: {str(e)}")
            # 创建占位符
            settings_widget = QWidget()
            settings_layout = QVBoxLayout(settings_widget)
            
            title_label = QLabel("系统设置")
            title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
            settings_layout.addWidget(title_label)
            
            placeholder_label = QLabel("设置面板组件未找到")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            settings_layout.addWidget(placeholder_label)
            
            settings_layout.addStretch()
            self.tab_widget.addTab(settings_widget, "设置")
        
        except Exception as e:
            logger.error(f"添加设置选项卡失败: {str(e)}")
    
    def _add_monitoring_components(self, layout: QVBoxLayout):
        """添加监控组件"""
        try:
            # 实时图表
            from src.ui.realtime_charts import RealtimeCharts
            
            charts = RealtimeCharts()
            self.ui_components["realtime_charts"] = charts
            layout.addWidget(charts)
            
        except ImportError as e:
            logger.warning(f"无法导入实时图表: {str(e)}")
            placeholder = QLabel("实时图表组件未找到")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)
        
        try:
            # 警告管理器
            from src.ui.alert_manager import AlertManager
            
            alert_manager = AlertManager()
            self.ui_components["alert_manager"] = alert_manager
            layout.addWidget(alert_manager)
            
        except ImportError as e:
            logger.warning(f"无法导入警告管理器: {str(e)}")
            placeholder = QLabel("警告管理器组件未找到")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)
        
        except Exception as e:
            logger.error(f"添加监控组件失败: {str(e)}")

    def _connect_component_signals(self):
        """连接组件间的信号"""
        try:
            # 连接实时图表和警告管理器
            charts = self.ui_components.get("realtime_charts")
            alert_manager = self.ui_components.get("alert_manager")
            settings_panel = self.ui_components.get("settings_panel")
            training_panel = self.ui_components.get("training_panel")

            if charts and alert_manager:
                # 当性能数据更新时，检查是否需要发出警告
                charts.data_updated.connect(self._check_performance_alerts)

            if settings_panel:
                # 连接设置变更信号
                settings_panel.theme_changed.connect(self._on_theme_changed)
                settings_panel.language_changed.connect(self._on_language_changed)
                settings_panel.settings_changed.connect(self._on_settings_changed)

            if training_panel and alert_manager:
                # 连接训练状态和警告系统
                if hasattr(training_panel, 'training_status_changed'):
                    training_panel.training_status_changed.connect(self._on_training_status_changed)

            logger.info("组件信号连接完成")

        except Exception as e:
            logger.error(f"连接组件信号失败: {str(e)}")

    def _check_performance_alerts(self, performance_data: dict):
        """检查性能数据并发出警告"""
        try:
            alert_manager = self.ui_components.get("alert_manager")
            if not alert_manager:
                return

            cpu_usage = performance_data.get("cpu_usage", 0)
            memory_usage = performance_data.get("memory_usage", 0)

            # CPU使用率过高警告
            if cpu_usage > 90:
                alert_manager.show_alert(
                    alert_manager.AlertLevel.WARNING if hasattr(alert_manager, 'AlertLevel') else "warning",
                    "CPU使用率过高",
                    f"当前CPU使用率: {cpu_usage:.1f}%，建议关闭其他应用程序"
                )

            # 内存使用率过高警告
            if memory_usage > 85:
                alert_manager.show_alert(
                    alert_manager.AlertLevel.WARNING if hasattr(alert_manager, 'AlertLevel') else "warning",
                    "内存使用率过高",
                    f"当前内存使用率: {memory_usage:.1f}%，建议释放内存"
                )

        except Exception as e:
            logger.error(f"性能警告检查失败: {str(e)}")

    def _on_theme_changed(self, theme: str):
        """主题变更处理"""
        try:
            logger.info(f"主题已切换到: {theme}")
            self.set_status(f"主题已切换到: {theme}")
            # 这里可以添加主题切换的具体逻辑
        except Exception as e:
            logger.error(f"主题切换失败: {str(e)}")

    def _on_language_changed(self, language: str):
        """语言变更处理"""
        try:
            logger.info(f"语言已切换到: {language}")
            self.set_status(f"语言已切换到: {language}")
            # 这里可以添加语言切换的具体逻辑
        except Exception as e:
            logger.error(f"语言切换失败: {str(e)}")

    def _on_settings_changed(self, settings: dict):
        """设置变更处理"""
        try:
            logger.info("设置已更新")
            self.set_status("设置已保存")
            # 这里可以添加设置应用的具体逻辑
        except Exception as e:
            logger.error(f"设置应用失败: {str(e)}")

    def _on_training_status_changed(self, status: str):
        """训练状态变更处理"""
        try:
            logger.info(f"训练状态: {status}")
            self.set_status(f"训练状态: {status}")
        except Exception as e:
            logger.error(f"训练状态更新失败: {str(e)}")

    def _show_initialization_error(self, error_message: str):
        """显示初始化错误"""
        try:
            if PYQT_AVAILABLE:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "初始化警告",
                    f"部分组件初始化失败，但核心功能仍可使用:\n{error_message}"
                )
        except Exception as e:
            logger.error(f"显示错误对话框失败: {str(e)}")

    def get_initialization_status(self) -> dict:
        """获取初始化状态"""
        return {
            "success": len(self.initialization_errors) == 0,
            "errors": self.initialization_errors,
            "components_loaded": list(self.ui_components.keys()),
            "components_count": len(self.ui_components)
        }

    def retry_failed_components(self):
        """重试失败的组件初始化"""
        try:
            logger.info("重试失败组件初始化")

            # 重新尝试连接组件信号
            self._connect_component_signals()

            # 清除错误记录
            self.initialization_errors.clear()

            self.set_status("组件重新初始化完成")

        except Exception as e:
            logger.error(f"重试组件初始化失败: {str(e)}")
            self.initialization_errors.append(f"重试失败: {str(e)}")
    
    def _init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建项目
        new_action = QAction("新建项目(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # 打开项目
        open_action = QAction("打开项目(&O)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 剪映导出
        export_action = QAction("导出到剪映(&E)", self)
        export_action.triggered.connect(self._export_to_jianying)
        tools_menu.addAction(export_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_tool_bar(self):
        """初始化工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 新建项目按钮
        new_action = QAction("新建", self)
        new_action.triggered.connect(self._new_project)
        toolbar.addAction(new_action)
        
        # 打开项目按钮
        open_action = QAction("打开", self)
        open_action.triggered.connect(self._open_project)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # 导出按钮
        export_action = QAction("导出", self)
        export_action.triggered.connect(self._export_to_jianying)
        toolbar.addAction(export_action)
    
    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 内存使用标签
        self.memory_label = QLabel("内存: 0MB")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        # 启动内存监控定时器
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self._update_memory_usage)
        self.memory_timer.start(5000)  # 每5秒更新一次

        # 启动内存清理定时器
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_memory)
        self.cleanup_timer.start(60000)  # 每分钟清理一次
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-family: 'Microsoft YaHei';
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
            }
            
            QTabBar::tab:hover {
                background-color: #0056b3;
                color: white;
            }
            
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                font-family: 'Microsoft YaHei';
            }
            
            QMenuBar::item {
                padding: 4px 8px;
                background-color: transparent;
            }
            
            QMenuBar::item:selected {
                background-color: #007bff;
                color: white;
            }
            
            QToolBar {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                spacing: 3px;
                font-family: 'Microsoft YaHei';
            }
            
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                font-family: 'Microsoft YaHei';
            }
        """)
    
    def _new_project(self):
        """新建项目"""
        logger.info("新建项目")
        self.set_status("新建项目...")
        # 这里添加新建项目的逻辑
    
    def _open_project(self):
        """打开项目"""
        logger.info("打开项目")
        self.set_status("打开项目...")
        # 这里添加打开项目的逻辑
    
    def _export_to_jianying(self):
        """导出到剪映（增强版：自动启动剪映+独立视频片段）"""
        try:
            logger.info("开始导出到剪映")
            self.set_status("正在导出到剪映...")

            # 显示进度条
            self.show_progress(10)

            # 导入剪映导出器
            from src.core.jianying_exporter import JianyingExporter

            # 创建导出器
            exporter = JianyingExporter()
            self.show_progress(20)

            # 生成示例数据（实际项目中应该从当前工作流程获取）
            original_subtitles = self._get_sample_original_subtitles()
            reconstructed_subtitles = self._get_sample_reconstructed_subtitles()
            video_duration = 30.0  # 示例视频时长

            self.show_progress(40)

            # 执行导出
            result = exporter.export_complete_package(
                original_subtitles=original_subtitles,
                reconstructed_subtitles=reconstructed_subtitles,
                video_duration=video_duration,
                project_name=f"VisionAI_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            self.show_progress(80)

            # 处理导出结果
            if result.get("status") == "success":
                project_dir = result.get("project_directory")
                jianying_launched = result.get("jianying_launched", False)
                project_auto_loaded = result.get("project_auto_loaded", False)
                enhanced_features = result.get("enhanced_features", {})

                self.show_progress(100)

                # 显示成功消息
                success_message = f"🎉 导出成功！\n\n"
                success_message += f"📁 项目目录: {project_dir}\n"
                success_message += f"🎬 导出类型: 原片映射多片段\n\n"

                # 增强功能状态
                if enhanced_features.get("multiple_segments_timeline", False):
                    success_message += f"✨ 增强功能已启用:\n"
                    success_message += f"   • 原片一一映射显示\n"
                    success_message += f"   • 可拖拽边界调整\n"
                    success_message += f"   • 完整素材库导入\n"
                    success_message += f"   • 时间轴分离显示\n\n"

                # 剪映启动状态
                if jianying_launched:
                    if project_auto_loaded:
                        success_message += f"🚀 剪映程序已自动启动并加载项目文件\n"
                        success_message += f"✅ 时间轴片段与原片一一映射显示\n"
                        success_message += f"🎯 可拖拽片段边界调整时长\n"
                        success_message += f"📚 素材库包含所有原始视频文件\n"
                        success_message += f"💡 您可以直接编辑、拖拽、调整每个片段"
                    else:
                        success_message += f"🚀 剪映程序已自动启动\n"
                        success_message += f"📂 请在剪映中打开项目文件查看原片映射片段"
                else:
                    jianying_path = result.get("jianying_path")
                    if jianying_path:
                        success_message += f"⚠️ 剪映程序启动失败，请手动打开剪映\n"
                        success_message += f"📍 剪映路径: {jianying_path}\n"
                        success_message += f"📂 然后打开项目文件查看多个片段"
                    else:
                        success_message += f"ℹ️ 未检测到剪映安装，请手动打开剪映\n"
                        success_message += f"📂 导入项目文件以查看多个独立片段"

                # 显示成功对话框
                alert_manager = self.ui_components.get("alert_manager")
                if alert_manager:
                    alert_manager.show_alert(
                        "info",
                        "剪映导出成功",
                        success_message,
                        auto_dismiss=False,
                        show_dialog=True
                    )
                else:
                    # 回退到简单消息框
                    if PYQT_AVAILABLE:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(self, "导出成功", success_message)

                self.set_status("剪映导出完成")

            else:
                # 导出失败
                error_message = result.get("error", "未知错误")
                logger.error(f"剪映导出失败: {error_message}")

                alert_manager = self.ui_components.get("alert_manager")
                if alert_manager:
                    alert_manager.show_alert(
                        "error",
                        "剪映导出失败",
                        f"导出过程中发生错误:\n{error_message}",
                        auto_dismiss=False,
                        show_dialog=True
                    )
                else:
                    if PYQT_AVAILABLE:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.critical(self, "导出失败", f"导出失败: {error_message}")

                self.set_status("剪映导出失败")

        except Exception as e:
            logger.error(f"剪映导出异常: {str(e)}")

            alert_manager = self.ui_components.get("alert_manager")
            if alert_manager:
                alert_manager.show_alert(
                    "error",
                    "剪映导出异常",
                    f"导出过程中发生异常:\n{str(e)}",
                    auto_dismiss=False,
                    show_dialog=True
                )

            self.set_status("剪映导出异常")

        finally:
            # 隐藏进度条
            self.hide_progress()

    def _get_sample_original_subtitles(self) -> List[Dict[str, Any]]:
        """获取示例原始字幕（实际项目中应该从当前工作流程获取）"""
        return [
            {"start": 0.0, "end": 3.0, "text": "这是第一段原始字幕"},
            {"start": 3.5, "end": 6.5, "text": "这是第二段原始字幕"},
            {"start": 7.0, "end": 10.0, "text": "这是第三段原始字幕"},
            {"start": 10.5, "end": 13.5, "text": "这是第四段原始字幕"},
            {"start": 14.0, "end": 17.0, "text": "这是第五段原始字幕"}
        ]

    def _get_sample_reconstructed_subtitles(self) -> List[Dict[str, Any]]:
        """获取示例重构字幕（实际项目中应该从AI重构结果获取）"""
        return [
            {"start": 0.0, "end": 2.8, "text": "🔥 震撼开场！你绝对想不到的剧情"},
            {"start": 3.0, "end": 6.2, "text": "💥 高能预警！接下来的内容太精彩了"},
            {"start": 6.5, "end": 9.8, "text": "😱 不敢相信！这个转折太意外了"},
            {"start": 10.0, "end": 13.3, "text": "🎯 关键时刻！所有谜团即将揭晓"},
            {"start": 13.5, "end": 16.8, "text": "🚀 爆款结局！记得点赞关注哦"}
        ]
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = """
        VisionAI-ClipsMaster v1.0
        
        AI驱动的短剧视频编辑工具
        
        功能特性：
        • AI剧本重构
        • 双语言模型支持
        • 剪映导出
        • 实时性能监控
        
        开发团队：VisionAI
        """
        
        QMessageBox.about(self, "关于 VisionAI-ClipsMaster", about_text)
    
    def _update_memory_usage(self):
        """更新内存使用显示"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"内存: {memory_mb:.1f}MB")

            # 内存使用过高警告
            if memory_mb > 350:  # 接近400MB限制时警告
                alert_manager = self.ui_components.get("alert_manager")
                if alert_manager:
                    alert_manager.show_alert(
                        "warning",
                        "内存使用过高",
                        f"当前内存使用: {memory_mb:.1f}MB，建议清理内存",
                        auto_dismiss=True,
                        show_dialog=False
                    )

        except ImportError:
            self.memory_label.setText("内存: N/A")
        except Exception as e:
            logger.error(f"更新内存使用失败: {str(e)}")

    def _cleanup_memory(self):
        """清理内存"""
        try:
            import gc

            # 强制垃圾回收
            collected = gc.collect()

            # 清理组件缓存
            for component_name, component in self.ui_components.items():
                if hasattr(component, 'cleanup_cache'):
                    component.cleanup_cache()

            if collected > 0:
                logger.debug(f"内存清理完成，回收了 {collected} 个对象")

        except Exception as e:
            logger.error(f"内存清理失败: {str(e)}")
    
    def set_status(self, message: str):
        """设置状态栏消息"""
        self.status_label.setText(message)
        logger.info(f"状态: {message}")
    
    def show_progress(self, value: int, maximum: int = 100):
        """显示进度"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
    
    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
    
    def get_ui_component(self, name: str):
        """获取UI组件"""
        return self.ui_components.get(name)
    
    def closeEvent(self, event):
        """关闭事件处理 - 增强版"""
        try:
            self.window_closing.emit()

            # 停止所有定时器
            if hasattr(self, 'memory_timer') and self.memory_timer:
                self.memory_timer.stop()
            if hasattr(self, 'cleanup_timer') and self.cleanup_timer:
                self.cleanup_timer.stop()

            # 安全清理组件
            for component_name, component in list(self.ui_components.items()):
                try:
                    if hasattr(component, 'closeEvent'):
                        component.close()
                    elif hasattr(component, 'cleanup'):
                        component.cleanup()
                except Exception as e:
                    logger.warning(f"清理组件 {component_name} 失败: {str(e)}")

            # 清理组件字典
            self.ui_components.clear()

            # 最终内存清理
            self._cleanup_memory()

            logger.info("主窗口安全关闭")
            event.accept()

        except Exception as e:
            logger.error(f"关闭窗口时发生错误: {str(e)}")
            # 即使出错也要关闭
            event.accept()


# 便捷函数
def create_main_window() -> Optional[MainWindow]:
    """创建主窗口"""
    if not PYQT_AVAILABLE:
        logger.error("PyQt6不可用，无法创建主窗口")
        return None
    
    try:
        return MainWindow()
    except Exception as e:
        logger.error(f"创建主窗口失败: {str(e)}")
        return None
