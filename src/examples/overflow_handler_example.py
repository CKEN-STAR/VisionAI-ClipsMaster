#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常溢出处理模块示例

此示例展示如何使用异常溢出处理模块处理场景时长溢出的情况，包括：
1. 基本溢出处理示例
2. 不同处理模式的比较
3. 处理大幅溢出的情况
4. 与其他时间码处理模块的集成
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入溢出处理器
from timecode.overflow_handler import (
    OverflowRescuer,
    handle_overflow, 
    sum_duration,
    RescueMode,
    CriticalOverflowError
)

# 导入可视化模块(如果已实现)
try:
    from timecode.live_preview import PreviewGenerator, generate_timeline_preview
    visualization_available = True
except ImportError:
    visualization_available = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("溢出处理示例")


def create_test_scenes(total_duration: float = 150.0, target_duration: float = 120.0) -> List[Dict[str, Any]]:
    """创建测试场景数据
    
    Args:
        total_duration: 总时长
        target_duration: 目标时长
        
    Returns:
        场景列表
    """
    # 场景比例配置
    scene_config = [
        {"type": "opening", "ratio": 0.1, "importance": 0.95},
        {"type": "introduction", "ratio": 0.15, "importance": 0.7},
        {"type": "development", "ratio": 0.3, "importance": 0.5},
        {"type": "climax", "ratio": 0.25, "importance": 0.9},
        {"type": "resolution", "ratio": 0.15, "importance": 0.65},
        {"type": "ending", "ratio": 0.05, "importance": 0.8}
    ]
    
    scenes = []
    start_time = 0
    
    for i, config in enumerate(scene_config):
        duration = total_duration * config["ratio"]
        end_time = start_time + duration
        
        scene = {
            "id": f"scene_{i+1}",
            "type": config["type"],
            "start": start_time,
            "end": end_time,
            "duration": duration,
            "importance_score": config["importance"],
            "tags": [config["type"]]
        }
        
        if config["type"] in ["opening", "climax", "ending"]:
            scene["tags"].append("critical")
            
        scenes.append(scene)
        start_time = end_time
        
    logger.info(f"创建了 {len(scenes)} 个测试场景，总时长: {sum_duration(scenes):.1f}秒")
    
    return scenes


def demo_basic_overflow_handling():
    """基本溢出处理示例"""
    logger.info("=== 基本溢出处理示例 ===")
    
    # 创建测试场景，总时长150秒，目标120秒
    scenes = create_test_scenes(150.0, 120.0)
    target_duration = 120.0
    
    # 打印原始场景信息
    logger.info(f"原始场景总时长: {sum_duration(scenes):.1f}秒，目标时长: {target_duration:.1f}秒")
    logger.info(f"溢出量: {sum_duration(scenes) - target_duration:.1f}秒")
    
    # 处理溢出
    try:
        adjusted_scenes = handle_overflow(scenes, target_duration)
        
        # 打印结果
        logger.info(f"处理后场景总时长: {sum_duration(adjusted_scenes):.1f}秒")
        
        # 打印每个场景的调整情况
        for i, scene in enumerate(adjusted_scenes):
            original = scene.get("_original_duration", 0)
            adjusted = scene.get("duration", 0)
            level = scene.get("_importance_level", "unknown")
            ratio = adjusted / original if original > 0 else 0
            
            logger.info(f"场景 {i+1} ({scene['type']}): {original:.1f}秒 -> {adjusted:.1f}秒 "
                      f"({ratio:.0%}), 重要性: {level}")
            
        # 可视化结果(如果可用)
        if visualization_available:
            _visualize_results(scenes, adjusted_scenes, target_duration)
            
    except CriticalOverflowError as e:
        logger.error(f"处理失败: {e}")


def demo_different_modes():
    """不同处理模式比较示例"""
    logger.info("\n=== 不同处理模式比较 ===")
    
    # 创建测试场景，总时长135秒，目标120秒
    scenes = create_test_scenes(135.0, 120.0)
    target_duration = 120.0
    
    modes = ["soft", "moderate", "aggressive"]
    results = {}
    
    logger.info(f"原始场景总时长: {sum_duration(scenes):.1f}秒，目标时长: {target_duration:.1f}秒")
    
    # 使用不同模式处理
    for mode in modes:
        try:
            adjusted = handle_overflow(scenes, target_duration, mode=mode)
            results[mode] = adjusted
            
            logger.info(f"模式 {mode}: 处理后总时长 {sum_duration(adjusted):.1f}秒")
            
            # 计算各重要性级别场景的压缩比例
            compression_by_level = {}
            
            for scene in adjusted:
                level = scene.get("_importance_level", "unknown")
                original = scene.get("_original_duration", 0)
                adjusted_duration = scene.get("duration", 0)
                
                if level not in compression_by_level:
                    compression_by_level[level] = {"original": 0, "adjusted": 0}
                    
                compression_by_level[level]["original"] += original
                compression_by_level[level]["adjusted"] += adjusted_duration
                
            # 打印压缩比例
            for level, data in compression_by_level.items():
                original = data["original"]
                adjusted = data["adjusted"]
                ratio = adjusted / original if original > 0 else 0
                
                logger.info(f"  {level} 场景: {original:.1f}秒 -> {adjusted:.1f}秒 ({ratio:.0%})")
                
        except CriticalOverflowError as e:
            logger.error(f"模式 {mode} 处理失败: {e}")
    
    # 可视化比较结果(如果可用)
    if visualization_available and len(results) > 0:
        _visualize_mode_comparison(scenes, results, target_duration)


def demo_extreme_overflow():
    """处理大幅溢出示例"""
    logger.info("\n=== 处理大幅溢出示例 ===")
    
    # 创建严重溢出的测试场景
    scenes = create_test_scenes(200.0, 100.0)
    target_duration = 100.0
    
    logger.info(f"原始场景总时长: {sum_duration(scenes):.1f}秒，目标时长: {target_duration:.1f}秒")
    logger.info(f"溢出量: {sum_duration(scenes) - target_duration:.1f}秒 ({(sum_duration(scenes) - target_duration) / sum_duration(scenes):.0%})")
    
    # 尝试处理极端溢出
    try:
        adjusted_scenes = handle_overflow(scenes, target_duration)
        
        logger.info(f"处理后场景总时长: {sum_duration(adjusted_scenes):.1f}秒")
        
        # 打印各场景类型的压缩情况
        scene_types = {}
        for scene in adjusted_scenes:
            scene_type = scene.get("type", "unknown")
            original = scene.get("_original_duration", 0)
            adjusted = scene.get("duration", 0)
            
            if scene_type not in scene_types:
                scene_types[scene_type] = {"original": 0, "adjusted": 0}
                
            scene_types[scene_type]["original"] += original
            scene_types[scene_type]["adjusted"] += adjusted
            
        for stype, data in scene_types.items():
            original = data["original"]
            adjusted = data["adjusted"]
            ratio = adjusted / original if original > 0 else 0
            
            logger.info(f"{stype} 类型场景: {original:.1f}秒 -> {adjusted:.1f}秒 ({ratio:.0%})")
            
    except CriticalOverflowError as e:
        logger.error(f"处理失败: {e}")
        
        # 尝试增加目标时长
        new_target = target_duration * 1.2
        logger.info(f"尝试增加目标时长至 {new_target:.1f}秒")
        
        try:
            adjusted_scenes = handle_overflow(scenes, new_target)
            logger.info(f"调整目标后处理成功: {sum_duration(adjusted_scenes):.1f}秒")
        except CriticalOverflowError as e:
            logger.error(f"依然无法处理: {e}")


def demo_integration():
    """与其他模块集成示例"""
    logger.info("\n=== 与其他模块集成示例 ===")
    
    try:
        # 尝试导入其他时间码处理模块
        from timecode.safety_margin import MarginKeeper, apply_safety_margin
        from timecode.smart_compressor import SmartCompressor
        
        logger.info("演示与安全余量管理器集成")
        
        # 创建测试场景
        scenes = create_test_scenes(140.0, 120.0)
        raw_target = 120.0
        
        # 应用安全余量
        margin_ratio = 0.05  # 5%安全余量
        adjusted_target = apply_safety_margin(raw_target, margin_ratio)
        
        logger.info(f"原始目标: {raw_target:.1f}秒，应用{margin_ratio:.0%}安全余量后: {adjusted_target:.1f}秒")
        logger.info(f"原始场景总时长: {sum_duration(scenes):.1f}秒")
        
        # 处理溢出
        try:
            adjusted_scenes = handle_overflow(scenes, adjusted_target)
            logger.info(f"处理后总时长: {sum_duration(adjusted_scenes):.1f}秒")
            
            # 检查是否满足原始目标
            if sum_duration(adjusted_scenes) <= raw_target:
                logger.info("✓ 最终结果满足原始目标时长要求")
            else:
                logger.warning(f"! 最终结果超出原始目标 {sum_duration(adjusted_scenes) - raw_target:.1f}秒")
                
        except CriticalOverflowError as e:
            logger.error(f"处理失败: {e}")
            
    except ImportError as e:
        logger.warning(f"无法导入其他模块: {e}")
        logger.info("请确保已实现相关模块")


def _visualize_results(original_scenes, adjusted_scenes, target_duration):
    """可视化处理结果"""
    if not visualization_available:
        return
        
    try:
        # 创建简化版的比较可视化，避免使用不存在的方法
        preview = PreviewGenerator()
        
        # 准备HTML内容
        html_content = f"""
        <h2>溢出处理效果比较</h2>
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div style="width: 100%;">
                <h3>原始场景 (总时长: {sum_duration(original_scenes):.1f}秒)</h3>
                {_generate_scenes_table(original_scenes)}
            </div>
            <div style="width: 100%;">
                <h3>调整后场景 (总时长: {sum_duration(adjusted_scenes):.1f}秒，目标: {target_duration}秒)</h3>
                {_generate_scenes_table(adjusted_scenes, True)}
            </div>
        </div>
        """
        
        # 保存到文件
        filename = f"overflow_handling_result_{datetime.now().strftime('%H%M%S')}.html"
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
            f.write(preview.wrap_html_content(html_content, "溢出处理效果比较"))
            
        logger.info(f"可视化结果已保存至 {filename}")
        
    except Exception as e:
        logger.error(f"生成可视化时出错: {e}")


def _visualize_mode_comparison(original_scenes, mode_results, target_duration):
    """可视化不同模式的比较结果"""
    if not visualization_available:
        return
        
    try:
        # 创建简化版的多模式比较可视化
        preview = PreviewGenerator()
        
        # 准备HTML内容
        html_content = f"""
        <h2>不同处理模式效果比较</h2>
        <div style="display: flex; flex-direction: column; gap: 30px;">
            <div style="width: 100%;">
                <h3>原始场景 (总时长: {sum_duration(original_scenes):.1f}秒，目标: {target_duration}秒)</h3>
                {_generate_scenes_table(original_scenes)}
            </div>
        """
        
        # 为每种模式添加表格
        for mode, scenes in mode_results.items():
            compression_ratio = sum_duration(scenes) / sum_duration(original_scenes)
            html_content += f"""
            <div style="width: 100%;">
                <h3>{mode} 模式 (总时长: {sum_duration(scenes):.1f}秒，压缩比: {compression_ratio:.0%})</h3>
                {_generate_scenes_table(scenes, True)}
            </div>
            """
        
        html_content += "</div>"
        
        # 保存到文件
        filename = f"overflow_modes_comparison_{datetime.now().strftime('%H%M%S')}.html"
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
            f.write(preview.wrap_html_content(html_content, "溢出处理模式比较"))
            
        logger.info(f"模式比较可视化已保存至 {filename}")
        
    except Exception as e:
        logger.error(f"生成可视化时出错: {e}")


def _generate_scenes_table(scenes, show_adjustment=False):
    """生成场景数据的HTML表格
    
    Args:
        scenes: 场景列表
        show_adjustment: 是否显示调整信息
        
    Returns:
        HTML表格代码
    """
    # 表头
    html = """
    <table style="width: 100%; border-collapse: collapse; text-align: left;">
        <thead>
            <tr style="background-color: #f8f8f8;">
                <th style="padding: 8px; border: 1px solid #ddd;">ID</th>
                <th style="padding: 8px; border: 1px solid #ddd;">类型</th>
                <th style="padding: 8px; border: 1px solid #ddd;">时长(秒)</th>
                <th style="padding: 8px; border: 1px solid #ddd;">重要性</th>
    """
    
    if show_adjustment:
        html += """
                <th style="padding: 8px; border: 1px solid #ddd;">原始时长</th>
                <th style="padding: 8px; border: 1px solid #ddd;">压缩比例</th>
        """
        
    html += """
            </tr>
        </thead>
        <tbody>
    """
    
    # 数据行
    for i, scene in enumerate(scenes):
        # 获取重要性级别的颜色
        level = scene.get("_importance_level", "")
        level_color = {
            "critical": "#ffcccc",  # 浅红色
            "high": "#ffffcc",      # 浅黄色
            "medium": "#ccffcc",    # 浅绿色
            "low": "#ccccff"        # 浅蓝色
        }.get(level, "#ffffff")     # 默认白色
        
        html += f"""
            <tr style="background-color: {level_color};">
                <td style="padding: 8px; border: 1px solid #ddd;">{scene.get('id', f'场景{i+1}')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{scene.get('type', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{scene.get('duration', 0):.1f}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{scene.get('importance_score', 0):.2f} ({level})</td>
        """
        
        if show_adjustment and "_original_duration" in scene:
            original = scene.get("_original_duration", 0)
            current = scene.get("duration", 0)
            ratio = current / original if original > 0 else 1.0
            
            html += f"""
                <td style="padding: 8px; border: 1px solid #ddd;">{original:.1f}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ratio:.0%}</td>
            """
            
        html += "</tr>"
        
    html += """
        </tbody>
    </table>
    """
    
    return html


def main():
    """主函数"""
    # 设置命令行参数解析
    import argparse
    parser = argparse.ArgumentParser(description="异常溢出处理示例")
    parser.add_argument("--demo", choices=["basic", "modes", "extreme", "integration", "all"], 
                        default="all", help="要运行的示例类型")
    
    args = parser.parse_args()
    
    # 根据参数运行相应示例
    if args.demo in ["basic", "all"]:
        demo_basic_overflow_handling()
        
    if args.demo in ["modes", "all"]:
        demo_different_modes()
        
    if args.demo in ["extreme", "all"]:
        demo_extreme_overflow()
        
    if args.demo in ["integration", "all"]:
        demo_integration()


if __name__ == "__main__":
    main() 