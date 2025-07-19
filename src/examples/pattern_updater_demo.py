"""
模式实时更新器演示

演示如何使用PatternUpdater组件处理实时模式更新
"""

import json
import random
from typing import List, Dict, Any

from src.core.pattern_updater import PatternUpdater
from loguru import logger


def generate_sample_hit_data(num_samples: int = 5) -> List[Dict[str, Any]]:
    """生成示例命中数据"""
    hit_data = []
    
    # 示例SRT模板
    origin_srt_template = """1
00:00:01,000 --> 00:00:04,000
这是原始字幕的第一行文本

2
00:00:05,000 --> 00:00:08,000
这是原始字幕的第二行文本

3
00:00:09,000 --> 00:00:12,000
这是原始字幕的第三行文本
"""
    
    hit_srt_template = """1
00:00:01,000 --> 00:00:04,000
这是命中字幕的第一行文本

2
00:00:05,000 --> 00:00:08,000
这是命中字幕的第二行文本，效果更好

3
00:00:09,000 --> 00:00:12,000
这是命中字幕的第三行文本，更吸引人
"""
    
    # 生成不同变体
    for i in range(num_samples):
        # 在模板基础上添加随机变化
        origin_lines = origin_srt_template.split("\n")
        hit_lines = hit_srt_template.split("\n")
        
        # 随机修改部分文本
        for j in range(len(origin_lines)):
            if "文本" in origin_lines[j]:
                if random.random() < 0.3:
                    # 添加一些随机词汇
                    words = ["精彩", "有趣", "引人注目", "令人惊讶", "动人", "感人"]
                    random_word = random.choice(words)
                    origin_lines[j] += f"，{random_word}"
        
        for j in range(len(hit_lines)):
            if "文本" in hit_lines[j]:
                if random.random() < 0.7:  # 命中版本更可能有修改
                    # 添加一些更吸引人的词汇
                    words = ["非常精彩", "极其有趣", "引人入胜", "震撼人心", "感动落泪", "妙不可言"]
                    random_word = random.choice(words)
                    hit_lines[j] += f"，{random_word}"
        
        # 构建随机变化的SRT文本
        origin_srt = "\n".join(origin_lines)
        hit_srt = "\n".join(hit_lines)
        
        # 添加到结果列表
        hit_data.append({
            "id": f"sample_{i+1}",
            "origin_srt": origin_srt,
            "hit_srt": hit_srt,
            "metadata": {
                "views": random.randint(1000, 1000000),
                "likes": random.randint(100, 50000),
                "shares": random.randint(10, 5000)
            }
        })
    
    return hit_data


def main():
    """主函数"""
    logger.info("开始模式实时更新器演示")
    
    # 初始化模式更新器
    updater = PatternUpdater()
    logger.info("模式更新器初始化完成")
    
    # 生成示例数据
    hit_data = generate_sample_hit_data(10)
    logger.info(f"生成了 {len(hit_data)} 条示例命中数据")
    
    # 模拟流式处理多批数据
    for batch_index in range(3):
        # 每批处理部分数据
        batch_size = min(4, len(hit_data))
        batch_data = hit_data[:batch_size]
        hit_data = hit_data[batch_size:]  # 剩余数据
        
        logger.info(f"处理第 {batch_index+1} 批数据，包含 {len(batch_data)} 条记录")
        
        # 调用实时更新器
        result = updater.streaming_update(batch_data)
        
        # 打印结果
        logger.info(f"批次 {batch_index+1} 处理结果：")
        logger.info(f"  - 处理记录数: {result['stats']['processed_items']}")
        logger.info(f"  - 挖掘模式数: {result['stats']['mined_patterns']}")
        logger.info(f"  - 重要模式数: {result['stats']['significant_patterns']}")
        logger.info(f"  - 合并模式数: {result['stats']['merged_patterns']}")
        logger.info(f"  - 是否创建新版本: {result['stats']['version_created']}")
        logger.info(f"  - 处理时间: {result['stats']['processing_time']:.2f}秒")
        logger.info("-" * 50)
        
        # 间隔一段时间，模拟真实场景
        import time
        time.sleep(1)
    
    logger.info("模式实时更新器演示完成")


if __name__ == "__main__":
    main() 