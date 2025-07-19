"""
模式实时更新器 - 独立测试版

独立运行的模式实时更新器，移除了对其他组件的依赖以方便测试
"""

import os
import time
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

class PatternUpdaterStandalone:
    """模式实时更新器独立版，用于测试"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化模式更新器
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认配置
        """
        # 状态记录
        self.last_update_time = None
        self.update_count = 0
        self.pending_patterns = []
        
        # 配置
        self.config = {
            "batch_size": 50,                # 批处理大小
            "update_threshold": 0.6,         # 模式更新阈值
            "min_patterns_for_version": 10,  # 创建新版本所需的最小模式数量
            "auto_version": True,            # 是否自动创建新版本
            "version_interval": 24 * 60 * 60,  # 版本更新间隔（秒）
            "pattern_types": [               # 支持的模式类型
                "opening", "climax", "transition", 
                "conflict", "resolution", "ending"
            ],
        }
        
        logger.info("模式实时更新器(独立版)初始化完成")
    
    def streaming_update(self, new_hit_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理流式输入的命中数据，更新模式库
        
        Args:
            new_hit_data: 新的命中数据列表，每项包含原始字幕和命中字幕数据
            
        Returns:
            Dict: 包含更新结果的字典
        """
        start_time = time.time()
        
        # 1. 记录更新状态
        self.update_count += 1
        self.last_update_time = datetime.now().isoformat()
        
        # 2. 处理命中数据 - 简化版只打印数据
        logger.info(f"开始处理 {len(new_hit_data)} 条命中数据")
        for hit_item in new_hit_data:
            logger.info(f"处理数据 {hit_item['id']}")
            logger.debug(f"原始数据长度: {len(hit_item.get('origin_srt', ''))}")
            logger.debug(f"命中数据长度: {len(hit_item.get('hit_srt', ''))}")
        
        # 3. 模拟模式挖掘
        mined_count = min(len(new_hit_data) * 2, 10)  # 每条数据产生约2个模式
        logger.info(f"从数据中挖掘出 {mined_count} 个模式")
        
        # 模拟生成一些模式
        mined_patterns = []
        pattern_types = self.config["pattern_types"]
        for i in range(mined_count):
            pattern_type = pattern_types[i % len(pattern_types)]
            pattern_id = f"{pattern_type}_{uuid.uuid4().hex[:8]}"
            pattern = {
                "id": pattern_id,
                "type": pattern_type,
                "description": f"{pattern_type.capitalize()}类型模式",
                "frequency": 0.5 + (i % 5) * 0.1,  # 0.5 ~ 0.9
                "position": (i % 10) * 0.1,        # 0.0 ~ 0.9
                "sentiment": -0.5 + (i % 10) * 0.1 # -0.5 ~ 0.4
            }
            mined_patterns.append(pattern)
        
        # 4. 模拟模式评估
        significant_count = int(mined_count * 0.7)  # 约70%的模式是重要的
        logger.info(f"评估出 {significant_count} 个重要模式")
        
        # 5. 模拟模式合并
        merged_count = significant_count
        logger.info(f"合并了 {merged_count} 个模式到数据库")
        
        # 6. 模拟版本管理
        version_created = merged_count >= self.config["min_patterns_for_version"]
        if version_created:
            logger.info("创建了新的模式版本")
        
        # 7. 准备返回结果
        elapsed_time = time.time() - start_time
        result = {
            "update_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "processed_items": len(new_hit_data),
                "mined_patterns": mined_count,
                "significant_patterns": significant_count,
                "merged_patterns": merged_count,
                "version_created": version_created,
                "processing_time": elapsed_time
            }
        }
        
        return result


def test_updater():
    """测试模式更新器"""
    logger.info("开始测试独立版模式实时更新器")
    
    # 初始化更新器
    updater = PatternUpdaterStandalone()
    
    # 准备测试数据
    test_data = [
        {
            "id": "test1",
            "origin_srt": "原始字幕1\n这是测试",
            "hit_srt": "命中字幕1\n这是测试，效果更好"
        },
        {
            "id": "test2",
            "origin_srt": "原始字幕2\n另一个测试",
            "hit_srt": "命中字幕2\n另一个测试，更吸引人"
        },
        {
            "id": "test3",
            "origin_srt": "原始字幕3\n第三个测试",
            "hit_srt": "命中字幕3\n第三个测试，非常精彩"
        }
    ]
    
    # 调用流式更新
    result = updater.streaming_update(test_data)
    
    # 打印结果
    logger.info("更新结果:")
    for key, value in result.items():
        if key != "stats":
            logger.info(f"  - {key}: {value}")
    
    logger.info("统计信息:")
    for key, value in result["stats"].items():
        logger.info(f"  - {key}: {value}")
    
    logger.info("测试完成")


if __name__ == "__main__":
    test_updater() 