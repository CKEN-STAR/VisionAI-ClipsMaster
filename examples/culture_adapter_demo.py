#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文化语境适配器演示脚本

通过多个示例展示文化语境适配器的功能和效果
"""

import sys
import os
from pathlib import Path
import colorama
from colorama import Fore, Style, init
import textwrap

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adaptation.culture_adapter import CultureAdapter


def setup_colorama():
    """初始化彩色输出"""
    init()


def print_header(text):
    """打印标题"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "=" * 80)
    print(f" {text}")
    print("=" * 80 + f"{Style.RESET_ALL}\n")


def print_example(original, adapted, lang_from, lang_to):
    """打印示例对比"""
    lang_names = {"zh": "中文", "en": "英文"}
    
    print(f"{Fore.YELLOW}● 原始{lang_names[lang_from]}:{Style.RESET_ALL}")
    print(f"  {original}")
    print(f"\n{Fore.GREEN}● 转换为{lang_names[lang_to]}:{Style.RESET_ALL}")
    print(f"  {adapted}")
    print(f"\n{Fore.MAGENTA}--------{Style.RESET_ALL}\n")


def demonstrate_emotion_adaptation(adapter):
    """情感表达适配演示"""
    print_header("情感表达适配")
    
    examples = [
        # 中文含蓄 -> 英文直接
        {
            "original": "这个作品还不错，值得一看。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        {
            "original": "我觉得你的提议可能有些小问题。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        # 英文直接 -> 中文含蓄
        {
            "original": "This movie is absolutely fantastic! I love it!",
            "lang_from": "en",
            "lang_to": "zh"
        },
        {
            "original": "I strongly disagree with your approach, it's completely wrong.",
            "lang_from": "en",
            "lang_to": "zh"
        }
    ]
    
    for example in examples:
        adapted = adapter.adapt_expression(
            example["original"], 
            example["lang_to"]
        )
        print_example(
            example["original"], 
            adapted, 
            example["lang_from"], 
            example["lang_to"]
        )


def demonstrate_idiom_translation(adapter):
    """成语习语转换演示"""
    print_header("成语习语转换")
    
    examples = [
        # 中文成语 -> 英文表达
        {
            "original": "这件事情真是一箭双雕，既解决了问题又节省了时间。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        {
            "original": "他总是守株待兔，从不主动寻找机会。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        # 英文习语 -> 中文成语
        {
            "original": "Let's not put all our eggs in one basket for this investment.",
            "lang_from": "en",
            "lang_to": "zh"
        },
        {
            "original": "We should cross that bridge when we come to it.",
            "lang_from": "en",
            "lang_to": "zh"
        }
    ]
    
    for example in examples:
        adapted = adapter.adapt_expression(
            example["original"], 
            example["lang_to"]
        )
        print_example(
            example["original"], 
            adapted, 
            example["lang_from"], 
            example["lang_to"]
        )


def demonstrate_cultural_references(adapter):
    """文化参考转换演示"""
    print_header("文化参考转换")
    
    examples = [
        # 中文文化参考 -> 英文
        {
            "original": "春节期间，全家人会一起包饺子、看春晚。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        {
            "original": "她在微信上发了一条朋友圈，收到了很多点赞。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        # 英文文化参考 -> 中文
        {
            "original": "We always open presents on Christmas morning.",
            "lang_from": "en",
            "lang_to": "zh"
        },
        {
            "original": "She posted a story on Instagram and got many likes.",
            "lang_from": "en",
            "lang_to": "zh"
        }
    ]
    
    for example in examples:
        adapted = adapter.localize_cultural_references(
            example["original"],
            example["lang_from"],
            example["lang_to"]
        )
        print_example(
            example["original"], 
            adapted, 
            example["lang_from"], 
            example["lang_to"]
        )


def demonstrate_sentence_structure(adapter):
    """句式结构调整演示"""
    print_header("句式结构调整")
    
    examples = [
        # 中文长句 -> 英文短句
        {
            "original": "这是一个非常复杂而且充满了各种修饰词和不必要的重复内容的中文长句，它可以被转换成更简洁明了的英文表达方式，让外国人更容易理解。",
            "lang_from": "zh",
            "lang_to": "en"
        },
        # 英文短句 -> 中文长句
        {
            "original": "This is short. Very direct. No extra words. Just facts.",
            "lang_from": "en",
            "lang_to": "zh"
        }
    ]
    
    for example in examples:
        adapted = adapter._adapt_sentence_structure(
            example["original"],
            example["lang_to"]
        )
        print_example(
            example["original"], 
            adapted, 
            example["lang_from"], 
            example["lang_to"]
        )


def demonstrate_complete_conversion(adapter):
    """完整转换演示"""
    print_header("完整文本转换示例")
    
    examples = [
        # 中文 -> 英文完整转换
        {
            "original": textwrap.dedent("""
            亲爱的朋友，
            
            首先，辛苦你了，你最近的工作真的做得不错。那个项目虽然有点小问题，但总体来说还是可以的。
            
            关于你上次提到的事情，我考虑了一下，可能不太方便，希望你能理解。如果实在需要帮忙，我们可以再商量其他解决办法。
            
            春节期间，如果你有空，可以来我家坐坐，一起吃个饭。我在微信上发了一些照片，你可以看看。
            
            守株待兔是不行的，机会要靠自己把握。希望我们一起加油，争取一鸣惊人！
            
            祝好，
            小李
            """).strip(),
            "lang_from": "zh",
            "lang_to": "en"
        },
        # 英文 -> 中文完整转换
        {
            "original": textwrap.dedent("""
            Dear Friend,
            
            I absolutely loved your presentation yesterday! It was amazing and the best I've seen this year.
            
            Regarding your request, I'm afraid I can't help with that. It's simply not possible with my current schedule.
            
            Let's meet for coffee during Christmas. I'll post some photos on Instagram from our meeting.
            
            Remember, you can't just wait for opportunities to come to you. You need to go out and seize them! I know you can do this and achieve great things!
            
            Best regards,
            John
            """).strip(),
            "lang_from": "en",
            "lang_to": "zh"
        }
    ]
    
    for example in examples:
        # 逐行处理以保持格式
        original_lines = example["original"].split("\n")
        adapted_lines = []
        
        for line in original_lines:
            if line.strip():
                adapted_line = adapter.adapt_expression(line, example["lang_to"])
                # 对文化参考进行本地化
                adapted_line = adapter.localize_cultural_references(
                    adapted_line,
                    example["lang_from"],
                    example["lang_to"]
                )
                adapted_lines.append(adapted_line)
            else:
                adapted_lines.append("")
        
        adapted = "\n".join(adapted_lines)
        
        print_example(
            example["original"], 
            adapted, 
            example["lang_from"], 
            example["lang_to"]
        )


def main():
    """主函数"""
    setup_colorama()
    
    # 创建适配器实例
    adapter = CultureAdapter()
    
    print_header("文化语境适配器演示")
    print(f"{Fore.WHITE}本演示展示了文化语境适配器在中英文表达转换中的应用。{Style.RESET_ALL}\n")
    
    # 各功能演示
    demonstrate_emotion_adaptation(adapter)
    demonstrate_idiom_translation(adapter)
    demonstrate_cultural_references(adapter)
    demonstrate_sentence_structure(adapter)
    demonstrate_complete_conversion(adapter)
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}演示结束{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main() 