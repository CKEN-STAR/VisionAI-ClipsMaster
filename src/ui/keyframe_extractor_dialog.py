#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键帧提取器对话框
提供独立的关键帧提取工具,支持智能推荐和手动控制
"""

import os
import json
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QRadioButton, QButtonGroup, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QProgressBar, QTabWidget, QTextEdit, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

from src.utils.log_handler import get_logger

logger = get_logger("keyframe_extractor_dialog")

# 延迟导入,避免cv2循环导入
extract_keyframes = None
cv2 = None
np = None

def _lazy_import_keyframe_extractor():
    """延迟导入关键帧提取器"""
    global extract_keyframes, cv2, np
    if extract_keyframes is None:
        try:
            from src.alignment import extract_keyframes as ekf
            import cv2 as cv
            import numpy as npy
            extract_keyframes = ekf
            cv2 = cv
            np = npy
            logger.info("关键帧提取器导入成功")
        except ImportError as e:
            logger.warning(f"关键帧提取器导入失败: {e}")
    return extract_keyframes


class KeyframeExtractionWorker(QThread):
    """关键帧提取后台线程"""
    
    started = pyqtSignal()
    progress = pyqtSignal(int, str)  # 进度百分比, 状态消息
    finished = pyqtSignal(list)  # 提取的关键帧列表
    error = pyqtSignal(str)  # 错误消息
    
    def __init__(self, video_path: str, method: str, num_frames: int, threshold: float, save_frames: bool, output_dir: str):
        super().__init__()
        self.video_path = video_path
        self.method = method
        self.num_frames = num_frames
        self.threshold = threshold
        self.save_frames = save_frames
        self.output_dir = output_dir
        self._is_cancelled = False
    
    def run(self):
        """执行关键帧提取"""
        try:
            self.started.emit()
            self.progress.emit(0, "开始提取关键帧...")
            
            # 延迟导入
            ekf = _lazy_import_keyframe_extractor()
            if ekf is None:
                self.error.emit("关键帧提取器未安装")
                return
            
            # 提取关键帧
            self.progress.emit(20, f"使用{self.method}方法提取...")
            keyframes = ekf(
                video_path=self.video_path,
                method=self.method,
                num_frames=self.num_frames,
                threshold=self.threshold,
                save_frames=self.save_frames,
                output_dir=self.output_dir if self.save_frames else None
            )
            
            if self._is_cancelled:
                self.progress.emit(100, "已取消")
                return
            
            self.progress.emit(100, f"提取完成: {len(keyframes)}帧")
            self.finished.emit(keyframes)
            
        except Exception as e:
            logger.error(f"关键帧提取失败: {e}")
            self.error.emit(str(e))
    
    def cancel(self):
        """取消提取"""
        self._is_cancelled = True


class KeyframeExtractorDialog(QDialog):
    """关键帧提取器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关键帧提取器")
        self.resize(900, 700)
        
        self.video_path: Optional[str] = None
        self.keyframes: List[Dict[str, Any]] = []
        self.worker: Optional[KeyframeExtractionWorker] = None
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("🎞️ 关键帧提取器")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 rgba(102, 126, 234, 0.1),
                                          stop: 1 rgba(118, 75, 162, 0.1));
                border-radius: 8px;
            }
        """)
        layout.addWidget(title_label)

        # 创建标签页
        tab_widget = QTabWidget()

        # 提取工具标签页
        extract_tab = self._create_extract_tab()
        tab_widget.addTab(extract_tab, "提取工具")

        # 功能说明标签页
        help_tab = self._create_help_tab()
        tab_widget.addTab(help_tab, "功能说明")

        layout.addWidget(tab_widget)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _create_extract_tab(self):
        """创建提取工具标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 视频文件选择
        file_group = QGroupBox("视频文件")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("未选择视频")
        self.file_label.setStyleSheet("color: #7f8c8d;")
        file_layout.addWidget(self.file_label, 1)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_video)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_group)
        
        # 提取方法
        method_group = QGroupBox("提取方法")
        method_layout = QVBoxLayout(method_group)
        
        self.method_group = QButtonGroup(self)
        
        self.uniform_radio = QRadioButton("均匀提取 - 按固定间隔提取帧(适合快速预览)")
        self.uniform_radio.setChecked(True)
        self.method_group.addButton(self.uniform_radio, 0)
        method_layout.addWidget(self.uniform_radio)
        
        self.difference_radio = QRadioButton("差异提取 - 基于帧间差异提取(适合动作检测)")
        self.method_group.addButton(self.difference_radio, 1)
        method_layout.addWidget(self.difference_radio)
        
        self.scene_radio = QRadioButton("场景变化 - 基于场景切换提取(适合场景分割)")
        self.method_group.addButton(self.scene_radio, 2)
        method_layout.addWidget(self.scene_radio)
        
        layout.addWidget(method_group)
        
        # 参数设置
        param_group = QGroupBox("参数设置")
        param_layout = QVBoxLayout(param_group)
        
        # 提取数量
        num_layout = QHBoxLayout()
        num_layout.addWidget(QLabel("提取数量:"))
        self.num_frames_spin = QSpinBox()
        self.num_frames_spin.setRange(1, 100)
        self.num_frames_spin.setValue(10)
        self.num_frames_spin.setSuffix(" 帧")
        num_layout.addWidget(self.num_frames_spin)
        num_layout.addWidget(QLabel("(仅均匀提取)"))
        num_layout.addStretch()
        param_layout.addLayout(num_layout)
        
        # 差异阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("差异阈值:"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(1.0, 100.0)
        self.threshold_spin.setValue(30.0)
        self.threshold_spin.setSingleStep(1.0)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addWidget(QLabel("(差异提取和场景变化)"))
        threshold_layout.addStretch()
        param_layout.addLayout(threshold_layout)
        
        layout.addWidget(param_group)
        
        # 输出选项
        output_group = QGroupBox("输出选项")
        output_layout = QVBoxLayout(output_group)
        
        self.save_frames_check = QCheckBox("保存关键帧图像")
        self.save_frames_check.setChecked(False)
        output_layout.addWidget(self.save_frames_check)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_label = QLabel("output/keyframes")
        dir_layout.addWidget(self.output_dir_label, 1)
        browse_dir_btn = QPushButton("浏览...")
        browse_dir_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_dir_btn)
        output_layout.addLayout(dir_layout)
        
        layout.addWidget(output_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #3498db; font-weight: bold;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # 结果表格
        result_label = QLabel("提取结果:")
        result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(result_label)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["帧编号", "时间戳", "差异分数", "方法"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setMinimumHeight(300)  # 设置最小高度,确保能显示多行
        layout.addWidget(self.result_table, 1)  # 添加拉伸因子,让表格占据更多空间

        # 按钮
        button_layout = QHBoxLayout()

        self.extract_btn = QPushButton("开始提取")
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.extract_btn.clicked.connect(self._start_extraction)
        button_layout.addWidget(self.extract_btn)

        self.export_btn = QPushButton("导出列表")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_results)
        button_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self._clear_results)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        return tab

    def _create_help_tab(self):
        """创建功能说明标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 功能说明文本
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
            <h2 style="color: #2c3e50;">🎞️ 关键帧提取器功能说明</h2>

            <h3 style="color: #3498db;">📖 功能概述</h3>
            <p>关键帧提取器可以从视频中智能提取关键帧，帮助您快速了解视频内容、检测动作变化、分析场景切换。</p>

            <h3 style="color: #3498db;">🔧 三种提取方法</h3>

            <h4 style="color: #27ae60;">1️⃣ 均匀提取 (Uniform)</h4>
            <p><b>原理</b>：按固定时间间隔提取帧</p>
            <p><b>适用场景</b>：</p>
            <ul>
                <li>快速预览视频内容</li>
                <li>生成视频缩略图</li>
                <li>制作视频摘要</li>
            </ul>
            <p><b>参数</b>：提取数量 (建议: 10-30帧)</p>

            <h4 style="color: #27ae60;">2️⃣ 差异提取 (Difference)</h4>
            <p><b>原理</b>：基于相邻帧之间的差异程度提取</p>
            <p><b>适用场景</b>：</p>
            <ul>
                <li>检测动作变化</li>
                <li>识别运动物体</li>
                <li>分析视频动态内容</li>
            </ul>
            <p><b>参数</b>：差异阈值 (建议: 30.0-40.0)</p>

            <h4 style="color: #27ae60;">3️⃣ 场景变化 (Scene)</h4>
            <p><b>原理</b>：基于场景切换检测提取</p>
            <p><b>适用场景</b>：</p>
            <ul>
                <li>场景分割</li>
                <li>镜头切换检测</li>
                <li>视频结构分析</li>
            </ul>
            <p><b>参数</b>：差异阈值 (建议: 25.0-35.0)</p>

            <h3 style="color: #3498db;">💡 智能自动化</h3>
            <p>在工作流程中，关键帧提取会根据视频时长自动选择最优方法：</p>
            <ul>
                <li><b>短视频 (&lt;5分钟)</b>: 均匀提取, 10帧</li>
                <li><b>中等视频 (5-30分钟)</b>: 差异提取, 阈值35.0</li>
                <li><b>长视频 (&gt;30分钟)</b>: 场景变化, 阈值30.0</li>
            </ul>

            <h3 style="color: #3498db;">📤 导出功能</h3>
            <p>提取完成后，您可以：</p>
            <ul>
                <li><b>保存关键帧图像</b>: 将关键帧保存为图片文件</li>
                <li><b>导出JSON格式</b>: 结构化数据，便于程序处理</li>
                <li><b>导出CSV格式</b>: 表格数据，便于Excel分析</li>
            </ul>

            <h3 style="color: #3498db;">🎯 使用建议</h3>
            <ul>
                <li><b>普通用户</b>: 使用工作流程自动提取，无需手动操作</li>
                <li><b>高级用户</b>: 使用独立工具精细控制，调整参数优化结果</li>
                <li><b>参数调整</b>: 如果提取结果过多或过少，可适当调整阈值</li>
                <li><b>性能优化</b>: 处理大视频时，建议先用均匀提取快速预览</li>
            </ul>

            <h3 style="color: #3498db;">⌨️ 快捷键</h3>
            <p><b>Ctrl+K</b>: 打开关键帧提取器</p>

            <hr style="border: 1px solid #ecf0f1; margin: 20px 0;">

            <p style="color: #7f8c8d; font-size: 12px;">
                <b>提示</b>: 关键帧提取是视频分析的基础功能，配合场景分析和剧情分析使用效果更佳。
            </p>
        </div>
        """)

        layout.addWidget(help_text)

        return tab
    
    def _browse_video(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*.*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
            logger.info(f"选择视频文件: {file_path}")
    
    def _browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_label.text()
        )
        
        if dir_path:
            self.output_dir_label.setText(dir_path)
            logger.info(f"选择输出目录: {dir_path}")
    
    def _start_extraction(self):
        """开始提取关键帧"""
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
        
        if not os.path.exists(self.video_path):
            QMessageBox.critical(self, "错误", "视频文件不存在")
            return
        
        # 获取参数
        method_id = self.method_group.checkedId()
        method = ['uniform', 'difference', 'scene'][method_id]
        num_frames = self.num_frames_spin.value()
        threshold = self.threshold_spin.value()
        save_frames = self.save_frames_check.isChecked()
        output_dir = self.output_dir_label.text()
        
        # 创建输出目录
        if save_frames and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 禁用按钮
        self.extract_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        
        # 创建并启动后台线程
        self.worker = KeyframeExtractionWorker(
            self.video_path, method, num_frames, threshold, save_frames, output_dir
        )
        self.worker.started.connect(self._on_extraction_started)
        self.worker.progress.connect(self._on_extraction_progress)
        self.worker.finished.connect(self._on_extraction_finished)
        self.worker.error.connect(self._on_extraction_error)
        self.worker.start()
    
    def _on_extraction_started(self):
        """提取开始"""
        logger.info("关键帧提取开始")
    
    def _on_extraction_progress(self, progress: int, message: str):
        """提取进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_extraction_finished(self, keyframes: List[Dict[str, Any]]):
        """提取完成"""
        self.keyframes = keyframes
        self._display_results()
        
        self.extract_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        QMessageBox.information(
            self,
            "提取完成",
            f"成功提取 {len(keyframes)} 个关键帧"
        )
        
        logger.info(f"关键帧提取完成: {len(keyframes)}帧")
    
    def _on_extraction_error(self, error_message: str):
        """提取错误"""
        self.extract_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        QMessageBox.critical(
            self,
            "提取失败",
            f"关键帧提取失败:\n{error_message}"
        )
        
        logger.error(f"关键帧提取失败: {error_message}")
    
    def _display_results(self):
        """显示提取结果"""
        self.result_table.setRowCount(len(self.keyframes))
        
        for i, kf in enumerate(self.keyframes):
            # 帧编号
            self.result_table.setItem(i, 0, QTableWidgetItem(str(kf.get('frame_idx', i))))
            
            # 时间戳
            timestamp = kf.get('timestamp', 0.0)
            self.result_table.setItem(i, 1, QTableWidgetItem(f"{timestamp:.2f}s"))
            
            # 差异分数
            diff_score = kf.get('diff_score', 0.0)
            self.result_table.setItem(i, 2, QTableWidgetItem(f"{diff_score:.2f}" if diff_score > 0 else "-"))
            
            # 方法
            method = kf.get('method', 'unknown')
            self.result_table.setItem(i, 3, QTableWidgetItem(method))
    
    def _export_results(self):
        """导出结果列表"""
        if not self.keyframes:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出结果",
            "keyframes.json",
            "JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.json'):
                # 导出为JSON
                export_data = []
                for kf in self.keyframes:
                    export_data.append({
                        'frame_idx': kf.get('frame_idx', 0),
                        'timestamp': kf.get('timestamp', 0.0),
                        'diff_score': kf.get('diff_score', 0.0),
                        'method': kf.get('method', 'unknown')
                    })
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif file_path.endswith('.csv'):
                # 导出为CSV
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['帧编号', '时间戳', '差异分数', '方法'])
                    for kf in self.keyframes:
                        writer.writerow([
                            kf.get('frame_idx', 0),
                            f"{kf.get('timestamp', 0.0):.2f}",
                            f"{kf.get('diff_score', 0.0):.2f}",
                            kf.get('method', 'unknown')
                        ])
            
            QMessageBox.information(self, "导出成功", f"结果已导出到:\n{file_path}")
            logger.info(f"结果已导出: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出失败:\n{str(e)}")
            logger.error(f"导出失败: {e}")
    
    def _clear_results(self):
        """清除结果"""
        self.keyframes = []
        self.result_table.setRowCount(0)
        self.export_btn.setEnabled(False)
        logger.info("结果已清除")
    
    def set_video_path(self, video_path: str):
        """设置视频路径"""
        if os.path.exists(video_path):
            self.video_path = video_path
            self.file_label.setText(os.path.basename(video_path))
            self.file_label.setStyleSheet("color: #2c3e50; font-weight: bold;")

