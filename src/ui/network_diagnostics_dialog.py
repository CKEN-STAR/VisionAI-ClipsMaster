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
from PyQt6.QtGui import QFont, QColor, QPalette, QColor, QIcon

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

            self.progress_updated.emit(5, "初始化网络检测器...")
            self.checker = NetworkConnectivityChecker()

            self.progress_updated.emit(10, "检查DNS解析...")

            # 使用同步方法进行网络诊断
            try:
                # 简化的网络诊断 - 不使用异步
                import socket
                import urllib.request
                import time

                diagnostics = {
                    'dns_working': False,
                    'internet_accessible': False,
                    'urls_status': {}
                }

                # 检查DNS
                try:
                    socket.gethostbyname('www.baidu.com')
                    diagnostics['dns_working'] = True
                    self.progress_updated.emit(15, "DNS解析成功 ✅")
                except:
                    self.progress_updated.emit(15, "DNS解析失败 ❌")

                self.progress_updated.emit(20, "开始检测网站连通性...")

                # 检查互联网连接和下载源
                test_urls = {
                    'https://www.baidu.com': '百度',
                    'https://modelscope.cn': 'ModelScope',
                    'https://huggingface.co': 'HuggingFace',
                    'https://github.com': 'GitHub',
                    'https://www.google.com': 'Google'
                }

                # 为每个URL分配进度 (20%-70%, 共50%, 每个URL 10%)
                url_count = len(test_urls)
                for idx, (url, name) in enumerate(test_urls.items()):
                    progress = 20 + int((idx / url_count) * 50)
                    self.progress_updated.emit(progress, f"检测 {name}...")

                    try:
                        start_time = time.time()
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=5) as response:
                            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                            diagnostics['urls_status'][url] = {
                                'accessible': True,
                                'status_code': response.status,
                                'response_time': response_time,
                                'name': name
                            }
                            diagnostics['internet_accessible'] = True
                            self.progress_updated.emit(progress + 5, f"{name} 可访问 ✅ ({response_time:.0f}ms)")
                    except Exception as e:
                        diagnostics['urls_status'][url] = {
                            'accessible': False,
                            'error': str(e),
                            'response_time': 0,
                            'name': name
                        }
                        self.progress_updated.emit(progress + 5, f"{name} 不可访问 ❌")

                self.progress_updated.emit(75, "分析下载源状态...")

                # 检查下载源
                download_sources = {
                    'ModelScope': 'https://modelscope.cn',
                    'HuggingFace': 'https://huggingface.co',
                    'GitHub': 'https://github.com'
                }

                source_status = {}
                for source_name, source_url in download_sources.items():
                    if source_url in diagnostics['urls_status']:
                        url_info = diagnostics['urls_status'][source_url]
                        source_status[source_name] = {
                            'available': url_info['accessible'],
                            'response_time': url_info.get('response_time', 0)
                        }

                self.progress_updated.emit(90, "生成诊断报告...")

                # 简化的结果
                result = {
                    'network_diagnostics': diagnostics,
                    'source_status': source_status,
                    'manager_diagnostics': {}
                }

                self.progress_updated.emit(100, "诊断完成")
                self.diagnostics_completed.emit(result)

            except Exception as e:
                logger.error(f"网络诊断执行失败: {e}")
                self.diagnostics_completed.emit(None)

        except Exception as e:
            logger.error(f"网络诊断失败: {e}")
            import traceback
            traceback.print_exc()
            self.diagnostics_completed.emit(None)

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

        # 设置更大的字体
        recommendations_font = QFont()
        recommendations_font.setPointSize(12)  # 从默认的9pt增加到12pt
        self.recommendations_text.setFont(recommendations_font)

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
            # 处理简化的字典格式
            dns_working = network_diag.get('dns_working', False)
            internet_accessible = network_diag.get('internet_accessible', False)
            urls_status = network_diag.get('urls_status', {})

            # 确定整体状态
            if internet_accessible and dns_working:
                overall_status = "良好 ✅"
            elif dns_working:
                overall_status = "一般 ⚠️"
            else:
                overall_status = "离线 ❌"

            self.overall_status_label.setText(f"状态: {overall_status}")
            self.internet_status_label.setText(f"互联网连接: {'正常 ✅' if internet_accessible else '异常 ❌'}")
            self.dns_status_label.setText(f"DNS解析: {'正常 ✅' if dns_working else '异常 ❌'}")

            # 计算平均响应时间
            response_times = []
            for url_info in urls_status.values():
                if url_info.get('accessible') and 'response_time' in url_info:
                    response_times.append(url_info['response_time'])
            avg_response = sum(response_times) / len(response_times) if response_times else 0
            self.avg_response_label.setText(f"平均响应时间: {avg_response:.1f}ms")

            # 更新详细结果表格
            self.details_table.setRowCount(len(urls_status))
            for i, (url, result) in enumerate(urls_status.items()):
                self.details_table.setItem(i, 0, QTableWidgetItem(url))
                accessible = result.get('accessible', False)
                self.details_table.setItem(i, 1, QTableWidgetItem("可访问 ✅" if accessible else "不可访问 ❌"))
                response_time = result.get('response_time', 0) if accessible else 0
                self.details_table.setItem(i, 2, QTableWidgetItem(f"{response_time:.1f}ms"))
                error = result.get('error', '无')
                self.details_table.setItem(i, 3, QTableWidgetItem(error))

            # 更新建议 - 根据实际网络状况动态生成
            recommendations = []

            # DNS检查
            if not dns_working:
                recommendations.append("❌ DNS解析失败")
                recommendations.append("   建议: 检查DNS设置,尝试使用8.8.8.8或114.114.114.114")

            # 互联网连接检查
            if not internet_accessible:
                recommendations.append("❌ 无法访问互联网")
                recommendations.append("   建议: 检查网络连接,确认路由器和防火墙设置")

            # 响应时间分析
            if avg_response > 0:
                if avg_response < 100:
                    recommendations.append("✅ 网络速度优秀 (平均响应时间 < 100ms)")
                elif avg_response < 300:
                    recommendations.append("⚠️ 网络速度良好 (平均响应时间 100-300ms)")
                elif avg_response < 1000:
                    recommendations.append("⚠️ 网络速度一般 (平均响应时间 300-1000ms)")
                    recommendations.append("   建议: 检查网络带宽,关闭占用带宽的程序")
                else:
                    recommendations.append("❌ 网络速度较慢 (平均响应时间 > 1000ms)")
                    recommendations.append("   建议: 检查网络质量,考虑更换网络环境")

            # 下载源可用性分析
            accessible_count = sum(1 for info in urls_status.values() if info.get('accessible'))
            total_count = len(urls_status)

            if accessible_count == total_count:
                recommendations.append("✅ 所有测试网站均可访问")
            elif accessible_count > 0:
                recommendations.append(f"⚠️ 部分网站不可访问 ({accessible_count}/{total_count})")
                # 列出不可访问的网站
                for url, info in urls_status.items():
                    if not info.get('accessible'):
                        name = info.get('name', url)
                        recommendations.append(f"   - {name}: {info.get('error', '未知错误')}")
            else:
                recommendations.append("❌ 所有测试网站均不可访问")
                recommendations.append("   建议: 检查防火墙设置,确认是否被拦截")

            # 如果一切正常
            if not recommendations:
                recommendations.append("✅ 网络连接正常,所有功能可用")

            self.recommendations_text.setPlainText("\n".join(recommendations))
        
        # 更新下载源状态
        if source_status:
            self.sources_table.setRowCount(len(source_status))
            for i, (source_id, source_info) in enumerate(source_status.items()):
                # 处理字典格式
                if isinstance(source_info, dict):
                    available = source_info.get('available', False)
                    response_time = source_info.get('response_time', 0)
                else:
                    # 兼容元组格式
                    available, response_time = source_info

                # 创建不可编辑的单元格
                name_item = QTableWidgetItem(source_id)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.sources_table.setItem(i, 0, name_item)

                type_item = QTableWidgetItem("模型下载源")
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.sources_table.setItem(i, 1, type_item)

                status_item = QTableWidgetItem("可用 ✅" if available else "不可用 ❌")
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.sources_table.setItem(i, 2, status_item)

                time_item = QTableWidgetItem(f"{response_time:.1f}ms" if available else "N/A")
                time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.sources_table.setItem(i, 3, time_item)

                # 根据响应时间和可用性智能推荐
                if available:
                    # 根据响应时间动态评分
                    if response_time < 100:
                        recommendation = "优先推荐 ⭐⭐⭐⭐"
                        priority_score = 4
                    elif response_time < 200:
                        recommendation = "强烈推荐 ⭐⭐⭐"
                        priority_score = 3
                    elif response_time < 500:
                        recommendation = "推荐使用 ⭐⭐"
                        priority_score = 2
                    elif response_time < 1000:
                        recommendation = "可以使用 ⭐"
                        priority_score = 1
                    else:
                        recommendation = "备用选择"
                        priority_score = 0
                else:
                    recommendation = "暂不可用 ❌"
                    priority_score = -1

                priority_item = QTableWidgetItem(recommendation)
                priority_item.setFlags(priority_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # 根据优先级设置颜色
                if priority_score >= 3:
                    priority_item.setForeground(QColor(0, 150, 0))  # 深绿色
                elif priority_score >= 2:
                    priority_item.setForeground(QColor(100, 200, 0))  # 浅绿色
                elif priority_score >= 1:
                    priority_item.setForeground(QColor(200, 150, 0))  # 橙色
                elif priority_score >= 0:
                    priority_item.setForeground(QColor(200, 100, 0))  # 深橙色
                else:
                    priority_item.setForeground(QColor(200, 0, 0))  # 红色

                self.sources_table.setItem(i, 4, priority_item)

def show_network_diagnostics(parent=None):
    """显示网络诊断对话框"""
    dialog = NetworkDiagnosticsDialog(parent)
    return dialog.exec()
