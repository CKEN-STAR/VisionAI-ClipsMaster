#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试数据初始化脚本
一键生成用于测试和开发的标准测试数据集
支持中英文测试场景
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# 导入测试数据生成模块
from tests.utils.test_data import initialize_test_data


def confirm(prompt):
    """交互式确认
    
    Args:
        prompt (str): 提示信息
        
    Returns:
        bool: 用户是否确认
    """
    valid = {"yes": True, "y": True, "no": False, "n": False}
    
    while True:
        sys.stdout.write(f"{prompt} [y/n] ")
        choice = input().lower()
        if choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("请输入 'yes'/'y' 或 'no'/'n'\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 测试数据初始化工具")
    parser.add_argument("--videos", type=int, default=3, help="每种语言生成的测试视频数量")
    parser.add_argument("--training", type=int, default=5, help="每种语言生成的训练数据对数量")
    parser.add_argument("--golden", type=int, default=2, help="每种语言生成的黄金样本数量")
    parser.add_argument("--force", action="store_true", help="强制重新生成所有测试数据")
    parser.add_argument("--clean", action="store_true", help="清空现有测试数据")
    parser.add_argument("--minimal", action="store_true", help="生成最小测试数据集（每种数据1个）")
    parser.add_argument("--quick", action="store_true", help="快速模式，所有视频限制在5秒以内")
    args = parser.parse_args()
    
    print("===== VisionAI-ClipsMaster 测试数据初始化工具 =====")
    
    # 测试数据目录
    test_data_dir = os.path.join(project_root, "data", "test")
    
    # 检查依赖
    try:
        import ffmpeg
        print("✓ ffmpeg-python 已安装")
    except ImportError:
        print("正在安装 ffmpeg-python...")
        os.system(f"{sys.executable} -m pip install ffmpeg-python")
    
    # 检查系统 ffmpeg
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✓ 系统已安装 ffmpeg")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告: 系统未安装 ffmpeg，请先安装 ffmpeg 命令行工具")
        print("  Windows: https://www.gyan.dev/ffmpeg/builds/")
        print("  macOS: brew install ffmpeg")
        print("  Linux: apt-get install ffmpeg 或 yum install ffmpeg")
        if not confirm("是否继续（可能无法生成测试视频）？"):
            sys.exit(1)
    
    # 处理清理操作
    if args.clean or args.force:
        if os.path.exists(test_data_dir):
            if args.force or confirm(f"确定要删除现有测试数据目录 {test_data_dir} 吗？"):
                print(f"正在删除测试数据目录: {test_data_dir}")
                shutil.rmtree(test_data_dir)
                print(f"✓ 已删除测试数据目录")
            else:
                print("已取消删除操作")
        else:
            print(f"测试数据目录不存在: {test_data_dir}")
    
    # 如果只是清理，不生成新数据，则退出
    if args.clean and not args.force:
        print("清理操作完成")
        return
    
    # 设置生成参数
    if args.minimal:
        videos = 1
        training = 1
        golden = 1
    else:
        videos = args.videos
        training = args.training
        golden = args.golden
    
    # 生成测试数据
    print(f"\n开始生成测试数据，参数:")
    print(f"  - 测试视频数量: {videos}个/语言")
    print(f"  - 训练数据对数量: {training}对/语言")
    print(f"  - 黄金样本数量: {golden}个/语言")
    print(f"  - 快速模式: {'已启用' if args.quick else '已禁用'}")
    print()
    
    # 导入并调用测试数据初始化函数
    try:
        from tests.utils import test_data
        
        # 临时修改视频时长（如果启用快速模式）
        if args.quick:
            # 保存原始选择
            original_choices = test_data.random.choice
            
            # 修改随机选择函数以限制视频时长
            def limited_choice(options):
                if isinstance(options, list) and isinstance(options[0], int) and max(options) > 10:
                    # 这是时长选择，限制为短时间
                    return min(options[:2])
                return original_choices(options)
            
            # 替换随机选择函数
            test_data.random.choice = limited_choice
        
        # 初始化测试数据
        test_data.initialize_test_data(
            video_count=videos,
            training_pairs=training,
            golden_samples=golden
        )
        
        # 恢复原始随机选择函数（如果有修改）
        if args.quick:
            test_data.random.choice = original_choices
            
    except ImportError as e:
        print(f"错误: 无法导入测试数据模块: {e}")
        print("请确保项目结构正确")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 测试数据生成失败: {e}")
        sys.exit(1)
    
    print("\n测试数据初始化完成!")
    print(f"数据目录: {test_data_dir}")
    print("你可以使用这些数据进行模型训练和功能测试")


if __name__ == "__main__":
    main() 