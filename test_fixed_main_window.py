#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的主窗口
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_fixed_main_window():
    """测试修复后的主窗口"""
    print("=" * 60)
    print("测试修复后的主窗口")
    print("=" * 60)
    
    try:
        # 清除模块缓存
        modules_to_clear = [name for name in sys.modules.keys() if 'main_window' in name]
        for module in modules_to_clear:
            del sys.modules[module]
        
        print("1. 导入修复后的主窗口模块...")
        from src.ui.main_window import MainWindow, PYQT_AVAILABLE
        print(f"✅ 主窗口模块导入成功")
        print(f"   PYQT_AVAILABLE = {PYQT_AVAILABLE}")
        
        if not PYQT_AVAILABLE:
            print("❌ PyQt6仍然不可用")
            return False
        
        print("2. 创建QApplication...")
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        print("✅ QApplication创建成功")
        
        print("3. 实例化MainWindow...")
        window = MainWindow()
        print("✅ MainWindow实例化成功")
        print(f"   窗口类型: {type(window)}")
        
        print("4. 测试窗口属性...")
        window.setWindowTitle("测试窗口")
        window.resize(800, 600)
        print("✅ 窗口属性设置成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 修复后主窗口测试工具")
    
    success = test_fixed_main_window()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 修复后的主窗口测试成功")
    else:
        print("❌ 修复后的主窗口测试失败")
    print("=" * 60)
