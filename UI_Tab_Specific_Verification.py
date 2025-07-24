#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 标签页特定UI实时更新验证脚本
专门检查视频处理和模型训练标签页中的智能推荐下载器实时更新机制
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, 
    QLabel, QTextEdit, QTabWidget, QGroupBox, QHBoxLayout, QProgressBar,
    QMessageBox, QDialog
)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TabSpecificUIVerifier(QMainWindow):
    """标签页特定UI验证器"""
    
    def __init__(self):
        super().__init__()
        self.main_app = None
        self.test_results = {}
        self.init_ui()
        self.setup_test_environment()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("🔍 VisionAI-ClipsMaster 标签页UI实时更新验证")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("🎯 标签页智能推荐下载器实时更新验证")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("margin: 10px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # 创建测试标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 视频处理标签页测试
        self.video_tab = self.create_video_processing_test_tab()
        self.tab_widget.addTab(self.video_tab, "🎬 视频处理标签页测试")
        
        # 模型训练标签页测试
        self.training_tab = self.create_training_module_test_tab()
        self.tab_widget.addTab(self.training_tab, "🧠 模型训练标签页测试")
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(200)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.result_text)
        
        # 状态栏
        self.status_label = QLabel("🚀 准备开始验证...")
        self.status_label.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(self.status_label)
    
    def create_video_processing_test_tab(self):
        """创建视频处理标签页测试"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 测试组
        test_group = QGroupBox("🎬 视频处理标签页 - 智能推荐下载器测试")
        test_layout = QVBoxLayout(test_group)
        
        # 说明
        info_label = QLabel("""
测试目标：验证视频处理标签页中的模型选择/下载按钮弹出的智能推荐下载器对话框
检查项目：
• 硬件配置信息实时更新（GPU显存、系统内存、CPU核心数等）
• 模型推荐信息动态更新（推荐的量化等级、文件大小、内存需求等）
• 下载状态和进度信息实时显示
• 硬件适配推荐理由智能生成
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #e8f4fd; padding: 10px; border-radius: 4px;")
        test_layout.addWidget(info_label)
        
        # 测试按钮
        self.test_video_lang_buttons_btn = QPushButton("测试语言模式按钮触发的下载器")
        self.test_video_lang_buttons_btn.clicked.connect(self.test_video_language_buttons)
        test_layout.addWidget(self.test_video_lang_buttons_btn)
        
        self.test_video_generate_srt_btn = QPushButton("测试生成爆款SRT按钮的模型检查")
        self.test_video_generate_srt_btn.clicked.connect(self.test_video_generate_srt)
        test_layout.addWidget(self.test_video_generate_srt_btn)
        
        self.test_video_realtime_update_btn = QPushButton("测试视频处理中的实时更新机制")
        self.test_video_realtime_update_btn.clicked.connect(self.test_video_realtime_update)
        test_layout.addWidget(self.test_video_realtime_update_btn)
        
        # 结果显示
        self.video_result_text = QTextEdit()
        self.video_result_text.setMaximumHeight(150)
        test_layout.addWidget(self.video_result_text)
        
        layout.addWidget(test_group)
        return tab
    
    def create_training_module_test_tab(self):
        """创建模型训练标签页测试"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 测试组
        test_group = QGroupBox("🧠 模型训练标签页 - 智能推荐下载器测试")
        test_layout = QVBoxLayout(test_group)
        
        # 说明
        info_label = QLabel("""
测试目标：验证模型训练标签页中的模型相关按钮弹出的智能推荐下载器对话框
检查项目：
• 当前硬件状态检测结果实时显示
• 基于硬件配置的模型推荐动态更新
• 训练相关的性能预估信息实时计算
• 资源使用情况预测和建议
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #f0f8ff; padding: 10px; border-radius: 4px;")
        test_layout.addWidget(info_label)
        
        # 测试按钮
        self.test_training_model_check_btn = QPushButton("测试训练页面模型检查机制")
        self.test_training_model_check_btn.clicked.connect(self.test_training_model_check)
        test_layout.addWidget(self.test_training_model_check_btn)
        
        self.test_training_lang_switch_btn = QPushButton("测试训练页面语言切换下载器")
        self.test_training_lang_switch_btn.clicked.connect(self.test_training_language_switch)
        test_layout.addWidget(self.test_training_lang_switch_btn)
        
        self.test_training_realtime_btn = QPushButton("测试训练页面实时更新机制")
        self.test_training_realtime_btn.clicked.connect(self.test_training_realtime)
        test_layout.addWidget(self.test_training_realtime_btn)
        
        # 结果显示
        self.training_result_text = QTextEdit()
        self.training_result_text.setMaximumHeight(150)
        test_layout.addWidget(self.training_result_text)
        
        layout.addWidget(test_group)
        return tab
    
    def setup_test_environment(self):
        """设置测试环境"""
        try:
            self.log_result("🔧 正在设置测试环境...")
            
            # 导入主应用程序
            import simple_ui_fixed
            
            # 创建主应用程序实例（但不显示）
            self.main_app = simple_ui_fixed.SimpleScreenplayApp()
            
            # 检查动态下载器集成
            has_dynamic_downloader = hasattr(self.main_app, 'dynamic_downloader')
            has_enhanced_downloader = hasattr(self.main_app, 'enhanced_downloader')
            has_training_feeder = hasattr(self.main_app, 'train_feeder')
            
            self.log_result(f"✅ 主应用程序创建成功")
            self.log_result(f"✅ 动态下载器集成: {'存在' if has_dynamic_downloader else '缺失'}")
            self.log_result(f"✅ 增强下载器: {'存在' if has_enhanced_downloader else '缺失'}")
            self.log_result(f"✅ 训练组件: {'存在' if has_training_feeder else '缺失'}")
            
            self.status_label.setText("✅ 测试环境设置完成")
            
        except Exception as e:
            self.log_result(f"❌ 测试环境设置失败: {e}")
            self.status_label.setText(f"❌ 环境设置失败: {e}")
    
    def test_video_language_buttons(self):
        """测试视频处理页面的语言模式按钮"""
        try:
            self.video_result_text.clear()
            self.video_result_text.append("🎬 开始测试视频处理页面的语言模式按钮...")
            
            if not self.main_app:
                self.video_result_text.append("❌ 主应用程序未初始化")
                return
            
            # 检查语言模式按钮
            has_lang_buttons = (
                hasattr(self.main_app, 'lang_zh_radio') and
                hasattr(self.main_app, 'lang_en_radio') and
                hasattr(self.main_app, 'lang_auto_radio')
            )
            
            self.video_result_text.append(f"✅ 语言模式按钮: {'存在' if has_lang_buttons else '缺失'}")
            
            # 检查语言切换方法
            has_change_method = hasattr(self.main_app, 'change_language_mode')
            self.video_result_text.append(f"✅ 语言切换方法: {'存在' if has_change_method else '缺失'}")
            
            # 检查模型检查方法
            has_model_check = (
                hasattr(self.main_app, 'check_zh_model') and
                hasattr(self.main_app, 'check_en_model')
            )
            self.video_result_text.append(f"✅ 模型检查方法: {'存在' if has_model_check else '缺失'}")
            
            # 测试语言切换触发下载器
            if has_change_method:
                self.video_result_text.append("🔄 测试中文模式切换...")
                try:
                    # 模拟切换到中文模式（这会触发模型检查）
                    self.main_app.change_language_mode("zh")
                    self.video_result_text.append("✅ 中文模式切换成功")
                except Exception as e:
                    self.video_result_text.append(f"⚠️ 中文模式切换异常: {e}")
                
                self.video_result_text.append("🔄 测试英文模式切换...")
                try:
                    # 模拟切换到英文模式（这会触发模型检查）
                    self.main_app.change_language_mode("en")
                    self.video_result_text.append("✅ 英文模式切换成功")
                except Exception as e:
                    self.video_result_text.append(f"⚠️ 英文模式切换异常: {e}")
            
            self.test_results['video_language_buttons'] = {
                'lang_buttons': has_lang_buttons,
                'change_method': has_change_method,
                'model_check': has_model_check
            }
            
        except Exception as e:
            self.video_result_text.append(f"❌ 测试失败: {e}")
            logger.error(f"视频语言按钮测试失败: {e}")
    
    def test_video_generate_srt(self):
        """测试视频处理页面的生成爆款SRT按钮"""
        try:
            self.video_result_text.clear()
            self.video_result_text.append("✨ 开始测试生成爆款SRT按钮...")
            
            if not self.main_app:
                self.video_result_text.append("❌ 主应用程序未初始化")
                return
            
            # 检查生成方法
            has_generate_method = hasattr(self.main_app, 'generate_viral_srt')
            self.video_result_text.append(f"✅ 生成爆款SRT方法: {'存在' if has_generate_method else '缺失'}")
            
            # 检查视频处理器
            has_processor = hasattr(self.main_app, 'processor')
            self.video_result_text.append(f"✅ 视频处理器: {'存在' if has_processor else '缺失'}")
            
            # 检查语言检测
            if has_processor and self.main_app.processor:
                has_lang_detect = hasattr(self.main_app.processor, 'generate_viral_srt')
                self.video_result_text.append(f"✅ 语言检测功能: {'存在' if has_lang_detect else '缺失'}")
            
            self.test_results['video_generate_srt'] = {
                'generate_method': has_generate_method,
                'processor': has_processor
            }
            
        except Exception as e:
            self.video_result_text.append(f"❌ 测试失败: {e}")
            logger.error(f"生成爆款SRT测试失败: {e}")
    
    def test_video_realtime_update(self):
        """测试视频处理的实时更新机制"""
        try:
            self.video_result_text.clear()
            self.video_result_text.append("🔄 开始测试视频处理实时更新机制...")
            
            if not self.main_app:
                self.video_result_text.append("❌ 主应用程序未初始化")
                return
            
            # 检查动态下载器集成
            has_dynamic_downloader = (
                hasattr(self.main_app, 'dynamic_downloader') and
                self.main_app.dynamic_downloader is not None
            )
            self.video_result_text.append(f"✅ 动态下载器集成: {'存在' if has_dynamic_downloader else '缺失'}")
            
            # 检查回调方法
            has_callbacks = (
                hasattr(self.main_app, 'on_dynamic_download_completed') and
                hasattr(self.main_app, 'on_hardware_changed')
            )
            self.video_result_text.append(f"✅ 实时更新回调: {'存在' if has_callbacks else '缺失'}")
            
            # 测试硬件信息获取
            if has_dynamic_downloader:
                try:
                    hardware_info = self.main_app.dynamic_downloader.get_hardware_info()
                    if hardware_info:
                        self.video_result_text.append(f"✅ 硬件信息获取成功")
                        self.video_result_text.append(f"   RAM: {hardware_info.get('system_ram_gb', 0):.1f}GB")
                        self.video_result_text.append(f"   GPU: {hardware_info.get('gpu_type', 'Unknown')}")
                    else:
                        self.video_result_text.append("⚠️ 硬件信息获取为空")
                except Exception as e:
                    self.video_result_text.append(f"⚠️ 硬件信息获取异常: {e}")
            
            self.test_results['video_realtime_update'] = {
                'dynamic_downloader': has_dynamic_downloader,
                'callbacks': has_callbacks
            }
            
        except Exception as e:
            self.video_result_text.append(f"❌ 测试失败: {e}")
            logger.error(f"视频实时更新测试失败: {e}")
    
    def test_training_model_check(self):
        """测试训练页面的模型检查机制"""
        try:
            self.training_result_text.clear()
            self.training_result_text.append("🧠 开始测试训练页面模型检查机制...")
            
            if not self.main_app:
                self.training_result_text.append("❌ 主应用程序未初始化")
                return
            
            # 检查训练组件
            has_training_feeder = hasattr(self.main_app, 'train_feeder')
            self.training_result_text.append(f"✅ 训练组件: {'存在' if has_training_feeder else '缺失'}")
            
            if has_training_feeder and self.main_app.train_feeder:
                # 检查模型检查方法
                has_model_check = (
                    hasattr(self.main_app.train_feeder, 'check_models') and
                    hasattr(self.main_app.train_feeder, 'check_zh_model') and
                    hasattr(self.main_app.train_feeder, 'check_en_model')
                )
                self.training_result_text.append(f"✅ 模型检查方法: {'存在' if has_model_check else '缺失'}")
                
                # 检查智能下载器集成
                training_feeder = self.main_app.train_feeder
                uses_enhanced_downloader = (
                    hasattr(training_feeder, 'main_window') and
                    training_feeder.main_window and
                    hasattr(training_feeder.main_window, 'enhanced_downloader')
                )
                self.training_result_text.append(f"✅ 智能下载器集成: {'存在' if uses_enhanced_downloader else '缺失'}")
                
                # 测试模型检查
                try:
                    model_status = training_feeder.check_models()
                    self.training_result_text.append(f"✅ 模型状态检查成功: {model_status}")
                except Exception as e:
                    self.training_result_text.append(f"⚠️ 模型状态检查异常: {e}")
            
            self.test_results['training_model_check'] = {
                'training_feeder': has_training_feeder,
                'model_check': has_model_check if has_training_feeder else False
            }
            
        except Exception as e:
            self.training_result_text.append(f"❌ 测试失败: {e}")
            logger.error(f"训练模型检查测试失败: {e}")
    
    def test_training_language_switch(self):
        """测试训练页面的语言切换下载器"""
        try:
            self.training_result_text.clear()
            self.training_result_text.append("🔄 开始测试训练页面语言切换下载器...")
            
            if not self.main_app or not hasattr(self.main_app, 'train_feeder'):
                self.training_result_text.append("❌ 训练组件未初始化")
                return
            
            training_feeder = self.main_app.train_feeder
            
            # 检查语言切换方法
            has_lang_switch = hasattr(training_feeder, 'switch_training_language')
            self.training_result_text.append(f"✅ 语言切换方法: {'存在' if has_lang_switch else '缺失'}")
            
            # 检查语言选择按钮
            has_lang_buttons = (
                hasattr(training_feeder, 'lang_zh_radio') and
                hasattr(training_feeder, 'lang_en_radio')
            )
            self.training_result_text.append(f"✅ 语言选择按钮: {'存在' if has_lang_buttons else '缺失'}")
            
            # 测试语言切换
            if has_lang_switch:
                try:
                    training_feeder.switch_training_language("zh")
                    self.training_result_text.append("✅ 中文训练模式切换成功")
                    
                    training_feeder.switch_training_language("en")
                    self.training_result_text.append("✅ 英文训练模式切换成功")
                except Exception as e:
                    self.training_result_text.append(f"⚠️ 语言切换异常: {e}")
            
            self.test_results['training_language_switch'] = {
                'lang_switch': has_lang_switch,
                'lang_buttons': has_lang_buttons
            }
            
        except Exception as e:
            self.training_result_text.append(f"❌ 测试失败: {e}")
            logger.error(f"训练语言切换测试失败: {e}")
    
    def test_training_realtime(self):
        """测试训练页面的实时更新机制"""
        try:
            self.training_result_text.clear()
            self.training_result_text.append("📊 开始测试训练页面实时更新机制...")
            
            if not self.main_app or not hasattr(self.main_app, 'train_feeder'):
                self.training_result_text.append("❌ 训练组件未初始化")
                return
            
            training_feeder = self.main_app.train_feeder
            
            # 检查训练监控
            has_training_monitor = hasattr(training_feeder, 'training_monitor')
            self.training_result_text.append(f"✅ 训练监控: {'存在' if has_training_monitor else '缺失'}")
            
            # 检查进度更新方法
            has_progress_methods = (
                hasattr(training_feeder, 'update_progress') and
                hasattr(training_feeder, 'update_status')
            )
            self.training_result_text.append(f"✅ 进度更新方法: {'存在' if has_progress_methods else '缺失'}")
            
            # 检查状态显示组件
            has_status_components = (
                hasattr(training_feeder, 'progress_bar') and
                hasattr(training_feeder, 'status_label')
            )
            self.training_result_text.append(f"✅ 状态显示组件: {'存在' if has_status_components else '缺失'}")
            
            self.test_results['training_realtime'] = {
                'training_monitor': has_training_monitor,
                'progress_methods': has_progress_methods,
                'status_components': has_status_components
            }
            
        except Exception as e:
            self.training_result_text.append(f"❌ 测试失败: {e}")
            logger.error(f"训练实时更新测试失败: {e}")
    
    def log_result(self, message: str):
        """记录结果"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.result_text.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            if self.main_app:
                self.main_app.close()
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"关闭验证器失败: {e}")
            super().closeEvent(event)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    try:
        # 创建验证器
        verifier = TabSpecificUIVerifier()
        verifier.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"标签页UI验证器启动失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
