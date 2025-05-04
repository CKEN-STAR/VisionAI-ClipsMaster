#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的预览模块测试脚本
"""

import os
import logging
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def simple_plot_test():
    """测试最基础的matplotlib绘图和HTML转换"""
    logger.info("创建简单的matplotlib图像...")
    
    # 创建简单的图
    plt.figure(figsize=(8, 4))
    plt.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16], 'ro-')
    plt.title("Simple Test Plot")
    plt.grid(True)
    
    # 保存为base64编码的图片
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # 创建HTML
    html = f'<img src="data:image/png;base64,{img_base64}" />'
    
    # 保存HTML
    output_file = "test_preview.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"<html><body>{html}</body></html>")
    
    logger.info(f"已保存HTML预览至: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    logger.info("开始预览模块基础测试...")
    simple_plot_test()
    logger.info("测试完成") 