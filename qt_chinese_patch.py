# -*- coding: utf-8 -*-
"""
PyQt5中文字体渲染补丁 - 简化版
此模块修复PyQt5中文字符显示问题，防止文本堆叠和乱码
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase

def get_suitable_chinese_font():
    """获取系统中可用的中文字体"""
    fontdb = QFontDatabase()
    families = fontdb.families()
    
    # 中文字体优先级
    priority_fonts = [
        "Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑",
        "SimHei", "黑体", "SimSun", "宋体", "NSimSun", "新宋体",
        "PingFang SC", "WenQuanYi Micro Hei", "Source Han Sans CN", "Noto Sans CJK SC"
    ]
    
    # 查找匹配的字体
    for name in priority_fonts:
        for family in families:
            if name in family:
                print(f"使用中文字体: {family}")
                return family
    
    print("警告: 未找到中文字体，使用默认字体")
    return "Microsoft YaHei UI"

# 获取合适的中文字体
chinese_font_name = get_suitable_chinese_font()

# 为应用设置默认字体
def apply_chinese_font():
    """应用中文字体到全局"""
    app = QApplication.instance()
    if app:
        # 设置字体
        font = QFont(chinese_font_name, 9)
        font.setHintingPreference(QFont.PreferFullHinting)
        app.setFont(font)
        
        # 应用全局样式表，针对中文显示进行优化
        app.setStyleSheet(f"""
            * {{
                font-family: '{chinese_font_name}';
            }}
            QLabel {{
                margin: 2px;
                padding: 2px;
                min-height: 18px;
            }}
            QGroupBox {{
                margin-top: 15px;
                padding-top: 15px;
            }}
            QPushButton {{
                padding: 4px 8px;
                min-height: 24px;
            }}
            QProgressBar {{
                text-align: center;
                min-height: 22px;
                border: 1px solid #aaa;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: #2196F3;
            }}
            QRadioButton, QCheckBox {{
                min-height: 22px;
                padding: 2px;
            }}
            QTextEdit, QListWidget {{
                padding: 2px;
                border: 1px solid #aaa;
            }}
        """)
        
        print(f"已应用简化版中文字体补丁: {chinese_font_name}")
    else:
        print("警告: 无法应用中文字体，QApplication实例未找到")

# 自动应用字体
apply_chinese_font()
