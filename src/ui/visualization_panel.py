#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化面板组件 - 提供剧本分析结果可视化界面
用于主界面集成
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

# 导入可视化模块
from src.visualization.script_visualizer import (
    generate_analysis_report,
    export_visualization_report
)

class VisualizationPanel:
    """可视化面板组件"""
    
    def __init__(self):
        """初始化可视化面板"""
        self.logger = logging.getLogger("visualization_panel")
        
        # 设置目录
        self.output_dir = os.path.join(ROOT_DIR, "data", "output", "reports")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_report(self, script_data: Dict[str, Any], 
                       output_path: Optional[str] = None,
                       format: str = "html") -> str:
        """
        生成可视化报告
        
        Args:
            script_data: 剧本数据
            output_path: 输出路径，如为None则使用默认路径
            format: 输出格式
            
        Returns:
            报告文件路径
        """
        try:
            if output_path is None:
                # 使用默认路径
                process_id = script_data.get("process_id", datetime.now().strftime("%Y%m%d%H%M%S"))
                output_path = os.path.join(self.output_dir, f"report_{process_id}.{format}")
            
            # 导出报告
            self.logger.info(f"正在生成可视化报告: {output_path}")
            return export_visualization_report(script_data, output_path, format)
        except Exception as e:
            self.logger.error(f"生成报告失败: {str(e)}")
            return str(e)
    
    def visualize_from_json(self, json_path: str, 
                           output_path: Optional[str] = None,
                           format: str = "html") -> str:
        """
        从JSON文件加载剧本数据并生成可视化报告
        
        Args:
            json_path: JSON文件路径
            output_path: 输出路径
            format: 输出格式
            
        Returns:
            报告文件路径
        """
        try:
            # 加载JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # 使用默认输出路径
            if output_path is None:
                output_path = os.path.splitext(json_path)[0] + f"_report.{format}"
            
            # 生成报告
            return self.generate_report(script_data, output_path, format)
        except Exception as e:
            self.logger.error(f"从JSON生成报告失败: {str(e)}")
            return str(e)
    
    def open_report(self, report_path: str) -> bool:
        """
        打开生成的报告
        
        Args:
            report_path: 报告文件路径
            
        Returns:
            是否成功打开
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(report_path):
                self.logger.error(f"报告文件不存在: {report_path}")
                return False
            
            # 使用系统默认程序打开
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            return True
        except Exception as e:
            self.logger.error(f"打开报告失败: {str(e)}")
            return False

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建面板
    panel = VisualizationPanel()
    
    # 测试从JSON生成报告
    test_json = os.path.join(ROOT_DIR, "data", "test", "test_script_data.json")
    
    if os.path.exists(test_json):
        report_path = panel.visualize_from_json(test_json)
        print(f"生成的报告: {report_path}")
        panel.open_report(report_path)
    else:
        print(f"测试数据不存在: {test_json}")
        print("请先运行 'python src/visualization/standalone_test.py' 生成测试数据") 