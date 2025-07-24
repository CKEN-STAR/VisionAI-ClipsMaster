#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能推荐下载器UI测试脚本

测试优化的智能推荐下载器UI的各项功能：
1. 硬件信息实时检测和显示
2. 智能推荐动态更新
3. 设备变化响应
4. UI组件集成
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import QTimer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能推荐下载器UI测试")
        self.resize(1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 添加标题
        title_label = QLabel("🤖 智能推荐下载器UI测试")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        
        # 测试按钮
        self.create_test_buttons(layout)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: green; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # 初始化智能下载器集成
        self.init_smart_downloader_integration()
    
    def create_test_buttons(self, layout):
        """创建测试按钮"""
        
        # 测试1: 显示智能下载器对话框
        btn1 = QPushButton("🎯 测试智能下载器对话框")
        btn1.clicked.connect(self.test_smart_downloader_dialog)
        layout.addWidget(btn1)
        
        # 测试2: 显示硬件信息组件
        btn2 = QPushButton("🔧 测试硬件信息组件")
        btn2.clicked.connect(self.test_hardware_info_widget)
        layout.addWidget(btn2)
        
        # 测试3: 显示推荐组件
        btn3 = QPushButton("💡 测试推荐组件")
        btn3.clicked.connect(self.test_recommendation_widget)
        layout.addWidget(btn3)
        
        # 测试4: 测试集成管理器
        btn4 = QPushButton("⚙️ 测试集成管理器")
        btn4.clicked.connect(self.test_integration_manager)
        layout.addWidget(btn4)
        
        # 测试5: 测试主UI集成
        btn5 = QPushButton("🏠 测试主UI集成")
        btn5.clicked.connect(self.test_main_ui_integration)
        layout.addWidget(btn5)
        
        # 测试6: 模拟设备变化
        btn6 = QPushButton("🔄 模拟设备变化")
        btn6.clicked.connect(self.test_device_change_simulation)
        layout.addWidget(btn6)
    
    def init_smart_downloader_integration(self):
        """初始化智能下载器集成"""
        try:
            from src.ui.smart_downloader_integration_enhanced import (
                initialize_smart_downloader_integration,
                get_integration_manager
            )
            
            # 定义下载回调
            def download_callback(model_name, variant_info):
                logger.info(f"下载回调触发: {model_name}")
                logger.info(f"变体信息: {variant_info}")
                
                QMessageBox.information(
                    self,
                    "下载模拟",
                    f"模拟下载 {model_name}\n\n"
                    f"变体: {variant_info.get('variant_name', 'unknown')}\n"
                    f"量化: {variant_info.get('quantization', 'unknown')}\n"
                    f"大小: {variant_info.get('size_gb', 0):.1f} GB"
                )
            
            # 初始化集成
            success = initialize_smart_downloader_integration(download_callback)
            
            if success:
                self.integration_manager = get_integration_manager()
                self.status_label.setText("✅ 智能下载器集成初始化成功")
                logger.info("智能下载器集成初始化成功")
            else:
                self.integration_manager = None
                self.status_label.setText("❌ 智能下载器集成初始化失败")
                logger.error("智能下载器集成初始化失败")
                
        except Exception as e:
            self.integration_manager = None
            self.status_label.setText(f"❌ 集成初始化异常: {e}")
            logger.error(f"集成初始化异常: {e}")
    
    def test_smart_downloader_dialog(self):
        """测试智能下载器对话框"""
        try:
            from src.ui.smart_downloader_ui_optimized import SmartDownloaderDialog
            
            # 创建对话框
            dialog = SmartDownloaderDialog("qwen2.5-7b", self)
            
            # 连接下载信号
            def on_download_requested(model_name, variant_info):
                QMessageBox.information(
                    self,
                    "下载请求",
                    f"用户请求下载: {model_name}\n\n"
                    f"推荐变体: {variant_info.get('variant_name', 'unknown')}\n"
                    f"量化等级: {variant_info.get('quantization', 'unknown')}\n"
                    f"模型大小: {variant_info.get('size_gb', 0):.1f} GB\n"
                    f"内存需求: {variant_info.get('memory_requirement_gb', 0):.1f} GB"
                )
            
            dialog.download_requested.connect(on_download_requested)
            
            # 显示对话框
            result = dialog.exec()
            
            if result == dialog.DialogCode.Accepted:
                self.status_label.setText("✅ 用户确认下载")
            else:
                self.status_label.setText("ℹ️ 用户取消下载")
                
        except Exception as e:
            logger.error(f"测试智能下载器对话框失败: {e}")
            QMessageBox.critical(self, "测试失败", f"智能下载器对话框测试失败:\n{e}")
    
    def test_hardware_info_widget(self):
        """测试硬件信息组件"""
        try:
            from src.ui.smart_downloader_ui_optimized import RealTimeHardwareInfoWidget
            from PyQt6.QtWidgets import QDialog, QVBoxLayout
            
            # 创建测试对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("硬件信息组件测试")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 添加硬件信息组件
            hardware_widget = RealTimeHardwareInfoWidget()
            layout.addWidget(hardware_widget)
            
            # 添加关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            # 显示对话框
            dialog.exec()
            
            self.status_label.setText("✅ 硬件信息组件测试完成")
            
        except Exception as e:
            logger.error(f"测试硬件信息组件失败: {e}")
            QMessageBox.critical(self, "测试失败", f"硬件信息组件测试失败:\n{e}")
    
    def test_recommendation_widget(self):
        """测试推荐组件"""
        try:
            from src.ui.smart_downloader_ui_optimized import DynamicRecommendationWidget
            from PyQt6.QtWidgets import QDialog, QVBoxLayout
            
            # 创建测试对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("推荐组件测试")
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # 添加推荐组件
            recommendation_widget = DynamicRecommendationWidget("qwen2.5-7b")
            layout.addWidget(recommendation_widget)
            
            # 添加刷新按钮
            refresh_btn = QPushButton("🔄 刷新推荐")
            refresh_btn.clicked.connect(recommendation_widget.refresh_recommendation)
            layout.addWidget(refresh_btn)
            
            # 添加关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            # 启动推荐刷新
            QTimer.singleShot(500, recommendation_widget.refresh_recommendation)
            
            # 显示对话框
            dialog.exec()
            
            self.status_label.setText("✅ 推荐组件测试完成")
            
        except Exception as e:
            logger.error(f"测试推荐组件失败: {e}")
            QMessageBox.critical(self, "测试失败", f"推荐组件测试失败:\n{e}")
    
    def test_integration_manager(self):
        """测试集成管理器"""
        try:
            if not self.integration_manager:
                QMessageBox.warning(self, "测试失败", "集成管理器未初始化")
                return
            
            # 获取集成状态
            status = self.integration_manager.get_integration_status()
            
            # 获取硬件信息
            hardware_info = self.integration_manager.get_hardware_info(force_refresh=True)
            
            # 获取推荐信息
            recommendation_info = self.integration_manager.get_recommendation("qwen2.5-7b", force_refresh=True)
            
            # 显示结果
            result_text = "🔧 集成管理器测试结果:\n\n"
            result_text += f"初始化状态: {status['is_initialized']}\n"
            result_text += f"组件状态: {status['components']}\n\n"
            
            if hardware_info:
                result_text += f"硬件信息:\n"
                result_text += f"  GPU类型: {hardware_info.get('gpu_type', 'unknown')}\n"
                result_text += f"  GPU内存: {hardware_info.get('gpu_memory_gb', 0):.1f} GB\n"
                result_text += f"  系统内存: {hardware_info.get('system_ram_gb', 0):.1f} GB\n\n"
            
            if recommendation_info:
                result_text += f"推荐信息:\n"
                result_text += f"  推荐变体: {recommendation_info.get('variant_name', 'unknown')}\n"
                result_text += f"  量化等级: {recommendation_info.get('quantization', 'unknown')}\n"
                result_text += f"  模型大小: {recommendation_info.get('size_gb', 0):.1f} GB\n"
            
            QMessageBox.information(self, "集成管理器测试", result_text)
            self.status_label.setText("✅ 集成管理器测试完成")
            
        except Exception as e:
            logger.error(f"测试集成管理器失败: {e}")
            QMessageBox.critical(self, "测试失败", f"集成管理器测试失败:\n{e}")
    
    def test_main_ui_integration(self):
        """测试主UI集成"""
        try:
            from src.ui.main_ui_integration import integrate_smart_downloader_to_main_ui
            
            # 创建新的测试窗口
            test_window = QMainWindow()
            test_window.setWindowTitle("主UI集成测试")
            test_window.resize(800, 600)
            
            # 集成智能下载器
            integrator = integrate_smart_downloader_to_main_ui(test_window)
            
            # 显示测试窗口
            test_window.show()
            
            QMessageBox.information(
                self,
                "主UI集成测试",
                "已创建集成测试窗口！\n\n"
                "请检查:\n"
                "• 菜单栏中的智能下载器选项\n"
                "• 工具栏中的智能下载器按钮\n"
                "• 状态栏中的硬件信息显示\n"
                "• 快捷键 Ctrl+Shift+D"
            )
            
            self.status_label.setText("✅ 主UI集成测试完成")
            
        except Exception as e:
            logger.error(f"测试主UI集成失败: {e}")
            QMessageBox.critical(self, "测试失败", f"主UI集成测试失败:\n{e}")
    
    def test_device_change_simulation(self):
        """模拟设备变化测试"""
        try:
            if not self.integration_manager:
                QMessageBox.warning(self, "测试失败", "集成管理器未初始化")
                return
            
            # 模拟设备变化 - 强制刷新硬件信息
            self.status_label.setText("🔄 模拟设备变化中...")
            
            def refresh_complete():
                self.status_label.setText("✅ 设备变化模拟完成")
                QMessageBox.information(
                    self,
                    "设备变化模拟",
                    "已模拟设备变化并刷新硬件信息！\n\n"
                    "在实际使用中，当检测到硬件变化时，\n"
                    "系统会自动刷新硬件信息和推荐内容。"
                )
            
            # 延迟执行刷新
            QTimer.singleShot(1000, lambda: self.integration_manager.get_hardware_info(force_refresh=True))
            QTimer.singleShot(2000, refresh_complete)
            
        except Exception as e:
            logger.error(f"设备变化模拟测试失败: {e}")
            QMessageBox.critical(self, "测试失败", f"设备变化模拟测试失败:\n{e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("智能推荐下载器UI测试")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = TestMainWindow()
    window.show()
    
    # 运行应用
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
