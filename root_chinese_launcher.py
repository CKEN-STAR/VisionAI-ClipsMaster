#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 核心中文启动器
最底层解决中文显示问题
"""
import sys
import os
import traceback

# 创建应用前初始化中文UI环境
from chinese_ui_engine import initialize_chinese_ui
initialize_chinese_ui()

# 保存原始stdout和stderr
original_stdout = sys.stdout
original_stderr = sys.stderr

# 导入PyQt5
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

def show_error(title, message):
    """显示错误对话框"""
    app = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.critical(None, title, message)
    sys.exit(1)

try:
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 显示启动画面
    splash = None
    try:
        if os.path.exists("resources/splash.png"):
            splash_pixmap = QPixmap("resources/splash.png")
            splash = QSplashScreen(splash_pixmap)
            splash.show()
            splash.showMessage("正在加载中文UI引擎...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
            app.processEvents()
    except Exception as e:
        print(f"加载启动画面失败: {e}")
    
    # 应用底层渲染补丁
    if splash:
        splash.showMessage("正在应用底层渲染补丁...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()
    
    import render_patch
    render_patch.install_render_patches()
    
    # 使用中文UI引擎设置应用
    from chinese_ui_engine import setup_chinese_application
    setup_chinese_application(app)
    
    if splash:
        splash.showMessage("正在应用SimpleUI补丁...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()
    
    # 初始化SimpleUI补丁
    import simple_ui_patch
    simple_ui_patch.init_patches()
    
    if splash:
        splash.showMessage("正在初始化程序...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()
    
    # 导入主程序模块
    import simple_ui
    
    # 创建主窗口
    main_window = simple_ui.SimpleScreenplayApp()
    
    # 使用SimpleUI补丁增强窗口
    simple_ui_patch.patch_window(main_window)
    
    # 使用中文UI引擎再次增强窗口
    from chinese_ui_engine import enhance_window
    enhance_window(main_window)
    
    # 关闭启动画面
    if splash:
        splash.finish(main_window)
    
    # 应用特殊列表修复
    from PyQt5.QtWidgets import QListWidget
    for list_widget in main_window.findChildren(QListWidget):
        list_font = QApplication.font()
        list_font.setPointSize(9)  # 减小字体，避免重叠
        list_widget.setFont(list_font)
        list_widget.setWordWrap(False)  # 禁用文本换行
        list_widget.setSpacing(0)  # 设置更紧凑的间距
        
        # 对每个项设置字体
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                item.setFont(list_font)
    
    # 显示主窗口
    main_window.show()
    
    # 运行应用
    sys.exit(app.exec_())

except ImportError as e:
    # 恢复标准输出
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    
    error_message = f"导入错误: {str(e)}\n\n可能是依赖库缺失，请确保已安装所有必要的库。"
    show_error("导入错误", error_message)

except Exception as e:
    # 恢复标准输出
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    
    # 获取详细错误信息
    error_details = traceback.format_exc()
    error_message = f"启动失败: {str(e)}\n\n详细错误信息:\n{error_details}"
    
    # 记录到日志
    try:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(error_message)
    except:
        pass
    
    show_error("启动错误", error_message) 