#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 实时日志UI演示

演示实时日志在UI界面中的显示效果
"""

import sys
import os
import time
import logging
import threading
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QComboBox
    from PyQt6.QtCore import QTimer, pyqtSignal, QObject
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt6 不可用，无法运行UI演示")
    sys.exit(1)

class LogDemoWindow(QMainWindow):
    """日志演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster 实时日志演示")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化日志系统
        self.init_logging()
        
        # 初始化UI
        self.init_ui()
        
        # 启动演示定时器
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.generate_demo_logs)
        
        print("日志演示窗口初始化完成")
    
    def init_logging(self):
        """初始化日志系统"""
        try:
            from src.visionai_clipsmaster.ui.main_window import LogHandler, log_signal_emitter
            
            # 创建日志处理器
            self.log_handler = LogHandler("demo_logger")
            
            # 连接信号
            log_signal_emitter.log_message.connect(self.on_log_message)
            
            print("日志系统初始化成功")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.log_handler = None
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("VisionAI-ClipsMaster 实时日志演示")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 日志级别选择
        control_layout.addWidget(QLabel("日志级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["INFO", "WARNING", "ERROR", "DEBUG"])
        control_layout.addWidget(self.level_combo)
        
        # 手动发送日志按钮
        send_log_btn = QPushButton("发送测试日志")
        send_log_btn.clicked.connect(self.send_manual_log)
        control_layout.addWidget(send_log_btn)
        
        # 开始/停止自动演示
        self.auto_demo_btn = QPushButton("开始自动演示")
        self.auto_demo_btn.clicked.connect(self.toggle_auto_demo)
        control_layout.addWidget(self.auto_demo_btn)
        
        # 清空日志
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.clear_logs)
        control_layout.addWidget(clear_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.log_display)
        
        # 状态栏
        self.status_label = QLabel("就绪 - 等待日志消息")
        layout.addWidget(self.status_label)
    
    def on_log_message(self, message, level):
        """处理日志消息"""
        # 根据日志级别设置颜色
        color_map = {
            'DEBUG': '#888888',
            'INFO': '#00ff00',
            'WARNING': '#ffaa00',
            'ERROR': '#ff4444',
            'CRITICAL': '#ff0000'
        }
        
        color = color_map.get(level.upper(), '#ffffff')
        timestamp = time.strftime('%H:%M:%S')
        
        # 格式化消息
        formatted_message = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'
        
        # 添加到显示区域
        self.log_display.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 更新状态
        self.status_label.setText(f"最新日志: [{level}] {message[:50]}...")
    
    def send_manual_log(self):
        """发送手动测试日志"""
        if not self.log_handler:
            return
        
        level = self.level_combo.currentText().lower()
        message = f"手动测试日志 - {time.strftime('%H:%M:%S')}"
        
        self.log_handler.log(level, message)
    
    def toggle_auto_demo(self):
        """切换自动演示"""
        if self.demo_timer.isActive():
            self.demo_timer.stop()
            self.auto_demo_btn.setText("开始自动演示")
        else:
            self.demo_timer.start(2000)  # 每2秒一条日志
            self.auto_demo_btn.setText("停止自动演示")
    
    def generate_demo_logs(self):
        """生成演示日志"""
        if not self.log_handler:
            return
        
        import random
        
        demo_messages = [
            ("info", "正在加载模型..."),
            ("info", "模型加载完成"),
            ("info", "开始处理视频文件"),
            ("warning", "检测到低内存情况"),
            ("info", "视频处理进度: 25%"),
            ("info", "视频处理进度: 50%"),
            ("info", "视频处理进度: 75%"),
            ("info", "视频处理完成"),
            ("info", "正在生成剪映工程文件"),
            ("info", "剪映工程文件导出成功"),
            ("warning", "临时文件清理中"),
            ("error", "网络连接超时"),
            ("info", "重试连接中..."),
            ("info", "连接恢复正常"),
        ]
        
        level, message = random.choice(demo_messages)
        self.log_handler.log(level, message)
    
    def clear_logs(self):
        """清空日志显示"""
        self.log_display.clear()
        self.status_label.setText("日志已清空")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.demo_timer.isActive():
            self.demo_timer.stop()
        event.accept()

def main():
    """主函数"""
    if not PYQT_AVAILABLE:
        print("PyQt6 不可用，无法运行UI演示")
        return 1
    
    app = QApplication(sys.argv)
    app.setApplicationName("VisionAI-ClipsMaster 日志演示")
    
    # 创建演示窗口
    window = LogDemoWindow()
    window.show()
    
    # 发送欢迎消息
    if window.log_handler:
        window.log_handler.log("info", "欢迎使用 VisionAI-ClipsMaster 实时日志演示")
        window.log_handler.log("info", "点击按钮测试不同级别的日志消息")
        window.log_handler.log("warning", "这是一条警告消息示例")
        window.log_handler.log("error", "这是一条错误消息示例")
    
    return app.exec()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
