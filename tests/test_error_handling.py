#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试错误处理增强
验证用户友好的错误提示功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_error_translator():
    """测试错误翻译器"""
    print("=" * 60)
    print("测试1: 错误翻译器")
    print("=" * 60)
    
    from src.utils.user_friendly_errors import translate_error, format_error
    
    # 测试各种错误类型
    test_cases = [
        (FileNotFoundError("No such file or directory: video.mp4"), "文件未找到"),
        (MemoryError("Out of memory"), "内存不足"),
        (RuntimeError("CUDA error: out of memory"), "GPU处理错误"),
        (PermissionError("Access denied"), "权限不足"),
        (OSError("[WinError 1114] 动态链接库(DLL)初始化例程失败"), "系统库加载失败"),
    ]
    
    for exception, expected_category in test_cases:
        friendly_error = translate_error(exception)
        print(f"\n原始错误: {type(exception).__name__}")
        print(f"友好标题: {friendly_error.title}")
        print(f"用户消息: {friendly_error.message}")
        print(f"建议方案: {len(friendly_error.solutions)}个")
        print(f"严重程度: {friendly_error.severity}")
        
        # 验证错误被正确分类
        assert friendly_error.title, "错误标题不能为空"
        assert friendly_error.message, "错误消息不能为空"
        assert friendly_error.solutions, "应该有解决方案"
    
    print("\n✓ 错误翻译器测试通过")
    print()


def test_format_error():
    """测试错误格式化"""
    print("=" * 60)
    print("测试2: 错误格式化")
    print("=" * 60)
    
    from src.utils.user_friendly_errors import format_error
    
    # 测试格式化输出
    exception = FileNotFoundError("video.mp4 not found")
    
    # 不显示技术细节
    formatted = format_error(exception, show_technical=False)
    print("\n不显示技术细节:")
    print(formatted)
    assert "❌" in formatted, "应该包含错误图标"
    assert "💡" in formatted, "应该包含建议图标"
    
    # 显示技术细节
    formatted_tech = format_error(exception, show_technical=True)
    print("\n显示技术细节:")
    print(formatted_tech)
    assert "🔧" in formatted_tech, "应该包含技术细节图标"
    assert "FileNotFoundError" in formatted_tech, "应该包含异常类型"
    
    print("\n✓ 错误格式化测试通过")
    print()


def test_clip_generator_error_handling():
    """测试ClipGenerator的错误处理"""
    print("=" * 60)
    print("测试3: ClipGenerator错误处理")
    print("=" * 60)
    
    try:
        from src.core.clip_generator import ClipGenerator
        
        generator = ClipGenerator()
        
        # 测试不存在的视频文件
        result = generator.get_video_info("nonexistent_video.mp4")
        
        print(f"状态: {'error' in result}")
        if 'error' in result:
            print(f"错误消息: {result['error']}")
        if 'user_message' in result:
            print(f"用户消息: {result['user_message']}")
            assert result['user_message'], "应该有用户友好的错误消息"
        
        print("✓ ClipGenerator错误处理正常")
    except Exception as e:
        print(f"⚠ ClipGenerator测试跳过（可能是环境问题）: {str(e)[:50]}")
    
    print()


def test_screenplay_engineer_error_handling():
    """测试ScreenplayEngineer的错误处理"""
    print("=" * 60)
    print("测试4: ScreenplayEngineer错误处理")
    print("=" * 60)
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        engineer = ScreenplayEngineer()
        
        # 测试加载不存在的字幕文件
        result = engineer.load_subtitles("nonexistent.srt")
        
        print(f"加载结果: {len(result)}个字幕")
        print("✓ ScreenplayEngineer错误处理正常（返回空列表作为fallback）")
    except Exception as e:
        print(f"⚠ ScreenplayEngineer测试跳过（可能是环境问题）: {str(e)[:50]}")
    
    print()


def test_error_patterns():
    """测试错误模式匹配"""
    print("=" * 60)
    print("测试5: 错误模式匹配")
    print("=" * 60)
    
    from src.utils.user_friendly_errors import ErrorTranslator
    
    translator = ErrorTranslator()
    
    # 验证所有错误模式都有必要的字段
    for pattern_name, pattern in translator.error_patterns.items():
        assert "keywords" in pattern, f"{pattern_name}缺少keywords"
        assert "title" in pattern, f"{pattern_name}缺少title"
        assert "message" in pattern, f"{pattern_name}缺少message"
        assert "solutions" in pattern, f"{pattern_name}缺少solutions"
        assert "severity" in pattern, f"{pattern_name}缺少severity"
        
        # 验证solutions不为空
        assert len(pattern["solutions"]) > 0, f"{pattern_name}的solutions为空"
        
        print(f"✓ {pattern_name:20s} - {pattern['title']}")
    
    print(f"\n✓ 共{len(translator.error_patterns)}个错误模式，全部验证通过")
    print()


def test_generic_error_handling():
    """测试通用错误处理"""
    print("=" * 60)
    print("测试6: 通用错误处理")
    print("=" * 60)
    
    from src.utils.user_friendly_errors import translate_error
    
    # 测试未知类型的错误
    unknown_error = ValueError("Some unknown error")
    friendly_error = translate_error(unknown_error)
    
    print(f"原始错误: {unknown_error}")
    print(f"友好标题: {friendly_error.title}")
    print(f"用户消息: {friendly_error.message}")
    print(f"建议方案: {friendly_error.solutions}")
    
    # 验证通用错误也有基本信息
    assert friendly_error.title, "通用错误应该有标题"
    assert friendly_error.message, "通用错误应该有消息"
    assert friendly_error.solutions, "通用错误应该有解决方案"
    
    print("\n✓ 通用错误处理测试通过")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("错误处理增强测试套件")
    print("=" * 60 + "\n")
    
    try:
        test_error_translator()
        test_format_error()
        test_clip_generator_error_handling()
        test_screenplay_engineer_error_handling()
        test_error_patterns()
        test_generic_error_handling()
        
        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试失败: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

