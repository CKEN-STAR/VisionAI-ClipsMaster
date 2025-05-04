#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证沙盒模块演示

演示如何使用验证沙盒模块评估脚本质量和提供改进建议。
该模块可以检测剧情漏洞、角色一致性问题和情感流程缺陷等。
"""

import os
import sys
import json
import argparse
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入验证沙盒模块
from src.validation.sandbox import (
    validate_script,
    visualize_sandbox,
    SandboxValidator
)

# 导入示例脚本和工具
from src.utils.sample_data import get_sample_script
from src.utils.log_handler import get_logger

# 创建日志记录器
logger = get_logger("validation_sandbox_demo")

def load_demo_script(demo_type: str = "standard") -> List[Dict[str, Any]]:
    """
    加载演示脚本
    
    Args:
        demo_type: 演示脚本类型
            - standard: 标准脚本
            - problematic: 有问题的脚本
            - custom: 自定义脚本
            
    Returns:
        脚本列表
    """
    if demo_type == "standard":
        # 加载标准示例脚本
        return get_sample_script()
    
    elif demo_type == "problematic":
        # 加载有问题的脚本（故意引入一些问题）
        script = get_sample_script()
        
        # 移除中间部分场景，制造情节断点
        if len(script) > 5:
            del script[2:4]
        
        # 修改角色情感，制造情感不连贯
        for i, scene in enumerate(script):
            if i % 3 == 0 and "sentiment" in scene:
                # 翻转情感
                if scene["sentiment"]["label"] == "POSITIVE":
                    scene["sentiment"]["label"] = "NEGATIVE"
                else:
                    scene["sentiment"]["label"] = "POSITIVE"
        
        return script
    
    elif demo_type == "custom":
        # 尝试从文件加载自定义脚本
        custom_script_path = "data/input/custom_script.json"
        if os.path.exists(custom_script_path):
            try:
                with open(custom_script_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载自定义脚本失败: {e}")
        
        logger.warning("找不到自定义脚本，使用标准脚本")
        return get_sample_script()
    
    else:
        logger.warning(f"未知脚本类型: {demo_type}，使用标准脚本")
        return get_sample_script()

def analyze_script(script: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    """
    分析脚本质量
    
    Args:
        script: 待分析的脚本
        verbose: 是否输出详细信息
        
    Returns:
        分析报告
    """
    logger.info("开始分析脚本...")
    
    # 运行沙盒验证
    validator = SandboxValidator()
    report = validator.dry_run(script)
    
    # 分析结果
    if report.get("status", "") == "success":
        quality_score = report.get("quality_score", 0)
        plot_holes = report.get("plot_holes", [])
        character_problems = report.get("character_consistency", {}).get("problems", [])
        suggestions = report.get("suggestions", [])
        
        # 输出结果
        logger.info(f"分析完成! 脚本质量评分: {quality_score:.2f}/1.0")
        logger.info(f"检测到 {len(plot_holes)} 个剧情漏洞")
        logger.info(f"检测到 {len(character_problems)} 个角色一致性问题")
        logger.info(f"提供 {len(suggestions)} 条改进建议")
        
        # 详细输出
        if verbose:
            # 输出剧情漏洞
            for i, hole in enumerate(plot_holes):
                logger.info(f"漏洞 {i+1}: {hole.get('description', '')}")
            
            # 输出改进建议
            for i, suggestion in enumerate(suggestions):
                logger.info(f"建议 {i+1}: {suggestion.get('description', '')} - "
                          f"{suggestion.get('fix_suggestion', '')}")
    else:
        # 验证失败
        logger.error(f"验证失败: {report.get('message', '未知错误')}")
    
    return report

def save_report(report: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    保存分析报告
    
    Args:
        report: 分析报告
        output_path: 输出路径，如果为None则使用默认路径
    """
    if not output_path:
        # 创建输出目录
        output_dir = "reports/sandbox"
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        import time
        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_path = os.path.join(output_dir, f"sandbox_report_{timestamp}.json")
    
    # 保存报告
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存到: {output_path}")
    except Exception as e:
        logger.error(f"保存报告失败: {e}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="验证沙盒模块演示")
    parser.add_argument("--script-type", type=str, default="standard",
                        choices=["standard", "problematic", "custom"],
                        help="演示脚本类型")
    parser.add_argument("--verbose", action="store_true",
                        help="输出详细信息")
    parser.add_argument("--visualize", action="store_true",
                        help="可视化分析结果")
    parser.add_argument("--save", action="store_true",
                        help="保存分析报告")
    parser.add_argument("--output", type=str, default=None,
                        help="报告输出路径")
    args = parser.parse_args()
    
    # 加载演示脚本
    script = load_demo_script(args.script_type)
    logger.info(f"已加载 {args.script_type} 类型脚本，共 {len(script)} 个场景")
    
    # 分析脚本
    report = analyze_script(script, args.verbose)
    
    # 可视化结果
    if args.visualize:
        visualize_sandbox(report)
    
    # 保存报告
    if args.save:
        save_report(report, args.output)

if __name__ == "__main__":
    main() 