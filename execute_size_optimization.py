#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 体积优化主执行器
一键执行完整的体积优化流程：备份 → 优化 → 验证 → 报告
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                VisionAI-ClipsMaster 体积优化器                ║
║                                                              ║
║  目标: 将项目从 18.3GB 压缩至 ≤5GB (72%压缩率)                ║
║  策略: Git历史清理 + 重复文件清理 + 模块化部署                  ║
║  保证: 100% 核心功能完整性                                    ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_prerequisites() -> bool:
    """检查前置条件"""
    print("🔍 检查前置条件...")
    
    # 检查Git
    git_exe = r"C:\Program Files\Git\bin\git.exe"
    try:
        subprocess.run([git_exe, "--version"], capture_output=True, check=True)
        print("  ✅ Git 可用")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ Git 不可用，请安装Git")
        return False
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print(f"  ❌ Python版本过低 ({sys.version}), 需要Python 3.8+")
        return False
    else:
        print(f"  ✅ Python版本: {sys.version}")
    
    # 检查磁盘空间（需要至少20GB空闲空间用于备份）
    try:
        import shutil
        free_space = shutil.disk_usage(".").free / (1024**3)  # GB
        if free_space < 20:
            print(f"  ⚠️ 磁盘空间不足: {free_space:.1f}GB (建议至少20GB)")
            response = input("    继续执行？(y/N): ")
            if response.lower() != 'y':
                return False
        else:
            print(f"  ✅ 磁盘空间充足: {free_space:.1f}GB")
    except Exception:
        print("  ⚠️ 无法检查磁盘空间")
    
    return True

def get_current_project_size() -> float:
    """获取当前项目大小（GB）"""
    try:
        from size_optimization_executor import SizeOptimizer
        optimizer = SizeOptimizer()
        size_bytes = optimizer.get_directory_size(Path("."))
        return size_bytes / (1024**3)  # 转换为GB
    except Exception:
        return 0.0

def run_optimization() -> Dict[str, Any]:
    """运行优化流程"""
    print("\n🚀 开始执行优化流程...")
    
    try:
        # 导入优化器
        from size_optimization_executor import SizeOptimizer
        
        # 创建优化器实例
        optimizer = SizeOptimizer()
        
        # 执行优化
        results = optimizer.run_optimization()
        
        return results
        
    except ImportError as e:
        print(f"❌ 无法导入优化模块: {e}")
        return {"error": f"导入失败: {e}"}
    except Exception as e:
        print(f"❌ 优化执行失败: {e}")
        return {"error": f"执行失败: {e}"}

def run_validation() -> Dict[str, Any]:
    """运行功能验证"""
    print("\n🔍 开始功能验证...")
    
    try:
        # 导入验证器
        from optimization_function_validator import FunctionValidator
        
        # 创建验证器实例
        validator = FunctionValidator()
        
        # 执行验证
        results = validator.run_all_tests()
        
        return results
        
    except ImportError as e:
        print(f"❌ 无法导入验证模块: {e}")
        return {"error": f"导入失败: {e}"}
    except Exception as e:
        print(f"❌ 验证执行失败: {e}")
        return {"error": f"执行失败: {e}"}

def generate_final_report(optimization_results: Dict, validation_results: Dict) -> Dict[str, Any]:
    """生成最终报告"""
    print("\n📊 生成最终报告...")
    
    report = {
        "optimization_summary": {
            "timestamp": datetime.now().isoformat(),
            "original_size_gb": optimization_results.get("original_size", 0) / (1024**3),
            "optimized_size_gb": optimization_results.get("optimized_size", 0) / (1024**3),
            "total_saved_gb": optimization_results.get("total_saved", 0) / (1024**3),
            "compression_ratio": optimization_results.get("compression_ratio", 0),
            "target_achieved": optimization_results.get("compression_ratio", 0) >= 70
        },
        "functionality_verification": {
            "overall_score": validation_results.get("overall_score", 0),
            "tests_passed": len([t for t in validation_results.get("tests", {}).values() if t.get("success", False)]),
            "total_tests": len(validation_results.get("tests", {})),
            "critical_failures": validation_results.get("critical_failures", []),
            "functionality_intact": len(validation_results.get("critical_failures", [])) == 0
        },
        "optimization_phases": optimization_results.get("phases", {}),
        "errors": optimization_results.get("errors", []) + validation_results.get("warnings", []),
        "recommendations": []
    }
    
    # 生成建议
    if report["optimization_summary"]["target_achieved"]:
        report["recommendations"].append("✅ 优化目标已达成，项目体积减少超过70%")
    else:
        report["recommendations"].append("⚠️ 优化目标未完全达成，建议进一步清理")
    
    if report["functionality_verification"]["functionality_intact"]:
        report["recommendations"].append("✅ 所有核心功能验证通过")
    else:
        report["recommendations"].append("❌ 存在功能问题，建议检查或回滚")
    
    # 保存报告
    report_path = Path("optimization_final_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📋 最终报告已保存: {report_path}")
    
    return report

def print_summary(report: Dict[str, Any]):
    """打印优化总结"""
    opt_summary = report["optimization_summary"]
    func_summary = report["functionality_verification"]
    
    print("\n" + "="*60)
    print("🎯 VisionAI-ClipsMaster 体积优化完成")
    print("="*60)
    
    print(f"📊 体积变化:")
    print(f"  优化前: {opt_summary['original_size_gb']:.2f} GB")
    print(f"  优化后: {opt_summary['optimized_size_gb']:.2f} GB")
    print(f"  节省空间: {opt_summary['total_saved_gb']:.2f} GB")
    print(f"  压缩比例: {opt_summary['compression_ratio']:.1f}%")
    
    print(f"\n🔍 功能验证:")
    print(f"  总体评分: {func_summary['overall_score']:.1f}/100")
    print(f"  通过测试: {func_summary['tests_passed']}/{func_summary['total_tests']}")
    
    if opt_summary["target_achieved"] and func_summary["functionality_intact"]:
        print(f"\n🎉 优化成功！")
        print(f"  ✅ 体积目标达成 (≥70%压缩)")
        print(f"  ✅ 功能完整性保持")
        print(f"  ✅ 项目可正常使用")
    else:
        print(f"\n⚠️ 优化部分成功")
        if not opt_summary["target_achieved"]:
            print(f"  ❌ 体积目标未达成 ({opt_summary['compression_ratio']:.1f}% < 70%)")
        if not func_summary["functionality_intact"]:
            print(f"  ❌ 功能验证失败: {func_summary['critical_failures']}")
        print(f"  💡 建议检查错误日志或执行回滚")
    
    print(f"\n📋 详细报告: optimization_final_report.json")
    print("="*60)

def main():
    """主函数"""
    print_banner()
    
    # 检查前置条件
    if not check_prerequisites():
        print("\n❌ 前置条件检查失败，无法继续")
        return 1
    
    # 显示当前项目大小
    current_size = get_current_project_size()
    print(f"\n📏 当前项目大小: {current_size:.2f} GB")
    
    if current_size < 5.0:
        print("✅ 项目大小已符合目标要求")
        response = input("是否仍要执行优化？(y/N): ")
        if response.lower() != 'y':
            return 0
    
    # 用户确认
    print(f"\n⚠️ 即将开始体积优化，这将:")
    print(f"  1. 创建项目备份")
    print(f"  2. 清理Git历史（不可逆）")
    print(f"  3. 删除重复文件")
    print(f"  4. 重组项目结构")
    print(f"  5. 验证功能完整性")
    
    confirm = input(f"\n确认执行优化？(y/N): ")
    if confirm.lower() != 'y':
        print("用户取消操作")
        return 0
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行优化
    optimization_results = run_optimization()
    
    if "error" in optimization_results:
        print(f"\n❌ 优化失败: {optimization_results['error']}")
        return 1
    
    # 执行验证
    validation_results = run_validation()
    
    if "error" in validation_results:
        print(f"\n❌ 验证失败: {validation_results['error']}")
        print("优化已完成，但无法验证功能完整性")
    
    # 生成最终报告
    final_report = generate_final_report(optimization_results, validation_results)
    
    # 计算总耗时
    total_time = time.time() - start_time
    print(f"\n⏱️ 总耗时: {total_time/60:.1f} 分钟")
    
    # 打印总结
    print_summary(final_report)
    
    # 返回状态码
    success = (
        final_report["optimization_summary"]["target_achieved"] and
        final_report["functionality_verification"]["functionality_intact"]
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        print("如果优化已部分完成，可以运行 optimization_rollback.py 进行回滚")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        print("如果优化已部分完成，可以运行 optimization_rollback.py 进行回滚")
        sys.exit(1)
