#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整工作流模拟测试 - 模拟UI调用WorkflowManager
"""

import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_full_workflow():
    """测试完整工作流"""
    print("\n" + "="*60)
    print("完整工作流模拟测试")
    print("="*60)
    
    try:
        # 1. 导入WorkflowManager
        print("\n[步骤1] 导入WorkflowManager...")
        from src.core.workflow_manager import WorkflowManager
        print("✅ WorkflowManager导入成功")
        
        # 2. 准备测试文件
        video_path = "examples/sample_video.mp4"
        subtitle_path = "examples/sample_subtitle.srt"
        output_dir = "output/test_full_workflow"
        
        print(f"\n[步骤2] 检查测试文件...")
        print(f"  视频: {video_path}")
        print(f"  字幕: {subtitle_path}")
        print(f"  输出: {output_dir}")
        
        if not os.path.exists(subtitle_path):
            print(f"❌ 字幕文件不存在: {subtitle_path}")
            return False
        
        print("✅ 字幕文件存在")
        
        # 3. 创建进度回调
        progress_updates = []
        
        def progress_callback(step, total, desc):
            timestamp = datetime.now().strftime("%H:%M:%S")
            progress_updates.append((timestamp, step, total, desc))
            print(f"  [{timestamp}] 📊 进度: {step}/{total} - {desc}")
        
        print(f"\n[步骤3] 创建WorkflowManager...")
        manager = WorkflowManager(progress_callback=progress_callback)
        print("✅ WorkflowManager创建成功")
        
        # 4. 执行工作流
        print(f"\n[步骤4] 执行完整工作流...")
        print(f"  开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            result = manager.execute_full_workflow(
                video_path=video_path,
                subtitle_path=subtitle_path,
                output_dir=output_dir
            )
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            print("-" * 60)
            print(f"  结束时间: {datetime.now().strftime('%H:%M:%S')}")
            print(f"  总耗时: {elapsed:.2f}秒")
            
            print(f"\n✅ 工作流执行完成")
            print(f"  状态: {result.get('status')}")
            print(f"  进度回调次数: {len(progress_updates)}")
            
            if len(progress_updates) > 0:
                print(f"\n进度更新记录:")
                for timestamp, step, total, desc in progress_updates:
                    print(f"  [{timestamp}] {step}/{total} - {desc}")
            
            return True
            
        except Exception as e:
            end_time = time.time()
            elapsed = end_time - start_time
            
            print("-" * 60)
            print(f"  结束时间: {datetime.now().strftime('%H:%M:%S')}")
            print(f"  总耗时: {elapsed:.2f}秒")
            
            print(f"\n⚠️ 工作流执行出错: {e}")
            print(f"  进度回调次数: {len(progress_updates)}")
            
            if len(progress_updates) > 0:
                print(f"\n✅ 进度回调被触发了!")
                print(f"进度更新记录:")
                for timestamp, step, total, desc in progress_updates:
                    print(f"  [{timestamp}] {step}/{total} - {desc}")
                return True
            else:
                print(f"\n❌ 进度回调没有被触发!")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行测试"""
    print("\n" + "="*60)
    print("完整工作流模拟测试")
    print("="*60)
    
    result = test_full_workflow()
    
    # 汇总
    print("\n" + "="*60)
    print("测试结果")
    print("="*60)
    
    if result:
        print("✅ 测试通过 - 工作流可以正常执行")
    else:
        print("❌ 测试失败 - 工作流无法执行")
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())

