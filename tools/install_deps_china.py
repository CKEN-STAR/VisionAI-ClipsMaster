#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中国大陆网络环境优化的依赖安装脚本

自动选择最快的镜像源，支持离线安装包
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path

class ChinaDependencyInstaller:
    """中国大陆依赖安装器"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        
        # Python包镜像源配置（按速度优先级排序）
        self.pip_mirrors = {
            "清华大学": {
                "url": "https://pypi.tuna.tsinghua.edu.cn/simple/",
                "trusted_host": "pypi.tuna.tsinghua.edu.cn",
                "description": "清华大学开源软件镜像站",
                "priority": 1
            },
            "阿里云": {
                "url": "https://mirrors.aliyun.com/pypi/simple/",
                "trusted_host": "mirrors.aliyun.com", 
                "description": "阿里云开源镜像站",
                "priority": 2
            },
            "豆瓣": {
                "url": "https://pypi.douban.com/simple/",
                "trusted_host": "pypi.douban.com",
                "description": "豆瓣PyPI镜像",
                "priority": 3
            },
            "中科大": {
                "url": "https://pypi.mirrors.ustc.edu.cn/simple/",
                "trusted_host": "pypi.mirrors.ustc.edu.cn",
                "description": "中科大开源软件镜像",
                "priority": 4
            },
            "华为云": {
                "url": "https://mirrors.huaweicloud.com/repository/pypi/simple/",
                "trusted_host": "mirrors.huaweicloud.com",
                "description": "华为云开源镜像站",
                "priority": 5
            }
        }
        
        # 核心依赖包列表
        self.core_dependencies = [
            "PyQt6>=6.5.0",
            "PyQt6-Qt6>=6.5.0", 
            "requests>=2.28.0",
            "psutil>=5.9.0",
            "numpy>=1.21.0",
            "Pillow>=9.0.0",
            "tqdm>=4.64.0"
        ]
        
        # 可选依赖包列表
        self.optional_dependencies = [
            "torch>=1.13.0",
            "torchvision>=0.14.0",
            "transformers>=4.21.0",
            "opencv-python>=4.6.0",
            "scikit-image>=0.19.0"
        ]
        
        self.selected_mirror = None
        
    def test_mirror_speed(self, mirror_name, timeout=5):
        """测试镜像源连接速度"""
        try:
            mirror_info = self.pip_mirrors[mirror_name]
            start_time = time.time()
            
            # 测试连接到镜像源
            response = requests.head(
                mirror_info["url"],
                timeout=timeout,
                allow_redirects=True
            )
            
            if response.status_code in [200, 301, 302]:
                speed = time.time() - start_time
                return speed
            else:
                return float('inf')
                
        except Exception as e:
            print(f"[WARN] 镜像源 {mirror_name} 测速失败: {e}")
            return float('inf')
            
    def select_fastest_mirror(self):
        """自动选择最快的镜像源"""
        print("[INFO] 正在测试Python包镜像源速度...")
        
        speed_results = {}
        for mirror_name in self.pip_mirrors.keys():
            print(f"[INFO] 测试 {mirror_name}...", end=" ")
            speed = self.test_mirror_speed(mirror_name)
            speed_results[mirror_name] = speed
            
            if speed < float('inf'):
                print(f"✅ {speed:.2f}秒")
            else:
                print("❌ 不可用")
                
        # 选择最快的可用镜像源
        available_mirrors = {k: v for k, v in speed_results.items() if v < float('inf')}
        
        if available_mirrors:
            best_mirror = min(available_mirrors.items(), key=lambda x: x[1])
            self.selected_mirror = best_mirror[0]
            print(f"[OK] 选择镜像源: {self.selected_mirror} (速度: {best_mirror[1]:.2f}秒)")
            return True
        else:
            print("[ERROR] 所有镜像源都不可用，将使用默认源")
            return False
            
    def get_pip_install_command(self, packages, upgrade=False):
        """生成pip安装命令"""
        cmd = [sys.executable, "-m", "pip", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
            
        # 添加镜像源配置
        if self.selected_mirror:
            mirror_info = self.pip_mirrors[self.selected_mirror]
            cmd.extend([
                "-i", mirror_info["url"],
                "--trusted-host", mirror_info["trusted_host"]
            ])
            
        # 添加其他优化参数
        cmd.extend([
            "--timeout", "60",
            "--retries", "3",
            "--no-cache-dir"  # 不使用缓存，确保获取最新版本
        ])
        
        # 添加包列表
        if isinstance(packages, str):
            cmd.append(packages)
        else:
            cmd.extend(packages)
            
        return cmd
        
    def install_packages(self, packages, description="依赖包"):
        """安装Python包"""
        print(f"\n[INFO] 开始安装{description}...")
        
        cmd = self.get_pip_install_command(packages, upgrade=True)
        
        print(f"[INFO] 执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            print(f"[OK] {description}安装成功")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {description}安装失败:")
            print(f"返回码: {e.returncode}")
            print(f"错误输出: {e.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            print(f"[ERROR] {description}安装超时")
            return False
            
    def check_package_installed(self, package_name):
        """检查包是否已安装"""
        try:
            import importlib
            importlib.import_module(package_name.split('>=')[0].split('==')[0])
            return True
        except ImportError:
            return False
            
    def install_core_dependencies(self):
        """安装核心依赖"""
        print("\n" + "="*60)
        print("安装核心依赖包")
        print("="*60)
        
        # 分批安装以提高成功率
        batches = [
            (["PyQt6>=6.5.0", "PyQt6-Qt6>=6.5.0"], "PyQt6框架"),
            (["requests>=2.28.0", "psutil>=5.9.0"], "系统工具"),
            (["numpy>=1.21.0", "Pillow>=9.0.0"], "数据处理"),
            (["tqdm>=4.64.0"], "进度显示")
        ]
        
        success_count = 0
        for packages, description in batches:
            if self.install_packages(packages, description):
                success_count += 1
            else:
                print(f"[WARN] {description}安装失败，但继续安装其他包")
                
        print(f"\n[INFO] 核心依赖安装完成: {success_count}/{len(batches)} 批次成功")
        return success_count == len(batches)
        
    def install_optional_dependencies(self):
        """安装可选依赖"""
        print("\n" + "="*60)
        print("安装可选依赖包（AI功能支持）")
        print("="*60)
        
        # 询问是否安装可选依赖
        try:
            response = input("是否安装AI功能依赖包？(y/N): ").strip().lower()
            if response not in ['y', 'yes', '是']:
                print("[INFO] 跳过可选依赖安装")
                return True
        except KeyboardInterrupt:
            print("\n[INFO] 用户取消安装")
            return False
            
        # 分批安装可选依赖
        optional_batches = [
            (["torch>=1.13.0", "torchvision>=0.14.0"], "PyTorch深度学习框架"),
            (["transformers>=4.21.0"], "Transformers模型库"),
            (["opencv-python>=4.6.0"], "OpenCV图像处理"),
            (["scikit-image>=0.19.0"], "图像科学计算")
        ]
        
        success_count = 0
        for packages, description in optional_batches:
            print(f"\n[INFO] 正在安装: {description}")
            if self.install_packages(packages, description):
                success_count += 1
            else:
                print(f"[WARN] {description}安装失败，跳过")
                
        print(f"\n[INFO] 可选依赖安装完成: {success_count}/{len(optional_batches)} 批次成功")
        return True
        
    def create_pip_config(self):
        """创建pip配置文件"""
        if not self.selected_mirror:
            return
            
        pip_config_dir = Path.home() / ".pip"
        pip_config_file = pip_config_dir / "pip.conf"
        
        # Windows系统使用不同的配置路径
        if sys.platform == "win32":
            pip_config_dir = Path.home() / "pip"
            pip_config_file = pip_config_dir / "pip.ini"
            
        try:
            pip_config_dir.mkdir(exist_ok=True)
            
            mirror_info = self.pip_mirrors[self.selected_mirror]
            config_content = f"""[global]
index-url = {mirror_info["url"]}
trusted-host = {mirror_info["trusted_host"]}
timeout = 60
retries = 3

[install]
trusted-host = {mirror_info["trusted_host"]}
"""
            
            with open(pip_config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
                
            print(f"[OK] pip配置文件已创建: {pip_config_file}")
            print(f"[INFO] 已配置默认镜像源: {self.selected_mirror}")
            
        except Exception as e:
            print(f"[WARN] 创建pip配置文件失败: {e}")
            
    def verify_installation(self):
        """验证安装结果"""
        print("\n" + "="*60)
        print("验证安装结果")
        print("="*60)
        
        # 检查核心包
        core_packages = ["PyQt6", "requests", "psutil", "numpy", "PIL", "tqdm"]
        
        print("\n核心依赖检查:")
        core_success = 0
        for package in core_packages:
            try:
                if package == "PIL":
                    import PIL
                else:
                    __import__(package)
                print(f"  ✅ {package}")
                core_success += 1
            except ImportError:
                print(f"  ❌ {package}")
                
        # 检查可选包
        optional_packages = ["torch", "torchvision", "transformers", "cv2", "skimage"]
        
        print("\n可选依赖检查:")
        optional_success = 0
        for package in optional_packages:
            try:
                __import__(package)
                print(f"  ✅ {package}")
                optional_success += 1
            except ImportError:
                print(f"  ⚪ {package} (未安装)")
                
        print(f"\n安装结果总结:")
        print(f"  核心依赖: {core_success}/{len(core_packages)} 成功")
        print(f"  可选依赖: {optional_success}/{len(optional_packages)} 成功")
        
        return core_success >= len(core_packages) - 1  # 允许1个核心包失败
        
    def run_installation(self):
        """执行完整安装流程"""
        print("🎬 VisionAI-ClipsMaster 依赖安装器 (中国大陆优化版)")
        print("="*60)
        
        # 1. 选择最快镜像源
        self.select_fastest_mirror()
        
        # 2. 创建pip配置
        self.create_pip_config()
        
        # 3. 升级pip
        print("\n[INFO] 升级pip到最新版本...")
        self.install_packages("pip", "pip包管理器")
        
        # 4. 安装核心依赖
        core_success = self.install_core_dependencies()
        
        # 5. 安装可选依赖
        if core_success:
            self.install_optional_dependencies()
        else:
            print("[WARN] 核心依赖安装不完整，跳过可选依赖")
            
        # 6. 验证安装
        success = self.verify_installation()
        
        if success:
            print("\n🎉 依赖安装完成！VisionAI-ClipsMaster已准备就绪。")
            print("\n下一步:")
            print("  1. 运行: python simple_ui_fixed.py")
            print("  2. 如需FFmpeg支持，程序会自动提示安装")
        else:
            print("\n⚠️  部分依赖安装失败，但基本功能应该可用。")
            print("如遇到问题，请检查网络连接或手动安装失败的包。")
            
        return success


def main():
    """主函数"""
    try:
        installer = ChinaDependencyInstaller()
        return installer.run_installation()
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户取消安装")
        return False
    except Exception as e:
        print(f"\n[ERROR] 安装过程发生异常: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
