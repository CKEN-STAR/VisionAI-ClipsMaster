#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩监控仪表盘演示

演示压缩性能监控仪表盘的功能，并展示如何与压缩系统集成。
"""

import os
import sys
import time
import logging
import random
import threading
from typing import Dict, Any

# 确保可以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入QT库
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QStatusBar, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer

# 导入项目模块
from src.ui.compression_dashboard_integration import (
    initialize_compression_monitoring,
    get_compression_dashboard_launcher,
    get_compression_monitor
)
from src.compression.adaptive_compression import (
    get_smart_compressor,
    smart_compress,
    smart_decompress
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("compression_demo")


class CompressionLoadGenerator:
    """压缩负载生成器，模拟应用中的压缩操作"""
    
    def __init__(self):
        """初始化负载生成器"""
        self.running = False
        self.thread = None
        
        # 模拟数据
        self.data_types = {
            "text": b"This is a sample text for compression. " * 1000,
            "binary": os.urandom(1000000),  # 1MB的随机二进制数据
            "repeating": b"ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10000,
            "mixed": b"Some text mixed with random data: " + os.urandom(500000)
        }
        
        self.resource_types = [
            "model_weights", "attention_cache", "intermediate_cache", 
            "subtitle", "log_data", "debug_info"
        ]
    
    def start_load(self, interval_range=(0.5, 3.0)):
        """开始生成负载
        
        Args:
            interval_range: 操作间隔范围(秒)
        """
        if self.running:
            logger.warning("负载生成器已在运行")
            return
            
        self.running = True
        self.thread = threading.Thread(
            target=self._load_loop,
            args=(interval_range,),
            daemon=True
        )
        self.thread.start()
        logger.info("负载生成器已启动")
    
    def stop_load(self):
        """停止生成负载"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("负载生成器已停止")
    
    def _load_loop(self, interval_range):
        """负载生成循环"""
        while self.running:
            try:
                # 随机选择数据类型
                data_type = random.choice(list(self.data_types.keys()))
                data = self.data_types[data_type]
                
                # 随机选择资源类型
                resource_type = random.choice(self.resource_types)
                
                # 压缩数据
                compressed, metadata = smart_compress(data, resource_type)
                
                # 解压数据(50%的概率)
                if random.random() > 0.5:
                    decompressed = smart_decompress(compressed, metadata)
                
                # 随机等待时间
                wait_time = random.uniform(interval_range[0], interval_range[1])
                time.sleep(wait_time)
            
            except Exception as e:
                logger.error(f"生成负载出错: {e}")
                time.sleep(1.0)  # 出错后短暂暂停


class DemoWindow(QMainWindow):
    """演示窗口"""
    
    def __init__(self):
        """初始化窗口"""
        super().__init__()
        
        # 设置窗口
        self.setWindowTitle("压缩监控演示")
        self.resize(600, 400)
        
        # 创建工具栏
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        # 添加压缩监控按钮
        launcher = get_compression_dashboard_launcher()
        launcher.create_toolbar_button(toolbar)
        
        # 添加状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 添加标签
        title_label = QLabel("压缩系统负载模拟")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # 添加说明
        desc_label = QLabel(
            "本演示程序模拟应用中的压缩负载，并展示压缩性能监控仪表盘。\n"
            "点击"启动负载"按钮开始生成随机压缩任务，点击"打开仪表盘"查看压缩性能。"
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # 添加控制按钮
        self.start_button = QPushButton("启动负载")
        self.start_button.clicked.connect(self._toggle_load)
        layout.addWidget(self.start_button)
        
        self.dashboard_button = QPushButton("打开仪表盘")
        self.dashboard_button.clicked.connect(launcher.launch_dashboard)
        layout.addWidget(self.dashboard_button)
        
        # 添加状态标签
        self.status_label = QLabel("状态：空闲")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 添加统计信息标签
        self.stats_label = QLabel("尚无统计信息")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        # 创建负载生成器
        self.load_generator = CompressionLoadGenerator()
        
        # 创建更新计时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_stats)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 初始化压缩监控
        initialize_compression_monitoring()
    
    def _toggle_load(self):
        """切换负载生成状态"""
        if self.load_generator.running:
            # 停止负载
            self.load_generator.stop_load()
            self.start_button.setText("启动负载")
            self.status_label.setText("状态：空闲")
            self.statusBar.showMessage("负载生成已停止")
        else:
            # 启动负载
            self.load_generator.start_load()
            self.start_button.setText("停止负载")
            self.status_label.setText("状态：生成负载中")
            self.statusBar.showMessage("负载生成已启动")
    
    def _update_stats(self):
        """更新统计信息"""
        try:
            # 获取压缩统计信息
            compressor = get_smart_compressor()
            stats = compressor.get_stats()
            
            if stats:
                # 构建统计信息文本
                text = "压缩统计信息:\n"
                text += f"压缩操作: {stats.get('compression_count', 0)} 次\n"
                text += f"解压操作: {stats.get('decompression_count', 0)} 次\n"
                
                avg_ratio = stats.get("average_ratio", 1.0)
                text += f"平均压缩率: {avg_ratio:.3f} ({(1-avg_ratio)*100:.1f}%)\n"
                
                bytes_processed = stats.get("bytes_processed", 0)
                text += f"处理数据量: {bytes_processed/(1024*1024):.2f} MB\n"
                
                time_spent = stats.get("time_spent", 0)
                if time_spent > 0:
                    throughput = bytes_processed / (1024 * 1024) / time_spent
                    text += f"平均吞吐量: {throughput:.2f} MB/s"
                
                self.stats_label.setText(text)
        
        except Exception as e:
            logger.error(f"更新统计信息出错: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止负载生成器
        if self.load_generator.running:
            self.load_generator.stop_load()
        
        # 停止计时器
        self.update_timer.stop()
        
        event.accept()


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建并显示窗口
    window = DemoWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 