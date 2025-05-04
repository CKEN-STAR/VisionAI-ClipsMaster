"""
简单测试模式实时更新器
"""

from src.core.pattern_updater import PatternUpdater
from loguru import logger

def main():
    """主函数"""
    logger.info("开始测试模式实时更新器")
    
    # 初始化模式更新器
    updater = PatternUpdater()
    logger.info("模式更新器初始化完成")
    
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
        }
    ]
    
    # 调用流式更新
    try:
        result = updater.streaming_update(test_data)
        
        # 打印结果
        logger.info("更新结果: ")
        logger.info(f"  - 更新ID: {result['update_id']}")
        logger.info(f"  - 时间戳: {result['timestamp']}")
        logger.info(f"  - 处理记录数: {result['stats']['processed_items']}")
        logger.info(f"  - 挖掘模式数: {result['stats']['mined_patterns']}")
        logger.info(f"  - 重要模式数: {result['stats']['significant_patterns']}")
        logger.info(f"  - 合并模式数: {result['stats']['merged_patterns']}")
        logger.info(f"  - 是否创建新版本: {result['stats']['version_created']}")
        logger.info(f"  - 处理时间: {result['stats']['processing_time']:.2f}秒")
    except Exception as e:
        logger.error(f"测试失败: {e}")
    
    logger.info("测试完成")

if __name__ == "__main__":
    main() 