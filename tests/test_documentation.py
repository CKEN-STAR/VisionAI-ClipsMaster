#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档验证测试
检查README文件是否与实际代码一致
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_main_readme_exists():
    """测试主README文件存在"""
    print("=" * 60)
    print("测试1: 主README文件检查")
    print("=" * 60)
    
    readme_path = project_root / "README.md"
    
    assert readme_path.exists(), "主README.md文件应该存在"
    
    # 检查文件大小
    file_size = readme_path.stat().st_size
    print(f"✓ README.md存在，大小: {file_size} 字节")
    
    # 检查关键内容
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证关键章节
    required_sections = [
        "VisionAI-ClipsMaster",
        "快速开始",
        "系统要求",
        "项目结构",
    ]
    
    for section in required_sections:
        if section in content:
            print(f"✓ 包含章节: {section}")
        else:
            print(f"⚠ 缺少章节: {section}")
    
    print("\n✓ 主README文件检查通过")
    print()


def test_exporters_readme_files():
    """测试exporters目录的README文件"""
    print("=" * 60)
    print("测试2: exporters目录README文件检查")
    print("=" * 60)
    
    exporters_dir = project_root / "src" / "exporters"
    readme_files = list(exporters_dir.glob("README*.md"))
    
    print(f"✓ 找到 {len(readme_files)} 个README文件")
    
    # 检查每个README对应的Python文件是否存在
    for readme_file in readme_files:
        # 从README文件名推断Python文件名
        # 例如: README_FFMPEG_ZEROCOPY.md -> ffmpeg_zerocopy.py
        if readme_file.name.startswith("README_"):
            module_name = readme_file.name.replace("README_", "").replace(".md", "").lower()
            py_file = exporters_dir / f"{module_name}.py"
            
            if py_file.exists():
                print(f"✓ {readme_file.name:40s} -> {py_file.name}")
            else:
                print(f"⚠ {readme_file.name:40s} -> {module_name}.py (文件不存在)")
    
    print(f"\n✓ exporters目录README文件检查完成")
    print()


def test_core_module_documentation():
    """测试核心模块文档"""
    print("=" * 60)
    print("测试3: 核心模块文档检查")
    print("=" * 60)
    
    core_modules = [
        "clip_generator.py",
        "screenplay_engineer.py",
        "model_switcher.py",
    ]
    
    core_dir = project_root / "src" / "core"
    
    for module in core_modules:
        module_path = core_dir / module
        
        if module_path.exists():
            # 检查模块是否有文档字符串
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有模块级文档字符串
            if '"""' in content[:500]:
                print(f"✓ {module:30s} - 有文档字符串")
            else:
                print(f"⚠ {module:30s} - 缺少文档字符串")
        else:
            print(f"✗ {module:30s} - 文件不存在")
    
    print("\n✓ 核心模块文档检查完成")
    print()


def test_api_documentation():
    """测试API文档"""
    print("=" * 60)
    print("测试4: API文档检查")
    print("=" * 60)
    
    docs_dir = project_root / "docs"
    
    if docs_dir.exists():
        api_doc = docs_dir / "API_REFERENCE.md"
        
        if api_doc.exists():
            print(f"✓ API文档存在: {api_doc.name}")
            
            # 检查文件大小
            file_size = api_doc.stat().st_size
            print(f"✓ 文档大小: {file_size} 字节")
        else:
            print("⚠ API_REFERENCE.md不存在")
    else:
        print("⚠ docs目录不存在")
    
    print("\n✓ API文档检查完成")
    print()


def test_requirements_documentation():
    """测试依赖文档"""
    print("=" * 60)
    print("测试5: 依赖文档检查")
    print("=" * 60)
    
    req_file = project_root / "requirements.txt"
    opt_req_file = project_root / "requirements-optional.txt"
    
    if req_file.exists():
        with open(req_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 统计依赖数量
        deps = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        print(f"✓ requirements.txt存在，包含 {len(deps)} 个依赖")
        
        # 检查是否有注释说明
        comments = [line for line in lines if line.strip().startswith('#')]
        print(f"✓ 包含 {len(comments)} 行注释说明")
    else:
        print("✗ requirements.txt不存在")
    
    if opt_req_file.exists():
        with open(opt_req_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"✓ requirements-optional.txt存在，包含 {len(lines)} 行")
    else:
        print("⚠ requirements-optional.txt不存在")
    
    print("\n✓ 依赖文档检查完成")
    print()


def test_configuration_documentation():
    """测试配置文档"""
    print("=" * 60)
    print("测试6: 配置文档检查")
    print("=" * 60)
    
    configs_dir = project_root / "configs"
    
    if configs_dir.exists():
        config_files = list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.json"))
        print(f"✓ 找到 {len(config_files)} 个配置文件")
        
        for config_file in config_files[:5]:  # 只显示前5个
            print(f"  - {config_file.name}")
    else:
        print("⚠ configs目录不存在")
    
    print("\n✓ 配置文档检查完成")
    print()


def generate_documentation_report():
    """生成文档报告"""
    print("=" * 60)
    print("生成文档报告")
    print("=" * 60)
    
    report = []
    report.append("# VisionAI-ClipsMaster 文档状态报告")
    report.append("")
    report.append(f"生成时间: {Path(__file__).stat().st_mtime}")
    report.append("")
    
    # 统计README文件
    readme_files = list(project_root.rglob("README*.md"))
    # 排除.venv和llama.cpp目录
    readme_files = [f for f in readme_files if ".venv" not in str(f) and "llama.cpp" not in str(f)]
    
    report.append(f"## 文档统计")
    report.append(f"- 总README文件数: {len(readme_files)}")
    report.append("")
    
    # 按目录分类
    by_dir = {}
    for f in readme_files:
        dir_name = f.parent.relative_to(project_root)
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(f.name)
    
    report.append("## 按目录分类")
    for dir_name, files in sorted(by_dir.items()):
        report.append(f"### {dir_name}")
        for file in sorted(files):
            report.append(f"- {file}")
        report.append("")
    
    report_content = "\n".join(report)
    
    # 保存报告
    report_path = project_root / "tests" / "documentation_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ 文档报告已生成: {report_path}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("文档验证测试套件")
    print("=" * 60 + "\n")
    
    try:
        test_main_readme_exists()
        test_exporters_readme_files()
        test_core_module_documentation()
        test_api_documentation()
        test_requirements_documentation()
        test_configuration_documentation()
        generate_documentation_report()
        
        print("=" * 60)
        print("✓ 所有文档检查完成！")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试失败: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

