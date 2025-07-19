#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI组件修复实现

基于UI组件整合测试结果，实现针对性的修复和优化
"""

import os
import sys
import json
import time
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

class UIComponentsFixer:
    """UI组件修复器"""
    
    def __init__(self):
        self.fixes_applied = []
        self.fixes_failed = []
        
    def apply_memory_optimization(self):
        """应用内存优化修复"""
        print("🔧 应用内存优化修复...")
        
        try:
            # 1. 调整内存阈值
            memory_config = {
                'memory_threshold_mb': 350,  # 从300MB调整到350MB
                'memory_warning_threshold_mb': 400,
                'memory_critical_threshold_mb': 450,
                'gc_frequency': 30,  # 每30秒执行一次垃圾回收
                'cache_cleanup_interval': 60  # 每60秒清理缓存
            }
            
            # 保存内存配置
            config_path = PROJECT_ROOT / "configs" / "memory_optimization.json"
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(memory_config, f, indent=2, ensure_ascii=False)
                
            self.fixes_applied.append("内存阈值优化配置已保存")
            
            # 2. 创建内存优化工具函数
            memory_utils_code = '''
import gc
import psutil
import threading
import time

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, threshold_mb=350):
        self.threshold_mb = threshold_mb
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """开始内存监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                if memory_mb > self.threshold_mb:
                    self.cleanup_memory()
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                print(f"内存监控错误: {e}")
                time.sleep(60)
                
    def cleanup_memory(self):
        """清理内存"""
        try:
            # 执行垃圾回收
            for _ in range(3):
                gc.collect()
                
            # 清理Python内部缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
                
            print("🧹 内存清理完成")
        except Exception as e:
            print(f"内存清理失败: {e}")

# 全局内存优化器实例
memory_optimizer = MemoryOptimizer()
'''
            
            memory_utils_path = PROJECT_ROOT / "ui" / "utils" / "memory_optimizer.py"
            memory_utils_path.parent.mkdir(exist_ok=True)
            
            with open(memory_utils_path, 'w', encoding='utf-8') as f:
                f.write(memory_utils_code)
                
            self.fixes_applied.append("内存优化工具类已创建")
            return True
            
        except Exception as e:
            self.fixes_failed.append(f"内存优化修复失败: {e}")
            return False
            
    def apply_css_compatibility_fix(self):
        """应用CSS兼容性修复"""
        print("🎨 应用CSS兼容性修复...")
        
        try:
            # CSS属性映射表
            css_compatibility_map = {
                'transform': 'qproperty-transform',
                'box-shadow': 'border',
                'text-shadow': 'color',
                'border-radius': 'border-radius',
                'transition': '',  # 移除不支持的属性
                'animation': '',   # 移除不支持的属性
            }
            
            # 创建CSS兼容性处理器
            css_processor_code = '''
import re

class CSSCompatibilityProcessor:
    """CSS兼容性处理器"""
    
    def __init__(self):
        self.compatibility_map = {
            'transform': '',  # PyQt6不支持，移除
            'box-shadow': 'border: 1px solid #ccc;',  # 用边框替代
            'text-shadow': '',  # 移除不支持的属性
            'transition': '',  # 移除不支持的属性
            'animation': '',   # 移除不支持的属性
        }
        
    def process_css(self, css_text):
        """处理CSS文本，移除不兼容属性"""
        if not css_text:
            return css_text
            
        # 移除不支持的属性
        for prop, replacement in self.compatibility_map.items():
            # 匹配属性及其值
            pattern = rf'{prop}\s*:[^;]*;'
            if replacement:
                css_text = re.sub(pattern, replacement, css_text, flags=re.IGNORECASE)
            else:
                css_text = re.sub(pattern, '', css_text, flags=re.IGNORECASE)
                
        # 清理多余的空行和空格
        css_text = re.sub(r'\n\s*\n', '\n', css_text)
        css_text = re.sub(r'{\s*}', '', css_text)  # 移除空的CSS规则
        
        return css_text.strip()
        
    def validate_css(self, css_text):
        """验证CSS兼容性"""
        unsupported_props = []
        for prop in self.compatibility_map.keys():
            if prop in css_text.lower():
                unsupported_props.append(prop)
                
        return {
            'is_compatible': len(unsupported_props) == 0,
            'unsupported_properties': unsupported_props
        }

# 全局CSS处理器实例
css_processor = CSSCompatibilityProcessor()
'''
            
            css_processor_path = PROJECT_ROOT / "ui" / "utils" / "css_compatibility.py"
            with open(css_processor_path, 'w', encoding='utf-8') as f:
                f.write(css_processor_code)
                
            self.fixes_applied.append("CSS兼容性处理器已创建")
            return True
            
        except Exception as e:
            self.fixes_failed.append(f"CSS兼容性修复失败: {e}")
            return False
            
    def apply_language_switching_fix(self):
        """应用语言切换功能修复"""
        print("🌐 应用语言切换功能修复...")
        
        try:
            # 创建语言切换管理器
            language_manager_code = '''
import json
import os
from pathlib import Path

class LanguageManager:
    """语言管理器"""
    
    def __init__(self):
        self.current_language = 'zh'  # 默认中文
        self.translations = {}
        self.load_translations()
        
    def load_translations(self):
        """加载翻译文件"""
        try:
            translations_dir = Path(__file__).parent.parent.parent / "resources" / "locales"
            
            # 中文翻译
            zh_file = translations_dir / "zh_CN.json"
            if zh_file.exists():
                with open(zh_file, 'r', encoding='utf-8') as f:
                    self.translations['zh'] = json.load(f)
            else:
                self.translations['zh'] = self._get_default_zh_translations()
                
            # 英文翻译
            en_file = translations_dir / "en_US.json"
            if en_file.exists():
                with open(en_file, 'r', encoding='utf-8') as f:
                    self.translations['en'] = json.load(f)
            else:
                self.translations['en'] = self._get_default_en_translations()
                
        except Exception as e:
            print(f"加载翻译文件失败: {e}")
            self._load_default_translations()
            
    def _get_default_zh_translations(self):
        """获取默认中文翻译"""
        return {
            "app_title": "🎬 VisionAI-ClipsMaster - AI短剧混剪大师",
            "video_processing": "视频处理",
            "model_training": "模型训练",
            "settings": "设置",
            "about": "关于",
            "file_upload": "文件上传",
            "language": "语言",
            "chinese": "中文",
            "english": "English",
            "auto_detect": "自动检测",
            "gpu_acceleration": "GPU加速",
            "memory_usage": "内存使用",
            "processing": "处理中...",
            "completed": "完成",
            "error": "错误",
            "warning": "警告",
            "info": "信息"
        }
        
    def _get_default_en_translations(self):
        """获取默认英文翻译"""
        return {
            "app_title": "🎬 VisionAI-ClipsMaster - AI Video Editor",
            "video_processing": "Video Processing",
            "model_training": "Model Training", 
            "settings": "Settings",
            "about": "About",
            "file_upload": "File Upload",
            "language": "Language",
            "chinese": "中文",
            "english": "English",
            "auto_detect": "Auto Detect",
            "gpu_acceleration": "GPU Acceleration",
            "memory_usage": "Memory Usage",
            "processing": "Processing...",
            "completed": "Completed",
            "error": "Error",
            "warning": "Warning",
            "info": "Information"
        }
        
    def _load_default_translations(self):
        """加载默认翻译"""
        self.translations = {
            'zh': self._get_default_zh_translations(),
            'en': self._get_default_en_translations()
        }
        
    def switch_language(self, language_code):
        """切换语言"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False
        
    def get_text(self, key, default=None):
        """获取翻译文本"""
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, default or key)
        return default or key
        
    def get_current_language(self):
        """获取当前语言"""
        return self.current_language

# 全局语言管理器实例
language_manager = LanguageManager()
'''
            
            language_manager_path = PROJECT_ROOT / "ui" / "utils" / "language_manager.py"
            with open(language_manager_path, 'w', encoding='utf-8') as f:
                f.write(language_manager_code)
                
            self.fixes_applied.append("语言切换管理器已创建")
            
            # 创建翻译文件目录
            locales_dir = PROJECT_ROOT / "resources" / "locales"
            locales_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存中文翻译文件
            zh_translations = {
                "app_title": "🎬 VisionAI-ClipsMaster - AI短剧混剪大师",
                "video_processing": "视频处理",
                "model_training": "模型训练",
                "settings": "设置",
                "about": "关于"
            }
            
            with open(locales_dir / "zh_CN.json", 'w', encoding='utf-8') as f:
                json.dump(zh_translations, f, indent=2, ensure_ascii=False)
                
            # 保存英文翻译文件
            en_translations = {
                "app_title": "🎬 VisionAI-ClipsMaster - AI Video Editor",
                "video_processing": "Video Processing",
                "model_training": "Model Training",
                "settings": "Settings",
                "about": "About"
            }
            
            with open(locales_dir / "en_US.json", 'w', encoding='utf-8') as f:
                json.dump(en_translations, f, indent=2, ensure_ascii=False)
                
            self.fixes_applied.append("翻译文件已创建")
            return True
            
        except Exception as e:
            self.fixes_failed.append(f"语言切换功能修复失败: {e}")
            return False

    def apply_alert_manager_fix(self):
        """应用AlertManager修复"""
        print("🔔 应用AlertManager修复...")

        try:
            # 创建增强的AlertManager
            alert_manager_code = '''
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QPalette
import time

class EnhancedAlertManager(QWidget):
    """增强的警告管理器"""

    alert_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.alerts = []
        self.max_alerts = 3
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setFixedSize(300, 0)  # 初始高度为0
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.8);
                border-radius: 5px;
                color: white;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

    def show_alert(self, message, level="info", timeout=3000):
        """显示警告"""
        if len(self.alerts) >= self.max_alerts:
            # 移除最旧的警告
            self.remove_alert(self.alerts[0])

        alert_widget = self.create_alert_widget(message, level)
        self.alerts.append(alert_widget)
        self.layout.addWidget(alert_widget)

        # 调整窗口大小
        self.adjust_size()

        # 设置自动关闭定时器
        if timeout > 0:
            timer = QTimer()
            timer.timeout.connect(lambda: self.remove_alert(alert_widget))
            timer.setSingleShot(True)
            timer.start(timeout)
            alert_widget.timer = timer

    def create_alert_widget(self, message, level):
        """创建警告组件"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # 设置样式
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336"
        }

        color = colors.get(level, colors["info"])
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 3px;
                padding: 5px;
            }}
        """)

        # 消息标签
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(lambda: self.remove_alert(widget))
        layout.addWidget(close_btn)

        return widget

    def remove_alert(self, alert_widget):
        """移除警告"""
        if alert_widget in self.alerts:
            self.alerts.remove(alert_widget)
            self.layout.removeWidget(alert_widget)
            alert_widget.deleteLater()
            self.adjust_size()

    def adjust_size(self):
        """调整大小"""
        height = len(self.alerts) * 50 + 20
        self.setFixedHeight(height)

        if self.parent_widget:
            # 定位到父窗口右上角
            parent_rect = self.parent_widget.geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 50
            self.move(x, y)

    def info(self, message, timeout=3000):
        """显示信息"""
        self.show_alert(message, "info", timeout)

    def success(self, message, timeout=3000):
        """显示成功"""
        self.show_alert(message, "success", timeout)

    def warning(self, message, timeout=3000):
        """显示警告"""
        self.show_alert(message, "warning", timeout)

    def error(self, message, timeout=5000):
        """显示错误"""
        self.show_alert(message, "error", timeout)

    def clear_alerts(self):
        """清除所有警告"""
        for alert in self.alerts.copy():
            self.remove_alert(alert)
'''

            alert_manager_path = PROJECT_ROOT / "ui" / "components" / "enhanced_alert_manager.py"
            alert_manager_path.parent.mkdir(exist_ok=True)

            with open(alert_manager_path, 'w', encoding='utf-8') as f:
                f.write(alert_manager_code)

            self.fixes_applied.append("增强AlertManager已创建")
            return True

        except Exception as e:
            self.fixes_failed.append(f"AlertManager修复失败: {e}")
            return False

    def generate_fix_report(self):
        """生成修复报告"""
        report = {
            "fix_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "total_fixes": len(self.fixes_applied) + len(self.fixes_failed),
            "success_rate": len(self.fixes_applied) / (len(self.fixes_applied) + len(self.fixes_failed)) * 100 if (len(self.fixes_applied) + len(self.fixes_failed)) > 0 else 0
        }

        # 保存报告
        report_path = PROJECT_ROOT / f"UI_Components_Fix_Report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report_path, report

    def run_all_fixes(self):
        """运行所有修复"""
        print("🔧 开始UI组件修复...")
        print("=" * 50)

        # 执行各项修复
        fixes = [
            ("内存优化", self.apply_memory_optimization),
            ("CSS兼容性", self.apply_css_compatibility_fix),
            ("语言切换功能", self.apply_language_switching_fix),
            ("AlertManager增强", self.apply_alert_manager_fix)
        ]

        for fix_name, fix_func in fixes:
            print(f"\n🔧 正在应用: {fix_name}")
            try:
                success = fix_func()
                if success:
                    print(f"✅ {fix_name} 修复成功")
                else:
                    print(f"❌ {fix_name} 修复失败")
            except Exception as e:
                print(f"❌ {fix_name} 修复异常: {e}")
                self.fixes_failed.append(f"{fix_name}修复异常: {e}")

        # 生成报告
        print("\n" + "=" * 50)
        print("📊 生成修复报告...")
        report_path, report = self.generate_fix_report()

        print(f"\n📋 修复摘要:")
        print(f"总修复项: {report['total_fixes']}")
        print(f"成功修复: {len(self.fixes_applied)}")
        print(f"失败修复: {len(self.fixes_failed)}")
        print(f"成功率: {report['success_rate']:.1f}%")
        print(f"报告已保存: {report_path}")

        if self.fixes_applied:
            print(f"\n✅ 成功应用的修复:")
            for fix in self.fixes_applied:
                print(f"  - {fix}")

        if self.fixes_failed:
            print(f"\n❌ 失败的修复:")
            for fix in self.fixes_failed:
                print(f"  - {fix}")

        return len(self.fixes_failed) == 0


def main():
    """主函数"""
    try:
        fixer = UIComponentsFixer()
        success = fixer.run_all_fixes()

        if success:
            print("\n🎉 所有UI组件修复成功完成！")
            return 0
        else:
            print("\n⚠️ 部分修复失败，请查看详细报告")
            return 1

    except Exception as e:
        print(f"\n❌ 修复过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
