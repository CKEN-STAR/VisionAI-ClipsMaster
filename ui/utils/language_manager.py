
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
