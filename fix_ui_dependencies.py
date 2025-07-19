"""
VisionAI-ClipsMaster UI依赖修复脚本
自动检测和修复UI组件的依赖问题
"""

import os
import sys
import subprocess
import importlib
from typing import List, Dict, Any

class UIDependencyFixer:
    """UI依赖修复器"""
    
    def __init__(self):
        self.required_packages = [
            'PyQt6',
            'psutil',
            'GPUtil'  # 可选，用于GPU监控
        ]
        self.optional_packages = [
            'matplotlib',  # 用于高级图表
            'numpy',       # 数值计算
            'pillow'       # 图像处理
        ]
        self.fix_results = {}
    
    def check_package(self, package_name: str) -> Dict[str, Any]:
        """检查包是否已安装"""
        try:
            module = importlib.import_module(package_name)
            version = getattr(module, '__version__', 'Unknown')
            return {
                'installed': True,
                'version': version,
                'module': module
            }
        except ImportError as e:
            return {
                'installed': False,
                'error': str(e)
            }
    
    def install_package(self, package_name: str) -> bool:
        """安装包"""
        try:
            print(f"正在安装 {package_name}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"✅ {package_name} 安装成功")
                return True
            else:
                print(f"❌ {package_name} 安装失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ {package_name} 安装超时")
            return False
        except Exception as e:
            print(f"❌ {package_name} 安装异常: {e}")
            return False
    
    def fix_pyqt6_issues(self) -> bool:
        """修复PyQt6相关问题"""
        try:
            print("🔧 检查PyQt6安装...")
            
            # 检查PyQt6核心模块
            pyqt6_modules = [
                'PyQt6.QtCore',
                'PyQt6.QtWidgets',
                'PyQt6.QtGui'
            ]
            
            missing_modules = []
            for module in pyqt6_modules:
                check_result = self.check_package(module)
                if not check_result['installed']:
                    missing_modules.append(module)
            
            if missing_modules:
                print(f"发现缺失的PyQt6模块: {missing_modules}")
                # 重新安装PyQt6
                return self.install_package('PyQt6')
            else:
                print("✅ PyQt6模块完整")
                return True
                
        except Exception as e:
            print(f"❌ PyQt6检查失败: {e}")
            return False
    
    def fix_psutil_issues(self) -> bool:
        """修复psutil相关问题"""
        try:
            print("🔧 检查psutil安装...")
            
            check_result = self.check_package('psutil')
            if not check_result['installed']:
                print("psutil未安装，正在安装...")
                return self.install_package('psutil')
            else:
                print(f"✅ psutil已安装，版本: {check_result['version']}")
                
                # 测试psutil功能
                import psutil
                try:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory_info = psutil.virtual_memory()
                    print(f"✅ psutil功能测试通过 (CPU: {cpu_percent}%, 内存: {memory_info.percent}%)")
                    return True
                except Exception as e:
                    print(f"❌ psutil功能测试失败: {e}")
                    return False
                
        except Exception as e:
            print(f"❌ psutil检查失败: {e}")
            return False
    
    def fix_gpu_monitoring(self) -> bool:
        """修复GPU监控功能"""
        try:
            print("🔧 检查GPU监控依赖...")
            
            check_result = self.check_package('GPUtil')
            if not check_result['installed']:
                print("GPUtil未安装，正在安装...")
                success = self.install_package('GPUtil')
                if not success:
                    print("⚠️ GPUtil安装失败，GPU监控将使用CPU模式")
                    return True  # 不是必需的，所以返回True
            else:
                print(f"✅ GPUtil已安装，版本: {check_result['version']}")
            
            # 测试GPU检测
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    print(f"✅ 检测到 {len(gpus)} 个GPU设备")
                    for i, gpu in enumerate(gpus):
                        print(f"  GPU {i}: {gpu.name}")
                else:
                    print("ℹ️ 未检测到GPU设备，将使用CPU模式")
                return True
                
            except Exception as e:
                print(f"⚠️ GPU检测失败: {e}，将使用CPU模式")
                return True  # GPU不是必需的
                
        except Exception as e:
            print(f"❌ GPU监控检查失败: {e}")
            return True  # GPU不是必需的
    
    def create_test_data(self) -> bool:
        """创建测试数据"""
        try:
            print("🔧 创建测试数据...")
            
            # 确保测试目录存在
            test_data_dir = os.path.join('tests', 'data')
            os.makedirs(test_data_dir, exist_ok=True)
            
            # 创建测试SRT文件
            test_srt_content = """1
00:00:00,000 --> 00:00:03,000
这是测试字幕第一行

2
00:00:03,000 --> 00:00:06,000
这是测试字幕第二行

3
00:00:06,000 --> 00:00:09,000
这是测试字幕第三行
"""
            
            original_srt = os.path.join(test_data_dir, 'test_original.srt')
            with open(original_srt, 'w', encoding='utf-8') as f:
                f.write(test_srt_content)
            
            viral_srt_content = """1
00:00:00,000 --> 00:00:02,000
震惊！真相大白

2
00:00:02,000 --> 00:00:04,000
接下来让人意想不到

3
00:00:04,000 --> 00:00:06,000
结局出人意料
"""
            
            viral_srt = os.path.join(test_data_dir, 'test_viral.srt')
            with open(viral_srt, 'w', encoding='utf-8') as f:
                f.write(viral_srt_content)
            
            print(f"✅ 测试数据创建成功:")
            print(f"  - {original_srt}")
            print(f"  - {viral_srt}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建测试数据失败: {e}")
            return False
    
    def update_requirements_txt(self) -> bool:
        """更新requirements.txt文件"""
        try:
            print("🔧 更新requirements.txt...")
            
            requirements_content = """# VisionAI-ClipsMaster UI Dependencies
PyQt6>=6.4.0
psutil>=5.9.0
GPUtil>=1.4.0

# Optional dependencies for advanced features
matplotlib>=3.6.0
numpy>=1.21.0
Pillow>=9.0.0

# Core AI dependencies
torch>=2.0.0
transformers>=4.20.0

# Video processing
opencv-python>=4.6.0
ffmpeg-python>=0.2.0

# Development and testing
pytest>=7.0.0
pytest-qt>=4.2.0
"""
            
            with open('requirements.txt', 'w', encoding='utf-8') as f:
                f.write(requirements_content)
            
            print("✅ requirements.txt 更新成功")
            return True
            
        except Exception as e:
            print(f"❌ 更新requirements.txt失败: {e}")
            return False
    
    def run_dependency_check(self) -> Dict[str, Any]:
        """运行完整的依赖检查"""
        print("🚀 开始UI依赖检查和修复...")
        print("=" * 50)
        
        results = {
            'pyqt6_fix': self.fix_pyqt6_issues(),
            'psutil_fix': self.fix_psutil_issues(),
            'gpu_monitoring_fix': self.fix_gpu_monitoring(),
            'test_data_creation': self.create_test_data(),
            'requirements_update': self.update_requirements_txt()
        }
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print("\n" + "=" * 50)
        print("🎯 依赖修复完成!")
        print(f"✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print("🎉 所有依赖问题已修复!")
        else:
            print("⚠️ 部分依赖问题需要手动处理")
        
        return results
    
    def generate_fix_report(self, results: Dict[str, Any]) -> str:
        """生成修复报告"""
        report = f"""# VisionAI-ClipsMaster UI依赖修复报告

## 修复结果概览
- PyQt6修复: {'✅ 成功' if results['pyqt6_fix'] else '❌ 失败'}
- psutil修复: {'✅ 成功' if results['psutil_fix'] else '❌ 失败'}
- GPU监控修复: {'✅ 成功' if results['gpu_monitoring_fix'] else '❌ 失败'}
- 测试数据创建: {'✅ 成功' if results['test_data_creation'] else '❌ 失败'}
- requirements.txt更新: {'✅ 成功' if results['requirements_update'] else '❌ 失败'}

## 下一步建议
1. 运行 `pip install -r requirements.txt` 确保所有依赖已安装
2. 重新运行UI测试: `python tests/ui_integration_test.py`
3. 如有问题，请检查Python环境和包管理器设置

## 生成时间
{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        with open('UI_Dependency_Fix_Report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report

def main():
    """主函数"""
    fixer = UIDependencyFixer()
    results = fixer.run_dependency_check()
    report = fixer.generate_fix_report(results)
    
    print(f"\n📄 修复报告已保存: UI_Dependency_Fix_Report.md")
    
    # 如果所有修复都成功，运行测试
    if all(results.values()):
        print("\n🧪 正在运行UI测试验证修复效果...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, 'tests/ui_integration_test.py'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ UI测试验证通过!")
            else:
                print("❌ UI测试验证失败，请检查输出:")
                print(result.stdout)
                print(result.stderr)
                
        except Exception as e:
            print(f"⚠️ 无法运行UI测试验证: {e}")

if __name__ == "__main__":
    main()
