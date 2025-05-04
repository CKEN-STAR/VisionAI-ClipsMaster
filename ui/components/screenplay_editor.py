from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QSplitter, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QGroupBox,
                           QLineEdit, QFileDialog, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QTextCursor, QColor, QTextCharFormat
import os
import sys
import json
from pathlib import Path

# 导入必要的项目模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.core.screenplay_engineer import ScreenplayEngineer

class ScreenplayEditor(QWidget):
    """剧本编辑器组件"""
    
    def __init__(self):
        super().__init__()
        self.screenplay_data = None
        self.current_segments = []
        self.engineer = ScreenplayEngineer()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 剧本信息
        info_layout = QHBoxLayout()
        self.info_label = QLabel("尚未加载剧本")
        info_layout.addWidget(self.info_label)
        
        # 保存按钮
        self.save_btn = QPushButton("导出SRT")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.export_srt)
        info_layout.addWidget(self.save_btn)
        
        layout.addLayout(info_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：片段表格
        self.segments_table = QTableWidget(0, 3)
        self.segments_table.setHorizontalHeaderLabels(["时间", "内容", "情感"])
        self.segments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.segments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.segments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.segments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.segments_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.segments_table.cellClicked.connect(self.on_segment_selected)
        
        splitter.addWidget(self.segments_table)
        
        # 右侧：编辑区域
        edit_group = QGroupBox("片段编辑")
        edit_layout = QVBoxLayout()
        
        # 文字编辑
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("选择左侧片段进行编辑...")
        self.text_edit.setEnabled(False)
        edit_layout.addWidget(self.text_edit)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("更新片段")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self.update_segment)
        btn_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("删除片段")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_segment)
        btn_layout.addWidget(self.delete_btn)
        
        edit_layout.addLayout(btn_layout)
        
        # 时间设置
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("开始时间:"))
        self.start_time_edit = QLineEdit()
        self.start_time_edit.setEnabled(False)
        self.start_time_edit.setPlaceholderText("00:00:00.000")
        time_layout.addWidget(self.start_time_edit)
        
        time_layout.addWidget(QLabel("结束时间:"))
        self.end_time_edit = QLineEdit()
        self.end_time_edit.setEnabled(False)
        self.end_time_edit.setPlaceholderText("00:00:00.000")
        time_layout.addWidget(self.end_time_edit)
        
        edit_layout.addLayout(time_layout)
        
        edit_group.setLayout(edit_layout)
        splitter.addWidget(edit_group)
        
        # 设置分割器初始大小
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def load_screenplay(self, data):
        """加载剧本数据"""
        if not data:
            QMessageBox.warning(self, "加载错误", "剧本数据为空")
            return
            
        self.screenplay_data = data
        self.current_segments = data.get("screenplay", [])
        
        # 更新信息标签
        segments_count = len(self.current_segments)
        self.info_label.setText(f"已加载剧本: {segments_count} 个片段")
        
        # 填充表格
        self.populate_segments_table()
        
        # 启用保存按钮
        self.save_btn.setEnabled(True)
    
    def populate_segments_table(self):
        """填充片段表格"""
        self.segments_table.setRowCount(0)  # 清空表格
        
        for i, segment in enumerate(self.current_segments):
            self.segments_table.insertRow(i)
            
            # 时间列
            start_time = self._format_time(segment.get("start_time", 0))
            end_time = self._format_time(segment.get("end_time", 0))
            time_item = QTableWidgetItem(f"{start_time} → {end_time}")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.segments_table.setItem(i, 0, time_item)
            
            # 内容列
            text_item = QTableWidgetItem(segment.get("text", ""))
            self.segments_table.setItem(i, 1, text_item)
            
            # 情感列
            sentiment = segment.get("sentiment", {})
            label = sentiment.get("label", "NEUTRAL")
            intensity = sentiment.get("intensity", 0.5)
            
            # 根据情感设置颜色
            sentiment_item = QTableWidgetItem(f"{label} ({intensity:.2f})")
            if label == "POSITIVE":
                sentiment_item.setBackground(QColor(200, 255, 200))  # 浅绿色
            elif label == "NEGATIVE":
                sentiment_item.setBackground(QColor(255, 200, 200))  # 浅红色
            sentiment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.segments_table.setItem(i, 2, sentiment_item)
    
    def on_segment_selected(self, row, column):
        """当选中片段时"""
        if 0 <= row < len(self.current_segments):
            segment = self.current_segments[row]
            
            # 填充编辑区域
            self.text_edit.setEnabled(True)
            self.text_edit.setText(segment.get("text", ""))
            
            # 更新时间输入框
            self.start_time_edit.setEnabled(True)
            self.end_time_edit.setEnabled(True)
            self.start_time_edit.setText(self._format_time(segment.get("start_time", 0)))
            self.end_time_edit.setText(self._format_time(segment.get("end_time", 0)))
            
            # 启用编辑按钮
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
    
    def update_segment(self):
        """更新当前选中的片段"""
        selected_rows = self.segments_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_segments):
            # 获取编辑后的内容
            new_text = self.text_edit.toPlainText()
            new_start_time = self._parse_time(self.start_time_edit.text())
            new_end_time = self._parse_time(self.end_time_edit.text())
            
            # 更新片段数据
            self.current_segments[row]["text"] = new_text
            self.current_segments[row]["start_time"] = new_start_time
            self.current_segments[row]["end_time"] = new_end_time
            
            # 更新表格
            self.segments_table.item(row, 0).setText(
                f"{self._format_time(new_start_time)} → {self._format_time(new_end_time)}"
            )
            self.segments_table.item(row, 1).setText(new_text)
            
            QMessageBox.information(self, "更新成功", "片段已更新")
    
    def delete_segment(self):
        """删除当前选中的片段"""
        selected_rows = self.segments_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_segments):
            # 确认删除
            result = QMessageBox.question(
                self, "确认删除", 
                "确定要删除这个片段吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                # 删除片段
                del self.current_segments[row]
                
                # 更新表格
                self.segments_table.removeRow(row)
                
                # 清空编辑区域
                self.text_edit.clear()
                self.text_edit.setEnabled(False)
                self.start_time_edit.clear()
                self.start_time_edit.setEnabled(False)
                self.end_time_edit.clear()
                self.end_time_edit.setEnabled(False)
                self.update_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
                # 更新信息标签
                segments_count = len(self.current_segments)
                self.info_label.setText(f"已加载剧本: {segments_count} 个片段")
    
    def export_srt(self):
        """导出SRT字幕文件"""
        if not self.current_segments:
            QMessageBox.warning(self, "导出错误", "没有剧本数据可导出")
            return
            
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出SRT文件", "", "SRT文件 (*.srt);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 使用ScreenplayEngineer导出SRT
            success = self.engineer.export_srt(self.current_segments, file_path)
            
            if success:
                QMessageBox.information(self, "导出成功", f"SRT文件已保存至: {file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "保存SRT文件时发生错误")
                
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"导出过程中发生错误:\n{str(e)}")
    
    def _format_time(self, seconds):
        """将秒转换为时间字符串 (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def _parse_time(self, time_str):
        """将时间字符串解析为秒"""
        try:
            # 解析 HH:MM:SS.mmm 格式
            parts = time_str.split(':')
            if len(parts) != 3:
                return 0.0
                
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication([])
    
    widget = ScreenplayEditor()
    
    # 模拟加载剧本数据
    test_data = {
        "screenplay": [
            {
                "id": 1,
                "start_time": 0.0,
                "end_time": 5.0,
                "text": "这是第一个片段",
                "sentiment": {"label": "NEUTRAL", "intensity": 0.5}
            },
            {
                "id": 2,
                "start_time": 5.5,
                "end_time": 10.0,
                "text": "这是第二个片段，情感积极",
                "sentiment": {"label": "POSITIVE", "intensity": 0.8}
            },
            {
                "id": 3,
                "start_time": 10.5,
                "end_time": 15.0,
                "text": "这是第三个片段，情感消极",
                "sentiment": {"label": "NEGATIVE", "intensity": 0.7}
            }
        ]
    }
    
    widget.load_screenplay(test_data)
    widget.show()
    
    app.exec() 