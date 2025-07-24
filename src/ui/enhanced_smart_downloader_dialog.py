#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强智能推荐下载器对话框 - VisionAI-ClipsMaster
集成动态硬件监控和模型推荐功能，实现实时适配和更新
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QProgressBar, QFrame, QTabWidget, QSizePolicy,
    QTextEdit, QScrollArea, QSpacerItem, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ui.dynamic_hardware_monitor import RealTimeHardwareInfoWidget
from src.ui.dynamic_model_recommendation import DynamicModelRecommendationWidget

logger = logging.getLogger(__name__)

class EnhancedSmartDownloaderDialog(QDialog):
    """增强智能推荐下载器对话框"""
    
    download_requested = pyqtSignal(str, object)  # 下载请求信号 (model_name, variant_info)
    hardware_changed = pyqtSignal(object)  # 硬件变化信号
    
    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.selected_variant = None
        self.current_hardware_info = {}
        
        self.init_ui()
        self.setup_connections()
        
        # 延迟启动硬件检测
        QTimer.singleShot(500, self.start_initial_detection)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"🎯 智能模型下载器 - {self.model_name}")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        title_label = QLabel(f"🤖 {self.model_name} 智能推荐下载")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 硬件状态指示器
        self.hardware_status_label = QLabel("🔍 检测硬件中...")
        self.hardware_status_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 4px;
                padding: 4px 8px;
                color: #1976d2;
            }
        """)
        title_layout.addWidget(self.hardware_status_label)
        
        main_layout.addLayout(title_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 智能推荐标签页
        self.recommendation_widget = DynamicModelRecommendationWidget(self.model_name)
        recommendation_scroll = QScrollArea()
        recommendation_scroll.setWidgetResizable(True)
        recommendation_scroll.setWidget(self.recommendation_widget)
        recommendation_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tab_widget.addTab(recommendation_scroll, "🎯 智能推荐")
        
        # 硬件信息标签页
        self.hardware_widget = RealTimeHardwareInfoWidget()
        hardware_scroll = QScrollArea()
        hardware_scroll.setWidgetResizable(True)
        hardware_scroll.setWidget(self.hardware_widget)
        hardware_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tab_widget.addTab(hardware_scroll, "🔧 硬件信息")
        
        # 推荐详情区域
        self.detail_group = QGroupBox("📋 当前推荐详情")
        detail_layout = QVBoxLayout(self.detail_group)
        
        self.recommendation_summary = QLabel("⏳ 正在分析设备配置...")
        self.recommendation_summary.setWordWrap(True)
        self.recommendation_summary.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                font-size: 11px;
            }
        """)
        detail_layout.addWidget(self.recommendation_summary)
        
        main_layout.addWidget(self.detail_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新检测")
        self.refresh_btn.clicked.connect(self.force_refresh)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # 下载按钮
        self.download_btn = QPushButton("⬇️ 开始下载")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.download_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态栏
        self.status_label = QLabel("🚀 智能推荐下载器已启动")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        main_layout.addWidget(self.status_label)
    
    def setup_connections(self):
        """设置信号连接"""
        try:
            # 硬件信息变化时更新推荐
            self.hardware_widget.hardware_changed.connect(self.on_hardware_changed)
            self.hardware_widget.refresh_requested.connect(self.on_hardware_refresh_requested)
            
            # 推荐变化时更新显示
            self.recommendation_widget.recommendation_changed.connect(self.on_recommendation_changed)
            self.recommendation_widget.variant_selected.connect(self.on_variant_selected)
            
        except Exception as e:
            logger.error(f"设置信号连接失败: {e}")
    
    def start_initial_detection(self):
        """开始初始检测"""
        try:
            self.status_label.setText("🔍 正在检测硬件配置...")
            
            # 强制刷新硬件信息
            self.hardware_widget.force_refresh()
            
        except Exception as e:
            logger.error(f"启动初始检测失败: {e}")
            self.status_label.setText(f"❌ 初始检测失败: {e}")
    
    def on_hardware_changed(self, hardware_snapshot):
        """硬件配置变化处理"""
        try:
            # 更新硬件信息
            self.current_hardware_info = self.hardware_widget.get_hardware_info() or {}
            
            # 更新硬件状态指示器
            if self.current_hardware_info.get('has_gpu', False):
                gpu_memory = self.current_hardware_info.get('gpu_memory_gb', 0)
                self.hardware_status_label.setText(f"🎮 GPU: {gpu_memory:.1f}GB")
                self.hardware_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #e8f5e8;
                        border: 1px solid #4caf50;
                        border-radius: 4px;
                        padding: 4px 8px;
                        color: #2e7d32;
                    }
                """)
            else:
                ram_gb = self.current_hardware_info.get('system_ram_gb', 0)
                self.hardware_status_label.setText(f"🧠 RAM: {ram_gb:.1f}GB")
                self.hardware_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #fff3e0;
                        border: 1px solid #ff9800;
                        border-radius: 4px;
                        padding: 4px 8px;
                        color: #f57c00;
                    }
                """)
            
            # 更新推荐组件
            self.recommendation_widget.update_hardware_info(self.current_hardware_info)
            
            # 更新状态
            self.status_label.setText("🔄 硬件配置已更新，正在重新分析推荐...")
            
            # 发送硬件变化信号
            self.hardware_changed.emit(hardware_snapshot)
            
        except Exception as e:
            logger.error(f"处理硬件变化失败: {e}")
            self.status_label.setText(f"❌ 硬件变化处理失败: {e}")
    
    def on_hardware_refresh_requested(self):
        """硬件刷新请求处理"""
        self.status_label.setText("🔄 正在刷新硬件信息...")
    
    def on_recommendation_changed(self, variants):
        """推荐变化处理"""
        try:
            # 查找推荐的变体
            recommended_variant = None
            for variant in variants:
                if variant.is_recommended:
                    recommended_variant = variant
                    break
            
            if recommended_variant:
                # 更新推荐摘要
                summary_text = f"""
🌟 推荐变体: {recommended_variant.name}
📦 文件大小: {recommended_variant.file_size_gb:.1f} GB
🧠 内存需求: {recommended_variant.memory_requirement_gb:.1f} GB  
📊 质量保持: {recommended_variant.quality_retention:.1%}
⚡ 推理速度: {recommended_variant.inference_speed_relative:.1f}x
⏱️ 预估下载: {recommended_variant.download_time_estimate_min} 分钟
💾 磁盘占用: {recommended_variant.disk_space_gb:.1f} GB
🎯 推荐理由: {recommended_variant.recommendation_reason}
"""
                self.recommendation_summary.setText(summary_text.strip())
                
                # 启用下载按钮
                self.download_btn.setEnabled(True)
                self.selected_variant = recommended_variant
                
                self.status_label.setText("✅ 推荐分析完成，可以开始下载")
            else:
                self.recommendation_summary.setText("⚠️ 暂无推荐变体，请检查硬件配置")
                self.download_btn.setEnabled(False)
                self.status_label.setText("⚠️ 无可用推荐")
                
        except Exception as e:
            logger.error(f"处理推荐变化失败: {e}")
            self.status_label.setText(f"❌ 推荐处理失败: {e}")
    
    def on_variant_selected(self, variant):
        """变体选择处理"""
        try:
            self.selected_variant = variant
            
            # 更新下载按钮状态
            if variant:
                self.download_btn.setEnabled(True)
                if variant.is_recommended:
                    self.download_btn.setText("⬇️ 下载推荐版本")
                else:
                    self.download_btn.setText("⬇️ 下载选中版本")
            else:
                self.download_btn.setEnabled(False)
                self.download_btn.setText("⬇️ 开始下载")
                
        except Exception as e:
            logger.error(f"处理变体选择失败: {e}")
    
    def force_refresh(self):
        """强制刷新"""
        try:
            self.status_label.setText("🔄 正在强制刷新...")
            
            # 刷新硬件信息
            self.hardware_widget.force_refresh()
            
            # 延迟刷新推荐
            QTimer.singleShot(1000, self.recommendation_widget.refresh_recommendations)
            
        except Exception as e:
            logger.error(f"强制刷新失败: {e}")
            self.status_label.setText(f"❌ 刷新失败: {e}")
    
    def start_download(self):
        """开始下载"""
        try:
            if not self.selected_variant:
                QMessageBox.warning(self, "警告", "请先选择要下载的模型变体")
                return
            
            # 确认下载
            reply = QMessageBox.question(
                self, 
                "确认下载",
                f"确定要下载 {self.selected_variant.name} 吗？\n\n"
                f"文件大小: {self.selected_variant.file_size_gb:.1f} GB\n"
                f"预估时间: {self.selected_variant.download_time_estimate_min} 分钟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 发送下载请求信号
                self.download_requested.emit(self.model_name, self.selected_variant)
                self.accept()
            
        except Exception as e:
            logger.error(f"开始下载失败: {e}")
            QMessageBox.critical(self, "错误", f"启动下载失败:\n{e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 停止硬件监控
            if self.hardware_widget:
                self.hardware_widget.stop_monitoring()
            
            super().closeEvent(event)
            
        except Exception as e:
            logger.error(f"关闭对话框失败: {e}")
            super().closeEvent(event)
