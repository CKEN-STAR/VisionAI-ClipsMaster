#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 最终启动脚本
确保程序能够正常启动，避免进入安全模式
"""

import os
import sys
import time
from pathlib import Path

def setup_environment():
    """设置环境变量"""
    # 设置关键环境变量
    env_vars = {
        'CUDA_VISIBLE_DEVICES': '',
        'TORCH_USE_CUDA_DSA': '0',
        'NPY_DISABLE_SVML': '1',
        'KMP_DUPLICATE_LIB_OK': 'TRUE',
        'PYTHONPATH': str(Path(__file__).parent),
        'QT_AUTO_SCREEN_SCALE_FACTOR': '1',
        'QT_ENABLE_HIGHDPI_SCALING': '1'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # 禁用警告
    import warnings
    warnings.filterwarnings('ignore')

def main():
    """主函数"""
    import time
    start_time = time.time()

    # 初始化启动日志管理器
    from ui.utils.startup_logger import startup_logger
    startup_logger.suppress_qt_warnings()

    print("🎬 VisionAI-ClipsMaster - AI短剧混剪工具")
    print("=" * 60)

    # 设置环境
    startup_logger.set_phase("环境配置")
    setup_environment()
    startup_logger.success("环境配置完成")

    try:
        # 导入PyQt6
        startup_logger.set_phase("初始化应用框架")
        from PyQt6.QtWidgets import QApplication

        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        app.setStyle('Fusion')
        app.setApplicationName("VisionAI-ClipsMaster")
        app.setApplicationVersion("1.0.0")
        app.setQuitOnLastWindowClosed(True)
        startup_logger.success("应用框架初始化完成")

        # 导入并创建主窗口
        startup_logger.set_phase("创建主界面")
        from simple_ui_fixed import SimpleScreenplayApp
        window = SimpleScreenplayApp()
        startup_logger.success("主界面创建完成")

        # 显示窗口
        startup_logger.set_phase("显示界面")
        window.show()
        window.raise_()
        window.activateWindow()
        window.setWindowTitle("VisionAI-ClipsMaster - AI短剧混剪工具")

        # 启动完成
        total_time = time.time() - start_time
        startup_logger.startup_summary(total_time)

        # 运行应用
        return app.exec()

    except ImportError as e:
        startup_logger.error(f"模块导入失败: {e}")
        print("\n🔧 请检查以下依赖是否已安装:")
        print("  pip install PyQt6 torch numpy opencv-python Pillow requests psutil")
        print("\n或运行诊断工具:")
        print("  python diagnose_startup_failure.py")
        return 1

    except Exception as e:
        startup_logger.error(f"启动失败: {e}")
        print("\n🔧 请尝试:")
        print("1. 重启计算机")
        print("2. 运行诊断工具: python diagnose_startup_failure.py")
        print("3. 使用修复版启动器: python start_visionai_fixed.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
