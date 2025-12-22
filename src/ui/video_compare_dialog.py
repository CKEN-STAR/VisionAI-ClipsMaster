#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频对比对话框
用于对比原片和混剪视频的质量差异
"""

import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTextEdit, QProgressBar, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# 导入视频对比模块
try:
    from src.core.video_comparison import VideoCompare
    VIDEO_COMPARE_AVAILABLE = True
except ImportError:
    VIDEO_COMPARE_AVAILABLE = False


class VideoCompareWorker(QThread):
    """视频对比工作线程"""
    
    progress = pyqtSignal(int, str)  # 进度, 消息
    finished = pyqtSignal(dict)  # 对比结果
    error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, video1_path: str, video2_path: str, use_gpu: bool = True):
        super().__init__()
        self.video1_path = video1_path
        self.video2_path = video2_path
        self.use_gpu = use_gpu
        self._is_cancelled = False
    
    def run(self):
        """执行视频对比"""
        try:
            if not VIDEO_COMPARE_AVAILABLE:
                self.error.emit("视频对比模块不可用，请检查安装")
                return
            
            self.progress.emit(10, "初始化视频对比器...")
            
            # 创建视频对比器
            comparer = VideoCompare(use_gpu=self.use_gpu)
            
            if self._is_cancelled:
                return
            
            self.progress.emit(30, "正在分析视频1...")
            
            # 对比视频
            result = comparer.compare_videos(
                self.video1_path,
                self.video2_path,
                sample_rate=30  # 每30帧采样一次
            )
            
            if self._is_cancelled:
                return
            
            self.progress.emit(100, "对比完成")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"视频对比失败: {str(e)}")
    
    def cancel(self):
        """取消对比"""
        self._is_cancelled = True


class VideoCompareDialog(QDialog):
    """视频对比对话框"""
    
    def __init__(self, parent=None, video1_path: str = None, video2_path: str = None):
        super().__init__(parent)
        self.video1_path = video1_path
        self.video2_path = video2_path
        self.worker = None
        
        self.setWindowTitle("视频质量对比")
        self.setMinimumSize(700, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("📊 视频质量对比工具")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel("对比原片和混剪视频的质量差异，包括PSNR、SSIM等指标")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 视频1选择
        video1_group = QGroupBox("原片视频")
        video1_layout = QHBoxLayout()
        self.video1_label = QLabel(self.video1_path if self.video1_path else "未选择")
        self.video1_label.setStyleSheet("padding: 5px; background: #f0f0f0; border-radius: 3px;")
        video1_layout.addWidget(self.video1_label, 1)
        
        video1_btn = QPushButton("选择视频1")
        video1_btn.clicked.connect(self.select_video1)
        video1_layout.addWidget(video1_btn)
        
        video1_group.setLayout(video1_layout)
        layout.addWidget(video1_group)
        
        # 视频2选择
        video2_group = QGroupBox("混剪视频")
        video2_layout = QHBoxLayout()
        self.video2_label = QLabel(self.video2_path if self.video2_path else "未选择")
        self.video2_label.setStyleSheet("padding: 5px; background: #f0f0f0; border-radius: 3px;")
        video2_layout.addWidget(self.video2_label, 1)
        
        video2_btn = QPushButton("选择视频2")
        video2_btn.clicked.connect(self.select_video2)
        video2_layout.addWidget(video2_btn)
        
        video2_group.setLayout(video2_layout)
        layout.addWidget(video2_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 结果显示
        result_group = QGroupBox("对比结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(300)
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.compare_btn = QPushButton("🔍 开始对比")
        self.compare_btn.setMinimumHeight(40)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #52c41a, stop: 1 #389e0d);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #73d13d, stop: 1 #52c41a);
            }
            QPushButton:disabled {
                background: #d9d9d9;
                color: #8c8c8c;
            }
        """)
        self.compare_btn.clicked.connect(self.start_compare)
        button_layout.addWidget(self.compare_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 更新按钮状态
        self.update_button_state()
    
    def select_video1(self):
        """选择视频1"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择原片视频",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*.*)"
        )
        
        if file_path:
            self.video1_path = file_path
            self.video1_label.setText(os.path.basename(file_path))
            self.update_button_state()
    
    def select_video2(self):
        """选择视频2"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择混剪视频",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*.*)"
        )
        
        if file_path:
            self.video2_path = file_path
            self.video2_label.setText(os.path.basename(file_path))
            self.update_button_state()
    
    def update_button_state(self):
        """更新按钮状态"""
        can_compare = (
            self.video1_path and os.path.exists(self.video1_path) and
            self.video2_path and os.path.exists(self.video2_path)
        )
        self.compare_btn.setEnabled(can_compare)
    
    def start_compare(self):
        """开始对比"""
        if not VIDEO_COMPARE_AVAILABLE:
            QMessageBox.warning(
                self,
                "功能不可用",
                "视频对比模块不可用，请检查安装"
            )
            return
        
        # 创建工作线程
        self.worker = VideoCompareWorker(
            self.video1_path,
            self.video2_path,
            use_gpu=True
        )
        
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        
        # 禁用按钮
        self.compare_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空结果
        self.result_text.clear()
        self.result_text.append("正在对比视频...\n")
        
        # 启动线程
        self.worker.start()
    
    def on_progress(self, value: int, message: str):
        """进度更新"""
        self.progress_bar.setValue(value)
        self.result_text.append(f"[{value}%] {message}")
    
    def on_finished(self, result: dict):
        """对比完成"""
        self.progress_bar.setVisible(False)
        self.compare_btn.setEnabled(True)
        
        # 显示结果
        self.result_text.clear()
        self.result_text.append("=" * 50)
        self.result_text.append("📊 视频对比结果")
        self.result_text.append("=" * 50)
        self.result_text.append("")
        
        # 相似度指标
        similarity = result.get('similarity', {})
        self.result_text.append("🎯 相似度指标:")
        self.result_text.append(f"  • 整体相似度: {similarity.get('overall', 0):.2%}")
        self.result_text.append(f"  • PSNR: {similarity.get('psnr', 0):.2f} dB")
        self.result_text.append(f"  • SSIM: {similarity.get('ssim', 0):.4f}")
        self.result_text.append("")
        
        # 质量评估
        quality = result.get('quality', {})
        self.result_text.append("📈 质量评估:")
        self.result_text.append(f"  • 颜色保真度: {quality.get('color_fidelity', 0):.2%}")
        self.result_text.append(f"  • 结构保持度: {quality.get('structural_similarity', 0):.2%}")
        self.result_text.append("")
        
        # 建议
        recommendations = result.get('recommendations', [])
        if recommendations:
            self.result_text.append("💡 优化建议:")
            for rec in recommendations:
                self.result_text.append(f"  • {rec}")
        
        self.result_text.append("")
        self.result_text.append("=" * 50)
        self.result_text.append("✅ 对比完成")
    
    def on_error(self, error_msg: str):
        """对比失败"""
        self.progress_bar.setVisible(False)
        self.compare_btn.setEnabled(True)
        
        self.result_text.append(f"\n❌ 错误: {error_msg}")
        
        QMessageBox.critical(self, "错误", error_msg)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        event.accept()

