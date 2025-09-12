#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 训练依赖安装脚本
安装真实机器学习训练所需的依赖库，优先使用国内镜像源
"""

import subprocess
import sys
import os
from typing import List, Dict, Any

class DependencyInstaller:
    """依赖安装器"""
    
    def __init__(self):
        """初始化安装器"""
        # 国内镜像源配置
        self.mirror_sources = [
            "https://pypi.tuna.tsinghua.edu.cn/simple/",  # 清华大学
            "https://mirrors.aliyun.com/pypi/simple/",     # 阿里云
            "https://pypi.douban.com/simple/",             # 豆瓣
            "https://pypi.mirrors.ustc.edu.cn/simple/"     # 中科大
        ]
        
        # 必需的依赖库
        self.required_packages = {
            "peft": ">=0.4.0",
            "datasets": ">=2.0.0", 
            "accelerate": ">=0.20.0",
            "bitsandbytes": ">=0.39.0",  # 量化支持
            "sentencepiece": ">=0.1.99"  # 分词器支持
        }
        
        # 可选的依赖库
        self.optional_packages = {
            "wandb": ">=0.15.0",  # 训练监控
            "tensorboard": ">=2.13.0"  # 日志记录
        }
        
        print("🚀 VisionAI-ClipsMaster 训练依赖安装器")
        print("=" * 50)
    
    def check_existing_packages(self) -> Dict[str, Any]:
        """检查已安装的包"""
        print("📦 检查当前已安装的包...")
        
        package_status = {}
        
        for package, version in self.required_packages.items():
            try:
                __import__(package)
                # 获取版本信息
                try:
                    if package == "peft":
                        import peft
                        current_version = peft.__version__
                    elif package == "datasets":
                        import datasets
                        current_version = datasets.__version__
                    elif package == "accelerate":
                        import accelerate
                        current_version = accelerate.__version__
                    elif package == "bitsandbytes":
                        import bitsandbytes
                        current_version = bitsandbytes.__version__
                    elif package == "sentencepiece":
                        import sentencepiece
                        current_version = "已安装"
                    else:
                        current_version = "未知版本"
                except:
                    current_version = "已安装"
                
                package_status[package] = {
                    "installed": True,
                    "version": current_version,
                    "required": version
                }
                print(f"  ✅ {package}: {current_version}")
                
            except ImportError:
                package_status[package] = {
                    "installed": False,
                    "version": None,
                    "required": version
                }
                print(f"  ❌ {package}: 未安装 (需要 {version})")
        
        return package_status
    
    def install_package(self, package: str, version: str, mirror_index: int = 0) -> bool:
        """安装单个包"""
        if mirror_index >= len(self.mirror_sources):
            print(f"❌ 所有镜像源都失败，无法安装 {package}")
            return False
        
        mirror = self.mirror_sources[mirror_index]
        package_spec = f"{package}{version}"
        
        print(f"📥 正在安装 {package_spec} (使用镜像: {mirror})")
        
        try:
            cmd = [
                sys.executable, "-m", "pip", "install", 
                package_spec, "-i", mirror, "--trusted-host", 
                mirror.split("//")[1].split("/")[0]
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"  ✅ {package} 安装成功")
                return True
            else:
                print(f"  ⚠️ {package} 安装失败，尝试下一个镜像源")
                print(f"     错误信息: {result.stderr[:200]}")
                return self.install_package(package, version, mirror_index + 1)
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {package} 安装超时，尝试下一个镜像源")
            return self.install_package(package, version, mirror_index + 1)
        except Exception as e:
            print(f"  ❌ {package} 安装异常: {str(e)}")
            return self.install_package(package, version, mirror_index + 1)
    
    def install_missing_packages(self, package_status: Dict[str, Any]) -> bool:
        """安装缺失的包"""
        missing_packages = [
            (pkg, info["required"]) 
            for pkg, info in package_status.items() 
            if not info["installed"]
        ]
        
        if not missing_packages:
            print("✅ 所有必需依赖已安装")
            return True
        
        print(f"📥 需要安装 {len(missing_packages)} 个缺失的包...")
        
        success_count = 0
        for package, version in missing_packages:
            if self.install_package(package, version):
                success_count += 1
            else:
                print(f"❌ {package} 安装失败")
        
        print(f"📊 安装结果: {success_count}/{len(missing_packages)} 成功")
        return success_count == len(missing_packages)
    
    def verify_installation(self) -> bool:
        """验证安装结果"""
        print("🔍 验证安装结果...")
        
        verification_results = {}
        
        # 验证核心功能
        try:
            # 测试transformers
            from transformers import AutoTokenizer
            verification_results["transformers"] = True
            print("  ✅ transformers: 正常")
        except Exception as e:
            verification_results["transformers"] = False
            print(f"  ❌ transformers: 异常 - {e}")
        
        # 测试peft
        try:
            from peft import LoraConfig, get_peft_model, TaskType
            verification_results["peft"] = True
            print("  ✅ peft: 正常")
        except Exception as e:
            verification_results["peft"] = False
            print(f"  ❌ peft: 异常 - {e}")
        
        # 测试datasets
        try:
            from datasets import Dataset
            verification_results["datasets"] = True
            print("  ✅ datasets: 正常")
        except Exception as e:
            verification_results["datasets"] = False
            print(f"  ❌ datasets: 异常 - {e}")
        
        # 测试torch
        try:
            import torch
            verification_results["torch"] = True
            print(f"  ✅ torch: {torch.__version__}")
        except Exception as e:
            verification_results["torch"] = False
            print(f"  ❌ torch: 异常 - {e}")
        
        success_rate = sum(verification_results.values()) / len(verification_results)
        print(f"📊 验证成功率: {success_rate*100:.1f}%")
        
        return success_rate >= 0.75  # 75%以上成功率认为可用
    
    def run_installation(self) -> bool:
        """运行完整的安装流程"""
        print("🚀 开始安装训练依赖...")
        
        try:
            # 1. 检查现有包
            package_status = self.check_existing_packages()
            
            # 2. 安装缺失包
            if not self.install_missing_packages(package_status):
                print("❌ 依赖安装失败")
                return False
            
            # 3. 验证安装
            if not self.verify_installation():
                print("❌ 安装验证失败")
                return False
            
            print("✅ 所有训练依赖安装完成！")
            return True
            
        except Exception as e:
            print(f"❌ 安装过程异常: {e}")
            return False

def main():
    """主函数"""
    installer = DependencyInstaller()
    success = installer.run_installation()
    
    if success:
        print("\n🎉 依赖安装成功！现在可以开始真实训练了。")
    else:
        print("\n💡 如果安装失败，请尝试手动安装:")
        print("pip install peft datasets accelerate bitsandbytes sentencepiece -i https://pypi.tuna.tsinghua.edu.cn/simple/")
    
    return success

if __name__ == "__main__":
    main()
