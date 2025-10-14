#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 环境配置检查工具
确认Python版本兼容性、目录结构和配置文件
"""

import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

class EnvironmentChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            'python_environment': {},
            'directory_structure': {},
            'config_files': {},
            'permissions': {},
            'system_info': {}
        }
    
    def check_python_environment(self):
        """检查Python环境"""
        print("\n🐍 检查Python环境...")
        
        # Python版本
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        # 虚拟环境检查
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        venv_path = sys.prefix if in_venv else None
        
        # 编码设置
        encoding = sys.getdefaultencoding()
        
        results = {
            'version': version_str,
            'compatible': version >= (3, 8),
            'virtual_env': in_venv,
            'venv_path': venv_path,
            'encoding': encoding,
            'executable': sys.executable
        }
        
        print(f"   ✅ Python版本: {version_str}")
        print(f"   {'✅' if in_venv else '⚠️'} 虚拟环境: {'是' if in_venv else '否'}")
        print(f"   ✅ 默认编码: {encoding}")
        
        self.results['python_environment'] = results
        return results
    
    def check_directory_structure(self):
        """检查目录结构"""
        print("\n📁 检查目录结构...")
        
        required_dirs = [
            'src',
            'configs', 
            'cache',
            'logs',
            'output',
            'temp',
            'tools',
            'requirements'
        ]
        
        optional_dirs = [
            'models',
            'data',
            'tests',
            'docs'
        ]
        
        results = {'required': {}, 'optional': {}, 'created': []}
        
        # 检查必需目录
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            exists = dir_path.exists()
            results['required'][dir_name] = exists
            
            if not exists:
                # 尝试创建目录
                try:
                    dir_path.mkdir(exist_ok=True)
                    results['created'].append(dir_name)
                    print(f"   ✅ {dir_name}/ (已创建)")
                except:
                    print(f"   ❌ {dir_name}/ (缺失且无法创建)")
            else:
                print(f"   ✅ {dir_name}/ (存在)")
        
        # 检查可选目录
        for dir_name in optional_dirs:
            dir_path = self.project_root / dir_name
            exists = dir_path.exists()
            results['optional'][dir_name] = exists
            print(f"   {'✅' if exists else 'ℹ️'} {dir_name}/ ({'存在' if exists else '可选'})")
        
        self.results['directory_structure'] = results
        return results
    
    def check_config_files(self):
        """检查配置文件"""
        print("\n⚙️ 检查配置文件...")
        
        config_files = [
            ('configs/auto_download_config.yaml', 'YAML', '自动下载配置'),
            ('configs/ffmpeg_config.json', 'JSON', 'FFmpeg配置'),
            ('configs/model_config.yaml', 'YAML', '模型配置'),
            ('configs/system_settings.yaml', 'YAML', '系统设置'),
            ('requirements.txt', 'TEXT', 'Python依赖'),
            ('requirements/requirements.txt', 'TEXT', '详细依赖'),
        ]
        
        results = {}
        for file_path, file_type, description in config_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            
            file_info = {
                'exists': exists,
                'type': file_type,
                'description': description,
                'valid': False,
                'content': None
            }
            
            if exists:
                try:
                    if file_type == 'JSON':
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        file_info['valid'] = True
                        file_info['content'] = content
                    elif file_type == 'YAML':
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = yaml.safe_load(f)
                        file_info['valid'] = True
                        file_info['content'] = content
                    elif file_type == 'TEXT':
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        file_info['valid'] = len(content.strip()) > 0
                        file_info['content'] = len(content.split('\n'))
                    
                    status = "✅" if file_info['valid'] else "⚠️"
                    print(f"   {status} {file_path} ({description})")
                    
                except Exception as e:
                    file_info['valid'] = False
                    file_info['error'] = str(e)
                    print(f"   ❌ {file_path} (格式错误: {e})")
            else:
                print(f"   ❌ {file_path} (不存在)")
            
            results[file_path] = file_info
        
        self.results['config_files'] = results
        return results
    
    def check_permissions(self):
        """检查文件权限"""
        print("\n🔐 检查文件权限...")
        
        test_dirs = ['cache', 'logs', 'output', 'temp']
        results = {}
        
        for dir_name in test_dirs:
            dir_path = self.project_root / dir_name
            
            # 检查读写权限
            readable = os.access(dir_path, os.R_OK)
            writable = os.access(dir_path, os.W_OK)
            
            results[dir_name] = {
                'readable': readable,
                'writable': writable,
                'full_access': readable and writable
            }
            
            status = "✅" if readable and writable else "❌"
            print(f"   {status} {dir_name}/ (读: {'是' if readable else '否'}, 写: {'是' if writable else '否'})")
        
        self.results['permissions'] = results
        return results
    
    def get_system_info(self):
        """获取系统信息"""
        print("\n💻 系统信息...")
        
        import platform
        import psutil
        
        # 系统信息
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_free': psutil.disk_usage('.').free,
            'cpu_count': psutil.cpu_count()
        }
        
        # 格式化显示
        memory_gb = system_info['memory_total'] / (1024**3)
        disk_gb = system_info['disk_free'] / (1024**3)
        
        print(f"   ✅ 操作系统: {platform.system()} {platform.release()}")
        print(f"   ✅ 处理器: {system_info['cpu_count']} 核心")
        print(f"   ✅ 内存: {memory_gb:.1f} GB")
        print(f"   ✅ 磁盘空间: {disk_gb:.1f} GB")
        
        self.results['system_info'] = system_info
        return system_info
    
    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "=" * 60)
        print("📋 环境配置检查报告")
        print("=" * 60)
        
        # 统计各项检查结果
        py_env = self.results['python_environment']
        dir_struct = self.results['directory_structure']
        config_files = self.results['config_files']
        permissions = self.results['permissions']
        
        # 计算总体状态
        total_checks = 0
        passed_checks = 0
        
        # Python环境
        if py_env.get('compatible', False):
            passed_checks += 1
        total_checks += 1
        
        # 目录结构
        required_dirs = dir_struct.get('required', {})
        for exists in required_dirs.values():
            total_checks += 1
            if exists:
                passed_checks += 1
        
        # 配置文件
        for file_info in config_files.values():
            total_checks += 1
            if file_info.get('valid', False):
                passed_checks += 1
        
        # 权限
        for perm_info in permissions.values():
            total_checks += 1
            if perm_info.get('full_access', False):
                passed_checks += 1
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n📊 总体状态:")
        print(f"   检查项目: {total_checks}")
        print(f"   通过项目: {passed_checks}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"   状态: ✅ 优秀")
        elif success_rate >= 75:
            print(f"   状态: ✅ 良好")
        elif success_rate >= 60:
            print(f"   状态: ⚠️ 需要注意")
        else:
            print(f"   状态: ❌ 需要修复")
        
        return {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'success_rate': success_rate
        }

def main():
    """主检查函数"""
    checker = EnvironmentChecker()
    
    print("=" * 60)
    print("🔍 VisionAI-ClipsMaster 环境配置检查")
    print("=" * 60)
    
    # 执行各项检查
    checker.check_python_environment()
    checker.check_directory_structure()
    checker.check_config_files()
    checker.check_permissions()
    checker.get_system_info()
    
    # 生成最终报告
    summary = checker.generate_final_report()
    
    return checker.results, summary

if __name__ == "__main__":
    main()
