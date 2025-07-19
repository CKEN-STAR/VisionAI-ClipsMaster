#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本文档生成器演示

此脚本演示如何使用版本文档生成器来创建多语言版本兼容性文档。
它展示了如何调用生成器的不同功能，并演示了如何自定义输出。
"""

import os
import sys
import argparse
from pathlib import Path

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

# 导入版本文档生成器
try:
    from tools.version_doc_generator import (
        generate_version_compatibility_doc,
        generate_version_compat_matrix,
        generate_version_feature_comparison,
        generate_migration_guide,
        save_documentation,
        LANG_ZH,
        LANG_EN,
        LANG_BOTH
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已经创建 tools/version_doc_generator.py 文件")
    sys.exit(1)

def create_demo_docs(output_dir: str, language: str):
    """
    创建演示文档
    
    Args:
        output_dir: 输出目录
        language: 语言代码 ('zh', 'en', 或 'both')
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义要生成的语言列表
    languages = []
    if language == LANG_BOTH:
        languages = [LANG_ZH, LANG_EN]
    else:
        languages = [language]
    
    for lang in languages:
        # 生成完整文档
        full_doc = generate_version_compatibility_doc(lang)
        
        lang_suffix = "zh" if lang == LANG_ZH else "en"
        doc_filename = f"version_compatibility_{lang_suffix}.md"
        save_documentation(full_doc, os.path.join(output_dir, doc_filename))
        
        # 只生成兼容性矩阵
        matrix_doc = generate_version_compat_matrix(lang)
        matrix_filename = f"version_matrix_{lang_suffix}.md"
        save_documentation(matrix_doc, os.path.join(output_dir, matrix_filename))
        
        # 只生成功能比较表
        features_doc = generate_version_feature_comparison(lang)
        features_filename = f"version_features_{lang_suffix}.md"
        save_documentation(features_doc, os.path.join(output_dir, features_filename))
        
        # 只生成迁移指南
        migration_doc = generate_migration_guide(lang)
        migration_filename = f"version_migration_{lang_suffix}.md"
        save_documentation(migration_doc, os.path.join(output_dir, migration_filename))
        
    print(f"所有文档已生成到目录: {output_dir}")
    print("生成的文件:")
    for file in os.listdir(output_dir):
        if file.startswith("version_") and file.endswith(".md"):
            print(f"  - {file}")

def main():
    parser = argparse.ArgumentParser(description="版本文档生成器演示")
    parser.add_argument('--output_dir', default='examples/version_docs',
                        help="输出目录路径")
    parser.add_argument('--lang', default=LANG_BOTH, choices=[LANG_ZH, LANG_EN, LANG_BOTH],
                        help="文档语言 (zh: 中文, en: 英文, both: 双语)")
    
    args = parser.parse_args()
    
    print("开始生成版本文档...")
    create_demo_docs(args.output_dir, args.lang)
    print("版本文档生成完成!")
    
if __name__ == "__main__":
    main() 