#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态下载器集成测试脚本 - VisionAI-ClipsMaster
测试动态硬件监控、模型推荐和实时适配功能
"""

import sys
import time
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DynamicDownloaderTestWindow(QMainWindow):
    """动态下载器测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_test_components()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("🧪 动态下载器集成测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("🎯 VisionAI-ClipsMaster 动态下载器集成测试")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 状态显示
        self.status_label = QLabel("🔍 正在初始化测试组件...")
        self.status_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)
        
        # 测试按钮
        self.test_hardware_btn = QPushButton("🔧 测试硬件监控")
        self.test_hardware_btn.clicked.connect(self.test_hardware_monitoring)
        layout.addWidget(self.test_hardware_btn)
        
        self.test_qwen_btn = QPushButton("🤖 测试Qwen模型推荐")
        self.test_qwen_btn.clicked.connect(self.test_qwen_recommendation)
        layout.addWidget(self.test_qwen_btn)
        
        self.test_mistral_btn = QPushButton("🤖 测试Mistral模型推荐")
        self.test_mistral_btn.clicked.connect(self.test_mistral_recommendation)
        layout.addWidget(self.test_mistral_btn)
        
        self.test_integration_btn = QPushButton("🎯 测试完整集成")
        self.test_integration_btn.clicked.connect(self.test_full_integration)
        layout.addWidget(self.test_integration_btn)
        
        # 结果显示
        self.result_label = QLabel("📋 测试结果将在这里显示...")
        self.result_label.setStyleSheet("""
            margin: 10px; 
            padding: 15px; 
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-family: monospace;
        """)
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
    
    def setup_test_components(self):
        """设置测试组件"""
        try:
            # 测试导入
            self.test_imports()
            
            # 初始化集成管理器
            from src.ui.dynamic_downloader_integration import DynamicDownloaderIntegration
            self.integration = DynamicDownloaderIntegration(self)
            
            # 注册回调
            self.integration.register_download_callback(self.on_test_download_completed)
            self.integration.register_hardware_change_callback(self.on_test_hardware_changed)
            
            self.status_label.setText("✅ 测试组件初始化完成")
            
        except Exception as e:
            logger.error(f"设置测试组件失败: {e}")
            self.status_label.setText(f"❌ 初始化失败: {e}")
    
    def test_imports(self):
        """测试导入"""
        try:
            # 测试硬件监控组件
            from src.ui.dynamic_hardware_monitor import RealTimeHardwareInfoWidget, HardwareSnapshot
            logger.info("✅ 硬件监控组件导入成功")
            
            # 测试模型推荐组件
            from src.ui.dynamic_model_recommendation import DynamicModelRecommendationWidget, ModelVariantInfo
            logger.info("✅ 模型推荐组件导入成功")
            
            # 测试增强对话框
            from src.ui.enhanced_smart_downloader_dialog import EnhancedSmartDownloaderDialog
            logger.info("✅ 增强对话框导入成功")
            
            # 测试集成管理器
            from src.ui.dynamic_downloader_integration import DynamicDownloaderIntegration
            logger.info("✅ 集成管理器导入成功")
            
            return True
            
        except ImportError as e:
            logger.error(f"导入测试失败: {e}")
            raise
    
    def test_hardware_monitoring(self):
        """测试硬件监控"""
        try:
            self.status_label.setText("🔧 正在测试硬件监控...")
            
            from src.ui.dynamic_hardware_monitor import RealTimeHardwareInfoWidget
            
            # 创建硬件监控组件
            hardware_widget = RealTimeHardwareInfoWidget()
            
            # 获取硬件信息
            QTimer.singleShot(2000, lambda: self.check_hardware_info(hardware_widget))
            
        except Exception as e:
            logger.error(f"硬件监控测试失败: {e}")
            self.result_label.setText(f"❌ 硬件监控测试失败: {e}")
    
    def check_hardware_info(self, hardware_widget):
        """检查硬件信息"""
        try:
            hardware_info = hardware_widget.get_hardware_info()
            
            if hardware_info:
                result_text = f"""
🔧 硬件监控测试结果:
✅ 检测成功
🎮 GPU类型: {hardware_info.get('gpu_type', 'N/A')}
💾 GPU显存: {hardware_info.get('gpu_memory_gb', 0):.1f} GB
🧠 系统内存: {hardware_info.get('system_ram_gb', 0):.1f} GB
⚡ CPU核心: {hardware_info.get('cpu_cores', 0)}
📊 性能等级: {hardware_info.get('performance_level', 'N/A')}
🎯 推荐量化: {hardware_info.get('recommended_quantization', 'N/A')}
"""
                self.result_label.setText(result_text.strip())
                self.status_label.setText("✅ 硬件监控测试完成")
            else:
                self.result_label.setText("❌ 硬件信息获取失败")
                self.status_label.setText("❌ 硬件监控测试失败")
            
            # 清理
            hardware_widget.stop_monitoring()
            
        except Exception as e:
            logger.error(f"检查硬件信息失败: {e}")
            self.result_label.setText(f"❌ 硬件信息检查失败: {e}")
    
    def test_qwen_recommendation(self):
        """测试Qwen模型推荐"""
        try:
            self.status_label.setText("🤖 正在测试Qwen模型推荐...")
            
            # 获取推荐
            recommendation = self.integration.get_model_recommendation("qwen2.5-7b")
            
            if recommendation:
                result_text = f"""
🤖 Qwen模型推荐测试结果:
✅ 推荐成功
📦 模型名称: {recommendation.get('model_name', 'N/A')}
🏷️ 变体名称: {recommendation.get('variant_name', 'N/A')}
⚙️ 量化等级: {recommendation.get('quantization', 'N/A')}
📏 文件大小: {recommendation.get('size_gb', 0):.1f} GB
📊 质量保持: {recommendation.get('quality_retention', 0):.1%}
🎯 推荐理由: {recommendation.get('recommendation_reason', 'N/A')}
"""
                self.result_label.setText(result_text.strip())
                self.status_label.setText("✅ Qwen模型推荐测试完成")
            else:
                self.result_label.setText("❌ Qwen模型推荐获取失败")
                self.status_label.setText("❌ Qwen模型推荐测试失败")
                
        except Exception as e:
            logger.error(f"Qwen模型推荐测试失败: {e}")
            self.result_label.setText(f"❌ Qwen模型推荐测试失败: {e}")
    
    def test_mistral_recommendation(self):
        """测试Mistral模型推荐"""
        try:
            self.status_label.setText("🤖 正在测试Mistral模型推荐...")
            
            # 获取推荐
            recommendation = self.integration.get_model_recommendation("mistral-7b")
            
            if recommendation:
                result_text = f"""
🤖 Mistral模型推荐测试结果:
✅ 推荐成功
📦 模型名称: {recommendation.get('model_name', 'N/A')}
🏷️ 变体名称: {recommendation.get('variant_name', 'N/A')}
⚙️ 量化等级: {recommendation.get('quantization', 'N/A')}
📏 文件大小: {recommendation.get('size_gb', 0):.1f} GB
📊 质量保持: {recommendation.get('quality_retention', 0):.1%}
🎯 推荐理由: {recommendation.get('recommendation_reason', 'N/A')}
"""
                self.result_label.setText(result_text.strip())
                self.status_label.setText("✅ Mistral模型推荐测试完成")
            else:
                self.result_label.setText("❌ Mistral模型推荐获取失败")
                self.status_label.setText("❌ Mistral模型推荐测试失败")
                
        except Exception as e:
            logger.error(f"Mistral模型推荐测试失败: {e}")
            self.result_label.setText(f"❌ Mistral模型推荐测试失败: {e}")
    
    def test_full_integration(self):
        """测试完整集成"""
        try:
            self.status_label.setText("🎯 正在测试完整集成...")
            
            # 显示智能下载器对话框
            result = self.integration.show_smart_downloader("qwen2.5-7b", self)
            
            if result:
                self.result_label.setText("✅ 完整集成测试：用户完成了下载流程")
                self.status_label.setText("✅ 完整集成测试完成")
            else:
                self.result_label.setText("ℹ️ 完整集成测试：用户取消了下载流程")
                self.status_label.setText("ℹ️ 完整集成测试完成（用户取消）")
                
        except Exception as e:
            logger.error(f"完整集成测试失败: {e}")
            self.result_label.setText(f"❌ 完整集成测试失败: {e}")
    
    def on_test_download_completed(self, model_name: str, variant_info, success: bool):
        """测试下载完成回调"""
        logger.info(f"测试下载完成回调: {model_name}, 成功: {success}")
        
        if success:
            self.result_label.setText(f"✅ 下载测试完成: {model_name} ({variant_info.name})")
        else:
            self.result_label.setText(f"❌ 下载测试失败: {model_name}")
    
    def on_test_hardware_changed(self, hardware_snapshot):
        """测试硬件变化回调"""
        logger.info("测试硬件变化回调触发")
        self.status_label.setText("🔄 检测到硬件配置变化")
    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            if hasattr(self, 'integration'):
                self.integration.cleanup()
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"关闭测试窗口失败: {e}")
            super().closeEvent(event)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    try:
        # 创建测试窗口
        window = DynamicDownloaderTestWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"测试应用启动失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
