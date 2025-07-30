#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 整合包体积分析工具
分析打包后的体积构成和优化建议
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

class PackageSizeAnalyzer:
    """整合包体积分析器"""
    
    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
        self.internal_path = self.package_path / "_internal"
        
        self.analysis_results = {
            "total_size_mb": 0,
            "file_count": 0,
            "directory_analysis": {},
            "largest_files": [],
            "component_breakdown": {},
            "optimization_opportunities": []
        }
    
    def get_directory_size(self, directory: Path) -> Tuple[int, int]:
        """获取目录大小和文件数量"""
        total_size = 0
        file_count = 0
        
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
        except (PermissionError, OSError):
            pass
        
        return total_size, file_count
    
    def analyze_internal_components(self):
        """分析_internal目录中的组件"""
        print("🔍 分析_internal目录组件...")
        
        if not self.internal_path.exists():
            print("❌ _internal目录不存在")
            return
        
        components = {}
        
        # 分析主要组件
        for item in self.internal_path.iterdir():
            if item.is_dir():
                size, count = self.get_directory_size(item)
                components[item.name] = {
                    "size_mb": size / 1024 / 1024,
                    "file_count": count,
                    "type": "directory"
                }
            elif item.is_file():
                size = item.stat().st_size
                components[item.name] = {
                    "size_mb": size / 1024 / 1024,
                    "file_count": 1,
                    "type": "file"
                }
        
        # 按大小排序
        sorted_components = sorted(components.items(), 
                                 key=lambda x: x[1]["size_mb"], 
                                 reverse=True)
        
        self.analysis_results["component_breakdown"] = dict(sorted_components)
        
        print("📊 主要组件大小排序:")
        for name, info in sorted_components[:15]:
            size_mb = info["size_mb"]
            file_count = info["file_count"]
            comp_type = info["type"]
            print(f"   {name:30} {size_mb:8.1f} MB ({file_count:4d} files) [{comp_type}]")
    
    def analyze_ai_frameworks(self):
        """分析AI框架组件"""
        print("\n🤖 分析AI框架组件...")
        
        ai_components = {
            "torch": "PyTorch深度学习框架",
            "transformers": "HuggingFace Transformers",
            "numpy": "数值计算库",
            "scipy": "科学计算库",
            "opencv": "计算机视觉库",
            "sklearn": "机器学习库",
            "pandas": "数据处理库",
            "matplotlib": "绘图库",
            "PIL": "图像处理库",
            "cv2": "OpenCV Python绑定"
        }
        
        ai_analysis = {}
        total_ai_size = 0
        
        for component, description in ai_components.items():
            component_path = self.internal_path / component
            if component_path.exists():
                size, count = self.get_directory_size(component_path)
                size_mb = size / 1024 / 1024
                ai_analysis[component] = {
                    "size_mb": size_mb,
                    "file_count": count,
                    "description": description
                }
                total_ai_size += size_mb
        
        print(f"🎯 AI框架总大小: {total_ai_size:.1f} MB")
        print("📋 AI框架详细分析:")
        
        for component, info in sorted(ai_analysis.items(), 
                                    key=lambda x: x[1]["size_mb"], 
                                    reverse=True):
            size_mb = info["size_mb"]
            file_count = info["file_count"]
            desc = info["description"]
            print(f"   {component:15} {size_mb:8.1f} MB ({file_count:4d} files) - {desc}")
        
        return ai_analysis, total_ai_size
    
    def analyze_python_runtime(self):
        """分析Python运行时组件"""
        print("\n🐍 分析Python运行时组件...")
        
        python_components = [
            "python3.dll", "python311.dll", "base_library.zip",
            "vcruntime140.dll", "msvcp140.dll", "ucrtbase.dll"
        ]
        
        python_analysis = {}
        total_python_size = 0
        
        for component in python_components:
            component_path = self.internal_path / component
            if component_path.exists():
                size = component_path.stat().st_size
                size_mb = size / 1024 / 1024
                python_analysis[component] = size_mb
                total_python_size += size_mb
        
        print(f"🎯 Python运行时总大小: {total_python_size:.1f} MB")
        print("📋 Python运行时详细分析:")
        
        for component, size_mb in sorted(python_analysis.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True):
            print(f"   {component:20} {size_mb:8.1f} MB")
        
        return python_analysis, total_python_size
    
    def find_largest_files(self, top_n: int = 20):
        """查找最大的文件"""
        print(f"\n📁 查找最大的{top_n}个文件...")
        
        all_files = []
        
        for item in self.package_path.rglob('*'):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    relative_path = item.relative_to(self.package_path)
                    all_files.append((str(relative_path), size))
                except (PermissionError, OSError):
                    continue
        
        # 按大小排序
        largest_files = sorted(all_files, key=lambda x: x[1], reverse=True)[:top_n]
        
        print("📊 最大文件列表:")
        for i, (file_path, size) in enumerate(largest_files, 1):
            size_mb = size / 1024 / 1024
            print(f"   {i:2d}. {file_path:60} {size_mb:8.1f} MB")
        
        self.analysis_results["largest_files"] = largest_files
        return largest_files
    
    def identify_optimization_opportunities(self):
        """识别优化机会"""
        print("\n🔧 识别优化机会...")
        
        opportunities = []
        
        # 检查可能的冗余组件
        redundant_patterns = [
            ("tests", "测试文件目录"),
            ("docs", "文档目录"),
            ("examples", "示例文件"),
            ("__pycache__", "Python缓存文件"),
            (".dist-info", "包信息文件"),
            ("locale", "本地化文件"),
            ("tcl8", "Tcl/Tk组件"),
            ("tk86t.dll", "Tk GUI组件"),
            ("_tcl_data", "Tcl数据文件"),
            ("_tk_data", "Tk数据文件")
        ]
        
        for pattern, description in redundant_patterns:
            matching_items = list(self.internal_path.glob(f"**/*{pattern}*"))
            if matching_items:
                total_size = 0
                for item in matching_items:
                    if item.is_file():
                        total_size += item.stat().st_size
                    elif item.is_dir():
                        size, _ = self.get_directory_size(item)
                        total_size += size
                
                if total_size > 1024 * 1024:  # 大于1MB才报告
                    opportunities.append({
                        "pattern": pattern,
                        "description": description,
                        "size_mb": total_size / 1024 / 1024,
                        "items_count": len(matching_items),
                        "optimization_type": "remove_redundant"
                    })
        
        # 检查大型AI库的优化机会
        large_ai_libs = [
            ("torch", "考虑使用CPU版本或量化版本"),
            ("transformers", "只保留必需的模型类型"),
            ("scipy", "考虑使用精简版本"),
            ("matplotlib", "如不需要绘图功能可移除"),
            ("pandas", "考虑使用更轻量的数据处理库")
        ]
        
        for lib_name, suggestion in large_ai_libs:
            lib_path = self.internal_path / lib_name
            if lib_path.exists():
                size, _ = self.get_directory_size(lib_path)
                size_mb = size / 1024 / 1024
                if size_mb > 50:  # 大于50MB
                    opportunities.append({
                        "pattern": lib_name,
                        "description": suggestion,
                        "size_mb": size_mb,
                        "optimization_type": "optimize_ai_lib"
                    })
        
        self.analysis_results["optimization_opportunities"] = opportunities
        
        print("💡 优化建议:")
        for opp in opportunities:
            print(f"   • {opp['pattern']:20} {opp['size_mb']:8.1f} MB - {opp['description']}")
        
        return opportunities
    
    def generate_optimization_plan(self):
        """生成优化方案"""
        print("\n📋 生成优化方案...")
        
        optimization_plan = {
            "immediate_savings": [],  # 立即可实现的节省
            "moderate_savings": [],   # 中等风险的节省
            "aggressive_savings": []  # 激进的节省方案
        }
        
        # 立即可实现的优化（低风险）
        immediate_items = [
            ("__pycache__", "Python缓存文件", 5, "删除所有.pyc文件"),
            ("tests", "测试文件", 20, "删除测试目录"),
            ("docs", "文档文件", 10, "删除文档目录"),
            (".dist-info", "包信息", 5, "删除包元数据"),
            ("locale", "本地化", 15, "只保留中英文")
        ]
        
        for pattern, desc, est_savings, action in immediate_items:
            optimization_plan["immediate_savings"].append({
                "item": pattern,
                "description": desc,
                "estimated_savings_mb": est_savings,
                "action": action,
                "risk": "低"
            })
        
        # 中等风险的优化
        moderate_items = [
            ("matplotlib", "绘图库", 80, "如不需要可视化功能可删除"),
            ("pandas", "数据处理", 60, "使用更轻量的替代方案"),
            ("scipy", "科学计算", 100, "只保留必需的子模块"),
            ("tcl8/tk86t", "GUI组件", 30, "删除Tkinter相关组件")
        ]
        
        for pattern, desc, est_savings, action in moderate_items:
            optimization_plan["moderate_savings"].append({
                "item": pattern,
                "description": desc,
                "estimated_savings_mb": est_savings,
                "action": action,
                "risk": "中"
            })
        
        # 激进的优化（高风险）
        aggressive_items = [
            ("torch", "PyTorch", 300, "使用ONNX Runtime替代"),
            ("transformers", "Transformers", 200, "只保留必需的模型架构"),
            ("opencv", "OpenCV", 150, "使用精简版本"),
            ("numpy", "NumPy", 50, "使用Intel MKL优化版本")
        ]
        
        for pattern, desc, est_savings, action in aggressive_items:
            optimization_plan["aggressive_savings"].append({
                "item": pattern,
                "description": desc,
                "estimated_savings_mb": est_savings,
                "action": action,
                "risk": "高"
            })
        
        # 计算总的潜在节省
        total_immediate = sum(item["estimated_savings_mb"] for item in optimization_plan["immediate_savings"])
        total_moderate = sum(item["estimated_savings_mb"] for item in optimization_plan["moderate_savings"])
        total_aggressive = sum(item["estimated_savings_mb"] for item in optimization_plan["aggressive_savings"])
        
        print(f"💾 潜在节省空间:")
        print(f"   立即可实现: {total_immediate} MB (低风险)")
        print(f"   中等优化:   {total_moderate} MB (中风险)")
        print(f"   激进优化:   {total_aggressive} MB (高风险)")
        print(f"   总计可节省: {total_immediate + total_moderate + total_aggressive} MB")
        
        return optimization_plan
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("🔍 VisionAI-ClipsMaster 整合包体积分析")
        print("=" * 60)
        
        # 基本信息
        total_size, file_count = self.get_directory_size(self.package_path)
        self.analysis_results["total_size_mb"] = total_size / 1024 / 1024
        self.analysis_results["file_count"] = file_count
        
        print(f"📊 整合包基本信息:")
        print(f"   总大小: {self.analysis_results['total_size_mb']:.1f} MB")
        print(f"   文件数: {file_count:,} 个")
        
        # 详细分析
        self.analyze_internal_components()
        ai_analysis, ai_total = self.analyze_ai_frameworks()
        python_analysis, python_total = self.analyze_python_runtime()
        self.find_largest_files()
        self.identify_optimization_opportunities()
        optimization_plan = self.generate_optimization_plan()
        
        # 生成总结报告
        self.generate_summary_report(ai_total, python_total, optimization_plan)
        
        return self.analysis_results
    
    def generate_summary_report(self, ai_total, python_total, optimization_plan):
        """生成总结报告"""
        print("\n" + "=" * 60)
        print("📋 体积分析总结报告")
        print("=" * 60)
        
        total_mb = self.analysis_results["total_size_mb"]
        
        print(f"🎯 体积构成分析:")
        print(f"   AI框架组件:    {ai_total:8.1f} MB ({ai_total/total_mb*100:.1f}%)")
        print(f"   Python运行时:  {python_total:8.1f} MB ({python_total/total_mb*100:.1f}%)")
        print(f"   其他组件:      {total_mb-ai_total-python_total:8.1f} MB ({(total_mb-ai_total-python_total)/total_mb*100:.1f}%)")
        print(f"   总计:          {total_mb:8.1f} MB (100.0%)")
        
        print(f"\n💡 优化建议总结:")
        immediate_savings = sum(item["estimated_savings_mb"] for item in optimization_plan["immediate_savings"])
        moderate_savings = sum(item["estimated_savings_mb"] for item in optimization_plan["moderate_savings"])
        aggressive_savings = sum(item["estimated_savings_mb"] for item in optimization_plan["aggressive_savings"])
        
        print(f"   保守优化: 可节省 {immediate_savings} MB (目标大小: {total_mb-immediate_savings:.1f} MB)")
        print(f"   中等优化: 可节省 {immediate_savings+moderate_savings} MB (目标大小: {total_mb-immediate_savings-moderate_savings:.1f} MB)")
        print(f"   激进优化: 可节省 {immediate_savings+moderate_savings+aggressive_savings} MB (目标大小: {total_mb-immediate_savings-moderate_savings-aggressive_savings:.1f} MB)")
    
    def save_analysis_report(self, output_file: str = "package_analysis_report.json"):
        """保存分析报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细分析报告已保存: {output_file}")

def main():
    """主函数"""
    package_path = "dist/VisionAI-ClipsMaster"
    
    if not Path(package_path).exists():
        print(f"❌ 整合包目录不存在: {package_path}")
        return
    
    analyzer = PackageSizeAnalyzer(package_path)
    results = analyzer.run_full_analysis()
    analyzer.save_analysis_report()

if __name__ == "__main__":
    main()
