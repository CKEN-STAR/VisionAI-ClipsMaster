#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 主窗口组件
基于simple_ui_fixed.py的架构创建标准化的主窗口组件
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit,
    QProgressBar, QSplitter, QFrame, QApplication,
    QMenuBar, QStatusBar, QToolBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction

# 导入优化模块
try:
    from .utils.startup_optimizer import get_startup_optimizer
    from .utils.thread_safety import get_thread_safety_manager, run_in_main_thread
    from .utils.memory_monitor import get_memory_monitor
    OPTIMIZATION_AVAILABLE = True
    print("[OK] 性能优化模块导入成功")
except ImportError as e:
    OPTIMIZATION_AVAILABLE = False
    print(f"[WARN] 性能优化模块导入失败: {e}")
    # 定义空函数以保持兼容性
    def get_startup_optimizer(): return None
    def get_thread_safety_manager(): return None
    def get_memory_monitor(): return None
    def run_in_main_thread(func, *args, **kwargs): return func(*args, **kwargs)

class MainWindow(QMainWindow):
    """VisionAI-ClipsMaster 主窗口"""
    
    # 信号定义
    window_closed = pyqtSignal()
    status_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 窗口基本设置
        self.setWindowTitle("VisionAI-ClipsMaster - AI驱动的短剧混剪工具")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 初始化性能优化
        self._init_optimization()

        # 设置窗口图标
        self._set_window_icon()

        # 初始化UI组件
        self._init_ui()

        # 初始化菜单和工具栏
        self._init_menu_bar()
        self._init_tool_bar()
        self._init_status_bar()

        # 应用样式
        self._apply_styles()

        # 初始化信号连接
        self._init_signals()

        # 启动内存监控
        self._start_memory_monitoring()

        print("[OK] 主窗口初始化完成")

    def _init_optimization(self):
        """初始化性能优化"""
        if not OPTIMIZATION_AVAILABLE:
            print("[WARN] 性能优化不可用，跳过初始化")
            return

        try:
            # 获取启动优化器
            self.startup_optimizer = get_startup_optimizer()

            # 获取线程安全管理器
            self.thread_safety_manager = get_thread_safety_manager()

            # 获取内存监控器
            self.memory_monitor = get_memory_monitor()

            # 启动优化
            self.startup_optimizer.start_optimization()

            # 连接信号
            self.startup_optimizer.startup_progress.connect(self._on_startup_progress)
            self.startup_optimizer.startup_complete.connect(self._on_startup_complete)

            print("[OK] 性能优化初始化完成")

        except Exception as e:
            print(f"[WARN] 性能优化初始化失败: {e}")

    def _start_memory_monitoring(self):
        """启动内存监控"""
        if not OPTIMIZATION_AVAILABLE:
            return

        try:
            # 启动内存监控
            self.memory_monitor.start_monitoring()

            # 连接内存监控信号
            self.memory_monitor.memory_warning.connect(self._on_memory_warning)
            self.memory_monitor.memory_critical.connect(self._on_memory_critical)
            self.memory_monitor.memory_optimized.connect(self._on_memory_optimized)

            # 定时更新内存使用显示
            self.memory_update_timer = QTimer()
            self.memory_update_timer.timeout.connect(self._update_memory_display)
            self.memory_update_timer.start(2000)  # 2秒更新一次

            print("[OK] 内存监控已启动")

        except Exception as e:
            print(f"[WARN] 内存监控启动失败: {e}")

    def _on_startup_progress(self, progress, message):
        """启动进度回调"""
        # 使用线程安全的方式更新UI
        if OPTIMIZATION_AVAILABLE:
            run_in_main_thread(self._update_startup_progress, progress, message)
        else:
            self._update_startup_progress(progress, message)

    def _update_startup_progress(self, progress, message):
        """更新启动进度"""
        # 更新状态栏
        self.statusBar().showMessage(f"启动中: {message} ({progress}%)")

    def _on_startup_complete(self):
        """启动完成回调"""
        if OPTIMIZATION_AVAILABLE:
            run_in_main_thread(self._handle_startup_complete)
        else:
            self._handle_startup_complete()

    def _handle_startup_complete(self):
        """处理启动完成"""
        # 更新状态栏
        self.statusBar().showMessage("启动完成")

        # 获取启动统计信息
        if hasattr(self, 'startup_optimizer'):
            stats = self.startup_optimizer.get_optimization_stats()
            if 'elapsed_time' in stats:
                print(f"[INFO] 启动耗时: {stats['elapsed_time']:.2f}秒")

    def _on_memory_warning(self, memory_mb):
        """内存警告回调"""
        if OPTIMIZATION_AVAILABLE:
            run_in_main_thread(self._handle_memory_warning, memory_mb)
        else:
            self._handle_memory_warning(memory_mb)

    def _handle_memory_warning(self, memory_mb):
        """处理内存警告"""
        self.statusBar().showMessage(f"内存警告: {memory_mb:.1f}MB")

        # 更新内存显示
        if hasattr(self, 'memory_usage'):
            self._apply_safe_style(self.memory_usage, "color: #ffc107; padding: 5px;")

    def _on_memory_critical(self, memory_mb):
        """内存危险回调"""
        if OPTIMIZATION_AVAILABLE:
            run_in_main_thread(self._handle_memory_critical, memory_mb)
        else:
            self._handle_memory_critical(memory_mb)

    def _handle_memory_critical(self, memory_mb):
        """处理内存危险"""
        self.statusBar().showMessage(f"内存危险: {memory_mb:.1f}MB")

        # 更新内存显示
        if hasattr(self, 'memory_usage'):
            self._apply_safe_style(self.memory_usage, "color: #dc3545; padding: 5px;")

    def _on_memory_optimized(self, memory_mb):
        """内存优化完成回调"""
        if OPTIMIZATION_AVAILABLE:
            run_in_main_thread(self._handle_memory_optimized, memory_mb)
        else:
            self._handle_memory_optimized(memory_mb)

    def _handle_memory_optimized(self, memory_mb):
        """处理内存优化完成"""
        self.statusBar().showMessage(f"内存优化完成: {memory_mb:.1f}MB")

        # 更新内存显示
        if hasattr(self, 'memory_usage'):
            self._apply_safe_style(self.memory_usage, "color: #28a745; padding: 5px;")

    def _update_memory_display(self):
        """更新内存使用显示"""
        if not OPTIMIZATION_AVAILABLE or not hasattr(self, 'memory_monitor'):
            return

        try:
            stats = self.memory_monitor.get_memory_stats()
            memory_mb = stats['current_memory_mb']
            usage_ratio = stats['usage_ratio']

            # 更新内存标签
            if hasattr(self, 'memory_usage'):
                self.memory_usage.setText(f"内存: {memory_mb:.1f}MB ({usage_ratio:.1%})")

                # 根据使用率设置颜色
                if stats['is_critical']:
                    color = "#dc3545"  # 红色
                elif stats['is_warning']:
                    color = "#ffc107"  # 黄色
                else:
                    color = "#495057"  # 正常颜色

                self._apply_safe_style(self.memory_usage, f"color: {color}; padding: 5px;")

        except Exception as e:
            print(f"[WARN] 更新内存显示失败: {e}")

    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            icon_path = Path("ui/assets/icons/app_icon.ico")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # 使用默认图标
                self.setWindowIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        except Exception as e:
            print(f"[WARN] 设置窗口图标失败: {e}")
    
    def _init_ui(self):
        """初始化用户界面"""
        try:
            # 创建中央组件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 创建主布局
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            # 创建顶部信息栏
            self._create_info_bar(main_layout)
            
            # 创建主要内容区域
            self._create_main_content(main_layout)
            
            # 创建底部状态栏
            self._create_bottom_panel(main_layout)
            
        except Exception as e:
            print(f"[ERROR] 初始化UI失败: {e}")
    
    def _create_info_bar(self, parent_layout):
        """创建顶部信息栏"""
        try:
            info_frame = QFrame()
            info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            info_frame.setMaximumHeight(80)
            
            info_layout = QHBoxLayout(info_frame)
            
            # 应用标题
            title_label = QLabel("VisionAI-ClipsMaster")
            title_label.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
            self._apply_safe_style(title_label, "color: #007bff; padding: 10px;")

            # 版本信息
            version_label = QLabel("v1.0.0")
            version_label.setFont(QFont("Microsoft YaHei UI", 10))
            self._apply_safe_style(version_label, "color: #6c757d; padding: 10px;")

            # 状态指示器
            self.status_indicator = QLabel("● 就绪")
            self.status_indicator.setFont(QFont("Microsoft YaHei UI", 10))
            self._apply_safe_style(self.status_indicator, "color: #28a745; padding: 10px;")
            
            info_layout.addWidget(title_label)
            info_layout.addStretch()
            info_layout.addWidget(version_label)
            info_layout.addWidget(self.status_indicator)
            
            parent_layout.addWidget(info_frame)
            
        except Exception as e:
            print(f"[ERROR] 创建信息栏失败: {e}")
    
    def _create_main_content(self, parent_layout):
        """创建主要内容区域"""
        try:
            # 创建分割器
            splitter = QSplitter(Qt.Orientation.Horizontal)
            
            # 创建左侧面板
            left_panel = self._create_left_panel()
            splitter.addWidget(left_panel)
            
            # 创建右侧主要工作区
            right_panel = self._create_right_panel()
            splitter.addWidget(right_panel)
            
            # 设置分割比例
            splitter.setSizes([300, 900])
            
            parent_layout.addWidget(splitter)
            
        except Exception as e:
            print(f"[ERROR] 创建主要内容失败: {e}")
    
    def _create_left_panel(self):
        """创建左侧面板"""
        try:
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            
            # 功能导航
            nav_label = QLabel("功能导航")
            nav_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
            self._apply_safe_style(nav_label, "color: #495057; padding: 5px; border-bottom: 2px solid #dee2e6;")
            
            # 导航按钮
            nav_buttons = [
                ("视频处理", self._on_video_processing),
                ("模型训练", self._on_model_training),
                ("数据管理", self._on_data_management),
                ("系统设置", self._on_system_settings),
                ("性能监控", self._on_performance_monitor),
                ("帮助文档", self._on_help_docs)
            ]
            
            left_layout.addWidget(nav_label)
            
            for button_text, callback in nav_buttons:
                btn = QPushButton(button_text)
                btn.setMinimumHeight(40)
                btn.clicked.connect(callback)
                left_layout.addWidget(btn)
            
            left_layout.addStretch()
            
            return left_widget
            
        except Exception as e:
            print(f"[ERROR] 创建左侧面板失败: {e}")
            return QWidget()
    
    def _create_right_panel(self):
        """创建右侧主要工作区"""
        try:
            # 创建标签页组件
            self.tab_widget = QTabWidget()
            
            # 添加各个功能标签页
            self._add_video_processing_tab()
            self._add_model_training_tab()
            self._add_data_management_tab()
            self._add_system_monitor_tab()
            
            return self.tab_widget
            
        except Exception as e:
            print(f"[ERROR] 创建右侧面板失败: {e}")
            return QWidget()
    
    def _add_video_processing_tab(self):
        """添加视频处理标签页"""
        try:
            video_widget = QWidget()
            video_layout = QVBoxLayout(video_widget)
            
            # 标题
            title = QLabel("AI驱动的短剧混剪")
            title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
            self._apply_safe_style(title, "color: #007bff; padding: 10px;")

            # 说明文本
            description = QLabel(
                "上传短剧视频和字幕文件，AI将自动分析剧情并生成具有爆款潜力的混剪视频。\n"
                "支持中英文双语处理，智能时间轴对齐，一键导出到剪映。"
            )
            description.setWordWrap(True)
            self._apply_safe_style(description, "color: #495057; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
            
            # 操作按钮
            buttons_layout = QHBoxLayout()
            
            upload_btn = QPushButton("上传视频文件")
            upload_btn.setMinimumHeight(40)
            upload_btn.clicked.connect(self._on_upload_video)
            
            process_btn = QPushButton("开始AI处理")
            process_btn.setMinimumHeight(40)
            process_btn.clicked.connect(self._on_start_processing)
            
            export_btn = QPushButton("导出到剪映")
            export_btn.setMinimumHeight(40)
            export_btn.clicked.connect(self._on_export_video)
            
            buttons_layout.addWidget(upload_btn)
            buttons_layout.addWidget(process_btn)
            buttons_layout.addWidget(export_btn)
            
            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            
            # 日志输出
            self.log_output = QTextEdit()
            self.log_output.setMaximumHeight(200)
            self.log_output.setPlaceholderText("处理日志将在这里显示...")
            
            video_layout.addWidget(title)
            video_layout.addWidget(description)
            video_layout.addLayout(buttons_layout)
            video_layout.addWidget(self.progress_bar)
            video_layout.addWidget(self.log_output)
            video_layout.addStretch()
            
            self.tab_widget.addTab(video_widget, "视频处理")
            
        except Exception as e:
            print(f"[ERROR] 添加视频处理标签页失败: {e}")
    
    def _add_model_training_tab(self):
        """添加模型训练标签页"""
        try:
            training_widget = QWidget()
            training_layout = QVBoxLayout(training_widget)

            title = QLabel("模型训练与微调")
            title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
            self._apply_safe_style(title, "color: #007bff; padding: 10px;")

            description = QLabel(
                "使用自定义数据训练AI模型，提升字幕重构质量。\n"
                "支持LoRA微调、数据增强、质量评估等功能。"
            )
            description.setWordWrap(True)
            self._apply_safe_style(description, "color: #495057; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")

            training_layout.addWidget(title)
            training_layout.addWidget(description)
            training_layout.addStretch()

            self.tab_widget.addTab(training_widget, "模型训练")

        except Exception as e:
            print(f"[ERROR] 添加模型训练标签页失败: {e}")
    
    def _add_data_management_tab(self):
        """添加数据管理标签页"""
        try:
            data_widget = QWidget()
            data_layout = QVBoxLayout(data_widget)
            
            title = QLabel("数据管理")
            title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
            self._apply_safe_style(title, "color: #007bff; padding: 10px;")

            description = QLabel(
                "管理训练数据、导出数据集、查看数据统计。\n"
                "支持多种格式导出，数据质量评估和清洗。"
            )
            description.setWordWrap(True)
            self._apply_safe_style(description, "color: #495057; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
            
            data_layout.addWidget(title)
            data_layout.addWidget(description)
            data_layout.addStretch()
            
            self.tab_widget.addTab(data_widget, "数据管理")
            
        except Exception as e:
            print(f"[ERROR] 添加数据管理标签页失败: {e}")
    
    def _add_system_monitor_tab(self):
        """添加系统监控标签页"""
        try:
            monitor_widget = QWidget()
            monitor_layout = QVBoxLayout(monitor_widget)
            
            title = QLabel("系统监控")
            title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
            self._apply_safe_style(title, "color: #007bff; padding: 10px;")

            description = QLabel(
                "实时监控系统性能、内存使用、处理进度。\n"
                "优化系统配置，确保最佳运行效果。"
            )
            description.setWordWrap(True)
            self._apply_safe_style(description, "color: #495057; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
            
            monitor_layout.addWidget(title)
            monitor_layout.addWidget(description)
            monitor_layout.addStretch()
            
            self.tab_widget.addTab(monitor_widget, "系统监控")
            
        except Exception as e:
            print(f"[ERROR] 添加系统监控标签页失败: {e}")
    
    def _create_bottom_panel(self, parent_layout):
        """创建底部面板"""
        try:
            bottom_frame = QFrame()
            bottom_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            bottom_frame.setMaximumHeight(60)
            
            bottom_layout = QHBoxLayout(bottom_frame)
            
            # 系统状态
            self.system_status = QLabel("系统就绪")
            self._apply_safe_style(self.system_status, "color: #28a745; padding: 5px;")

            # 内存使用
            self.memory_usage = QLabel("内存: 0MB")
            self._apply_safe_style(self.memory_usage, "color: #495057; padding: 5px;")

            # CPU使用
            self.cpu_usage = QLabel("CPU: 0%")
            self._apply_safe_style(self.cpu_usage, "color: #495057; padding: 5px;")
            
            bottom_layout.addWidget(self.system_status)
            bottom_layout.addStretch()
            bottom_layout.addWidget(self.memory_usage)
            bottom_layout.addWidget(self.cpu_usage)
            
            parent_layout.addWidget(bottom_frame)
            
        except Exception as e:
            print(f"[ERROR] 创建底部面板失败: {e}")
    
    def _init_menu_bar(self):
        """初始化菜单栏"""
        try:
            menubar = self.menuBar()
            
            # 文件菜单
            file_menu = menubar.addMenu('文件(&F)')
            
            open_action = QAction('打开项目(&O)', self)
            open_action.setShortcut('Ctrl+O')
            open_action.triggered.connect(self._on_open_project)
            file_menu.addAction(open_action)
            
            save_action = QAction('保存项目(&S)', self)
            save_action.setShortcut('Ctrl+S')
            save_action.triggered.connect(self._on_save_project)
            file_menu.addAction(save_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction('退出(&X)', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # 工具菜单
            tools_menu = menubar.addMenu('工具(&T)')
            
            settings_action = QAction('设置(&S)', self)
            settings_action.triggered.connect(self._on_system_settings)
            tools_menu.addAction(settings_action)
            
            # 帮助菜单
            help_menu = menubar.addMenu('帮助(&H)')
            
            about_action = QAction('关于(&A)', self)
            about_action.triggered.connect(self._on_about)
            help_menu.addAction(about_action)
            
        except Exception as e:
            print(f"[ERROR] 初始化菜单栏失败: {e}")
    
    def _init_tool_bar(self):
        """初始化工具栏"""
        try:
            toolbar = self.addToolBar('主工具栏')
            
            # 添加常用操作按钮
            open_action = QAction('打开', self)
            open_action.triggered.connect(self._on_upload_video)
            toolbar.addAction(open_action)
            
            process_action = QAction('处理', self)
            process_action.triggered.connect(self._on_start_processing)
            toolbar.addAction(process_action)
            
            toolbar.addSeparator()
            
            settings_action = QAction('设置', self)
            settings_action.triggered.connect(self._on_system_settings)
            toolbar.addAction(settings_action)
            
        except Exception as e:
            print(f"[ERROR] 初始化工具栏失败: {e}")
    
    def _init_status_bar(self):
        """初始化状态栏"""
        try:
            self.statusBar().showMessage("VisionAI-ClipsMaster 已就绪")
            
        except Exception as e:
            print(f"[ERROR] 初始化状态栏失败: {e}")
    
    def _apply_styles(self):
        """应用样式 - 使用统一样式管理器"""
        try:
            # 导入样式管理器
            from .utils.style_manager import get_style_manager

            # 获取样式管理器实例
            style_manager = get_style_manager()

            # 应用样式到当前窗口
            success = style_manager.apply_style_to_widget(self)

            if success:
                print("[OK] 样式应用成功")
            else:
                print("[WARN] 样式应用失败，使用回退样式")
                self._apply_fallback_style()

        except ImportError as e:
            print(f"[WARN] 样式管理器不可用: {e}")
            self._apply_fallback_style()
        except Exception as e:
            print(f"[ERROR] 应用样式失败: {e}")
            self._apply_fallback_style()

    def _apply_fallback_style(self):
        """应用回退样式"""
        try:
            # 简单的回退样式，确保PyQt6兼容
            fallback_style = """
            QMainWindow {
                background-color: #ffffff;
                color: #333333;
                font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC";
                font-size: 13px;
            }

            QPushButton {
                background-color: #007bff;
                color: white;
                border: 1px solid #007bff;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                min-height: 32px;
            }

            QPushButton:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }

            QPushButton:pressed {
                background-color: #004085;
                border-color: #004085;
            }

            QTabWidget::pane {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }

            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 6px 6px 0px 0px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #495057;
                min-width: 80px;
            }

            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
                border-color: #0056b3;
            }

            QTabBar::tab:hover {
                background-color: #e9ecef;
                color: #007bff;
            }

            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px 12px;
                color: #495057;
            }

            QLineEdit:focus {
                border-color: #007bff;
            }

            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                color: #495057;
            }

            QProgressBar {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                color: #495057;
                min-height: 20px;
            }

            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 4px;
            }
            """

            self.setStyleSheet(fallback_style)
            print("[OK] 回退样式应用成功")

        except Exception as e:
            print(f"[ERROR] 回退样式应用失败: {e}")
            # 最后的回退 - 清空样式
            self.setStyleSheet("")

    def _apply_safe_style(self, widget, style: str):
        """安全地应用样式到组件"""
        try:
            # 导入样式管理器
            from .utils.style_manager import apply_safe_style

            # 使用安全样式应用
            success = apply_safe_style(widget, style)

            if not success:
                # 如果失败，直接应用原始样式
                widget.setStyleSheet(style)

        except ImportError:
            # 如果样式管理器不可用，直接应用
            widget.setStyleSheet(style)
        except Exception as e:
            print(f"[WARN] 样式应用失败: {e}")
            # 静默失败，不应用样式
    
    def _init_signals(self):
        """初始化信号连接"""
        try:
            # 连接内部信号
            self.status_changed.connect(self._on_status_changed)
            self.progress_updated.connect(self._on_progress_updated)
            
        except Exception as e:
            print(f"[ERROR] 初始化信号失败: {e}")
    
    # 事件处理方法
    def _on_video_processing(self):
        """视频处理按钮点击"""
        self.tab_widget.setCurrentIndex(0)
    
    def _on_model_training(self):
        """模型训练按钮点击"""
        self.tab_widget.setCurrentIndex(1)
    
    def _on_data_management(self):
        """数据管理按钮点击"""
        self.tab_widget.setCurrentIndex(2)
    
    def _on_system_settings(self):
        """系统设置按钮点击"""
        QMessageBox.information(self, "系统设置", "系统设置功能正在开发中...")
    
    def _on_performance_monitor(self):
        """性能监控按钮点击"""
        self.tab_widget.setCurrentIndex(3)
    
    def _on_help_docs(self):
        """帮助文档按钮点击"""
        QMessageBox.information(self, "帮助文档", "帮助文档功能正在开发中...")
    
    def _on_upload_video(self):
        """上传视频按钮点击"""
        QMessageBox.information(self, "上传视频", "视频上传功能正在开发中...")
    
    def _on_start_processing(self):
        """开始处理按钮点击"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        QMessageBox.information(self, "开始处理", "AI处理功能正在开发中...")
    
    def _on_export_video(self):
        """导出视频按钮点击"""
        QMessageBox.information(self, "导出视频", "视频导出功能正在开发中...")
    
    def _on_open_project(self):
        """打开项目"""
        QMessageBox.information(self, "打开项目", "项目管理功能正在开发中...")
    
    def _on_save_project(self):
        """保存项目"""
        QMessageBox.information(self, "保存项目", "项目管理功能正在开发中...")
    
    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(self, "关于 VisionAI-ClipsMaster", 
                         "VisionAI-ClipsMaster v1.0.0\n\n"
                         "AI驱动的短剧混剪工具\n"
                         "支持中英文双语处理\n"
                         "智能字幕重构和视频拼接\n\n"
                         "© 2025 VisionAI Team")
    
    def _on_status_changed(self, status):
        """状态改变处理"""
        self.statusBar().showMessage(status)
        self.system_status.setText(status)
    
    def _on_progress_updated(self, value):
        """进度更新处理"""
        self.progress_bar.setValue(value)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            reply = QMessageBox.question(self, '确认退出', 
                                       '确定要退出 VisionAI-ClipsMaster 吗？',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.window_closed.emit()
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            print(f"[ERROR] 窗口关闭事件处理失败: {e}")
            event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("VisionAI-ClipsMaster")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VisionAI Team")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

# 全局实例
_main_window = None

def get_main_window():
    """获取主窗口实例"""
    global _main_window
    if _main_window is None:
        _main_window = MainWindow()
    return _main_window

if __name__ == "__main__":
    main()
