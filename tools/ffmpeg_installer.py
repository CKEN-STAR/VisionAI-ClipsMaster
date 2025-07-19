#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FFmpeg自动安装器 - 针对中国大陆网络环境优化

支持多镜像源、断点续传、离线安装等功能
"""

import os
import sys
import time
import json
import zipfile
import requests
import threading
from pathlib import Path
from urllib.parse import urljoin
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QTextEdit, QComboBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class FFmpegInstaller:
    """FFmpeg安装器核心类"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.ffmpeg_dir = self.project_root / "tools" / "ffmpeg"
        self.ffmpeg_bin_dir = self.ffmpeg_dir / "bin"
        self.ffmpeg_exe = self.ffmpeg_bin_dir / "ffmpeg.exe"
        
        # 中国大陆镜像源配置
        self.mirror_sources = {
            "清华大学": {
                "base_url": "https://mirrors.tuna.tsinghua.edu.cn/",
                "ffmpeg_path": "ffmpeg/releases/",
                "speed_test_url": "https://mirrors.tuna.tsinghua.edu.cn/speedtest/",
                "priority": 1
            },
            "中科大": {
                "base_url": "https://mirrors.ustc.edu.cn/",
                "ffmpeg_path": "ffmpeg/releases/",
                "speed_test_url": "https://mirrors.ustc.edu.cn/speedtest/",
                "priority": 2
            },
            "阿里云": {
                "base_url": "https://mirrors.aliyun.com/",
                "ffmpeg_path": "ffmpeg/releases/",
                "speed_test_url": "https://mirrors.aliyun.com/speedtest/",
                "priority": 3
            },
            "华为云": {
                "base_url": "https://mirrors.huaweicloud.com/",
                "ffmpeg_path": "ffmpeg/releases/",
                "speed_test_url": "https://mirrors.huaweicloud.com/speedtest/",
                "priority": 4
            },
            "官方源": {
                "base_url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/",
                "ffmpeg_path": "latest/",
                "speed_test_url": "https://github.com/",
                "priority": 5
            }
        }
        
        # FFmpeg版本配置
        self.ffmpeg_versions = {
            "6.1": {
                "filename": "ffmpeg-6.1-essentials_build.zip",
                "size_mb": 45,
                "description": "FFmpeg 6.1 精简版 (推荐)"
            },
            "6.0": {
                "filename": "ffmpeg-6.0-essentials_build.zip", 
                "size_mb": 43,
                "description": "FFmpeg 6.0 精简版"
            },
            "5.1": {
                "filename": "ffmpeg-5.1-essentials_build.zip",
                "size_mb": 41,
                "description": "FFmpeg 5.1 精简版 (兼容性好)"
            }
        }
        
        self.selected_mirror = None
        self.selected_version = "6.1"
        
    def test_mirror_speed(self, mirror_name, timeout=5):
        """测试镜像源速度"""
        try:
            mirror_info = self.mirror_sources[mirror_name]
            start_time = time.time()
            
            response = requests.head(
                mirror_info["speed_test_url"], 
                timeout=timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                speed = time.time() - start_time
                return speed
            else:
                return float('inf')
                
        except Exception as e:
            print(f"[WARN] 镜像源 {mirror_name} 测速失败: {e}")
            return float('inf')
            
    def select_best_mirror(self):
        """自动选择最快的镜像源"""
        print("[INFO] 正在测试镜像源速度...")
        
        speed_results = {}
        for mirror_name in self.mirror_sources.keys():
            speed = self.test_mirror_speed(mirror_name)
            speed_results[mirror_name] = speed
            print(f"[INFO] {mirror_name}: {speed:.2f}秒")
            
        # 选择最快的可用镜像源
        best_mirror = min(speed_results.items(), key=lambda x: x[1])
        
        if best_mirror[1] < float('inf'):
            self.selected_mirror = best_mirror[0]
            print(f"[OK] 选择镜像源: {self.selected_mirror} (速度: {best_mirror[1]:.2f}秒)")
            return True
        else:
            print("[ERROR] 所有镜像源都不可用")
            return False
            
    def get_download_url(self, version="6.1"):
        """获取下载URL"""
        if not self.selected_mirror:
            if not self.select_best_mirror():
                return None
                
        mirror_info = self.mirror_sources[self.selected_mirror]
        version_info = self.ffmpeg_versions[version]
        
        if self.selected_mirror == "官方源":
            # GitHub官方源特殊处理
            url = f"{mirror_info['base_url']}autobuild-2023-12-07-12-49/{version_info['filename']}"
        else:
            # 镜像源标准路径
            url = urljoin(
                mirror_info["base_url"],
                f"{mirror_info['ffmpeg_path']}{version_info['filename']}"
            )
            
        return url
        
    def download_with_progress(self, url, filepath, progress_callback=None):
        """带进度的下载功能"""
        try:
            print(f"[INFO] 开始下载: {url}")
            
            # 检查是否支持断点续传
            resume_pos = 0
            if filepath.exists():
                resume_pos = filepath.stat().st_size
                
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
                print(f"[INFO] 断点续传，从 {resume_pos} 字节开始")
                
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            if resume_pos > 0:
                total_size += resume_pos
                
            downloaded = resume_pos
            
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(filepath, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, downloaded, total_size)
                            
            print(f"[OK] 下载完成: {filepath}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 下载失败: {e}")
            return False
            
    def extract_ffmpeg(self, zip_path, extract_to):
        """解压FFmpeg"""
        try:
            print(f"[INFO] 正在解压: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找ffmpeg.exe文件
                ffmpeg_files = [f for f in zip_ref.namelist() if f.endswith('ffmpeg.exe')]
                
                if not ffmpeg_files:
                    print("[ERROR] 压缩包中未找到ffmpeg.exe")
                    return False
                    
                # 解压ffmpeg.exe到指定目录
                ffmpeg_file = ffmpeg_files[0]
                extract_to.mkdir(parents=True, exist_ok=True)
                
                with zip_ref.open(ffmpeg_file) as source:
                    with open(extract_to / "ffmpeg.exe", 'wb') as target:
                        target.write(source.read())
                        
                print(f"[OK] FFmpeg解压完成: {extract_to / 'ffmpeg.exe'}")
                return True
                
        except Exception as e:
            print(f"[ERROR] 解压失败: {e}")
            return False
            
    def verify_installation(self):
        """验证FFmpeg安装"""
        try:
            if not self.ffmpeg_exe.exists():
                return False, "FFmpeg可执行文件不存在"
                
            # 测试FFmpeg版本
            import subprocess
            result = subprocess.run(
                [str(self.ffmpeg_exe), '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, f"FFmpeg安装成功: {version_line}"
            else:
                return False, f"FFmpeg执行失败: {result.stderr}"
                
        except Exception as e:
            return False, f"FFmpeg验证失败: {e}"
            
    def install_ffmpeg(self, version="6.1", progress_callback=None):
        """安装FFmpeg主流程"""
        try:
            # 1. 选择镜像源
            if not self.selected_mirror:
                if not self.select_best_mirror():
                    return False, "无可用镜像源"
                    
            # 2. 获取下载URL
            download_url = self.get_download_url(version)
            if not download_url:
                return False, "无法获取下载URL"
                
            # 3. 下载FFmpeg
            version_info = self.ffmpeg_versions[version]
            zip_filename = version_info["filename"]
            zip_path = self.ffmpeg_dir / zip_filename
            
            self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.download_with_progress(download_url, zip_path, progress_callback):
                return False, "下载失败"
                
            # 4. 解压FFmpeg
            if not self.extract_ffmpeg(zip_path, self.ffmpeg_bin_dir):
                return False, "解压失败"
                
            # 5. 验证安装
            success, message = self.verify_installation()
            
            # 6. 清理临时文件
            try:
                zip_path.unlink()
            except:
                pass
                
            return success, message
            
        except Exception as e:
            return False, f"安装过程异常: {e}"


class FFmpegInstallerDialog(QDialog):
    """FFmpeg安装器UI对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.installer = FFmpegInstaller()
        self.download_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("FFmpeg自动安装器")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🎬 FFmpeg自动安装器")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 说明文本
        info_label = QLabel(
            "FFmpeg是视频处理的核心组件。\n"
            "本安装器将自动选择最快的镜像源进行下载。"
        )
        layout.addWidget(info_label)
        
        # 版本选择
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("版本选择:"))
        
        self.version_combo = QComboBox()
        for version, info in self.installer.ffmpeg_versions.items():
            self.version_combo.addItem(f"{version} - {info['description']}", version)
        version_layout.addWidget(self.version_combo)
        layout.addLayout(version_layout)
        
        # 镜像源选择
        mirror_layout = QHBoxLayout()
        mirror_layout.addWidget(QLabel("镜像源:"))
        
        self.mirror_combo = QComboBox()
        self.mirror_combo.addItem("自动选择最快源", "auto")
        for mirror_name in self.installer.mirror_sources.keys():
            self.mirror_combo.addItem(mirror_name, mirror_name)
        mirror_layout.addWidget(self.mirror_combo)
        layout.addLayout(mirror_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态文本
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.install_button = QPushButton("开始安装")
        self.install_button.clicked.connect(self.start_installation)
        button_layout.addWidget(self.install_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def log_message(self, message):
        """添加日志消息"""
        self.status_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
    def start_installation(self):
        """开始安装"""
        self.install_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 获取选择的版本和镜像源
        selected_version = self.version_combo.currentData()
        selected_mirror = self.mirror_combo.currentData()
        
        if selected_mirror != "auto":
            self.installer.selected_mirror = selected_mirror
            
        self.log_message(f"开始安装FFmpeg {selected_version}")
        
        # 启动下载线程
        self.download_thread = FFmpegDownloadThread(
            self.installer, selected_version
        )
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.status_updated.connect(self.log_message)
        self.download_thread.installation_finished.connect(self.installation_finished)
        self.download_thread.start()
        
    def update_progress(self, progress, downloaded, total):
        """更新进度条"""
        self.progress_bar.setValue(int(progress))
        
        downloaded_mb = downloaded / 1024 / 1024
        total_mb = total / 1024 / 1024
        
        self.log_message(f"下载进度: {progress:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
        
    def installation_finished(self, success, message):
        """安装完成"""
        self.install_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_message(f"✅ {message}")
            QMessageBox.information(self, "安装成功", message)
            self.accept()
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.critical(self, "安装失败", message)


class FFmpegDownloadThread(QThread):
    """FFmpeg下载线程"""
    
    progress_updated = pyqtSignal(float, int, int)  # progress, downloaded, total
    status_updated = pyqtSignal(str)
    installation_finished = pyqtSignal(bool, str)
    
    def __init__(self, installer, version):
        super().__init__()
        self.installer = installer
        self.version = version
        
    def run(self):
        """执行下载安装"""
        def progress_callback(progress, downloaded, total):
            self.progress_updated.emit(progress, downloaded, total)
            
        def status_callback(message):
            self.status_updated.emit(message)
            
        # 重定向installer的输出到信号
        success, message = self.installer.install_ffmpeg(
            self.version, progress_callback
        )
        
        self.installation_finished.emit(success, message)


def show_ffmpeg_installer(parent=None):
    """显示FFmpeg安装器对话框"""
    dialog = FFmpegInstallerDialog(parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


def check_ffmpeg_and_install(parent=None):
    """检查FFmpeg并在需要时安装"""
    installer = FFmpegInstaller()
    
    # 检查是否已安装
    success, message = installer.verify_installation()
    if success:
        print(f"[OK] {message}")
        return True
        
    # 询问是否安装
    from PyQt6.QtWidgets import QMessageBox
    reply = QMessageBox.question(
        parent,
        "FFmpeg未安装",
        "视频处理功能需要FFmpeg支持。\n\n是否现在自动安装？\n\n"
        "安装器将自动选择最快的国内镜像源。",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        return show_ffmpeg_installer(parent)
    else:
        return False


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试安装器
    success = check_ffmpeg_and_install()
    print(f"安装结果: {success}")
    
    sys.exit(0)
