#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
元数据剪辑编辑器对话框

提供可视化的元数据剪辑编辑界面,支持创建、编辑、预览和执行剪辑操作。
"""

import os
import json
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QComboBox,
    QLineEdit, QFileDialog, QMessageBox, QSplitter,
    QTextEdit, QDoubleSpinBox, QFormLayout, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.exporters.metaclip_engine import (
    MetaClipEngine, MetaClip, OperationType, CodecMode
)
from src.utils.log_handler import get_logger

logger = get_logger("metaclip_editor")


class MetaClipEditorDialog(QDialog):
    """元数据剪辑编辑器对话框"""
    
    # 信号
    operation_executed = pyqtSignal(dict)  # 操作执行完成信号
    
    def __init__(self, parent=None):
        """初始化元数据剪辑编辑器对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("元数据剪辑编辑器")
        self.resize(1000, 700)
        
        # 初始化MetaClipEngine
        self.engine = MetaClipEngine()
        
        # 当前操作列表
        self.operations: List[MetaClip] = []
        
        # 当前选中的操作
        self.current_operation: Optional[MetaClip] = None
        
        # 初始化UI
        self._init_ui()
        
        logger.info("元数据剪辑编辑器对话框初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("元数据剪辑编辑器")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明文字
        desc_label = QLabel(
            "使用元数据描述剪辑操作,支持切片、连接、转场等12种操作类型。\n"
            "左侧列表显示所有操作,右侧编辑当前操作的参数。"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(desc_label)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧: 操作列表
        left_widget = self._create_operation_list()
        splitter.addWidget(left_widget)
        
        # 右侧: 参数编辑
        right_widget = self._create_parameter_editor()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 底部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
    
    def _create_operation_list(self) -> QGroupBox:
        """创建操作列表区域
        
        Returns:
            QGroupBox: 操作列表组件
        """
        group = QGroupBox("操作列表")
        layout = QVBoxLayout(group)
        
        # 操作树
        self.operation_tree = QTreeWidget()
        self.operation_tree.setHeaderLabels(["操作", "类型", "源文件"])
        self.operation_tree.setColumnWidth(0, 150)
        self.operation_tree.setColumnWidth(1, 100)
        self.operation_tree.itemClicked.connect(self._on_operation_selected)
        layout.addWidget(self.operation_tree)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加操作")
        add_btn.clicked.connect(self._add_operation)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("删除操作")
        remove_btn.clicked.connect(self._remove_operation)
        button_layout.addWidget(remove_btn)
        
        move_up_btn = QPushButton("上移")
        move_up_btn.clicked.connect(self._move_operation_up)
        button_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("下移")
        move_down_btn.clicked.connect(self._move_operation_down)
        button_layout.addWidget(move_down_btn)
        
        layout.addLayout(button_layout)
        
        return group
    
    def _create_parameter_editor(self) -> QGroupBox:
        """创建参数编辑区域
        
        Returns:
            QGroupBox: 参数编辑组件
        """
        group = QGroupBox("参数编辑")
        layout = QFormLayout(group)
        
        # 操作类型
        self.operation_type_combo = QComboBox()
        for op_type in OperationType:
            self.operation_type_combo.addItem(op_type.value, op_type)
        self.operation_type_combo.currentIndexChanged.connect(self._on_operation_type_changed)
        layout.addRow("操作类型:", self.operation_type_combo)
        
        # 源文件
        src_layout = QHBoxLayout()
        self.src_input = QLineEdit()
        src_layout.addWidget(self.src_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_source_file)
        src_layout.addWidget(browse_btn)
        
        layout.addRow("源文件:", src_layout)
        
        # 入点时间
        self.in_point_spin = QDoubleSpinBox()
        self.in_point_spin.setRange(0, 999999)
        self.in_point_spin.setDecimals(2)
        self.in_point_spin.setSuffix(" 秒")
        layout.addRow("入点时间:", self.in_point_spin)
        
        # 出点时间
        self.out_point_spin = QDoubleSpinBox()
        self.out_point_spin.setRange(0, 999999)
        self.out_point_spin.setDecimals(2)
        self.out_point_spin.setSuffix(" 秒")
        layout.addRow("出点时间:", self.out_point_spin)
        
        # 编解码模式
        self.codec_combo = QComboBox()
        for codec in CodecMode:
            self.codec_combo.addItem(codec.value, codec)
        layout.addRow("编解码模式:", self.codec_combo)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        output_layout.addWidget(self.output_input)
        
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self._browse_output_file)
        output_layout.addWidget(output_browse_btn)
        
        layout.addRow("输出文件:", output_layout)
        
        # 附加参数
        self.params_text = QTextEdit()
        self.params_text.setPlaceholderText('{"key": "value"}')
        self.params_text.setMaximumHeight(100)
        layout.addRow("附加参数(JSON):", self.params_text)
        
        # 应用按钮
        apply_btn = QPushButton("应用修改")
        apply_btn.clicked.connect(self._apply_changes)
        layout.addRow("", apply_btn)
        
        return group
    
    def _create_toolbar(self) -> QGroupBox:
        """创建底部工具栏
        
        Returns:
            QGroupBox: 工具栏组件
        """
        group = QGroupBox()
        layout = QHBoxLayout(group)
        
        # 导入元数据
        import_btn = QPushButton("导入元数据")
        import_btn.clicked.connect(self._import_metadata)
        layout.addWidget(import_btn)
        
        # 导出元数据
        export_btn = QPushButton("导出元数据")
        export_btn.clicked.connect(self._export_metadata)
        layout.addWidget(export_btn)
        
        layout.addStretch()
        
        # 预览
        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self._preview_operations)
        layout.addWidget(preview_btn)
        
        # 执行
        execute_btn = QPushButton("执行")
        execute_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        execute_btn.clicked.connect(self._execute_operations)
        layout.addWidget(execute_btn)
        
        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return group
    
    def _add_operation(self):
        """添加新操作"""
        # 创建新的MetaClip
        new_operation = MetaClip(
            operation=OperationType.SLICE.value,
            src="",
            in_point=0.0,
            out_point=0.0,
            codec=CodecMode.COPY.value
        )
        
        self.operations.append(new_operation)
        self._refresh_operation_tree()
        
        logger.info(f"添加新操作: {new_operation.id}")
    
    def _remove_operation(self):
        """删除选中的操作"""
        current_item = self.operation_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的操作")
            return
        
        # 获取操作ID
        operation_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # 从列表中删除
        self.operations = [op for op in self.operations if op.id != operation_id]
        self._refresh_operation_tree()
        
        logger.info(f"删除操作: {operation_id}")
    
    def _move_operation_up(self):
        """上移操作"""
        current_item = self.operation_tree.currentItem()
        if not current_item:
            return
        
        operation_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # 找到操作索引
        for i, op in enumerate(self.operations):
            if op.id == operation_id and i > 0:
                self.operations[i], self.operations[i-1] = self.operations[i-1], self.operations[i]
                self._refresh_operation_tree()
                break
    
    def _move_operation_down(self):
        """下移操作"""
        current_item = self.operation_tree.currentItem()
        if not current_item:
            return
        
        operation_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # 找到操作索引
        for i, op in enumerate(self.operations):
            if op.id == operation_id and i < len(self.operations) - 1:
                self.operations[i], self.operations[i+1] = self.operations[i+1], self.operations[i]
                self._refresh_operation_tree()
                break

    def _refresh_operation_tree(self):
        """刷新操作树"""
        self.operation_tree.clear()

        for i, operation in enumerate(self.operations):
            item = QTreeWidgetItem()
            item.setText(0, f"操作 {i+1}")
            item.setText(1, operation.operation)

            # 显示源文件
            if isinstance(operation.src, list):
                item.setText(2, f"{len(operation.src)} 个文件")
            else:
                src_name = os.path.basename(operation.src) if operation.src else "未设置"
                item.setText(2, src_name)

            # 保存操作ID
            item.setData(0, Qt.ItemDataRole.UserRole, operation.id)

            self.operation_tree.addTopLevelItem(item)

    def _on_operation_selected(self, item: QTreeWidgetItem, column: int):
        """操作被选中时的回调

        Args:
            item: 选中的项
            column: 列索引
        """
        operation_id = item.data(0, Qt.ItemDataRole.UserRole)

        # 找到对应的操作
        for operation in self.operations:
            if operation.id == operation_id:
                self.current_operation = operation
                self._load_operation_to_editor(operation)
                break

    def _load_operation_to_editor(self, operation: MetaClip):
        """加载操作到编辑器

        Args:
            operation: 要加载的操作
        """
        # 设置操作类型
        index = self.operation_type_combo.findData(OperationType(operation.operation))
        if index >= 0:
            self.operation_type_combo.setCurrentIndex(index)

        # 设置源文件
        if isinstance(operation.src, list):
            self.src_input.setText(", ".join(operation.src))
        else:
            self.src_input.setText(operation.src)

        # 设置时间点
        self.in_point_spin.setValue(operation.in_point or 0.0)
        self.out_point_spin.setValue(operation.out_point or 0.0)

        # 设置编解码模式
        codec_index = self.codec_combo.findData(CodecMode(operation.codec))
        if codec_index >= 0:
            self.codec_combo.setCurrentIndex(codec_index)

        # 设置输出文件
        output = operation.params.get("output", "")
        self.output_input.setText(output)

        # 设置附加参数
        params_copy = operation.params.copy()
        params_copy.pop("output", None)  # 移除output,因为已经单独显示
        if params_copy:
            self.params_text.setPlainText(json.dumps(params_copy, indent=2, ensure_ascii=False))
        else:
            self.params_text.clear()

    def _on_operation_type_changed(self, index: int):
        """操作类型改变时的回调

        Args:
            index: 新的索引
        """
        operation_type = self.operation_type_combo.currentData()

        # 根据操作类型调整UI
        if operation_type == OperationType.CONCAT:
            self.src_input.setPlaceholderText("多个文件路径,用逗号分隔")
        else:
            self.src_input.setPlaceholderText("单个文件路径")

    def _browse_source_file(self):
        """浏览源文件"""
        operation_type = self.operation_type_combo.currentData()

        if operation_type == OperationType.CONCAT:
            # 多文件选择
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择源文件",
                "",
                "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
            )
            if files:
                self.src_input.setText(", ".join(files))
        else:
            # 单文件选择
            file, _ = QFileDialog.getOpenFileName(
                self,
                "选择源文件",
                "",
                "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
            )
            if file:
                self.src_input.setText(file)

    def _browse_output_file(self):
        """浏览输出文件"""
        file, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )
        if file:
            self.output_input.setText(file)

    def _apply_changes(self):
        """应用修改"""
        if not self.current_operation:
            QMessageBox.warning(self, "警告", "请先选择要修改的操作")
            return

        try:
            # 获取操作类型
            operation_type = self.operation_type_combo.currentData()
            self.current_operation.operation = operation_type.value

            # 获取源文件
            src_text = self.src_input.text().strip()
            if operation_type == OperationType.CONCAT:
                # 多文件
                self.current_operation.src = [s.strip() for s in src_text.split(",") if s.strip()]
            else:
                # 单文件
                self.current_operation.src = src_text

            # 获取时间点
            self.current_operation.in_point = self.in_point_spin.value()
            self.current_operation.out_point = self.out_point_spin.value()

            # 获取编解码模式
            codec = self.codec_combo.currentData()
            self.current_operation.codec = codec.value

            # 获取附加参数
            params = {}
            params_text = self.params_text.toPlainText().strip()
            if params_text:
                params = json.loads(params_text)

            # 添加输出文件
            output = self.output_input.text().strip()
            if output:
                params["output"] = output

            self.current_operation.params = params

            # 刷新树
            self._refresh_operation_tree()

            QMessageBox.information(self, "成功", "修改已应用")
            logger.info(f"应用修改: {self.current_operation.id}")

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "错误", f"附加参数JSON格式错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用修改失败: {e}")
            logger.error(f"应用修改失败: {e}")

    def _import_metadata(self):
        """导入元数据"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "导入元数据",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if not file:
            return

        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 清空现有操作
            self.operations.clear()

            # 加载操作
            if isinstance(data, list):
                for item in data:
                    operation = MetaClip.from_dict(item)
                    self.operations.append(operation)
            else:
                operation = MetaClip.from_dict(data)
                self.operations.append(operation)

            self._refresh_operation_tree()

            QMessageBox.information(self, "成功", f"成功导入 {len(self.operations)} 个操作")
            logger.info(f"导入元数据: {file}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")
            logger.error(f"导入元数据失败: {e}")

    def _export_metadata(self):
        """导出元数据"""
        if not self.operations:
            QMessageBox.warning(self, "警告", "没有可导出的操作")
            return

        file, _ = QFileDialog.getSaveFileName(
            self,
            "导出元数据",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if not file:
            return

        try:
            # 转换为字典列表
            data = [op.to_dict() for op in self.operations]

            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "成功", f"成功导出 {len(self.operations)} 个操作")
            logger.info(f"导出元数据: {file}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
            logger.error(f"导出元数据失败: {e}")

    def _preview_operations(self):
        """预览操作"""
        if not self.operations:
            QMessageBox.warning(self, "警告", "没有可预览的操作")
            return

        # 生成预览文本
        preview_text = "操作流程预览:\n\n"

        for i, operation in enumerate(self.operations):
            preview_text += f"步骤 {i+1}: {operation.operation}\n"
            preview_text += f"  源文件: {operation.src}\n"

            if operation.in_point is not None:
                preview_text += f"  入点: {operation.in_point}秒\n"
            if operation.out_point is not None:
                preview_text += f"  出点: {operation.out_point}秒\n"

            preview_text += f"  编解码: {operation.codec}\n"

            if operation.params:
                preview_text += f"  参数: {json.dumps(operation.params, ensure_ascii=False)}\n"

            preview_text += "\n"

        # 显示预览对话框
        QMessageBox.information(self, "操作预览", preview_text)

    def _execute_operations(self):
        """执行操作"""
        if not self.operations:
            QMessageBox.warning(self, "警告", "没有可执行的操作")
            return

        # 确认执行
        reply = QMessageBox.question(
            self,
            "确认执行",
            f"确定要执行 {len(self.operations)} 个操作吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 创建进度对话框
        progress = QProgressDialog("正在执行操作...", "取消", 0, len(self.operations), self)
        progress.setWindowTitle("执行中")
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        results = []

        try:
            for i, operation in enumerate(self.operations):
                if progress.wasCanceled():
                    break

                progress.setValue(i)
                progress.setLabelText(f"正在执行操作 {i+1}/{len(self.operations)}: {operation.operation}")

                # 执行操作
                result = self.engine.process(operation)
                results.append(result)

                logger.info(f"执行操作 {i+1}: {result}")

            progress.setValue(len(self.operations))

            # 显示结果
            if results:
                QMessageBox.information(
                    self,
                    "执行完成",
                    f"成功执行 {len(results)} 个操作"
                )

                # 发送信号
                self.operation_executed.emit({"results": results})

        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行失败: {e}")
            logger.error(f"执行操作失败: {e}")
        finally:
            progress.close()


