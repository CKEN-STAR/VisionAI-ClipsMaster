#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 修复版启动脚本
确保环境设置正确，避免进入安全模式
"""

import os
import sys
import time
from pathlib import Path

def setup_environment():
    """设置环境变量和路径"""
    print("🔧 设置环境变量...")
    
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
        print(f"  {key} = {value}")
    
    # 禁用警告
    import warnings
    warnings.filterwarnings('ignore')
    
    print("✅ 环境变量设置完成")

def check_dependencies():
    """检查关键依赖"""
    print("\n🔍 检查关键依赖...")
    
    critical_deps = [
        ("PyQt6", "PyQt6.QtWidgets"),
        ("NumPy", "numpy"),
        ("PyTorch", "torch"),
        ("OpenCV", "cv2"),
        ("PIL", "PIL"),
        ("Requests", "requests"),
        ("PSUtil", "psutil"),
    ]
    
    missing_deps = []
    
    for name, module in critical_deps:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - 缺失")
            missing_deps.append(name)
    
    if missing_deps:
        print(f"\n❌ 发现缺失依赖: {', '.join(missing_deps)}")
        print("请运行以下命令安装:")
        for dep in missing_deps:
            if dep == "PyQt6":
                print("  pip install PyQt6")
            elif dep == "PyTorch":
                print("  pip install torch --index-url https://download.pytorch.org/whl/cpu")
            elif dep == "OpenCV":
                print("  pip install opencv-python")
            else:
                print(f"  pip install {dep.lower()}")
        return False
    
    print("✅ 所有关键依赖都已安装")
    return True

def check_ui_modules():
    """检查UI模块"""
    print("\n🔍 检查UI模块...")
    
    try:
        # 添加项目路径
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # 检查关键UI模块
        from ui.config.environment import setup_environment as setup_ui_env
        setup_ui_env()
        print("  ✅ UI环境模块")
        
        from ui.hardware.memory_manager import UIMemoryManager
        print("  ✅ 内存管理器")
        
        from ui.hardware.performance_tier import PerformanceTierClassifier
        print("  ✅ 性能分级器")
        
        from src.ui.enhanced_style_manager import EnhancedStyleManager
        print("  ✅ 样式管理器")
        
        print("✅ UI模块检查完成")
        return True
        
    except Exception as e:
        print(f"❌ UI模块检查失败: {e}")
        return False

def create_safe_startup():
    """创建安全启动函数"""
    print("\n🚀 启动VisionAI-ClipsMaster...")
    
    try:
        # 导入PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        app.setStyle('Fusion')
        app.setApplicationName("VisionAI-ClipsMaster")
        app.setApplicationVersion("1.0.0")
        app.setQuitOnLastWindowClosed(True)
        
        print("✅ QApplication创建成功")
        
        # 导入主窗口类
        from simple_ui_fixed import SimpleScreenplayApp
        print("✅ 主窗口类导入成功")
        
        # 创建主窗口
        print("📱 正在创建主窗口...")
        window = SimpleScreenplayApp()
        print("✅ 主窗口创建成功")
        
        # 显示窗口
        window.show()
        window.raise_()
        window.activateWindow()
        print("✅ 窗口显示成功")
        
        # 设置窗口标题
        window.setWindowTitle("VisionAI-ClipsMaster - AI短剧混剪工具")
        
        print("\n" + "=" * 60)
        print("🎉 VisionAI-ClipsMaster 启动成功！")
        print("=" * 60)
        print("📱 主界面已显示")
        print("🎬 可以开始使用AI短剧混剪功能")
        print("💡 如需帮助，请查看'关于我们'标签页")
        print("=" * 60)
        
        # 运行应用
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("\n🔧 修复建议:")
        print("1. 检查Python环境是否正确")
        print("2. 确保所有依赖包已安装")
        print("3. 运行: python diagnose_startup_failure.py")
        return 1
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 尝试安全模式启动...")
        
        try:
            # 尝试安全模式
            from simple_ui_fixed import create_safe_mode_window
            safe_window = create_safe_mode_window()
            
            if safe_window:
                safe_window.show()
                print("✅ 安全模式启动成功")
                return app.exec()
            else:
                print("❌ 安全模式启动失败")
                return 1
                
        except Exception as safe_e:
            print(f"❌ 安全模式也失败了: {safe_e}")
            print("\n🆘 请联系技术支持或查看错误日志")
            return 1

def main():
    """主函数"""
    print("=" * 80)
    print("🎬 VisionAI-ClipsMaster 修复版启动器")
    print("=" * 80)
    
    # 1. 设置环境
    setup_environment()
    
    # 2. 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的包后重试")
        input("按回车键退出...")
        return 1
    
    # 3. 检查UI模块
    if not check_ui_modules():
        print("\n❌ UI模块检查失败")
        print("🔧 尝试运行诊断工具: python diagnose_startup_failure.py")
        input("按回车键退出...")
        return 1
    
    # 4. 启动应用
    try:
        return create_safe_startup()
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在退出...")
        return 0
    except Exception as e:
        print(f"\n💥 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 请尝试:")
        print("1. 重启计算机")
        print("2. 运行诊断工具: python diagnose_startup_failure.py")
        print("3. 联系技术支持")
        input("按回车键退出...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
