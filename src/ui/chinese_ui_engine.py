#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 中文UI引擎
全面解决PyQt5中文字体渲染问题
"""
import sys
import os
import ctypes
import platform
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QListWidget, 
    QListWidgetItem, QListView, QComboBox, QMainWindow
)
from PyQt5.QtGui import (
    QFont, QPainter, QPen, QColor, QFontMetrics, 
    QFontDatabase, QPalette, QPixmap, QImage
)
from PyQt5.QtCore import Qt, QRect, QSize, QEvent, QObject

# ========== 系统环境配置 ==========
def configure_system_env():
    """配置系统环境，确保正确编码设置"""
    # 设置环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["LANG"] = "zh_CN.UTF-8"
    os.environ["LC_ALL"] = "zh_CN.UTF-8"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_FONT_DPI"] = "96"
    
    # Windows特殊处理
    if sys.platform.startswith('win'):
        # 设置控制台代码页
        os.system('chcp 65001 > nul')
        # 使用Windows API设置控制台编码
        try:
            k32 = ctypes.windll.kernel32
            k32.SetConsoleCP(65001)
            k32.SetConsoleOutputCP(65001)
        except Exception as e:
            print(f"设置控制台编码失败: {e}")

# ========== 字体管理 ==========
class FontManager:
    """字体管理器，处理系统字体和字体回退机制"""
    
    # 中文字体优先级列表
    CHINESE_FONTS = [
        "Microsoft YaHei UI", "Microsoft YaHei", 
        "微软雅黑", "微软雅黑 UI", 
        "SimHei", "黑体", 
        "PingFang SC", "苹方-简",
        "WenQuanYi Micro Hei", "文泉驿微米黑",
        "Noto Sans CJK SC", "Noto Sans SC", 
        "Source Han Sans CN", "思源黑体",
        "FangSong", "仿宋", 
        "KaiTi", "楷体",
        "STHeiti", "华文黑体", 
        "STFangsong", "华文仿宋",
        "STKaiti", "华文楷体", 
        "STSong", "华文宋体",
        "SimSun", "宋体", 
        "NSimSun", "新宋体"
    ]
    
    # 不同用途的字体配置
    FONT_CONFIGS = {
        "default": {"size": 9, "weight": QFont.Normal, "strategy": QFont.PreferAntialias},
        "list": {"size": 9, "weight": QFont.Normal, "strategy": QFont.PreferAntialias},
        "title": {"size": 12, "weight": QFont.Bold, "strategy": QFont.PreferAntialias},
        "button": {"size": 9, "weight": QFont.Normal, "strategy": QFont.PreferAntialias},
        "label": {"size": 9, "weight": QFont.Normal, "strategy": QFont.PreferAntialias}
    }
    
    @classmethod
    def ensure_font_installed(cls):
        """确保必要字体已安装"""
        # 检查系统字体库
        fontdb = QFontDatabase()
        available_fonts = fontdb.families()
        
        # 检查是否有至少一个中文字体
        for font in cls.CHINESE_FONTS:
            if font in available_fonts:
                print(f"找到可用中文字体: {font}")
                return True
        
        # 如果没有找到中文字体，打印警告
        print("警告: 系统中没有找到可用的中文字体")
        return False
    
    @classmethod
    def get_best_chinese_font(cls, purpose="default"):
        """获取最佳中文字体"""
        fontdb = QFontDatabase()
        available_fonts = fontdb.families()
        
        # 根据字体优先级查找
        for font in cls.CHINESE_FONTS:
            if font in available_fonts:
                # 创建字体对象
                config = cls.FONT_CONFIGS.get(purpose, cls.FONT_CONFIGS["default"])
                font_obj = QFont(font, config["size"])
                font_obj.setWeight(config["weight"])
                font_obj.setStyleStrategy(config["strategy"])
                # 设置额外属性
                font_obj.setHintingPreference(QFont.PreferFullHinting)
                if hasattr(font_obj, 'setLetterSpacing'):
                    font_obj.setLetterSpacing(QFont.PercentageSpacing, 100)
                return font_obj
        
        # 找不到中文字体时的后备方案
        print("警告: 使用默认字体")
        default_font = QFont("Arial", 9)
        default_font.setStyleStrategy(QFont.PreferAntialias)
        return default_font
    
    @classmethod
    def set_application_fonts(cls, app):
        """设置应用程序级字体"""
        if not app or not isinstance(app, QApplication):
            print("错误: 无效的应用程序实例")
            return False
        
        # 确保字体已安装
        cls.ensure_font_installed()
        
        # 设置应用默认字体
        default_font = cls.get_best_chinese_font("default")
        app.setFont(default_font)
        
        return True


# ========== UI渲染增强 ==========
class UiEnhancer:
    """UI增强器，提供更好的中文显示"""
    
    @staticmethod
    def setup_global_style(app):
        """设置全局样式表"""
        if not app:
            return False
        
        # 获取最佳字体
        font_name = FontManager.get_best_chinese_font().family()
        
        # 应用全局样式表
        app.setStyleSheet(f"""
        * {{
            font-family: "{font_name}";
            font-size: 9px;
        }}
        
        QListWidget, QListView {{
            font-family: "{font_name}";
            font-size: 9px;
            padding: 1px;
            line-height: 100%;
        }}
        
        QListWidget::item, QListView::item {{
            padding: 1px 2px;
            margin: 0px;
            min-height: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        QLabel {{
            font-family: "{font_name}";
            font-size: 9px;
            padding: 1px;
            color: black;
            background: transparent;
        }}
        
        QPushButton {{
            font-family: "{font_name}";
            font-size: 9px;
            padding: 2px 8px;
        }}
        
        QComboBox {{
            font-family: "{font_name}";
            font-size: 9px;
            padding: 1px 6px;
        }}
        
        QGroupBox {{
            font-family: "{font_name}";
            font-size: 10px;
            font-weight: bold;
            margin-top: 6px;
            padding-top: 10px;
        }}
        """)
        
        return True
    
    @staticmethod
    def enhance_list_widget(list_widget):
        """增强列表控件显示"""
        if not isinstance(list_widget, QListWidget):
            return
        
        # 设置字体
        list_font = FontManager.get_best_chinese_font("list")
        list_widget.setFont(list_font)
        
        # 优化显示参数
        list_widget.setSpacing(0)  # 设置项间距
        list_widget.setWordWrap(False)  # 禁用自动换行
        list_widget.setTextElideMode(Qt.ElideRight)  # 文本省略模式
        
        # 为每个项设置字体
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                item.setFont(list_font)
    
    @staticmethod
    def enhance_widget_recursively(widget):
        """递归增强所有子控件"""
        if not widget:
            return
        
        # 处理特定类型的控件
        if isinstance(widget, QListWidget):
            UiEnhancer.enhance_list_widget(widget)
        elif isinstance(widget, QLabel):
            label_font = FontManager.get_best_chinese_font("label")
            widget.setFont(label_font)
            widget.setTextFormat(Qt.PlainText)  # 使用纯文本格式
        elif isinstance(widget, QPushButton):
            button_font = FontManager.get_best_chinese_font("button")
            widget.setFont(button_font)
        
        # 递归处理所有子控件
        for child in widget.findChildren(QWidget):
            UiEnhancer.enhance_widget_recursively(child)


# ========== 事件过滤器，用于动态修复 ==========
class ChineseRenderEventFilter(QObject):
    """中文渲染事件过滤器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = FontManager.get_best_chinese_font()
    
    def eventFilter(self, watched, event):
        """事件过滤器，处理绘制事件"""
        # 对于列表控件，在绘制前应用字体
        if isinstance(watched, QListWidget) and event.type() == QEvent.Paint:
            # 确保字体正确
            if watched.font().family() != self.font.family():
                watched.setFont(self.font)
                
                # 更新每个项的字体
                for i in range(watched.count()):
                    item = watched.item(i)
                    if item and item.font().family() != self.font.family():
                        item.setFont(self.font)
        
        # 对于标签控件，在绘制前应用字体
        elif isinstance(watched, QLabel) and event.type() == QEvent.Paint:
            if watched.font().family() != self.font.family():
                watched.setFont(self.font)
        
        # 继续正常事件处理
        return super().eventFilter(watched, event)


# ========== 主要接口函数 ==========
def initialize_chinese_ui():
    """初始化中文UI环境，必须在QApplication创建前调用"""
    # 配置系统环境
    configure_system_env()
    
    # 设置Qt属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    print("中文UI环境已初始化")
    return True

def setup_chinese_application(app):
    """设置中文应用程序，必须在QApplication创建后调用"""
    if not app or not isinstance(app, QApplication):
        print("错误: 无效的应用程序实例")
        return False
    
    # 设置字体
    FontManager.set_application_fonts(app)
    
    # 设置全局样式
    UiEnhancer.setup_global_style(app)
    
    # 创建并安装事件过滤器
    event_filter = ChineseRenderEventFilter()
    app.installEventFilter(event_filter)
    
    print("中文应用程序设置完成")
    return True

def enhance_window(window):
    """增强窗口，修复所有子控件"""
    if not window:
        print("错误: 无效的窗口实例")
        return False
    
    # 递归增强所有控件
    UiEnhancer.enhance_widget_recursively(window)
    
    print("窗口增强完成")
    return True


# ========== 如果直接运行，执行测试 ==========
if __name__ == "__main__":
    # 初始化中文UI环境
    initialize_chinese_ui()
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置中文应用程序
    setup_chinese_application(app)
    
    # 测试窗口
    test_window = QMainWindow()
    test_window.setWindowTitle("中文UI测试窗口")
    test_window.resize(600, 400)
    
    # 添加一些控件
    central_widget = QWidget()
    test_window.setCentralWidget(central_widget)
    
    # 布局
    from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
    layout = QVBoxLayout(central_widget)
    
    # 标签
    label = QLabel("这是中文标签测试")
    layout.addWidget(label)
    
    # 按钮
    button = QPushButton("中文按钮测试")
    layout.addWidget(button)
    
    # 列表
    list_widget = QListWidget()
    list_widget.addItems([
        "中文列表项测试1",
        "中文列表项测试2",
        "中文列表项测试3",
        "这是一个很长的中文文本项，用于测试文本省略和换行功能"
    ])
    layout.addWidget(list_widget)
    
    # 增强窗口
    enhance_window(test_window)
    
    # 显示窗口
    test_window.show()
    
    # 执行应用
    sys.exit(app.exec_()) 