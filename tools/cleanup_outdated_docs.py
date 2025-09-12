#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理过时文档脚本
识别并删除项目中过时、重复或不再使用的文档文件
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

def identify_outdated_docs():
    """识别过时的文档文件"""
    
    # 过时的README文件
    outdated_readmes = [
        "README_FIXED.md",
        "README_ACCESSIBILITY.md", 
        "README_ALERTING_SYSTEM.md",
        "README_CACHE_STRATEGY.md",
        "README_CHAOS_ENGINEERING.md",
        "README_COPYRIGHT_EMBEDDER.md",
        "README_DEPENDENCIES.md",  # 已整合到主README
        "README_MEMORY_SAFETY.md",
        "README_MULTILINGUAL.md",
        "README_MULTI_STRATEGY.md",
        "README_MULTI_VERSION.md",
        "README_QUALITY_IMPROVEMENT.md",
        "README_SMART_DEFAULTS.md",
        "README_causality_engine.md",
        "README_dialogue_validator.md",
        "updated_README.md"
    ]
    
    # 过时的实现总结文档
    outdated_summaries = [
        "ALIGNMENT_ENGINEER_IMPLEMENTATION_SUMMARY.md",
        "CLIP_GENERATOR_STAGE5_IMPLEMENTATION_SUMMARY.md",
        "COMPLETION_REPORT.md",
        "GOLDEN_STANDARD_IMPLEMENTATION.md",
        "IMPLEMENTATION_SUMMARY.md",
        "INSTRUCTION_PIPELINE_OPTIMIZATION.md",
        "PERFORMANCE_OPTIMIZATION_SUMMARY.md",
        "TIMELINE_VALIDATOR_SUMMARY.md",
        "VisionAI-ClipsMaster_Performance_Optimization_Summary.md",
        "VisionAI-ClipsMaster_Real_Material_Test_Summary.md",
        "VisionAI-ClipsMaster_Test_Summary.md"
    ]
    
    # 过时的UI相关报告
    outdated_ui_reports = [
        "VisionAI-ClipsMaster_UI改进效果验证报告.md",
        "VisionAI-ClipsMaster_UI测试完成总结.md",
        "VisionAI-ClipsMaster_UI测试报告.md",
        "VisionAI-ClipsMaster_UI高优先级优化完成报告.md",
        "VisionAI-ClipsMaster_关键修复验证报告.md",
        "VisionAI-ClipsMaster_稳定性改进完成报告.md",
        "VisionAI-ClipsMaster_稳定性测试报告.md",
        "VisionAI-ClipsMaster_进度条显示策略修复报告.md",
        "UI整合报告.md"
    ]
    
    # 过时的测试和环境文档
    outdated_test_docs = [
        "TEST_ENVIRONMENT.md",
        "TEST_ENV_README.md",
        "DEPENDENCY_STATUS.md",
        "UPDATES.md",
        "SUMMARY.md"
    ]
    
    # 过时的docs目录下的文档
    outdated_docs_files = [
        "docs/cleanup_system.md",  # 功能已整合
        "docs/coverage_optimization.md",  # 测试相关，已过时
        "docs/quality_tools.md",  # 质量工具已整合
        "docs/API_REFERENCE.md",  # API已变更，需重写
        "docs/i18n/README.md",  # 国际化功能暂未实现
        "docs/version_evolution_tracker.md",  # 版本管理已简化
        "docs/tests/TEST_STRUCTURE.md",  # 测试结构已变更
        "docs/source/index.rst",  # Sphinx文档已废弃
    ]
    
    # 过时的工具脚本文档
    outdated_tools = [
        "tools/doc_translator.py",  # 文档翻译工具暂未使用
        "tools/update_docs.sh",  # 更新脚本已过时
    ]
    
    return {
        "outdated_readmes": outdated_readmes,
        "outdated_summaries": outdated_summaries, 
        "outdated_ui_reports": outdated_ui_reports,
        "outdated_test_docs": outdated_test_docs,
        "outdated_docs_files": outdated_docs_files,
        "outdated_tools": outdated_tools
    }

def backup_files(files_to_remove: List[str], backup_dir: str = "docs_backup"):
    """备份要删除的文件"""
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_backup = backup_path / f"cleanup_{timestamp}"
    session_backup.mkdir(exist_ok=True)
    
    backed_up = []
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                # 保持目录结构
                rel_path = Path(file_path)
                backup_file = session_backup / rel_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(file_path, backup_file)
                backed_up.append(file_path)
                print(f"✓ 已备份: {file_path}")
            except Exception as e:
                print(f"✗ 备份失败 {file_path}: {e}")
    
    return backed_up, str(session_backup)

def remove_files(files_to_remove: List[str]):
    """删除文件"""
    removed = []
    failed = []
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                removed.append(file_path)
                print(f"✓ 已删除: {file_path}")
            except Exception as e:
                failed.append((file_path, str(e)))
                print(f"✗ 删除失败 {file_path}: {e}")
    
    return removed, failed

def generate_cleanup_report(outdated_docs: Dict, removed_files: List[str], 
                          failed_files: List, backup_location: str):
    """生成清理报告"""
    
    report_content = f"""# VisionAI-ClipsMaster 文档清理报告

**清理时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**备份位置**: {backup_location}  

## 清理概览

### 文件统计
- **总计识别**: {sum(len(files) for files in outdated_docs.values())} 个过时文档
- **成功删除**: {len(removed_files)} 个文件
- **删除失败**: {len(failed_files)} 个文件

## 详细清理列表

### 1. 过时的README文件 ({len(outdated_docs['outdated_readmes'])}个)
"""
    
    for readme in outdated_docs['outdated_readmes']:
        status = "✅ 已删除" if readme in removed_files else "❌ 未删除"
        report_content += f"- {readme} - {status}\n"
    
    report_content += f"""
### 2. 过时的实现总结文档 ({len(outdated_docs['outdated_summaries'])}个)
"""
    
    for summary in outdated_docs['outdated_summaries']:
        status = "✅ 已删除" if summary in removed_files else "❌ 未删除"
        report_content += f"- {summary} - {status}\n"
    
    report_content += f"""
### 3. 过时的UI报告文档 ({len(outdated_docs['outdated_ui_reports'])}个)
"""
    
    for ui_report in outdated_docs['outdated_ui_reports']:
        status = "✅ 已删除" if ui_report in removed_files else "❌ 未删除"
        report_content += f"- {ui_report} - {status}\n"
    
    report_content += f"""
### 4. 过时的测试文档 ({len(outdated_docs['outdated_test_docs'])}个)
"""
    
    for test_doc in outdated_docs['outdated_test_docs']:
        status = "✅ 已删除" if test_doc in removed_files else "❌ 未删除"
        report_content += f"- {test_doc} - {status}\n"
    
    report_content += f"""
### 5. 过时的docs目录文档 ({len(outdated_docs['outdated_docs_files'])}个)
"""
    
    for docs_file in outdated_docs['outdated_docs_files']:
        status = "✅ 已删除" if docs_file in removed_files else "❌ 未删除"
        report_content += f"- {docs_file} - {status}\n"
    
    report_content += f"""
### 6. 过时的工具脚本 ({len(outdated_docs['outdated_tools'])}个)
"""
    
    for tool in outdated_docs['outdated_tools']:
        status = "✅ 已删除" if tool in removed_files else "❌ 未删除"
        report_content += f"- {tool} - {status}\n"
    
    if failed_files:
        report_content += f"""
## 删除失败的文件

"""
        for file_path, error in failed_files:
            report_content += f"- {file_path}: {error}\n"
    
    report_content += f"""
## 清理效果

### 空间释放
- 删除了 {len(removed_files)} 个过时文档文件
- 简化了项目文档结构
- 提高了文档的可维护性

### 保留的核心文档
- ✅ README.md (已更新)
- ✅ README_EN.md (已更新)  
- ✅ LICENSE
- ✅ CONTRIBUTING.md
- ✅ docs/USER_GUIDE.md
- ✅ docs/DEVELOPMENT_STEPS.md
- ✅ docs/ERROR_HANDLING.md
- ✅ docs/TESTING.md

### 建议后续操作
1. 验证主要文档的完整性和准确性
2. 更新文档索引和链接
3. 考虑创建新的用户指南和开发文档
4. 定期清理临时文件和测试报告

---

**清理执行**: CKEN  
**完成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**备份状态**: 已完成 ✅  
"""
    
    return report_content

def main():
    """主函数"""
    print("🧹 开始清理VisionAI-ClipsMaster过时文档...")
    
    # 识别过时文档
    outdated_docs = identify_outdated_docs()
    
    # 收集所有要删除的文件
    all_files_to_remove = []
    for category, files in outdated_docs.items():
        all_files_to_remove.extend(files)
    
    print(f"📋 识别到 {len(all_files_to_remove)} 个过时文档文件")
    
    # 显示将要删除的文件
    print("\n📄 将要删除的文件:")
    for i, file_path in enumerate(all_files_to_remove, 1):
        exists = "✓" if os.path.exists(file_path) else "✗"
        print(f"  {i:2d}. {exists} {file_path}")
    
    # 确认删除
    response = input(f"\n❓ 确认删除这 {len(all_files_to_remove)} 个文件吗? (y/N): ")
    if response.lower() != 'y':
        print("❌ 取消清理操作")
        return
    
    # 备份文件
    print("\n💾 正在备份文件...")
    backed_up_files, backup_location = backup_files(all_files_to_remove)
    print(f"✓ 已备份 {len(backed_up_files)} 个文件到: {backup_location}")
    
    # 删除文件
    print("\n🗑️ 正在删除文件...")
    removed_files, failed_files = remove_files(all_files_to_remove)
    
    # 生成报告
    print("\n📊 生成清理报告...")
    report_content = generate_cleanup_report(outdated_docs, removed_files, failed_files, backup_location)
    
    # 保存报告
    report_file = "docs_cleanup_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ 清理报告已保存: {report_file}")
    
    # 总结
    print(f"\n🎉 文档清理完成!")
    print(f"   - 成功删除: {len(removed_files)} 个文件")
    print(f"   - 删除失败: {len(failed_files)} 个文件") 
    print(f"   - 备份位置: {backup_location}")
    print(f"   - 清理报告: {report_file}")

if __name__ == "__main__":
    main()
