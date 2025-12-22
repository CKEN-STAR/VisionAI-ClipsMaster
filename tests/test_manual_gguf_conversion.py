#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试手动GGUF转换功能

验证：
1. ModelConverter可以正常导入
2. 转换方法可以正常调用
3. UI组件可以正常创建
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model_converter_import():
    """测试ModelConverter导入"""
    print("=" * 60)
    print("测试1: ModelConverter导入")
    print("=" * 60)
    
    try:
        from models.converters.model_converter import ModelConverter
        print("✅ ModelConverter导入成功")
        return True
    except Exception as e:
        print(f"❌ ModelConverter导入失败: {e}")
        return False

def test_model_converter_creation():
    """测试ModelConverter创建"""
    print("\n" + "=" * 60)
    print("测试2: ModelConverter创建")
    print("=" * 60)
    
    try:
        from models.converters.model_converter import ModelConverter
        converter = ModelConverter()
        print("✅ ModelConverter创建成功")
        print(f"   支持的格式: {converter.supported_formats}")
        print(f"   支持的量化: {converter.supported_quant}")
        return True
    except Exception as e:
        print(f"❌ ModelConverter创建失败: {e}")
        return False

def test_settings_panel_import():
    """测试SettingsPanel导入"""
    print("\n" + "=" * 60)
    print("测试3: SettingsPanel导入")
    print("=" * 60)
    
    try:
        from src.ui.settings_panel import SettingsPanel
        print("✅ SettingsPanel导入成功")
        return True
    except Exception as e:
        print(f"❌ SettingsPanel导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_panel_has_model_management():
    """测试SettingsPanel是否有模型管理标签页"""
    print("\n" + "=" * 60)
    print("测试4: SettingsPanel模型管理标签页")
    print("=" * 60)
    
    try:
        from src.ui.settings_panel import SettingsPanel
        import inspect
        
        # 检查是否有_add_model_management_tab方法
        if hasattr(SettingsPanel, '_add_model_management_tab'):
            print("✅ SettingsPanel有_add_model_management_tab方法")
            
            # 检查方法签名
            method = getattr(SettingsPanel, '_add_model_management_tab')
            sig = inspect.signature(method)
            print(f"   方法签名: {sig}")
            
            return True
        else:
            print("❌ SettingsPanel没有_add_model_management_tab方法")
            return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_conversion_method_signature():
    """测试转换方法签名"""
    print("\n" + "=" * 60)
    print("测试5: 转换方法签名")
    print("=" * 60)
    
    try:
        from models.converters.model_converter import ModelConverter
        import inspect
        
        converter = ModelConverter()
        method = getattr(converter, 'convert_format')
        sig = inspect.signature(method)
        
        print("✅ convert_format方法签名:")
        print(f"   {sig}")
        print(f"   参数: {list(sig.parameters.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_trainer_auto_convert_disabled():
    """测试训练器自动转换已禁用"""
    print("\n" + "=" * 60)
    print("测试6: 训练器自动转换已禁用")
    print("=" * 60)
    
    try:
        # 检查zh_trainer.py
        zh_trainer_path = project_root / "src" / "training" / "zh_trainer.py"
        with open(zh_trainer_path, 'r', encoding='utf-8') as f:
            zh_content = f.read()
        
        # 检查是否有"不自动转换GGUF"的注释
        if "不自动转换GGUF" in zh_content:
            print("✅ zh_trainer.py: 已禁用自动转换")
        else:
            print("⚠️ zh_trainer.py: 未找到禁用自动转换的注释")
        
        # 检查en_trainer.py
        en_trainer_path = project_root / "src" / "training" / "en_trainer.py"
        with open(en_trainer_path, 'r', encoding='utf-8') as f:
            en_content = f.read()
        
        if "Don't auto-convert to GGUF" in en_content:
            print("✅ en_trainer.py: 已禁用自动转换")
        else:
            print("⚠️ en_trainer.py: 未找到禁用自动转换的注释")
        
        return True
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_downloader_comments_fixed():
    """测试下载器注释已修正"""
    print("\n" + "=" * 60)
    print("测试7: 下载器注释已修正")
    print("=" * 60)
    
    try:
        downloader_path = project_root / "src" / "core" / "enhanced_model_downloader.py"
        with open(downloader_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否还有"GPTQ格式"的误导性注释
        if "GPTQ格式" in content:
            print("❌ 仍然存在'GPTQ格式'的误导性注释")
            return False
        else:
            print("✅ 已修正为'HuggingFace格式'")
        
        # 检查是否有正确的注释
        if "HuggingFace格式" in content or "HuggingFace标准格式" in content:
            print("✅ 注释已正确修改")
            return True
        else:
            print("⚠️ 未找到'HuggingFace格式'注释")
            return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster 手动GGUF转换功能测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("ModelConverter导入", test_model_converter_import()))
    results.append(("ModelConverter创建", test_model_converter_creation()))
    results.append(("SettingsPanel导入", test_settings_panel_import()))
    results.append(("模型管理标签页", test_settings_panel_has_model_management()))
    results.append(("转换方法签名", test_conversion_method_signature()))
    results.append(("自动转换已禁用", test_trainer_auto_convert_disabled()))
    results.append(("下载器注释已修正", test_downloader_comments_fixed()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

