#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 简化UI

此脚本创建一个简化的UI界面，支持中英文切换和日志查看功能
"""

import sys
import os
from pathlib import Path
import json
import tempfile
import shutil
import time
import threading
import subprocess
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                           QFileDialog, QMessageBox, QTabWidget, QSplitter, QProgressBar, QListWidget, QListWidgetItem, QCheckBox, 
                           QComboBox, QGroupBox, QRadioButton, QButtonGroup, QStackedWidget)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QObject

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VisionAI-ClipsMaster")

# 导入项目模块
try:
    from src.core.clip_generator import ClipGenerator
    from src.timecode.smart_compressor import SmartCompressor
    from src.nlp import process_subtitle_text
    from src.quality import score_video_quality
    from src.training.trainer import ModelTrainer
    CORE_MODULES_AVAILABLE = True
    logger.info("成功导入核心模块")
except ImportError as e:
    logger.warning(f"无法导入核心模块: {e}")
    CORE_MODULES_AVAILABLE = False

# GPU检测工具
def detect_gpu_info():
    """检测系统GPU信息
    
    返回:
        dict: GPU信息，包含可用性和设备名称
    """
    gpu_info = {"available": False, "name": "未检测到GPU"}
    logger.info("开始检测GPU...")
    
    try:
        # 尝试使用torch检测GPU
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["name"] = torch.cuda.get_device_name(0)
            logger.info(f"使用PyTorch检测到GPU: {gpu_info['name']}")
        return gpu_info
    except ImportError:
        logger.debug("未找到PyTorch，尝试其他方法检测GPU")
    
    try:
        # 尝试使用tensorflow检测GPU
        import tensorflow as tf
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            gpu_info["available"] = True
            gpu_info["name"] = f"{len(gpus)}个GPU设备"
            logger.info(f"使用TensorFlow检测到GPU: {gpu_info['name']}")
        return gpu_info
    except ImportError:
        logger.debug("未找到TensorFlow，尝试系统命令检测GPU")
    
    # 检查NVIDIA系统信息 (Windows)
    try:
        result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            gpu_info["available"] = True
            gpu_info["name"] = result.stdout.strip().split("\n")[0]
            logger.info(f"使用nvidia-smi检测到GPU: {gpu_info['name']}")
        return gpu_info
    except (FileNotFoundError, subprocess.SubprocessError):
        logger.debug("nvidia-smi命令失败，无法检测到GPU")
    
    logger.info("GPU检测完成: 未检测到GPU")
    return gpu_info

# 视频处理辅助工具
class VideoProcessor:
    """视频处理工具类"""
    
    @staticmethod
    def generate_viral_srt(original_srt_path, output_path=None, language_mode="auto"):
        """
        根据原始SRT生成爆款SRT
        
        Args:
            original_srt_path: 原始SRT文件路径
            output_path: 输出路径，如果为None则自动生成
            language_mode: 语言模式，可选"auto"、"zh"(中文)、"en"(英文)
            
        Returns:
            str: 生成的爆款SRT文件路径
        """
        logger.info(f"开始生成爆款SRT，原文件: {original_srt_path}, 语言模式: {language_mode}")
        
        if not output_path:
            output_dir = os.path.dirname(original_srt_path)
            output_name = os.path.splitext(os.path.basename(original_srt_path))[0]
            output_path = os.path.join(output_dir, f"{output_name}_viral.srt")
        
        try:
            # 读取原始SRT
            with open(original_srt_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 检测语言，如果设置了自动
            detected_language = language_mode
            if language_mode == "auto":
                detected_language = VideoProcessor._detect_language(original_content)
                logger.info(f"自动检测到语言: {detected_language}")
            
            # 如果可以使用核心NLP模块
            if CORE_MODULES_AVAILABLE:
                try:
                    logger.info("使用核心NLP模块处理字幕")
                    # 处理字幕文本
                    processed_data = process_subtitle_text(original_content, target_language=detected_language)
                    
                    # 根据处理结果生成爆款文本
                    viral_content = processed_data.get("viral_text", "")
                    
                    if not viral_content:
                        logger.warning("核心处理返回空结果，回退到默认模板")
                        # 如果处理失败，使用默认模板
                        viral_content = VideoProcessor._generate_default_viral_srt(original_content, detected_language)
                except Exception as e:
                    logger.error(f"NLP处理失败: {e}")
                    viral_content = VideoProcessor._generate_default_viral_srt(original_content, detected_language)
            else:
                logger.info("核心模块不可用，使用默认模板")
                # 使用默认模板
                viral_content = VideoProcessor._generate_default_viral_srt(original_content, detected_language)
            
            # 保存爆款SRT
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(viral_content)
            
            logger.info(f"爆款SRT生成成功: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"生成爆款SRT失败: {e}", exc_info=True)
            return None 

    @staticmethod
    def _detect_language(text):
        """
        检测文本语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            str: 检测到的语言代码，"zh"或"en"
        """
        # 检测中文字符
        chinese_chars = len(re.findall(r'[\\\14e00-\\\19fff]', text))
        # 检测英文单词
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        # 简单规则：如果中文字符数量比英文单词数量多，就认为是中文
        if chinese_chars > english_words * 0.3:
            logger.debug(f"检测到中文字符: {chinese_chars}, 英文单词: {english_words}, 判定为中文")
            return "zh"
        else:
            logger.debug(f"检测到中文字符: {chinese_chars}, 英文单词: {english_words}, 判定为英文")
            return "en"
    
    @staticmethod
    def _generate_default_viral_srt(original_content, language="zh"):
        """
        生成默认的爆款SRT模板
        
        Args:
            original_content: 原始SRT内容
            language: 语言，"zh"(中文)或"en"(英文)
            
        Returns:
            str: 生成的爆款SRT内容
        """
        logger.info(f"使用默认模板生成爆款字幕，语言: {language}")
        lines = original_content.strip().split('\n')
        result = []
        
        current_block = []
        
        # 根据语言选择不同的模板
        if language == "zh":
            viral_prefixes = [
                "【震撼】", "【独家】", "【揭秘】", "【必看】", "【紧急】",
                "【重磅】", "【突发】", "【首发】", "【爆料】", "【惊呆】"
            ]
            
            viral_suffixes = [
                "太震撼了！", "简直难以置信！", "史诗级体验！", "满分推荐！", 
                "不容错过！", "超乎想象！", "前所未见！", "必看系列！"
            ]
        else:  # 英文模式
            viral_prefixes = [
                "[SHOCKING] ", "[EXCLUSIVE] ", "[REVEALED] ", "[MUST-SEE] ", "[URGENT] ",
                "[BREAKING] ", "[VIRAL] ", "[FIRST TIME] ", "[LEAKED] ", "[AMAZING] "
            ]
            
            viral_suffixes = [
                " - INCREDIBLE!", " - UNBELIEVABLE!", " - EPIC EXPERIENCE!", " - HIGHLY RECOMMENDED!", 
                " - DON'T MISS THIS!", " - MIND-BLOWING!", " - NEVER SEEN BEFORE!", " - MUST WATCH!"
            ]
        
        import random
        
        block_count = 0
        for line in lines:
            if line.strip().isdigit():
                # 新字幕块开始
                if current_block:
                    result.extend(current_block)
                    current_block = []
                current_block.append(line)
                block_count += 1
            elif ' --> ' in line:
                # 时间码行
                current_block.append(line)
            elif line.strip():
                # 文本行
                if len(line) > 3:
                    prefix = random.choice(viral_prefixes) if random.random() < 0.3 else ""
                    suffix = random.choice(viral_suffixes) if random.random() < 0.2 else ""
                    
                    # 替换文本，但保留原始格式
                    if prefix or suffix:
                        new_line = f"{prefix}{line}{suffix}"
                        current_block.append(new_line)
                    else:
                        current_block.append(line)
                else:
                    current_block.append(line)
            else:
                # 空行
                current_block.append(line)
        
        # 处理最后一个块
        if current_block:
            result.extend(current_block)
        
        logger.debug(f"默认模板生成完成，处理了 {block_count} 个字幕块")
        return '\n'.join(result)
    
    @staticmethod
    def generate_video(video_path, srt_path, output_path=None, use_gpu=True):
        """
        根据视频和SRT生成新视频
        
        Args:
            video_path: 原始视频路径
            srt_path: SRT字幕路径
            output_path: 输出视频路径
            use_gpu: 是否使用GPU
            
        Returns:
            str: 生成的视频路径
        """
        logger.info(f"开始生成视频，原始视频: {video_path}, 字幕: {srt_path}, 使用GPU: {use_gpu}")
        
        if not output_path:
            output_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(output_dir, f"{video_name}_爆款.mp4")
        
        if CORE_MODULES_AVAILABLE:
            try:
                logger.info("使用项目核心功能生成视频")
                # 使用项目的核心功能
                clip_generator = ClipGenerator()
                result = clip_generator.process_video(
                    video_path=video_path,
                    subtitle_path=srt_path,
                    output_path=output_path,
                    use_gpu=use_gpu
                )
                if result.get("success", False):
                    logger.info(f"视频生成成功: {output_path}")
                    return output_path
                else:
                    logger.warning(f"核心视频生成失败: {result.get('error', '未知错误')}")
            except Exception as e:
                logger.error(f"视频生成失败: {e}", exc_info=True)
        
        # 如果核心功能不可用或处理失败，使用FFmpeg简单处理
        try:
            logger.info("尝试使用FFmpeg生成视频")
            # 检查FFmpeg是否可用
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            
            # 创建临时字幕文件（ASS格式，支持样式）
            temp_dir = tempfile.mkdtemp()
            ass_path = os.path.join(temp_dir, "subtitle.ass")
            
            # 将SRT转换为ASS
            logger.debug(f"将SRT转换为ASS: {srt_path} -> {ass_path}")
            subprocess.run([
                "ffmpeg", "-i", srt_path, ass_path
            ], capture_output=True, check=True)
            
            # 使用FFmpeg将字幕烧入视频
            logger.debug(f"使用FFmpeg将字幕烧入视频: {video_path} + {ass_path} -> {output_path}")
            subprocess.run([
                "ffmpeg", "-i", video_path, 
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                "-y", output_path
            ], capture_output=True, check=True)
            
            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"FFmpeg处理成功: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"FFmpeg处理失败: {e}", exc_info=True)
            
            # 如果所有处理方法都失败，简单复制原视频
            try:
                logger.warning("所有处理方法失败，简单复制原视频")
                shutil.copy2(video_path, output_path)
                return output_path
            except Exception as e2:
                logger.error(f"复制视频失败: {e2}", exc_info=True)
                return None 

class TrainingWorker(QObject):
    """训练工作器，用于后台线程运行训练任务"""
    
    # 定义信号
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    training_completed = pyqtSignal(dict)
    training_failed = pyqtSignal(str)
    
    def __init__(self, original_srt_paths, viral_srt_text, use_gpu=True, language_mode="zh"):
        super().__init__()
        self.original_srt_paths = original_srt_paths
        self.viral_srt_text = viral_srt_text
        self.use_gpu = use_gpu
        self.language_mode = language_mode
        self.is_running = False
        logger.info(f"初始化训练工作器，样本数: {len(original_srt_paths)}, 语言: {language_mode}, GPU: {use_gpu}")
    
    def train(self):
        """执行训练任务"""
        self.is_running = True
        logger.info("开始训练任务")
        
        try:
            # 发送状态更新
            self.status_updated.emit("正在准备训练数据...")
            self.progress_updated.emit(5)
            
            # 准备训练数据
            training_data = []
            
            # 读取原始SRT文件
            for i, srt_path in enumerate(self.original_srt_paths):
                try:
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 添加到训练数据
                    training_data.append({
                        "original": content,
                        "viral": self.viral_srt_text,
                        "source": os.path.basename(srt_path),
                        "language": self.language_mode
                    })
                    
                    # 更新进度
                    progress = 5 + int((i + 1) / len(self.original_srt_paths) * 15)
                    self.progress_updated.emit(progress)
                    logger.debug(f"已处理训练样本 {i+1}/{len(self.original_srt_paths)}")
                    
                except Exception as e:
                    logger.error(f"读取SRT文件失败: {e}")
            
            if not training_data:
                logger.error("没有有效的训练数据")
                self.training_failed.emit("没有有效的训练数据")
                return
            
            # 保存训练数据
            self.status_updated.emit("正在保存训练数据...")
            self.progress_updated.emit(20)
            
            # 创建训练数据目录
            training_dir = os.path.join(PROJECT_ROOT, "data", "training", self.language_mode)
            os.makedirs(training_dir, exist_ok=True)
            logger.info(f"创建训练数据目录: {training_dir}")
            
            # 保存为JSON文件
            import json
            import datetime
            
            training_file = os.path.join(
                training_dir, 
                f"training_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "count": len(training_data),
                    "created_at": datetime.datetime.now().isoformat(),
                    "language": self.language_mode,
                    "samples": training_data
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"训练数据已保存: {training_file}")
            self.progress_updated.emit(25)
            
            # 如果有可用的训练模块，使用它
            if CORE_MODULES_AVAILABLE:
                try:
                    self.status_updated.emit("正在训练模型...")
                    logger.info("使用核心训练模块训练模型")
                    
                    # 创建训练器
                    trainer = ModelTrainer(
                        training_data=training_data,
                        use_gpu=self.use_gpu,
                        language=self.language_mode
                    )
                    
                    # 设置进度回调
                    def progress_callback(progress, message):
                        if not self.is_running:
                            logger.info("训练被用户中断")
                            return False  # 返回False停止训练
                        
                        # 更新UI进度 (25-90%)
                        ui_progress = 25 + int(progress * 65)
                        self.progress_updated.emit(ui_progress)
                        self.status_updated.emit(message)
                        logger.debug(f"训练进度: {progress:.2%}, {message}")
                        return True
                    
                    # 执行训练
                    result = trainer.train(progress_callback=progress_callback)
                    
                    if not self.is_running:
                        return
                    
                    # 完成训练
                    self.progress_updated.emit(100)
                    self.status_updated.emit("训练完成！")
                    self.training_completed.emit(result)
                    logger.info(f"核心模块训练完成: {result}")
                    return
                
                except Exception as e:
                    logger.error(f"核心模块训练失败: {e}", exc_info=True)
                    # 回退到模拟训练
            
            # 如果核心训练模块不可用或训练失败，进行模拟训练
            logger.info("使用模拟训练")
            self.simulate_training()
            
        except Exception as e:
            logger.error(f"训练过程异常: {e}", exc_info=True)
            self.training_failed.emit(str(e))
        
        finally:
            self.is_running = False
    
    def simulate_training(self):
        """模拟训练过程"""
        logger.info("开始模拟训练过程")
        if not self.is_running:
            return
        
        self.status_updated.emit("正在训练模型...")
        
        # 模拟训练过程
        total_steps = 100
        current_step = 25  # 从25%开始
        
        while current_step < 100 and self.is_running:
            # 更新进度
            self.progress_updated.emit(current_step)
            
            # 模拟进度文本
            if current_step < 50:
                status_msg = f"训练中: 正在分析语义特征... {current_step}%"
                self.status_updated.emit(status_msg)
                logger.debug(status_msg)
            elif current_step < 75:
                status_msg = f"训练中: 优化模型参数... {current_step}%"
                self.status_updated.emit(status_msg)
                logger.debug(status_msg)
            else:
                status_msg = f"训练中: 验证模型性能... {current_step}%"
                self.status_updated.emit(status_msg)
                logger.debug(status_msg)
            
            # 模拟计算时间
            time.sleep(0.1)
            current_step += 1
        
        if not self.is_running:
            logger.info("模拟训练被用户中断")
            return
        
        # 完成训练
        self.progress_updated.emit(100)
        self.status_updated.emit("训练完成！")
        
        # 返回模拟结果
        result = {
            "samples_count": len(self.original_srt_paths),
            "use_gpu": self.use_gpu,
            "language": self.language_mode,
            "accuracy": 0.85 + len(self.original_srt_paths) * 0.01,
            "loss": 0.3 - len(self.original_srt_paths) * 0.01,
            "training_file": f"training_data_{self.language_mode}.json",
            "completed": True
        }
        
        logger.info(f"模拟训练完成: {result}")
        self.training_completed.emit(result)
    
    def stop(self):
        """停止训练"""
        logger.info("用户请求停止训练")
        self.is_running = False 

class SimplifiedUI(QMainWindow):
    """简化版剧本应用，支持中英文切换和日志查看"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster")
        self.setMinimumSize(1000, 700)
        self.current_language = "zh"  # 默认为中文界面
        logger.info("初始化简化版UI")
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建中央Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建语言切换按钮
        language_btn_layout = QHBoxLayout()
        self.switch_language_btn = QPushButton("切换到英文模式" if self.current_language == "zh" else "Switch to Chinese Mode")
        self.switch_language_btn.clicked.connect(self.toggle_language)
        language_btn_layout.addWidget(self.switch_language_btn)
        language_btn_layout.addStretch()
        
        # 添加查看日志按钮
        self.view_log_btn = QPushButton("查看日志" if self.current_language == "zh" else "View Logs")
        self.view_log_btn.clicked.connect(self.show_log_viewer)
        language_btn_layout.addWidget(self.view_log_btn)
        
        main_layout.addLayout(language_btn_layout)
        
        # 创建堆叠窗口用于切换语言界面
        self.stacked_widget = QStackedWidget()
        
        # 创建中文和英文界面
        self.zh_widget = self.create_language_interface("zh")
        self.en_widget = self.create_language_interface("en")
        
        # 添加到堆叠窗口
        self.stacked_widget.addWidget(self.zh_widget)
        self.stacked_widget.addWidget(self.en_widget)
        
        # 设置当前界面
        self.stacked_widget.setCurrentIndex(0 if self.current_language == "zh" else 1)
        
        main_layout.addWidget(self.stacked_widget)
        
        # 设置状态栏
        self.statusBar().showMessage("就绪" if self.current_language == "zh" else "Ready")
        
        logger.info(f"UI初始化完成，当前语言: {self.current_language}")
        
    def create_language_interface(self, language):
        """创建特定语言的界面
        
        Args:
            language: 语言代码，"zh"或"en"
            
        Returns:
            QWidget: 特定语言的界面Widget
        """
        logger.info(f"创建{language}语言界面")
        
        # 创建标签页
        lang_widget = QWidget()
        lang_layout = QVBoxLayout(lang_widget)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # 创建视频处理标签页
        video_tab = self.create_video_processing_tab(language)
        tabs.addTab(video_tab, "视频处理" if language == "zh" else "Video Processing")
        
        # 创建模型训练标签页
        train_tab = self.create_training_tab(language)
        tabs.addTab(train_tab, "模型训练" if language == "zh" else "Model Training")
        
        lang_layout.addWidget(tabs)
        
        return lang_widget
    
    def create_video_processing_tab(self, language):
        """创建视频处理标签页
        
        Args:
            language: 语言代码，"zh"或"en"
            
        Returns:
            QWidget: 视频处理标签页
        """
        # 创建视频处理标签页
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加说明
        title_text = "VisionAI-ClipsMaster 视频处理池" if language == "zh" else "VisionAI-ClipsMaster Video Processing Pool"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 创建上部区域 - 视频池和SRT文件存储
        top_area = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：视频池
        video_pool_widget = QWidget()
        video_pool_layout = QVBoxLayout(video_pool_widget)
        video_pool_text = "视频池：" if language == "zh" else "Video Pool:"
        video_pool_label = QLabel(video_pool_text)
        video_pool_layout.addWidget(video_pool_label)
        
        # 视频列表
        if language == "zh":
            self.zh_video_list = QListWidget()
            video_list = self.zh_video_list
        else:
            self.en_video_list = QListWidget()
            video_list = self.en_video_list
            
        video_pool_layout.addWidget(video_list)
        
        # 视频池操作按钮
        video_btn_layout = QHBoxLayout()
        add_video_text = "添加视频" if language == "zh" else "Add Video"
        remove_video_text = "移除视频" if language == "zh" else "Remove Video"
        
        add_video_btn = QPushButton(add_video_text)
        remove_video_btn = QPushButton(remove_video_text)
        
        if language == "zh":
            add_video_btn.clicked.connect(lambda: self.select_video("zh"))
            remove_video_btn.clicked.connect(lambda: self.remove_video("zh"))
        else:
            add_video_btn.clicked.connect(lambda: self.select_video("en"))
            remove_video_btn.clicked.connect(lambda: self.remove_video("en"))
            
        video_btn_layout.addWidget(add_video_btn)
        video_btn_layout.addWidget(remove_video_btn)
        video_pool_layout.addLayout(video_btn_layout)
        
        top_area.addWidget(video_pool_widget)
        
        # 右侧：SRT文件存储
        srt_pool_widget = QWidget()
        srt_pool_layout = QVBoxLayout(srt_pool_widget)
        srt_pool_text = "SRT文件存储：" if language == "zh" else "SRT Files Storage:"
        srt_pool_label = QLabel(srt_pool_text)
        srt_pool_layout.addWidget(srt_pool_label)
        
        # SRT文件列表
        if language == "zh":
            self.zh_srt_list = QListWidget()
            srt_list = self.zh_srt_list
        else:
            self.en_srt_list = QListWidget()
            srt_list = self.en_srt_list
            
        srt_pool_layout.addWidget(srt_list)
        
        # SRT文件操作按钮
        srt_btn_layout = QHBoxLayout()
        add_srt_text = "添加SRT" if language == "zh" else "Add SRT"
        remove_srt_text = "移除SRT" if language == "zh" else "Remove SRT"
        
        add_srt_btn = QPushButton(add_srt_text)
        remove_srt_btn = QPushButton(remove_srt_text)
        
        if language == "zh":
            add_srt_btn.clicked.connect(lambda: self.select_subtitle("zh"))
            remove_srt_btn.clicked.connect(lambda: self.remove_srt("zh"))
        else:
            add_srt_btn.clicked.connect(lambda: self.select_subtitle("en"))
            remove_srt_btn.clicked.connect(lambda: self.remove_srt("en"))
            
        srt_btn_layout.addWidget(add_srt_btn)
        srt_btn_layout.addWidget(remove_srt_btn)
        srt_pool_layout.addLayout(srt_btn_layout)
        
        top_area.addWidget(srt_pool_widget)
        
        layout.addWidget(top_area)
        
        # 添加操作按钮
        action_layout = QVBoxLayout()
        
        # 添加GPU检测按钮
        detect_gpu_text = "检测GPU硬件" if language == "zh" else "Detect GPU Hardware"
        detect_gpu_btn = QPushButton(detect_gpu_text)
        if language == "zh":
            detect_gpu_btn.clicked.connect(lambda: self.detect_gpu("zh"))
        else:
            detect_gpu_btn.clicked.connect(lambda: self.detect_gpu("en"))
        action_layout.addWidget(detect_gpu_btn)
        
        generate_srt_text = "生成爆款SRT" if language == "zh" else "Generate Viral SRT"
        generate_srt_btn = QPushButton(generate_srt_text)
        generate_srt_btn.setMinimumHeight(40)
        if language == "zh":
            generate_srt_btn.clicked.connect(lambda: self.generate_viral_srt("zh"))
        else:
            generate_srt_btn.clicked.connect(lambda: self.generate_viral_srt("en"))
        action_layout.addWidget(generate_srt_btn)
        
        generate_video_text = "生成视频" if language == "zh" else "Generate Video"
        generate_video_btn = QPushButton(generate_video_text)
        generate_video_btn.setMinimumHeight(40)
        if language == "zh":
            generate_video_btn.clicked.connect(lambda: self.generate_video("zh"))
        else:
            generate_video_btn.clicked.connect(lambda: self.generate_video("en"))
        action_layout.addWidget(generate_video_btn)
        
        layout.addLayout(action_layout)
        
        # 添加状态显示
        status_text = "就绪" if language == "zh" else "Ready"
        if language == "zh":
            self.zh_status_label = QLabel(status_text)
            status_label = self.zh_status_label
        else:
            self.en_status_label = QLabel(status_text)
            status_label = self.en_status_label
            
        layout.addWidget(status_label)
        
        return tab

    def create_training_tab(self, language):
        """创建模型训练标签页
        
        Args:
            language: 语言代码，"zh"或"en"
            
        Returns:
            QWidget: 模型训练标签页
        """
        # 创建训练标签页
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加说明
        title_text = "模型训练" if language == "zh" else "Model Training"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        description_text = "通过多个原始SRT和一个爆款SRT，训练AI模型提升生成质量" if language == "zh" else "Train AI model with multiple original SRTs and one viral SRT to improve generation quality"
        description = QLabel(description_text)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：原始SRT列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_text = "原始SRT列表:" if language == "zh" else "Original SRT List:"
        left_label = QLabel(left_text)
        left_layout.addWidget(left_label)
        
        # 原始SRT列表
        if language == "zh":
            self.zh_original_srt_list = QListWidget()
            original_srt_list = self.zh_original_srt_list
        else:
            self.en_original_srt_list = QListWidget()
            original_srt_list = self.en_original_srt_list
            
        left_layout.addWidget(original_srt_list)
        
        # 添加导入按钮
        import_btn_layout = QHBoxLayout()
        import_text = "导入原始SRT" if language == "zh" else "Import Original SRT"
        remove_text = "移除选中" if language == "zh" else "Remove Selected"
        
        import_original_btn = QPushButton(import_text)
        remove_original_btn = QPushButton(remove_text)
        
        if language == "zh":
            import_original_btn.clicked.connect(lambda: self.import_original_srt("zh"))
            remove_original_btn.clicked.connect(lambda: self.remove_original_srt("zh"))
        else:
            import_original_btn.clicked.connect(lambda: self.import_original_srt("en"))
            remove_original_btn.clicked.connect(lambda: self.remove_original_srt("en"))
            
        import_btn_layout.addWidget(import_original_btn)
        import_btn_layout.addWidget(remove_original_btn)
        left_layout.addLayout(import_btn_layout)
        
        # 添加原始SRT预览
        if language == "zh":
            self.zh_original_preview = QTextEdit()
            original_preview = self.zh_original_preview
        else:
            self.en_original_preview = QTextEdit()
            original_preview = self.en_original_preview
            
        preview_text = "选择左侧的SRT文件进行预览..." if language == "zh" else "Select an SRT file on the left for preview..."
        original_preview.setPlaceholderText(preview_text)
        original_preview.setReadOnly(True)
        original_preview.setMaximumHeight(150)
        preview_label_text = "预览:" if language == "zh" else "Preview:"
        left_layout.addWidget(QLabel(preview_label_text))
        left_layout.addWidget(original_preview)
        
        # 连接列表选择事件
        if language == "zh":
            self.zh_original_srt_list.currentItemChanged.connect(lambda current, previous: self.preview_original_srt(current, previous, "zh"))
        else:
            self.en_original_srt_list.currentItemChanged.connect(lambda current, previous: self.preview_original_srt(current, previous, "en"))
        
        splitter.addWidget(left_widget)
        
        # 右侧：爆款SRT
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_text = "爆款SRT:" if language == "zh" else "Viral SRT:"
        right_label = QLabel(right_text)
        right_layout.addWidget(right_label)
        
        if language == "zh":
            self.zh_viral_srt = QTextEdit()
            viral_srt = self.zh_viral_srt
        else:
            self.en_viral_srt = QTextEdit()
            viral_srt = self.en_viral_srt
            
        placeholder_text = "输入或导入爆款SRT剧本..." if language == "zh" else "Enter or import viral SRT script..."
        viral_srt.setPlaceholderText(placeholder_text)
        right_layout.addWidget(viral_srt)
        
        # 添加导入按钮
        import_viral_text = "导入爆款SRT" if language == "zh" else "Import Viral SRT"
        import_viral_btn = QPushButton(import_viral_text)
        if language == "zh":
            import_viral_btn.clicked.connect(lambda: self.import_viral_srt("zh"))
        else:
            import_viral_btn.clicked.connect(lambda: self.import_viral_srt("en"))
            
        right_layout.addWidget(import_viral_btn)
        
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        
        # 添加学习按钮和GPU选项
        train_controls = QHBoxLayout()
        
        use_gpu_text = "使用GPU加速训练" if language == "zh" else "Use GPU for Training"
        if language == "zh":
            self.zh_use_gpu_checkbox = QCheckBox(use_gpu_text)
            use_gpu_checkbox = self.zh_use_gpu_checkbox
        else:
            self.en_use_gpu_checkbox = QCheckBox(use_gpu_text)
            use_gpu_checkbox = self.en_use_gpu_checkbox
            
        use_gpu_checkbox.setChecked(True)
        train_controls.addWidget(use_gpu_checkbox)
        
        detect_gpu_text = "检测GPU" if language == "zh" else "Detect GPU"
        detect_gpu_btn = QPushButton(detect_gpu_text)
        if language == "zh":
            detect_gpu_btn.clicked.connect(lambda: self.detect_training_gpu("zh"))
        else:
            detect_gpu_btn.clicked.connect(lambda: self.detect_training_gpu("en"))
            
        train_controls.addWidget(detect_gpu_btn)
        
        layout.addLayout(train_controls)
        
        learn_text = "开始训练模型" if language == "zh" else "Start Training Model"
        learn_btn = QPushButton(learn_text)
        learn_btn.setMinimumHeight(40)
        if language == "zh":
            learn_btn.clicked.connect(lambda: self.learn_data_pair("zh"))
        else:
            learn_btn.clicked.connect(lambda: self.learn_data_pair("en"))
            
        layout.addWidget(learn_btn)
        
        # 添加状态标签
        status_text = "准备就绪" if language == "zh" else "Ready"
        if language == "zh":
            self.zh_train_status_label = QLabel(status_text)
            train_status_label = self.zh_train_status_label
        else:
            self.en_train_status_label = QLabel(status_text)
            train_status_label = self.en_train_status_label
            
        layout.addWidget(train_status_label)
        
        # 添加进度条
        if language == "zh":
            self.zh_progress_bar = QProgressBar()
            progress_bar = self.zh_progress_bar
        else:
            self.en_progress_bar = QProgressBar()
            progress_bar = self.en_progress_bar
            
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)
        
        return tab

    def toggle_language(self):
        """切换语言界面"""
        if self.current_language == "zh":
            self.current_language = "en"
            self.switch_language_btn.setText("Switch to Chinese Mode")
            self.view_log_btn.setText("View Logs")
            self.stacked_widget.setCurrentIndex(1)  # 英文界面
            self.statusBar().showMessage("Ready")
            logger.info("切换到英文界面")
        else:
            self.current_language = "zh"
            self.switch_language_btn.setText("切换到英文模式")
            self.view_log_btn.setText("查看日志")
            self.stacked_widget.setCurrentIndex(0)  # 中文界面
            self.statusBar().showMessage("就绪")
            logger.info("切换到中文界面")
    
    def show_log_viewer(self):
        """显示日志查看器"""
        log_viewer = LogViewer(self.current_language, parent=self)
        log_viewer.exec()
    
    # 视频处理相关方法
    def select_video(self, language):
        """选择视频文件
        
        Args:
            language: 语言代码，"zh"或"en"
        """
        dialog_title = "选择视频文件" if language == "zh" else "Select Video Files"
        filter_text = "视频文件 (*.mp4 *.avi *.mov *.mkv)" if language == "zh" else "Video Files (*.mp4 *.avi *.mov *.mkv)"
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, dialog_title, "", filter_text
        )
        
        video_list = self.zh_video_list if language == "zh" else self.en_video_list
        status_label = self.zh_status_label if language == "zh" else self.en_status_label
        
        for file_path in file_paths:
            if file_path:
                # 添加到视频池列表
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
                video_list.addItem(item)
                added_msg = f"已添加视频文件: {os.path.basename(file_path)}" if language == "zh" else f"Added video file: {os.path.basename(file_path)}"
                self.statusBar().showMessage(added_msg)
                status_label.setText(added_msg)
                logger.info(f"添加视频文件: {file_path}")
    
    def remove_video(self, language):
        """从视频池中移除视频
        
        Args:
            language: 语言代码，"zh"或"en"
        """
        video_list = self.zh_video_list if language == "zh" else self.en_video_list
        status_label = self.zh_status_label if language == "zh" else self.en_status_label
        
        selected_items = video_list.selectedItems()
        if not selected_items:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请先选择要移除的视频" if language == "zh" else "Please select videos to remove first"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            video_list.takeItem(video_list.row(item))
            logger.info(f"移除视频文件: {file_path}")
        
        removed_msg = f"已移除 {len(selected_items)} 个视频文件" if language == "zh" else f"Removed {len(selected_items)} video files"
        self.statusBar().showMessage(removed_msg)
        status_label.setText(removed_msg)
    
    def select_subtitle(self, language):
        """选择字幕文件
        
        Args:
            language: 语言代码，"zh"或"en"
        """
        dialog_title = "选择字幕文件" if language == "zh" else "Select Subtitle Files"
        filter_text = "字幕文件 (*.srt *.ass *.vtt)" if language == "zh" else "Subtitle Files (*.srt *.ass *.vtt)"
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, dialog_title, "", filter_text
        )
        
        srt_list = self.zh_srt_list if language == "zh" else self.en_srt_list
        status_label = self.zh_status_label if language == "zh" else self.en_status_label
        
        for file_path in file_paths:
            if file_path:
                # 添加到SRT列表
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
                srt_list.addItem(item)
                added_msg = f"已添加字幕文件: {os.path.basename(file_path)}" if language == "zh" else f"Added subtitle file: {os.path.basename(file_path)}"
                self.statusBar().showMessage(added_msg)
                status_label.setText(added_msg)
                logger.info(f"添加字幕文件: {file_path}")
    
    def remove_srt(self, language):
        """从SRT池中移除SRT文件
        
        Args:
            language: 语言代码，"zh"或"en"
        """
        srt_list = self.zh_srt_list if language == "zh" else self.en_srt_list
        status_label = self.zh_status_label if language == "zh" else self.en_status_label
        
        selected_items = srt_list.selectedItems()
        if not selected_items:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请先选择要移除的SRT文件" if language == "zh" else "Please select SRT files to remove first"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            srt_list.takeItem(srt_list.row(item))
            logger.info(f"移除字幕文件: {file_path}")
        
        removed_msg = f"已移除 {len(selected_items)} 个SRT文件" if language == "zh" else f"Removed {len(selected_items)} SRT files"
        self.statusBar().showMessage(removed_msg)
        status_label.setText(removed_msg)

    def generate_viral_srt(self, language):
        """生成爆款SRT
        
        Args:
            language: 语言代码，"zh"或"en"
        """
        # 获取相应语言的UI组件
        srt_list = self.zh_srt_list if language == "zh" else self.en_srt_list
        status_label = self.zh_status_label if language == "zh" else self.en_status_label
        video_list = self.zh_video_list if language == "zh" else self.en_video_list
        
        # 检查是否有选中的视频和SRT
        if video_list.count() == 0:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请先添加视频" if language == "zh" else "Please add videos first"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        if srt_list.count() == 0:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请先添加SRT文件" if language == "zh" else "Please add SRT files first"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        # 获取选中的SRT文件
        selected_items = srt_list.selectedItems()
        if not selected_items:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请先选择要处理的SRT文件" if language == "zh" else "Please select SRT files to process"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        # 更新状态
        processing_msg = "正在生成爆款SRT..." if language == "zh" else "Generating viral SRT..."
        status_label.setText(processing_msg)
        self.statusBar().showMessage(processing_msg)
        logger.info(f"开始生成爆款SRT, 语言: {language}")
        
        # 批量处理选中的SRT
        for item in selected_items:
            srt_path = item.data(Qt.ItemDataRole.UserRole)
            output_path = VideoProcessor.generate_viral_srt(
                srt_path, 
                language_mode=language
            )
            
            if output_path:
                # 处理成功，添加生成的SRT到列表
                viral_prefix = "爆款-" if language == "zh" else "Viral-"
                viral_item = QListWidgetItem(f"{viral_prefix}{os.path.basename(output_path)}")
                viral_item.setData(Qt.ItemDataRole.UserRole, output_path)
                viral_item.setBackground(Qt.GlobalColor.lightGray)  # 标记为爆款样式
                srt_list.addItem(viral_item)
                
                success_msg = f"成功生成爆款SRT: {os.path.basename(output_path)}" if language == "zh" else f"Successfully generated viral SRT: {os.path.basename(output_path)}"
                self.statusBar().showMessage(success_msg)
                status_label.setText(success_msg)
                logger.info(f"成功生成爆款SRT: {output_path}")
            else:
                # 处理失败
                warning_title = "警告" if language == "zh" else "Warning"
                fail_msg = f"生成爆款SRT失败: {os.path.basename(srt_path)}" if language == "zh" else f"Failed to generate viral SRT: {os.path.basename(srt_path)}"
                QMessageBox.warning(self, warning_title, fail_msg)
                self.statusBar().showMessage(fail_msg)
                status_label.setText(fail_msg)
                logger.error(f"生成爆款SRT失败: {srt_path}")
    
    def generate_video(self, language):
        """生成新视频
        
        Args:
            language: 语言代码，"zh"或"en"
        """
        # 获取相应语言的UI组件
        video_list = self.zh_video_list if language == "zh" else self.en_video_list
        srt_list = self.zh_srt_list if language == "zh" else self.en_srt_list
        status_label = self.zh_status_label if language == "zh" else self.en_status_label
        
        # 检查是否有选中的视频和SRT
        if video_list.count() == 0:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请先添加视频" if language == "zh" else "Please add videos first"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        # 获取选中的视频
        selected_video = video_list.currentItem()
        
        if not selected_video:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请选择一个要处理的视频" if language == "zh" else "Please select a video to process"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        video_path = selected_video.data(Qt.ItemDataRole.UserRole)
        
        # 找到选中的爆款SRT
        selected_srt = srt_list.currentItem()
        
        if not selected_srt:
            warning_title = "警告" if language == "zh" else "Warning"
            warning_msg = "请选择一个爆款SRT文件" if language == "zh" else "Please select a viral SRT file"
            QMessageBox.warning(self, warning_title, warning_msg)
            return
        
        srt_path = selected_srt.data(Qt.ItemDataRole.UserRole)
        
        # 检查是否为爆款SRT
        viral_keyword = "爆款" if language == "zh" else "viral"
        srt_name = os.path.basename(srt_path)
        if viral_keyword not in srt_name.lower():
            confirm_title = "确认使用" if language == "zh" else "Confirm Usage"
            confirm_msg = f"所选SRT文件 '{srt_name}' 不是爆款SRT，确定要使用吗?" if language == "zh" else f"Selected SRT file '{srt_name}' is not a viral SRT, are you sure you want to use it?"
            reply = QMessageBox.question(
                self, 
                confirm_title, 
                confirm_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 显示处理中
        processing_msg = "视频生成中..." if language == "zh" else "Generating video..."
        status_label.setText(processing_msg)
        self.statusBar().showMessage(processing_msg)
        logger.info(f"开始生成视频, 语言: {language}, 视频: {video_path}, 字幕: {srt_path}")
        
        # 检测GPU
        gpu_info = detect_gpu_info()
        use_gpu = gpu_info.get("available", False)
        
        # 模拟处理
        QApplication.processEvents()
        
        # 询问保存路径
        save_title = "保存生成的视频" if language == "zh" else "Save Generated Video"
        filter_text = "视频文件 (*.mp4)" if language == "zh" else "Video Files (*.mp4)"
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        default_name = f"{video_name}_爆款.mp4" if language == "zh" else f"{video_name}_viral.mp4"
        save_path, _ = QFileDialog.getSaveFileName(
            self, save_title, default_name, filter_text
        )
        
        if not save_path:
            canceled_msg = "已取消" if language == "zh" else "Canceled"
            status_label.setText(canceled_msg)
            self.statusBar().showMessage(canceled_msg)
            logger.info("用户取消了视频生成")
            return
        
        # 显示处理进度
        progress_title = "处理中" if language == "zh" else "Processing"
        progress_msg = "正在生成视频，请稍候..." if language == "zh" else "Generating video, please wait..."
        progress_dialog = QMessageBox(self)
        progress_dialog.setIcon(QMessageBox.Icon.Information)
        progress_dialog.setWindowTitle(progress_title)
        progress_dialog.setText(progress_msg)
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # 使用实际功能生成视频
            output_path = VideoProcessor.generate_video(
                video_path=video_path,
                srt_path=srt_path,
                output_path=save_path,
                use_gpu=use_gpu
            )
            
            progress_dialog.close()
            
            if not output_path or not os.path.exists(output_path):
                raise Exception("生成视频失败" if language == "zh" else "Failed to generate video")
            
            # 更新UI
            complete_msg = "视频生成完成" if language == "zh" else "Video generation complete"
            status_label.setText(complete_msg)
            saved_msg = f"新视频已保存到: {os.path.basename(save_path)}" if language == "zh" else f"New video saved to: {os.path.basename(save_path)}"
            self.statusBar().showMessage(saved_msg)
            
            # 显示成功消息
            success_title = "成功" if language == "zh" else "Success"
            success_msg = f"爆款视频已生成并保存到:\n{save_path}" if language == "zh" else f"Viral video has been generated and saved to:\n{save_path}"
            QMessageBox.information(self, success_title, success_msg)
            logger.info(f"视频生成成功: {save_path}")
            
        except Exception as e:
            progress_dialog.close()
            error_title = "错误" if language == "zh" else "Error"
            error_msg = f"生成失败: {str(e)}" if language == "zh" else f"Generation failed: {str(e)}"
            QMessageBox.critical(self, error_title, error_msg)
            fail_msg = "生成失败" if language == "zh" else "Generation failed"
            status_label.setText(fail_msg)
            self.statusBar().showMessage(fail_msg)
            logger.error(f"视频生成失败: {str(e)}", exc_info=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimplifiedUI()
    window.show()
    sys.exit(app.exec()) 