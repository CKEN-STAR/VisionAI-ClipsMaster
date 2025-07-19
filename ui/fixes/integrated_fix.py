"""
集成修复模块
提供各种技术修复和环境优化功能
"""

import os
import sys
import warnings
from pathlib import Path

def apply_all_fixes():
    """应用所有技术修复"""
    try:
        # 1. 设置CUDA环境变量（强制CPU模式）
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['TORCH_USE_CUDA_DSA'] = '0'
        
        # 2. 禁用不必要的警告
        warnings.filterwarnings('ignore', category=UserWarning)
        warnings.filterwarnings('ignore', category=FutureWarning)
        
        # 3. 设置编码
        if sys.platform.startswith('win'):
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 4. 优化内存设置
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        
        print("[OK] 技术修复应用完成")
        return True
        
    except Exception as e:
        print(f"[WARN] 技术修复应用失败: {e}")
        return False

def initialize_post_app_fixes(app):
    """在QApplication创建后的修复"""
    try:
        if app:
            # 设置应用程序属性 - 修复PyQt6兼容性
            from PyQt6.QtCore import Qt
            try:
                # PyQt6中的正确方式
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
                print("[OK] 高DPI支持已启用")
            except AttributeError:
                # 如果属性不存在，尝试其他方式
                try:
                    app.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi, False)
                    print("[OK] DPI设置已应用（备用方式）")
                except AttributeError:
                    print("[WARN] 无法设置DPI属性，跳过")

        print("[OK] 应用后修复完成")
        return True

    except Exception as e:
        print(f"[WARN] 应用后修复失败: {e}")
        return False

def get_fix_status():
    """获取修复状态"""
    return {
        'cuda_disabled': os.environ.get('CUDA_VISIBLE_DEVICES') == '',
        'encoding_set': os.environ.get('PYTHONIOENCODING') == 'utf-8',
        'memory_optimized': 'PYTORCH_CUDA_ALLOC_CONF' in os.environ
    }

# 兼容性函数
def apply_fixes():
    """兼容性函数"""
    return apply_all_fixes()

__all__ = [
    'apply_all_fixes',
    'initialize_post_app_fixes', 
    'get_fix_status',
    'apply_fixes'
]
