#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文本方向适配演示

此脚本演示了如何在UI中应用文本方向适配，支持RTL语言（阿拉伯语、希伯来语和波斯语）
"""

import sys
import os
from pathlib import Path
import logging

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                           QComboBox, QGroupBox, QRadioButton, QFrame)
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

# 导入文本方向适配模块
try:
    from ui.utils.text_direction import LayoutDirection, set_application_layout_direction, apply_rtl_styles
except ImportError:
    # 如果无法从标准路径导入，尝试从当前目录导入
    sys.path.append(os.path.join(PROJECT_ROOT, "ui", "utils"))
    try:
        from text_direction import LayoutDirection, set_application_layout_direction, apply_rtl_styles
    except ImportError:
        print("错误：无法导入文本方向适配模块，请确保文件存在于正确位置")
        sys.exit(1)

class TextDirectionDemo(QMainWindow):
    """文本方向适配演示应用"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster 文本方向适配演示")
        self.resize(800, 600)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 初始化UI
        self.init_ui()
        
        # 默认设置为中文
        self.current_language = "zh"
        self.update_language("zh")
    
    def init_ui(self):
        """初始化UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 标题标签
        title_label = QLabel("VisionAI-ClipsMaster 文本方向适配")
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
        language_label = QLabel("选择界面语言：")
        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("العربية (阿拉伯语)", "ar")
        self.language_combo.addItem("עברית (希伯来语)", "he")
        self.language_combo.addItem("فارسی (波斯语)", "fa")
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        language_row.addWidget(language_label)
        language_row.addWidget(self.language_combo)
        language_row.addStretch(1)
        language_layout.addLayout(language_row)
        
        # 方向说明标签
        direction_label = QLabel("当前文本方向：从左到右 (LTR)")
        direction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.direction_label = direction_label
        language_layout.addWidget(direction_label)
        
        main_layout.addWidget(language_group)
        
        # 演示内容区域
        demo_group = QGroupBox("界面元素演示")
        demo_layout = QVBoxLayout(demo_group)
        
        # 文本输入
        text_label = QLabel("内容输入：")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此输入文本内容...")
        demo_layout.addWidget(text_label)
        demo_layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        self.apply_button = QPushButton("应用")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        demo_layout.addLayout(button_layout)
        
        # 选项演示
        options_layout = QHBoxLayout()
        self.option1 = QRadioButton("选项一")
        self.option2 = QRadioButton("选项二")
        self.option3 = QRadioButton("选项三")
        options_layout.addWidget(self.option1)
        options_layout.addWidget(self.option2)
        options_layout.addWidget(self.option3)
        demo_layout.addLayout(options_layout)
        
        main_layout.addWidget(demo_group)
        
        # 说明区域
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setFrameShadow(QFrame.Shadow.Raised)
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("说明")
        info_title.setFont(QFont("", 12, QFont.Weight.Bold))
        info_content = QLabel(
            "本演示展示了VisionAI-ClipsMaster中的文本方向适配功能。\n"
            "当选择阿拉伯语、希伯来语或波斯语等RTL语言时，界面会自动调整为从右到左布局。\n"
            "这确保了在多语言环境下，用户界面始终保持良好的可用性和一致性。"
        )
        info_content.setWordWrap(True)
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_content)
        
        main_layout.addWidget(info_frame)
        
        # 状态栏
        self.statusBar().showMessage("准备就绪")
        
        # 保存需要更新文本的组件引用
        self.ui_texts = {
            "title": title_label,
            "language_group": language_group,
            "language_label": language_label,
            "demo_group": demo_group,
            "text_label": text_label,
            "save_button": self.save_button,
            "cancel_button": self.cancel_button,
            "apply_button": self.apply_button,
            "option1": self.option1,
            "option2": self.option2,
            "option3": self.option3,
            "info_title": info_title,
            "info_content": info_content
        }
    
    def on_language_changed(self, index):
        """语言选择变更处理
        
        Args:
            index: 下拉框索引
        """
        # 获取选中的语言代码
        lang_code = self.language_combo.currentData()
        self.update_language(lang_code)
    
    def update_language(self, lang_code):
        """更新界面语言和方向
        
        Args:
            lang_code: 语言代码
        """
        # 保存当前语言
        self.current_language = lang_code
        
        # 调用布局方向适配
        set_application_layout_direction(lang_code)
        
        # 应用RTL样式
        apply_rtl_styles(self.central_widget, lang_code)
        
        # 更新文本内容
        self.update_ui_texts(lang_code)
        
        # 更新方向标签
        is_rtl = LayoutDirection.is_rtl_language(lang_code)
        if is_rtl:
            self.direction_label.setText("当前文本方向：从右到左 (RTL)")
            self.statusBar().showMessage(f"已切换到{self.get_language_name(lang_code)}，使用RTL布局")
        else:
            self.direction_label.setText("当前文本方向：从左到右 (LTR)")
            self.statusBar().showMessage(f"已切换到{self.get_language_name(lang_code)}，使用LTR布局")
    
    def update_ui_texts(self, lang_code):
        """更新UI文本内容
        
        Args:
            lang_code: 语言代码
        """
        # 这里只是演示，实际应用中应该使用翻译系统
        texts = {
            "zh": {
                "title": "VisionAI-ClipsMaster 文本方向适配",
                "language_group": "语言选择",
                "language_label": "选择界面语言：",
                "demo_group": "界面元素演示",
                "text_label": "内容输入：",
                "save_button": "保存",
                "cancel_button": "取消",
                "apply_button": "应用",
                "option1": "选项一",
                "option2": "选项二",
                "option3": "选项三",
                "info_title": "说明",
                "info_content": "本演示展示了VisionAI-ClipsMaster中的文本方向适配功能。\n当选择阿拉伯语、希伯来语或波斯语等RTL语言时，界面会自动调整为从右到左布局。\n这确保了在多语言环境下，用户界面始终保持良好的可用性和一致性。"
            },
            "en": {
                "title": "VisionAI-ClipsMaster Text Direction Adaptation",
                "language_group": "Language Selection",
                "language_label": "Choose UI Language:",
                "demo_group": "UI Elements Demo",
                "text_label": "Content Input:",
                "save_button": "Save",
                "cancel_button": "Cancel",
                "apply_button": "Apply",
                "option1": "Option 1",
                "option2": "Option 2",
                "option3": "Option 3",
                "info_title": "Description",
                "info_content": "This demo showcases the text direction adaptation feature in VisionAI-ClipsMaster.\nWhen RTL languages like Arabic, Hebrew, or Persian are selected, the interface automatically adjusts to a right-to-left layout.\nThis ensures that the user interface maintains good usability and consistency in multilingual environments."
            },
            "ar": {
                "title": "تكيف اتجاه النص VisionAI-ClipsMaster",
                "language_group": "اختيار اللغة",
                "language_label": "اختر لغة واجهة المستخدم:",
                "demo_group": "عرض عناصر واجهة المستخدم",
                "text_label": "إدخال المحتوى:",
                "save_button": "حفظ",
                "cancel_button": "إلغاء",
                "apply_button": "تطبيق",
                "option1": "الخيار 1",
                "option2": "الخيار 2",
                "option3": "الخيار 3",
                "info_title": "وصف",
                "info_content": "يعرض هذا العرض التوضيحي ميزة تكيف اتجاه النص في VisionAI-ClipsMaster.\nعند تحديد لغات RTL مثل العربية أو العبرية أو الفارسية، تتكيف واجهة المستخدم تلقائيًا مع تخطيط من اليمين إلى اليسار.\nهذا يضمن أن واجهة المستخدم تحافظ على قابلية الاستخدام والاتساق في بيئات متعددة اللغات."
            },
            "he": {
                "title": "התאמת כיוון טקסט VisionAI-ClipsMaster",
                "language_group": "בחירת שפה",
                "language_label": "בחר שפת ממשק:",
                "demo_group": "הדגמת רכיבי ממשק",
                "text_label": "הזנת תוכן:",
                "save_button": "שמור",
                "cancel_button": "ביטול",
                "apply_button": "החל",
                "option1": "אפשרות 1",
                "option2": "אפשרות 2",
                "option3": "אפשרות 3",
                "info_title": "תיאור",
                "info_content": "הדגמה זו מציגה את תכונת התאמת כיוון הטקסט ב-VisionAI-ClipsMaster.\nכאשר נבחרות שפות RTL כמו ערבית, עברית או פרסית, הממשק מתאים באופן אוטומטי לפריסה מימין לשמאל.\nזה מבטיח שממשק המשתמש שומר על שימושיות ועקביות בסביבות רב-לשוניות."
            },
            "fa": {
                "title": "تطبیق جهت متن VisionAI-ClipsMaster",
                "language_group": "انتخاب زبان",
                "language_label": "انتخاب زبان رابط کاربری:",
                "demo_group": "نمایش عناصر رابط کاربری",
                "text_label": "ورودی محتوا:",
                "save_button": "ذخیره",
                "cancel_button": "لغو",
                "apply_button": "اعمال",
                "option1": "گزینه 1",
                "option2": "گزینه 2",
                "option3": "گزینه 3",
                "info_title": "توضیحات",
                "info_content": "این نسخه نمایشی ویژگی تطبیق جهت متن در VisionAI-ClipsMaster را نشان می دهد.\nهنگامی که زبان‌های RTL مانند عربی، عبری یا فارسی انتخاب می‌شوند، رابط کاربری به طور خودکار با چیدمان راست به چپ تنظیم می‌شود.\nاین اطمینان حاصل می‌کند که رابط کاربری در محیط‌های چند زبانه همیشه قابل استفاده و سازگار باقی می‌ماند."
            }
        }
        
        # 如果没有该语言的翻译，使用英文
        if lang_code not in texts:
            lang_code = "en"
        
        # 更新所有组件文本
        for key, widget in self.ui_texts.items():
            if key in texts[lang_code]:
                if key == "info_content":
                    widget.setText(texts[lang_code][key])
                else:
                    widget.setText(texts[lang_code][key])
    
    def get_language_name(self, lang_code):
        """获取语言名称
        
        Args:
            lang_code: 语言代码
            
        Returns:
            str: 语言名称
        """
        names = {
            "zh": "简体中文",
            "en": "English",
            "ar": "العربية (阿拉伯语)",
            "he": "עברית (希伯来语)",
            "fa": "فارسی (波斯语)"
        }
        return names.get(lang_code, lang_code)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = TextDirectionDemo()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 