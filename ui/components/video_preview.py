from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QSlider, QFileDialog, QMessageBox,
                           QGroupBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QIcon, QPixmap
# 移除多媒体导入
# from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
# from PyQt6.QtMultimediaWidgets import QVideoWidget
import os
import sys
from pathlib import Path

# 导入必要的项目模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

class VideoPreview(QWidget):
    """视频预览组件 - 简化版"""
    
    def __init__(self):
        super().__init__()
        self.current_segments = []
        self.current_segment_index = -1
        self.subtitle_timer = QTimer()
        self.subtitle_timer.timeout.connect(self.update_subtitle_display)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 替换视频播放区域为占位符
        self.video_placeholder = QLabel("视频预览区域 (需要安装PyQt6多媒体组件)")
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setStyleSheet("""
            background-color: #222;
            color: white;
            font-size: 16px;
            padding: 100px;
            border-radius: 4px;
        """)
        self.video_placeholder.setMinimumHeight(360)
        layout.addWidget(self.video_placeholder)
        
        # 字幕显示区域
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 16px;
        """)
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        
        # 控制区域（简化版）
        controls_layout = QHBoxLayout()
        
        # 播放/暂停按钮
        self.play_button = QPushButton("播放")
        self.play_button.setEnabled(False)
        controls_layout.addWidget(self.play_button)
        
        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        # 模拟进度条
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setEnabled(False)
        controls_layout.addWidget(self.position_slider)
        
        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # 剧本控制区域
        screenplay_group = QGroupBox("剧本预览控制")
        screenplay_layout = QVBoxLayout()
        
        # 字幕切换
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一句")
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.goto_prev_segment)
        nav_layout.addWidget(self.prev_button)
        
        self.segment_combo = QComboBox()
        self.segment_combo.setEnabled(False)
        self.segment_combo.currentIndexChanged.connect(self.on_segment_selected)
        nav_layout.addWidget(self.segment_combo)
        
        self.next_button = QPushButton("下一句")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.goto_next_segment)
        nav_layout.addWidget(self.next_button)
        
        screenplay_layout.addLayout(nav_layout)
        
        # 加载视频按钮
        self.load_button = QPushButton("选择字幕文件")
        self.load_button.clicked.connect(self.load_subtitle)
        screenplay_layout.addWidget(self.load_button)
        
        screenplay_group.setLayout(screenplay_layout)
        layout.addWidget(screenplay_group)
        
        self.setLayout(layout)
    
    def load_video(self):
        """加载视频文件 - 简化版"""
        QMessageBox.information(self, "提示", "视频预览功能需要安装PyQt6多媒体组件")
    
    def load_subtitle(self):
        """加载字幕文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "字幕文件 (*.srt *.vtt);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        # 更新UI
        self.subtitle_label.setText("已加载字幕文件")
        
        # 启用导航按钮
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        QMessageBox.information(self, "字幕加载成功", "字幕文件已加载。视频预览功能需要安装PyQt6多媒体组件。")
    
    def load_screenplay(self, data):
        """加载剧本数据"""
        if not data:
            return
            
        self.current_segments = data.get("screenplay", [])
        self.current_segment_index = -1
        
        # 更新控件
        self.update_subtitle_controls()
    
    def update_subtitle_controls(self):
        """更新字幕控制UI"""
        # 清空并重新填充下拉框
        self.segment_combo.clear()
        
        for i, segment in enumerate(self.current_segments):
            text = segment.get("text", "")
            # 裁剪过长的文本
            display_text = text[:30] + "..." if len(text) > 30 else text
            self.segment_combo.addItem(f"{i+1}. {display_text}")
        
        # 启用字幕导航控件
        self.segment_combo.setEnabled(True)
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        # 显示第一个字幕
        if self.current_segments:
            self.current_segment_index = 0
            self.segment_combo.setCurrentIndex(0)
            self.subtitle_label.setText(self.current_segments[0].get("text", ""))
    
    def goto_prev_segment(self):
        """跳转到上一个字幕段落"""
        if not self.current_segments or self.current_segment_index <= 0:
            return
            
        self.current_segment_index -= 1
        self.segment_combo.setCurrentIndex(self.current_segment_index)
        self._goto_current_segment()
    
    def goto_next_segment(self):
        """跳转到下一个字幕段落"""
        if not self.current_segments or self.current_segment_index >= len(self.current_segments) - 1:
            return
            
        self.current_segment_index += 1
        self.segment_combo.setCurrentIndex(self.current_segment_index)
        self._goto_current_segment()
    
    def on_segment_selected(self, index):
        """字幕段落选择回调"""
        if index < 0 or index >= len(self.current_segments):
            return
            
        self.current_segment_index = index
        self._goto_current_segment()
    
    def _goto_current_segment(self):
        """跳转到当前选择的字幕段落"""
        if self.current_segment_index < 0 or self.current_segment_index >= len(self.current_segments):
            return
            
        segment = self.current_segments[self.current_segment_index]
        # 显示字幕
        self.subtitle_label.setText(segment.get("text", ""))
        
        # 显示时间信息
        start_time = self._format_time(segment.get("start_time", 0) * 1000)
        end_time = self._format_time(segment.get("end_time", 0) * 1000)
        self.time_label.setText(f"{start_time} / {end_time}")
    
    def update_subtitle_display(self):
        """定时更新字幕显示 - 简化版"""
        pass
    
    def _format_time(self, milliseconds):
        """将毫秒转换为时间字符串 (MM:SS)"""
        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication([])
    
    widget = VideoPreview()
    
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