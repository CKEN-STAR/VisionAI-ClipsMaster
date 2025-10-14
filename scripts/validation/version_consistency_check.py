#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 版本一致性检查工具
用于验证所有版本相关文件的一致性
"""

import json
import yaml
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class VersionConsistencyChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.expected_version = "1.1.0"
        self.expected_date = "2025-10-06"
        self.expected_name = "智能下载器优化版"
        self.issues = []
        
    def check_version_py(self) -> bool:
        """检查 version.py 文件"""
        version_file = self.project_root / "src" / "utils" / "version.py"
        if not version_file.exists():
            self.issues.append("❌ src/utils/version.py 文件不存在")
            return False
            
        content = version_file.read_text(encoding='utf-8')
        
        # 检查版本号
        version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if not version_match or version_match.group(1) != self.expected_version:
            self.issues.append(f"❌ version.py 中版本号不匹配: 期望 {self.expected_version}")
            return False
            
        # 检查发布日期
        date_match = re.search(r'__release_date__ = ["\']([^"\']+)["\']', content)
        if not date_match or date_match.group(1) != self.expected_date:
            self.issues.append(f"❌ version.py 中发布日期不匹配: 期望 {self.expected_date}")
            return False
            
        # 检查发布名称
        name_match = re.search(r'__release_name__ = ["\']([^"\']+)["\']', content)
        if not name_match or name_match.group(1) != self.expected_name:
            self.issues.append(f"❌ version.py 中发布名称不匹配: 期望 {self.expected_name}")
            return False
            
        print("✅ version.py 检查通过")
        return True
        
    def check_setup_py(self) -> bool:
        """检查 setup.py 文件"""
        setup_file = self.project_root / "setup.py"
        if not setup_file.exists():
            self.issues.append("❌ setup.py 文件不存在")
            return False
            
        content = setup_file.read_text(encoding='utf-8')
        
        # 检查版本号
        version_match = re.search(r'version=["\']([^"\']+)["\']', content)
        if not version_match or version_match.group(1) != self.expected_version:
            self.issues.append(f"❌ setup.py 中版本号不匹配: 期望 {self.expected_version}")
            return False
            
        print("✅ setup.py 检查通过")
        return True
        
    def check_pyproject_toml(self) -> bool:
        """检查 pyproject.toml 文件"""
        toml_file = self.project_root / "pyproject.toml"
        if not toml_file.exists():
            self.issues.append("❌ pyproject.toml 文件不存在")
            return False
            
        content = toml_file.read_text(encoding='utf-8')
        
        # 检查版本号
        version_match = re.search(r'version = ["\']([^"\']+)["\']', content)
        if not version_match or version_match.group(1) != self.expected_version:
            self.issues.append(f"❌ pyproject.toml 中版本号不匹配: 期望 {self.expected_version}")
            return False
            
        print("✅ pyproject.toml 检查通过")
        return True
        
    def check_docs_version_json(self) -> bool:
        """检查 configs/docs_version.json 文件"""
        docs_file = self.project_root / "configs" / "docs_version.json"
        if not docs_file.exists():
            self.issues.append("❌ configs/docs_version.json 文件不存在")
            return False
            
        try:
            with open(docs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查当前版本
            current_version = data.get('current_version', '')
            if current_version != f"v{self.expected_version}":
                self.issues.append(f"❌ docs_version.json 中当前版本不匹配: 期望 v{self.expected_version}")
                return False
                
            # 检查发布版本列表
            published_versions = data.get('published_versions', [])
            v101_found = False
            for version in published_versions:
                if version.get('version') == f"v{self.expected_version}":
                    v101_found = True
                    if version.get('release_date') != self.expected_date:
                        self.issues.append(f"❌ docs_version.json 中v{self.expected_version}发布日期不匹配")
                        return False
                    if version.get('code_name') != self.expected_name:
                        self.issues.append(f"❌ docs_version.json 中v{self.expected_version}代码名称不匹配")
                        return False
                    break
                    
            if not v101_found:
                self.issues.append(f"❌ docs_version.json 中未找到v{self.expected_version}版本信息")
                return False
                
        except Exception as e:
            self.issues.append(f"❌ 读取 docs_version.json 失败: {e}")
            return False
            
        print("✅ configs/docs_version.json 检查通过")
        return True
        
    def check_version_control_json(self) -> bool:
        """检查 configs/version_control.json 文件"""
        control_file = self.project_root / "configs" / "version_control.json"
        if not control_file.exists():
            self.issues.append("❌ configs/version_control.json 文件不存在")
            return False
            
        try:
            with open(control_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            version_info = data.get('version_info', {})
            
            # 检查版本组件
            if (version_info.get('major') != 1 or
                version_info.get('minor') != 1 or
                version_info.get('patch') != 0):
                self.issues.append("❌ version_control.json 中版本组件不匹配")
                return False
                
            # 检查发布日期
            if version_info.get('release_date') != self.expected_date:
                self.issues.append(f"❌ version_control.json 中发布日期不匹配: 期望 {self.expected_date}")
                return False
                
        except Exception as e:
            self.issues.append(f"❌ 读取 version_control.json 失败: {e}")
            return False
            
        print("✅ configs/version_control.json 检查通过")
        return True
        
    def check_changelog_md(self) -> bool:
        """检查 CHANGELOG.md 或 RELEASE_NOTES 文件"""
        # 优先检查 RELEASE_NOTES_v1.1.0.md
        release_notes_file = self.project_root / f"RELEASE_NOTES_v{self.expected_version}.md"
        changelog_file = self.project_root / "CHANGELOG.md"

        if release_notes_file.exists():
            content = release_notes_file.read_text(encoding='utf-8')
            if f"v{self.expected_version}" in content:
                print(f"✅ RELEASE_NOTES_v{self.expected_version}.md 检查通过")
                return True

        if changelog_file.exists():
            content = changelog_file.read_text(encoding='utf-8')
            if f"## [1.1.0] - {self.expected_date}" in content or f"### v1.1.0" in content:
                print("✅ CHANGELOG.md 检查通过")
                return True

        self.issues.append(f"❌ 未找到版本 {self.expected_version} 的发布说明文件")
        return False
        
    def check_readme_md(self) -> bool:
        """检查 README.md 文件"""
        readme_file = self.project_root / "README.md"
        if not readme_file.exists():
            self.issues.append("❌ README.md 文件不存在")
            return False
            
        content = readme_file.read_text(encoding='utf-8')
        
        # 检查是否包含版本历史
        if f"### v{self.expected_version} - {self.expected_name}" not in content:
            self.issues.append(f"❌ README.md 中未找到v{self.expected_version}版本历史")
            return False
            
        print("✅ README.md 检查通过")
        return True
        
    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print(f"🔍 开始版本一致性检查 (期望版本: {self.expected_version})")
        print("=" * 60)
        
        checks = [
            self.check_version_py,
            self.check_setup_py,
            self.check_pyproject_toml,
            self.check_docs_version_json,
            self.check_version_control_json,
            self.check_changelog_md,
            self.check_readme_md,
        ]
        
        all_passed = True
        for check in checks:
            if not check():
                all_passed = False
                
        print("=" * 60)
        
        if all_passed:
            print("🎉 所有版本一致性检查通过！")
            print(f"✅ 版本 {self.expected_version} ({self.expected_name}) 已正确配置")
            return True
        else:
            print("❌ 发现版本一致性问题:")
            for issue in self.issues:
                print(f"   {issue}")
            return False

def main():
    """主函数"""
    checker = VersionConsistencyChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
