#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 优化启动脚本
使用智能预加载和进度显示提供最佳启动体验
"""

import os
import sys
import time
import traceback
from typing import Dict, Any

def setup_environment():
    """设置运行环境"""
    # 设置CUDA环境
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['TORCH_USE_CUDA_DSA'] = '0'
    
    # 设置Python路径
    if '.' not in sys.path:
        sys.path.insert(0, '.')
    
    # 设置编码
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

def main():
    """优化主函数"""
    print("🚀 VisionAI-ClipsMaster 优化启动")
    print("=" * 50)
    
    # 设置环境
    setup_environment()
    
    total_start_time = time.time()
    
    try:
        # 导入优化启动模块
        print("[1/4] 导入启动优化模块...")
        import_start = time.time()
        
        from ui.startup import start_optimized_application, create_main_window_after_startup
        from PyQt6.QtWidgets import QApplication
        
        import_time = time.time() - import_start
        print(f"✅ 启动模块导入完成 (耗时: {import_time:.2f}秒)")
        
        # 执行优化启动流程
        print("\n[2/4] 执行优化启动流程...")
        startup_start = time.time()
        
        startup_report = start_optimized_application(show_progress=True)
        
        startup_time = time.time() - startup_start
        print(f"✅ 优化启动完成 (耗时: {startup_time:.2f}秒)")
        
        # 检查启动是否成功
        if not startup_report['startup_success']:
            print("❌ 优化启动失败，尝试安全模式...")
            return start_safe_mode()
        
        # 创建主窗口
        print("\n[3/4] 创建主窗口...")
        window_start = time.time()
        
        main_window = create_main_window_after_startup()
        if main_window is None:
            print("❌ 主窗口创建失败，尝试传统启动...")
            return start_traditional_mode()
        
        window_time = time.time() - window_start
        print(f"✅ 主窗口创建完成 (耗时: {window_time:.2f}秒)")
        
        # 显示窗口并运行应用
        print("\n[4/4] 启动应用程序...")
        app_start = time.time()

        main_window.show()

        # 获取QApplication实例
        app = QApplication.instance()
        if app is None:
            print("❌ QApplication实例不存在")
            return 1

        app_time = time.time() - app_start
        total_time = time.time() - total_start_time

        print(f"✅ 应用程序启动完成 (耗时: {app_time:.2f}秒)")
        print(f"🎉 总启动时间: {total_time:.2f}秒")

        # 显示启动报告
        print_startup_report(startup_report, total_time)

        # 启动高级性能监控
        try:
            from ui.performance import AdvancedPerformanceMonitor
            performance_monitor = AdvancedPerformanceMonitor()
            performance_monitor.start_monitoring()
            print("📊 高级性能监控已启动")

            # 设置内存警告阈值为200MB
            performance_monitor.memory_warning_threshold = 200
            performance_monitor.memory_critical_threshold = 300

        except Exception as e:
            print(f"⚠️ 性能监控启动失败: {e}")

        # 运行应用程序
        print("\n🎬 VisionAI-ClipsMaster 已就绪，等待用户操作...")
        return app.exec()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断启动")
        return 1
        
    except Exception as e:
        total_time = time.time() - total_start_time
        print(f"\n❌ 启动失败: {e}")
        print(f"💥 失败时间: {total_time:.2f}秒")
        traceback.print_exc()
        
        # 尝试安全模式
        print("\n🛡️ 尝试启动安全模式...")
        return start_safe_mode()

def start_safe_mode():
    """启动增强安全模式"""
    try:
        print("🛡️ 正在启动增强安全模式...")

        from ui.safety import EnhancedSafeModeWindow
        from PyQt6.QtWidgets import QApplication

        # 确保有QApplication实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # 创建增强安全模式窗口
        safe_window = EnhancedSafeModeWindow()
        safe_window.show()

        print("✅ 增强安全模式启动成功")
        print("🔍 自动诊断系统已启动")
        print("🔧 自动修复功能已就绪")

        return app.exec()

    except Exception as e:
        print(f"❌ 增强安全模式启动失败: {e}")
        traceback.print_exc()

        # 回退到基础安全模式
        try:
            print("🔄 尝试基础安全模式...")
            from simple_ui_fixed import create_safe_mode_window

            safe_window = create_safe_mode_window()
            if safe_window:
                safe_window.show()
                print("✅ 基础安全模式启动成功")
                return app.exec()
            else:
                print("❌ 基础安全模式启动失败")
                return 1
        except Exception as fallback_e:
            print(f"❌ 基础安全模式也启动失败: {fallback_e}")
            return 1

def start_traditional_mode():
    """启动传统模式"""
    try:
        print("🔄 正在启动传统模式...")
        
        from simple_ui_fixed import main as traditional_main
        return traditional_main()
        
    except Exception as e:
        print(f"❌ 传统模式启动失败: {e}")
        return 1

def print_startup_report(report: Dict[str, Any], total_time: float):
    """打印启动报告"""
    print("\n" + "=" * 50)
    print("📊 启动性能报告")
    print("=" * 50)
    
    # 基本信息
    print(f"启动状态: {'✅ 成功' if report['startup_success'] else '❌ 失败'}")
    print(f"总启动时间: {total_time:.2f}秒")
    print(f"优化启动时间: {report['total_time']:.2f}秒")
    print(f"阶段成功率: {report['success_rate']:.1f}% ({report['successful_stages']}/{report['total_stages']})")
    
    # 性能评级
    performance = report['performance_metrics']
    print(f"性能评级: {performance['performance_rating'].upper()}")
    print(f"目标时间: {performance['target_time']}秒")
    
    if performance['improvement_needed'] > 0:
        print(f"需要改进: {performance['improvement_needed']:.2f}秒")
    else:
        print("🎯 已达到性能目标！")
    
    # 阶段耗时
    print("\n📈 各阶段耗时:")
    for stage_name, stage_time in report['stage_times'].items():
        status = "✅" if report['stage_results'][stage_name]['success'] else "❌"
        print(f"  {status} {stage_name}: {stage_time:.2f}秒")
    
    # 模块加载统计
    module_report = report['module_load_report']
    print(f"\n📦 模块加载统计:")
    print(f"  总模块数: {module_report['total_modules']}")
    print(f"  已加载: {module_report['loaded_modules']}")
    print(f"  失败: {module_report['failed_modules']}")
    print(f"  成功率: {module_report['success_rate']:.1f}%")
    
    # 最慢阶段
    slowest_stage, slowest_time = report['slowest_stage']
    print(f"\n⏱️ 最慢阶段: {slowest_stage} ({slowest_time:.2f}秒)")
    
    print("=" * 50)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"💥 程序异常退出: {e}")
        traceback.print_exc()
        sys.exit(1)
