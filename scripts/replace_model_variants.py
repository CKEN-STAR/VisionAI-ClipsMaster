#!/usr/bin/env python
"""
替换quantization_analysis.py中的模型变体定义
"""

def main():
    # 读取原文件
    with open("src/core/quantization_analysis.py", 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 读取生成的GGUF变体代码
    with open("scripts/generated_gguf_variants.txt", 'r', encoding='utf-8') as f:
        new_variants = f.read()
    
    # 找到需要替换的起始和结束行
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if 'return {' in line and start_line is None and i > 80:  # 在_initialize_model_variants方法中
            start_line = i
        if start_line is not None and line.strip() == '}' and 'def _initialize_benchmarks' in ''.join(lines[i+1:i+5]):
            end_line = i
            break
    
    if start_line is None or end_line is None:
        print(f"❌ 未找到替换位置: start_line={start_line}, end_line={end_line}")
        return
    
    print(f"✅ 找到替换位置: 第{start_line+1}行 到 第{end_line+1}行")
    print(f"📝 原内容行数: {end_line - start_line + 1}")
    
    # 构建新文件内容
    new_lines = lines[:start_line] + [new_variants + '\n'] + lines[end_line+1:]
    
    # 写回文件
    with open("src/core/quantization_analysis.py", 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ 替换完成！新文件总行数: {len(new_lines)}")
    print(f"📊 变体定义从 {end_line - start_line + 1} 行减少到 {len(new_variants.split(chr(10)))} 行")

if __name__ == "__main__":
    main()

