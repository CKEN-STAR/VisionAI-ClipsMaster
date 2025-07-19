#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 增强下载对话框
提供直观友好的模型下载确认界面，集成智能推荐功能
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QProgressBar, QFrame, QScrollArea,
    QWidget, QTabWidget, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class HardwareInfoWidget(QFrame):
    """硬件信息显示组件"""
    
    def __init__(self, hardware_info: Dict):
        super().__init__()
        self.hardware_info = hardware_info
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🔧 检测到的硬件配置")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 硬件信息网格
        grid_layout = QGridLayout()
        
        # GPU信息
        gpu_label = QLabel("GPU内存:")
        gpu_value = QLabel(f"{self.hardware_info.get('gpu_memory_gb', 0):.1f} GB")
        if self.hardware_info.get('has_gpu', False):
            gpu_value.setStyleSheet("color: green; font-weight: bold;")
        else:
            gpu_value.setStyleSheet("color: orange;")
            gpu_value.setText("无GPU (将使用CPU)")
        
        grid_layout.addWidget(gpu_label, 0, 0)
        grid_layout.addWidget(gpu_value, 0, 1)
        
        # 系统内存
        ram_label = QLabel("系统内存:")
        ram_value = QLabel(f"{self.hardware_info.get('system_ram_gb', 0):.1f} GB")
        ram_value.setStyleSheet("color: blue; font-weight: bold;")
        grid_layout.addWidget(ram_label, 1, 0)
        grid_layout.addWidget(ram_value, 1, 1)
        
        # 存储空间
        storage_label = QLabel("可用存储:")
        storage_value = QLabel(f"{self.hardware_info.get('storage_available_gb', 0):.1f} GB")
        storage_value.setStyleSheet("color: green; font-weight: bold;")
        grid_layout.addWidget(storage_label, 2, 0)
        grid_layout.addWidget(storage_value, 2, 1)
        
        # CPU核心
        cpu_label = QLabel("CPU核心:")
        cpu_value = QLabel(f"{self.hardware_info.get('cpu_cores', 0)} 核")
        cpu_value.setStyleSheet("color: purple; font-weight: bold;")
        grid_layout.addWidget(cpu_label, 3, 0)
        grid_layout.addWidget(cpu_value, 3, 1)
        
        layout.addLayout(grid_layout)

class ModelVariantWidget(QFrame):
    """模型变体显示组件"""
    
    selected = pyqtSignal(dict)
    
    def __init__(self, variant_info: Dict, is_recommended: bool = False):
        super().__init__()
        self.variant_info = variant_info
        self.is_recommended = is_recommended
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        
        if self.is_recommended:
            self.setStyleSheet("""
                QFrame {
                    border: 3px solid #4CAF50;
                    border-radius: 12px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8fff8, stop:1 #e8f5e8);
                    margin: 8px;
                    padding: 15px;
                }
                QFrame:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f0fff0, stop:1 #d8f5d8);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #fafafa;
                    margin: 5px;
                    padding: 12px;
                }
                QFrame:hover {
                    border-color: #2196F3;
                    background-color: #f0f8ff;
                }
            """)
        
        layout = QVBoxLayout(self)
        
        # 标题行
        title_layout = QHBoxLayout()
        
        if self.is_recommended:
            recommend_label = QLabel("🏆 智能推荐")
            recommend_label.setStyleSheet("""
                color: #4CAF50; 
                font-weight: bold; 
                font-size: 14px;
                background-color: rgba(76, 175, 80, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
            """)
            title_layout.addWidget(recommend_label)
        
        title_layout.addStretch()
        
        # 选择按钮
        self.select_btn = QPushButton("选择此版本")
        if self.is_recommended:
            self.select_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            self.select_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        
        self.select_btn.clicked.connect(self.on_select)
        title_layout.addWidget(self.select_btn)
        
        layout.addLayout(title_layout)
        
        # 版本信息
        variant = self.variant_info.get('variant')
        if variant:
            # 版本名称
            name_label = QLabel(f"<b>{variant.name}</b>")
            name_label.setStyleSheet("font-size: 14px; color: #333; margin-bottom: 8px;")
            layout.addWidget(name_label)
            
            # 信息网格
            info_grid = QGridLayout()
            
            # 大小
            size_icon = QLabel("📦")
            size_label = QLabel("大小:")
            size_value = QLabel(f"{variant.size_gb:.1f} GB")
            size_value.setStyleSheet("font-weight: bold; color: #666;")
            info_grid.addWidget(size_icon, 0, 0)
            info_grid.addWidget(size_label, 0, 1)
            info_grid.addWidget(size_value, 0, 2)
            
            # 内存需求
            memory_icon = QLabel("💾")
            memory_label = QLabel("内存需求:")
            memory_value = QLabel(f"{variant.memory_requirement_gb:.1f} GB")
            memory_value.setStyleSheet("font-weight: bold; color: #666;")
            info_grid.addWidget(memory_icon, 1, 0)
            info_grid.addWidget(memory_label, 1, 1)
            info_grid.addWidget(memory_value, 1, 2)
            
            # 质量保持
            quality_icon = QLabel("🎯")
            quality_label = QLabel("质量保持:")
            quality_value = QLabel(f"{variant.quality_retention:.1%}")
            if variant.quality_retention >= 0.95:
                quality_value.setStyleSheet("font-weight: bold; color: green;")
            elif variant.quality_retention >= 0.90:
                quality_value.setStyleSheet("font-weight: bold; color: orange;")
            else:
                quality_value.setStyleSheet("font-weight: bold; color: red;")
            info_grid.addWidget(quality_icon, 2, 0)
            info_grid.addWidget(quality_label, 2, 1)
            info_grid.addWidget(quality_value, 2, 2)
            
            # 推理速度
            speed_icon = QLabel("⚡")
            speed_label = QLabel("推理速度:")
            speed_value = QLabel(f"{variant.inference_speed_factor:.1%}")
            speed_value.setStyleSheet("font-weight: bold; color: #666;")
            info_grid.addWidget(speed_icon, 3, 0)
            info_grid.addWidget(speed_label, 3, 1)
            info_grid.addWidget(speed_value, 3, 2)
            
            # CPU兼容
            cpu_icon = QLabel("🖥️")
            cpu_label = QLabel("CPU兼容:")
            cpu_value = QLabel("是" if variant.cpu_compatible else "否")
            cpu_value.setStyleSheet(f"font-weight: bold; color: {'green' if variant.cpu_compatible else 'red'};")
            info_grid.addWidget(cpu_icon, 4, 0)
            info_grid.addWidget(cpu_label, 4, 1)
            info_grid.addWidget(cpu_value, 4, 2)
            
            layout.addLayout(info_grid)
        
        # 兼容性信息
        compatibility = self.variant_info.get('compatibility', {})
        if compatibility:
            compat_layout = QHBoxLayout()
            
            compat_score = compatibility.get('compatibility_score', 0)
            is_compatible = compatibility.get('is_compatible', False)
            
            compat_icon = QLabel("✅" if is_compatible else "⚠️")
            compat_text = f"兼容性: {compat_score:.1%}"
            compat_label = QLabel(compat_text)
            compat_label.setStyleSheet(f"color: {'green' if is_compatible else 'orange'}; font-weight: bold;")
            
            compat_layout.addWidget(compat_icon)
            compat_layout.addWidget(compat_label)
            compat_layout.addStretch()
            
            layout.addLayout(compat_layout)
    
    def on_select(self):
        """选择此变体"""
        self.selected.emit(self.variant_info)

class EnhancedDownloadDialog(QDialog):
    """增强下载对话框"""
    
    def __init__(self, model_name: str, recommendation: Dict, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.recommendation = recommendation
        self.selected_variant = None

        # 最强防护：多层验证机制
        logger.info(f"🔍 创建下载对话框: 请求模型={model_name}")

        # 第一层：基础验证
        if recommendation and hasattr(recommendation, 'model_name'):
            if recommendation.model_name != model_name:
                logger.error(f"❌ 对话框推荐内容不一致: 请求={model_name}, 推荐={recommendation.model_name}")
                # 强制关闭对话框并抛出异常
                self.close()
                raise ValueError(f"推荐内容与请求的模型名称不一致: {model_name} vs {recommendation.model_name}")

        # 第二层：变体名称验证
        if recommendation and hasattr(recommendation, 'variant'):
            variant_name = recommendation.variant.name.lower()
            model_key = model_name.lower().replace('-', '').replace('.', '')

            # 严格的变体匹配验证
            is_valid = False
            expected_keywords = []

            if 'mistral' in model_key:
                expected_keywords = ['mistral']
                is_valid = any(keyword in variant_name for keyword in expected_keywords)
            elif 'qwen' in model_key:
                expected_keywords = ['qwen']
                is_valid = any(keyword in variant_name for keyword in expected_keywords)

            if not is_valid:
                logger.error(f"❌ 变体名称与模型不匹配: 模型={model_name}, 变体={variant_name}, 期望关键词={expected_keywords}")
                self.close()
                raise ValueError(f"变体名称与模型不匹配: {model_name} vs {recommendation.variant.name}")

        # 第三层：窗口标题验证（额外保险）
        expected_title_keywords = []
        if 'mistral' in model_name.lower():
            expected_title_keywords = ['mistral', 'english', '英文']
        elif 'qwen' in model_name.lower():
            expected_title_keywords = ['qwen', 'chinese', '中文']

        # 第四层：运行时状态验证（最关键的修复）
        # 在对话框显示前，最后一次验证推荐内容
        if recommendation and hasattr(recommendation, 'variant'):
            final_check_passed = False

            # 英文模型验证
            if model_name.lower() in ['mistral-7b', 'mistral']:
                if 'mistral' in recommendation.variant.name.lower():
                    final_check_passed = True
                    logger.info(f"✅ 英文模型最终验证通过: {model_name} -> {recommendation.variant.name}")
                else:
                    logger.error(f"❌ 英文模型最终验证失败: 请求={model_name}, 推荐变体={recommendation.variant.name}")

            # 中文模型验证
            elif model_name.lower() in ['qwen2.5-7b', 'qwen']:
                if 'qwen' in recommendation.variant.name.lower():
                    final_check_passed = True
                    logger.info(f"✅ 中文模型最终验证通过: {model_name} -> {recommendation.variant.name}")
                else:
                    logger.error(f"❌ 中文模型最终验证失败: 请求={model_name}, 推荐变体={recommendation.variant.name}")

            if not final_check_passed:
                logger.error(f"❌ 对话框最终验证失败，强制关闭")
                self.close()
                raise ValueError(f"对话框内容与请求模型严重不匹配: {model_name} vs {recommendation.variant.name}")

        self.setup_ui()

        # 第四层：UI设置后的最终验证
        window_title = self.windowTitle().lower()
        if expected_title_keywords:
            title_valid = any(keyword.lower() in window_title for keyword in expected_title_keywords)
            if not title_valid:
                logger.error(f"❌ 窗口标题验证失败: 标题={self.windowTitle()}, 期望关键词={expected_title_keywords}")
                self.close()
                raise ValueError(f"窗口标题与模型不匹配: {self.windowTitle()} for {model_name}")

        # 自动选择推荐版本
        if recommendation and hasattr(recommendation, 'variant'):
            self.selected_variant = {
                'variant': recommendation.variant,
                'compatibility': recommendation.compatibility_assessment
            }
            self.update_download_button()
            logger.info(f"✅ 对话框内容验证通过: {model_name} -> {recommendation.variant.name}")

        # 最终确认日志
        logger.info(f"🎯 对话框创建完成: 模型={model_name}, 变体={recommendation.variant.name if recommendation and hasattr(recommendation, 'variant') else 'None'}, 标题={self.windowTitle()}")
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"模型下载 - {self.model_name}")
        # 缩小对话框尺寸到原来的80%（900*0.8=720, 700*0.8=560）
        self.setMinimumSize(720, 560)
        self.setMaximumSize(900, 700)  # 设置最大尺寸限制
        self.resize(720, 560)  # 设置默认尺寸
        self.setModal(True)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"🤖 {self.model_name} 模型下载")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px; padding: 10px;")
        layout.addWidget(title_label)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #2196F3;
            }
        """)
        
        # 智能推荐标签页
        recommend_tab = self.create_recommendation_tab()
        tab_widget.addTab(recommend_tab, "🏆 智能推荐")

        # 硬件信息标签页
        hardware_tab = self.create_hardware_tab()
        tab_widget.addTab(hardware_tab, "🔧 硬件信息")
        
        layout.addWidget(tab_widget)
        
        # 底部按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 15px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        
        # 下载信息显示
        self.download_info_label = QLabel("请选择要下载的模型版本")
        self.download_info_label.setStyleSheet("color: #666; font-style: italic;")
        button_layout.addWidget(self.download_info_label)
        
        button_layout.addStretch()
        
        # 按钮
        self.download_btn = QPushButton("📥 开始下载")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addWidget(button_frame)
        
        # 连接信号 - 使用安全的信号连接
        self.download_btn.clicked.connect(self.safe_accept)
        cancel_btn.clicked.connect(self.safe_reject)

        # 初始状态
        self.update_download_button()
    
    def create_recommendation_tab(self) -> QWidget:
        """创建推荐标签页"""
        # 创建主容器
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 创建滚动内容容器
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        if not self.recommendation:
            layout.addWidget(QLabel("暂无推荐信息"))
            scroll_area.setWidget(scroll_widget)
            main_layout.addWidget(scroll_area)
            return main_widget
        
        # 推荐说明
        intro_label = QLabel("""
        <h3>🎯 基于您的硬件配置，我们为您推荐以下版本：</h3>
        <p style="color: #666;">我们的智能算法分析了您的硬件配置、性能需求和使用场景，为您选择了最适合的模型版本。</p>
        """)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # 推荐版本卡片
        recommended_card = ModelVariantWidget({
            'variant': self.recommendation.variant,
            'compatibility': self.recommendation.compatibility_assessment
        }, is_recommended=True)
        
        recommended_card.selected.connect(self.on_variant_selected)
        layout.addWidget(recommended_card)
        
        # 推荐理由
        if hasattr(self.recommendation, 'reasoning') and self.recommendation.reasoning:
            reasoning_group = QGroupBox("💡 推荐理由")
            reasoning_layout = QVBoxLayout(reasoning_group)
            
            reasoning_text = QTextEdit()
            reasoning_text.setPlainText("\n".join(self.recommendation.reasoning))
            reasoning_text.setMaximumHeight(120)
            reasoning_text.setReadOnly(True)
            reasoning_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            reasoning_layout.addWidget(reasoning_text)
            
            layout.addWidget(reasoning_group)
        
        # 部署说明
        if hasattr(self.recommendation, 'deployment_notes') and self.recommendation.deployment_notes:
            deploy_group = QGroupBox("🚀 部署说明")
            deploy_layout = QVBoxLayout(deploy_group)
            
            deploy_text = QTextEdit()
            deploy_text.setPlainText("\n".join(self.recommendation.deployment_notes))
            deploy_text.setMaximumHeight(100)
            deploy_text.setReadOnly(True)
            deploy_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            deploy_layout.addWidget(deploy_text)
            
            layout.addWidget(deploy_group)
        
        layout.addStretch()

        # 将滚动内容设置到滚动区域
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        return main_widget
    
    def create_hardware_tab(self) -> QWidget:
        """创建硬件信息标签页"""
        # 创建主容器
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 创建滚动内容容器
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 硬件信息
        try:
            # 修复导入路径 - 尝试多种导入方式
            import sys
            from pathlib import Path

            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))

            # 添加src目录到路径
            src_path = Path(__file__).parent.parent
            sys.path.insert(0, str(src_path))

            # 尝试导入硬件检测器
            try:
                from src.core.quantization_analysis import HardwareDetector
            except ImportError:
                try:
                    from core.quantization_analysis import HardwareDetector
                except ImportError:
                    # 直接使用绝对路径导入
                    hardware_path = Path(__file__).parent.parent / "core" / "quantization_analysis.py"
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("quantization_analysis", hardware_path)
                    hardware_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(hardware_module)
                    HardwareDetector = hardware_module.HardwareDetector
            hardware = HardwareDetector.detect_hardware()
            
            hardware_info = {
                'gpu_memory_gb': hardware.gpu_memory_gb,
                'system_ram_gb': hardware.system_ram_gb,
                'storage_available_gb': hardware.storage_available_gb,
                'cpu_cores': hardware.cpu_cores,
                'has_gpu': hardware.has_gpu
            }
            
            hardware_widget = HardwareInfoWidget(hardware_info)
            layout.addWidget(hardware_widget)
            
        except Exception as e:
            error_label = QLabel(f"硬件检测失败: {e}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
        
        # 性能预期说明
        performance_group = QGroupBox("⚡ 性能预期说明")
        performance_layout = QVBoxLayout(performance_group)
        
        performance_text = QLabel("""
<b>智能推荐说明：</b><br><br>
🎯 <b>系统已为您选择最适合的模型版本</b><br><br>
基于您的硬件配置分析，智能推荐系统会自动选择：<br>
• ✅ 与您的内存容量匹配的版本<br>
• ✅ 在您的设备上运行流畅的版本<br>
• ✅ 保证VisionAI-ClipsMaster功能完整性的版本<br><br>
<b>VisionAI-ClipsMaster 核心功能保障：</b><br>
• 🎬 字幕重构：智能分析原始剧本结构<br>
• 📝 剧本分析：深度理解情节发展脉络<br>
• 💭 情感分析：精准识别情感转折点<br>
• 🎯 病毒式改编：生成符合传播规律的内容
        """)
        performance_text.setWordWrap(True)
        performance_text.setStyleSheet("padding: 10px;")
        performance_layout.addWidget(performance_text)
        
        layout.addWidget(performance_group)
        
        layout.addStretch()

        # 将滚动内容设置到滚动区域
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        return main_widget
    

    
    def on_variant_selected(self, variant_info: Dict):
        """选择变体"""
        self.selected_variant = variant_info
        self.update_download_button()
    
    def update_download_button(self):
        """更新下载按钮"""
        if self.selected_variant:
            variant = self.selected_variant.get('variant')
            if variant:
                self.download_btn.setEnabled(True)
                self.download_btn.setText(f"📥 下载 {variant.name}")
                self.download_info_label.setText(f"将下载: {variant.name} ({variant.size_gb:.1f}GB)")
                self.download_info_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.download_btn.setEnabled(False)
            self.download_btn.setText("📥 开始下载")
            self.download_info_label.setText("请选择要下载的模型版本")
            self.download_info_label.setStyleSheet("color: #666; font-style: italic;")
    
    def get_selected_variant(self):
        """获取选中的变体"""
        return self.selected_variant

    def safe_accept(self):
        """安全的接受处理"""
        try:
            print("🔍 [DEBUG] 用户点击下载按钮")
            self.accept()
        except Exception as e:
            print(f"❌ [ERROR] 接受对话框时出错: {e}")
            # 即使出错也要关闭对话框
            try:
                self.close()
            except:
                pass

    def safe_reject(self):
        """安全的拒绝处理"""
        try:
            print("🔍 [DEBUG] 用户点击取消按钮")
            self.reject()
        except Exception as e:
            print(f"❌ [ERROR] 拒绝对话框时出错: {e}")
            # 即使出错也要关闭对话框
            try:
                self.close()
            except:
                pass

    def closeEvent(self, event):
        """重写关闭事件，确保安全关闭"""
        try:
            print("🔍 [DEBUG] 对话框关闭事件触发")
            # 清理资源
            if hasattr(self, 'recommendation_tab'):
                self.recommendation_tab = None
            if hasattr(self, 'custom_tab'):
                self.custom_tab = None

            # 调用父类的关闭事件
            super().closeEvent(event)
            print("🔍 [DEBUG] 对话框关闭完成")
        except Exception as e:
            print(f"❌ [ERROR] 关闭对话框时出错: {e}")
            # 强制接受关闭事件
            event.accept()
