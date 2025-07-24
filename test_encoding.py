#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码测试脚本
测试各种字符的显示效果
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_encoding():
    """测试编码"""
    print("=" * 50)
    print("编码测试开始")
    print("=" * 50)
    
    # 测试基本中文
    print("✅ 中文测试: 这是中文字符")
    
    # 测试emoji（安全模式）
    print("✅ Emoji测试: [MUSIC] [NOTE] [CHECK] [CROSS]")
    
    # 测试英文
    print("✅ English test: This is English text")
    
    # 测试混合
    print("✅ 混合测试: VisionAI-ClipsMaster 短剧混剪系统")
    
    # 测试日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("日志测试: 系统正常运行")
    logger.info("Log test: System running normally")
    logger.info("混合日志: VisionAI-ClipsMaster [MUSIC] 节奏分析完成")
    
    print("=" * 50)
    print("编码测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_encoding()
