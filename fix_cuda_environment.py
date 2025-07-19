#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster CUDA环境修复工具
解决CUDA依赖导致的UI组件导入失败问题
"""

import os
import sys
import warnings
from pathlib import Path

def fix_cuda_environment():
    """修复CUDA环境问题"""
    print("🔧 正在修复CUDA环境...")
    
    # 设置环境变量强制使用CPU模式
    cuda_env_vars = {
        'CUDA_VISIBLE_DEVICES': '',
        'TORCH_USE_CUDA_DSA': '0',
        'CUDA_LAUNCH_BLOCKING': '1',
        'TORCH_USE_CUDA': '0',
        'FORCE_CPU': '1'
    }
    
    for key, value in cuda_env_vars.items():
        os.environ[key] = value
        print(f"  设置 {key}={value}")
    
    # 禁用CUDA相关警告
    os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'
    
    # 抑制警告
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    print("✅ CUDA环境修复完成")

def fix_torch_import():
    """修复PyTorch导入问题"""
    print("🔧 正在修复PyTorch导入...")
    
    try:
        # 尝试导入torch并强制CPU模式
        import torch
        
        # 如果CUDA可用，强制禁用
        if torch.cuda.is_available():
            print("  检测到CUDA，强制切换到CPU模式")
            torch.cuda.set_device(-1)
        
        # 设置默认设备为CPU
        torch.set_default_tensor_type('torch.FloatTensor')
        
        print("✅ PyTorch导入修复完成")
        return True
        
    except ImportError as e:
        print(f"⚠️ PyTorch未安装或导入失败: {e}")
        return False
    except Exception as e:
        print(f"⚠️ PyTorch配置失败: {e}")
        return False

def fix_import_paths():
    """修复模块导入路径"""
    print("🔧 正在修复导入路径...")
    
    # 获取项目根目录
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    
    # 添加路径到sys.path
    paths_to_add = [
        str(project_root),
        str(src_path),
        str(src_path / "ui"),
        str(src_path / "ui" / "components")
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
            print(f"  添加路径: {path}")
    
    print("✅ 导入路径修复完成")

def test_ui_imports():
    """测试UI组件导入"""
    print("🧪 测试UI组件导入...")
    
    import_tests = [
        ("src.ui.training_panel", "TrainingPanel"),
        ("src.ui.progress_dashboard", "ProgressDashboard"),
        ("src.ui.components.realtime_charts", "RealtimeCharts"),
        ("src.ui.components.alert_manager", "AlertManager")
    ]
    
    success_count = 0
    total_count = len(import_tests)
    
    for module_name, class_name in import_tests:
        try:
            print(f"  测试导入 {module_name}.{class_name}...", end=" ")
            
            # 尝试导入模块
            module = __import__(module_name, fromlist=[class_name])
            
            # 检查类是否存在
            if hasattr(module, class_name):
                component_class = getattr(module, class_name)
                if component_class is not None:
                    print("✅")
                    success_count += 1
                else:
                    print("❌ (类为None)")
            else:
                print(f"❌ (类{class_name}不存在)")
                
        except ImportError as e:
            print(f"❌ (导入错误: {str(e)})")
        except Exception as e:
            print(f"❌ (意外错误: {str(e)})")
    
    success_rate = success_count / total_count
    print(f"📊 导入测试结果: {success_count}/{total_count} ({success_rate:.1%})")
    
    return success_rate >= 0.8

def main():
    """主修复流程"""
    print("🚀 开始修复VisionAI-ClipsMaster UI组件导入问题...")
    print("=" * 60)
    
    # 步骤1: 修复CUDA环境
    fix_cuda_environment()
    print()
    
    # 步骤2: 修复PyTorch导入
    torch_ok = fix_torch_import()
    print()
    
    # 步骤3: 修复导入路径
    fix_import_paths()
    print()
    
    # 步骤4: 测试UI组件导入
    import_ok = test_ui_imports()
    print()
    
    # 总结
    print("=" * 60)
    if import_ok:
        print("🎉 UI组件导入问题修复成功!")
        print("✅ 所有UI组件现在应该可以正常导入")
    else:
        print("⚠️ UI组件导入仍有问题")
        print("💡 建议:")
        print("  1. 检查是否所有UI组件文件都已创建")
        print("  2. 验证__init__.py文件配置")
        print("  3. 确保PyQt6正确安装")
    
    if not torch_ok:
        print("⚠️ PyTorch导入有问题，但不影响UI组件基本功能")
    
    print("\n🔄 请重新运行UI测试脚本验证修复效果")

if __name__ == "__main__":
    main()
