#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 模型选择对话框
提供用户友好的模型版本选择界面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QRadioButton, QButtonGroup,
    QProgressBar, QTabWidget, QWidget, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ModelVariantCard(QFrame):
    """模型变体卡片组件"""
    
    selected = pyqtSignal(dict)  # 选中信号
    
    def __init__(self, variant_info: Dict, is_recommended: bool = False):
        super().__init__()
        self.variant_info = variant_info
        self.is_recommended = is_recommended
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        
        # 设置样式
        if self.is_recommended:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    background-color: #f8fff8;
                    margin: 5px;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #fafafa;
                    margin: 5px;
                    padding: 10px;
                }
                QFrame:hover {
                    border-color: #2196F3;
                    background-color: #f0f8ff;
                }
            """)
        
        layout = QVBoxLayout(self)
        
        # 标题行
        title_layout = QHBoxLayout()
        
        # 推荐标签
        if self.is_recommended:
            recommend_label = QLabel("🏆 推荐")
            recommend_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            title_layout.addWidget(recommend_label)
        
        title_layout.addStretch()
        
        # 选择按钮
        self.select_btn = QPushButton("选择此版本")
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
            info_label = QLabel(f"""
<b>{variant.name}</b><br>
📦 大小: {variant.size_gb:.1f} GB<br>
💾 内存需求: {variant.memory_requirement_gb:.1f} GB<br>
🎯 质量保持: {variant.quality_retention:.1%}<br>
⚡ 推理速度: {variant.inference_speed_factor:.1%}<br>
🖥️ CPU兼容: {'是' if variant.cpu_compatible else '否'}
            """.strip())
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
        
        # 兼容性信息
        compatibility = self.variant_info.get('compatibility', {})
        if compatibility:
            compat_score = compatibility.get('compatibility_score', 0)
            is_compatible = compatibility.get('is_compatible', False)
            
            compat_text = f"🔧 兼容性: {compat_score:.1%} "
            compat_text += "✅ 兼容" if is_compatible else "⚠️ 有限兼容"
            
            compat_label = QLabel(compat_text)
            compat_label.setStyleSheet(f"color: {'green' if is_compatible else 'orange'};")
            layout.addWidget(compat_label)
        
        # 描述信息
        description = self.variant_info.get('description', '')
        if description:
            desc_label = QLabel(f"💡 {description}")
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(desc_label)
    
    def on_select(self):
        """选择此变体"""
        self.selected.emit(self.variant_info)

class ModelSelectionDialog(QDialog):
    """模型选择对话框"""
    
    def __init__(self, model_name: str, recommendation: Dict, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.recommendation = recommendation
        self.selected_variant = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"选择 {self.model_name} 模型版本")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"🤖 {self.model_name} 模型版本选择")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 智能推荐标签页
        recommend_tab = self.create_recommendation_tab()
        tab_widget.addTab(recommend_tab, "🏆 智能推荐")
        
        # 所有选项标签页
        options_tab = self.create_options_tab()
        tab_widget.addTab(options_tab, "📋 所有选项")
        
        # 硬件信息标签页
        hardware_tab = self.create_hardware_tab()
        tab_widget.addTab(hardware_tab, "🔧 硬件信息")
        
        layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("📥 开始下载")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.download_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
    
    def create_recommendation_tab(self) -> QWidget:
        """创建推荐标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 推荐说明
        intro_label = QLabel("""
        <h3>🎯 基于您的硬件配置，我们为您推荐以下版本：</h3>
        <p>我们的智能算法分析了您的硬件配置、性能需求和使用场景，为您选择了最适合的模型版本。</p>
        """)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # 推荐版本卡片
        if self.recommendation:
            recommended_card = ModelVariantCard({
                'variant': self.recommendation.variant,
                'compatibility': self.recommendation.compatibility_assessment,
                'description': "智能推荐版本，最适合您的硬件配置"
            }, is_recommended=True)
            
            recommended_card.selected.connect(self.on_variant_selected)
            layout.addWidget(recommended_card)
            
            # 推荐理由
            reasoning_group = QGroupBox("💡 推荐理由")
            reasoning_layout = QVBoxLayout(reasoning_group)
            
            reasoning_text = QTextEdit()
            reasoning_text.setPlainText("\n".join(self.recommendation.reasoning))
            reasoning_text.setMaximumHeight(120)
            reasoning_text.setReadOnly(True)
            reasoning_layout.addWidget(reasoning_text)
            
            layout.addWidget(reasoning_group)
            
            # 部署说明
            if self.recommendation.deployment_notes:
                deploy_group = QGroupBox("🚀 部署说明")
                deploy_layout = QVBoxLayout(deploy_group)
                
                deploy_text = QTextEdit()
                deploy_text.setPlainText("\n".join(self.recommendation.deployment_notes))
                deploy_text.setMaximumHeight(100)
                deploy_text.setReadOnly(True)
                deploy_layout.addWidget(deploy_text)
                
                layout.addWidget(deploy_group)
        
        layout.addStretch()
        return widget
    
    def create_options_tab(self) -> QWidget:
        """创建所有选项标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        intro_label = QLabel("""
        <h3>📋 所有可用版本</h3>
        <p>您可以根据自己的需求选择任何版本。每个版本都有不同的性能特点和硬件要求。</p>
        """)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 添加所有选项
        if self.recommendation and self.recommendation.alternative_options:
            for option in self.recommendation.alternative_options:
                if 'variant' in option:
                    card = ModelVariantCard(option)
                    card.selected.connect(self.on_variant_selected)
                    scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return widget
    
    def create_hardware_tab(self) -> QWidget:
        """创建硬件信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 硬件信息
        hardware_group = QGroupBox("🔧 检测到的硬件配置")
        hardware_layout = QVBoxLayout(hardware_group)
        
        try:
            from ..core.quantization_analysis import HardwareDetector
            hardware = HardwareDetector.detect_hardware()
            
            hardware_text = f"""
GPU内存: {hardware.gpu_memory_gb:.1f} GB
系统内存: {hardware.system_ram_gb:.1f} GB  
可用存储: {hardware.storage_available_gb:.1f} GB
CPU核心: {hardware.cpu_cores}
GPU支持: {'是' if hardware.has_gpu else '否'}
            """.strip()
            
            if hardware.gpu_compute_capability:
                hardware_text += f"\nGPU计算能力: {hardware.gpu_compute_capability}"
            
        except Exception as e:
            hardware_text = f"硬件检测失败: {e}"
        
        hardware_label = QLabel(hardware_text)
        hardware_label.setStyleSheet("font-family: monospace; padding: 10px;")
        hardware_layout.addWidget(hardware_label)
        
        layout.addWidget(hardware_group)
        
        # 性能预期说明
        performance_group = QGroupBox("⚡ 性能预期说明")
        performance_layout = QVBoxLayout(performance_group)
        
        performance_text = QLabel("""
<b>版本对比说明：</b><br><br>
🏆 <b>完整版 (FP16)</b>: 最高质量和速度，需要16GB+ GPU内存<br>
⚖️ <b>中等量化 (Q8)</b>: 平衡质量和大小，需要8-10GB内存<br>
💾 <b>轻量版 (Q5)</b>: 较小体积，质量略降，需要6-8GB内存<br>
🚀 <b>超轻版 (Q4)</b>: 最小体积，适合4GB设备，质量有所降低<br><br>
<b>VisionAI-ClipsMaster 特定影响：</b><br>
• 字幕重构准确率: FP16(95%) > Q8(94%) > Q5(92%) > Q4(89%)<br>
• 剧本分析质量: FP16(92%) > Q8(91%) > Q5(89%) > Q4(86%)<br>
• 情感分析精度: FP16(88%) > Q8(87%) > Q5(85%) > Q4(82%)
        """)
        performance_text.setWordWrap(True)
        performance_layout.addWidget(performance_text)
        
        layout.addWidget(performance_group)
        
        layout.addStretch()
        return widget
    
    def on_variant_selected(self, variant_info: Dict):
        """选择变体"""
        self.selected_variant = variant_info
        self.download_btn.setEnabled(True)
        
        # 更新按钮文本
        variant = variant_info.get('variant')
        if variant:
            self.download_btn.setText(f"📥 下载 {variant.name} ({variant.size_gb:.1f}GB)")
    
    def get_selected_variant(self):
        """获取选中的变体"""
        return self.selected_variant
