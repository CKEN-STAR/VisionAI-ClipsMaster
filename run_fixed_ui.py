#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 启动器
安全启动UI，确保中文显示正常
"""
import sys
import os
import traceback

# 设置关键环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "zh_CN.UTF-8"
os.environ["LC_ALL"] = "zh_CN.UTF-8"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"
# 彻底禁用所有GPU和CUDA功能
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:32"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 屏蔽TensorFlow警告

try:
    # 尝试导入PyQt5
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtGui import QFont
    
    # 创建对话框函数
    def show_error(title, message):
        """显示错误对话框"""
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
    
    # 开始主程序
    print("正在启动程序...")
    
    try:
        import fixed_direct_ui
        fixed_direct_ui.main()
    except Exception as e:
        error_detail = traceback.format_exc()
        error_message = f"启动失败: {str(e)}\n\n详细错误信息:\n{error_detail}"
        print(error_message)
        
        # 写入错误日志
        with open("启动错误.log", "w", encoding="utf-8") as f:
            f.write(error_message)
        
        # 显示错误信息
        show_error("启动错误", error_message)
        sys.exit(1)
    
except ImportError as e:
    print(f"导入PyQt5失败: {e}")
    print("请确保已安装PyQt5库")
    
    # 写入错误日志
    with open("导入错误.log", "w", encoding="utf-8") as f:
        f.write(f"导入PyQt5失败: {e}\n\n{traceback.format_exc()}")
    
    sys.exit(1)
except Exception as e:
    print(f"未知错误: {e}")
    
    # 写入错误日志
    with open("未知错误.log", "w", encoding="utf-8") as f:
        f.write(f"未知错误: {e}\n\n{traceback.format_exc()}")
    
    sys.exit(1) 