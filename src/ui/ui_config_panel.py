#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户界面配置绑定模块

负责将用户界面元素绑定到配置系统，实现自动同步配置更改到UI界面
和从UI界面更新到配置系统。支持多种UI组件类型和复杂的配置路径。
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Callable, Union, TypeVar

from PyQt6.QtWidgets import (
    QWidget, QComboBox, QLineEdit, QSlider, QSpinBox, QDoubleSpinBox,
    QCheckBox, QRadioButton, QListWidget, QTextEdit, QPlainTextEdit,
    QFileDialog, QButtonGroup, QAbstractButton
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

# 导入配置系统
try:
    from src.config import config_manager
    from src.utils.log_handler import get_logger
except ImportError as e:
    # 如果无法导入，使用标准日志
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    # 模拟配置管理器
    class MockConfigManager:
        def __init__(self):
            self.configs = {
                "user": {},
                "system": {},
                "version": {},
                "export": {},
                "app": {}
            }
        
        def get_config(self, config_type, key=None):
            if key is None:
                return self.configs.get(config_type, {})
            
            if "." in key:
                parts = key.split(".")
                value = self.configs.get(config_type, {})
                for part in parts:
                    if part not in value:
                        return None
                    value = value[part]
                return value
            
            return self.configs.get(config_type, {}).get(key)
        
        def set_config(self, config_type, key, value):
            if "." in key:
                parts = key.split(".")
                config = self.configs.setdefault(config_type, {})
                for part in parts[:-1]:
                    config = config.setdefault(part, {})
                config[parts[-1]] = value
            else:
                self.configs.setdefault(config_type, {})[key] = value
    
    config_manager = MockConfigManager()

# 设置日志记录器
logger = get_logger("ui_config_binder")

class ConfigBinder(QObject):
    """
    配置绑定器，负责UI元素和配置的双向绑定
    
    支持多种UI组件类型，包括：
    - QComboBox (下拉选择框)
    - QLineEdit (单行文本输入框)
    - QTextEdit/QPlainTextEdit (多行文本输入框)
    - QSlider (滑块)
    - QSpinBox/QDoubleSpinBox (数字输入框)
    - QCheckBox (复选框)
    - QRadioButton (单选按钮)
    - QListWidget (列表部件)
    - QFileDialog (文件选择器)
    """
    
    # 定义信号
    config_changed = pyqtSignal(str, str, object)  # 配置类型, 键, 值
    ui_updated = pyqtSignal(str, object)  # 组件ID, 值
    
    def __init__(self, ui_elements: Dict[str, Any], config_type: str = "user"):
        """
        初始化配置绑定器
        
        Args:
            ui_elements: UI元素字典，键为元素ID，值为UI控件
            config_type: 配置类型，默认为 "user"
        """
        super().__init__()
        self.ui_elements = ui_elements
        self.config_type = config_type
        self.mapping = {}  # 配置键到UI控件的映射
        self.reverse_mapping = {}  # UI控件到配置键的映射
        self.watchers = []  # 配置变化监听器
        self.validators = {}  # 验证器
        self.transformers = {}  # 数据转换器
        self.default_values = {}  # 默认值
        self.initialized = False
        self.hot_reloaded = False
        
        # 初始化热重载监听器
        self._setup_hot_reload()
    
    def _setup_hot_reload(self):
        """设置配置热重载监听"""
        try:
            # 如果热重载可用，设置监听
            from src.config.hot_reload import get_config_watcher, watch_config
            
            # 创建配置监听器
            watcher = get_config_watcher()
            
            # 添加监听
            watcher.add_listener(self._on_config_changed)
            
            # 监听特定配置类型
            watch_config(self.config_type)
            
            # 标记已启用热重载
            self.hot_reloaded = True
            logger.info(f"已启用 {self.config_type} 配置的热重载监听")
        except ImportError:
            logger.warning("配置热重载模块不可用，将不会自动响应配置文件变化")
    
    def _on_config_changed(self, config_type: str, key: str, value: Any):
        """
        当配置变化时调用
        
        Args:
            config_type: 配置类型
            key: 配置键
            value: 新值
        """
        if config_type != self.config_type:
            return
        
        # 检查是否有对应的UI元素
        mapping_key = f"{config_type}.{key}"
        if mapping_key in self.mapping:
            # 更新UI元素
            ui_element = self.mapping[mapping_key]
            self._update_ui_element(ui_element, value)
            
            # 发出信号
            self.ui_updated.emit(key, value)
            logger.debug(f"由于配置变化更新UI元素: {key} -> {value}")
    
    def bind(self, config_key: str, ui_element_id: str, default_value: Any = None, 
             validator: Optional[Callable[[Any], bool]] = None,
             transformer: Optional[Callable[[Any], Any]] = None):
        """
        绑定配置键到UI元素
        
        Args:
            config_key: 配置键，支持点分隔的路径如 "export.resolution"
            ui_element_id: UI元素ID
            default_value: 默认值
            validator: 可选的验证器函数
            transformer: 可选的数据转换器
        """
        if ui_element_id not in self.ui_elements:
            logger.warning(f"UI元素不存在: {ui_element_id}")
            return False
        
        ui_element = self.ui_elements[ui_element_id]
        
        # 存储映射
        full_key = f"{self.config_type}.{config_key}"
        self.mapping[full_key] = ui_element
        self.reverse_mapping[ui_element] = full_key
        
        # 存储默认值、验证器和转换器
        if default_value is not None:
            self.default_values[full_key] = default_value
        
        if validator is not None:
            self.validators[full_key] = validator
        
        if transformer is not None:
            self.transformers[full_key] = transformer
        
        # 连接UI元素的信号
        self._connect_ui_signals(ui_element, config_key)
        
        # 立即加载配置值到UI
        self._load_config_to_ui(config_key, ui_element, default_value)
        
        return True
    
    def bind_multiple(self, mappings: Dict[str, str], defaults: Dict[str, Any] = None):
        """
        批量绑定多个配置键到UI元素
        
        Args:
            mappings: 配置键到UI元素ID的映射字典
            defaults: 可选的默认值字典
        """
        if defaults is None:
            defaults = {}
        
        for config_key, ui_element_id in mappings.items():
            default_value = defaults.get(config_key)
            self.bind(config_key, ui_element_id, default_value)
    
    def _connect_ui_signals(self, ui_element: QWidget, config_key: str):
        """
        连接UI元素的信号到配置更新
        
        Args:
            ui_element: UI控件
            config_key: 配置键
        """
        # 根据控件类型连接合适的信号
        if isinstance(ui_element, QComboBox):
            ui_element.currentIndexChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, QLineEdit):
            ui_element.textChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, (QTextEdit, QPlainTextEdit)):
            ui_element.textChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, QSlider):
            ui_element.valueChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, (QSpinBox, QDoubleSpinBox)):
            ui_element.valueChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, QCheckBox):
            ui_element.stateChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, QRadioButton):
            ui_element.toggled.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, QListWidget):
            ui_element.itemSelectionChanged.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
        
        elif isinstance(ui_element, QButtonGroup):
            ui_element.buttonClicked.connect(
                lambda: self._update_config_from_ui(ui_element, config_key)
            )
    
    def _load_config_to_ui(self, config_key: str, ui_element: QWidget, default_value: Any = None):
        """
        从配置加载值到UI元素
        
        Args:
            config_key: 配置键
            ui_element: UI控件
            default_value: 默认值
        """
        # 从配置获取值
        value = config_manager.get_config(self.config_type, config_key)
        
        # 如果值不存在且有默认值，使用默认值并设置到配置中
        if value is None and default_value is not None:
            value = default_value
            config_manager.set_config(self.config_type, config_key, value)
        
        # 如果仍然为None，直接返回
        if value is None:
            return
        
        # 如果有转换器，应用转换
        full_key = f"{self.config_type}.{config_key}"
        if full_key in self.transformers:
            try:
                value = self.transformers[full_key](value)
            except Exception as e:
                logger.error(f"应用转换器失败: {full_key}, 错误: {str(e)}")
        
        # 更新UI元素
        self._update_ui_element(ui_element, value)
    
    def _update_ui_element(self, ui_element: QWidget, value: Any):
        """
        更新UI元素的值
        
        Args:
            ui_element: UI控件
            value: 要设置的值
        """
        try:
            # 根据控件类型设置值
            if isinstance(ui_element, QComboBox):
                if isinstance(value, str):
                    index = ui_element.findText(value)
                    if index >= 0:
                        ui_element.setCurrentIndex(index)
                elif isinstance(value, int) and value < ui_element.count():
                    ui_element.setCurrentIndex(value)
            
            elif isinstance(ui_element, QLineEdit):
                ui_element.setText(str(value))
            
            elif isinstance(ui_element, (QTextEdit, QPlainTextEdit)):
                ui_element.setPlainText(str(value))
            
            elif isinstance(ui_element, QSlider):
                ui_element.setValue(int(value))
            
            elif isinstance(ui_element, QSpinBox):
                ui_element.setValue(int(value))
            
            elif isinstance(ui_element, QDoubleSpinBox):
                ui_element.setValue(float(value))
            
            elif isinstance(ui_element, QCheckBox):
                ui_element.setChecked(bool(value))
            
            elif isinstance(ui_element, QRadioButton):
                ui_element.setChecked(bool(value))
            
            elif isinstance(ui_element, QListWidget):
                if isinstance(value, list):
                    # 清除当前选择
                    ui_element.clearSelection()
                    # 选择匹配的项
                    for i in range(ui_element.count()):
                        item = ui_element.item(i)
                        if item.text() in value or i in value:
                            item.setSelected(True)
                else:
                    # 单个值情况
                    for i in range(ui_element.count()):
                        item = ui_element.item(i)
                        if item.text() == value or i == value:
                            ui_element.setCurrentItem(item)
                            break
            
            elif isinstance(ui_element, QButtonGroup):
                if isinstance(value, int):
                    button = ui_element.button(value)
                    if button:
                        button.setChecked(True)
                elif isinstance(value, str):
                    # 通过文本匹配按钮
                    for button in ui_element.buttons():
                        if button.text() == value:
                            button.setChecked(True)
                            break
        
        except Exception as e:
            logger.error(f"更新UI元素失败: {type(ui_element).__name__}, 值: {value}, 错误: {str(e)}")
    
    def _update_config_from_ui(self, ui_element: QWidget, config_key: str):
        """
        从UI元素更新配置
        
        Args:
            ui_element: UI控件
            config_key: 配置键
        """
        # 获取UI元素的值
        value = self._get_ui_element_value(ui_element)
        
        # 如果有验证器，验证值
        full_key = f"{self.config_type}.{config_key}"
        if full_key in self.validators and not self.validators[full_key](value):
            logger.warning(f"配置值验证失败: {config_key}, 值: {value}")
            
            # 恢复到原始值
            orig_value = config_manager.get_config(self.config_type, config_key)
            if orig_value is not None:
                self._update_ui_element(ui_element, orig_value)
            
            return
        
        # 如果有转换器，应用逆向转换
        if full_key in self.transformers:
            try:
                # 这里假设转换器能处理双向转换，实际中可能需要单独的逆向转换器
                if hasattr(self.transformers[full_key], "inverse"):
                    value = self.transformers[full_key].inverse(value)
            except Exception as e:
                logger.error(f"应用逆向转换器失败: {full_key}, 错误: {str(e)}")
        
        # 更新配置
        config_manager.set_config(self.config_type, config_key, value)
        
        # 发出信号
        self.config_changed.emit(self.config_type, config_key, value)
        logger.debug(f"从UI更新配置: {config_key} -> {value}")
    
    def _get_ui_element_value(self, ui_element: QWidget) -> Any:
        """
        获取UI元素的当前值
        
        Args:
            ui_element: UI控件
            
        Returns:
            Any: UI元素的值
        """
        if isinstance(ui_element, QComboBox):
            # 返回当前选中的数据或文本
            index = ui_element.currentIndex()
            if ui_element.itemData(index) is not None:
                return ui_element.itemData(index)
            return ui_element.currentText()
        
        elif isinstance(ui_element, QLineEdit):
            return ui_element.text()
        
        elif isinstance(ui_element, (QTextEdit, QPlainTextEdit)):
            return ui_element.toPlainText()
        
        elif isinstance(ui_element, QSlider):
            return ui_element.value()
        
        elif isinstance(ui_element, (QSpinBox, QDoubleSpinBox)):
            return ui_element.value()
        
        elif isinstance(ui_element, QCheckBox):
            return ui_element.isChecked()
        
        elif isinstance(ui_element, QRadioButton):
            return ui_element.isChecked()
        
        elif isinstance(ui_element, QListWidget):
            if ui_element.selectionMode() == QListWidget.SelectionMode.SingleSelection:
                item = ui_element.currentItem()
                return item.text() if item else None
            else:
                return [item.text() for item in ui_element.selectedItems()]
        
        elif isinstance(ui_element, QButtonGroup):
            button = ui_element.checkedButton()
            if button:
                return button.text()
            return None
        
        # 默认返回None
        return None
    
    def ui_to_config(self):
        """将UI元素的值同步到配置，通常在应用关闭时调用"""
        for ui_element, full_key in self.reverse_mapping.items():
            parts = full_key.split(".", 1)
            if len(parts) == 2:
                config_type, config_key = parts
                self._update_config_from_ui(ui_element, config_key)
    
    def config_to_ui(self):
        """将配置的值同步到UI元素，通常在应用启动时调用"""
        for full_key, ui_element in self.mapping.items():
            parts = full_key.split(".", 1)
            if len(parts) == 2:
                config_type, config_key = parts
                default_value = self.default_values.get(full_key)
                self._load_config_to_ui(config_key, ui_element, default_value)

# 定义一些常用的验证器
class Validators:
    """常用验证器集合"""
    
    @staticmethod
    def range(min_val, max_val):
        """范围验证器"""
        return lambda x: min_val <= x <= max_val
    
    @staticmethod
    def min_length(min_len):
        """最小长度验证器"""
        return lambda x: len(str(x)) >= min_len
    
    @staticmethod
    def max_length(max_len):
        """最大长度验证器"""
        return lambda x: len(str(x)) <= max_len
    
    @staticmethod
    def pattern(regex):
        """正则表达式验证器"""
        import re
        pattern = re.compile(regex)
        return lambda x: bool(pattern.match(str(x)))
    
    @staticmethod
    def file_exists():
        """文件存在验证器"""
        return lambda x: os.path.exists(str(x))
    
    @staticmethod
    def directory_exists():
        """目录存在验证器"""
        return lambda x: os.path.isdir(str(x))
    
    @staticmethod
    def is_int():
        """整数验证器"""
        return lambda x: isinstance(x, int) or (isinstance(x, str) and x.isdigit())
    
    @staticmethod
    def is_float():
        """浮点数验证器"""
        return lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())
    
    @staticmethod
    def in_list(values):
        """列表成员验证器"""
        return lambda x: x in values

# 定义一些常用的转换器
class Transformers:
    """常用转换器集合"""
    
    @staticmethod
    def path_to_string():
        """路径对象到字符串的转换器"""
        return lambda x: str(x) if x is not None else ""
    
    @staticmethod
    def string_to_path():
        """字符串到路径对象的转换器"""
        from pathlib import Path
        return lambda x: Path(x) if x else None
    
    @staticmethod
    def str_to_int():
        """字符串到整数的转换器"""
        return lambda x: int(x) if x and str(x).strip() else 0
    
    @staticmethod
    def str_to_float():
        """字符串到浮点数的转换器"""
        return lambda x: float(x) if x and str(x).strip() else 0.0
    
    @staticmethod
    def bool_to_str():
        """布尔值到字符串的转换器"""
        return lambda x: "是" if x else "否"
    
    @staticmethod
    def str_to_bool():
        """字符串到布尔值的转换器"""
        true_values = ["是", "true", "yes", "1", "on", "开启", "启用"]
        return lambda x: str(x).lower() in true_values if x else False
    
    @staticmethod
    def list_to_str(separator=","):
        """列表到字符串的转换器"""
        return lambda x: separator.join(str(i) for i in x) if isinstance(x, list) else str(x)
    
    @staticmethod
    def str_to_list(separator=","):
        """字符串到列表的转换器"""
        return lambda x: x.split(separator) if isinstance(x, str) else []

# 双向转换器基类
class BiTransformer:
    """双向转换器基类"""
    
    def __call__(self, value):
        """正向转换"""
        return self.forward(value)
    
    def forward(self, value):
        """正向转换"""
        raise NotImplementedError
    
    def inverse(self, value):
        """逆向转换"""
        raise NotImplementedError

# 示例：分辨率转换器，在字符串和元组之间转换
class ResolutionTransformer(BiTransformer):
    """分辨率转换器，在字符串和元组之间转换"""
    
    def forward(self, value):
        """(1920, 1080) -> '1920x1080'"""
        if isinstance(value, tuple) and len(value) == 2:
            return f"{value[0]}x{value[1]}"
        return str(value)
    
    def inverse(self, value):
        """'1920x1080' -> (1920, 1080)"""
        if isinstance(value, str) and 'x' in value:
            parts = value.lower().split('x')
            if len(parts) == 2:
                try:
                    return (int(parts[0]), int(parts[1]))
                except ValueError:
                    pass
        return value

# 工厂函数，方便创建配置绑定器
def create_config_binder(ui_elements, config_type="user"):
    """
    创建配置绑定器
    
    Args:
        ui_elements: UI元素字典
        config_type: 配置类型
        
    Returns:
        ConfigBinder: 配置绑定器实例
    """
    return ConfigBinder(ui_elements, config_type)

# 用法示例
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
    
    app = QApplication(sys.argv)
    window = QMainWindow()
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # 创建一些UI元素
    resolution_combo = QComboBox()
    resolution_combo.addItems(["1920x1080", "1280x720", "720x480"])
    
    output_path = QLineEdit()
    output_path.setPlaceholderText("输出路径")
    
    # 添加UI元素到布局
    layout.addWidget(QLabel("分辨率:"))
    layout.addWidget(resolution_combo)
    layout.addWidget(QLabel("输出路径:"))
    layout.addWidget(output_path)
    
    # 创建UI元素字典
    ui_elements = {
        "resolution_dropdown": resolution_combo,
        "output_path": output_path
    }
    
    # 创建配置绑定器
    binder = create_config_binder(ui_elements, "export")
    
    # 绑定配置
    binder.bind("resolution", "resolution_dropdown", "1280x720")
    binder.bind("output_path", "output_path", "D:/output")
    
    # 更新UI
    binder.config_to_ui()
    
    window.setWindowTitle("配置绑定示例")
    window.resize(400, 200)
    window.show()
    
    sys.exit(app.exec()) 