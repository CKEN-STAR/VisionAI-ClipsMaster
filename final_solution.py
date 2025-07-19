#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 最终解决方案
完全从底层修复Qt字体渲染问题
"""
import sys
import os

# 设置控制台编码
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')
    import ctypes
    try:
        k32 = ctypes.windll.kernel32
        k32.SetConsoleCP(65001)
        k32.SetConsoleOutputCP(65001)
    except:
        pass

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "zh_CN.UTF-8"
os.environ["LC_ALL"] = "zh_CN.UTF-8"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"

# 保存原始stdout和stderr
original_stdout = sys.stdout
original_stderr = sys.stderr

# 导入字体引擎修复模块
try:
    # 先导入修复模块，它会在导入时设置Qt属性
    import font_engine_fix
except ImportError as e:
    print(f"警告: 无法导入字体引擎修复模块: {e}")

# 导入PyQt基础组件
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QListWidget, QLabel, QWidget,
    QComboBox, QPushButton, QRadioButton, QCheckBox
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

# 创建应用实例(必须在设置全局属性后创建)
app = QApplication(sys.argv)

# 应用字体修复
try:
    font_engine_fix.install_font_engine_patch()
    print("已应用字体引擎补丁")
except Exception as e:
    print(f"字体引擎补丁应用失败: {e}")

# 导入UI修补程序
try:
    import custom_ui_patch
    custom_ui_patch.apply_patches()
    print("已应用UI补丁")
except ImportError:
    print("无法导入UI补丁，将使用默认UI组件")

# =============== 核心功能：修复列表控件 ===============
def force_list_widget_patch():
    """强制修复列表控件的绘制"""
    try:
        # 保存原始方法
        original_paint = QListWidget.paintEvent
        
        # 自定义绘制方法
        def custom_paint(self, event):
            # 原始绘制
            original_paint(self, event)
            
            # 获取当前字体并确保是正确的
            font = self.font()
            if font.family() not in ["Microsoft YaHei", "Microsoft YaHei UI", "微软雅黑"]:
                # 如果字体不是理想字体，则重新设置
                best_font = QFont("Microsoft YaHei UI", 8)
                best_font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
                self.setFont(best_font)
                
                # 对每个项应用字体
                for i in range(self.count()):
                    item = self.item(i)
                    if item:
                        item.setFont(best_font)
        
        # 应用修改
        QListWidget.paintEvent = custom_paint
        print("已应用列表控件强制修复")
        return True
    except Exception as e:
        print(f"应用列表控件修复失败: {e}")
        return False

# 强制应用修复
force_list_widget_patch()

# =============== 核心功能：动态修复组件 ===============
def patch_widget_properties(widget):
    """递归修复所有子控件的属性"""
    
    # 对不同类型的控件应用特定修复
    if isinstance(widget, QListWidget):
        # 修复列表控件
        font = QFont("Microsoft YaHei UI", 8)
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        widget.setFont(font)
        
        # 设置特殊样式
        widget.setStyleSheet("""
        QListWidget {
            font-family: "Microsoft YaHei UI", "微软雅黑";
            font-size: 8px;
            line-height: 100%;
            padding: 1px;
        }
        QListWidget::item {
            padding: 1px 2px;
            margin: 0px;
            min-height: 12px;
        }
        """)
        
        # 项目级别修复
        for i in range(widget.count()):
            item = widget.item(i)
            if item:
                item.setFont(font)
                
        # 设置显示参数
        widget.setWordWrap(False)  # 禁用文本换行
    
    elif isinstance(widget, QLabel):
        # 修复标签控件
        font = QFont("Microsoft YaHei UI", 8)
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        widget.setFont(font)
        widget.setTextFormat(Qt.PlainText)  # 使用纯文本格式
        widget.setWordWrap(False)  # 禁用文本换行
    
    elif isinstance(widget, QPushButton):
        # 修复按钮控件
        font = QFont("Microsoft YaHei UI", 8)
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        widget.setFont(font)
    
    elif isinstance(widget, QCheckBox) or isinstance(widget, QRadioButton):
        # 修复复选框和单选按钮
        font = QFont("Microsoft YaHei UI", 8)
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        widget.setFont(font)
    
    # 递归处理所有子控件
    for child in widget.findChildren(QWidget):
        patch_widget_properties(child)

try:
    # 重置stdout/stderr以避免冲突
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    
    print("正在导入simple_ui模块...")
    import simple_ui
    print("成功导入simple_ui模块")
    
    # 创建主窗口
    print("正在创建主窗口...")
    main_window = simple_ui.SimpleScreenplayApp()
    
    # 修复主窗口及其所有子控件
    patch_widget_properties(main_window)
    print("已修复所有UI组件")
    
    # 设置强制应用样式表
    main_window.setStyleSheet("""
    * {
        font-family: "Microsoft YaHei UI", "微软雅黑";
        font-size: 8px;
    }
    QLabel {
        color: #000000;
        padding: 1px;
        margin: 0px;
    }
    QListWidget, QListView {
        font-family: "Microsoft YaHei UI", "微软雅黑";
        font-size: 8px;
        line-height: 100%;
        padding: 1px;
    }
    QListWidget::item, QListView::item {
        padding: 1px;
        margin: 0px;
        min-height: 12px;
    }
    """)
    
    # 显示窗口
    main_window.show()
    
    # 运行应用
    print("启动应用...")
    sys.exit(app.exec_())
    
except Exception as e:
    # 恢复标准输出
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    
    # 显示错误
    from PyQt5.QtWidgets import QMessageBox
    error_msg = f"启动失败: {str(e)}"
    print(error_msg)
    QMessageBox.critical(None, "错误", error_msg)
    raise 