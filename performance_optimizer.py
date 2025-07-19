#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能优化器
实施具体的性能优化措施
"""

import os
import sys
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.optimization_log = []
        
    def optimize_file_structure(self) -> Dict[str, Any]:
        """优化文件结构"""
        print("📁 优化文件结构...")
        
        optimization_result = {
            "cleaned_files": 0,
            "saved_space_mb": 0,
            "actions": []
        }
        
        # 清理临时文件
        temp_patterns = [
            '**/__pycache__',
            '**/*.pyc',
            '**/*.pyo',
            '**/.pytest_cache',
            '**/crash_log.txt',
            '**/test_output*.json',
            '**/temp_*',
            '**/*.tmp'
        ]
        
        for pattern in temp_patterns:
            for path in self.project_root.glob(pattern):
                if path.exists():
                    try:
                        size_before = self._get_size(path)
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                        
                        optimization_result["cleaned_files"] += 1
                        optimization_result["saved_space_mb"] += size_before / 1024**2
                        optimization_result["actions"].append(f"删除: {path}")
                        
                    except Exception as e:
                        logger.warning(f"无法删除 {path}: {e}")
        
        print(f"✅ 清理了 {optimization_result['cleaned_files']} 个文件")
        print(f"   节省空间: {optimization_result['saved_space_mb']:.2f} MB")
        
        return optimization_result
    
    def optimize_imports(self) -> Dict[str, Any]:
        """优化导入性能"""
        print("\n🚀 优化导入性能...")
        
        # 创建延迟导入包装器
        lazy_import_template = '''
def lazy_import(module_name):
    """延迟导入装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not hasattr(wrapper, '_module'):
                wrapper._module = __import__(module_name, fromlist=[''])
            return func(wrapper._module, *args, **kwargs)
        return wrapper
    return decorator
'''
        
        # 保存延迟导入工具
        lazy_import_file = self.project_root / 'src' / 'utils' / 'lazy_import.py'
        lazy_import_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(lazy_import_file, 'w', encoding='utf-8') as f:
            f.write(lazy_import_template)
        
        print("✅ 创建了延迟导入工具")
        
        return {"lazy_import_created": True}
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        print("\n💾 优化内存使用...")
        
        # 创建内存优化配置
        memory_config = {
            "gc_threshold": [700, 10, 10],  # 更激进的垃圾回收
            "max_cache_size": 100,  # 限制缓存大小
            "enable_memory_profiling": False,  # 生产环境关闭内存分析
            "lazy_loading": True,  # 启用延迟加载
            "memory_limit_mb": 400  # 内存限制
        }
        
        config_file = self.project_root / 'configs' / 'memory_optimization.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(memory_config, f, indent=2, ensure_ascii=False)
        
        print("✅ 创建了内存优化配置")
        
        return {"memory_config_created": True}
    
    def optimize_startup_sequence(self) -> Dict[str, Any]:
        """优化启动序列"""
        print("\n⚡ 优化启动序列...")
        
        # 创建优化的启动脚本
        startup_script = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化启动脚本
"""

import os
import sys
import gc
from pathlib import Path

def optimize_startup():
    """优化启动过程"""
    # 设置垃圾回收阈值
    gc.set_threshold(700, 10, 10)
    
    # 设置环境变量
    os.environ['PYTHONOPTIMIZE'] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    # 预编译正则表达式
    import re
    re.compile(r'\\d+')  # 预编译常用正则
    
    print("🚀 启动优化完成")

def main():
    """主启动函数"""
    optimize_startup()
    
    # 导入主应用
    try:
        from simple_ui_fixed import main as ui_main
        ui_main()
    except ImportError:
        print("❌ 无法导入UI模块")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        startup_file = self.project_root / 'optimized_launcher.py'
        with open(startup_file, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        print("✅ 创建了优化启动脚本")
        
        return {"startup_script_created": True}
    
    def create_performance_monitor(self) -> Dict[str, Any]:
        """创建性能监控器"""
        print("\n📊 创建性能监控器...")
        
        monitor_script = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能监控器
"""

import time
import psutil
import threading
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            "memory_usage": [],
            "cpu_usage": [],
            "response_times": []
        }
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            # 记录内存使用
            memory = psutil.virtual_memory()
            self.stats["memory_usage"].append({
                "timestamp": time.time(),
                "usage_mb": memory.used / 1024**2,
                "percent": memory.percent
            })
            
            # 记录CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            self.stats["cpu_usage"].append({
                "timestamp": time.time(),
                "percent": cpu_percent
            })
            
            # 保持最近100个记录
            for key in self.stats:
                if len(self.stats[key]) > 100:
                    self.stats[key] = self.stats[key][-100:]
            
            time.sleep(5)  # 每5秒监控一次
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def record_response_time(self, operation: str, duration: float):
        """记录响应时间"""
        self.stats["response_times"].append({
            "timestamp": time.time(),
            "operation": operation,
            "duration": duration
        })

# 全局监控器实例
performance_monitor = PerformanceMonitor()
'''
        
        monitor_file = self.project_root / 'src' / 'utils' / 'performance_monitor.py'
        monitor_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(monitor_file, 'w', encoding='utf-8') as f:
            f.write(monitor_script)
        
        print("✅ 创建了性能监控器")
        
        return {"performance_monitor_created": True}
    
    def _get_size(self, path: Path) -> int:
        """获取文件或目录大小"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total_size = 0
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, FileNotFoundError):
                        pass
            return total_size
        return 0
    
    def run_all_optimizations(self) -> Dict[str, Any]:
        """运行所有优化"""
        print("=== VisionAI-ClipsMaster 性能优化 ===")
        print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {}
        
        # 执行各项优化
        results["file_structure"] = self.optimize_file_structure()
        results["imports"] = self.optimize_imports()
        results["memory"] = self.optimize_memory_usage()
        results["startup"] = self.optimize_startup_sequence()
        results["monitor"] = self.create_performance_monitor()
        
        print("\n=== 优化完成 ===")
        print("🎉 所有性能优化措施已实施完成！")
        print("\n📋 优化总结:")
        print(f"- 清理文件: {results['file_structure']['cleaned_files']} 个")
        print(f"- 节省空间: {results['file_structure']['saved_space_mb']:.2f} MB")
        print("- 创建了延迟导入工具")
        print("- 创建了内存优化配置")
        print("- 创建了优化启动脚本")
        print("- 创建了性能监控器")
        
        print("\n🚀 使用优化启动脚本:")
        print("   python optimized_launcher.py")
        
        return results

def main():
    """主函数"""
    optimizer = PerformanceOptimizer()
    return optimizer.run_all_optimizations()

if __name__ == "__main__":
    main()
