#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工作流程进度对话框
显示8步工作流程的实时进度
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QTextEdit, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class WorkflowProgressDialog(QDialog):
    """工作流程进度对话框"""
    
    # 信号定义
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("工作流程进度")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.current_step = 0
        self.total_steps = 9  # 从8步增加到9步(添加关键帧提取)
        self.is_cancelled = False
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🎬 视频混剪工作流程")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 rgba(102, 126, 234, 0.1),
                                          stop: 1 rgba(118, 75, 162, 0.1));
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # 总体进度
        overall_label = QLabel("总体进度:")
        overall_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(overall_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #667eea, stop: 1 #764ba2);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.overall_progress)
        
        # 当前步骤
        self.step_label = QLabel("准备开始...")
        self.step_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #34495e;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.step_label)
        
        # 步骤详情
        steps_label = QLabel("工作流程步骤:")
        steps_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(steps_label)
        
        # 创建9个步骤的显示
        self.step_widgets = []
        steps = [
            ("1️⃣", "输入验证", "验证视频和字幕文件"),
            ("2️⃣", "语言检测", "自动检测字幕语言"),
            ("3️⃣", "字幕解析", "解析字幕文件结构"),
            ("4️⃣", "关键帧提取", "智能提取视频关键帧"),
            ("5️⃣", "场景分析", "检测视频场景变化"),
            ("6️⃣", "剧情分析", "分析叙事结构和节奏"),
            ("7️⃣", "剧本重构", "重构剧本生成新字幕"),
            ("8️⃣", "视频生成", "根据新字幕生成混剪视频"),
            ("9️⃣", "导出工程", "导出剪映工程文件")
        ]
        
        for emoji, title, desc in steps:
            step_widget = self._create_step_widget(emoji, title, desc)
            self.step_widgets.append(step_widget)
            layout.addWidget(step_widget)
        
        # 日志区域
        log_label = QLabel("处理日志:")
        log_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_step_widget(self, emoji, title, desc):
        """创建步骤显示组件"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-radius: 5px;
                padding: 5px;
                margin: 2px 0;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Emoji
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(emoji_label)
        
        # 标题和描述
        text_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # 状态标签
        status_label = QLabel("⏳ 等待中")
        status_label.setStyleSheet("font-size: 12px; color: #95a5a6;")
        status_label.setObjectName("status_label")
        layout.addWidget(status_label)
        
        return widget
    
    def update_step(self, step_number, status="running", message=""):
        """
        更新步骤状态
        
        Args:
            step_number: 步骤编号 (1-7)
            status: 状态 ("running", "completed", "error")
            message: 状态消息
        """
        if step_number < 1 or step_number > 9:
            return

        self.current_step = step_number

        # 更新总体进度
        progress = int((step_number - 1) / self.total_steps * 100)
        self.overall_progress.setValue(progress)

        # 更新当前步骤标签
        step_names = ["输入验证", "语言检测", "字幕解析", "关键帧提取",
                     "场景分析", "剧情分析", "剧本重构", "视频生成", "导出工程"]
        self.step_label.setText(f"当前步骤: {step_number}/9 - {step_names[step_number-1]}")
        
        # 更新步骤状态
        widget = self.step_widgets[step_number - 1]
        status_label = widget.findChild(QLabel, "status_label")
        
        if status == "running":
            status_label.setText("⏳ 进行中")
            status_label.setStyleSheet("font-size: 12px; color: #3498db; font-weight: bold;")
            widget.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                              stop: 0 rgba(52, 152, 219, 0.1),
                                              stop: 1 rgba(52, 152, 219, 0.2));
                    border-radius: 5px;
                    padding: 5px;
                    margin: 2px 0;
                    border-left: 3px solid #3498db;
                }
            """)
        elif status == "completed":
            status_label.setText("✅ 完成")
            status_label.setStyleSheet("font-size: 12px; color: #27ae60; font-weight: bold;")
            widget.setStyleSheet("""
                QWidget {
                    background: rgba(39, 174, 96, 0.1);
                    border-radius: 5px;
                    padding: 5px;
                    margin: 2px 0;
                }
            """)
        elif status == "error":
            status_label.setText("❌ 失败")
            status_label.setStyleSheet("font-size: 12px; color: #e74c3c; font-weight: bold;")
            widget.setStyleSheet("""
                QWidget {
                    background: rgba(231, 76, 60, 0.1);
                    border-radius: 5px;
                    padding: 5px;
                    margin: 2px 0;
                    border-left: 3px solid #e74c3c;
                }
            """)
        
        # 添加日志
        if message:
            self.add_log(message)
    
    def add_log(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def set_completed(self, success=True):
        """设置工作流程完成"""
        self.overall_progress.setValue(100)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        if success:
            self.step_label.setText("✅ 工作流程完成!")
            self.step_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #27ae60;
                    font-weight: bold;
                    padding: 10px;
                    background: rgba(39, 174, 96, 0.1);
                    border-radius: 5px;
                    margin-top: 10px;
                }
            """)
        else:
            self.step_label.setText("❌ 工作流程失败")
            self.step_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #e74c3c;
                    font-weight: bold;
                    padding: 10px;
                    background: rgba(231, 76, 60, 0.1);
                    border-radius: 5px;
                    margin-top: 10px;
                }
            """)
    
    def _on_cancel(self):
        """取消按钮点击"""
        self.is_cancelled = True
        self.cancelled.emit()
        self.add_log("用户取消了工作流程")
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

