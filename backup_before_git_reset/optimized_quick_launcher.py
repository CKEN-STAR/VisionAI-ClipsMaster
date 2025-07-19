#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化启动器
实现快速启动和延迟加载
"""

import os
import sys
import time
from pathlib import Path

class OptimizedLauncher:
    """优化启动器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.modules_cache = {}
        self.startup_time = time.time()
        
    def setup_environment(self):
        """快速环境设置"""
        # 设置基本环境变量
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['TORCH_USE_CUDA_DSA'] = '0'
        
        # 添加项目路径
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def lazy_import(self, module_name: str):
        """延迟导入模块"""
        if module_name not in self.modules_cache:
            try:
                self.modules_cache[module_name] = __import__(module_name)
            except ImportError as e:
                print(f"延迟导入失败: {module_name} - {e}")
                return None
        return self.modules_cache[module_name]
    
    def quick_start(self):
        """快速启动"""
        print("🚀 VisionAI-ClipsMaster 快速启动中...")
        
        # 快速环境设置
        self.setup_environment()
        
        # 只导入最必要的模块
        essential_modules = [
            'simple_ui_fixed'
        ]
        
        for module in essential_modules:
            start_time = time.time()
            imported_module = self.lazy_import(module)
            import_time = time.time() - start_time
            
            if imported_module:
                print(f"✅ {module}: {import_time:.3f}秒")
            else:
                print(f"❌ {module}: 导入失败")
        
        total_startup_time = time.time() - self.startup_time
        print(f"🎉 启动完成: {total_startup_time:.3f}秒")
        
        return imported_module

def main():
    """主函数"""
    launcher = OptimizedLauncher()
    ui_module = launcher.quick_start()
    
    if ui_module and hasattr(ui_module, 'main'):
        ui_module.main()
    else:
        print("❌ UI模块启动失败")

if __name__ == "__main__":
    main()
