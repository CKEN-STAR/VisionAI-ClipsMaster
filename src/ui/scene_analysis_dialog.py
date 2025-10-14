#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
场景分析对话框

提供可视化的场景分析结果展示界面,支持查看场景列表、关键帧和导出数据。
"""

import os
import json
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox, QFileDialog,
    QMessageBox, QProgressDialog, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QImage

from src.utils.log_handler import get_logger

logger = get_logger("scene_analysis_dialog")

# 延迟导入SceneAnalyzer和Scene,避免cv2循环导入
SceneAnalyzer = None
Scene = None

def _lazy_import_scene_analyzer():
    """延迟导入SceneAnalyzer"""
    global SceneAnalyzer, Scene
    if SceneAnalyzer is None:
        try:
            from src.alignment.scene_analyzer import SceneAnalyzer as SA, Scene as S
            SceneAnalyzer = SA
            Scene = S
            logger.info("SceneAnalyzer导入成功")
        except ImportError as e:
            logger.warning(f"SceneAnalyzer导入失败: {e}")
    return SceneAnalyzer, Scene

logger = get_logger("scene_analysis_dialog")

# 延迟导入cv2和numpy
cv2 = None
np = None

def _lazy_import_cv2():
    """延迟导入cv2"""
    global cv2, np
    if cv2 is None:
        try:
            import cv2 as cv2_module
            import numpy as np_module
            cv2 = cv2_module
            np = np_module
        except ImportError as e:
            logger.warning(f"cv2或numpy导入失败: {e}")
    return cv2, np


class SceneAnalysisDialog(QDialog):
    """场景分析对话框"""
    
    # 信号
    analysis_completed = pyqtSignal(list)  # 分析完成信号
    
    def __init__(self, parent=None):
        """初始化场景分析对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("场景分析")
        self.resize(900, 600)

        # 延迟导入并创建场景分析器
        SA, _ = _lazy_import_scene_analyzer()
        if SA is not None:
            self.analyzer = SA(
                min_scene_duration=1.0,
                scene_threshold=30.0,
                use_external_models=False
            )
        else:
            self.analyzer = None

        # 分析结果
        self.scenes: List = []
        self.video_path: Optional[str] = None
        
        # 初始化UI
        self._init_ui()
        
        logger.info("场景分析对话框初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("场景分析")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明文字
        desc_label = QLabel(
            "自动检测视频中的场景变化,分析场景类型(日景/夜景/室内/室外),提取关键帧。"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(desc_label)
        
        # 视频选择区域
        video_group = self._create_video_selection()
        layout.addWidget(video_group)
        
        # 场景列表区域
        scenes_group = self._create_scenes_table()
        layout.addWidget(scenes_group)
        
        # 底部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
    
    def _create_video_selection(self) -> QGroupBox:
        """创建视频选择区域
        
        Returns:
            QGroupBox: 视频选择组件
        """
        group = QGroupBox("视频文件")
        layout = QHBoxLayout(group)
        
        # 视频路径显示
        self.video_path_label = QLabel("未选择视频")
        self.video_path_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.video_path_label)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_video)
        layout.addWidget(browse_btn)
        
        # 分析按钮
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.analyze_btn.clicked.connect(self._analyze_video)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        return group
    
    def _create_scenes_table(self) -> QGroupBox:
        """创建场景列表区域
        
        Returns:
            QGroupBox: 场景列表组件
        """
        group = QGroupBox("场景列表")
        layout = QVBoxLayout(group)
        
        # 场景表格
        self.scenes_table = QTableWidget()
        self.scenes_table.setColumnCount(6)
        self.scenes_table.setHorizontalHeaderLabels([
            "场景编号", "开始时间", "结束时间", "持续时间", "场景类型", "位置"
        ])
        
        # 设置列宽
        header = self.scenes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        # 设置表格属性
        self.scenes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.scenes_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.scenes_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.scenes_table)
        
        # 统计信息
        self.stats_label = QLabel("场景数量: 0")
        self.stats_label.setStyleSheet("padding: 5px; font-weight: bold;")
        layout.addWidget(self.stats_label)
        
        return group
    
    def _create_toolbar(self) -> QGroupBox:
        """创建底部工具栏
        
        Returns:
            QGroupBox: 工具栏组件
        """
        group = QGroupBox()
        layout = QHBoxLayout(group)
        
        # 导出JSON
        export_json_btn = QPushButton("导出JSON")
        export_json_btn.clicked.connect(self._export_json)
        layout.addWidget(export_json_btn)
        
        # 导出报告
        export_report_btn = QPushButton("导出报告")
        export_report_btn.clicked.connect(self._export_report)
        layout.addWidget(export_report_btn)
        
        layout.addStretch()
        
        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return group
    
    def _browse_video(self):
        """浏览视频文件"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )
        
        if file:
            self.video_path = file
            self.video_path_label.setText(os.path.basename(file))
            self.analyze_btn.setEnabled(True)
            logger.info(f"选择视频文件: {file}")
    
    def set_video_path(self, video_path: str):
        """设置视频路径
        
        Args:
            video_path: 视频文件路径
        """
        if os.path.exists(video_path):
            self.video_path = video_path
            self.video_path_label.setText(os.path.basename(video_path))
            self.analyze_btn.setEnabled(True)
            logger.info(f"设置视频路径: {video_path}")
    
    def _analyze_video(self):
        """分析视频"""
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "警告", "请先选择有效的视频文件")
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在分析视频场景...", "取消", 0, 0, self)
        progress.setWindowTitle("分析中")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            # 执行场景分析
            self.scenes = self.analyzer.analyze_video(self.video_path)
            
            # 更新表格
            self._update_scenes_table()
            
            # 更新统计信息
            self._update_stats()
            
            # 发送信号
            self.analysis_completed.emit(self.scenes)
            
            QMessageBox.information(
                self,
                "分析完成",
                f"成功分析 {len(self.scenes)} 个场景"
            )
            
            logger.info(f"场景分析完成: {len(self.scenes)} 个场景")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"场景分析失败: {e}")
            logger.error(f"场景分析失败: {e}")
        finally:
            progress.close()
    
    def _update_scenes_table(self):
        """更新场景表格"""
        self.scenes_table.setRowCount(len(self.scenes))
        
        for i, scene in enumerate(self.scenes):
            # 场景编号
            self.scenes_table.setItem(i, 0, QTableWidgetItem(f"场景 {i+1}"))
            
            # 开始时间
            start_time = f"{scene.start_time:.2f}s"
            self.scenes_table.setItem(i, 1, QTableWidgetItem(start_time))
            
            # 结束时间
            end_time = f"{scene.end_time:.2f}s"
            self.scenes_table.setItem(i, 2, QTableWidgetItem(end_time))
            
            # 持续时间
            duration = f"{scene.end_time - scene.start_time:.2f}s"
            self.scenes_table.setItem(i, 3, QTableWidgetItem(duration))
            
            # 场景类型
            scene_type = scene.scene_type or "未知"
            self.scenes_table.setItem(i, 4, QTableWidgetItem(scene_type))
            
            # 位置
            location = scene.location or "未知"
            self.scenes_table.setItem(i, 5, QTableWidgetItem(location))
    
    def _update_stats(self):
        """更新统计信息"""
        total_scenes = len(self.scenes)
        
        # 统计场景类型
        scene_types = {}
        for scene in self.scenes:
            scene_type = scene.scene_type or "未知"
            scene_types[scene_type] = scene_types.get(scene_type, 0) + 1
        
        # 生成统计文本
        stats_text = f"场景数量: {total_scenes}"
        if scene_types:
            stats_text += " | "
            stats_text += ", ".join([f"{k}: {v}" for k, v in scene_types.items()])
        
        self.stats_label.setText(stats_text)
    
    def _export_json(self):
        """导出JSON"""
        if not self.scenes:
            QMessageBox.warning(self, "警告", "没有可导出的场景数据")
            return
        
        file, _ = QFileDialog.getSaveFileName(
            self,
            "导出场景数据",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file:
            return
        
        try:
            # 转换为字典列表
            scenes_data = []
            for i, scene in enumerate(self.scenes):
                scene_dict = {
                    "scene_id": i + 1,
                    "start_time": scene.start_time,
                    "end_time": scene.end_time,
                    "duration": scene.end_time - scene.start_time,
                    "scene_type": scene.scene_type,
                    "location": scene.location,
                    "confidence": scene.confidence,
                    "text": scene.text,
                    "characters": scene.characters,
                    "metadata": scene.metadata
                }
                scenes_data.append(scene_dict)
            
            # 保存JSON
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(scenes_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", f"成功导出 {len(scenes_data)} 个场景")
            logger.info(f"导出场景数据: {file}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
            logger.error(f"导出场景数据失败: {e}")
    
    def _export_report(self):
        """导出报告"""
        if not self.scenes:
            QMessageBox.warning(self, "警告", "没有可导出的场景数据")
            return
        
        file, _ = QFileDialog.getSaveFileName(
            self,
            "导出场景分析报告",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if not file:
            return
        
        try:
            # 生成报告
            report = self._generate_report()
            
            # 保存报告
            with open(file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            QMessageBox.information(self, "成功", "报告导出成功")
            logger.info(f"导出场景分析报告: {file}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")
            logger.error(f"导出报告失败: {e}")
    
    def _generate_report(self) -> str:
        """生成场景分析报告
        
        Returns:
            str: 报告文本
        """
        report = "=" * 60 + "\n"
        report += "场景分析报告\n"
        report += "=" * 60 + "\n\n"
        
        report += f"视频文件: {os.path.basename(self.video_path)}\n"
        report += f"场景数量: {len(self.scenes)}\n\n"
        
        # 统计场景类型
        scene_types = {}
        for scene in self.scenes:
            scene_type = scene.scene_type or "未知"
            scene_types[scene_type] = scene_types.get(scene_type, 0) + 1
        
        report += "场景类型统计:\n"
        for scene_type, count in scene_types.items():
            report += f"  {scene_type}: {count}\n"
        
        report += "\n" + "-" * 60 + "\n\n"
        
        # 详细场景列表
        report += "详细场景列表:\n\n"
        for i, scene in enumerate(self.scenes):
            report += f"场景 {i+1}:\n"
            report += f"  时间范围: {scene.start_time:.2f}s - {scene.end_time:.2f}s\n"
            report += f"  持续时间: {scene.end_time - scene.start_time:.2f}s\n"
            report += f"  场景类型: {scene.scene_type or '未知'}\n"
            report += f"  位置: {scene.location or '未知'}\n"
            report += f"  置信度: {scene.confidence:.2f}\n"
            if scene.text:
                report += f"  文本: {scene.text}\n"
            report += "\n"
        
        return report

