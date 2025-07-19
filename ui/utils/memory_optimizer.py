
import gc
import psutil
import threading
import time

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, threshold_mb=350):
        self.threshold_mb = threshold_mb
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """开始内存监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                if memory_mb > self.threshold_mb:
                    self.cleanup_memory()
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                print(f"内存监控错误: {e}")
                time.sleep(60)
                
    def cleanup_memory(self):
        """清理内存"""
        try:
            # 执行垃圾回收
            for _ in range(3):
                gc.collect()
                
            # 清理Python内部缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
                
            print("🧹 内存清理完成")
        except Exception as e:
            print(f"内存清理失败: {e}")

# 全局内存优化器实例
memory_optimizer = MemoryOptimizer()
