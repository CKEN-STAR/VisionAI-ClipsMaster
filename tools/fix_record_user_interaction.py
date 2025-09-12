#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复record_user_interaction调用问题的脚本
"""

import re

def fix_record_user_interaction_calls():
    """修复所有record_user_interaction调用"""
    
    # 读取文件
    with open('simple_ui_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有self.record_user_interaction()调用
    pattern = r'(\\\1+)self\\\1record_user_interaction\\\1\\\1'
    
    def replace_call(match):
        indent = match.group(1)
        return f'''{indent}# 安全调用record_user_interaction
{indent}try:
{indent}    if hasattr(self, 'record_user_interaction'):
{indent}        self.record_user_interaction()
{indent}    else:
{indent}        print("🔍 [DEBUG] record_user_interaction方法不存在，跳过")
{indent}except Exception as e:
{indent}    print(f"⚠️ [WARNING] record_user_interaction调用失败: {{e}}")'''
    
    # 替换所有调用
    new_content = re.sub(pattern, replace_call, content)
    
    # 写回文件
    with open('simple_ui_fixed.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 已修复所有record_user_interaction调用")

if __name__ == "__main__":
    fix_record_user_interaction_calls()
