#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时间轴存档命令行工具

提供命令行界面来管理短剧混剪项目的时间轴版本。
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.timecode import TimelineArchiver

def setup_parser() -> argparse.ArgumentParser:
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="时间轴存档管理工具 - 管理短剧混剪项目的时间轴版本",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--project", "-p", type=str, required=True,
        help="项目ID"
    )
    
    parser.add_argument(
        "--storage", "-s", type=str, default=None,
        help="存储目录路径, 默认为 'data/output/timeline_versions'"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 查看版本列表命令
    list_parser = subparsers.add_parser("list", help="查看版本列表")
    list_parser.add_argument(
        "--limit", "-l", type=int, default=None,
        help="限制显示的版本数量"
    )
    list_parser.add_argument(
        "--reverse", "-r", action="store_true",
        help="反向排序(从旧到新)"
    )
    
    # 查看版本详情命令
    show_parser = subparsers.add_parser("show", help="查看版本详情")
    show_parser.add_argument(
        "version_id", type=str,
        help="要查看的版本ID"
    )
    
    # 保存版本命令
    save_parser = subparsers.add_parser("save", help="保存新版本")
    save_parser.add_argument(
        "input_file", type=str,
        help="输入的场景数据JSON文件路径"
    )
    save_parser.add_argument(
        "--note", "-n", type=str, default="",
        help="版本说明"
    )
    
    # 导出版本命令
    export_parser = subparsers.add_parser("export", help="导出版本")
    export_parser.add_argument(
        "version_id", type=str,
        help="要导出的版本ID"
    )
    export_parser.add_argument(
        "output_file", type=str,
        help="输出文件路径"
    )
    
    # 导入版本命令
    import_parser = subparsers.add_parser("import", help="导入版本")
    import_parser.add_argument(
        "input_file", type=str,
        help="要导入的版本文件路径"
    )
    import_parser.add_argument(
        "--note", "-n", type=str, default=None,
        help="版本说明(可选)"
    )
    
    # 删除版本命令
    delete_parser = subparsers.add_parser("delete", help="删除版本")
    delete_parser.add_argument(
        "version_id", type=str,
        help="要删除的版本ID"
    )
    delete_parser.add_argument(
        "--force", "-f", action="store_true",
        help="强制删除(不提示确认)"
    )
    
    # 比较版本命令
    compare_parser = subparsers.add_parser("compare", help="比较两个版本")
    compare_parser.add_argument(
        "version_id1", type=str,
        help="第一个版本ID"
    )
    compare_parser.add_argument(
        "version_id2", type=str,
        help="第二个版本ID"
    )
    
    return parser

def display_version_info(version_info: Dict) -> None:
    """格式化显示版本信息"""
    print(f"版本ID: {version_info['version_id']}")
    print(f"创建时间: {version_info['formatted_time']}")
    print(f"场景数量: {version_info['scene_count']}")
    print(f"说明: {version_info['note']}")
    print(f"当前激活版本: {'是' if version_info['is_current'] else '否'}")

def display_version_list(version_list: List[Dict]) -> None:
    """显示版本列表"""
    if not version_list:
        print("暂无版本记录")
        return
    
    print(f"\n找到 {len(version_list)} 个版本:")
    print(f"{'版本ID':<15} {'时间':<22} {'场景数':<8} {'当前':<5} {'说明'}")
    print("-" * 80)
    
    for version in version_list:
        is_current = "✓" if version["is_current"] else ""
        print(f"{version['version_id']:<15} {version['formatted_time']:<22} " +
              f"{version['scene_count']:<8} {is_current:<5} {version['note'][:30]}")

def display_scene_summary(scenes: List[Dict]) -> None:
    """显示场景摘要"""
    print(f"\n共有 {len(scenes)} 个场景:")
    
    # 检查场景数据结构
    if not scenes:
        return
    
    first_scene = scenes[0]
    headers = []
    
    # 动态确定要显示的字段
    if "id" in first_scene:
        headers.append(("ID", "id", 10, "<"))
    
    if "source_file" in first_scene:
        headers.append(("源文件", "source_file", 15, "<"))
    
    if "start_time" in first_scene and "end_time" in first_scene:
        headers.append(("开始", "start_time", 8, ">"))
        headers.append(("结束", "end_time", 8, ">"))
    
    if "duration" in first_scene:
        headers.append(("时长", "duration", 8, ">"))
    
    if "character" in first_scene:
        headers.append(("角色", "character", 8, "<"))
    
    if "emotion" in first_scene:
        headers.append(("情感", "emotion", 8, "<"))
    
    if "text" in first_scene:
        headers.append(("文本", "text", 30, "<"))
    
    # 打印表头
    header_line = ""
    for title, _, width, align in headers:
        format_str = f"{{:{align}{width}}}"
        header_line += format_str.format(title) + " "
    print(header_line)
    print("-" * 100)
    
    # 打印每个场景的信息
    for scene in scenes:
        line = ""
        for _, key, width, align in headers:
            value = scene.get(key, "")
            
            # 处理特殊类型
            if isinstance(value, float):
                value = f"{value:.1f}"
                
            # 裁剪过长的文本
            if key == "text" and len(str(value)) > width:
                value = str(value)[:width-3] + "..."
            
            format_str = f"{{:{align}{width}}}"
            line += format_str.format(str(value)) + " "
        print(line)
    
    # 如果有时长信息，显示总时长
    if "duration" in first_scene:
        total_duration = sum(scene.get("duration", 0) for scene in scenes)
        print("-" * 100)
        print(f"总时长: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")

def display_comparison(comparison: Dict) -> None:
    """显示版本比较结果"""
    print("\n版本比较:")
    print("-" * 80)
    print(f"版本 {comparison['version1']['id']} ({comparison['version1']['time']})")
    print(f"  - 场景数: {comparison['version1']['scene_count']}")
    print(f"vs")
    print(f"版本 {comparison['version2']['id']} ({comparison['version2']['time']})")
    print(f"  - 场景数: {comparison['version2']['scene_count']}")
    print("-" * 80)
    print(f"场景数量变化: {comparison['scene_diff']:+d} 个场景")
    print(f"总时长变化: {comparison['total_duration_diff']:+.1f} 秒")
    print("-" * 80)
    
def confirm_action(message: str) -> bool:
    """确认操作"""
    response = input(f"{message} (y/n): ").strip().lower()
    return response in ("y", "yes")

def command_list(args, archiver: TimelineArchiver) -> int:
    """处理列表命令"""
    version_list = archiver.get_version_list(
        limit=args.limit,
        sort_by_time=not args.reverse
    )
    display_version_list(version_list)
    return 0

def command_show(args, archiver: TimelineArchiver) -> int:
    """处理显示命令"""
    scenes = archiver.load_version(args.version_id)
    if not scenes:
        print(f"错误: 无法加载版本 {args.version_id}")
        return 1
    
    # 获取版本信息
    version_info = None
    for v in archiver.get_version_list():
        if v["version_id"] == args.version_id:
            version_info = v
            break
    
    if version_info:
        print("\n版本信息:")
        print("-" * 80)
        display_version_info(version_info)
    
    # 显示场景摘要
    display_scene_summary(scenes)
    return 0

def command_save(args, archiver: TimelineArchiver) -> int:
    """处理保存命令"""
    # 加载输入文件
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
    except Exception as e:
        print(f"错误: 无法加载输入文件 - {e}")
        return 1
    
    # 保存版本
    version_id = archiver.save_version(scenes, args.note)
    if not version_id:
        print("错误: 保存版本失败")
        return 1
    
    print(f"✓ 版本保存成功: {version_id}")
    return 0

def command_export(args, archiver: TimelineArchiver) -> int:
    """处理导出命令"""
    success = archiver.export_version(args.version_id, args.output_file)
    if not success:
        print(f"错误: 导出版本 {args.version_id} 失败")
        return 1
    
    print(f"✓ 版本导出成功: {args.output_file}")
    return 0

def command_import(args, archiver: TimelineArchiver) -> int:
    """处理导入命令"""
    version_id = archiver.import_version(args.input_file, args.note)
    if not version_id:
        print(f"错误: 导入版本失败")
        return 1
    
    print(f"✓ 版本导入成功: {version_id}")
    return 0

def command_delete(args, archiver: TimelineArchiver) -> int:
    """处理删除命令"""
    # 确认删除
    if not args.force:
        if not confirm_action(f"确定要删除版本 {args.version_id} 吗?"):
            print("操作已取消")
            return 0
    
    success = archiver.delete_version(args.version_id)
    if not success:
        print(f"错误: 删除版本 {args.version_id} 失败")
        return 1
    
    print(f"✓ 版本删除成功: {args.version_id}")
    return 0

def command_compare(args, archiver: TimelineArchiver) -> int:
    """处理比较命令"""
    comparison = archiver.compare_versions(args.version_id1, args.version_id2)
    if "error" in comparison:
        print(f"错误: {comparison['error']}")
        return 1
    
    display_comparison(comparison)
    return 0

def main() -> int:
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 创建存档器
    archiver = TimelineArchiver(args.project, args.storage)
    
    # 执行相应的命令
    commands = {
        "list": command_list,
        "show": command_show,
        "save": command_save,
        "export": command_export,
        "import": command_import,
        "delete": command_delete,
        "compare": command_compare
    }
    
    command_func = commands.get(args.command)
    if not command_func:
        print(f"错误: 未知命令 {args.command}")
        return 1
    
    return command_func(args, archiver)

if __name__ == "__main__":
    sys.exit(main()) 