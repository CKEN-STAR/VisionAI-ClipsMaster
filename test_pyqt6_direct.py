#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试PyQt6可用性
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_pyqt6_direct():
    """直接测试PyQt6"""
    print("=" * 50)
    print("直接测试PyQt6可用性")
    print("=" * 50)
    
    try:
        print("1. 测试PyQt6基础导入...")
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        print("✅ PyQt6基础组件导入成功")
        
        print("2. 测试QApplication创建...")
        app = QApplication.instance() or QApplication([])
        print("✅ QApplication创建成功")
        
        print("3. 测试窗口创建...")
        window = QWidget()
        window.setWindowTitle("PyQt6测试窗口")
        window.resize(300, 200)
        
        label = QLabel("PyQt6工作正常！", window)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.resize(300, 200)
        print("✅ 窗口和组件创建成功")
        
        print("4. 测试主窗口模块导入...")
        from src.ui.main_window import PYQT_AVAILABLE
        print(f"✅ 主窗口模块PYQT_AVAILABLE = {PYQT_AVAILABLE}")
        
        if PYQT_AVAILABLE:
            print("5. 测试主窗口类导入...")
            from src.ui.main_window import MainWindow
            print("✅ MainWindow类导入成功")
            
            print("6. 测试主窗口实例化...")
            main_window = MainWindow()
            print("✅ MainWindow实例化成功")
            print(f"   窗口类型: {type(main_window)}")
        else:
            print("❌ 主窗口模块检测到PyQt6不可用")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_conflicts():
    """测试导入冲突"""
    print("\n" + "=" * 50)
    print("检查导入冲突")
    print("=" * 50)
    
    print("当前sys.path:")
    for i, path in enumerate(sys.path[:10]):  # 只显示前10个
        print(f"  {i}: {path}")
    
    print("\n检查PyQt相关模块:")
    pyqt_modules = [name for name in sys.modules.keys() if 'qt' in name.lower()]
    for module in sorted(pyqt_modules):
        print(f"  {module}")
    
    print("\n检查项目模块:")
    project_modules = [name for name in sys.modules.keys() if 'visionai' in name.lower() or 'ui' in name]
    for module in sorted(project_modules):
        print(f"  {module}")

if __name__ == "__main__":
    print("🔧 PyQt6直接测试工具")
    
    # 测试PyQt6
    success = test_pyqt6_direct()
    
    # 检查导入冲突
    test_import_conflicts()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ PyQt6测试完成，功能正常")
    else:
        print("❌ PyQt6测试失败")
    print("=" * 50)
