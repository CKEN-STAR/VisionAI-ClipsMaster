#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复simple_ui.py文件中的错误
"""

with open('simple_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并删除SimpleScreenplayApp类init_ui方法中错误的布局设置代码
start_marker = '        # 设置状态栏\n        self.statusBar().showMessage("就绪")'
end_marker = '    def check_models(self):'

# 找到开始和结束标记在内容中的位置
start_pos = content.find(start_marker)
end_pos = content.find(end_marker, start_pos)

if start_pos != -1 and end_pos != -1:
    # 替换部分内容
    new_content = content[:start_pos + len(start_marker)] + '\n\n' + content[end_pos:]
    
    # 写入修复后的文件
    with open('fixed_simple_ui.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("文件修复成功！")
else:
    print("无法找到要修复的代码段") 