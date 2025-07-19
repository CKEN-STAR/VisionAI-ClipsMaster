#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文档完整性检查工具
检查项目文档的完整性、准确性和用户友好性
"""

import os
import json
import time
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    exists = os.path.exists(file_path)
    return {
        "file": file_path,
        "description": description,
        "exists": exists,
        "size": os.path.getsize(file_path) if exists else 0
    }

def analyze_readme_content(readme_path):
    """分析README.md内容的完整性"""
    if not os.path.exists(readme_path):
        return {"exists": False, "analysis": {}}
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查必要的章节
    required_sections = {
        "项目介绍": ["# 🎬 VisionAI-ClipsMaster", "项目亮点"],
        "快速开始": ["🚀 快速开始", "系统要求", "一键安装"],
        "技术架构": ["🏗️ 技术架构", "AI引擎", "工作流程"],
        "安装指南": ["安装与设置", "环境要求", "快速安装"],
        "使用教程": ["🎯 使用方法", "图形界面", "使用方法"],
        "功能特性": ["开发状态", "已完成功能", "持续优化"],
        "系统要求": ["📋 系统要求", "操作系统", "Python"],
        "故障排除": ["常见问题", "FAQ", "故障排除"],
        "贡献指南": ["🤝 贡献指南", "开发环境设置", "提交规范"],
        "许可证信息": ["📄 开源协议", "MIT License"],
        "更新日志": ["版本历史", "更新日志", "CHANGELOG"]
    }
    
    section_analysis = {}
    for section, keywords in required_sections.items():
        found = any(keyword in content for keyword in keywords)
        section_analysis[section] = {
            "found": found,
            "keywords": keywords,
            "matched": [kw for kw in keywords if kw in content]
        }
    
    # 检查代码示例
    code_blocks = content.count("```")
    has_installation_commands = "pip install" in content or "git clone" in content
    has_usage_examples = "python" in content and ".py" in content
    
    # 检查链接和引用
    has_external_links = "http" in content or "https" in content
    has_internal_links = "[" in content and "](" in content
    
    # 检查多语言支持
    has_chinese = any(ord(char) > 127 for char in content)
    has_english = any(char.isalpha() and ord(char) < 128 for char in content)
    
    return {
        "exists": True,
        "size": len(content),
        "lines": len(content.split('\n')),
        "sections": section_analysis,
        "code_examples": {
            "code_blocks": code_blocks // 2,  # 每个代码块有开始和结束
            "has_installation": has_installation_commands,
            "has_usage": has_usage_examples
        },
        "links": {
            "external_links": has_external_links,
            "internal_links": has_internal_links
        },
        "language": {
            "chinese": has_chinese,
            "english": has_english,
            "bilingual": has_chinese and has_english
        }
    }

def check_documentation_structure(root_path):
    """检查文档目录结构"""
    docs_path = os.path.join(root_path, "docs")
    
    expected_docs = {
        "INSTALLATION.md": "安装指南",
        "USER_GUIDE.md": "用户指南", 
        "CONTRIBUTING.md": "贡献指南",
        "API_REFERENCE.md": "API参考",
        "TROUBLESHOOTING.md": "故障排除",
        "CHANGELOG.md": "更新日志",
        "FAQ.md": "常见问题"
    }
    
    docs_analysis = {}
    for doc_file, description in expected_docs.items():
        file_path = os.path.join(docs_path, doc_file)
        docs_analysis[doc_file] = check_file_exists(file_path, description)
    
    return docs_analysis

def check_project_files(root_path):
    """检查项目必要文件"""
    essential_files = {
        "README.md": "项目说明文档",
        "LICENSE": "开源许可证",
        "requirements.txt": "Python依赖列表",
        "setup.py": "安装脚本",
        "pyproject.toml": "项目配置",
        ".gitignore": "Git忽略文件",
        "Dockerfile": "Docker配置",
        "simple_ui_fixed.py": "主程序入口"
    }
    
    files_analysis = {}
    for file_name, description in essential_files.items():
        file_path = os.path.join(root_path, file_name)
        files_analysis[file_name] = check_file_exists(file_path, description)
    
    return files_analysis

def analyze_project_structure(root_path):
    """分析项目目录结构"""
    important_dirs = {
        "src": "源代码目录",
        "ui": "用户界面组件",
        "configs": "配置文件目录",
        "tools": "工具目录",
        "models": "AI模型目录",
        "data": "数据目录",
        "tests": "测试代码目录",
        "docs": "文档目录",
        "examples": "示例代码目录"
    }
    
    structure_analysis = {}
    for dir_name, description in important_dirs.items():
        dir_path = os.path.join(root_path, dir_name)
        exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
        file_count = 0
        if exists:
            try:
                file_count = len([f for f in os.listdir(dir_path) 
                                if os.path.isfile(os.path.join(dir_path, f))])
            except PermissionError:
                file_count = -1
        
        structure_analysis[dir_name] = {
            "exists": exists,
            "description": description,
            "file_count": file_count
        }
    
    return structure_analysis

def check_current_project_status():
    """检查当前项目状态信息"""
    root_path = r"d:\zancun\VisionAI-ClipsMaster-backup"
    
    # 获取项目体积
    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(root_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
    
    # 检查Git状态
    git_exists = os.path.exists(os.path.join(root_path, ".git"))
    
    # 检查主程序
    main_program = os.path.join(root_path, "simple_ui_fixed.py")
    main_exists = os.path.exists(main_program)
    
    # 检查测试文件
    test_file = os.path.join(root_path, "VisionAI_ClipsMaster_Comprehensive_Verification_Test.py")
    test_exists = os.path.exists(test_file)
    
    return {
        "project_size": total_size,
        "project_size_gb": total_size / (1024**3),
        "file_count": file_count,
        "git_initialized": git_exists,
        "main_program_exists": main_exists,
        "test_file_exists": test_exists,
        "optimization_status": "已优化" if total_size < 2 * 1024**3 else "未优化"
    }

def generate_documentation_report(root_path):
    """生成文档完整性报告"""
    print("🔍 开始VisionAI-ClipsMaster文档完整性检查...")
    print("=" * 80)
    
    # 1. 检查README.md
    readme_path = os.path.join(root_path, "README.md")
    readme_analysis = analyze_readme_content(readme_path)
    
    # 2. 检查项目文件
    files_analysis = check_project_files(root_path)
    
    # 3. 检查文档结构
    docs_analysis = check_documentation_structure(root_path)
    
    # 4. 检查项目结构
    structure_analysis = analyze_project_structure(root_path)
    
    # 5. 检查当前状态
    project_status = check_current_project_status()
    
    # 生成报告
    report = {
        "analysis_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "project_path": root_path,
        "project_status": project_status,
        "readme_analysis": readme_analysis,
        "essential_files": files_analysis,
        "documentation_structure": docs_analysis,
        "project_structure": structure_analysis
    }
    
    # 计算完整性得分
    score = calculate_completeness_score(report)
    report["completeness_score"] = score
    
    # 保存报告
    report_file = "VisionAI_ClipsMaster_Documentation_Audit_Report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 显示摘要
    print_report_summary(report)
    
    return report

def calculate_completeness_score(report):
    """计算文档完整性得分"""
    total_score = 0
    max_score = 0
    
    # README分析得分 (40分)
    readme = report["readme_analysis"]
    if readme["exists"]:
        sections_found = sum(1 for s in readme["sections"].values() if s["found"])
        total_sections = len(readme["sections"])
        readme_score = (sections_found / total_sections) * 40
        total_score += readme_score
    max_score += 40
    
    # 必要文件得分 (30分)
    files = report["essential_files"]
    files_found = sum(1 for f in files.values() if f["exists"])
    total_files = len(files)
    files_score = (files_found / total_files) * 30
    total_score += files_score
    max_score += 30
    
    # 项目结构得分 (20分)
    structure = report["project_structure"]
    dirs_found = sum(1 for d in structure.values() if d["exists"])
    total_dirs = len(structure)
    structure_score = (dirs_found / total_dirs) * 20
    total_score += structure_score
    max_score += 20
    
    # 文档目录得分 (10分)
    docs = report["documentation_structure"]
    docs_found = sum(1 for d in docs.values() if d["exists"])
    total_docs = len(docs)
    docs_score = (docs_found / total_docs) * 10 if total_docs > 0 else 0
    total_score += docs_score
    max_score += 10
    
    return {
        "total_score": round(total_score, 2),
        "max_score": max_score,
        "percentage": round((total_score / max_score) * 100, 1),
        "grade": get_grade(total_score / max_score)
    }

def get_grade(percentage):
    """根据得分获取等级"""
    if percentage >= 0.9:
        return "A+ (优秀)"
    elif percentage >= 0.8:
        return "A (良好)"
    elif percentage >= 0.7:
        return "B (中等)"
    elif percentage >= 0.6:
        return "C (及格)"
    else:
        return "D (需要改进)"

def print_report_summary(report):
    """打印报告摘要"""
    print("\n📊 文档完整性检查结果:")
    print("-" * 60)
    
    # 项目状态
    status = report["project_status"]
    print(f"📁 项目体积: {status['project_size_gb']:.2f}GB ({status['file_count']}个文件)")
    print(f"🔧 Git状态: {'✅ 已初始化' if status['git_initialized'] else '❌ 未初始化'}")
    print(f"🚀 主程序: {'✅ 存在' if status['main_program_exists'] else '❌ 缺失'}")
    print(f"🧪 测试文件: {'✅ 存在' if status['test_file_exists'] else '❌ 缺失'}")
    
    # README分析
    readme = report["readme_analysis"]
    if readme["exists"]:
        sections_found = sum(1 for s in readme["sections"].values() if s["found"])
        total_sections = len(readme["sections"])
        print(f"📖 README.md: ✅ 存在 ({sections_found}/{total_sections}个必要章节)")
        print(f"   - 代码示例: {readme['code_examples']['code_blocks']}个")
        print(f"   - 多语言支持: {'✅' if readme['language']['bilingual'] else '❌'}")
    else:
        print("📖 README.md: ❌ 缺失")
    
    # 必要文件
    files = report["essential_files"]
    files_found = sum(1 for f in files.values() if f["exists"])
    total_files = len(files)
    print(f"📄 必要文件: {files_found}/{total_files}个存在")
    
    # 项目结构
    structure = report["project_structure"]
    dirs_found = sum(1 for d in structure.values() if d["exists"])
    total_dirs = len(structure)
    print(f"📁 项目结构: {dirs_found}/{total_dirs}个目录存在")
    
    # 完整性得分
    score = report["completeness_score"]
    print(f"\n🎯 文档完整性得分: {score['total_score']}/{score['max_score']} ({score['percentage']}%)")
    print(f"📊 评级: {score['grade']}")
    
    print(f"\n📋 详细报告已保存: VisionAI_ClipsMaster_Documentation_Audit_Report.json")

def main():
    """主函数"""
    root_path = r"d:\zancun\VisionAI-ClipsMaster-backup"
    
    print("🔍 VisionAI-ClipsMaster 文档完整性检查")
    print("=" * 80)
    print(f"检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {root_path}")
    
    # 生成报告
    report = generate_documentation_report(root_path)
    
    print("\n✅ 文档检查完成!")

if __name__ == "__main__":
    main()
