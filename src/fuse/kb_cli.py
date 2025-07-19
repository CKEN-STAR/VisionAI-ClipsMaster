#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
熔断知识库命令行工具
---------------
提供命令行接口访问和管理熔断知识库
支持诊断、查询、学习和导出功能
"""

import os
import sys
import argparse
import json
import logging
import time
import datetime
from typing import Dict, List, Any, Optional
import numpy as np

# 添加项目根目录到路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# 直接导入知识库，不依赖于其他模块
current_file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_file_dir)

# 导入知识库
from knowledge_base import FuseKB, get_knowledge_base
from knowledge_service import KnowledgeService, get_knowledge_service

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fuse_kb_cli")


def setup_parser() -> argparse.ArgumentParser:
    """
    设置命令行参数解析器
    
    Returns:
        参数解析器
    """
    parser = argparse.ArgumentParser(
        description="熔断知识库命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  查看知识库统计:
    python kb_cli.py stats
    
  查询当前系统状态:
    python kb_cli.py diagnose
    
  查询特定案例:
    python kb_cli.py case OOM_001
    
  添加自定义案例:
    python kb_cli.py learn --file case_data.json
    
  导出知识库:
    python kb_cli.py export --output kb_backup.json
"""
    )
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # stats命令 - 显示知识库统计
    stats_parser = subparsers.add_parser("stats", help="显示知识库统计信息")
    
    # diagnose命令 - 诊断当前状态
    diagnose_parser = subparsers.add_parser("diagnose", help="诊断当前系统状态")
    diagnose_parser.add_argument("--file", help="从文件加载内存压力数据进行诊断")
    diagnose_parser.add_argument("--test", action="store_true", help="使用测试数据进行诊断")
    
    # case命令 - 查询案例
    case_parser = subparsers.add_parser("case", help="查询案例详情")
    case_parser.add_argument("case_id", help="案例ID")
    
    # list命令 - 列出所有案例
    list_parser = subparsers.add_parser("list", help="列出所有案例")
    list_parser.add_argument("--type", help="按类型筛选 (OOM/FRAG/LEAK/CONT/CONF)")
    
    # learn命令 - 学习新案例
    learn_parser = subparsers.add_parser("learn", help="添加学习案例")
    learn_parser.add_argument("--file", required=True, help="案例数据JSON文件")
    
    # export命令 - 导出知识库
    export_parser = subparsers.add_parser("export", help="导出知识库")
    export_parser.add_argument("--output", help="输出文件路径")
    
    # 查看历史诊断
    history_parser = subparsers.add_parser("history", help="查看历史诊断结果")
    history_parser.add_argument("--count", type=int, default=5, help="显示的结果数量")
    
    return parser


def format_severity(severity: str) -> str:
    """
    为严重等级添加颜色标记（适用于支持ANSI颜色的终端）
    
    Args:
        severity: 严重等级
        
    Returns:
        带颜色的严重等级字符串
    """
    if severity == "critical":
        return "\033[1;31m严重\033[0m"
    elif severity == "high":
        return "\033[31m高危\033[0m"
    elif severity == "medium":
        return "\033[33m中等\033[0m"
    elif severity == "low":
        return "\033[32m低危\033[0m"
    else:
        return severity


def print_diagnosis_result(result: Dict[str, Any]):
    """
    打印诊断结果
    
    Args:
        result: 诊断结果字典
    """
    if not result:
        print("无诊断结果")
        return
        
    print("\n" + "="*50)
    print(f"诊断ID: {result.get('diagnosis_id', 'N/A')}")
    print(f"时间: {result.get('timestamp', 'N/A')}")
    print(f"匹配案例: {result.get('matched_case', 'N/A')}")
    print(f"置信度: {result.get('confidence', 0)*100:.1f}%")
    print(f"严重等级: {format_severity(result.get('severity', 'unknown'))}")
    print("-"*50)
    print(f"根本原因: {result.get('root_cause', 'N/A')}")
    print(f"解决方案: {result.get('solution', 'N/A')}")
    
    if "impact" in result and result["impact"]:
        print("可能影响:")
        for impact in result["impact"]:
            print(f"  - {impact}")
            
    if "similar_cases" in result and result["similar_cases"]:
        print("相似案例:")
        for case_id in result["similar_cases"]:
            print(f"  - {case_id}")
    
    print("="*50)


def print_case_details(case: Dict[str, Any], case_id: str):
    """
    打印案例详情
    
    Args:
        case: 案例数据字典
        case_id: 案例ID
    """
    if not case:
        print(f"案例 {case_id} 不存在")
        return
        
    print("\n" + "="*50)
    print(f"案例ID: {case_id}")
    print(f"症状: {case.get('symptoms', 'N/A')}")
    print(f"模式: {case.get('pattern', 'N/A')}")
    print(f"严重等级: {format_severity(case.get('severity', 'unknown'))}")
    print("-"*50)
    print(f"根本原因: {case.get('root_cause', 'N/A')}")
    print(f"解决方案: {case.get('solution', 'N/A')}")
    
    if "impact" in case and case["impact"]:
        print("可能影响:")
        for impact in case["impact"]:
            print(f"  - {impact}")
            
    if "detection" in case and case["detection"]:
        print(f"检测规则: {case['detection']}")
        
    if "source" in case and case["source"]:
        print(f"知识来源: {case['source']}")
        
    print("="*50)


def load_json_data(file_path: str) -> Any:
    """
    从JSON文件加载数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        加载的数据或None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {e}")
        return None


def handle_stats_command():
    """处理stats命令"""
    service = get_knowledge_service()
    stats = service.get_knowledge_stats()
    
    kb_stats = stats.get("knowledge_base", {})
    service_stats = stats.get("service", {})
    
    print("\n=== 熔断知识库统计 ===")
    print(f"总案例数: {kb_stats.get('total_cases', 0)}")
    
    if "case_types" in kb_stats:
        print("按类型统计:")
        for type_name, count in kb_stats["case_types"].items():
            print(f"  - {type_name}: {count}案例")
            
    print(f"诊断次数: {kb_stats.get('diagnosis_count', 0)}")
    
    if "top_matched_cases" in kb_stats:
        print("常匹配案例:")
        for case_id, count in kb_stats["top_matched_cases"].items():
            print(f"  - {case_id}: 匹配{count}次")
            
    print("\n=== 知识库服务状态 ===")
    print(f"自动诊断: {'启用' if service_stats.get('auto_diagnosis', False) else '禁用'}")
    print(f"诊断间隔: {service_stats.get('diagnosis_interval', 0)}秒")
    print(f"自动学习: {'启用' if service_stats.get('auto_learning', False) else '禁用'}")
    print(f"最近诊断: {service_stats.get('recent_diagnoses_count', 0)}次")


def handle_diagnose_command(args):
    """
    处理diagnose命令
    
    Args:
        args: 命令行参数
    """
    service = get_knowledge_service()
    
    if args.file:
        # 从文件加载数据进行诊断
        data = load_json_data(args.file)
        if not data:
            print(f"无法从 {args.file} 加载数据")
            return
            
        result = service.diagnose_custom(data)
        print_diagnosis_result(result)
        
    elif args.test:
        # 使用测试数据进行诊断
        print("使用测试数据进行诊断...")
        test_data = np.array([30, 35, 42, 55, 70, 82, 95])
        test_info = {"uptime_hours": 24, "task_type": "video_processing"}
        
        result = service.diagnose_custom(test_data, test_info)
        print_diagnosis_result(result)
        
    else:
        # 诊断当前系统状态
        print("诊断当前系统状态...")
        result = service.diagnose_current_state()
        
        if result:
            print_diagnosis_result(result)
        else:
            print("无法诊断当前系统状态，请确保熔断相关组件已正确配置")
            print("提示: 您可以使用 --test 参数测试知识库功能")


def handle_case_command(args):
    """
    处理case命令
    
    Args:
        args: 命令行参数
    """
    kb = get_knowledge_base()
    case = kb.get_case(args.case_id)
    print_case_details(case, args.case_id)


def handle_list_command(args):
    """
    处理list命令
    
    Args:
        args: 命令行参数
    """
    kb = get_knowledge_base()
    
    # 获取所有案例
    all_cases = kb.cases
    
    # 按类型过滤
    if args.type:
        filtered_cases = {
            case_id: case for case_id, case in all_cases.items()
            if case_id.startswith(args.type)
        }
    else:
        filtered_cases = all_cases
    
    if not filtered_cases:
        print(f"没有找到{args.type + '类型的' if args.type else ''}案例")
        return
        
    # 按类型分组
    cases_by_type = {}
    for case_id, case in filtered_cases.items():
        type_id = case_id.split("_")[0]
        if type_id not in cases_by_type:
            cases_by_type[type_id] = []
        cases_by_type[type_id].append((case_id, case))
    
    # 打印结果
    print(f"\n找到 {len(filtered_cases)} 个{args.type + '类型的' if args.type else ''}案例:")
    
    for type_id, cases in cases_by_type.items():
        print(f"\n--- {type_id} 类型 ({len(cases)}个) ---")
        for case_id, case in cases:
            print(f"{case_id:10} | {format_severity(case.get('severity', 'unknown')):10} | {case.get('symptoms', 'N/A')[:50]}")


def handle_learn_command(args):
    """
    处理learn命令
    
    Args:
        args: 命令行参数
    """
    service = get_knowledge_service()
    
    # 加载案例数据
    case_data = load_json_data(args.file)
    if not case_data:
        print(f"无法从 {args.file} 加载案例数据")
        return
    
    # 处理单个案例或案例列表
    if isinstance(case_data, list):
        success_count = 0
        for case in case_data:
            success = service.add_learned_case(case)
            if success:
                success_count += 1
        
        print(f"成功添加 {success_count}/{len(case_data)} 个学习案例")
        
    else:
        # 单个案例
        success = service.add_learned_case(case_data)
        if success:
            print("成功添加学习案例")
        else:
            print("添加学习案例失败，请检查数据格式和必填字段")


def handle_export_command(args):
    """
    处理export命令
    
    Args:
        args: 命令行参数
    """
    service = get_knowledge_service()
    output_path = args.output
    
    # 导出知识库
    file_path = service.export_knowledge(output_path)
    
    if file_path:
        print(f"知识库已成功导出到: {file_path}")
    else:
        print("导出知识库失败")


def handle_history_command(args):
    """
    处理history命令
    
    Args:
        args: 命令行参数
    """
    service = get_knowledge_service()
    count = args.count
    
    # 获取历史诊断结果
    history = service.get_recent_diagnoses(count)
    
    if not history:
        print("没有历史诊断记录")
        return
        
    print(f"\n最近 {len(history)} 次诊断结果:")
    
    for i, result in enumerate(history):
        print(f"\n--- 诊断 {i+1} ---")
        print(f"时间: {result.get('timestamp', 'N/A')}")
        print(f"匹配案例: {result.get('matched_case', 'N/A')}")
        print(f"置信度: {result.get('confidence', 0)*100:.1f}%")
        print(f"根本原因: {result.get('root_cause', 'N/A')}")
        print(f"严重等级: {format_severity(result.get('severity', 'unknown'))}")


def main():
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()
    
    # 处理命令
    if args.command == "stats":
        handle_stats_command()
    elif args.command == "diagnose":
        handle_diagnose_command(args)
    elif args.command == "case":
        handle_case_command(args)
    elif args.command == "list":
        handle_list_command(args)
    elif args.command == "learn":
        handle_learn_command(args)
    elif args.command == "export":
        handle_export_command(args)
    elif args.command == "history":
        handle_history_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        logger.error(f"出错: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1) 