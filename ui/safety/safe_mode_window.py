"""
增强安全模式窗口
提供诊断、修复和问题解决向导界面
"""

import os
import sys
import time
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QTabWidget,
                            QProgressBar, QListWidget, QListWidgetItem,
                            QGroupBox, QCheckBox, QComboBox, QSpinBox,
                            QScrollArea, QFrame, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor

from .enhanced_safe_mode import SystemDiagnostic, AutoRepairSystem

class DiagnosticWorker(QThread):
    """诊断工作线程"""
    
    diagnostic_completed = pyqtSignal(dict)
    progress_updated = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.diagnostic = SystemDiagnostic()
    
    def run(self):
        """运行诊断"""
        try:
            self.progress_updated.emit("开始系统诊断...", 0)
            
            # 模拟诊断进度
            checks = [
                ("检查Python环境", 10),
                ("检查依赖包", 25),
                ("检查系统资源", 40),
                ("检查文件权限", 55),
                ("检查网络连接", 70),
                ("检查GPU/CUDA", 85),
                ("检查FFmpeg", 95),
                ("生成诊断报告", 100)
            ]
            
            for check_name, progress in checks:
                self.progress_updated.emit(check_name, progress)
                time.sleep(0.5)  # 模拟检查时间
            
            # 运行实际诊断
            results = self.diagnostic.run_full_diagnostic()
            self.diagnostic_completed.emit(results)
            
        except Exception as e:
            error_result = {
                'overall': {
                    'health_score': 0,
                    'error': str(e)
                }
            }
            self.diagnostic_completed.emit(error_result)

class EnhancedSafeModeWindow(QMainWindow):
    """增强安全模式窗口"""
    
    def __init__(self):
        super().__init__()
        self.diagnostic_results = {}
        self.repair_system = AutoRepairSystem()
        self.repair_suggestions = []
        
        self.setWindowTitle("🛡️ VisionAI-ClipsMaster 安全模式")
        self.setGeometry(200, 200, 1000, 700)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.setup_ui()
        
        # 自动开始诊断
        QTimer.singleShot(1000, self.start_diagnostic)
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题区域
        self.setup_header(layout)
        
        # 主要内容区域
        self.setup_main_content(layout)
        
        # 底部按钮区域
        self.setup_footer(layout)
    
    def setup_header(self, layout):
        """设置标题区域"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:1 #ffa500);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # 标题
        title_label = QLabel("🛡️ 安全模式")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 健康度显示
        self.health_label = QLabel("系统健康度: 检测中...")
        self.health_label.setStyleSheet("color: white; font-size: 14px;")
        header_layout.addWidget(self.health_label)
        
        layout.addWidget(header_frame)
    
    def setup_main_content(self, layout):
        """设置主要内容区域"""
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 诊断标签页
        self.setup_diagnostic_tab()
        
        # 修复标签页
        self.setup_repair_tab()
        
        # 日志标签页
        self.setup_log_tab()
        
        # 设置标签页
        self.setup_settings_tab()
        
        layout.addWidget(self.tab_widget)
    
    def setup_diagnostic_tab(self):
        """设置诊断标签页"""
        diagnostic_widget = QWidget()
        layout = QVBoxLayout(diagnostic_widget)
        
        # 诊断进度
        progress_group = QGroupBox("诊断进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.diagnostic_progress = QProgressBar()
        self.diagnostic_progress.setRange(0, 100)
        progress_layout.addWidget(self.diagnostic_progress)
        
        self.diagnostic_status = QLabel("准备开始诊断...")
        progress_layout.addWidget(self.diagnostic_status)
        
        layout.addWidget(progress_group)
        
        # 诊断结果
        results_group = QGroupBox("诊断结果")
        results_layout = QVBoxLayout(results_group)
        
        self.diagnostic_results_list = QListWidget()
        results_layout.addWidget(self.diagnostic_results_list)
        
        # 重新诊断按钮
        self.rediagnose_button = QPushButton("🔄 重新诊断")
        self.rediagnose_button.clicked.connect(self.start_diagnostic)
        results_layout.addWidget(self.rediagnose_button)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(diagnostic_widget, "🔍 系统诊断")
    
    def setup_repair_tab(self):
        """设置修复标签页"""
        repair_widget = QWidget()
        layout = QVBoxLayout(repair_widget)
        
        # 修复建议
        suggestions_group = QGroupBox("修复建议")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.repair_suggestions_list = QListWidget()
        suggestions_layout.addWidget(self.repair_suggestions_list)
        
        # 修复按钮
        repair_buttons_layout = QHBoxLayout()
        
        self.auto_repair_button = QPushButton("🔧 自动修复")
        self.auto_repair_button.clicked.connect(self.start_auto_repair)
        self.auto_repair_button.setEnabled(False)
        repair_buttons_layout.addWidget(self.auto_repair_button)
        
        self.manual_repair_button = QPushButton("📖 手动修复指南")
        self.manual_repair_button.clicked.connect(self.show_manual_repair_guide)
        self.manual_repair_button.setEnabled(False)
        repair_buttons_layout.addWidget(self.manual_repair_button)
        
        repair_buttons_layout.addStretch()
        suggestions_layout.addLayout(repair_buttons_layout)
        
        layout.addWidget(suggestions_group)
        
        # 修复进度
        repair_progress_group = QGroupBox("修复进度")
        repair_progress_layout = QVBoxLayout(repair_progress_group)
        
        self.repair_progress = QProgressBar()
        repair_progress_layout.addWidget(self.repair_progress)
        
        self.repair_status = QLabel("等待开始修复...")
        repair_progress_layout.addWidget(self.repair_status)
        
        layout.addWidget(repair_progress_group)
        
        self.tab_widget.addTab(repair_widget, "🔧 自动修复")
    
    def setup_log_tab(self):
        """设置日志标签页"""
        log_widget = QWidget()
        layout = QVBoxLayout(log_widget)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 日志控制按钮
        log_buttons_layout = QHBoxLayout()
        
        clear_log_button = QPushButton("🗑️ 清空日志")
        clear_log_button.clicked.connect(self.log_text.clear)
        log_buttons_layout.addWidget(clear_log_button)
        
        save_log_button = QPushButton("💾 保存日志")
        save_log_button.clicked.connect(self.save_log)
        log_buttons_layout.addWidget(save_log_button)
        
        log_buttons_layout.addStretch()
        layout.addLayout(log_buttons_layout)
        
        self.tab_widget.addTab(log_widget, "📋 详细日志")
    
    def setup_settings_tab(self):
        """设置设置标签页"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # 安全模式设置
        safety_group = QGroupBox("安全模式设置")
        safety_layout = QVBoxLayout(safety_group)
        
        self.auto_diagnostic_checkbox = QCheckBox("启动时自动诊断")
        self.auto_diagnostic_checkbox.setChecked(True)
        safety_layout.addWidget(self.auto_diagnostic_checkbox)
        
        self.auto_repair_checkbox = QCheckBox("自动修复安全问题")
        safety_layout.addWidget(self.auto_repair_checkbox)
        
        self.detailed_logging_checkbox = QCheckBox("详细日志记录")
        self.detailed_logging_checkbox.setChecked(True)
        safety_layout.addWidget(self.detailed_logging_checkbox)
        
        layout.addWidget(safety_group)
        
        # 系统信息
        system_group = QGroupBox("系统信息")
        system_layout = QVBoxLayout(system_group)
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(200)
        system_layout.addWidget(self.system_info_text)
        
        # 显示系统信息
        self.update_system_info()
        
        layout.addWidget(system_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "⚙️ 设置")
    
    def setup_footer(self, layout):
        """设置底部按钮区域"""
        footer_layout = QHBoxLayout()
        
        # 尝试正常启动按钮
        self.try_normal_button = QPushButton("🚀 尝试正常启动")
        self.try_normal_button.clicked.connect(self.try_normal_startup)
        footer_layout.addWidget(self.try_normal_button)
        
        # 重置设置按钮
        reset_button = QPushButton("🔄 重置设置")
        reset_button.clicked.connect(self.reset_settings)
        footer_layout.addWidget(reset_button)
        
        footer_layout.addStretch()
        
        # 退出按钮
        exit_button = QPushButton("❌ 退出程序")
        exit_button.clicked.connect(self.close)
        exit_button.setStyleSheet("background-color: #f44336;")
        footer_layout.addWidget(exit_button)
        
        layout.addLayout(footer_layout)
    
    def start_diagnostic(self):
        """开始诊断"""
        self.log("开始系统诊断...")
        self.diagnostic_progress.setValue(0)
        self.diagnostic_status.setText("正在诊断...")
        self.rediagnose_button.setEnabled(False)
        
        # 启动诊断工作线程
        self.diagnostic_worker = DiagnosticWorker()
        self.diagnostic_worker.diagnostic_completed.connect(self.on_diagnostic_completed)
        self.diagnostic_worker.progress_updated.connect(self.on_diagnostic_progress)
        self.diagnostic_worker.start()
    
    def on_diagnostic_progress(self, status: str, progress: int):
        """诊断进度更新"""
        self.diagnostic_status.setText(status)
        self.diagnostic_progress.setValue(progress)
        self.log(f"[诊断] {status}")
    
    def on_diagnostic_completed(self, results: Dict[str, Any]):
        """诊断完成"""
        self.diagnostic_results = results
        self.rediagnose_button.setEnabled(True)
        
        # 更新健康度显示
        overall = results.get('overall', {})
        health_score = overall.get('health_score', 0)
        self.health_label.setText(f"系统健康度: {health_score:.1f}%")
        
        # 更新诊断结果列表
        self.update_diagnostic_results(results)
        
        # 生成修复建议
        self.generate_repair_suggestions(results)
        
        self.log(f"诊断完成，系统健康度: {health_score:.1f}%")
    
    def update_diagnostic_results(self, results: Dict[str, Any]):
        """更新诊断结果显示"""
        self.diagnostic_results_list.clear()
        
        for category, result in results.items():
            if category == 'overall':
                continue
            
            status = result.get('status', 'unknown')
            message = result.get('message', '无信息')
            
            # 创建列表项
            item = QListWidgetItem()
            
            # 设置图标和颜色
            if status == 'ok':
                icon = "✅"
                color = QColor(76, 175, 80)  # 绿色
            elif status == 'warning':
                icon = "⚠️"
                color = QColor(255, 152, 0)  # 橙色
            else:
                icon = "❌"
                color = QColor(244, 67, 54)  # 红色
            
            item.setText(f"{icon} {category}: {message}")
            item.setForeground(color)
            
            self.diagnostic_results_list.addItem(item)
    
    def generate_repair_suggestions(self, results: Dict[str, Any]):
        """生成修复建议"""
        self.repair_suggestions = self.repair_system.suggest_repairs(results)
        self.update_repair_suggestions_display()
    
    def update_repair_suggestions_display(self):
        """更新修复建议显示"""
        self.repair_suggestions_list.clear()
        
        if not self.repair_suggestions:
            item = QListWidgetItem("🎉 没有发现需要修复的问题")
            item.setForeground(QColor(76, 175, 80))
            self.repair_suggestions_list.addItem(item)
            return
        
        auto_fixable_count = 0
        
        for suggestion in self.repair_suggestions:
            priority = suggestion.get('priority', 'medium')
            title = suggestion.get('title', '')
            description = suggestion.get('description', '')
            auto_fixable = suggestion.get('auto_fixable', False)
            
            if auto_fixable:
                auto_fixable_count += 1
            
            # 设置优先级图标
            if priority == 'critical':
                icon = "🚨"
                color = QColor(244, 67, 54)
            elif priority == 'high':
                icon = "⚠️"
                color = QColor(255, 152, 0)
            else:
                icon = "ℹ️"
                color = QColor(33, 150, 243)
            
            # 添加自动修复标识
            auto_text = " [可自动修复]" if auto_fixable else " [需手动修复]"
            
            item = QListWidgetItem(f"{icon} {title}{auto_text}\n   {description}")
            item.setForeground(color)
            
            self.repair_suggestions_list.addItem(item)
        
        # 更新按钮状态
        self.auto_repair_button.setEnabled(auto_fixable_count > 0)
        self.manual_repair_button.setEnabled(len(self.repair_suggestions) > 0)
    
    def start_auto_repair(self):
        """开始自动修复"""
        self.log("开始自动修复...")
        # 这里实现自动修复逻辑
        pass
    
    def show_manual_repair_guide(self):
        """显示手动修复指南"""
        self.log("显示手动修复指南...")
        # 这里实现手动修复指南
        pass
    
    def try_normal_startup(self):
        """尝试正常启动"""
        self.log("尝试正常启动...")
        try:
            # 尝试启动主应用
            from optimized_main import main
            self.close()
            main()
        except Exception as e:
            self.log(f"正常启动失败: {e}")
    
    def reset_settings(self):
        """重置设置"""
        self.log("重置应用设置...")
        # 这里实现设置重置逻辑
        pass
    
    def update_system_info(self):
        """更新系统信息"""
        import platform
        
        info = f"""
Python版本: {sys.version}
操作系统: {platform.system()} {platform.release()}
架构: {platform.machine()}
处理器: {platform.processor()}
当前目录: {os.getcwd()}
Python路径: {sys.executable}
        """.strip()
        
        self.system_info_text.setPlainText(info)
    
    def save_log(self):
        """保存日志"""
        try:
            log_content = self.log_text.toPlainText()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"safe_mode_log_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            self.log(f"日志已保存到: {filename}")
        except Exception as e:
            self.log(f"保存日志失败: {e}")
    
    def log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

__all__ = ['EnhancedSafeModeWindow']
