#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
黄金样本生成运行脚本

简化黄金样本的生成过程，提供命令行界面生成和管理黄金样本。
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 导入生成器模块
from tests.golden_samples.generate_samples import (
    create_golden_sample,
    update_golden_samples_index
)
from src.utils.log_handler import get_logger

# 初始化日志
logger = get_logger("run_golden_sample")

def setup_logging(level):
    """设置日志级别"""
    logger = logging.getLogger("golden_samples")
    logger.setLevel(getattr(logging, level))
    logger = logging.getLogger("run_golden_sample")
    logger.setLevel(getattr(logging, level))

def create_template_files():
    """创建模板文件，如果不存在"""
    # 创建XML模板文件
    template_dir = os.path.join(PROJECT_ROOT, "templates")
    os.makedirs(template_dir, exist_ok=True)
    
    template_path = os.path.join(template_dir, "golden_sample_template.xml")
    if not os.path.exists(template_path):
        logger.info(f"创建XML模板文件: {template_path}")
        
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<project version="1.0">
    <info>
        <name>Golden Sample - {{scene_name}}</name>
        <type>{{scene_type}}</type>
        <duration>120.0</duration>
        <resolution>1920x1080</resolution>
        <framerate>30</framerate>
        <description>This is a golden standard sample for {{scene_type}} scene type.</description>
        <created_by>VisionAI-ClipsMaster</created_by>
    </info>
    
    <timeline>
        <track type="video">
            <clip start="0" end="120" source="golden_{{scene_type}}_source.mp4">
                <effects>
                    <effect type="color_grading" preset="standard"/>
                    <effect type="stabilization" amount="0.3"/>
                </effects>
            </clip>
        </track>
        
        <track type="audio">
            <clip start="0" end="120" source="golden_{{scene_type}}_audio.wav">
                <effects>
                    <effect type="normalization" target_db="-14"/>
                    <effect type="noise_reduction" amount="0.2"/>
                </effects>
            </clip>
        </track>
        
        <track type="subtitle">
            <clip start="0" end="120" source="golden_{{scene_type}}.srt">
                <settings>
                    <font>Arial</font>
                    <size>42</size>
                    <color>#FFFFFF</color>
                    <background>#80000000</background>
                    <position>bottom_center</position>
                </settings>
            </clip>
        </track>
    </timeline>
    
    <metadata>
        <golden_standard>true</golden_standard>
        <test_purpose>quality_comparison</test_purpose>
        <category>{{scene_type}}</category>
        <tags>golden_sample, {{scene_type}}, test, benchmark</tags>
        <content_rating>general</content_rating>
    </metadata>
    
    <test_parameters>
        <ssim_baseline>0.95</ssim_baseline>
        <psnr_baseline>40.0</psnr_baseline>
        <motion_consistency_baseline>0.92</motion_consistency_baseline>
        <audio_quality_baseline>0.90</audio_quality_baseline>
    </test_parameters>
</project>
"""
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)

def create_directory_structure():
    """确保所有必要的目录结构都存在"""
    # 黄金样本主目录
    golden_dir = os.path.join(PROJECT_ROOT, "tests", "golden_samples")
    os.makedirs(golden_dir, exist_ok=True)
    
    # 输出目录
    output_dir = os.path.join(golden_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 哈希目录
    hash_dir = os.path.join(golden_dir, "hashes")
    os.makedirs(hash_dir, exist_ok=True)
    
    # 报告目录
    report_dir = os.path.join(golden_dir, "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    logger.info("已创建所有必要的目录结构")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="黄金样本生成运行脚本")
    
    # 版本参数
    parser.add_argument("--version", default="1.0.0", help="生成样本的版本号")
    
    # 功能选择
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true", help="生成黄金样本")
    group.add_argument("--update-index", action="store_true", help="更新样本索引")
    group.add_argument("--list", action="store_true", help="列出所有样本")
    
    # 其他选项
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 设置日志级别
    setup_logging(args.log_level)
    
    # 创建模板文件
    create_template_files()
    
    # 创建目录结构
    create_directory_structure()
    
    # 根据选项执行相应功能
    if args.generate:
        logger.info(f"开始生成版本 {args.version} 的黄金样本")
        golden_hash = create_golden_sample(args.version)
        logger.info(f"黄金样本生成完成，哈希值: {golden_hash}")
        
        # 自动更新索引
        update_golden_samples_index()
    
    elif args.update_index:
        logger.info("更新黄金样本索引")
        update_golden_samples_index()
    
    elif args.list:
        # 查找索引文件
        index_path = os.path.join(PROJECT_ROOT, "tests", "golden_samples", "index.json")
        
        if os.path.exists(index_path):
            import json
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            print("\n黄金样本列表:")
            print("=" * 80)
            print(f"最后更新时间: {index_data.get('last_updated', '未知')}")
            print("-" * 80)
            
            for version, version_data in index_data.get("versions", {}).items():
                print(f"\n版本: {version}")
                samples = version_data.get("samples", [])
                print(f"样本数量: {len(samples)}")
                
                for sample_id in samples:
                    if sample_id in index_data.get("samples", {}):
                        sample_info = index_data["samples"][sample_id]
                        print(f"  - {sample_id} ({sample_info.get('type', '未知类型')})")
            
            print("\n使用 --generate 选项生成新的样本")
        else:
            logger.warning("索引文件不存在，请先生成样本或更新索引")
            print("\n尚未生成任何黄金样本。使用以下命令生成:")
            print(f"python {os.path.basename(__file__)} --generate --version VERSION")
    
    logger.info("操作完成")

if __name__ == "__main__":
    main() 