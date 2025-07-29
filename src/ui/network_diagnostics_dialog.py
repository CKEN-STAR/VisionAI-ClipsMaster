#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络诊断对话框 - VisionAI-ClipsMaster
提供网络状态检测、下载源选择等功能
"""

import asyncio
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QProgressBar, QTextEdit, QComboBox, QFrame,
    QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QApplication, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.network_connectivity_checker import NetworkConnectivityChecker, NetworkStatus
    from src.core.intelligent_download_manager import IntelligentDownloadManager
    HAS_NETWORK_TOOLS = True
except ImportError as e:
    HAS_NETWORK_TOOLS = False
    print(f"网络工具导入失败: {e}")

logger = logging.getLogger(__name__)

class NetworkDiagnosticsWorker(QThread):
    """网络诊断工作线程"""
    
    diagnostics_completed = pyqtSignal(object)  # 诊断完成信号
    progress_updated = pyqtSignal(int, str)  # 进度更新信号
    
    def __init__(self):
        super().__init__()
        self.checker = None
        self.manager = None
    
    def run(self):
        """执行网络诊断"""
        try:
            if not HAS_NETWORK_TOOLS:
                self.diagnostics_completed.emit(None)
                return
            
            self.progress_updated.emit(10, "初始化网络检测器...")
            self.checker = NetworkConnectivityChecker()
            self.manager = IntelligentDownloadManager()
            
            self.progress_updated.emit(30, "检查基本网络连通性...")
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                self.progress_updated.emit(50, "执行综合网络诊断...")
                diagnostics = loop.run_until_complete(self.checker.comprehensive_network_diagnosis())
                
                self.progress_updated.emit(70, "检查下载源状态...")
                source_status = loop.run_until_complete(self.manager.check_all_sources())
                
                self.progress_updated.emit(90, "生成诊断报告...")
                
                # 合并结果
                result = {
                    'network_diagnostics': diagnostics,
                    'source_status': source_status,
                    'manager_diagnostics': self.manager.get_network_diagnostics()
                }
                
                self.progress_updated.emit(100, "诊断完成")
                self.diagnostics_completed.emit(result)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"网络诊断失败: {e}")
            self.diagnostics_completed.emit(None)
        finally:
            # 清理资源
            if self.checker:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.checker.close())
                    loop.close()
                except:
                    pass
            if self.manager:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.manager.close())
                    loop.close()
                except:
                    pass

class NetworkDiagnosticsDialog(QDialog):
    """网络诊断对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.diagnostics_worker = None
        self.current_diagnostics = None
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("网络诊断工具")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("网络连通性诊断")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 诊断页面
        self.create_diagnostics_tab()
        
        # 下载源状态页面
        self.create_sources_tab()
        
        # 建议页面
        self.create_recommendations_tab()
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_diagnosis_btn = QPushButton("开始诊断")
        self.start_diagnosis_btn.setMinimumHeight(35)
        button_layout.addWidget(self.start_diagnosis_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setMinimumHeight(35)
        self.refresh_btn.setEnabled(False)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setMinimumHeight(35)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        main_layout.addWidget(self.status_label)
    
    def create_diagnostics_tab(self):
        """创建诊断标签页"""
        diagnostics_widget = QWidget()
        layout = QVBoxLayout(diagnostics_widget)
        
        # 网络状态概览
        status_group = QGroupBox("网络状态概览")
        status_layout = QVBoxLayout(status_group)
        
        self.overall_status_label = QLabel("状态: 未检测")
        self.internet_status_label = QLabel("互联网连接: 未检测")
        self.dns_status_label = QLabel("DNS解析: 未检测")
        self.avg_response_label = QLabel("平均响应时间: 未检测")
        
        status_layout.addWidget(self.overall_status_label)
        status_layout.addWidget(self.internet_status_label)
        status_layout.addWidget(self.dns_status_label)
        status_layout.addWidget(self.avg_response_label)
        
        layout.addWidget(status_group)
        
        # 详细结果
        details_group = QGroupBox("详细检测结果")
        details_layout = QVBoxLayout(details_group)
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(4)
        self.details_table.setHorizontalHeaderLabels(["URL", "状态", "响应时间", "错误信息"])
        self.details_table.horizontalHeader().setStretchLastSection(True)
        
        details_layout.addWidget(self.details_table)
        layout.addWidget(details_group)
        
        self.tab_widget.addTab(diagnostics_widget, "网络诊断")
    
    def create_sources_tab(self):
        """创建下载源状态标签页"""
        sources_widget = QWidget()
        layout = QVBoxLayout(sources_widget)
        
        # 下载源状态
        sources_group = QGroupBox("下载源连通性状态")
        sources_layout = QVBoxLayout(sources_group)
        
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(5)
        self.sources_table.setHorizontalHeaderLabels(["源名称", "类型", "状态", "响应时间", "优先级"])
        self.sources_table.horizontalHeader().setStretchLastSection(True)
        
        sources_layout.addWidget(self.sources_table)
        layout.addWidget(sources_group)
        
        self.tab_widget.addTab(sources_widget, "下载源状态")
    
    def create_recommendations_tab(self):
        """创建建议标签页"""
        recommendations_widget = QWidget()
        layout = QVBoxLayout(recommendations_widget)
        
        # 优化建议
        recommendations_group = QGroupBox("网络优化建议")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setPlainText("请先运行网络诊断以获取优化建议...")
        
        recommendations_layout.addWidget(self.recommendations_text)
        layout.addWidget(recommendations_group)
        
        self.tab_widget.addTab(recommendations_widget, "优化建议")
    
    def setup_connections(self):
        """设置信号连接"""
        self.start_diagnosis_btn.clicked.connect(self.start_diagnosis)
        self.refresh_btn.clicked.connect(self.start_diagnosis)
        self.close_btn.clicked.connect(self.close)
    
    def start_diagnosis(self):
        """开始网络诊断"""
        if not HAS_NETWORK_TOOLS:
            QMessageBox.warning(self, "警告", "网络诊断工具不可用，请检查相关模块是否正确安装。")
            return
        
        self.start_diagnosis_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动诊断工作线程
        self.diagnostics_worker = NetworkDiagnosticsWorker()
        self.diagnostics_worker.diagnostics_completed.connect(self.on_diagnostics_completed)
        self.diagnostics_worker.progress_updated.connect(self.on_progress_updated)
        self.diagnostics_worker.start()
    
    def on_progress_updated(self, progress: int, message: str):
        """进度更新处理"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_diagnostics_completed(self, result):
        """诊断完成处理"""
        self.progress_bar.setVisible(False)
        self.start_diagnosis_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        
        if result is None:
            self.status_label.setText("诊断失败")
            QMessageBox.critical(self, "错误", "网络诊断失败，请检查网络连接。")
            return
        
        self.current_diagnostics = result
        self.update_diagnostics_display(result)
        self.status_label.setText("诊断完成")
    
    def update_diagnostics_display(self, result: Dict[str, Any]):
        """更新诊断结果显示"""
        network_diag = result.get('network_diagnostics')
        source_status = result.get('source_status', {})
        
        if network_diag:
            # 更新网络状态概览
            status_map = {
                NetworkStatus.EXCELLENT: "优秀 ✅",
                NetworkStatus.GOOD: "良好 ✅", 
                NetworkStatus.FAIR: "一般 ⚠️",
                NetworkStatus.POOR: "较差 ❌",
                NetworkStatus.OFFLINE: "离线 ❌"
            }
            
            self.overall_status_label.setText(f"状态: {status_map.get(network_diag.overall_status, '未知')}")
            self.internet_status_label.setText(f"互联网连接: {'正常 ✅' if network_diag.internet_accessible else '异常 ❌'}")
            self.dns_status_label.setText(f"DNS解析: {'正常 ✅' if network_diag.dns_working else '异常 ❌'}")
            self.avg_response_label.setText(f"平均响应时间: {network_diag.avg_response_time:.1f}ms")
            
            # 更新详细结果表格
            self.details_table.setRowCount(len(network_diag.detailed_results))
            for i, (url, result) in enumerate(network_diag.detailed_results.items()):
                self.details_table.setItem(i, 0, QTableWidgetItem(url))
                self.details_table.setItem(i, 1, QTableWidgetItem("可访问 ✅" if result.accessible else "不可访问 ❌"))
                self.details_table.setItem(i, 2, QTableWidgetItem(f"{result.response_time:.1f}ms"))
                self.details_table.setItem(i, 3, QTableWidgetItem(result.error or "无"))
            
            # 更新建议
            recommendations = "\n".join(network_diag.recommendations)
            self.recommendations_text.setPlainText(recommendations)
        
        # 更新下载源状态
        if source_status:
            self.sources_table.setRowCount(len(source_status))
            for i, (source_id, (available, response_time)) in enumerate(source_status.items()):
                self.sources_table.setItem(i, 0, QTableWidgetItem(source_id))
                self.sources_table.setItem(i, 1, QTableWidgetItem("下载源"))
                self.sources_table.setItem(i, 2, QTableWidgetItem("可用 ✅" if available else "不可用 ❌"))
                self.sources_table.setItem(i, 3, QTableWidgetItem(f"{response_time:.1f}ms" if available else "N/A"))
                self.sources_table.setItem(i, 4, QTableWidgetItem("自动"))

def show_network_diagnostics(parent=None):
    """显示网络诊断对话框"""
    dialog = NetworkDiagnosticsDialog(parent)
    return dialog.exec()
