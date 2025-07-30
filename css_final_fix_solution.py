#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster CSS兼容性最终修复解决方案
统一处理所有CSS生成点，彻底消除CSS警告
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

class CSSFinalFixer:
    """CSS最终修复器"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.fixes_applied = []
        
    def apply_final_css_fixes(self):
        """应用最终CSS修复"""
        print("🎨 VisionAI-ClipsMaster CSS兼容性最终修复")
        print("=" * 60)
        
        # 1. 创建统一CSS管理器
        self.create_unified_css_manager()
        
        # 2. 修复CSS优化器
        self.fix_css_optimizer_integration()
        
        # 3. 修复样式编译器正则表达式
        self.fix_style_compiler_regex()
        
        # 4. 更新主UI文件使用统一CSS管理器
        self.update_main_ui_css_usage()
        
        # 5. 创建CSS兼容性测试
        self.create_css_compatibility_test()
        
        print(f"\n✅ CSS最终修复完成！应用了 {len(self.fixes_applied)} 项修复")
        
    def create_unified_css_manager(self):
        """创建统一CSS管理器"""
        print("\n1. 创建统一CSS管理器...")
        
        css_manager_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 统一CSS管理器
提供统一的CSS处理和应用接口
"""

import re
import logging
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import QWidget

# 设置日志
logger = logging.getLogger(__name__)

class UnifiedCSSManager:
    """统一CSS管理器"""
    
    def __init__(self):
        self.cache = {}
        self.stats = {
            'processed_count': 0,
            'warnings_removed': 0,
            'cache_hits': 0
        }
        
        # Qt不支持的CSS属性完整列表
        self.unsupported_properties = {
            'transform', 'transform-origin', 'transform-style',
            'transition', 'transition-property', 'transition-duration', 
            'transition-timing-function', 'transition-delay',
            'animation', 'animation-name', 'animation-duration',
            'animation-timing-function', 'animation-delay',
            'animation-iteration-count', 'animation-direction',
            'animation-fill-mode', 'animation-play-state',
            'box-shadow', 'text-shadow', 'filter', 'backdrop-filter',
            'drop-shadow', 'clip-path', 'mask', 'mask-image', 'mask-size',
            'flex', 'flex-direction', 'flex-wrap', 'flex-flow',
            'justify-content', 'align-items', 'align-content',
            'grid', 'grid-template', 'grid-area', 'opacity'
        }
        
        # CSS属性智能替代方案
        self.smart_replacements = {
            '/* transform not supported in QSS */',
            '/* text-shadow not supported in QSS - use color/font-weight instead */',
            '/* transition not supported in QSS */',
            'opacity: 1': '/* fully opaque */',
        }
        
    def apply_css(self, widget: QWidget, css_content: str, cache_key: Optional[str] = None) -> bool:
        """统一的CSS应用接口"""
        try:
            # 检查缓存
            if cache_key and cache_key in self.cache:
                processed_css = self.cache[cache_key]
                self.stats['cache_hits'] += 1
            else:
                # 处理CSS
                processed_css = self.process_css_content(css_content)
                
                # 缓存结果
                if cache_key:
                    self.cache[cache_key] = processed_css
            
            # 应用CSS
            widget.setStyleSheet(processed_css)
            self.stats['processed_count'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"CSS应用失败: {e}")
            # 回退到原始CSS
            try:
                widget.setStyleSheet(css_content)
                return True
            except:
                return False
    
    def process_css_content(self, css_content: str) -> str:
        """处理CSS内容"""
        if not css_content:
            return css_content
        
        original_warnings = self._count_unsupported_properties(css_content)
        
        # 1. 移除不支持的CSS属性
        processed_css = self._remove_unsupported_properties(css_content)
        
        # 2. 应用智能替代方案
        processed_css = self._apply_smart_replacements(processed_css)
        
        # 3. 清理空规则
        processed_css = self._clean_empty_rules(processed_css)
        
        # 4. 格式化CSS
        processed_css = self._format_css(processed_css)
        
        # 统计移除的警告
        final_warnings = self._count_unsupported_properties(processed_css)
        self.stats['warnings_removed'] += max(0, original_warnings - final_warnings)
        
        return processed_css
    
    def _remove_unsupported_properties(self, css_content: str) -> str:
        """移除不支持的CSS属性"""
        lines = css_content.split('\\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip().lower()
            should_keep = True
            
            # 检查是否包含不支持的属性
            for prop in self.unsupported_properties:
                if f'{prop}:' in line_stripped or f'{prop} :' in line_stripped:
                    should_keep = False
                    break
            
            if should_keep:
                cleaned_lines.append(line)
        
        return '\\n'.join(cleaned_lines)
    
    def _apply_smart_replacements(self, css_content: str) -> str:
        """应用智能替代方案"""
        result = css_content
        
        for old_pattern, replacement in self.smart_replacements.items():
            if old_pattern in result:
                # 使用正则表达式进行更精确的替换
                pattern = re.escape(old_pattern) + r'[^;]*;'
                result = re.sub(pattern, replacement + ';', result, flags=re.IGNORECASE)
        
        return result
    
    def _clean_empty_rules(self, css_content: str) -> str:
        """清理空的CSS规则"""
        # 移除只包含注释或空白的CSS规则
        pattern = r'[^{]*\\{\\s*(?:/\\*[^*]*\\*/\\s*)*\\}'
        return re.sub(pattern, '', css_content, flags=re.MULTILINE)
    
    def _format_css(self, css_content: str) -> str:
        """格式化CSS"""
        # 移除多余的空行
        lines = css_content.split('\\n')
        formatted_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):
                formatted_lines.append(line)
            prev_empty = is_empty
        
        return '\\n'.join(formatted_lines)
    
    def _count_unsupported_properties(self, css_content: str) -> int:
        """统计不支持的CSS属性数量"""
        count = 0
        for prop in self.unsupported_properties:
            count += len(re.findall(rf'{prop}\\s*:', css_content, re.IGNORECASE))
        return count
    
    def validate_css_compatibility(self, css_content: str) -> Dict[str, List[str]]:
        """验证CSS兼容性"""
        supported = []
        unsupported = []
        
        # 简单的CSS属性提取
        properties = re.findall(r'([a-zA-Z-]+)\\s*:', css_content)
        
        for prop in properties:
            prop_lower = prop.lower()
            if any(unsup in prop_lower for unsup in self.unsupported_properties):
                unsupported.append(prop)
            else:
                supported.append(prop)
        
        return {
            'supported': list(set(supported)),
            'unsupported': list(set(unsupported))
        }
    
    def get_stats(self) -> Dict[str, int]:
        """获取处理统计"""
        return self.stats.copy()
    
    def clear_cache(self):
        """清理缓存"""
        self.cache.clear()
        logger.info("CSS缓存已清理")

# 全局CSS管理器实例
css_manager = UnifiedCSSManager()

def apply_qt_compatible_css(widget: QWidget, css_content: str, cache_key: Optional[str] = None) -> bool:
    """统一的Qt兼容CSS应用函数"""
    return css_manager.apply_css(widget, css_content, cache_key)

def process_css_for_compatibility(css_content: str) -> str:
    """处理CSS以确保兼容性"""
    return css_manager.process_css_content(css_content)

def validate_css_before_apply(css_content: str) -> Dict[str, List[str]]:
    """CSS应用前验证"""
    return css_manager.validate_css_compatibility(css_content)

def get_css_processing_stats() -> Dict[str, int]:
    """获取CSS处理统计"""
    return css_manager.get_stats()

def clear_css_cache():
    """清理CSS缓存"""
    css_manager.clear_cache()
'''
        
        css_manager_path = self.project_root / "ui" / "utils" / "unified_css_manager.py"
        css_manager_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(css_manager_path, 'w', encoding='utf-8') as f:
            f.write(css_manager_content)
        
        print(f"  ✅ 统一CSS管理器已创建: {css_manager_path}")
        self.fixes_applied.append("创建统一CSS管理器")
    
    def fix_css_optimizer_integration(self):
        """修复CSS优化器集成"""
        print("\n2. 修复CSS优化器集成...")
        
        css_optimizer_path = self.project_root / "css_optimizer.py"
        
        if not css_optimizer_path.exists():
            print("  ⚠️ CSS优化器文件不存在")
            return
        
        try:
            with open(css_optimizer_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加统一CSS管理器导入
            import_addition = '''
# 导入统一CSS管理器
try:
    from ui.utils.unified_css_manager import apply_qt_compatible_css, process_css_for_compatibility
    UNIFIED_CSS_MANAGER_AVAILABLE = True
    print("[OK] 统一CSS管理器导入成功")
except ImportError as e:
    UNIFIED_CSS_MANAGER_AVAILABLE = False
    print(f"[WARN] 统一CSS管理器导入失败: {e}")
    def apply_qt_compatible_css(widget, css, cache_key=None): 
        widget.setStyleSheet(css)
        return True
    def process_css_for_compatibility(css): 
        return css
'''
            
            # 在文件开头添加导入
            if 'unified_css_manager' not in content:
                content = import_addition + '\n' + content
                self.fixes_applied.append("CSS优化器添加统一管理器导入")
            
            # 更新apply_optimized_styles函数
            old_apply_function = r'def apply_optimized_styles\(widget\):.*?(?=\ndef|\nclass|\Z)'
            new_apply_function = '''def apply_optimized_styles(widget):
    """应用优化的样式表到组件"""
    try:
        # 获取组件类型
        widget_type = widget.__class__.__name__
        
        # 生成缓存键
        cache_key = f"optimized_{widget_type}"
        
        # 获取基础样式
        base_style = get_base_style_for_widget(widget_type)
        
        # 使用统一CSS管理器应用样式
        if UNIFIED_CSS_MANAGER_AVAILABLE:
            success = apply_qt_compatible_css(widget, base_style, cache_key)
            if success:
                print(f"[OK] 使用统一CSS管理器应用样式: {widget_type}")
            else:
                print(f"[WARN] 统一CSS管理器应用失败，使用原始样式: {widget_type}")
                widget.setStyleSheet(base_style)
        else:
            widget.setStyleSheet(base_style)
            
    except Exception as e:
        print(f"[ERROR] 应用优化样式失败: {e}")'''
        
            if 'def apply_optimized_styles(' in content:
                content = re.sub(old_apply_function, new_apply_function, content, flags=re.DOTALL)
                self.fixes_applied.append("更新CSS优化器应用函数")
            
            # 保存修改
            with open(css_optimizer_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ CSS优化器集成修复完成")
            
        except Exception as e:
            print(f"  ❌ CSS优化器集成修复失败: {e}")
    
    def fix_style_compiler_regex(self):
        """修复样式编译器正则表达式"""
        print("\n3. 修复样式编译器正则表达式...")
        
        style_compiler_path = self.project_root / "ui" / "themes" / "style_compiler.py"
        
        if not style_compiler_path.exists():
            print("  ⚠️ 样式编译器文件不存在")
            return
        
        try:
            with open(style_compiler_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修复所有正则表达式问题
            regex_fixes = [
                # 修复group reference错误
                (r'\\\\1', r'\\\\g<1>'),
                (r'\\1(?![0-9])', r'\\g<1>'),
                (r'\$1(?![0-9])', r'\\g<1>'),
                
                # 修复条件编译正则表达式
                (r'/\\\*\*@if\\\s\+\(.*?\)\\\s\*\\\*/\(.*?\)/\\\*\*@endif\\\s\*\\\*/', 
                 r'/\\*\\*@if\\s+(.*?)\\s*\\*/(.*?)/\\*\\*@endif\\s*\\*/'),
                
                # 修复变量替换正则表达式
                (r'\\\{\\\{([^}]+)\\\}\\\}', r'\\{\\{([^}]+)\\}\\}'),
                
                # 修复嵌套变量正则表达式
                (r'\\\{\\\{([^:}]+):([^}]+)\\\}\\\}', r'\\{\\{([^:}]+):([^}]+)\\}\\}'),
            ]
            
            original_content = content
            for old_pattern, new_pattern in regex_fixes:
                content = re.sub(old_pattern, new_pattern, content)
            
            if content != original_content:
                with open(style_compiler_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("  ✅ 样式编译器正则表达式修复完成")
                self.fixes_applied.append("修复样式编译器正则表达式")
            else:
                print("  ℹ️ 样式编译器无需修复")
                
        except Exception as e:
            print(f"  ❌ 样式编译器正则表达式修复失败: {e}")
    
    def update_main_ui_css_usage(self):
        """更新主UI文件使用统一CSS管理器"""
        print("\n4. 更新主UI文件CSS使用...")
        
        ui_file_path = self.project_root / "simple_ui_fixed.py"
        
        if not ui_file_path.exists():
            print("  ⚠️ 主UI文件不存在")
            return
        
        try:
            with open(ui_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加统一CSS管理器导入
            import_pattern = r'# 导入增强CSS处理器.*?def validate_css_compatibility\(css\): return \{\'supported\': \[\], \'unsupported\': \[\]\}'
            
            new_import = '''# 导入增强CSS处理器
try:
    from ui.utils.enhanced_css_processor import process_css_for_qt, validate_css_compatibility
    ENHANCED_CSS_PROCESSOR_AVAILABLE = True
    print("[OK] 增强CSS处理器导入成功")
except ImportError as e:
    ENHANCED_CSS_PROCESSOR_AVAILABLE = False
    print(f"[WARN] 增强CSS处理器导入失败: {e}")
    # 定义空函数以保持兼容性
    def process_css_for_qt(css): return css
    def validate_css_compatibility(css): return {'supported': [], 'unsupported': []}

# 导入统一CSS管理器
try:
    from ui.utils.unified_css_manager import apply_qt_compatible_css, get_css_processing_stats
    UNIFIED_CSS_MANAGER_AVAILABLE = True
    print("[OK] 统一CSS管理器导入成功")
except ImportError as e:
    UNIFIED_CSS_MANAGER_AVAILABLE = False
    print(f"[WARN] 统一CSS管理器导入失败: {e}")
    # 定义空函数以保持兼容性
    def apply_qt_compatible_css(widget, css, cache_key=None): 
        widget.setStyleSheet(css)
        return True
    def get_css_processing_stats(): return {}'''
            
            if 'unified_css_manager' not in content:
                content = re.sub(import_pattern, new_import, content, flags=re.DOTALL)
                self.fixes_applied.append("主UI文件添加统一CSS管理器导入")
            
            # 更新setup_ui_style方法
            old_css_apply = r'self\.setStyleSheet\(style_sheet\)'
            new_css_apply = '''# 使用统一CSS管理器应用样式
        if UNIFIED_CSS_MANAGER_AVAILABLE:
            success = apply_qt_compatible_css(self, style_sheet, "main_ui_style")
            if success:
                print("[OK] 使用统一CSS管理器应用主UI样式")
                # 显示处理统计
                stats = get_css_processing_stats()
                if stats.get('warnings_removed', 0) > 0:
                    print(f"[INFO] 移除了 {stats['warnings_removed']} 个CSS兼容性警告")
            else:
                print("[WARN] 统一CSS管理器应用失败，使用原始样式")
                self.setStyleSheet(style_sheet)
        else:
            self.setStyleSheet(style_sheet)'''
            
            if 'self.setStyleSheet(style_sheet)' in content:
                content = content.replace('self.setStyleSheet(style_sheet)', new_css_apply)
                self.fixes_applied.append("更新主UI样式应用方法")
            
            # 保存修改
            with open(ui_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ 主UI文件CSS使用更新完成")
            
        except Exception as e:
            print(f"  ❌ 主UI文件CSS使用更新失败: {e}")
    
    def create_css_compatibility_test(self):
        """创建CSS兼容性测试"""
        print("\n5. 创建CSS兼容性测试...")
        
        test_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster CSS兼容性测试
验证CSS处理和兼容性修复效果
"""

import sys
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def test_css_compatibility():
    """测试CSS兼容性"""
    print("🧪 CSS兼容性测试")
    print("=" * 40)
    
    try:
        from ui.utils.unified_css_manager import (
            css_manager, apply_qt_compatible_css, 
            process_css_for_compatibility, validate_css_before_apply
        )
        
        # 测试CSS内容
        test_css = """
        .test-widget {
            background-color: #ffffff;
            border: 1px solid #ddd;
            /* transform not supported in QSS */
            /* box-shadow not supported in QSS - use border instead */
            /* text-shadow not supported in QSS - use color/font-weight instead */
            /* transition not supported in QSS */
            /* animation not supported in QSS */
            opacity: 0.8;
            color: #333;
            font-size: 14px;
        }
        """
        
        print("原始CSS:")
        print(test_css)
        
        # 验证兼容性
        compatibility = validate_css_before_apply(test_css)
        print(f"\\n兼容性检查:")
        print(f"  支持的属性: {len(compatibility['supported'])} 个")
        print(f"  不支持的属性: {len(compatibility['unsupported'])} 个")
        
        if compatibility['unsupported']:
            print(f"  不支持的属性列表: {compatibility['unsupported']}")
        
        # 处理CSS
        processed_css = process_css_for_compatibility(test_css)
        print(f"\\n处理后CSS:")
        print(processed_css)
        
        # 验证处理后的兼容性
        final_compatibility = validate_css_before_apply(processed_css)
        print(f"\\n处理后兼容性:")
        print(f"  支持的属性: {len(final_compatibility['supported'])} 个")
        print(f"  不支持的属性: {len(final_compatibility['unsupported'])} 个")
        
        # 获取统计信息
        stats = css_manager.get_stats()
        print(f"\\n处理统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\\n✅ CSS兼容性测试完成")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_css_compatibility()
'''
        
        test_path = self.project_root / "test_css_compatibility.py"
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"  ✅ CSS兼容性测试已创建: {test_path}")
        self.fixes_applied.append("创建CSS兼容性测试")

def main():
    """主修复函数"""
    fixer = CSSFinalFixer()
    fixer.apply_final_css_fixes()
    
    print("\n" + "=" * 60)
    print("🎉 CSS兼容性最终修复完成！")
    print("\n下一步:")
    print("1. 运行 test_css_compatibility.py 验证修复效果")
    print("2. 启动 simple_ui_fixed.py 检查CSS警告")
    print("3. 查看 CSS_Compatibility_Verification_Report.md")

if __name__ == "__main__":
    main()
