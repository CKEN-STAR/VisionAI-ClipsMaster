#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
叙事引擎演示脚本

演示如何使用叙事引擎对剧本进行分析和不同结构的重构
"""

import sys
import os
import json
from pathlib import Path

# 将项目根目录添加到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.narrative.narrative_engine import (
    NarrativeEngine, 
    PlotStructure,
    remix_plot
)

# 示例剧本
SAMPLE_SCRIPT = """
场景1：城市街道 - 白天
ALEX (25岁) 匆忙走在繁忙的街道上，手机突然响起。

ALEX
(看着手机)
又是推销电话...

ALEX挂断电话，继续走路，但脸上露出思考的表情。

场景2：办公室 - 下午
ALEX坐在办公桌前，盯着电脑屏幕。他的同事MAYA (28岁) 走过来。

MAYA
嘿，你还好吧？看起来心事重重。

ALEX
(揉眼睛)
没什么，只是...我总觉得生活缺了点什么。

MAYA
(微笑)
也许是时候尝试些新事物了。

场景3：公园 - 傍晚
ALEX独自坐在公园长椅上，望着夕阳。一只小狗跑到他脚边。

狗主人LISA (27岁) 跟着跑过来。

LISA
对不起！他太兴奋了。

ALEX
(微笑，摸了摸狗)
没关系，他很可爱。

LISA和ALEX相视而笑。

场景4：咖啡馆 - 次日上午
ALEX和LISA坐在一起喝咖啡，轻松交谈。

ALEX (旁白)
有时候，生活会在你最不经意的时刻，给你一个转机。

【剧终】
"""

def demo_narrative_engine():
    """演示叙事引擎的基本用法"""
    print("=" * 50)
    print("叙事引擎演示")
    print("=" * 50)
    
    # 初始化引擎
    engine = NarrativeEngine()
    
    # 分析剧本
    print("\n1. 分析剧本:")
    analysis = engine.analyze_script(SAMPLE_SCRIPT)
    print(f"- 剧本长度: {analysis['length']} 字符")
    print(f"- 场景数量: {analysis['scene_count']}")
    
    # 使用不同结构重构剧本
    print("\n2. 使用不同叙事结构重构剧本:")
    
    # 线性结构 (保持原有顺序)
    print("\n2.1 线性结构:")
    linear_result = engine.remix_plot(SAMPLE_SCRIPT, PlotStructure.LINEAR)
    print_summary(linear_result)
    
    # 非线性结构 (如倒叙、插叙)
    print("\n2.2 非线性结构:")
    nonlinear_result = engine.remix_plot(SAMPLE_SCRIPT, "nonlinear")
    print_summary(nonlinear_result)
    
    # 平行结构 (多线并行)
    print("\n2.3 平行结构:")
    parallel_result = engine.remix_plot(SAMPLE_SCRIPT, "平行")
    print_summary(parallel_result)
    
    # 环形结构 (首尾呼应)
    print("\n2.4 环形结构:")
    circular_result = engine.remix_plot(SAMPLE_SCRIPT, PlotStructure.CIRCULAR)
    print_summary(circular_result)
    
    # 嵌套结构 (故事中的故事)
    print("\n2.5 嵌套结构:")
    nested_result = engine.remix_plot(SAMPLE_SCRIPT, "nested")
    print_summary(nested_result)
    
    # 分支结构 (多种结局)
    print("\n2.6 分支结构:")
    branching_result = engine.remix_plot(SAMPLE_SCRIPT, "分支")
    print_summary(branching_result)
    
    # 使用便捷函数
    print("\n3. 使用便捷函数:")
    custom_result = remix_plot(SAMPLE_SCRIPT, "非线性", intensity=0.8, preserve_emotions=True)
    print_summary(custom_result)
    
    print("\n4. 自动选择最佳结构:")
    auto_result = engine.remix_plot(SAMPLE_SCRIPT)  # 不指定结构，自动选择
    print(f"- 自动选择的结构: {auto_result['structure_type']}")
    print(f"- 结构描述: {auto_result['metadata']['structure_description']}")
    
    print("\n演示完成!")

def print_summary(result):
    """打印重构结果摘要"""
    print(f"- 结构类型: {result['structure_type']}")
    print(f"- 原始长度: {result['original_length']} 行")
    print(f"- 重构后长度: {result['remixed_length']} 行")
    print(f"- 结构描述: {result['metadata']['structure_description']}")
    
    # 打印前几行预览
    preview_lines = 5
    if len(result['remixed_content']) > 0:
        print(f"\n内容预览 (前 {preview_lines} 行):")
        for i, line in enumerate(result['remixed_content'][:preview_lines]):
            if line.strip():  # 只打印非空行
                print(f"  {line}")
        print("  ...")

def save_results_to_file():
    """将不同结构的重构结果保存到文件"""
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    engine = NarrativeEngine()
    
    # 所有结构类型
    structures = [
        "linear", "nonlinear", "parallel", "circular", "nested", "branching"
    ]
    
    # 为每种结构生成重构并保存
    for structure in structures:
        result = engine.remix_plot(SAMPLE_SCRIPT, structure)
        
        # 保存完整内容
        content_file = output_dir / f"{structure}_remix.txt"
        with open(content_file, "w", encoding="utf-8") as f:
            f.write("\n".join(result["remixed_content"]))
        
        # 保存元数据
        meta_file = output_dir / f"{structure}_metadata.json"
        metadata = {
            "structure_type": result["structure_type"],
            "original_length": result["original_length"],
            "remixed_length": result["remixed_length"],
            "structure_description": result["metadata"]["structure_description"]
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"所有重构结果已保存到 {output_dir} 目录")

if __name__ == "__main__":
    # 如果带--save参数，则保存结果到文件
    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        save_results_to_file()
    else:
        demo_narrative_engine() 