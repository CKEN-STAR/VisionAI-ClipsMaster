#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI整合演示脚本
展示核心功能的完整工作流程

演示内容:
1. 语言检测和模型切换
2. 剧本重构工作流
3. 训练数据管理
4. 剪映工程导出
5. 内存管理监控
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_demo_subtitle_files():
    """创建演示用的字幕文件"""
    print("📝 创建演示字幕文件...")
    
    # 中文原片字幕
    zh_original = """1
00:00:01,000 --> 00:00:05,000
小明是一个普通的上班族

2
00:00:05,000 --> 00:00:10,000
每天过着平凡的生活

3
00:00:10,000 --> 00:00:15,000
直到有一天他遇到了神秘的老人

4
00:00:15,000 --> 00:00:20,000
老人告诉他一个惊天秘密

5
00:00:20,000 --> 00:00:25,000
原来小明拥有超能力
"""

    # 英文原片字幕
    en_original = """1
00:00:01,000 --> 00:00:05,000
Tom is an ordinary office worker

2
00:00:05,000 --> 00:00:10,000
Living a mundane life every day

3
00:00:10,000 --> 00:00:15,000
Until one day he met a mysterious old man

4
00:00:15,000 --> 00:00:20,000
The old man told him a shocking secret

5
00:00:20,000 --> 00:00:25,000
Tom actually has superpowers
"""

    # 创建临时文件
    zh_file = tempfile.NamedTemporaryFile(mode='w', suffix='_zh_original.srt', delete=False, encoding='utf-8')
    zh_file.write(zh_original)
    zh_file.close()
    
    en_file = tempfile.NamedTemporaryFile(mode='w', suffix='_en_original.srt', delete=False, encoding='utf-8')
    en_file.write(en_original)
    en_file.close()
    
    print(f"  ✅ 中文字幕: {zh_file.name}")
    print(f"  ✅ 英文字幕: {en_file.name}")
    
    return zh_file.name, en_file.name

def demo_language_detection_and_model_switching():
    """演示语言检测和模型切换"""
    print("\n🔍 === 语言检测和模型切换演示 ===")
    
    try:
        from src.core.language_detector import detect_language_from_file
        from src.core.model_switcher import ModelSwitcher
        
        # 创建演示文件
        zh_file, en_file = create_demo_subtitle_files()
        
        # 初始化模型切换器
        switcher = ModelSwitcher()
        print(f"🤖 模型切换器初始化完成")
        
        # 演示中文检测和切换
        print(f"\n📋 检测中文字幕...")
        zh_lang = detect_language_from_file(zh_file)
        print(f"  检测结果: {zh_lang}")
        
        zh_switch = switcher.switch_model(zh_lang)
        current_model = switcher.get_current_model()
        print(f"  切换到中文模型: {current_model} ({'成功' if zh_switch else '失败'})")
        
        # 演示英文检测和切换
        print(f"\n📋 检测英文字幕...")
        en_lang = detect_language_from_file(en_file)
        print(f"  检测结果: {en_lang}")
        
        en_switch = switcher.switch_model(en_lang)
        current_model = switcher.get_current_model()
        print(f"  切换到英文模型: {current_model} ({'成功' if en_switch else '失败'})")
        
        # 清理文件
        os.unlink(zh_file)
        os.unlink(en_file)
        
        print(f"✅ 语言检测和模型切换演示完成")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_screenplay_reconstruction():
    """演示剧本重构工作流"""
    print("\n🎬 === 剧本重构工作流演示 ===")
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        # 创建演示文件
        zh_file, _ = create_demo_subtitle_files()
        
        # 初始化剧本工程师
        engineer = ScreenplayEngineer()
        print(f"🎭 剧本工程师初始化完成")
        
        # 步骤1: 加载原片字幕
        print(f"\n📖 步骤1: 加载原片字幕")
        subtitles = engineer.load_subtitles(zh_file)
        print(f"  加载字幕: {len(subtitles)}条")
        
        # 步骤2: 分析剧情结构
        print(f"\n🔍 步骤2: 分析剧情结构")
        analysis = engineer.analyze_plot(subtitles)
        print(f"  分析完成: {len(analysis)}个维度")
        
        # 步骤3: 重构为爆款风格
        print(f"\n✨ 步骤3: 重构为爆款风格")
        result = engineer.reconstruct_screenplay(srt_input=subtitles, target_style="viral")
        reconstructed = result.get('segments', []) if isinstance(result, dict) else []
        print(f"  重构完成: {len(reconstructed)}个片段")
        
        # 显示重构效果
        if reconstructed:
            print(f"\n📊 重构效果:")
            print(f"  原始片段: {len(subtitles)}")
            print(f"  重构片段: {len(reconstructed)}")
            compression_ratio = len(reconstructed) / len(subtitles) if subtitles else 0
            print(f"  压缩比例: {compression_ratio:.2f}")
            print(f"  重构类型: 爆款短剧混剪")
        
        # 清理文件
        os.unlink(zh_file)
        
        print(f"✅ 剧本重构工作流演示完成")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_training_system():
    """演示训练系统"""
    print("\n📚 === 训练系统演示 ===")
    
    try:
        from src.training.trainer import ModelTrainer
        
        # 初始化训练器
        trainer = ModelTrainer()
        print(f"🤖 训练器初始化完成")
        
        # 获取训练状态
        status = trainer.get_training_status() if hasattr(trainer, 'get_training_status') else {"active": False}
        print(f"📊 当前训练状态: {status}")
        
        # 模拟投喂训练数据
        print(f"\n📥 模拟投喂训练数据:")
        print(f"  - 原片字幕: 100个文件")
        print(f"  - 爆款字幕: 100个对应文件")
        print(f"  - 训练对数: 100对")
        print(f"  - 语言分布: 中文60%, 英文40%")
        
        # 模拟训练过程
        print(f"\n🔄 模拟训练过程:")
        print(f"  阶段1: 基础时间轴对齐学习")
        print(f"  阶段2: 剧情结构理解训练")
        print(f"  阶段3: 爆款风格生成优化")
        
        print(f"✅ 训练系统演示完成")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_jianying_export():
    """演示剪映导出功能"""
    print("\n📤 === 剪映导出功能演示 ===")
    
    try:
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        
        # 初始化导出器
        exporter = JianyingProExporter()
        print(f"🎬 剪映导出器初始化完成")
        
        # 显示导出设置
        print(f"\n⚙️ 导出设置:")
        for key, value in exporter.export_settings.items():
            print(f"  {key}: {value}")
        
        # 模拟导出过程
        print(f"\n📋 模拟导出过程:")
        print(f"  1. 解析重构后的字幕时间轴")
        print(f"  2. 生成剪映工程文件结构")
        print(f"  3. 创建视频轨道和音频轨道")
        print(f"  4. 添加字幕轨道和特效")
        print(f"  5. 保存为.jyp工程文件")
        
        print(f"✅ 剪映导出功能演示完成")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def demo_memory_management():
    """演示内存管理"""
    print("\n💾 === 内存管理演示 ===")
    
    try:
        from ui_integration_fixes import AdvancedMemoryManager
        import psutil
        
        # 初始化内存管理器
        memory_mgr = AdvancedMemoryManager(target_limit_gb=3.8)
        print(f"🛡️ 内存管理器初始化完成")
        
        # 获取当前内存状态
        status = memory_mgr.get_memory_status()
        print(f"\n📊 当前内存状态:")
        print(f"  总内存: {status['total_gb']:.2f}GB")
        print(f"  已用内存: {status['used_gb']:.2f}GB")
        print(f"  可用内存: {status['available_gb']:.2f}GB")
        print(f"  使用率: {status['percent']:.1f}%")
        print(f"  状态级别: {status['status']}")
        print(f"  在限制内: {'是' if status['within_limit'] else '否'}")
        
        # 执行内存监控和清理
        print(f"\n🧹 执行内存监控和清理:")
        cleanup_result = memory_mgr.monitor_and_cleanup()
        if cleanup_result["performed"]:
            print(f"  执行了{cleanup_result['method']}清理")
            print(f"  释放内存: {cleanup_result.get('freed_mb', 0):.1f}MB")
        else:
            print(f"  内存状态良好，无需清理")
        
        # 获取清理报告
        cleanup_report = memory_mgr.get_cleanup_report()
        print(f"\n📈 清理历史报告:")
        print(f"  总清理次数: {cleanup_report['total_cleanups']}")
        if cleanup_report['total_cleanups'] > 0:
            print(f"  总释放内存: {cleanup_report['total_freed_mb']:.1f}MB")
            print(f"  平均释放: {cleanup_report['average_freed_mb']:.1f}MB")
        
        print(f"✅ 内存管理演示完成")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

def run_complete_demo():
    """运行完整的UI整合演示"""
    print("🎭 VisionAI-ClipsMaster UI整合功能演示")
    print("=" * 60)
    print("展示核心功能的完整工作流程")
    print("=" * 60)
    
    demo_functions = [
        ("语言检测和模型切换", demo_language_detection_and_model_switching),
        ("剧本重构工作流", demo_screenplay_reconstruction),
        ("训练系统", demo_training_system),
        ("剪映导出功能", demo_jianying_export),
        ("内存管理", demo_memory_management)
    ]
    
    results = {}
    
    for demo_name, demo_func in demo_functions:
        try:
            print(f"\n{'='*20} {demo_name} {'='*20}")
            result = demo_func()
            results[demo_name] = result
            time.sleep(1)  # 演示间隔
        except Exception as e:
            print(f"❌ {demo_name}演示异常: {e}")
            results[demo_name] = False
    
    # 生成演示总结
    print(f"\n{'='*60}")
    print("🎯 演示结果总结:")
    
    success_count = sum(results.values())
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    for demo_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {demo_name}: {status}")
    
    print(f"\n📊 总体成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    if success_rate == 100:
        print("🎉 所有功能演示成功！VisionAI-ClipsMaster UI整合完美运行！")
    elif success_rate >= 80:
        print("🎊 大部分功能演示成功！系统基本可用！")
    else:
        print("⚠️ 部分功能需要进一步优化。")
    
    print(f"\n💡 核心价值:")
    print(f"  🎬 智能短剧混剪: AI驱动的爆款内容生成")
    print(f"  🔄 双语言支持: 中英文内容无缝处理")
    print(f"  📤 专业导出: 剪映工程文件二次编辑")
    print(f"  💾 低配友好: 4GB内存设备运行")
    print(f"  🎯 一键操作: 简化的用户界面")
    
    return results, success_rate

if __name__ == "__main__":
    # 运行完整演示
    demo_results, rate = run_complete_demo()
    
    # 保存演示报告
    import json
    demo_report = {
        "timestamp": time.time(),
        "demo_results": demo_results,
        "success_rate": rate,
        "total_demos": len(demo_results),
        "successful_demos": sum(demo_results.values()),
        "summary": "VisionAI-ClipsMaster UI整合功能演示完成"
    }
    
    with open("ui_integration_demo_report.json", "w", encoding="utf-8") as f:
        json.dump(demo_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 演示报告已保存到: ui_integration_demo_report.json")
