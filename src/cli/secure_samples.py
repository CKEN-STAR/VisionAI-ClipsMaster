#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
黄金样本安全管理工具

提供命令行接口，用于管理黄金样本的安全访问，包括:
1. 设置安全权限
2. 验证黄金样本完整性
3. 查看安全审计日志
4. 配置Git安全属性
"""

import os
import sys
import argparse
import textwrap
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 导入安全模块
from src.security import (
    get_access_control,
    secure_golden_samples,
    verify_golden_samples_integrity,
    get_audit_logger
)

def print_header(title):
    """打印带格式的标题"""
    width = len(title) + 4
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")

def secure_samples_cmd(args):
    """设置黄金样本安全权限"""
    print_header("设置黄金样本安全权限")
    
    result = secure_golden_samples(force=args.force)
    
    if result:
        print("✓ 黄金样本目录权限设置成功")
    else:
        print("✗ 黄金样本目录权限设置失败")
        sys.exit(1)
        
    # 如果需要配置Git属性
    if args.git_config:
        ac = get_access_control()
        if ac.configure_git_attributes():
            print("✓ Git安全属性配置成功")
        else:
            print("✗ Git安全属性配置失败")

def verify_samples_cmd(args):
    """验证黄金样本完整性"""
    print_header("验证黄金样本完整性")
    
    success, errors = verify_golden_samples_integrity()
    
    if success:
        print("✓ 黄金样本完整性验证通过")
    else:
        print("✗ 黄金样本完整性验证失败，发现以下问题:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        
        if not args.ignore_errors:
            sys.exit(1)

def view_logs_cmd(args):
    """查看安全审计日志"""
    print_header("安全审计日志")
    
    # 获取审计日志记录器
    audit_logger = get_audit_logger()
    
    # 获取最近的事件
    events = audit_logger.get_recent_events(limit=args.limit)
    
    if not events:
        print("没有找到安全事件记录")
        return
    
    # 打印事件
    print(f"最近 {len(events)} 条安全事件:\n")
    
    for i, event in enumerate(events, 1):
        timestamp = event.get('timestamp', 'N/A')
        event_type = event.get('event_type', 'N/A')
        description = event.get('description', 'N/A')
        user = event.get('user', 'N/A')
        
        print(f"{i}. [{timestamp}] {event_type} - {description}")
        print(f"   用户: {user}")
        
        # 显示详情
        if args.verbose and 'details' in event:
            details = event['details']
            for k, v in details.items():
                print(f"   ├─ {k}: {v}")
        
        print()

def install_hooks_cmd(args):
    """安装Git钩子"""
    print_header("安装Git安全钩子")
    
    # 导入Git钩子安装模块
    sys.path.append(str(project_root / 'scripts'))
    
    try:
        import install_git_hooks
        install_git_hooks.main()
    except Exception as e:
        print(f"✗ 安装Git钩子失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="VisionAI-ClipsMaster 黄金样本安全管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        示例:
          python -m src.cli.secure_samples secure --force
          python -m src.cli.secure_samples verify
          python -m src.cli.secure_samples logs --limit 10 --verbose
          python -m src.cli.secure_samples hooks
        """)
    )
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 设置安全权限命令
    secure_parser = subparsers.add_parser('secure', help='设置黄金样本安全权限')
    secure_parser.add_argument('--force', action='store_true', help='强制修改权限')
    secure_parser.add_argument('--git-config', action='store_true', help='配置Git安全属性')
    secure_parser.set_defaults(func=secure_samples_cmd)
    
    # 验证完整性命令
    verify_parser = subparsers.add_parser('verify', help='验证黄金样本完整性')
    verify_parser.add_argument('--ignore-errors', action='store_true', help='忽略验证错误')
    verify_parser.set_defaults(func=verify_samples_cmd)
    
    # 查看日志命令
    logs_parser = subparsers.add_parser('logs', help='查看安全审计日志')
    logs_parser.add_argument('--limit', type=int, default=20, help='显示事件数量限制')
    logs_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    logs_parser.set_defaults(func=view_logs_cmd)
    
    # 安装Git钩子命令
    hooks_parser = subparsers.add_parser('hooks', help='安装Git安全钩子')
    hooks_parser.set_defaults(func=install_hooks_cmd)
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行子命令
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 