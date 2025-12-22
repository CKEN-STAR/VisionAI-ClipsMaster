#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试下载取消机制
验证multiprocessing.Process方案是否能真正终止下载
"""

import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.enhanced_model_downloader import ModelDownloadThread

def test_cancel_mechanism():
    """测试取消机制"""
    print("=" * 70)
    print("测试下载取消机制")
    print("=" * 70)
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 准备下载配置（使用小模型测试）
    download_config = {
        "repo_id": "Qwen/Qwen3-0.6B",  # 使用最小的模型测试
        "target_dir": "models/test_cancel",  # 修正：使用target_dir而不是local_dir
        "mirror_sources": [
            {'name': 'HF-Mirror', 'endpoint': 'https://hf-mirror.com'},
        ],
        "use_snapshot_download": True
    }
    
    print("\n1. 创建下载线程...")
    thread = ModelDownloadThread("qwen3-0.6b", download_config)
    
    # 连接信号
    def on_progress(progress, message):
        print(f"   进度: {progress}% - {message}")
    
    def on_completed(model_name, success):
        print(f"   完成: {model_name} - {'成功' if success else '失败'}")
        app.quit()
    
    def on_error(error_type, error_message):
        print(f"   错误: {error_type} - {error_message}")
        app.quit()
    
    thread.progress_updated.connect(on_progress)
    thread.download_completed.connect(on_completed)
    thread.error_occurred.connect(on_error)
    
    print("2. 启动下载...")
    thread.start()
    
    # 3秒后取消下载
    def cancel_download():
        print("\n3. 发送取消信号...")
        thread.cancel_download()
        print("   ✅ 取消信号已发送")
        print("   ⏳ 等待进程终止...")
        
        # 再等待5秒后检查
        QTimer.singleShot(5000, check_result)
    
    def check_result():
        print("\n4. 检查结果...")
        print("   如果终端没有继续显示下载活动，说明取消成功！")
        app.quit()
    
    QTimer.singleShot(3000, cancel_download)
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_cancel_mechanism()

