"""
性能监控仪表板
提供实时性能监控和优化控制界面
"""

import time
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QTabWidget,
                            QProgressBar, QListWidget, QListWidgetItem,
                            QGroupBox, QCheckBox, QComboBox, QSpinBox,
                            QScrollArea, QFrame, QSplitter, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor

from .advanced_monitor import (AdvancedPerformanceMonitor, MemoryAnalysis, 
                              CPUAnalysis, PerformanceVisualizationWidget)

class PerformanceMetricWidget(QWidget):
    """性能指标显示组件"""
    
    def __init__(self, title: str, unit: str = "", color: str = "#2196F3"):
        super().__init__()
        self.title = title
        self.unit = unit
        self.color = color
        self.current_value = 0
        self.max_value = 100
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"font-weight: bold; color: {self.color};")
        layout.addWidget(self.title_label)
        
        # 数值显示
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # 单位
        if self.unit:
            self.unit_label = QLabel(self.unit)
            self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.unit_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(self.unit_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: #f0f0f0;
            }}
            QProgressBar::chunk {{
                background-color: {self.color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
    
    def update_value(self, value: float, max_value: float = None):
        """更新数值"""
        self.current_value = value
        if max_value is not None:
            self.max_value = max_value
        
        # 更新显示
        if isinstance(value, float):
            self.value_label.setText(f"{value:.1f}")
        else:
            self.value_label.setText(str(value))
        
        # 更新进度条
        progress = min(100, (value / self.max_value) * 100) if self.max_value > 0 else 0
        self.progress_bar.setValue(int(progress))
        
        # 根据数值调整颜色
        if progress > 80:
            color = "#f44336"  # 红色
        elif progress > 60:
            color = "#ff9800"  # 橙色
        else:
            color = self.color  # 原色
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: #f0f0f0;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

class PerformanceMonitorDashboard(QMainWindow):
    """性能监控仪表板"""
    
    def __init__(self):
        super().__init__()
        self.monitor = AdvancedPerformanceMonitor()
        self.visualization = PerformanceVisualizationWidget(self.monitor)
        
        self.setWindowTitle("📊 性能监控仪表板")
        self.setGeometry(300, 300, 1200, 800)
        
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
        """)
        
        self.setup_ui()
        self.setup_connections()
        
        # 启动监控
        self.monitor.start_monitoring()
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题栏
        self.setup_header(layout)
        
        # 主要内容区域
        self.setup_main_content(layout)
        
        # 控制按钮区域
        self.setup_controls(layout)
    
    def setup_header(self, layout):
        """设置标题栏"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #21CBF3);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # 标题
        title_label = QLabel("📊 性能监控仪表板")
        title_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 状态指示器
        self.status_label = QLabel("🟢 监控中")
        self.status_label.setStyleSheet("color: white; font-size: 14px;")
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header_frame)
    
    def setup_main_content(self, layout):
        """设置主要内容区域"""
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 实时监控标签页
        self.setup_realtime_tab()
        
        # 内存分析标签页
        self.setup_memory_tab()
        
        # CPU分析标签页
        self.setup_cpu_tab()
        
        # 优化建议标签页
        self.setup_optimization_tab()
        
        layout.addWidget(self.tab_widget)
    
    def setup_realtime_tab(self):
        """设置实时监控标签页"""
        realtime_widget = QWidget()
        layout = QVBoxLayout(realtime_widget)
        
        # 性能指标网格
        metrics_frame = QFrame()
        metrics_layout = QGridLayout(metrics_frame)
        
        # 创建性能指标组件
        self.memory_metric = PerformanceMetricWidget("内存使用", "MB", "#4CAF50")
        self.cpu_metric = PerformanceMetricWidget("CPU使用", "%", "#FF9800")
        self.threads_metric = PerformanceMetricWidget("线程数", "个", "#9C27B0")
        self.gc_metric = PerformanceMetricWidget("GC对象", "个", "#607D8B")
        
        metrics_layout.addWidget(self.memory_metric, 0, 0)
        metrics_layout.addWidget(self.cpu_metric, 0, 1)
        metrics_layout.addWidget(self.threads_metric, 1, 0)
        metrics_layout.addWidget(self.gc_metric, 1, 1)
        
        layout.addWidget(metrics_frame)
        
        # 实时日志
        log_group = QGroupBox("实时日志")
        log_layout = QVBoxLayout(log_group)
        
        self.realtime_log = QTextEdit()
        self.realtime_log.setMaximumHeight(200)
        self.realtime_log.setReadOnly(True)
        self.realtime_log.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.realtime_log)
        
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(realtime_widget, "📈 实时监控")
    
    def setup_memory_tab(self):
        """设置内存分析标签页"""
        memory_widget = QWidget()
        layout = QVBoxLayout(memory_widget)
        
        # 内存统计
        stats_group = QGroupBox("内存统计")
        stats_layout = QGridLayout(stats_group)
        
        self.memory_current_label = QLabel("当前: 0 MB")
        self.memory_peak_label = QLabel("峰值: 0 MB")
        self.memory_average_label = QLabel("平均: 0 MB")
        self.memory_growth_label = QLabel("增长率: 0 MB/min")
        
        stats_layout.addWidget(self.memory_current_label, 0, 0)
        stats_layout.addWidget(self.memory_peak_label, 0, 1)
        stats_layout.addWidget(self.memory_average_label, 1, 0)
        stats_layout.addWidget(self.memory_growth_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # 内存优化建议
        suggestions_group = QGroupBox("优化建议")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.memory_suggestions_list = QListWidget()
        suggestions_layout.addWidget(self.memory_suggestions_list)
        
        # 内存优化按钮
        optimize_memory_button = QPushButton("🔧 执行内存优化")
        optimize_memory_button.clicked.connect(self.optimize_memory)
        suggestions_layout.addWidget(optimize_memory_button)
        
        layout.addWidget(suggestions_group)
        
        self.tab_widget.addTab(memory_widget, "💾 内存分析")
    
    def setup_cpu_tab(self):
        """设置CPU分析标签页"""
        cpu_widget = QWidget()
        layout = QVBoxLayout(cpu_widget)
        
        # CPU统计
        stats_group = QGroupBox("CPU统计")
        stats_layout = QGridLayout(stats_group)
        
        self.cpu_current_label = QLabel("当前: 0%")
        self.cpu_average_label = QLabel("平均: 0%")
        self.cpu_peak_label = QLabel("峰值: 0%")
        self.cpu_efficiency_label = QLabel("线程效率: 0")
        
        stats_layout.addWidget(self.cpu_current_label, 0, 0)
        stats_layout.addWidget(self.cpu_average_label, 0, 1)
        stats_layout.addWidget(self.cpu_peak_label, 1, 0)
        stats_layout.addWidget(self.cpu_efficiency_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # CPU优化建议
        suggestions_group = QGroupBox("优化建议")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.cpu_suggestions_list = QListWidget()
        suggestions_layout.addWidget(self.cpu_suggestions_list)
        
        # CPU优化按钮
        optimize_cpu_button = QPushButton("⚡ 执行CPU优化")
        optimize_cpu_button.clicked.connect(self.optimize_cpu)
        suggestions_layout.addWidget(optimize_cpu_button)
        
        layout.addWidget(suggestions_group)
        
        self.tab_widget.addTab(cpu_widget, "⚡ CPU分析")
    
    def setup_optimization_tab(self):
        """设置优化建议标签页"""
        optimization_widget = QWidget()
        layout = QVBoxLayout(optimization_widget)
        
        # 综合建议
        recommendations_group = QGroupBox("综合优化建议")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_list = QListWidget()
        recommendations_layout.addWidget(self.recommendations_list)
        
        # 自动优化按钮
        auto_optimize_button = QPushButton("🚀 一键优化")
        auto_optimize_button.clicked.connect(self.auto_optimize)
        recommendations_layout.addWidget(auto_optimize_button)
        
        layout.addWidget(recommendations_group)
        
        # 优化历史
        history_group = QGroupBox("优化历史")
        history_layout = QVBoxLayout(history_group)
        
        self.optimization_history = QTextEdit()
        self.optimization_history.setReadOnly(True)
        self.optimization_history.setMaximumHeight(200)
        history_layout.addWidget(self.optimization_history)
        
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(optimization_widget, "🎯 优化建议")
    
    def setup_controls(self, layout):
        """设置控制按钮区域"""
        controls_layout = QHBoxLayout()
        
        # 监控控制
        self.start_button = QPushButton("▶️ 开始监控")
        self.start_button.clicked.connect(self.start_monitoring)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏸️ 停止监控")
        self.stop_button.clicked.connect(self.stop_monitoring)
        controls_layout.addWidget(self.stop_button)
        
        # 报告生成
        generate_report_button = QPushButton("📋 生成报告")
        generate_report_button.clicked.connect(self.generate_report)
        controls_layout.addWidget(generate_report_button)
        
        controls_layout.addStretch()
        
        # 关闭按钮
        close_button = QPushButton("❌ 关闭")
        close_button.clicked.connect(self.close)
        controls_layout.addWidget(close_button)
        
        layout.addLayout(controls_layout)
    
    def setup_connections(self):
        """设置信号连接"""
        self.monitor.performance_updated.connect(self.update_realtime_display)
        self.monitor.memory_warning.connect(self.show_memory_warning)
        self.monitor.cpu_warning.connect(self.show_cpu_warning)
    
    def update_realtime_display(self, performance_data: Dict[str, Any]):
        """更新实时显示"""
        # 更新性能指标
        self.memory_metric.update_value(performance_data.get('memory_mb', 0), 500)
        self.cpu_metric.update_value(performance_data.get('cpu_percent', 0), 100)
        self.threads_metric.update_value(performance_data.get('thread_count', 0), 50)
        self.gc_metric.update_value(performance_data.get('gc_objects', 0), 10000)
        
        # 更新实时日志
        timestamp = time.strftime("%H:%M:%S")
        memory_mb = performance_data.get('memory_mb', 0)
        cpu_percent = performance_data.get('cpu_percent', 0)
        
        log_entry = f"[{timestamp}] 内存: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%"
        self.realtime_log.append(log_entry)
        
        # 自动滚动到底部
        cursor = self.realtime_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.realtime_log.setTextCursor(cursor)
        
        # 更新分析标签页
        self.update_analysis_tabs()
    
    def update_analysis_tabs(self):
        """更新分析标签页"""
        # 更新内存分析
        memory_analysis = self.monitor.get_memory_analysis()
        self.memory_current_label.setText(f"当前: {memory_analysis.current_mb:.1f} MB")
        self.memory_peak_label.setText(f"峰值: {memory_analysis.peak_mb:.1f} MB")
        self.memory_average_label.setText(f"平均: {memory_analysis.average_mb:.1f} MB")
        self.memory_growth_label.setText(f"增长率: {memory_analysis.growth_rate:.2f} MB/min")
        
        # 更新内存建议
        self.memory_suggestions_list.clear()
        for suggestion in memory_analysis.optimization_suggestions:
            self.memory_suggestions_list.addItem(suggestion)
        
        # 更新CPU分析
        cpu_analysis = self.monitor.get_cpu_analysis()
        self.cpu_current_label.setText(f"当前: {cpu_analysis.current_percent:.1f}%")
        self.cpu_average_label.setText(f"平均: {cpu_analysis.average_percent:.1f}%")
        self.cpu_peak_label.setText(f"峰值: {cpu_analysis.peak_percent:.1f}%")
        self.cpu_efficiency_label.setText(f"线程效率: {cpu_analysis.thread_efficiency:.1f}")
        
        # 更新CPU建议
        self.cpu_suggestions_list.clear()
        for suggestion in cpu_analysis.optimization_suggestions:
            self.cpu_suggestions_list.addItem(suggestion)
        
        # 更新综合建议
        report = self.monitor.get_performance_report()
        self.recommendations_list.clear()
        for recommendation in report.get('recommendations', []):
            self.recommendations_list.addItem(recommendation)
    
    def show_memory_warning(self, message: str, value: float):
        """显示内存警告"""
        warning_text = f"⚠️ {message}: {value:.1f}MB"
        self.realtime_log.append(warning_text)
    
    def show_cpu_warning(self, message: str, value: float):
        """显示CPU警告"""
        warning_text = f"⚠️ {message}: {value:.1f}%"
        self.realtime_log.append(warning_text)
    
    def start_monitoring(self):
        """开始监控"""
        self.monitor.start_monitoring()
        self.status_label.setText("🟢 监控中")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitor.stop_monitoring()
        self.status_label.setText("🔴 已停止")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def optimize_memory(self):
        """优化内存"""
        result = self.monitor.optimize_memory()
        if result['success']:
            freed_mb = result.get('memory_freed_mb', 0)
            message = f"✅ 内存优化完成，释放了 {freed_mb:.1f}MB"
        else:
            message = f"❌ 内存优化失败: {result.get('error', '未知错误')}"
        
        self.optimization_history.append(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def optimize_cpu(self):
        """优化CPU"""
        result = self.monitor.optimize_cpu()
        if result['success']:
            improvement = result.get('cpu_improvement_percent', 0)
            message = f"✅ CPU优化完成，改善了 {improvement:.1f}%"
        else:
            message = f"❌ CPU优化失败: {result.get('error', '未知错误')}"
        
        self.optimization_history.append(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def auto_optimize(self):
        """一键优化"""
        self.optimization_history.append(f"[{time.strftime('%H:%M:%S')}] 🚀 开始一键优化...")
        
        # 执行内存优化
        memory_result = self.monitor.optimize_memory()
        if memory_result['success']:
            freed_mb = memory_result.get('memory_freed_mb', 0)
            self.optimization_history.append(f"   ✅ 内存优化: 释放 {freed_mb:.1f}MB")
        
        # 执行CPU优化
        cpu_result = self.monitor.optimize_cpu()
        if cpu_result['success']:
            improvement = cpu_result.get('cpu_improvement_percent', 0)
            self.optimization_history.append(f"   ✅ CPU优化: 改善 {improvement:.1f}%")
        
        self.optimization_history.append(f"[{time.strftime('%H:%M:%S')}] 🎉 一键优化完成")
    
    def generate_report(self):
        """生成性能报告"""
        report = self.monitor.get_performance_report()
        
        # 这里可以实现报告生成和保存功能
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"performance_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("VisionAI-ClipsMaster 性能报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"监控时长: {report.get('monitoring_duration', 0):.1f}秒\n")
                f.write(f"数据点数: {report.get('data_points', 0)}\n\n")
                
                # 内存分析
                memory_analysis = report.get('memory_analysis', {})
                f.write("内存分析:\n")
                f.write(f"  当前使用: {memory_analysis.get('current_mb', 0):.1f}MB\n")
                f.write(f"  峰值使用: {memory_analysis.get('peak_mb', 0):.1f}MB\n")
                f.write(f"  平均使用: {memory_analysis.get('average_mb', 0):.1f}MB\n")
                f.write(f"  增长率: {memory_analysis.get('growth_rate', 0):.2f}MB/min\n\n")
                
                # CPU分析
                cpu_analysis = report.get('cpu_analysis', {})
                f.write("CPU分析:\n")
                f.write(f"  当前使用: {cpu_analysis.get('current_percent', 0):.1f}%\n")
                f.write(f"  平均使用: {cpu_analysis.get('average_percent', 0):.1f}%\n")
                f.write(f"  峰值使用: {cpu_analysis.get('peak_percent', 0):.1f}%\n")
                f.write(f"  线程效率: {cpu_analysis.get('thread_efficiency', 0):.1f}\n\n")
                
                # 优化建议
                f.write("优化建议:\n")
                for recommendation in report.get('recommendations', []):
                    f.write(f"  - {recommendation}\n")
            
            self.optimization_history.append(f"[{time.strftime('%H:%M:%S')}] 📋 报告已保存: {filename}")
            
        except Exception as e:
            self.optimization_history.append(f"[{time.strftime('%H:%M:%S')}] ❌ 报告保存失败: {e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        self.monitor.stop_monitoring()
        event.accept()

__all__ = [
    'PerformanceMetricWidget',
    'PerformanceMonitorDashboard'
]
