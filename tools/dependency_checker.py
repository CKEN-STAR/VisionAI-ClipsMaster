#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 依赖检查工具
全面检查项目的所有依赖安装状态
"""

import sys
import os
import subprocess
import importlib
import pkg_resources
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional

class DependencyChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            'python_packages': {},
            'system_dependencies': {},
            'functional_modules': {},
            'environment_config': {},
            'summary': {}
        }
    
    def check_python_version(self) -> Tuple[bool, str]:
        """检查Python版本兼容性"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        # 项目要求Python 3.8+
        if version >= (3, 8):
            return True, f"✅ Python {version_str} (兼容)"
        else:
            return False, f"❌ Python {version_str} (需要3.8+)"
    
    def parse_requirements(self, req_file: str) -> List[Dict]:
        """解析requirements文件"""
        requirements = []
        req_path = self.project_root / req_file
        
        if not req_path.exists():
            return requirements
            
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 简单解析包名和版本要求
                    if '>=' in line:
                        name, version = line.split('>=')
                        requirements.append({
                            'name': name.strip(),
                            'required_version': version.strip(),
                            'operator': '>='
                        })
                    elif '==' in line:
                        name, version = line.split('==')
                        requirements.append({
                            'name': name.strip(),
                            'required_version': version.strip(),
                            'operator': '=='
                        })
                    else:
                        requirements.append({
                            'name': line.strip(),
                            'required_version': None,
                            'operator': None
                        })
        
        return requirements
    
    def check_package_installation(self, package_name: str) -> Tuple[bool, str, Optional[str]]:
        """检查单个包的安装状态"""
        try:
            # 尝试导入包
            importlib.import_module(package_name.lower().replace('-', '_'))
            
            # 获取版本信息
            try:
                version = pkg_resources.get_distribution(package_name).version
                return True, f"✅ {package_name} v{version}", version
            except:
                return True, f"✅ {package_name} (已安装，版本未知)", None
                
        except ImportError:
            try:
                # 尝试通过pip检查
                result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 包已安装但可能导入名称不同
                    lines = result.stdout.split('\n')
                    version_line = [l for l in lines if l.startswith('Version:')]
                    version = version_line[0].split(':')[1].strip() if version_line else 'Unknown'
                    return True, f"⚠️ {package_name} v{version} (已安装但导入失败)", version
                else:
                    return False, f"❌ {package_name} (未安装)", None
            except:
                return False, f"❌ {package_name} (检查失败)", None
    
    def check_critical_imports(self) -> Dict[str, Tuple[bool, str]]:
        """检查关键模块的导入状态"""
        critical_modules = {
            'PyQt6': 'PyQt6.QtWidgets',
            'torch': 'torch',
            'numpy': 'numpy',
            'opencv': 'cv2',
            'transformers': 'transformers',
            'matplotlib': 'matplotlib.pyplot',
            'plotly': 'plotly.graph_objects',
            'requests': 'requests',
            'yaml': 'yaml',
            'jieba': 'jieba',
            'spacy': 'spacy',
            'psutil': 'psutil',
            'GPUtil': 'GPUtil',
            'loguru': 'loguru'
        }
        
        results = {}
        for name, module_path in critical_modules.items():
            try:
                importlib.import_module(module_path)
                results[name] = (True, f"✅ {name} 导入成功")
            except ImportError as e:
                results[name] = (False, f"❌ {name} 导入失败: {str(e)}")
            except Exception as e:
                results[name] = (False, f"⚠️ {name} 导入异常: {str(e)}")
        
        return results
    
    def check_version_conflicts(self) -> List[str]:
        """检查版本冲突"""
        conflicts = []
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'check'], 
                                  capture_output=True, text=True)
            if result.returncode != 0 and result.stdout.strip():
                conflicts = result.stdout.strip().split('\n')
        except:
            pass
        
        return conflicts
    
    def run_python_package_check(self):
        """运行Python包检查"""
        print("🔍 检查Python依赖包...")
        
        # 检查requirements.txt中的包
        requirements = self.parse_requirements('requirements.txt')
        
        package_results = {}
        for req in requirements:
            is_installed, status, version = self.check_package_installation(req['name'])
            package_results[req['name']] = {
                'installed': is_installed,
                'status': status,
                'installed_version': version,
                'required_version': req.get('required_version'),
                'operator': req.get('operator')
            }
        
        # 检查关键模块导入
        import_results = self.check_critical_imports()
        
        # 检查版本冲突
        conflicts = self.check_version_conflicts()
        
        self.results['python_packages'] = {
            'requirements_check': package_results,
            'import_check': import_results,
            'version_conflicts': conflicts
        }
        
        # 统计结果
        total_packages = len(package_results)
        installed_packages = sum(1 for r in package_results.values() if r['installed'])
        successful_imports = sum(1 for r in import_results.values() if r[0])
        
        print(f"\n📊 Python包检查结果:")
        print(f"   总包数: {total_packages}")
        print(f"   已安装: {installed_packages}")
        print(f"   成功导入: {successful_imports}/{len(import_results)}")
        print(f"   版本冲突: {len(conflicts)}")
        
        return package_results, import_results, conflicts

    def check_ffmpeg_status(self) -> Tuple[bool, str, Dict]:
        """检查FFmpeg状态"""
        ffmpeg_info = {
            'system_path': False,
            'project_local': False,
            'config_file': False,
            'executable_test': False,
            'details': {}
        }

        # 1. 检查系统PATH中的FFmpeg
        import shutil
        system_ffmpeg = shutil.which('ffmpeg')
        if system_ffmpeg:
            ffmpeg_info['system_path'] = True
            ffmpeg_info['details']['system_path'] = system_ffmpeg

            # 测试FFmpeg可执行性
            try:
                result = subprocess.run([system_ffmpeg, '-version'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    ffmpeg_info['executable_test'] = True
                    version_line = result.stdout.split('\n')[0]
                    ffmpeg_info['details']['version'] = version_line
            except:
                pass

        # 2. 检查项目本地FFmpeg
        local_paths = [
            self.project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            self.project_root / "ffmpeg" / "ffmpeg.exe",
            self.project_root / "ffmpeg" / "bin" / "ffmpeg.exe"
        ]

        for path in local_paths:
            if path.exists():
                ffmpeg_info['project_local'] = True
                ffmpeg_info['details']['local_path'] = str(path)
                break

        # 3. 检查配置文件
        config_file = self.project_root / "configs" / "ffmpeg_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                ffmpeg_info['config_file'] = True
                ffmpeg_info['details']['config'] = config
            except:
                pass

        # 生成状态消息
        if ffmpeg_info['system_path'] and ffmpeg_info['executable_test']:
            status = "✅ FFmpeg已安装且可用"
        elif ffmpeg_info['project_local']:
            status = "⚠️ FFmpeg在项目本地，需要配置PATH"
        elif ffmpeg_info['config_file']:
            config = ffmpeg_info['details'].get('config', {})
            if config.get('skip_ffmpeg_check'):
                status = "ℹ️ FFmpeg检查已跳过（配置模式）"
            else:
                status = "⚠️ FFmpeg配置文件存在但未验证"
        else:
            status = "❌ FFmpeg未找到"

        return ffmpeg_info['system_path'] or ffmpeg_info['project_local'], status, ffmpeg_info

    def check_system_dependencies(self):
        """检查系统依赖"""
        print("\n🖥️ 检查系统依赖...")

        # FFmpeg检查
        ffmpeg_ok, ffmpeg_msg, ffmpeg_info = self.check_ffmpeg_status()

        # 其他系统检查
        system_results = {
            'ffmpeg': {
                'available': ffmpeg_ok,
                'status': ffmpeg_msg,
                'details': ffmpeg_info
            }
        }

        self.results['system_dependencies'] = system_results

        print(f"   {ffmpeg_msg}")

        return system_results

def main():
    """主检查函数"""
    checker = DependencyChecker()

    print("=" * 60)
    print("🔍 VisionAI-ClipsMaster 依赖状态检查")
    print("=" * 60)

    # 1. Python版本检查
    py_ok, py_msg = checker.check_python_version()
    print(f"\n🐍 Python版本: {py_msg}")

    # 2. Python包检查
    pkg_results, import_results, conflicts = checker.run_python_package_check()

    # 3. 系统依赖检查
    system_results = checker.check_system_dependencies()

    # 显示详细结果
    print(f"\n📦 依赖包详细状态:")
    for name, info in pkg_results.items():
        print(f"   {info['status']}")

    print(f"\n🔧 关键模块导入测试:")
    for name, (success, msg) in import_results.items():
        print(f"   {msg}")

    if conflicts:
        print(f"\n⚠️ 版本冲突:")
        for conflict in conflicts:
            print(f"   {conflict}")
    else:
        print(f"\n✅ 无版本冲突")

    return checker.results

if __name__ == "__main__":
    main()
