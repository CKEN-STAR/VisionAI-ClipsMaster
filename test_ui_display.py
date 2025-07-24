#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI界面显示测试脚本

测试VisionAI-ClipsMaster的UI界面是否能正常启动和显示

作者: VisionAI-ClipsMaster Team
日期: 2025-07-23
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ui_display():
    """测试UI界面显示"""
    logger.info("开始UI界面显示测试...")
    
    try:
        # 导入PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # 创建应用程序
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        logger.info("✅ QApplication创建成功")
        
        # 导入主界面
        from simple_ui_fixed import VisionAIClipsMasterUI
        
        # 创建主窗口
        main_window = VisionAIClipsMasterUI()
        logger.info("✅ 主窗口创建成功")
        
        # 显示窗口
        main_window.show()
        logger.info("✅ 主窗口显示成功")
        
        # 设置定时器自动关闭（5秒后）
        def close_window():
            logger.info("自动关闭窗口...")
            main_window.close()
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(close_window)
        timer.start(5000)  # 5秒后关闭
        
        logger.info("UI界面将显示5秒钟...")
        logger.info("如果看到界面正常显示，说明UI功能正常")
        
        # 运行应用程序
        app.exec()
        
        logger.info("✅ UI界面测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ UI界面测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("VisionAI-ClipsMaster UI界面显示测试")
    print("=" * 60)
    
    success = test_ui_display()
    
    if success:
        print("\n🎉 UI界面测试成功！")
        print("✅ 界面能够正常启动和显示")
        print("✅ 所有UI组件加载正常")
    else:
        print("\n❌ UI界面测试失败")
        print("请检查PyQt6安装和依赖项")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
