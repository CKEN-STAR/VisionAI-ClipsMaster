"""完整测试下载流程（模拟UI）"""
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from src.core.enhanced_model_downloader import ModelDownloadThread

class TestDownloader(QObject):
    """测试下载器"""
    
    def __init__(self):
        super().__init__()
        self.downloader = None
        
    def on_progress_updated(self, progress, message):
        """进度更新回调"""
        print(f"[进度] {progress}% - {message}")
        
    def on_download_completed(self, model_name, success):
        """下载完成回调"""
        if success:
            print(f"[完成] 模型下载成功: {model_name}")
        else:
            print(f"[失败] 模型下载失败: {model_name}")
        
    def on_error_occurred(self, title, message):
        """错误回调"""
        print(f"[错误] {title}: {message}")
        
    def test_download(self):
        """测试下载"""
        print("=" * 80)
        print("测试完整下载流程")
        print("=" * 80)

        # 创建下载配置
        download_config = {
            'repo_id': 'Qwen/Qwen2.5-0.5B',  # 使用小模型测试
            'target_dir': 'models/test_qwen',  # 使用target_dir而不是local_dir
            'use_snapshot_download': True,
            'resume_download': True,
            'max_retries': 3,
            'timeout': 300
        }

        # 创建下载器
        self.downloader = ModelDownloadThread(
            model_name="Qwen2.5-0.5B",
            download_config=download_config
        )
        
        # 连接信号
        self.downloader.progress_updated.connect(self.on_progress_updated)
        self.downloader.download_completed.connect(self.on_download_completed)
        self.downloader.error_occurred.connect(self.on_error_occurred)
        
        # 开始下载
        print("\n[开始] 启动下载...")
        self.downloader.start()
        
        # 等待下载完成
        self.downloader.wait()
        
        print("\n[结束] 下载流程结束")
        print("=" * 80)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    tester = TestDownloader()
    tester.test_download()
    
    # 清理测试文件
    import shutil
    test_dir = Path("models/test_qwen")
    if test_dir.exists():
        print(f"\n[清理] 删除测试目录: {test_dir}")
        shutil.rmtree(test_dir)
    
    sys.exit(0)

