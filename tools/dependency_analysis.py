#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 依赖项分析工具
分析项目中的依赖项使用情况，识别缺失和冗余的依赖
"""

import json
import os
import sys
import subprocess
import importlib
from pathlib import Path
from collections import defaultdict, Counter
import pkg_resources

def load_declared_dependencies():
    """加载已声明的依赖项"""
    declared_deps = set()
    
    # 从requirements.txt加载
    req_files = [
        "requirements.txt",
        "requirements/requirements.txt", 
        "requirements/requirements-full.txt",
        "requirements/requirements-dev.txt",
        "requirements/requirements-lite.txt"
    ]
    
    for req_file in req_files:
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-r'):
                            # 提取包名（去除版本号）
                            pkg_name = line.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].split('!')[0].strip()
                            if pkg_name:
                                declared_deps.add(pkg_name.lower())
            except Exception as e:
                print(f"读取 {req_file} 时出错: {e}")
    
    # 从setup.py加载
    if os.path.exists("setup.py"):
        try:
            with open("setup.py", 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单的正则匹配来提取依赖
                import re
                matches = re.findall(r'"([^"]+)"', content)
                for match in matches:
                    if '>=' in match or '==' in match:
                        pkg_name = match.split('>=')[0].split('==')[0].strip()
                        declared_deps.add(pkg_name.lower())
        except Exception as e:
            print(f"读取 setup.py 时出错: {e}")
    
    return declared_deps

def load_used_imports():
    """加载实际使用的导入"""
    if not os.path.exists("import_scan_results.json"):
        print("未找到 import_scan_results.json，请先运行导入扫描")
        return {}
    
    with open("import_scan_results.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def get_package_mapping():
    """获取导入名到包名的映射"""
    mapping = {
        # 常见的导入名到包名映射
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'sklearn': 'scikit-learn',
        'skimage': 'scikit-image',
        'bs4': 'beautifulsoup4',
        'dateutil': 'python-dateutil',
        'magic': 'python-magic',
        'jwt': 'PyJWT',
        'flask_cors': 'Flask-CORS',
        'redis': 'redis',
        'psutil': 'psutil',
        'requests': 'requests',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'plotly': 'plotly',
        'torch': 'torch',
        'transformers': 'transformers',
        'huggingface_hub': 'huggingface-hub',
        'loguru': 'loguru',
        'tqdm': 'tqdm',
        'colorama': 'colorama',
        'jieba': 'jieba',
        'langdetect': 'langdetect',
        'scipy': 'scipy',
        'networkx': 'networkx',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'aiofiles': 'aiofiles',
        'watchdog': 'watchdog',
        'chardet': 'chardet',
        'lxml': 'lxml',
        'joblib': 'joblib',
        'schedule': 'schedule',
        'ffmpeg': 'ffmpeg-python',
        'tiktoken': 'tiktoken',
        'modelscope': 'modelscope',
        'memory_profiler': 'memory-profiler',
        'pyarrow': 'pyarrow',
        'cpuinfo': 'py-cpuinfo',
        'tabulate': 'tabulate',
        'pytest': 'pytest',
        'coverage': 'coverage',
        'pkg_resources': 'setuptools',
        'mpl_toolkits': 'matplotlib',
        'PyQt6': 'PyQt6',
        'PyQt5': 'PyQt5',
        'tkinter': 'tkinter',  # 内置模块
    }
    return mapping

def categorize_imports(used_imports):
    """分类导入的模块"""
    stdlib_modules = {
        'os', 'sys', 'typing', 'logging', 'pathlib', 'json', 'time', 'datetime',
        'threading', 're', 'argparse', 'enum', 'shutil', 'platform', 'dataclasses',
        'gc', 'random', 'traceback', 'hashlib', 'tempfile', 'collections', 'math',
        'xml', 'uuid', 'importlib', 'asyncio', 'functools', 'copy', 'weakref',
        'ctypes', 'unittest', 'base64', 'glob', 'concurrent', 'zipfile', 'pickle',
        'abc', 'io', 'warnings', 'stat', 'queue', 'hmac', 'inspect', 'csv',
        'locale', 'urllib', 'ast', 'statistics', 'signal', 'contextlib',
        'webbrowser', 'textwrap', 'unicodedata', 'atexit', 'zlib', 'multiprocessing',
        'mmap', 'struct', 'socket', 'bisect', 'http', 'setuptools', 'py_compile',
        'compileall', 'ipaddress', 'gzip', 'bz2', 'lzma', 'secrets', 'getpass',
        'packaging', 'tracemalloc', 'codecs', 'types', 'binascii', 'mimetypes',
        'fnmatch', 'string', 'builtins', 'tkinter'
    }
    
    project_modules = {
        'src', 'ui', 'tests', 'configs', 'models', 'core', 'training',
        'knowledge_base', 'utils', 'docs', 'test'
    }
    
    categorized = {
        'stdlib': {},
        'third_party': {},
        'project': {},
        'unknown': {}
    }
    
    for module, files in used_imports.items():
        if module in stdlib_modules:
            categorized['stdlib'][module] = files
        elif module in project_modules or module.startswith('simple_ui') or module.startswith('test_'):
            categorized['project'][module] = files
        elif module.startswith('.') or '.' in module:
            categorized['project'][module] = files
        else:
            categorized['third_party'][module] = files
    
    return categorized

def check_installed_packages():
    """检查已安装的包"""
    try:
        installed = [pkg.project_name.lower() for pkg in pkg_resources.working_set]
        return set(installed)
    except Exception as e:
        print(f"检查已安装包时出错: {e}")
        return set()

def analyze_dependencies():
    """分析依赖项"""
    print("🔍 开始分析VisionAI-ClipsMaster项目依赖项...")
    print("=" * 80)
    
    # 1. 加载数据
    declared_deps = load_declared_dependencies()
    used_imports = load_used_imports()
    installed_packages = check_installed_packages()
    package_mapping = get_package_mapping()
    
    print(f"📋 已声明依赖: {len(declared_deps)} 个")
    print(f"📦 实际导入: {len(used_imports)} 个模块")
    print(f"💾 已安装包: {len(installed_packages)} 个")
    print()
    
    # 2. 分类导入
    categorized = categorize_imports(used_imports)
    
    print("📊 导入分类统计:")
    print(f"  - 标准库模块: {len(categorized['stdlib'])} 个")
    print(f"  - 第三方包: {len(categorized['third_party'])} 个") 
    print(f"  - 项目模块: {len(categorized['project'])} 个")
    print()
    
    # 3. 分析缺失依赖
    missing_deps = []
    for module, files in categorized['third_party'].items():
        package_name = package_mapping.get(module, module).lower()
        if package_name not in declared_deps and package_name not in installed_packages:
            missing_deps.append({
                'import_name': module,
                'package_name': package_name,
                'files_count': len(files),
                'sample_files': files[:3]
            })
    
    # 4. 分析未使用依赖
    used_packages = set()
    for module in categorized['third_party'].keys():
        package_name = package_mapping.get(module, module).lower()
        used_packages.add(package_name)
    
    unused_deps = declared_deps - used_packages
    
    # 5. 分析版本冲突（简化版）
    version_conflicts = []
    
    return {
        'declared_deps': declared_deps,
        'used_imports': categorized,
        'missing_deps': missing_deps,
        'unused_deps': unused_deps,
        'version_conflicts': version_conflicts,
        'installed_packages': installed_packages
    }

def generate_report(analysis_result):
    """生成分析报告"""
    print("📄 生成依赖项分析报告...")
    print("=" * 80)

    # 缺失依赖 - 只显示真正的第三方包
    critical_missing = []
    project_missing = []

    for dep in analysis_result['missing_deps']:
        if dep['import_name'] in ['subprocess', 'pprint', 'difflib', 'heapq']:
            # 这些是标准库，不需要安装
            continue
        elif dep['import_name'] in ['xml_builder', 'clipsmaster_sdk', 'timecode', 'qt_chinese_patch',
                                   'advanced_emotion_analysis_engine', 'event_tracer', 'placeholder',
                                   'legal_injector', 'advanced_plot_point_analyzer', 'chinese_ui_engine',
                                   'window_initializer', 'main_layout', 'encoding_fix', 'visionai_clipsmaster',
                                   'emotion_continuity_standalone', 'resource', 'knowledge_service']:
            # 这些是项目内部模块
            project_missing.append(dep)
        else:
            # 真正的第三方依赖
            critical_missing.append(dep)

    if critical_missing:
        print("❌ 缺失的关键第三方依赖项:")
        for dep in sorted(critical_missing, key=lambda x: x['files_count'], reverse=True):
            print(f"  - {dep['package_name']} (导入为 {dep['import_name']})")
            print(f"    使用文件数: {dep['files_count']}")
            print(f"    安装命令: pip install {dep['package_name']}")
            print()
    else:
        print("✅ 未发现缺失的关键第三方依赖项")
        print()

    if project_missing:
        print("⚠️  项目内部模块导入问题:")
        for dep in sorted(project_missing, key=lambda x: x['files_count'], reverse=True):
            print(f"  - {dep['import_name']} (在 {dep['files_count']} 个文件中使用)")
            print(f"    建议: 检查模块路径或创建缺失的模块文件")
        print()

    # 未使用依赖 - 过滤掉一些明显的开发依赖
    dev_deps = {'pytest', 'black', 'isort', 'mypy', 'flake8', 'pre-commit', 'coverage',
                'pytest-cov', 'pytest-mock', 'pytest-asyncio', 'bandit', 'safety'}

    runtime_unused = [dep for dep in analysis_result['unused_deps'] if dep not in dev_deps]

    if runtime_unused:
        print("⚠️  可能未使用的运行时依赖项 (前20个):")
        for dep in sorted(runtime_unused)[:20]:
            print(f"  - {dep}")
        if len(runtime_unused) > 20:
            print(f"  ... 还有 {len(runtime_unused) - 20} 个")
        print()
    else:
        print("✅ 所有运行时依赖项都在使用中")
        print()

    # 使用频率最高的第三方包
    third_party = analysis_result['used_imports']['third_party']
    if third_party:
        print("📈 使用频率最高的第三方包:")
        sorted_packages = sorted(third_party.items(), key=lambda x: len(x[1]), reverse=True)
        for pkg, files in sorted_packages[:10]:
            print(f"  - {pkg}: {len(files)} 个文件")
        print()

    # 生成修复建议
    print("🔧 修复建议:")
    print("=" * 40)

    if critical_missing:
        print("1. 安装缺失的关键依赖:")
        install_cmd = "pip install " + " ".join([dep['package_name'] for dep in critical_missing])
        print(f"   {install_cmd}")
        print()

    if len(runtime_unused) > 10:
        print("2. 考虑清理未使用的依赖项以减少项目大小")
        print("   建议创建精简版requirements文件")
        print()

    if project_missing:
        print("3. 修复项目内部模块导入问题:")
        print("   检查模块路径配置和PYTHONPATH设置")
        print()

    return analysis_result

def generate_fix_script(analysis_result):
    """生成依赖修复脚本"""
    critical_missing = []
    for dep in analysis_result['missing_deps']:
        if dep['import_name'] not in ['subprocess', 'pprint', 'difflib', 'heapq'] and \
           not dep['import_name'].startswith(('xml_builder', 'clipsmaster_sdk', 'timecode', 'qt_chinese_patch')):
            critical_missing.append(dep)

    if not critical_missing:
        return

    script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
VisionAI-ClipsMaster 依赖修复脚本
自动安装缺失的关键依赖项
\"\"\"

import subprocess
import sys

def install_package(package_name):
    \"\"\"安装单个包\"\"\"
    try:
        print(f"正在安装 {{package_name}}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {{package_name}} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {{package_name}} 安装失败: {{e}}")
        return False

def main():
    \"\"\"主函数\"\"\"
    print("🔧 开始修复VisionAI-ClipsMaster依赖项...")
    print("=" * 50)

    # 需要安装的包列表
    packages_to_install = [
"""

    for dep in critical_missing:
        script_content += f'        "{dep["package_name"]}",  # {dep["import_name"]} - {dep["files_count"]} 个文件使用\n'

    script_content += """    ]

    success_count = 0
    total_count = len(packages_to_install)

    for package in packages_to_install:
        if install_package(package):
            success_count += 1

    print("=" * 50)
    print(f"安装完成: {success_count}/{total_count} 个包安装成功")

    if success_count == total_count:
        print("✅ 所有依赖项安装成功！")
    else:
        print("⚠️  部分依赖项安装失败，请手动检查")

if __name__ == "__main__":
    main()
"""

    with open("fix_dependencies.py", 'w', encoding='utf-8') as f:
        f.write(script_content)

    print("🔧 依赖修复脚本已生成: fix_dependencies.py")

if __name__ == "__main__":
    try:
        analysis_result = analyze_dependencies()
        generate_report(analysis_result)
        generate_fix_script(analysis_result)

        # 保存详细结果
        with open("dependency_analysis_report.json", 'w', encoding='utf-8') as f:
            # 转换set为list以便JSON序列化
            serializable_result = {
                'declared_deps': list(analysis_result['declared_deps']),
                'used_imports': analysis_result['used_imports'],
                'missing_deps': analysis_result['missing_deps'],
                'unused_deps': list(analysis_result['unused_deps']),
                'version_conflicts': analysis_result['version_conflicts'],
                'installed_packages': list(analysis_result['installed_packages'])
            }
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)
        
        print("📁 详细报告已保存到 dependency_analysis_report.json")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
