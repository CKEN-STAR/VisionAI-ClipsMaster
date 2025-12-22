#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
超快速智能推荐下载器对话框 - VisionAI-ClipsMaster
根本性重构版本，从根源上解决性能和UI问题

核心特性:
1. 无线程设计 - 所有操作在主线程，避免线程安全问题
2. 硬件快照缓存 - 类级别缓存，5分钟TTL，消除停顿
3. 预加载推荐 - 初始化时立即使用缓存获取推荐
4. 动态获取 - 所有模型信息从配置文件和智能推荐系统获取
5. 简洁UI - 卡片式设计，信息层级清晰
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFrame, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGridLayout, QScrollArea,
    QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


@dataclass
class VariantInfo:
    """变体信息"""
    name: str
    quantization: str
    size_gb: float
    memory_gb: float
    quality: float
    speed: float
    is_recommended: bool = False
    reason: str = ""


class UltraFastSmartDownloaderDialog(QDialog):
    """超快速智能推荐下载器对话框
    
    设计原则:
    1. 无线程 - 所有操作在主线程中完成
    2. 使用缓存 - 硬件信息缓存5分钟
    3. 预加载 - 初始化时立即加载推荐
    4. 动态获取 - 所有信息从配置文件获取
    """
    
    download_requested = pyqtSignal(str, object)  # (model_name, variant_info)

    # 类级别硬件缓存
    _hardware_cache = None
    _cache_timestamp = 0
    _cache_ttl = 1800  # 30分钟（延长缓存时间以提升性能）
    _hardware_fingerprint = None  # 硬件指纹,用于检测设备变化
    
    def __init__(self, model_name: str, parent=None):
        """初始化对话框
        
        Args:
            model_name: 模型名称（通用名称，如"qwen"或"mistral"）
            parent: 父窗口
        """
        super().__init__(parent)
        self.model_name = model_name
        self.recommended_variant = None
        self.all_variants = []
        self.hardware_snapshot = None
        
        # 设置窗口属性
        self.setWindowTitle(f"🎯 智能模型推荐 - {model_name}")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self.setModal(True)
        
        # 初始化UI
        self.init_ui()
        
        # 立即加载推荐（使用缓存，无停顿）
        self.load_recommendations()
    
    @classmethod
    def get_cached_hardware(cls):
        """获取缓存的硬件快照（支持设备变化检测）"""
        current_time = time.time()

        # 🔧 生成当前硬件指纹（用于检测设备变化）
        try:
            import psutil
            import platform
            current_fingerprint = f"{psutil.cpu_count()}_{int(psutil.virtual_memory().total/1024**3)}_{platform.machine()}"
        except:
            current_fingerprint = "unknown"

        # 检查缓存是否有效
        cache_expired = (current_time - cls._cache_timestamp) > cls._cache_ttl
        hardware_changed = (cls._hardware_fingerprint != current_fingerprint)

        if cls._hardware_cache is None or cache_expired or hardware_changed:
            if hardware_changed:
                logger.info("🔄 检测到硬件变化，重新检测...")
            else:
                logger.info("🔄 硬件缓存过期或不存在，重新检测...")

            try:
                from src.core.hardware_detector import HardwareDetector
                detector = HardwareDetector()
                cls._hardware_cache = detector.detect_hardware()
                cls._cache_timestamp = current_time
                cls._hardware_fingerprint = current_fingerprint
                logger.info("✅ 硬件检测完成并缓存")
            except Exception as e:
                logger.error(f"❌ 硬件检测失败: {e}")
                # 返回默认值
                from src.core.hardware_detector import HardwareSnapshot
                cls._hardware_cache = HardwareSnapshot(
                    system_ram_gb=8.0,
                    available_ram_gb=4.0,
                    cpu_cores=4,
                    cpu_freq_mhz=2400,
                    has_gpu=False,
                    gpu_name="",
                    gpu_memory_gb=0.0,
                    performance_level="MEDIUM",
                    recommended_quantization="INT4",
                    detection_timestamp=current_time
                )
                cls._hardware_fingerprint = current_fingerprint
        else:
            logger.info("✅ 使用缓存的硬件信息")

        return cls._hardware_cache
    
    @classmethod
    def clear_cache(cls):
        """清除硬件缓存"""
        cls._hardware_cache = None
        cls._cache_timestamp = 0
        cls._hardware_fingerprint = None
        logger.info("🧹 硬件缓存已清除")
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题区域
        title_label = QLabel(f"🎯 智能模型推荐")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #333333;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2196f3;
                border-bottom: 3px solid #2196f3;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:hover {
                background-color: #e8e8e8;
                color: #1976d2;
            }
        """)
        
        # 智能推荐标签页
        self.recommendation_tab = self.create_recommendation_tab()
        self.tab_widget.addTab(self.recommendation_tab, "🌟 智能推荐")
        
        # 硬件配置标签页
        self.hardware_tab = self.create_hardware_tab()
        self.tab_widget.addTab(self.hardware_tab, "💻 硬件配置")
        
        main_layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新检测")
        refresh_btn.setToolTip("重新检测硬件并刷新推荐")
        refresh_btn.clicked.connect(self.refresh_all)
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 18px;
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #1976d2;
            }
        """)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        # 下载按钮
        self.download_btn = QPushButton("📥 下载推荐版本")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_recommended)
        self.download_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.download_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_recommendation_tab(self) -> QWidget:
        """创建智能推荐标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 推荐卡片
        self.recommendation_card = QGroupBox("🌟 推荐变体")
        self.recommendation_card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f1f8f4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        card_layout = QVBoxLayout(self.recommendation_card)
        
        self.recommendation_info = QLabel("⏳ 正在加载推荐...")
        self.recommendation_info.setWordWrap(True)
        self.recommendation_info.setStyleSheet("padding: 10px; font-size: 14px;")
        card_layout.addWidget(self.recommendation_info)
        
        layout.addWidget(self.recommendation_card)
        
        # 其他可用变体
        variants_group = QGroupBox("📋 其他可用变体（仅供参考）")
        variants_layout = QVBoxLayout(variants_group)

        # 添加说明
        info_label = QLabel("💡 提示：为确保最佳性能，只能下载推荐的模型变体")
        info_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px; background-color: #fff3cd; border-radius: 3px;")
        info_label.setWordWrap(True)
        variants_layout.addWidget(info_label)

        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(5)
        self.variants_table.setHorizontalHeaderLabels([
            "变体名称", "内存需求", "文件大小", "质量保持", "推理速度"
        ])
        self.variants_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 🔧 禁用选择和编辑,只允许查看
        self.variants_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.variants_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.variants_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.variants_table.setAlternatingRowColors(True)
        self.variants_table.setMaximumHeight(200)

        # 🔧 设置表格字体大小
        table_font = QFont("Microsoft YaHei", 12)
        self.variants_table.setFont(table_font)

        # 🔧 设置表头字体
        header_font = QFont("Microsoft YaHei", 12, QFont.Weight.Bold)
        self.variants_table.horizontalHeader().setFont(header_font)

        # 🔧 设置行高
        self.variants_table.verticalHeader().setDefaultSectionSize(35)

        variants_layout.addWidget(self.variants_table)
        layout.addWidget(variants_group)
        
        # 状态标签
        self.status_label = QLabel("✅ 准备就绪")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px; font-size: 13px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return tab
    
    def create_hardware_tab(self) -> QWidget:
        """创建硬件配置标签页"""
        tab = QWidget()
        self.hardware_tab_layout = QVBoxLayout(tab)
        self.hardware_tab_layout.setSpacing(10)

        # 硬件信息网格
        self.hardware_grid = QGridLayout()
        self.hardware_grid.setSpacing(10)

        # 占位标签（保存引用以便后续删除）
        self.hardware_loading_label = QLabel("⏳ 正在加载硬件信息...")
        self.hardware_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hardware_loading_label.setStyleSheet("color: #666; font-style: italic; padding: 20px; font-size: 14px;")
        self.hardware_tab_layout.addWidget(self.hardware_loading_label)

        self.hardware_tab_layout.addLayout(self.hardware_grid)
        self.hardware_tab_layout.addStretch()

        return tab

    def load_recommendations(self):
        """加载推荐（无线程，使用缓存）"""
        try:
            logger.info(f"🚀 开始加载 {self.model_name} 的推荐")

            # 1. 获取硬件快照（使用缓存）
            self.hardware_snapshot = self.get_cached_hardware()
            logger.info(f"✅ 硬件快照获取成功: {self.hardware_snapshot.performance_level}")

            # 2. 更新硬件信息显示
            self.update_hardware_display()

            # 3. 获取所有变体
            self.all_variants = self.get_all_variants()
            logger.info(f"✅ 找到 {len(self.all_variants)} 个变体")

            # 4. 获取推荐
            from src.core.intelligent_model_selector import IntelligentModelSelector
            selector = IntelligentModelSelector()
            recommendation = selector.recommend_model_version(self.model_name)

            if recommendation and recommendation.variant:
                logger.info(f"✅ 推荐变体: {recommendation.variant.name}")

                # 标记推荐的变体
                recommended_name = recommendation.variant.name
                for variant in self.all_variants:
                    if variant.name == recommended_name:
                        variant.is_recommended = True
                        variant.reason = self.get_recommendation_reason(recommendation)
                        self.recommended_variant = variant
                        break

                # 更新UI
                self.update_recommendation_display()
                self.update_variants_table()

                # 启用下载按钮
                self.download_btn.setEnabled(True)
                self.status_label.setText(f"✅ 已加载 {len(self.all_variants)} 个变体，推荐 1 个")
            else:
                logger.warning("⚠️ 未获取到推荐结果")
                self.status_label.setText("⚠️ 未找到推荐，请检查硬件配置")

        except Exception as e:
            logger.error(f"❌ 加载推荐失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            self.status_label.setText(f"❌ 加载失败: {e}")

    def get_all_variants(self) -> List[VariantInfo]:
        """获取所有模型变体（动态获取）"""
        try:
            from src.core.quantization_analysis import QuantizationAnalyzer

            analyzer = QuantizationAnalyzer()

            # 获取所有模型变体
            variants = []
            for model_key, variant_list in analyzer.model_variants.items():
                # 检查是否属于当前模型
                if self.is_variant_for_model(model_key):
                    for variant_data in variant_list:
                        variants.append(VariantInfo(
                            name=variant_data.name,
                            quantization=variant_data.quantization.value,
                            size_gb=variant_data.size_gb,
                            memory_gb=variant_data.memory_requirement_gb,
                            quality=variant_data.quality_retention,
                            speed=variant_data.inference_speed_factor
                        ))

            return variants

        except Exception as e:
            logger.error(f"获取变体失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return []

    def is_variant_for_model(self, variant_name: str) -> bool:
        """检查变体是否属于当前模型"""
        variant_lower = variant_name.lower().replace("-", "").replace("_", "")
        model_lower = self.model_name.lower().replace("-", "").replace("_", "")

        # Qwen系列
        if "qwen" in model_lower and "qwen" in variant_lower:
            return True
        # Mistral系列
        elif "mistral" in model_lower and "mistral" in variant_lower:
            return True
        # 精确匹配
        elif model_lower in variant_lower:
            return True

        return False

    def get_recommendation_reason(self, recommendation) -> str:
        """获取推荐理由"""
        try:
            reasons = []

            # 基于性能等级
            perf_level = getattr(self.hardware_snapshot, 'performance_level', 'UNKNOWN')
            if hasattr(perf_level, 'value'):
                perf_level = perf_level.value
            perf_level_str = str(perf_level).upper()

            if "ULTRA" in perf_level_str:
                reasons.append("旗舰级设备，可运行大规模模型")
            elif "HIGH" in perf_level_str:
                reasons.append("高性能设备，平衡质量与速度")
            elif "MEDIUM" in perf_level_str:
                reasons.append("中等性能设备，优化内存占用")
            elif "LOW" in perf_level_str:
                reasons.append("入门级设备，轻量化优先")
            else:
                reasons.append("基础设备，最小内存需求")

            # 基于内存
            ram_gb = getattr(self.hardware_snapshot, 'total_memory_gb',
                           getattr(self.hardware_snapshot, 'system_ram_gb', 0))
            if ram_gb <= 8:
                reasons.append("适配低内存环境")
            elif ram_gb <= 16:
                reasons.append("适配中等内存环境")
            else:
                reasons.append("充分利用大内存优势")

            # 基于GPU
            has_gpu = getattr(self.hardware_snapshot, 'has_gpu', False) or \
                     getattr(self.hardware_snapshot, 'gpu_count', 0) > 0
            if has_gpu:
                gpu_name = getattr(self.hardware_snapshot, 'gpu_name', '')
                gpu_names = getattr(self.hardware_snapshot, 'gpu_names', [])
                display_name = gpu_name if gpu_name else (gpu_names[0] if gpu_names else "GPU")
                reasons.append(f"GPU加速支持 ({display_name})")
            else:
                reasons.append("CPU优化运行")

            return "、".join(reasons)

        except Exception as e:
            logger.error(f"生成推荐理由失败: {e}")
            return "智能推荐"

    def update_recommendation_display(self):
        """更新推荐显示"""
        if not self.recommended_variant:
            self.recommendation_info.setText("⚠️ 未找到推荐变体")
            return

        v = self.recommended_variant
        info_text = f"""
<div style='font-size: 14px; line-height: 1.8;'>
    <p style='font-size: 16px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;'>
        🌟 {v.name}
    </p>
    <p style='margin: 5px 0;'><b>📊 推荐理由:</b> {v.reason}</p>
    <p style='margin: 5px 0;'><b>💾 内存需求:</b> {v.memory_gb:.1f} GB</p>
    <p style='margin: 5px 0;'><b>📦 文件大小:</b> {v.size_gb:.1f} GB</p>
    <p style='margin: 5px 0;'><b>✨ 质量保持:</b> {v.quality:.1%}</p>
    <p style='margin: 5px 0;'><b>⚡ 推理速度:</b> {v.speed:.1f}x (相对FP16)</p>
    <p style='margin: 5px 0;'><b>🎯 量化等级:</b> {v.quantization}</p>
    <p style='margin: 5px 0; color: #666;'><b>⏱️ 预估下载:</b> {int(v.size_gb * 2.5)} 分钟 (假设10MB/s)</p>
</div>
        """
        self.recommendation_info.setText(info_text.strip())

    def update_variants_table(self):
        """更新变体表格"""
        self.variants_table.setRowCount(len(self.all_variants))

        for row, variant in enumerate(self.all_variants):
            # 变体名称
            name_item = QTableWidgetItem(variant.name)
            if variant.is_recommended:
                name_item.setBackground(QColor(220, 255, 220))
                name_item.setForeground(QColor(0, 128, 0))
                font = name_item.font()
                font.setBold(True)
                name_item.setFont(font)
            self.variants_table.setItem(row, 0, name_item)

            # 内存需求
            memory_item = QTableWidgetItem(f"{variant.memory_gb:.1f} GB")
            self.variants_table.setItem(row, 1, memory_item)

            # 文件大小
            size_item = QTableWidgetItem(f"{variant.size_gb:.1f} GB")
            self.variants_table.setItem(row, 2, size_item)

            # 质量保持
            quality_item = QTableWidgetItem(f"{variant.quality:.1%}")
            self.variants_table.setItem(row, 3, quality_item)

            # 推理速度
            speed_item = QTableWidgetItem(f"{variant.speed:.1f}x")
            self.variants_table.setItem(row, 4, speed_item)

    def update_hardware_display(self):
        """更新硬件信息显示"""
        if not self.hardware_snapshot:
            return

        # 🔧 删除占位标签
        if hasattr(self, 'hardware_loading_label') and self.hardware_loading_label:
            self.hardware_loading_label.setParent(None)
            self.hardware_loading_label = None

        # 清除现有内容
        for i in reversed(range(self.hardware_grid.count())):
            widget = self.hardware_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        hw = self.hardware_snapshot
        row = 0

        # 系统信息
        os_type = getattr(hw, 'os_type', 'Unknown')
        self._add_hardware_info("🖥️ 操作系统", os_type, row)
        row += 1

        # CPU信息
        cpu_brand = getattr(hw, 'cpu_brand', '')
        if cpu_brand:
            self._add_hardware_info("💻 CPU型号", cpu_brand, row)
            row += 1

        cpu_count = getattr(hw, 'cpu_count', getattr(hw, 'cpu_cores', 0))
        self._add_hardware_info("💻 CPU核心", f"{cpu_count} 核", row)
        row += 1

        cpu_freq = getattr(hw, 'cpu_freq_mhz', 0)
        if cpu_freq > 0:
            self._add_hardware_info("🔄 CPU频率", f"{cpu_freq:.0f} MHz ({cpu_freq/1000:.2f} GHz)", row)
            row += 1

        # 内存信息
        total_mem = getattr(hw, 'total_memory_gb', getattr(hw, 'system_ram_gb', 0))
        available_mem = getattr(hw, 'available_memory_gb', getattr(hw, 'available_ram_gb', 0))

        self._add_hardware_info("🧠 系统内存", f"{total_mem:.1f} GB", row)
        row += 1

        self._add_hardware_info("💿 可用内存", f"{available_mem:.1f} GB", row)
        row += 1

        # GPU信息
        has_gpu = getattr(hw, 'has_gpu', False) or getattr(hw, 'gpu_count', 0) > 0
        gpu_name = getattr(hw, 'gpu_name', '')
        gpu_names = getattr(hw, 'gpu_names', [])

        if has_gpu and (gpu_name or gpu_names):
            display_name = gpu_name if gpu_name else (gpu_names[0] if gpu_names else "未知GPU")
            self._add_hardware_info("🎮 GPU型号", display_name, row)
            row += 1

            gpu_mem = getattr(hw, 'gpu_memory_gb', 0)
            if gpu_mem > 0:
                self._add_hardware_info("🎮 GPU显存", f"{gpu_mem:.1f} GB", row)
                row += 1
        else:
            self._add_hardware_info("🎮 GPU", "未检测到独立显卡", row)
            row += 1

        # 磁盘信息
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            self._add_hardware_info("💾 磁盘可用", f"{free_gb:.1f} GB / {total_gb:.1f} GB", row)
            row += 1
        except:
            pass

        # 性能等级
        perf_level = getattr(hw, 'performance_level', 'UNKNOWN')
        if hasattr(perf_level, 'value'):
            perf_level = perf_level.value
        self._add_hardware_info("📊 性能等级", str(perf_level), row, highlight=True)
        row += 1

        # 推荐量化
        recommended_quant = getattr(hw, 'recommended_quantization', 'INT4')
        self._add_hardware_info("🎯 推荐量化", str(recommended_quant), row, highlight=True)
        row += 1

        # 添加说明
        explanation = QLabel(
            "💡 提示: 性能等级基于CPU、内存和GPU综合评估，"
            "推荐量化等级可在保证质量的同时优化内存占用。"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("""
            color: #666;
            font-size: 14px;
            font-style: italic;
            padding: 12px;
            background-color: #f9f9f9;
            border-radius: 4px;
            margin-top: 10px;
        """)
        self.hardware_grid.addWidget(explanation, row, 0, 1, 2)

    def _add_hardware_info(self, label: str, value: str, row: int, highlight: bool = False):
        """添加硬件信息行"""
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-weight: bold; padding: 8px; font-size: 14px;")

        value_widget = QLabel(value)
        if highlight:
            value_widget.setStyleSheet("""
                color: #2196f3;
                font-weight: bold;
                padding: 8px;
                font-size: 14px;
                border-radius: 3px;
            """)
        else:
            value_widget.setStyleSheet("padding: 8px; font-size: 14px;")

        self.hardware_grid.addWidget(label_widget, row, 0)
        self.hardware_grid.addWidget(value_widget, row, 1)

    def refresh_all(self):
        """刷新所有信息"""
        try:
            logger.info("🔄 用户请求刷新")

            # 清除缓存
            self.clear_cache()

            # 重新加载
            self.status_label.setText("🔄 正在刷新...")
            self.load_recommendations()

            logger.info("✅ 刷新完成")

        except Exception as e:
            logger.error(f"❌ 刷新失败: {e}")
            self.status_label.setText(f"❌ 刷新失败: {e}")

    def download_recommended(self):
        """下载推荐的变体"""
        if not self.recommended_variant:
            QMessageBox.warning(self, "警告", "未找到推荐的变体")
            return

        # 确认下载（保留此弹窗，移除后续的基础推荐对话框）
        variant = self.recommended_variant
        msg = f"""
确认下载以下模型变体？

变体名称: {variant.name}
文件大小: {variant.size_gb:.1f} GB
内存需求: {variant.memory_gb:.1f} GB
质量保持: {variant.quality:.1%}
预估时间: {int(variant.size_gb * 2.5)} 分钟

推荐理由: {variant.reason}
        """

        reply = QMessageBox.question(
            self,
            "确认下载",
            msg.strip(),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"✅ 用户确认下载: {variant.name}")

            # 发送下载请求信号
            # 构造variant_info对象
            variant_info = type('VariantInfo', (), {
                'name': variant.name,
                'quantization': variant.quantization,
                'size_gb': variant.size_gb,
                'memory_requirement_gb': variant.memory_gb,
                'quality_retention': variant.quality,
                'inference_speed_relative': variant.speed
            })()

            self.download_requested.emit(self.model_name, variant_info)
            self.accept()
        else:
            logger.info("⚠️ 用户取消下载")

