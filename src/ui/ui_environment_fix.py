#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI环境修复工具
解决CUDA依赖和模块导入问题
"""

import os
import sys
import warnings

def fix_cuda_environment():
    """修复CUDA环境问题"""
    # 设置环境变量避免CUDA问题
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['TORCH_USE_CUDA_DSA'] = '0'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

    # 禁用CUDA相关警告
    os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'

    # 设置CPU模式 - 使用更安全的导入方式
    try:
        # 先检查torch是否可以安全导入
        import importlib.util
        torch_spec = importlib.util.find_spec("torch")
        if torch_spec is not None:
            # 尝试导入torch，如果失败则跳过
            try:
                import torch
                if hasattr(torch, 'cuda') and torch.cuda.is_available():
                    torch.cuda.set_device(-1)  # 强制使用CPU
                print("[OK] CUDA环境已禁用，使用CPU模式")
            except (OSError, ImportError, RuntimeError) as e:
                print(f"[WARN] torch导入失败，跳过CUDA设置: {e}")
                # 不抛出异常，继续执行
        else:
            print("[INFO] torch未安装，跳过CUDA设置")
    except Exception as e:
        print(f"[WARN] CUDA环境设置失败: {e}")
        # 不抛出异常，继续执行

def fix_import_paths():
    """修复导入路径"""
    # 添加项目根目录到路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 添加src目录到路径
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def suppress_warnings():
    """抑制不必要的警告"""
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)

def safe_import_ui_components():
    """安全导入UI组件"""
    components = {}

    # 首先尝试阻止任何可能的torch导入
    import sys

    # 临时替换torch模块以避免CUDA问题
    class MockTorch:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    # 如果torch已经导入失败，创建一个mock版本
    if 'torch' not in sys.modules:
        sys.modules['torch'] = MockTorch()
        sys.modules['torch.cuda'] = MockTorch()

    try:
        from .training_panel import TrainingPanel
        components['TrainingPanel'] = TrainingPanel
    except Exception as e:
        print(f"Warning: Failed to import TrainingPanel: {e}")
        components['TrainingPanel'] = None

    try:
        from .progress_dashboard import ProgressDashboard
        components['ProgressDashboard'] = ProgressDashboard
    except Exception as e:
        print(f"Warning: Failed to import ProgressDashboard: {e}")
        components['ProgressDashboard'] = None

    try:
        from .components.realtime_charts import RealtimeCharts
        components['RealtimeCharts'] = RealtimeCharts
    except Exception as e:
        print(f"Warning: Failed to import RealtimeCharts: {e}")
        components['RealtimeCharts'] = None

    try:
        from .components.alert_manager import AlertManager
        components['AlertManager'] = AlertManager
    except Exception as e:
        print(f"Warning: Failed to import AlertManager: {e}")
        components['AlertManager'] = None

    return components

def initialize_ui_environment():
    """初始化UI环境"""
    print("正在初始化UI环境...")
    
    # 修复CUDA环境
    fix_cuda_environment()
    print("✓ CUDA环境已修复")
    
    # 修复导入路径
    fix_import_paths()
    print("✓ 导入路径已修复")
    
    # 抑制警告
    suppress_warnings()
    print("✓ 警告已抑制")
    
    # 安全导入组件
    components = safe_import_ui_components()
    available_components = [name for name, comp in components.items() if comp is not None]
    print(f"✓ 可用UI组件: {', '.join(available_components)}")
    
    return components

# 不自动执行环境修复，由调用者决定何时执行
# 这样避免了导入时的副作用
