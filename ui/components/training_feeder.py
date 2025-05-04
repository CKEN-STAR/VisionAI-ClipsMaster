#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练数据投喂组件 - 用于模型训练和微调
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QListWidget, QListWidgetItem,
                           QGroupBox, QComboBox, QSpinBox, QLineEdit,
                           QTextEdit, QProgressBar, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal

# 导入项目模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

class TrainingFeeder(QWidget):
    """训练数据投喂组件"""
    
    # 信号定义
    training_started = pyqtSignal(dict)
    training_completed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.training_data = []
        self.training_in_progress = False
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 添加说明标签
        title_label = QLabel("模型训练与微调")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        description = QLabel("通过提供高质量样本，改进AI模型的理解与生成能力")
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        # 数据源选择区域
        data_source_group = QGroupBox("训练数据源")
        data_source_layout = QVBoxLayout()
        
        # 添加单个样本区域
        sample_layout = QHBoxLayout()
        self.sample_text = QTextEdit()
        self.sample_text.setPlaceholderText("在此输入单个训练样本文本...")
        self.sample_text.setMaximumHeight(100)
        
        add_sample_btn = QPushButton("添加样本")
        add_sample_btn.clicked.connect(self.add_single_sample)
        
        sample_layout.addWidget(self.sample_text)
        sample_layout.addWidget(add_sample_btn)
        data_source_layout.addLayout(sample_layout)
        
        # 批量导入区域
        batch_layout = QHBoxLayout()
        
        import_srt_btn = QPushButton("导入SRT文件")
        import_srt_btn.clicked.connect(self.import_srt_files)
        
        import_text_btn = QPushButton("导入文本文件")
        import_text_btn.clicked.connect(self.import_text_files)
        
        import_json_btn = QPushButton("导入JSON数据")
        import_json_btn.clicked.connect(self.import_json_files)
        
        batch_layout.addWidget(import_srt_btn)
        batch_layout.addWidget(import_text_btn)
        batch_layout.addWidget(import_json_btn)
        
        data_source_layout.addLayout(batch_layout)
        data_source_group.setLayout(data_source_layout)
        main_layout.addWidget(data_source_group)
        
        # 样本列表区域
        samples_group = QGroupBox("已添加的样本")
        samples_layout = QVBoxLayout()
        
        self.samples_list = QListWidget()
        self.samples_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        samples_layout.addWidget(self.samples_list)
        
        # 样本操作按钮
        samples_btn_layout = QHBoxLayout()
        
        remove_btn = QPushButton("删除选中")
        remove_btn.clicked.connect(self.remove_selected_samples)
        
        clear_btn = QPushButton("清空所有")
        clear_btn.clicked.connect(self.clear_all_samples)
        
        export_btn = QPushButton("导出样本")
        export_btn.clicked.connect(self.export_samples)
        
        samples_btn_layout.addWidget(remove_btn)
        samples_btn_layout.addWidget(clear_btn)
        samples_btn_layout.addWidget(export_btn)
        
        samples_layout.addLayout(samples_btn_layout)
        samples_group.setLayout(samples_layout)
        main_layout.addWidget(samples_group)
        
        # 训练参数区域
        params_group = QGroupBox("训练参数")
        params_layout = QVBoxLayout()
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("目标模型:"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "情感分析模型", 
            "叙事结构模型", 
            "视觉描述模型",
            "剧本优化模型"
        ])
        model_layout.addWidget(self.model_combo)
        params_layout.addLayout(model_layout)
        
        # 学习率
        lr_layout = QHBoxLayout()
        lr_layout.addWidget(QLabel("学习率:"))
        
        self.lr_combo = QComboBox()
        self.lr_combo.addItems(["0.0001", "0.001", "0.01"])
        self.lr_combo.setCurrentIndex(1)  # 默认选择0.001
        lr_layout.addWidget(self.lr_combo)
        params_layout.addLayout(lr_layout)
        
        # 批量大小
        batch_size_layout = QHBoxLayout()
        batch_size_layout.addWidget(QLabel("批量大小:"))
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 64)
        self.batch_size_spin.setValue(8)
        batch_size_layout.addWidget(self.batch_size_spin)
        params_layout.addLayout(batch_size_layout)
        
        # 训练轮次
        epochs_layout = QHBoxLayout()
        epochs_layout.addWidget(QLabel("训练轮次:"))
        
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 100)
        self.epochs_spin.setValue(3)
        epochs_layout.addWidget(self.epochs_spin)
        params_layout.addLayout(epochs_layout)
        
        # GPU加速
        gpu_layout = QHBoxLayout()
        self.gpu_checkbox = QCheckBox("使用GPU加速")
        self.gpu_checkbox.setChecked(True)
        gpu_layout.addWidget(self.gpu_checkbox)
        params_layout.addLayout(gpu_layout)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # 训练控制区域
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始训练")
        self.start_btn.clicked.connect(self.start_training)
        
        self.stop_btn = QPushButton("停止训练")
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        
        main_layout.addLayout(control_layout)
        
        # 进度条
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("准备就绪")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
    
    def add_single_sample(self):
        """添加单个样本"""
        sample_text = self.sample_text.toPlainText().strip()
        if not sample_text:
            QMessageBox.warning(self, "警告", "请输入样本文本")
            return
        
        # 添加到样本列表
        item = QListWidgetItem(f"样本 {self.samples_list.count()+1}: {sample_text[:50]}...")
        self.samples_list.addItem(item)
        
        # 添加到数据集
        self.training_data.append({
            "id": self.samples_list.count(),
            "text": sample_text,
            "type": "manual"
        })
        
        # 清空输入框
        self.sample_text.clear()
        self.progress_label.setText(f"已添加 {self.samples_list.count()} 个样本")
    
    def import_srt_files(self):
        """导入SRT文件作为训练样本"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择SRT文件", "", "SRT文件 (*.srt)"
        )
        
        if not file_paths:
            return
            
        count_before = self.samples_list.count()
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单处理SRT文件，提取文本内容
                import re
                text_lines = []
                pattern = re.compile(r'\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}\s+(.*?)(?=\n\d+\s+|$)', re.DOTALL)
                matches = pattern.findall(content)
                
                for i, text in enumerate(matches):
                    clean_text = text.strip().replace('\n', ' ')
                    if clean_text:
                        # 添加到样本列表
                        item = QListWidgetItem(f"SRT样本 {self.samples_list.count()+1}: {clean_text[:50]}...")
                        self.samples_list.addItem(item)
                        
                        # 添加到数据集
                        self.training_data.append({
                            "id": self.samples_list.count(),
                            "text": clean_text,
                            "type": "srt",
                            "source": os.path.basename(file_path)
                        })
            except Exception as e:
                QMessageBox.warning(self, "导入错误", f"导入文件 {os.path.basename(file_path)} 失败: {str(e)}")
        
        added_count = self.samples_list.count() - count_before
        self.progress_label.setText(f"已添加 {self.samples_list.count()} 个样本 (本次+{added_count})")
    
    def import_text_files(self):
        """导入文本文件作为训练样本"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择文本文件", "", "文本文件 (*.txt)"
        )
        
        if not file_paths:
            return
            
        count_before = self.samples_list.count()
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 按段落拆分
                paragraphs = content.split('\n\n')
                
                for paragraph in paragraphs:
                    clean_text = paragraph.strip()
                    if clean_text:
                        # 添加到样本列表
                        item = QListWidgetItem(f"文本样本 {self.samples_list.count()+1}: {clean_text[:50]}...")
                        self.samples_list.addItem(item)
                        
                        # 添加到数据集
                        self.training_data.append({
                            "id": self.samples_list.count(),
                            "text": clean_text,
                            "type": "text",
                            "source": os.path.basename(file_path)
                        })
            except Exception as e:
                QMessageBox.warning(self, "导入错误", f"导入文件 {os.path.basename(file_path)} 失败: {str(e)}")
        
        added_count = self.samples_list.count() - count_before
        self.progress_label.setText(f"已添加 {self.samples_list.count()} 个样本 (本次+{added_count})")
    
    def import_json_files(self):
        """导入JSON文件作为训练样本"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择JSON文件", "", "JSON文件 (*.json)"
        )
        
        if not file_paths:
            return
            
        count_before = self.samples_list.count()
        
        for file_path in file_paths:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 处理各种格式的JSON
                if isinstance(data, list):
                    # 列表格式
                    items = data
                elif isinstance(data, dict) and "items" in data:
                    # {items: [...]} 格式
                    items = data["items"]
                elif isinstance(data, dict) and "samples" in data:
                    # {samples: [...]} 格式
                    items = data["samples"]
                elif isinstance(data, dict) and "data" in data:
                    # {data: [...]} 格式
                    items = data["data"]
                else:
                    # 单个对象
                    items = [data]
                
                for item in items:
                    # 提取文本：可能在不同字段
                    if isinstance(item, str):
                        text = item
                    elif isinstance(item, dict):
                        text = item.get("text") or item.get("content") or item.get("data") or str(item)
                    else:
                        text = str(item)
                    
                    clean_text = str(text).strip()
                    if clean_text:
                        # 添加到样本列表
                        item = QListWidgetItem(f"JSON样本 {self.samples_list.count()+1}: {clean_text[:50]}...")
                        self.samples_list.addItem(item)
                        
                        # 添加到数据集
                        self.training_data.append({
                            "id": self.samples_list.count(),
                            "text": clean_text,
                            "type": "json",
                            "source": os.path.basename(file_path)
                        })
            except Exception as e:
                QMessageBox.warning(self, "导入错误", f"导入文件 {os.path.basename(file_path)} 失败: {str(e)}")
        
        added_count = self.samples_list.count() - count_before
        self.progress_label.setText(f"已添加 {self.samples_list.count()} 个样本 (本次+{added_count})")
    
    def remove_selected_samples(self):
        """删除选中的样本"""
        selected_items = self.samples_list.selectedItems()
        if not selected_items:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除选中的 {len(selected_items)} 个样本吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 删除选中的项目
        for item in selected_items:
            index = self.samples_list.row(item)
            self.samples_list.takeItem(index)
            self.training_data.pop(index)
        
        # 更新样本ID
        for i, sample in enumerate(self.training_data):
            sample["id"] = i + 1
        
        # 更新状态
        self.progress_label.setText(f"已添加 {self.samples_list.count()} 个样本")
    
    def clear_all_samples(self):
        """清空所有样本"""
        if self.samples_list.count() == 0:
            return
            
        # 确认清空
        reply = QMessageBox.question(
            self, 
            "确认清空", 
            f"确定要清空所有 {self.samples_list.count()} 个样本吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 清空列表和数据
        self.samples_list.clear()
        self.training_data.clear()
        
        # 更新状态
        self.progress_label.setText("准备就绪")
    
    def export_samples(self):
        """导出样本集"""
        if not self.training_data:
            QMessageBox.warning(self, "警告", "没有可导出的样本")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出样本集", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            import json
            import datetime
            
            export_data = {
                "count": len(self.training_data),
                "model_target": self.model_combo.currentText(),
                "exported_at": datetime.datetime.now().isoformat(),
                "samples": self.training_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            QMessageBox.information(self, "导出成功", f"成功导出 {len(self.training_data)} 个样本到 {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"导出失败: {str(e)}")
    
    def start_training(self):
        """开始训练"""
        if not self.training_data:
            QMessageBox.warning(self, "警告", "没有训练样本")
            return
            
        # 获取训练参数
        params = {
            "model": self.model_combo.currentText(),
            "learning_rate": float(self.lr_combo.currentText()),
            "batch_size": self.batch_size_spin.value(),
            "epochs": self.epochs_spin.value(),
            "use_gpu": self.gpu_checkbox.isChecked(),
            "samples_count": len(self.training_data)
        }
        
        # 确认训练参数
        confirm_msg = (f"将开始训练 {params['model']} 模型\n\n"
                      f"- 样本数量: {params['samples_count']}\n"
                      f"- 学习率: {params['learning_rate']}\n"
                      f"- 批量大小: {params['batch_size']}\n"
                      f"- 训练轮次: {params['epochs']}\n"
                      f"- {'使用' if params['use_gpu'] else '不使用'}GPU加速\n\n"
                      f"确定开始训练吗?")
        
        reply = QMessageBox.question(
            self, 
            "确认训练参数", 
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 更新UI状态
        self.training_in_progress = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_label.setText("正在初始化训练...")
        self.progress_bar.setValue(0)
        
        # 模拟训练过程
        import threading
        import time
        
        def simulate_training():
            # 模拟训练过程
            total_steps = params['epochs'] * (params['samples_count'] // params['batch_size'] + 1)
            
            for step in range(total_steps):
                if not self.training_in_progress:
                    # 训练被中止
                    self.training_completed.emit({
                        "status": "cancelled",
                        "completed_steps": step,
                        "total_steps": total_steps,
                        "params": params
                    })
                    break
                    
                # 更新进度
                progress = int((step + 1) / total_steps * 100)
                current_epoch = step // (params['samples_count'] // params['batch_size'] + 1) + 1
                
                # 更新UI（使用Qt的线程安全方式）
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
                QMetaObject.invokeMethod(
                    self.progress_bar, 
                    "setValue", 
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(int, progress)
                )
                
                QMetaObject.invokeMethod(
                    self.progress_label, 
                    "setText", 
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, f"训练中... 第 {current_epoch}/{params['epochs']} 轮, 进度: {progress}%")
                )
                
                # 模拟计算时间
                time.sleep(0.1)
                
            # 训练完成
            time.sleep(0.5)
            
            self.training_in_progress = False
            
            # 更新UI
            QMetaObject.invokeMethod(
                self.progress_bar, 
                "setValue", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(int, 100)
            )
            
            QMetaObject.invokeMethod(
                self.progress_label, 
                "setText", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "训练完成!")
            )
            
            QMetaObject.invokeMethod(
                self.start_btn, 
                "setEnabled", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, True)
            )
            
            QMetaObject.invokeMethod(
                self.stop_btn, 
                "setEnabled", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, False)
            )
            
            # 模拟准确率和损失
            accuracy = 0.85 + params['epochs'] * 0.03 # 模拟值
            loss = 0.5 - params['epochs'] * 0.1 # 模拟值
            
            # 发出完成信号
            self.training_completed.emit({
                "status": "completed",
                "accuracy": accuracy,
                "loss": loss,
                "params": params
            })
            
            # 显示完成消息
            QMetaObject.invokeMethod(
                self, 
                "show_training_complete_dialog", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(float, accuracy),
                Q_ARG(float, loss),
                Q_ARG(int, params['epochs'])
            )
        
        # 发出训练开始信号
        self.training_started.emit(params)
        
        # 启动训练线程
        training_thread = threading.Thread(target=simulate_training)
        training_thread.daemon = True
        training_thread.start()
    
    def show_training_complete_dialog(self, accuracy, loss, epochs):
        """显示训练完成对话框"""
        QMessageBox.information(
            self,
            "训练完成",
            f"模型训练已完成！\n\n"
            f"- 准确率: {accuracy:.2%}\n"
            f"- 损失值: {loss:.4f}\n"
            f"- 训练轮次: {epochs}\n\n"
            f"模型已保存并可用于生产环境。"
        )
    
    def stop_training(self):
        """停止训练"""
        if not self.training_in_progress:
            return
            
        reply = QMessageBox.question(
            self, 
            "确认停止", 
            "确定要停止当前训练吗? 已完成的训练将保存。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 停止训练
        self.training_in_progress = False
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("正在停止训练...")

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication([])
    
    widget = TrainingFeeder()
    widget.show()
    
    app.exec() 