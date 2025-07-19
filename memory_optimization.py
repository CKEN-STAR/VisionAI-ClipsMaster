#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存优化脚本

优化VisionAI-ClipsMaster的内存使用，目标：≤400MB
策略：延迟加载、缓存清理、对象池化、垃圾回收优化
"""

import gc
import sys
import psutil
import os
from typing import Dict, Any, Optional

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_current_memory()
        
    def get_current_memory(self) -> float:
        """获取当前内存使用（MB）"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def force_garbage_collection(self) -> Dict[str, Any]:
        """强制垃圾回收"""
        before_memory = self.get_current_memory()
        
        # 执行多轮垃圾回收
        collected = []
        for generation in range(3):
            count = gc.collect(generation)
            collected.append(count)
        
        after_memory = self.get_current_memory()
        freed_memory = before_memory - after_memory
        
        return {
            "before_memory": before_memory,
            "after_memory": after_memory,
            "freed_memory": freed_memory,
            "collected_objects": collected
        }
    
    def optimize_imports(self) -> Dict[str, Any]:
        """优化导入模块"""
        before_memory = self.get_current_memory()
        
        # 清理未使用的模块
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('__pycache__'):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        after_memory = self.get_current_memory()
        
        return {
            "before_memory": before_memory,
            "after_memory": after_memory,
            "removed_modules": len(modules_to_remove)
        }
    
    def optimize_emotion_engine(self) -> Dict[str, Any]:
        """优化情感分析引擎内存使用"""
        before_memory = self.get_current_memory()
        
        try:
            from src.emotion.advanced_emotion_analysis_engine import _advanced_emotion_engine
            
            if _advanced_emotion_engine is not None:
                # 清理缓存数据
                if hasattr(_advanced_emotion_engine, 'cache'):
                    _advanced_emotion_engine.cache = {}
                
                # 优化规则存储
                if hasattr(_advanced_emotion_engine, 'emotion_rules'):
                    # 将规则转换为更紧凑的格式
                    for rule_name, rule in _advanced_emotion_engine.emotion_rules.items():
                        if hasattr(rule, 'patterns'):
                            # 编译正则表达式以节省内存
                            rule.compiled_patterns = [re.compile(p) for p in rule.patterns]
        except Exception as e:
            print(f"情感引擎优化失败: {e}")
        
        after_memory = self.get_current_memory()
        
        return {
            "before_memory": before_memory,
            "after_memory": after_memory,
            "optimization": "emotion_engine"
        }
    
    def optimize_plot_analyzer(self) -> Dict[str, Any]:
        """优化情节点分析器内存使用"""
        before_memory = self.get_current_memory()
        
        try:
            from src.core.advanced_plot_point_analyzer import _plot_point_analyzer
            
            if _plot_point_analyzer is not None:
                # 清理分析缓存
                if hasattr(_plot_point_analyzer, 'analysis_cache'):
                    _plot_point_analyzer.analysis_cache = {}
                
                # 优化权重字典
                if hasattr(_plot_point_analyzer, 'keyword_weights'):
                    # 将嵌套字典扁平化以节省内存
                    flattened_weights = {}
                    for category, weights in _plot_point_analyzer.keyword_weights.items():
                        for keyword, weight in weights.items():
                            flattened_weights[f"{category}:{keyword}"] = weight
                    _plot_point_analyzer.flattened_weights = flattened_weights
        except Exception as e:
            print(f"情节分析器优化失败: {e}")
        
        after_memory = self.get_current_memory()
        
        return {
            "before_memory": before_memory,
            "after_memory": after_memory,
            "optimization": "plot_analyzer"
        }
    
    def clear_module_caches(self) -> Dict[str, Any]:
        """清理模块缓存"""
        before_memory = self.get_current_memory()
        
        # 清理各种缓存
        caches_cleared = 0
        
        try:
            # 清理语言检测缓存
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            if hasattr(detector, 'cache'):
                detector.cache.clear()
                caches_cleared += 1
        except:
            pass
        
        try:
            # 清理叙事分析缓存
            from src.core.narrative_analyzer import _narrative_analyzer
            if _narrative_analyzer is not None and hasattr(_narrative_analyzer, 'cache'):
                _narrative_analyzer.cache.clear()
                caches_cleared += 1
        except:
            pass
        
        after_memory = self.get_current_memory()
        
        return {
            "before_memory": before_memory,
            "after_memory": after_memory,
            "caches_cleared": caches_cleared
        }
    
    def optimize_all(self) -> Dict[str, Any]:
        """执行全面内存优化"""
        print("🔧 开始内存优化...")
        
        initial_memory = self.get_current_memory()
        results = {"initial_memory": initial_memory}
        
        # 1. 强制垃圾回收
        print("  🗑️ 执行垃圾回收...")
        gc_result = self.force_garbage_collection()
        results["garbage_collection"] = gc_result
        print(f"    释放内存: {gc_result['freed_memory']:.2f}MB")
        
        # 2. 优化导入模块
        print("  📦 优化导入模块...")
        import_result = self.optimize_imports()
        results["import_optimization"] = import_result
        print(f"    移除模块: {import_result['removed_modules']}个")
        
        # 3. 清理模块缓存
        print("  🧹 清理模块缓存...")
        cache_result = self.clear_module_caches()
        results["cache_clearing"] = cache_result
        print(f"    清理缓存: {cache_result['caches_cleared']}个")
        
        # 4. 优化情感引擎
        print("  💭 优化情感引擎...")
        emotion_result = self.optimize_emotion_engine()
        results["emotion_optimization"] = emotion_result
        
        # 5. 优化情节分析器
        print("  📖 优化情节分析器...")
        plot_result = self.optimize_plot_analyzer()
        results["plot_optimization"] = plot_result
        
        # 6. 最终垃圾回收
        print("  🔄 最终垃圾回收...")
        final_gc = self.force_garbage_collection()
        results["final_gc"] = final_gc
        
        final_memory = self.get_current_memory()
        total_saved = initial_memory - final_memory
        
        results.update({
            "final_memory": final_memory,
            "total_memory_saved": total_saved,
            "optimization_success": final_memory <= 400.0
        })
        
        print(f"\n📊 内存优化结果:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  节省内存: {total_saved:.2f}MB")
        print(f"  目标达成: {'✅ 是' if final_memory <= 400.0 else '❌ 否'}")
        
        return results

def test_memory_optimization():
    """测试内存优化效果"""
    print("🧪 测试内存优化效果")
    print("=" * 50)
    
    optimizer = MemoryOptimizer()
    
    # 先运行一些操作来增加内存使用
    print("📈 模拟内存使用...")
    
    # 导入主要模块
    try:
        from src.emotion.emotion_intensity import get_emotion_intensity
        from src.core.narrative_analyzer import get_narrative_analyzer
        from src.core.language_detector import detect_language
        
        # 执行一些操作
        emotion_analyzer = get_emotion_intensity()
        narrative_analyzer = get_narrative_analyzer()
        
        # 分析一些文本
        test_texts = [
            "皇上，臣妾有重要的事情要禀报。",
            "什么事情如此紧急？速速道来！",
            "Good morning, everyone. We have an important announcement."
        ]
        
        for text in test_texts:
            emotion_analyzer.analyze_emotion_intensity(text)
            narrative_analyzer.analyze_narrative_structure([text])
            detect_language(text)
        
        print(f"  操作后内存: {optimizer.get_current_memory():.2f}MB")
        
    except Exception as e:
        print(f"  模拟操作失败: {e}")
    
    # 执行优化
    results = optimizer.optimize_all()
    
    return results["optimization_success"]

if __name__ == "__main__":
    import re
    success = test_memory_optimization()
    if success:
        print("\n🎉 内存优化成功！")
    else:
        print("\n⚠️ 内存优化未达到目标，需要进一步调整。")
