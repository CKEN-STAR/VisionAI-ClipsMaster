#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 本地化格式化器演示

演示本地化格式化功能，包括日期、数字、货币等在多语言环境下的格式化
"""

import sys
import os
from pathlib import Path
import datetime
import logging

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                           QComboBox, QGroupBox, QRadioButton, QFrame, QGridLayout,
                           QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# 设置项目根目录并添加到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 导入本地化格式化器模块
try:
    from ui.i18n.localization import (
        format_date, format_time, format_datetime, 
        format_number, format_currency, format_percentage,
        format_file_size, LocalizationFormatter
    )
except ImportError:
    # 如果无法从标准路径导入，尝试从当前目录导入
    sys.path.append(os.path.join(PROJECT_ROOT, "ui", "i18n"))
    try:
        from localization import (
            format_date, format_time, format_datetime, 
            format_number, format_currency, format_percentage,
            format_file_size, LocalizationFormatter
        )
    except ImportError:
        print("错误：无法导入本地化格式化器模块，请确保文件存在于正确位置")
        sys.exit(1)

class LocalizationDemo(QMainWindow):
    """本地化格式化器演示应用"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster 本地化格式化器演示")
        self.resize(800, 800)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 初始化UI
        self.init_ui()
        
        # 默认设置为中文
        self.current_language = "zh_CN"
        self.update_samples()
    
    def init_ui(self):
        """初始化UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 标题标签
        title_label = QLabel("VisionAI-ClipsMaster 本地化格式化器演示")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 语言选择部分
        language_group = QGroupBox("语言选择")
        language_layout = QVBoxLayout(language_group)
        
        # 语言切换下拉框
        language_row = QHBoxLayout()
        language_label = QLabel("选择语言：")
        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("繁体中文", "zh_TW")
        self.language_combo.addItem("English (US)", "en_US")
        self.language_combo.addItem("English (UK)", "en_GB")
        self.language_combo.addItem("Français", "fr")
        self.language_combo.addItem("Deutsch", "de")
        self.language_combo.addItem("Español", "es")
        self.language_combo.addItem("日本語", "ja")
        self.language_combo.addItem("한국어", "ko")
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.addItem("العربية", "ar")
        self.language_combo.addItem("עברית", "he")
        self.language_combo.addItem("فارسی", "fa")
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        language_row.addWidget(language_label)
        language_row.addWidget(self.language_combo)
        language_row.addStretch(1)
        language_layout.addLayout(language_row)
        
        main_layout.addWidget(language_group)
        
        # 数字格式化示例
        number_group = QGroupBox("数字格式化")
        number_layout = QGridLayout(number_group)
        
        # 输入数字
        input_number_label = QLabel("输入数字：")
        self.input_number = QDoubleSpinBox()
        self.input_number.setRange(-1000000, 1000000)
        self.input_number.setValue(1234.56)
        self.input_number.setDecimals(4)
        self.input_number.valueChanged.connect(self.update_samples)
        
        # 格式化结果
        number_result_label = QLabel("格式化结果：")
        self.number_result = QLabel()
        self.number_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        number_layout.addWidget(input_number_label, 0, 0)
        number_layout.addWidget(self.input_number, 0, 1)
        number_layout.addWidget(number_result_label, 1, 0)
        number_layout.addWidget(self.number_result, 1, 1)
        
        main_layout.addWidget(number_group)
        
        # 货币格式化示例
        currency_group = QGroupBox("货币格式化")
        currency_layout = QGridLayout(currency_group)
        
        # 输入金额
        input_amount_label = QLabel("输入金额：")
        self.input_amount = QDoubleSpinBox()
        self.input_amount.setRange(0, 1000000)
        self.input_amount.setValue(1234.56)
        self.input_amount.setDecimals(2)
        self.input_amount.valueChanged.connect(self.update_samples)
        
        # 货币选择
        currency_select_label = QLabel("货币：")
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("自动 (根据语言)", "auto")
        self.currency_combo.addItem("人民币 (CNY)", "CNY")
        self.currency_combo.addItem("美元 (USD)", "USD")
        self.currency_combo.addItem("欧元 (EUR)", "EUR")
        self.currency_combo.addItem("英镑 (GBP)", "GBP")
        self.currency_combo.addItem("日元 (JPY)", "JPY")
        self.currency_combo.addItem("韩元 (KRW)", "KRW")
        self.currency_combo.currentIndexChanged.connect(self.update_samples)
        
        # 格式化结果
        currency_result_label = QLabel("格式化结果：")
        self.currency_result = QLabel()
        self.currency_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        currency_layout.addWidget(input_amount_label, 0, 0)
        currency_layout.addWidget(self.input_amount, 0, 1)
        currency_layout.addWidget(currency_select_label, 1, 0)
        currency_layout.addWidget(self.currency_combo, 1, 1)
        currency_layout.addWidget(currency_result_label, 2, 0)
        currency_layout.addWidget(self.currency_result, 2, 1)
        
        main_layout.addWidget(currency_group)
        
        # 日期时间格式化示例
        datetime_group = QGroupBox("日期时间格式化")
        datetime_layout = QGridLayout(datetime_group)
        
        # 使用当前时间
        now = datetime.datetime.now()
        
        # 日期格式
        date_label = QLabel("日期格式：")
        self.date_result = QLabel()
        self.date_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        # 时间格式
        time_label = QLabel("时间格式：")
        self.time_result = QLabel()
        self.time_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        # 日期时间格式
        datetime_label = QLabel("日期时间格式：")
        self.datetime_result = QLabel()
        self.datetime_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        datetime_layout.addWidget(date_label, 0, 0)
        datetime_layout.addWidget(self.date_result, 0, 1)
        datetime_layout.addWidget(time_label, 1, 0)
        datetime_layout.addWidget(self.time_result, 1, 1)
        datetime_layout.addWidget(datetime_label, 2, 0)
        datetime_layout.addWidget(self.datetime_result, 2, 1)
        
        main_layout.addWidget(datetime_group)
        
        # 其他格式化示例
        other_group = QGroupBox("其他格式化")
        other_layout = QGridLayout(other_group)
        
        # 百分比格式
        percentage_label = QLabel("百分比格式：")
        self.percentage_result = QLabel()
        self.percentage_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        # 文件大小格式
        filesize_label = QLabel("文件大小格式：")
        self.filesize_result = QLabel()
        self.filesize_result.setStyleSheet("font-weight: bold; color: #3366cc;")
        
        # 输入百分比值
        input_percentage_label = QLabel("输入百分比值 (0.xx)：")
        self.input_percentage = QDoubleSpinBox()
        self.input_percentage.setRange(0, 1)
        self.input_percentage.setValue(0.2356)
        self.input_percentage.setSingleStep(0.01)
        self.input_percentage.setDecimals(4)
        self.input_percentage.valueChanged.connect(self.update_samples)
        
        # 输入文件大小
        input_filesize_label = QLabel("输入文件大小 (字节)：")
        self.input_filesize = QSpinBox()
        self.input_filesize.setRange(0, 1000000000)
        self.input_filesize.setValue(15728640)  # 15MB
        self.input_filesize.setSingleStep(1024)
        self.input_filesize.valueChanged.connect(self.update_samples)
        
        other_layout.addWidget(input_percentage_label, 0, 0)
        other_layout.addWidget(self.input_percentage, 0, 1)
        other_layout.addWidget(percentage_label, 1, 0)
        other_layout.addWidget(self.percentage_result, 1, 1)
        other_layout.addWidget(input_filesize_label, 2, 0)
        other_layout.addWidget(self.input_filesize, 2, 1)
        other_layout.addWidget(filesize_label, 3, 0)
        other_layout.addWidget(self.filesize_result, 3, 1)
        
        main_layout.addWidget(other_group)
        
        # 说明区域
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setFrameShadow(QFrame.Shadow.Raised)
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("说明")
        info_title.setFont(QFont("", 12, QFont.Weight.Bold))
        info_content = QLabel(
            "本演示展示了VisionAI-ClipsMaster中的本地化格式化功能。\n"
            "可以切换不同语言，查看日期、数字、货币等在各种语言环境下的格式化效果。"
        )
        info_content.setWordWrap(True)
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_content)
        
        main_layout.addWidget(info_frame)
        
        # 状态栏
        self.statusBar().showMessage("准备就绪")
    
    def on_language_changed(self, index):
        """语言选择变更处理
        
        Args:
            index: 下拉框索引
        """
        # 获取选中的语言代码
        self.current_language = self.language_combo.currentData()
        self.update_samples()
        self.statusBar().showMessage(f"已切换到 {self.language_combo.currentText()} ({self.current_language})")
    
    def update_samples(self):
        """更新所有格式化示例"""
        # 获取当前输入值
        number_value = self.input_number.value()
        amount_value = self.input_amount.value()
        percentage_value = self.input_percentage.value()
        filesize_value = self.input_filesize.value()
        
        # 获取当前时间
        now = datetime.datetime.now()
        
        # 获取当前选择的货币
        currency_code = self.currency_combo.currentData()
        
        # 更新格式化结果
        self.number_result.setText(format_number(number_value, self.current_language))
        
        self.currency_result.setText(
            format_currency(amount_value, currency_code, self.current_language)
        )
        
        self.date_result.setText(format_date(now, self.current_language))
        self.time_result.setText(format_time(now, self.current_language))
        self.datetime_result.setText(format_datetime(now, self.current_language))
        
        self.percentage_result.setText(
            format_percentage(percentage_value, self.current_language)
        )
        
        self.filesize_result.setText(
            format_file_size(filesize_value, self.current_language)
        )

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = LocalizationDemo()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 