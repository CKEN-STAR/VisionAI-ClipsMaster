#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文档构建命令行工具

用于构建多语言文档的命令行界面。
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加父目录到路径，以便能够导入doc_builder模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docs.i18n.doc_builder import DocLocalizer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 文档构建工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 构建命令
    build_parser = subparsers.add_parser("build", help="构建文档")
    build_parser.add_argument("--languages", "-l", nargs="+", choices=["en", "zh", "ja"], 
                            default=["en", "zh", "ja"], help="要构建的语言列表")
    
    # 同步命令
    sync_parser = subparsers.add_parser("sync", help="同步文档结构")
    sync_parser.add_argument("--source", "-s", choices=["en", "zh", "ja"], default="en",
                           help="源语言")
    
    # 初始化命令
    init_parser = subparsers.add_parser("init", help="初始化文档结构")
    
    # 全部命令（init + sync + build）
    all_parser = subparsers.add_parser("all", help="执行完整的文档工作流")
    all_parser.add_argument("--source", "-s", choices=["en", "zh", "ja"], default="en",
                          help="源语言")
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 创建DocLocalizer实例
    doc_builder = DocLocalizer()
    
    if args.command == "build":
        # 只构建文档
        logger.info(f"开始构建语言: {', '.join(args.languages)}")
        for lang in args.languages:
            doc_builder._build_doc(lang)
        doc_builder.generate_doc_index()
    
    elif args.command == "sync":
        # 同步文档结构
        logger.info(f"从{args.source}同步文档结构")
        doc_builder.sync_documents(source_lang=args.source)
    
    elif args.command == "init":
        # 初始化文档结构
        logger.info("初始化文档结构")
        doc_builder.ensure_language_dirs()
    
    elif args.command == "all" or args.command is None:
        # 执行完整工作流
        logger.info("执行完整文档工作流")
        
        # 1. 初始化文档结构
        doc_builder.ensure_language_dirs()
        
        # 2. 同步文档
        source_lang = getattr(args, "source", "en")
        doc_builder.sync_documents(source_lang=source_lang)
        
        # 3. 构建文档
        doc_builder.build_all()
        
        # 4. 生成索引
        doc_builder.generate_doc_index()
    
    else:
        logger.error(f"未知命令: {args.command}")
        return 1
    
    logger.info("文档任务完成")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 