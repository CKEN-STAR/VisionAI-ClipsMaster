#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态模型推荐组件 - VisionAI-ClipsMaster
根据设备配置动态更新模型推荐信息，包括文件大小、内存需求、质量保持率等
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QProgressBar, QFrame, QGridLayout, QSizePolicy,
    QTextEdit, QScrollArea, QSpacerItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from PyQt6.QtGui import QFont, QPalette, QColor

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

@dataclass
class ModelVariantInfo:
    """模型变体信息"""
    name: str
    quantization: str
    file_size_gb: float
    memory_requirement_gb: float
    quality_retention: float
    inference_speed_relative: float
    download_time_estimate_min: int
    disk_space_gb: float
    is_recommended: bool = False
    recommendation_reason: str = ""

class ModelRecommendationWorker(QObject):
    """模型推荐工作线程"""
    
    recommendation_completed = pyqtSignal(list)  # 推荐完成信号
    recommendation_failed = pyqtSignal(str)      # 推荐失败信号
    
    def __init__(self, model_name: str, hardware_info: Dict = None):
        super().__init__()
        self.model_name = model_name
        self.hardware_info = hardware_info or {}
        self.is_cancelled = False
    
    def get_recommendations(self):
        """获取模型推荐"""
        try:
            logger.info(f"🚀 开始获取 {self.model_name} 的推荐")

            if self.is_cancelled:
                logger.info("⚠️ 推荐已取消")
                return

            # 导入智能选择器
            logger.info("📦 导入智能选择器...")
            from src.core.intelligent_model_selector import IntelligentModelSelector

            logger.info("🔧 创建智能选择器实例...")
            selector = IntelligentModelSelector()

            # 强制刷新硬件配置
            logger.info("🔄 强制刷新硬件配置...")
            selector.force_refresh_hardware()

            if self.is_cancelled:
                logger.info("⚠️ 推荐已取消")
                return

            # 获取所有可用变体
            logger.info("📋 获取所有可用变体...")
            variants = self._get_all_variants()
            logger.info(f"✅ 找到 {len(variants)} 个变体")

            # 获取推荐
            logger.info("🎯 获取智能推荐...")
            recommendation = selector.recommend_model_version(self.model_name)

            if self.is_cancelled:
                logger.info("⚠️ 推荐已取消")
                return

            # 标记推荐的变体
            if recommendation and recommendation.variant:
                recommended_name = recommendation.variant.name
                logger.info(f"✅ 推荐变体: {recommended_name}")
                for variant in variants:
                    if variant.name == recommended_name:
                        variant.is_recommended = True
                        variant.recommendation_reason = self._get_recommendation_reason(
                            recommendation, self.hardware_info
                        )
                        logger.info(f"✅ 标记推荐变体成功")
                        break
            else:
                logger.warning("⚠️ 未获取到推荐结果")

            logger.info("📤 发送推荐完成信号...")
            self.recommendation_completed.emit(variants)
            logger.info("✅ 推荐获取完成")

        except Exception as e:
            logger.error(f"❌ 获取模型推荐失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            self.recommendation_failed.emit(str(e))
    
    def _get_all_variants(self) -> List[ModelVariantInfo]:
        """获取所有模型变体信息 - 从QuantizationAnalyzer动态获取"""
        try:
            # 🔧 修复：从QuantizationAnalyzer动态获取变体信息,而不是硬编码
            from src.core.quantization_analysis import QuantizationAnalyzer

            analyzer = QuantizationAnalyzer()

            # 获取所有变体
            all_variants = analyzer.get_all_variants()

            # 过滤出当前模型的变体
            model_variants = []
            for variant_name, variant_info in all_variants.items():
                # 检查变体是否属于当前模型
                if self._is_variant_for_model(variant_name, self.model_name):
                    model_variants.append(ModelVariantInfo(
                        name=variant_info.name,
                        quantization=variant_info.quantization.value,
                        file_size_gb=variant_info.size_gb,
                        memory_requirement_gb=variant_info.memory_requirement_gb,
                        quality_retention=variant_info.quality_retention,
                        inference_speed_relative=variant_info.inference_speed_relative,
                        download_time_estimate_min=int(variant_info.size_gb * 2.5),  # 估算下载时间
                        disk_space_gb=variant_info.size_gb * 1.05  # 预留5%空间
                    ))

            if not model_variants:
                logger.warning(f"未找到模型 {self.model_name} 的变体,使用通用变体")
                return self._get_generic_variants()

            return model_variants

        except Exception as e:
            logger.error(f"动态获取变体失败: {e},回退到通用变体")
            return self._get_generic_variants()

    def _is_variant_for_model(self, variant_name: str, model_name: str) -> bool:
        """检查变体是否属于指定模型"""
        variant_lower = variant_name.lower().replace("-", "").replace("_", "")
        model_lower = model_name.lower().replace("-", "").replace("_", "")

        # 检查Qwen系列
        if "qwen" in model_lower and "qwen" in variant_lower:
            return True
        # 检查Mistral系列
        elif "mistral" in model_lower and "mistral" in variant_lower:
            return True
        # 精确匹配
        elif model_lower in variant_lower:
            return True

        return False

    def _get_generic_variants(self) -> List[ModelVariantInfo]:
        """获取通用模型变体"""
        return [
            ModelVariantInfo(
                name=f"{self.model_name}-FP16",
                quantization="FP16",
                file_size_gb=13.8,
                memory_requirement_gb=15.8,
                quality_retention=1.0,
                inference_speed_relative=1.0,
                download_time_estimate_min=35,
                disk_space_gb=14.2
            ),
            ModelVariantInfo(
                name=f"{self.model_name}-Q4",
                quantization="Q4_K_M",
                file_size_gb=4.1,
                memory_requirement_gb=5.1,
                quality_retention=0.93,
                inference_speed_relative=1.8,
                download_time_estimate_min=10,
                disk_space_gb=4.3
            )
        ]
    
    def _get_recommendation_reason(self, recommendation, hardware_info: Dict) -> str:
        """获取推荐理由"""
        try:
            ram_gb = hardware_info.get('system_ram_gb', 0)
            has_gpu = hardware_info.get('has_gpu', False)
            performance_level = hardware_info.get('performance_level', 'unknown')
            
            reasons = []
            
            if ram_gb <= 8:
                reasons.append("适合低内存设备")
            elif ram_gb <= 16:
                reasons.append("适合中等内存设备")
            else:
                reasons.append("适合高内存设备")
            
            if not has_gpu:
                reasons.append("CPU优化")
            else:
                reasons.append("GPU加速支持")
            
            if performance_level == "Low":
                reasons.append("轻量化优先")
            elif performance_level == "Medium":
                reasons.append("平衡性能与质量")
            else:
                reasons.append("高质量优先")
            
            return "、".join(reasons)
            
        except Exception as e:
            logger.error(f"生成推荐理由失败: {e}")
            return "智能推荐"
    
    def cancel(self):
        """取消推荐"""
        self.is_cancelled = True

class DynamicModelRecommendationWidget(QWidget):
    """动态模型推荐组件"""
    
    recommendation_changed = pyqtSignal(object)  # 推荐变化信号
    variant_selected = pyqtSignal(object)  # 变体选择信号
    
    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.current_variants = []
        self.current_hardware_info = {}
        self.recommendation_worker = None
        self.recommendation_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"🎯 {self.model_name} 智能推荐")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 推荐表格
        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(7)
        self.variants_table.setHorizontalHeaderLabels([
            "变体名称", "量化等级", "文件大小", "内存需求", 
            "质量保持", "推理速度", "推荐状态"
        ])
        
        # 设置表格属性
        header = self.variants_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.variants_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.variants_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.variants_table)
        
        # 详细信息区域
        self.detail_group = QGroupBox("详细信息")
        self.detail_layout = QVBoxLayout(self.detail_group)
        self.detail_text = QTextEdit()
        self.detail_text.setMaximumHeight(100)
        self.detail_text.setReadOnly(True)
        self.detail_layout.addWidget(self.detail_text)
        layout.addWidget(self.detail_group)
        
        # 状态标签
        self.status_label = QLabel("🔍 正在获取推荐...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # 连接信号
        self.variants_table.itemSelectionChanged.connect(self.on_variant_selected)
    
    def update_hardware_info(self, hardware_info: Dict):
        """更新硬件信息"""
        self.current_hardware_info = hardware_info
        self.refresh_recommendations()
    
    def refresh_recommendations(self):
        """刷新推荐"""
        try:
            self.status_label.setText("🔄 正在更新推荐...")

            # 🔧 修复：清理旧的线程和worker,避免内存泄漏和崩溃
            if self.recommendation_worker:
                logger.info("🧹 取消旧的推荐任务...")
                self.recommendation_worker.cancel()
                self.recommendation_worker = None

            if self.recommendation_thread and self.recommendation_thread.isRunning():
                logger.info("🧹 停止旧的推荐线程...")
                self.recommendation_thread.quit()
                self.recommendation_thread.wait(1000)  # 等待最多1秒
                if self.recommendation_thread.isRunning():
                    logger.warning("⚠️ 线程未能正常停止,强制终止")
                    self.recommendation_thread.terminate()
                    self.recommendation_thread.wait()
                self.recommendation_thread.deleteLater()
                self.recommendation_thread = None

            # 创建推荐工作线程
            self.recommendation_thread = QThread()
            self.recommendation_worker = ModelRecommendationWorker(
                self.model_name, self.current_hardware_info
            )
            self.recommendation_worker.moveToThread(self.recommendation_thread)

            # 连接信号
            self.recommendation_worker.recommendation_completed.connect(self.update_recommendations)
            self.recommendation_worker.recommendation_failed.connect(self.on_recommendation_failed)

            # 🔧 修复：线程完成后自动清理
            self.recommendation_thread.finished.connect(self.recommendation_thread.deleteLater)

            # 启动线程
            self.recommendation_thread.started.connect(self.recommendation_worker.get_recommendations)
            self.recommendation_thread.start()

        except Exception as e:
            logger.error(f"刷新推荐失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            self.status_label.setText(f"❌ 刷新失败: {e}")
    
    def update_recommendations(self, variants: List[ModelVariantInfo]):
        """更新推荐显示"""
        try:
            self.current_variants = variants
            
            # 更新表格
            self.variants_table.setRowCount(len(variants))
            
            for row, variant in enumerate(variants):
                # 变体名称
                name_item = QTableWidgetItem(variant.name)
                if variant.is_recommended:
                    name_item.setBackground(QColor(220, 255, 220))
                self.variants_table.setItem(row, 0, name_item)
                
                # 量化等级
                quant_item = QTableWidgetItem(variant.quantization)
                self.variants_table.setItem(row, 1, quant_item)
                
                # 文件大小
                size_item = QTableWidgetItem(f"{variant.file_size_gb:.1f} GB")
                self.variants_table.setItem(row, 2, size_item)
                
                # 内存需求
                memory_item = QTableWidgetItem(f"{variant.memory_requirement_gb:.1f} GB")
                self.variants_table.setItem(row, 3, memory_item)
                
                # 质量保持
                quality_item = QTableWidgetItem(f"{variant.quality_retention:.1%}")
                self.variants_table.setItem(row, 4, quality_item)
                
                # 推理速度
                speed_item = QTableWidgetItem(f"{variant.inference_speed_relative:.1f}x")
                self.variants_table.setItem(row, 5, speed_item)
                
                # 推荐状态
                status_item = QTableWidgetItem("🌟 推荐" if variant.is_recommended else "可选")
                if variant.is_recommended:
                    status_item.setBackground(QColor(255, 215, 0, 100))
                self.variants_table.setItem(row, 6, status_item)
            
            # 更新状态
            recommended_count = sum(1 for v in variants if v.is_recommended)
            self.status_label.setText(f"✅ 已更新 {len(variants)} 个变体，{recommended_count} 个推荐")
            
            # 发送推荐变化信号
            self.recommendation_changed.emit(variants)
            
        except Exception as e:
            logger.error(f"更新推荐显示失败: {e}")
            self.status_label.setText(f"❌ 更新失败: {e}")
    
    def on_variant_selected(self):
        """变体选择处理"""
        try:
            current_row = self.variants_table.currentRow()
            if 0 <= current_row < len(self.current_variants):
                variant = self.current_variants[current_row]
                
                # 更新详细信息
                detail_text = f"""
选中变体: {variant.name}
量化等级: {variant.quantization}
文件大小: {variant.file_size_gb:.1f} GB
内存需求: {variant.memory_requirement_gb:.1f} GB
质量保持: {variant.quality_retention:.1%}
推理速度: {variant.inference_speed_relative:.1f}x (相对于FP16)
预估下载时间: {variant.download_time_estimate_min} 分钟
磁盘占用: {variant.disk_space_gb:.1f} GB
"""
                
                if variant.is_recommended:
                    detail_text += f"推荐理由: {variant.recommendation_reason}"
                
                self.detail_text.setPlainText(detail_text.strip())
                
                # 发送选择信号
                self.variant_selected.emit(variant)
                
        except Exception as e:
            logger.error(f"处理变体选择失败: {e}")
    
    def on_recommendation_failed(self, error_msg: str):
        """推荐失败处理"""
        logger.error(f"获取推荐失败: {error_msg}")
        self.status_label.setText(f"❌ 获取推荐失败: {error_msg}")
    
    def get_recommended_variant(self) -> Optional[ModelVariantInfo]:
        """获取推荐的变体"""
        for variant in self.current_variants:
            if variant.is_recommended:
                return variant
        return None
    
    def get_selected_variant(self) -> Optional[ModelVariantInfo]:
        """获取当前选中的变体"""
        current_row = self.variants_table.currentRow()
        if 0 <= current_row < len(self.current_variants):
            return self.current_variants[current_row]
        return None

    def stop_recommendation(self):
        """停止推荐线程"""
        try:
            if self.recommendation_worker:
                self.recommendation_worker.is_cancelled = True

            if hasattr(self, 'recommendation_thread') and self.recommendation_thread and self.recommendation_thread.isRunning():
                self.recommendation_thread.quit()
                if not self.recommendation_thread.wait(3000):  # 等待3秒
                    logger.warning("推荐线程未能在3秒内正常退出，强制终止")
                    self.recommendation_thread.terminate()
                    self.recommendation_thread.wait(1000)  # 再等待1秒

            # 清理引用
            self.recommendation_worker = None
            if hasattr(self, 'recommendation_thread'):
                self.recommendation_thread = None

            logger.info("推荐线程已停止")

        except Exception as e:
            logger.error(f"停止推荐线程失败: {e}")

    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.stop_recommendation()
        except:
            pass  # 析构函数中忽略异常
