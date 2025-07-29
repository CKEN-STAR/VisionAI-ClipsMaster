#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能推荐下载器UI优化版本

确保硬件信息和推荐内容能够实时响应设备变化：
1. 智能推荐区域动态更新
2. 硬件信息标签页实时刷新
3. 设备迁移适配
4. 集成已优化的硬件检测器和智能推荐器
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QProgressBar, QFrame, QScrollArea,
    QWidget, QTabWidget, QGridLayout, QSizePolicy, QMessageBox,
    QApplication, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class HardwareDetectionWorker(QObject):
    """硬件检测工作线程"""
    
    detection_completed = pyqtSignal(dict)  # 检测完成信号
    detection_failed = pyqtSignal(str)      # 检测失败信号
    
    def __init__(self):
        super().__init__()
        self.is_cancelled = False
    
    def detect_hardware(self):
        """执行硬件检测"""
        try:
            if self.is_cancelled:
                return
            
            # 导入硬件检测器
            from src.core.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            if self.is_cancelled:
                return
            
            # 转换为字典格式
            hardware_dict = {
                'gpu_type': str(getattr(hardware_info, 'gpu_type', 'unknown')),
                'gpu_memory_gb': getattr(hardware_info, 'gpu_memory_gb', 0),
                'gpu_count': getattr(hardware_info, 'gpu_count', 0),
                'gpu_names': getattr(hardware_info, 'gpu_names', []),
                'system_ram_gb': getattr(hardware_info, 'total_memory_gb', 0),
                'available_ram_gb': getattr(hardware_info, 'available_memory_gb', 0),
                'cpu_cores': getattr(hardware_info, 'cpu_cores', 0),
                'cpu_freq_mhz': getattr(hardware_info, 'cpu_freq_mhz', 0),
                'performance_level': str(getattr(hardware_info, 'performance_level', 'unknown')),
                'recommended_quantization': getattr(hardware_info, 'recommended_quantization', 'unknown'),
                'gpu_acceleration': getattr(hardware_info, 'gpu_acceleration', False),
                'has_gpu': getattr(hardware_info, 'gpu_memory_gb', 0) > 0,
                'detection_timestamp': time.time()
            }
            
            self.detection_completed.emit(hardware_dict)
            
        except Exception as e:
            logger.error(f"硬件检测失败: {e}")
            self.detection_failed.emit(str(e))
    
    def cancel(self):
        """取消检测"""
        self.is_cancelled = True


class RecommendationWorker(QObject):
    """推荐获取工作线程"""
    
    recommendation_completed = pyqtSignal(dict)  # 推荐完成信号
    recommendation_failed = pyqtSignal(str)      # 推荐失败信号
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self.is_cancelled = False
    
    def get_recommendation(self):
        """获取智能推荐"""
        try:
            if self.is_cancelled:
                return
            
            # 导入智能推荐器
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            selector = IntelligentModelSelector()
            
            # 强制刷新硬件配置
            selector.force_refresh_hardware()
            
            if self.is_cancelled:
                return
            
            # 获取推荐
            recommendation = selector.recommend_model_version(self.model_name)
            
            if self.is_cancelled:
                return
            
            if recommendation:
                # 转换为字典格式
                recommendation_dict = {
                    'model_name': recommendation.model_name,
                    'variant_name': recommendation.variant.name if recommendation.variant else None,
                    'quantization': recommendation.variant.quantization.value if recommendation.variant else None,
                    'size_gb': recommendation.variant.size_gb if recommendation.variant else None,
                    'quality_retention': recommendation.variant.quality_retention if recommendation.variant else None,
                    'memory_requirement_gb': recommendation.variant.memory_requirement_gb if recommendation.variant else None,
                    'reasoning': recommendation.reasoning if hasattr(recommendation, 'reasoning') else [],
                    'compatibility_score': getattr(recommendation, 'compatibility_score', 0),
                    'recommendation_timestamp': time.time()
                }
                
                self.recommendation_completed.emit(recommendation_dict)
            else:
                self.recommendation_failed.emit("未能获取推荐结果")
                
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            self.recommendation_failed.emit(str(e))
    
    def cancel(self):
        """取消推荐获取"""
        self.is_cancelled = True


class RealTimeHardwareInfoWidget(QFrame):
    """实时硬件信息显示组件"""
    
    refresh_requested = pyqtSignal()  # 刷新请求信号
    
    def __init__(self):
        super().__init__()
        self.hardware_info = {}
        self.detection_worker = None
        self.detection_thread = None
        self.setup_ui()
        self.setup_auto_refresh()
    
    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        
        # 标题和刷新按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🔧 硬件配置信息")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setToolTip("手动刷新硬件信息")
        self.refresh_btn.clicked.connect(self.refresh_hardware_info)
        header_layout.addWidget(self.refresh_btn)
        
        self.layout.addLayout(header_layout)
        
        # 检测状态指示器
        self.status_label = QLabel("🔍 正在检测硬件配置...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        self.layout.addWidget(self.status_label)
        
        # 硬件信息网格
        self.info_grid = QGridLayout()
        self.layout.addLayout(self.info_grid)
        
        # 初始化空的信息显示
        self.update_hardware_display({})
    
    def setup_auto_refresh(self):
        """设置自动刷新"""
        # 定期检查硬件变化（每30秒）
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.check_hardware_changes)
        self.auto_refresh_timer.start(30000)  # 30秒
        
        # 启动时立即检测
        QTimer.singleShot(100, self.refresh_hardware_info)
    
    def refresh_hardware_info(self):
        """刷新硬件信息"""
        if self.detection_worker and self.detection_thread:
            # 如果正在检测，先取消
            self.detection_worker.cancel()
            self.detection_thread.quit()
            self.detection_thread.wait(1000)
        
        # 更新状态
        self.status_label.setText("🔍 正在检测硬件配置...")
        self.refresh_btn.setEnabled(False)
        
        # 创建新的检测线程
        self.detection_thread = QThread()
        self.detection_worker = HardwareDetectionWorker()
        self.detection_worker.moveToThread(self.detection_thread)
        
        # 连接信号
        self.detection_thread.started.connect(self.detection_worker.detect_hardware)
        self.detection_worker.detection_completed.connect(self.on_hardware_detected)
        self.detection_worker.detection_failed.connect(self.on_detection_failed)
        self.detection_worker.detection_completed.connect(self.detection_thread.quit)
        self.detection_worker.detection_failed.connect(self.detection_thread.quit)
        self.detection_thread.finished.connect(self.detection_thread.deleteLater)
        
        # 启动检测
        self.detection_thread.start()
    
    def on_hardware_detected(self, hardware_info: Dict):
        """硬件检测完成"""
        self.hardware_info = hardware_info
        self.update_hardware_display(hardware_info)
        self.status_label.setText(f"✅ 硬件检测完成 ({time.strftime('%H:%M:%S')})")
        self.refresh_btn.setEnabled(True)
        
        # 发送刷新请求信号
        self.refresh_requested.emit()
    
    def on_detection_failed(self, error_message: str):
        """硬件检测失败"""
        self.status_label.setText(f"❌ 硬件检测失败: {error_message}")
        self.refresh_btn.setEnabled(True)
    
    def update_hardware_display(self, hardware_info: Dict):
        """更新硬件信息显示"""
        # 清除现有信息
        for i in reversed(range(self.info_grid.count())):
            self.info_grid.itemAt(i).widget().setParent(None)
        
        if not hardware_info:
            no_info_label = QLabel("暂无硬件信息")
            no_info_label.setStyleSheet("color: #999; font-style: italic;")
            self.info_grid.addWidget(no_info_label, 0, 0, 1, 2)
            return
        
        row = 0
        
        # GPU信息
        gpu_label = QLabel("GPU类型:")
        gpu_type = hardware_info.get('gpu_type', 'unknown')
        gpu_memory = hardware_info.get('gpu_memory_gb', 0)
        
        if gpu_type != 'unknown' and gpu_memory > 0:
            gpu_value = QLabel(f"{gpu_type.upper()} ({gpu_memory:.1f}GB)")
            gpu_value.setStyleSheet("color: green; font-weight: bold;")
        else:
            gpu_value = QLabel("无独立显卡 (使用CPU)")
            gpu_value.setStyleSheet("color: orange;")
        
        self.info_grid.addWidget(gpu_label, row, 0)
        self.info_grid.addWidget(gpu_value, row, 1)
        row += 1
        
        # 系统内存
        ram_label = QLabel("系统内存:")
        ram_total = hardware_info.get('system_ram_gb', 0)
        ram_available = hardware_info.get('available_ram_gb', 0)
        ram_value = QLabel(f"{ram_total:.1f}GB (可用: {ram_available:.1f}GB)")
        ram_value.setStyleSheet("color: blue; font-weight: bold;")
        self.info_grid.addWidget(ram_label, row, 0)
        self.info_grid.addWidget(ram_value, row, 1)
        row += 1
        
        # CPU信息
        cpu_label = QLabel("CPU核心:")
        cpu_cores = hardware_info.get('cpu_cores', 0)
        cpu_freq = hardware_info.get('cpu_freq_mhz', 0)
        cpu_value = QLabel(f"{cpu_cores}核 ({cpu_freq:.0f}MHz)")
        cpu_value.setStyleSheet("color: purple; font-weight: bold;")
        self.info_grid.addWidget(cpu_label, row, 0)
        self.info_grid.addWidget(cpu_value, row, 1)
        row += 1
        
        # 性能等级
        perf_label = QLabel("性能等级:")
        perf_level = hardware_info.get('performance_level', 'unknown')
        perf_value = QLabel(perf_level.upper())
        
        # 根据性能等级设置颜色
        if perf_level.lower() == 'ultra':
            perf_value.setStyleSheet("color: #ff6b35; font-weight: bold;")
        elif perf_level.lower() == 'high':
            perf_value.setStyleSheet("color: #f7931e; font-weight: bold;")
        elif perf_level.lower() == 'medium':
            perf_value.setStyleSheet("color: #ffb347; font-weight: bold;")
        else:
            perf_value.setStyleSheet("color: #999; font-weight: bold;")
        
        self.info_grid.addWidget(perf_label, row, 0)
        self.info_grid.addWidget(perf_value, row, 1)
        row += 1
        
        # 推荐量化
        quant_label = QLabel("推荐量化:")
        quant_value = QLabel(hardware_info.get('recommended_quantization', 'unknown'))
        quant_value.setStyleSheet("color: #28a745; font-weight: bold;")
        self.info_grid.addWidget(quant_label, row, 0)
        self.info_grid.addWidget(quant_value, row, 1)
        row += 1
        
        # GPU加速
        accel_label = QLabel("GPU加速:")
        gpu_accel = hardware_info.get('gpu_acceleration', False)
        accel_value = QLabel("✅ 支持" if gpu_accel else "❌ 不支持")
        accel_value.setStyleSheet("color: green;" if gpu_accel else "color: red;")
        self.info_grid.addWidget(accel_label, row, 0)
        self.info_grid.addWidget(accel_value, row, 1)
    
    def check_hardware_changes(self):
        """检查硬件变化"""
        # 这里可以添加更智能的硬件变化检测逻辑
        # 目前简单地定期刷新
        pass
    
    def get_hardware_info(self) -> Dict:
        """获取当前硬件信息"""
        return self.hardware_info.copy()


class DynamicRecommendationWidget(QFrame):
    """动态推荐显示组件"""
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self.recommendation_info = {}
        self.recommendation_worker = None
        self.recommendation_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f0f8ff;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"🎯 {self.model_name} 智能推荐")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        self.layout.addWidget(title_label)
        
        # 状态标签
        self.status_label = QLabel("🔍 正在分析您的硬件配置...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        self.layout.addWidget(self.status_label)
        
        # 推荐内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.layout.addWidget(self.content_widget)
        
        # 初始化空内容
        self.update_recommendation_display({})
    
    def refresh_recommendation(self):
        """刷新推荐"""
        if self.recommendation_worker and self.recommendation_thread:
            # 如果正在获取推荐，先取消
            self.recommendation_worker.cancel()
            self.recommendation_thread.quit()
            self.recommendation_thread.wait(1000)
        
        # 更新状态
        self.status_label.setText("🔍 正在分析您的硬件配置...")
        
        # 创建新的推荐线程
        self.recommendation_thread = QThread()
        self.recommendation_worker = RecommendationWorker(self.model_name)
        self.recommendation_worker.moveToThread(self.recommendation_thread)
        
        # 连接信号
        self.recommendation_thread.started.connect(self.recommendation_worker.get_recommendation)
        self.recommendation_worker.recommendation_completed.connect(self.on_recommendation_received)
        self.recommendation_worker.recommendation_failed.connect(self.on_recommendation_failed)
        self.recommendation_worker.recommendation_completed.connect(self.recommendation_thread.quit)
        self.recommendation_worker.recommendation_failed.connect(self.recommendation_thread.quit)
        self.recommendation_thread.finished.connect(self.recommendation_thread.deleteLater)
        
        # 启动推荐获取
        self.recommendation_thread.start()
    
    def on_recommendation_received(self, recommendation_info: Dict):
        """推荐获取完成"""
        self.recommendation_info = recommendation_info
        self.update_recommendation_display(recommendation_info)
        self.status_label.setText(f"✅ 推荐分析完成 ({time.strftime('%H:%M:%S')})")
    
    def on_recommendation_failed(self, error_message: str):
        """推荐获取失败"""
        self.status_label.setText(f"❌ 推荐分析失败: {error_message}")
    
    def update_recommendation_display(self, recommendation_info: Dict):
        """更新推荐显示"""
        # 清除现有内容
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        if not recommendation_info:
            no_rec_label = QLabel("暂无推荐信息")
            no_rec_label.setStyleSheet("color: #999; font-style: italic;")
            self.content_layout.addWidget(no_rec_label)
            return
        
        # 推荐版本信息
        version_group = QGroupBox("📦 推荐版本")
        version_layout = QGridLayout(version_group)
        
        # 版本名称
        version_layout.addWidget(QLabel("版本:"), 0, 0)
        version_name = QLabel(recommendation_info.get('variant_name', 'unknown'))
        version_name.setStyleSheet("font-weight: bold; color: #007bff;")
        version_layout.addWidget(version_name, 0, 1)
        
        # 量化等级
        version_layout.addWidget(QLabel("量化等级:"), 1, 0)
        quantization = QLabel(recommendation_info.get('quantization', 'unknown'))
        quantization.setStyleSheet("font-weight: bold; color: #28a745;")
        version_layout.addWidget(quantization, 1, 1)
        
        # 模型大小
        version_layout.addWidget(QLabel("模型大小:"), 2, 0)
        size_gb = recommendation_info.get('size_gb', 0)
        size_label = QLabel(f"{size_gb:.1f} GB")
        size_label.setStyleSheet("font-weight: bold; color: #fd7e14;")
        version_layout.addWidget(size_label, 2, 1)
        
        # 内存需求
        version_layout.addWidget(QLabel("内存需求:"), 3, 0)
        memory_req = recommendation_info.get('memory_requirement_gb', 0)
        memory_label = QLabel(f"{memory_req:.1f} GB")
        memory_label.setStyleSheet("font-weight: bold; color: #6f42c1;")
        version_layout.addWidget(memory_label, 3, 1)
        
        # 质量保持
        version_layout.addWidget(QLabel("质量保持:"), 4, 0)
        quality = recommendation_info.get('quality_retention', 0)
        quality_label = QLabel(f"{quality:.1%}")
        quality_label.setStyleSheet("font-weight: bold; color: #e83e8c;")
        version_layout.addWidget(quality_label, 4, 1)
        
        self.content_layout.addWidget(version_group)
        
        # 推荐理由
        reasoning = recommendation_info.get('reasoning', [])
        if reasoning:
            reasoning_group = QGroupBox("💡 推荐理由")
            reasoning_layout = QVBoxLayout(reasoning_group)
            
            reasoning_text = QTextEdit()
            reasoning_text.setPlainText("\n".join(reasoning))
            reasoning_text.setMaximumHeight(100)
            reasoning_text.setReadOnly(True)
            reasoning_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            reasoning_layout.addWidget(reasoning_text)
            
            self.content_layout.addWidget(reasoning_group)
    
    def get_recommendation_info(self) -> Dict:
        """获取当前推荐信息"""
        return self.recommendation_info.copy()


class OptimizedSmartDownloaderDialog(QDialog):
    """优化的智能推荐下载器对话框"""

    download_requested = pyqtSignal(str, dict)  # 下载请求信号

    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.dialog = SmartDownloaderDialog(model_name, parent)

        # 连接信号
        self.dialog.download_requested.connect(self.download_requested)

        # 设置窗口属性
        self.setWindowTitle(f"优化智能下载器 - {model_name}")
        self.setModal(True)

    def show_intelligent_recommendation(self):
        """显示智能推荐"""
        return self.dialog.show_intelligent_recommendation()

    def update_recommendation(self, recommendation):
        """更新推荐"""
        return self.dialog.update_recommendation(recommendation)

    def exec(self):
        """执行对话框"""
        return self.dialog.exec()

class SmartDownloaderDialog(QDialog):
    """智能推荐下载器对话框 - 优化版本"""

    download_requested = pyqtSignal(str, dict)  # 下载请求信号 (model_name, variant_info)

    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.selected_variant = None
        self.hardware_widget = None
        self.recommendation_widget = None
        self.setup_ui()
        self.setup_connections()

        # 启动初始化
        QTimer.singleShot(100, self.initialize_components)

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"智能推荐下载器 - {self.model_name}")
        self.setModal(True)
        self.resize(900, 700)

        # 设置窗口图标
        self.setWindowIcon(QIcon(":/icons/download.png") if hasattr(self, "setWindowIcon") else QIcon())

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题区域
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 20px;
                border-radius: 0px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)

        title_label = QLabel(f"🤖 {self.model_name} 智能下载助手")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("基于您的硬件配置，为您推荐最适合的模型版本")
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px;")
        title_layout.addWidget(subtitle_label)

        main_layout.addWidget(title_frame)

        # 标签页容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #667eea;
            }
        """)

        main_layout.addWidget(self.tab_widget)

        # 底部按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 15px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)

        # 状态信息
        self.status_label = QLabel("请等待硬件检测和推荐分析完成...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        button_layout.addWidget(self.status_label)

        button_layout.addStretch()

        # 刷新按钮
        self.refresh_all_btn = QPushButton("🔄 刷新全部")
        self.refresh_all_btn.setToolTip("重新检测硬件并刷新推荐")
        self.refresh_all_btn.clicked.connect(self.refresh_all)
        button_layout.addWidget(self.refresh_all_btn)

        # 下载按钮
        self.download_btn = QPushButton("📥 下载推荐版本")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)

        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addWidget(button_frame)

    def setup_connections(self):
        """设置信号连接"""
        pass  # 将在initialize_components中设置

    def initialize_components(self):
        """初始化组件"""
        try:
            # 创建智能推荐标签页
            self.recommendation_widget = DynamicRecommendationWidget(self.model_name)

            # 创建滚动区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(self.recommendation_widget)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)

            self.tab_widget.addTab(scroll_area, "🎯 智能推荐")

            # 创建硬件信息标签页
            self.hardware_widget = RealTimeHardwareInfoWidget()

            hardware_scroll = QScrollArea()
            hardware_scroll.setWidgetResizable(True)
            hardware_scroll.setWidget(self.hardware_widget)
            hardware_scroll.setFrameShape(QFrame.Shape.NoFrame)

            self.tab_widget.addTab(hardware_scroll, "🔧 硬件信息")

            # 设置信号连接
            self.hardware_widget.refresh_requested.connect(self.on_hardware_refreshed)

            # 启动推荐刷新
            QTimer.singleShot(500, self.recommendation_widget.refresh_recommendation)

        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            self.status_label.setText(f"❌ 初始化失败: {e}")

    def on_hardware_refreshed(self):
        """硬件信息刷新完成"""
        # 刷新推荐
        if self.recommendation_widget:
            self.recommendation_widget.refresh_recommendation()

        # 更新状态
        self.status_label.setText("✅ 硬件检测完成，正在更新推荐...")

        # 检查是否可以启用下载按钮
        QTimer.singleShot(2000, self.check_download_readiness)

    def check_download_readiness(self):
        """检查下载准备状态"""
        if (self.recommendation_widget and
            self.recommendation_widget.get_recommendation_info()):
            self.download_btn.setEnabled(True)
            self.status_label.setText("✅ 准备就绪，可以开始下载")
        else:
            self.status_label.setText("⏳ 正在分析推荐...")

    def refresh_all(self):
        """刷新全部信息"""
        self.status_label.setText("🔄 正在刷新硬件信息和推荐...")
        self.download_btn.setEnabled(False)

        # 刷新硬件信息
        if self.hardware_widget:
            self.hardware_widget.refresh_hardware_info()

    def start_download(self):
        """开始下载"""
        if not self.recommendation_widget:
            QMessageBox.warning(self, "错误", "推荐组件未初始化")
            return

        recommendation_info = self.recommendation_widget.get_recommendation_info()
        if not recommendation_info:
            QMessageBox.warning(self, "错误", "未获取到推荐信息")
            return

        # 确认下载
        variant_name = recommendation_info.get('variant_name', 'unknown')
        size_gb = recommendation_info.get('size_gb', 0)

        reply = QMessageBox.question(
            self,
            "确认下载",
            f"确定要下载 {self.model_name} 的 {variant_name} 版本吗？\n\n"
            f"模型大小: {size_gb:.1f} GB\n"
            f"量化等级: {recommendation_info.get('quantization', 'unknown')}\n"
            f"内存需求: {recommendation_info.get('memory_requirement_gb', 0):.1f} GB",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 发送下载请求信号
            self.download_requested.emit(self.model_name, recommendation_info)
            self.accept()


if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)

    # 创建测试对话框
    dialog = SmartDownloaderDialog("qwen2.5-7b")

    # 连接下载信号
    def on_download_requested(model_name, variant_info):
        print(f"下载请求: {model_name}")
        print(f"变体信息: {variant_info}")

    dialog.download_requested.connect(on_download_requested)

    # 显示对话框
    result = dialog.exec()
    print(f"对话框结果: {result}")

    sys.exit(0)
