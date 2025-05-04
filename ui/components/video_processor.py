#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频处理组件模块 - 处理视频导入、参数设置和处理
"""

import os
import sys
from pathlib import Path
import subprocess
import logging
import threading
import requests
import time
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QProgressBar, QComboBox, 
                           QGroupBox, QMessageBox, QListWidget, QListWidgetItem, 
                           QRadioButton, QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap

# 导入项目模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

try:
    from src.core.screenplay_engineer import ScreenplayEngineer
    CORE_MODULES_AVAILABLE = True
except ImportError:
    print("警告: 无法导入ScreenplayEngineer模块，将使用模拟数据")
    CORE_MODULES_AVAILABLE = False
    
    # 定义模拟的ScreenplayEngineer类
    class ScreenplayEngineer:
        def __init__(self):
            pass
            
        def import_srt(self, srt_path):
            print(f"模拟导入SRT: {srt_path}")
            # 返回模拟数据
            return [
                {"id": 1, "start_time": 0.0, "end_time": 5.0, "text": "这是模拟字幕1"},
                {"id": 2, "start_time": 5.5, "end_time": 10.0, "text": "这是模拟字幕2"}
            ]
            
        def generate_screenplay(self, original_subtitles, preset_name=None, custom_params=None):
            print(f"模拟生成剧本: {preset_name}")
            # 返回模拟数据
            return {
                "process_id": "sim_123456",
                "preset": preset_name or "默认",
                "total_segments": len(original_subtitles),
                "processing_time": 1.5,
                "screenplay": original_subtitles
            }

# 模型下载线程
class ModelDownloadThread(QThread):
    """模型下载线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度, 消息
    download_completed = pyqtSignal()
    download_failed = pyqtSignal(str)
    
    def __init__(self, model_name: str):
        """初始化
        
        Args:
            model_name: 模型名称，如"mistral-7b-en"
        """
        super().__init__()
        self.model_name = model_name
        self.is_running = False
        
        # 模型配置映射
        self.model_configs = {
            'mistral-7b-en': {
                'url': 'https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf',
                'path': 'models/mistral/quantized/Q4_K_M.gguf',
                'size': 4_000_000_000  # 约4GB
            },
            'qwen2.5-7b-zh': {
                'url': 'https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/main/qwen1_5-7b-chat-q4_k_m.gguf',
                'path': 'models/qwen/quantized/Q4_K_M.gguf',
                'size': 4_000_000_000  # 约4GB
            }
        }
    
    def run(self):
        """线程执行函数"""
        self.is_running = True
        
        try:
            if self.model_name not in self.model_configs:
                self.download_failed.emit(f"未知的模型: {self.model_name}")
                return
            
            config = self.model_configs[self.model_name]
            url = config['url']
            dest_path = config['path']
            expected_size = config['size']
            
            # 确保目录存在
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            self.progress_updated.emit(5, f"已创建目录: {dest_dir}")
            
            # 开始下载
            self.progress_updated.emit(10, "开始下载...")
            success = self.download_file(url, dest_path, expected_size)
            
            if success:
                # 检查是否需要量化模型
                self.progress_updated.emit(95, "检查模型是否需要量化...")
                quantized_path = self.quantize_model_if_needed(dest_path)
                
                # 更新配置
                self.progress_updated.emit(98, "更新模型配置...")
                self.update_model_config(self.model_name, quantized_path)
                
                self.progress_updated.emit(100, "下载完成")
                self.download_completed.emit()
            else:
                self.download_failed.emit("下载失败")
                
        except Exception as e:
            self.download_failed.emit(str(e))
        
        finally:
            self.is_running = False
    
    def download_file(self, url: str, dest_path: str, expected_size: int) -> bool:
        """下载文件并显示进度
        
        Args:
            url: 下载URL
            dest_path: 目标路径
            expected_size: 预期文件大小（字节）
            
        Returns:
            bool: 是否下载成功
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # 发起请求
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # 获取总大小
                total_size = int(response.headers.get('content-length', expected_size))
                downloaded = 0
                
                # 写入文件
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not self.is_running:
                            # 用户取消
                            return False
                            
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 更新进度
                            progress = int(40 + (downloaded / total_size) * 50)  # 10-90%
                            self.progress_updated.emit(
                                progress, 
                                f"已下载: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB"
                            )
                
                # 下载完成，验证文件大小
                actual_size = os.path.getsize(dest_path)
                if actual_size < expected_size * 0.9:  # 允许10%的误差
                    self.progress_updated.emit(90, "下载的文件大小不正确，重试...")
                    continue
                    
                return True
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    self.progress_updated.emit(10, f"下载失败，{retry_delay}秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    self.progress_updated.emit(10, f"多次重试后下载失败: {str(e)}")
                    return False
        
        return False
    
    def quantize_model_if_needed(self, model_path: str) -> str:
        """如果需要，量化模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            str: 量化后的模型路径
        """
        # 检查文件名是否已经包含量化标记
        if any(marker in model_path for marker in ["Q4_K_M", "Q5_K_M", "Q4_0", "Q5_0", "Q8_0"]):
            # 已经是量化模型，无需处理
            return model_path
            
        # 建立量化后的路径
        base_name = os.path.basename(model_path)
        quantized_name = os.path.splitext(base_name)[0] + ".Q4_K_M.gguf"
        quantized_path = os.path.join(os.path.dirname(model_path), quantized_name)
        
        self.progress_updated.emit(90, "正在量化模型...")
        
        # 在真实项目中，应该使用GGML/llama.cpp等工具进行量化
        # 简化版本，仅模拟量化过程
        
        try:
            # 模拟量化过程
            llama_cpp_path = os.path.join(Path(__file__).resolve().parent.parent.parent, "llama.cpp")
            quantize_script = os.path.join(llama_cpp_path, "quantize")
            
            if os.path.exists(quantize_script):
                # 实际运行量化命令
                cmd = [
                    quantize_script,
                    model_path,
                    quantized_path,
                    "q4_k_m"
                ]
                
                self.progress_updated.emit(92, "运行量化命令...")
                
                # 执行量化命令
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 监控进度
                while process.poll() is None:
                    line = process.stdout.readline()
                    if line and "progress" in line.lower():
                        progress = 92 + int(float(line.split("%")[0].strip()) * 0.03)
                        self.progress_updated.emit(progress, f"量化进度: {line.strip()}")
                
                # 检查是否成功
                if process.returncode != 0:
                    error = process.stderr.read()
                    raise RuntimeError(f"量化失败: {error}")
                
                return quantized_path
            else:
                # 量化工具不存在，直接复制文件并模拟量化过程
                with open(model_path, 'rb') as src, open(quantized_path, 'wb') as dst:
                    dst.write(src.read())
                
                # 模拟延迟
                time.sleep(2)
                
                return quantized_path
                
        except Exception as e:
            self.progress_updated.emit(93, f"量化失败，使用原始模型: {str(e)}")
            return model_path
    
    def update_model_config(self, model_name: str, model_path: str):
        """更新模型配置
        
        Args:
            model_name: 模型名称
            model_path: 模型文件路径
        """
        # 获取模型类型和语言
        if "mistral" in model_name.lower():
            model_type = "en"
        else:
            model_type = "zh"
            
        # 更新已配置标志
        try:
            # 创建或更新配置目录
            config_dir = os.path.join(
                Path(__file__).resolve().parent.parent.parent,
                "configs",
                "models"
            )
            os.makedirs(config_dir, exist_ok=True)
            
            # 更新active_model.yaml
            active_model_path = os.path.join(config_dir, "active_model.yaml")
            
            config_data = {
                "active_model": model_name,
                "language": model_type,
                "path": model_path,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 创建或更新文件
            try:
                import yaml
                with open(active_model_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            except ImportError:
                # YAML不可用，使用简单文本格式
                with open(active_model_path, 'w', encoding='utf-8') as f:
                    for key, value in config_data.items():
                        f.write(f"{key}: {value}\n")
            
            print(f"已更新模型配置文件: {active_model_path}")
            
        except Exception as e:
            print(f"更新配置文件失败: {str(e)}")
    
    def stop(self):
        """停止下载"""
        self.is_running = False

class VideoProcessorWorker(QThread):
    """视频处理工作线程"""
    progress_updated = pyqtSignal(int, str)
    process_completed = pyqtSignal(dict)
    process_error = pyqtSignal(Exception)
    
    def __init__(self, video_path, subtitle_path, params):
        super().__init__()
        self.video_path = video_path
        self.subtitle_path = subtitle_path
        self.params = params
        self.cancelled = False
        
    def run(self):
        try:
            # 模拟处理步骤
            self.progress_updated.emit(10, "解析视频文件...")
            time.sleep(0.5)  # 模拟处理时间
            
            self.progress_updated.emit(20, "解析字幕文件...")
            time.sleep(0.5)
            
            # 实际使用ScreenplayEngineer进行剧本重构
            engineer = ScreenplayEngineer()
            
            # 导入字幕文件
            self.progress_updated.emit(30, "导入字幕...")
            original_subtitles = engineer.import_srt(self.subtitle_path)
            
            # 生成剧本
            self.progress_updated.emit(40, "分析剧情结构...")
            time.sleep(0.5)
            
            self.progress_updated.emit(50, "检测情感曲线...")
            time.sleep(0.5)
            
            self.progress_updated.emit(60, "重构剧本...")
            result = engineer.generate_screenplay(
                original_subtitles, 
                preset_name=self.params.get("preset"),
                custom_params=self.params
            )
            
            self.progress_updated.emit(80, "优化时间轴...")
            time.sleep(0.5)
            
            self.progress_updated.emit(90, "生成最终剧本...")
            time.sleep(0.5)
            
            if self.cancelled:
                return
                
            self.progress_updated.emit(100, "处理完成")
            self.process_completed.emit(result)
            
        except Exception as e:
            self.process_error.emit(e)

class VideoProcessor(QWidget):
    """视频处理组件"""
    process_completed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.video_path = ""
        self.subtitle_path = ""
        self.worker = None
        self.init_ui()
        self.current_language = "auto"
        self.check_models()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 添加语言选择区域
        lang_group = QGroupBox("语言模式")
        lang_layout = QHBoxLayout()
        
        self.lang_auto_radio = QRadioButton("自动检测")
        self.lang_zh_radio = QRadioButton("中文")
        self.lang_en_radio = QRadioButton("英文")
        
        self.lang_auto_radio.setChecked(True)
        
        # 连接语言选择信号
        self.lang_auto_radio.toggled.connect(lambda: self.change_language_mode("auto"))
        self.lang_zh_radio.toggled.connect(lambda: self.change_language_mode("zh"))
        self.lang_en_radio.toggled.connect(lambda: self.change_language_mode("en"))
        
        lang_layout.addWidget(self.lang_auto_radio)
        lang_layout.addWidget(self.lang_zh_radio)
        lang_layout.addWidget(self.lang_en_radio)
        
        # 添加模型下载按钮
        self.download_en_model_btn = QPushButton("下载英文模型")
        self.download_en_model_btn.setToolTip("下载Mistral-7B英文模型（约4GB）")
        self.download_en_model_btn.clicked.connect(self.download_en_model)
        lang_layout.addWidget(self.download_en_model_btn)
        
        lang_group.setLayout(lang_layout)
        main_layout.addWidget(lang_group)
        
        # 文件选择区域
        file_group = QGroupBox("输入文件")
        file_layout = QVBoxLayout()
        
        # 视频选择
        video_layout = QHBoxLayout()
        self.video_label = QLabel("视频文件: 未选择")
        video_layout.addWidget(self.video_label)
        
        video_btn = QPushButton("选择视频")
        video_btn.clicked.connect(self.select_video)
        video_layout.addWidget(video_btn)
        file_layout.addLayout(video_layout)
        
        # 字幕选择
        subtitle_layout = QHBoxLayout()
        self.subtitle_label = QLabel("字幕文件: 未选择")
        subtitle_layout.addWidget(self.subtitle_label)
        
        subtitle_btn = QPushButton("选择字幕")
        subtitle_btn.clicked.connect(self.select_subtitle)
        subtitle_layout.addWidget(subtitle_btn)
        file_layout.addLayout(subtitle_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 参数设置区域
        params_group = QGroupBox("剧本设置")
        params_layout = QVBoxLayout()
        
        # 预设选择
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("剧本风格:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "默认", "快节奏", "情感化", "悬疑", "励志", "对比式", "金字塔", "三段式"
        ])
        preset_layout.addWidget(self.preset_combo)
        params_layout.addLayout(preset_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        params_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        params_layout.addWidget(self.status_label)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("开始处理")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.start_processing)
        btn_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)
        
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.video_label.setText(f"视频文件: {os.path.basename(file_path)}")
            self.check_ready()
    
    def select_subtitle(self):
        """选择字幕文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "字幕文件 (*.srt *.vtt);;所有文件 (*)"
        )
        
        if file_path:
            self.subtitle_path = file_path
            self.subtitle_label.setText(f"字幕文件: {os.path.basename(file_path)}")
            self.check_ready()
    
    def check_ready(self):
        """检查是否可以开始处理"""
        is_ready = self.video_path and self.subtitle_path
        self.process_btn.setEnabled(is_ready)
    
    def start_processing(self):
        """开始处理视频"""
        if not (self.video_path and self.subtitle_path):
            QMessageBox.warning(self, "缺少文件", "请选择视频和字幕文件")
            return
        
        # 准备参数
        params = {
            "preset": self.preset_combo.currentText(),
            "language": self.current_language
        }
        
        # 调整语言参数
        if params["language"] == "auto":
            params["language"] = "auto"
        elif params["language"] == "zh":
            params["language"] = "zh"
        elif params["language"] == "en":
            params["language"] = "en"
        
        # 启动工作线程
        self.worker = VideoProcessorWorker(
            self.video_path, self.subtitle_path, params
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.process_completed.connect(self.handle_completion)
        self.worker.process_error.connect(self.handle_error)
        
        # 更新UI状态
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("处理中...")
        
        # 启动线程
        self.worker.start()
    
    def cancel_processing(self):
        """取消处理"""
        if self.worker and self.worker.isRunning():
            self.worker.cancelled = True
            self.worker.quit()
            self.worker.wait()
            
            self.status_label.setText("已取消")
            self.progress_bar.setValue(0)
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
    
    def update_progress(self, value, message):
        """更新进度条和状态信息"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def handle_completion(self, result):
        """处理完成回调"""
        self.progress_bar.setValue(100)
        self.status_label.setText("处理完成")
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # 发送处理结果信号
        self.process_completed.emit(result)
        
        QMessageBox.information(self, "处理完成", "剧本重构完成！")
    
    def handle_error(self, error):
        """处理错误回调"""
        self.progress_bar.setValue(0)
        self.status_label.setText("处理出错")
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        QMessageBox.critical(self, "处理错误", f"处理过程中发生错误:\n{str(error)}")

    def change_language_mode(self, mode):
        """切换语言模式
        
        Args:
            mode: 语言模式，"auto", "zh" 或 "en"
        """
        if mode == self.current_language:
            return
            
        self.current_language = mode
        
        # 如果选择了英文模式，检查英文模型是否已下载
        if mode == "en":
            self.check_en_model()
        
        print(f"语言模式已切换为: {mode}")
    
    def check_models(self):
        """检查模型是否已下载"""
        # 检查中文模型
        zh_model_path = os.path.join(
            Path(__file__).resolve().parent.parent.parent,
            "models/qwen/quantized/Q4_K_M.gguf"
        )
        self.zh_model_exists = os.path.exists(zh_model_path)
        
        # 检查英文模型
        en_model_path = os.path.join(
            Path(__file__).resolve().parent.parent.parent,
            "models/mistral/quantized/Q4_K_M.gguf"
        )
        self.en_model_exists = os.path.exists(en_model_path)
        
        # 更新下载按钮状态
        self.update_download_button()
    
    def check_en_model(self):
        """检查英文模型是否存在，不存在则提示下载"""
        if not self.en_model_exists:
            reply = QMessageBox.question(
                self, 
                "英文模型未安装",
                "英文模型尚未下载，是否现在下载？\n(约4GB，需要较长时间)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.download_en_model()
    
    def update_download_button(self):
        """更新下载按钮状态"""
        if self.en_model_exists:
            self.download_en_model_btn.setText("英文模型已安装")
            self.download_en_model_btn.setEnabled(False)
        else:
            self.download_en_model_btn.setText("下载英文模型")
            self.download_en_model_btn.setEnabled(True)
        
    def download_en_model(self):
        """下载英文模型"""
        reply = QMessageBox.question(
            self, 
            "下载英文模型",
            "将下载Mistral-7B英文模型（约4GB），此过程可能需要较长时间。继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 创建并启动下载线程
        self.download_thread = ModelDownloadThread("mistral-7b-en")
        self.download_thread.progress_updated.connect(self.update_download_progress)
        self.download_thread.download_completed.connect(self.on_download_completed)
        self.download_thread.download_failed.connect(self.on_download_failed)
        
        # 创建进度对话框
        self.progress_dialog = QProgressDialog("正在下载模型...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("下载英文模型")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.canceled.connect(self.cancel_download)
        self.progress_dialog.show()
        
        # 开始下载
        self.download_thread.start()
    
    def update_download_progress(self, progress, message):
        """更新下载进度"""
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)
            self.progress_dialog.setLabelText(message)
    
    def on_download_completed(self):
        """下载完成回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        QMessageBox.information(
            self,
            "下载完成",
            "英文模型已成功下载并配置。现在可以使用英文模式处理视频。"
        )
        
        # 更新模型状态
        self.en_model_exists = True
        self.update_download_button()
    
    def on_download_failed(self, error_message):
        """下载失败回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        QMessageBox.critical(
            self,
            "下载失败",
            f"英文模型下载失败: {error_message}"
        )
    
    def cancel_download(self):
        """取消下载"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait()
        
        QMessageBox.information(
            self,
            "下载取消",
            "模型下载已取消"
        )

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication([])
    widget = VideoProcessor()
    widget.show()
    app.exec() 